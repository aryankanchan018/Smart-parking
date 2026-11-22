"""
verify_setup.py - Verifies camera + ONNX model without torch.
Run: python verify_setup.py
     python verify_setup.py --source http://192.168.x.x:4747/video
"""

import sys
import argparse
import os

def check_imports():
    print("[1/4] Checking imports...")
    try:
        import cv2
        print(f"      OpenCV: {cv2.__version__} OK")
    except ImportError:
        print("      [FAIL] opencv-python not installed.")
        sys.exit(1)
    try:
        import numpy as np
        print(f"      NumPy: {np.__version__} OK")
    except ImportError:
        print("      [FAIL] numpy not installed.")
        sys.exit(1)
    try:
        import onnxruntime as ort
        print(f"      onnxruntime: {ort.__version__} OK")
        print(f"      Providers: {ort.get_available_providers()}")
    except ImportError:
        print("      [FAIL] onnxruntime not installed. Run: python -m pip install onnxruntime")
        sys.exit(1)


def check_model():
    model_path = os.path.join(os.path.dirname(__file__), "yolo11n.onnx")
    print(f"\n[2/4] Checking ONNX model: {model_path}")
    if not os.path.exists(model_path):
        print(f"      [FAIL] Model not found at {model_path}")
        print("      Run: python export_onnx.py  (from d:\\ drive)")
        sys.exit(1)
    size_mb = os.path.getsize(model_path) / 1024 / 1024
    print(f"      Model found: {size_mb:.1f} MB OK")
    return model_path


def check_camera(source):
    import cv2
    print(f"\n[3/4] Checking camera source: {source}")
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"      [FAIL] Cannot open: {source}")
        if isinstance(source, str):
            print("      - Ensure DroidCam app is running on phone")
            print("      - Ensure phone and laptop are on same WiFi")
            print("      - Try opening the URL in a browser first")
        else:
            print("      - Try source 1 instead of 0")
        sys.exit(1)
    ret, frame = cap.read()
    cap.release()
    if not ret or frame is None:
        print("      [FAIL] Camera opened but no frame received.")
        sys.exit(1)
    h, w = frame.shape[:2]
    print(f"      Camera OK - Resolution: {w}x{h}")
    return frame


def check_inference(model_path, frame):
    print("\n[4/4] Running test inference...")
    from yolo_onnx import YOLOOnnx
    model = YOLOOnnx(model_path, conf=0.4)
    results = model.detect(frame)
    print(f"      Inference OK - Detections in test frame: {len(results)}")
    print("\n[PASS] All checks passed. You can now run:")
    print("       python slot_configurator.py   (define slot polygons once)")
    print("       python detector.py            (start live detection)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=None)
    args = parser.parse_args()

    check_imports()
    model_path = check_model()

    import json
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "parking_slots.json")
    with open(config_path) as f:
        cfg = json.load(f)

    source = args.source if args.source else cfg.get("camera_source", 0)
    try:
        source = int(source)
    except (ValueError, TypeError):
        pass

    frame = check_camera(source)
    check_inference(model_path, frame)
