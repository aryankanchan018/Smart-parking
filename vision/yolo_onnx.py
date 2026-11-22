"""
yolo_onnx.py — Torch-free YOLO11n inference using onnxruntime.
Replaces ultralytics YOLO class entirely.
"""

import cv2
import numpy as np
import onnxruntime as ort

COCO_CLASSES = {
    0:"person",1:"bicycle",2:"car",3:"motorcycle",4:"airplane",5:"bus",
    6:"train",7:"truck",8:"boat",9:"traffic light",10:"fire hydrant",
}

class YOLOOnnx:
    def __init__(self, model_path: str, conf: float = 0.4, iou: float = 0.45):
        self.conf = conf
        self.iou  = iou
        self.input_size = 640
        self.session = ort.InferenceSession(
            model_path, providers=["CPUExecutionProvider"]
        )
        self.input_name  = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def preprocess(self, frame):
        h, w = frame.shape[:2]
        # letterbox resize
        scale = self.input_size / max(h, w)
        nh, nw = int(h * scale), int(w * scale)
        resized = cv2.resize(frame, (nw, nh))
        padded  = np.full((self.input_size, self.input_size, 3), 114, dtype=np.uint8)
        padded[:nh, :nw] = resized
        blob = padded.astype(np.float32) / 255.0
        blob = blob.transpose(2, 0, 1)[np.newaxis]  # BHWC -> BCHW
        return blob, scale, (h, w)

    def postprocess(self, output, scale, orig_shape):
        """
        output shape: (1, 84, 8400)
        84 = 4 box coords + 80 class scores
        """
        preds = output[0].squeeze(0).T  # (8400, 84)
        boxes_xywh = preds[:, :4]
        scores     = preds[:, 4:]
        class_ids  = np.argmax(scores, axis=1)
        confidences = scores[np.arange(len(scores)), class_ids]

        mask = confidences >= self.conf
        boxes_xywh  = boxes_xywh[mask]
        confidences = confidences[mask]
        class_ids   = class_ids[mask]

        if len(boxes_xywh) == 0:
            return []

        # xywh -> xyxy, undo letterbox scale
        x1 = (boxes_xywh[:, 0] - boxes_xywh[:, 2] / 2) / scale
        y1 = (boxes_xywh[:, 1] - boxes_xywh[:, 3] / 2) / scale
        x2 = (boxes_xywh[:, 0] + boxes_xywh[:, 2] / 2) / scale
        y2 = (boxes_xywh[:, 1] + boxes_xywh[:, 3] / 2) / scale

        # clip to frame
        oh, ow = orig_shape
        x1 = np.clip(x1, 0, ow).astype(int)
        y1 = np.clip(y1, 0, oh).astype(int)
        x2 = np.clip(x2, 0, ow).astype(int)
        y2 = np.clip(y2, 0, oh).astype(int)

        # NMS
        boxes_list = [[int(x1[i]), int(y1[i]), int(x2[i]-x1[i]), int(y2[i]-y1[i])]
                      for i in range(len(x1))]
        indices = cv2.dnn.NMSBoxes(
            boxes_list, confidences.tolist(), self.conf, self.iou
        )
        if len(indices) == 0:
            return []

        results = []
        for i in indices.flatten():
            results.append({
                "box":      (int(x1[i]), int(y1[i]), int(x2[i]), int(y2[i])),
                "conf":     float(confidences[i]),
                "class_id": int(class_ids[i]),
            })
        return results

    def detect(self, frame):
        blob, scale, orig_shape = self.preprocess(frame)
        output = self.session.run([self.output_name], {self.input_name: blob})
        return self.postprocess(output, scale, orig_shape)
