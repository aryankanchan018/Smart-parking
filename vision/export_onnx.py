"""
export_onnx.py — Export YOLO11n to ONNX format.
Run from D: drive: python d:\smart-parking\vision\export_onnx.py
"""
import sys
import os

out_path = r"d:\smart-parking\vision\yolo11n.onnx"

print("[1/3] Loading YOLO11n via ultralytics...")
from ultralytics import YOLO
model = YOLO("yolo11n.pt")  # auto-downloads if not present

print("[2/3] Exporting to ONNX...")
model.export(format="onnx", imgsz=640, simplify=True)

# ultralytics saves as yolo11n.onnx in current dir
src = os.path.join(os.getcwd(), "yolo11n.onnx")
if os.path.exists(src) and src != out_path:
    import shutil
    shutil.move(src, out_path)
    print(f"[3/3] Moved to {out_path}")
elif os.path.exists(out_path):
    print(f"[3/3] Saved to {out_path}")
else:
    print(f"[3/3] Check current dir for yolo11n.onnx and move to {out_path}")

print("Done. ONNX model ready.")
