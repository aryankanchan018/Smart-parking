"""
Slot Configurator - Run this ONCE to define parking slot polygons.
Click corners of each slot polygon, press ENTER to confirm, ESC to redo.
Saves coordinates to config/parking_slots.json.
"""

import cv2
import json
import numpy as np
import sys
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "parking_slots.json")
SLOT_IDS = ["P1", "P2", "P3", "P4"]
COLORS = [[0, 255, 0], [255, 165, 0], [0, 165, 255], [255, 0, 255]]

current_points = []
frame_copy = None


def mouse_callback(event, x, y, flags, param):
    global current_points, frame_copy
    if event == cv2.EVENT_LBUTTONDOWN:
        current_points.append([x, y])
        cv2.circle(frame_copy, (x, y), 5, (0, 0, 255), -1)
        if len(current_points) > 1:
            cv2.line(frame_copy, tuple(current_points[-2]), tuple(current_points[-1]), (0, 0, 255), 2)
        cv2.imshow("Slot Configurator", frame_copy)


def draw_slot(frame, points, label, color):
    if len(points) >= 2:
        pts = np.array(points, np.int32)
        cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)
        cv2.putText(frame, label, tuple(points[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)


def configure_slots(camera_source):
    global current_points, frame_copy

    cap = cv2.VideoCapture(camera_source)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera source: {camera_source}")
        sys.exit(1)

    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("[ERROR] Failed to capture frame.")
        sys.exit(1)

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    confirmed_slots = []
    cv2.namedWindow("Slot Configurator")
    cv2.setMouseCallback("Slot Configurator", mouse_callback)

    for i, slot_id in enumerate(SLOT_IDS):
        current_points = []
        print(f"\n[INFO] Define polygon for {slot_id}. Click corners, press ENTER to confirm, ESC to redo.")

        while True:
            frame_copy = frame.copy()
            # Draw already confirmed slots
            for s in confirmed_slots:
                draw_slot(frame_copy, s["polygon"], s["id"], s["color"])
            # Draw current in-progress points
            for p in current_points:
                cv2.circle(frame_copy, tuple(p), 5, (0, 0, 255), -1)
            if len(current_points) > 1:
                pts = np.array(current_points, np.int32)
                cv2.polylines(frame_copy, [pts], isClosed=False, color=(0, 0, 255), thickness=2)

            cv2.putText(frame_copy, f"Defining: {slot_id} | Points: {len(current_points)} | ENTER=confirm ESC=redo",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imshow("Slot Configurator", frame_copy)

            key = cv2.waitKey(1) & 0xFF
            if key == 13 and len(current_points) >= 3:  # ENTER
                confirmed_slots.append({
                    "id": slot_id,
                    "polygon": current_points.copy(),
                    "color": COLORS[i]
                })
                print(f"[OK] {slot_id} confirmed with {len(current_points)} points.")
                break
            elif key == 27:  # ESC
                current_points = []
                print(f"[INFO] Redo {slot_id}.")

    cv2.destroyAllWindows()

    config["parking_slots"] = confirmed_slots
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    print(f"\n[SAVED] Slot coordinates saved to {CONFIG_PATH}")


if __name__ == "__main__":
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    src = cfg.get("camera_source", 0)
    # Allow DroidCam URL override: python slot_configurator.py http://192.168.x.x:4747/video
    if len(sys.argv) > 1:
        src = sys.argv[1]
        try:
            src = int(src)
        except ValueError:
            pass
    configure_slots(src)
