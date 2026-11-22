"""
detector.py - ONNX-based detector (no torch required)
Run: python detector.py
     python detector.py --source http://192.168.x.x:4747/video
     python detector.py --no-backend
"""

import cv2
import json
import numpy as np
import argparse
import os
import time
import threading
import urllib.request

from yolo_onnx import YOLOOnnx

CONFIG_PATH  = os.path.join(os.path.dirname(__file__), "..", "config", "parking_slots.json")
MODEL_PATH   = os.path.join(os.path.dirname(__file__), "yolo11n.onnx")
BACKEND_URL  = "http://localhost:8000/api/camera-detections"


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def point_in_polygon(point, polygon):
    pts = np.array(polygon, np.int32)
    return cv2.pointPolygonTest(pts, point, False) >= 0


def box_intersects_polygon(box, polygon):
    x1, y1, x2, y2 = box
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    return any(point_in_polygon(p, polygon)
               for p in [(cx, cy), (x1, y1), (x2, y1), (x1, y2), (x2, y2)])


def post_to_backend(slots_data):
    try:
        payload = json.dumps({"slots": slots_data}).encode()
        req = urllib.request.Request(
            BACKEND_URL, data=payload,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        urllib.request.urlopen(req, timeout=1)
    except Exception:
        pass


def draw_slot(frame, slot, occupied):
    pts = np.array(slot["polygon"], np.int32).reshape((-1, 1, 2))
    color = (0, 0, 255) if occupied else (0, 255, 0)
    overlay = frame.copy()
    cv2.fillPoly(overlay, [pts], color)
    cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)
    cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)
    x, y = slot["polygon"][0]
    cv2.putText(frame, f"{slot['id']}: {'OCC' if occupied else 'FREE'}",
                (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)


def draw_detection(frame, box, label, conf):
    x1, y1, x2, y2 = box
    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 200, 0), 2)
    cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 200, 0), 2)


def draw_summary(frame, total, occupied, fps):
    cv2.rectangle(frame, (0, 0), (340, 70), (0, 0, 0), -1)
    cv2.putText(frame, f"Total:{total}  Occ:{occupied}  Free:{total-occupied}",
                (8, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    cv2.putText(frame, f"FPS: {fps:.1f}", (8, 55),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)


def run(source, use_backend):
    config          = load_config()
    slots           = config["parking_slots"]
    vehicle_classes = config["vehicle_classes"]
    vehicle_labels  = config["vehicle_labels"]
    conf_thresh     = config["confidence_threshold"]

    print(f"[INFO] Loading ONNX model: {MODEL_PATH}")
    model = YOLOOnnx(MODEL_PATH, conf=conf_thresh)
    print("[INFO] Model ready.")

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open source: {source}")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  config["frame_width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config["frame_height"])
    print("[INFO] Camera opened. Press Q to quit.")

    prev_time    = time.time()
    last_post_ts = 0
    POST_INTERVAL = 0.5

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        detections = model.detect(frame)

        slot_occupied = {s["id"]: False for s in slots}
        slot_max_conf = {s["id"]: 0.0   for s in slots}

        for det in detections:
            if det["class_id"] not in vehicle_classes:
                continue
            box   = det["box"]
            conf  = det["conf"]
            label = vehicle_labels.get(str(det["class_id"]), "vehicle")
            draw_detection(frame, box, label, conf)

            for slot in slots:
                if box_intersects_polygon(box, slot["polygon"]):
                    slot_occupied[slot["id"]] = True
                    slot_max_conf[slot["id"]] = max(slot_max_conf[slot["id"]], conf)

        for slot in slots:
            draw_slot(frame, slot, slot_occupied[slot["id"]])

        now = time.time()
        fps = 1.0 / (now - prev_time + 1e-6)
        prev_time = now

        occupied_count = sum(slot_occupied.values())
        draw_summary(frame, len(slots), occupied_count, fps)

        if use_backend and (now - last_post_ts) >= POST_INTERVAL:
            last_post_ts = now
            slots_data = [{"id": sid, "occupied": slot_occupied[sid],
                           "confidence": slot_max_conf[sid]} for sid in slot_occupied]
            threading.Thread(target=post_to_backend, args=(slots_data,), daemon=True).start()

        cv2.imshow("Smart Parking - Live Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source",     default=None)
    parser.add_argument("--no-backend", action="store_true")
    args = parser.parse_args()

    config = load_config()
    source = args.source if args.source else config.get("camera_source", 0)
    try:
        source = int(source)
    except (ValueError, TypeError):
        pass

    run(source, use_backend=not args.no_backend)
