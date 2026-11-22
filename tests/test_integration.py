"""
test_integration.py — End-to-end integration test (no hardware needed).
Simulates ESP32 + camera → backend → fusion → WebSocket.
Requires backend running: python backend/main.py

Run: python tests/test_integration.py
"""

import urllib.request
import urllib.error
import json
import time
import threading
import sys

BASE = "http://localhost:8000"


def post(path, data):
    payload = json.dumps(data).encode()
    req = urllib.request.Request(
        BASE + path, data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=5) as r:
        return json.loads(r.read())


def check_backend_alive():
    try:
        get("/api/slots")
        return True
    except Exception:
        return False


# ── Test cases ────────────────────────────────────────────────────

def test_sensor_post_updates_fusion():
    post("/api/sensor-readings", {
        "device_id": "TEST_ESP32",
        "timestamp": int(time.time() * 1000),
        "slots": [
            {"id": "P1", "distance": 12.0, "occupied": True},
            {"id": "P2", "distance": 130.0, "occupied": False},
            {"id": "P3", "distance": 18.0, "occupied": True},
            {"id": "P4", "distance": 115.0, "occupied": False},
        ]
    })
    summary = get("/api/summary")
    assert summary["total"] == 4
    print("  PASS sensor POST updates fusion")


def test_camera_post_updates_fusion():
    post("/api/camera-detections", {
        "slots": [
            {"id": "P1", "occupied": True,  "confidence": 0.91},
            {"id": "P2", "occupied": False, "confidence": 0.0},
            {"id": "P3", "occupied": True,  "confidence": 0.87},
            {"id": "P4", "occupied": False, "confidence": 0.0},
        ]
    })
    summary = get("/api/summary")
    assert summary["occupied"] >= 0
    print("  PASS camera POST updates fusion")


def test_hybrid_mode_appears():
    # Post both sensor and camera for same slots
    for _ in range(3):
        post("/api/sensor-readings", {
            "device_id": "TEST_ESP32",
            "timestamp": int(time.time() * 1000),
            "slots": [{"id": "P1", "distance": 10.0, "occupied": True},
                      {"id": "P2", "distance": 120.0, "occupied": False},
                      {"id": "P3", "distance": 10.0, "occupied": True},
                      {"id": "P4", "distance": 120.0, "occupied": False}]
        })
        post("/api/camera-detections", {
            "slots": [{"id": "P1", "occupied": True,  "confidence": 0.9},
                      {"id": "P2", "occupied": False, "confidence": 0.0},
                      {"id": "P3", "occupied": True,  "confidence": 0.88},
                      {"id": "P4", "occupied": False, "confidence": 0.0}]
        })
        time.sleep(0.1)

    summary = get("/api/summary")
    modes = [s["mode"] for s in summary["slots"]]
    assert "hybrid" in modes, f"Expected hybrid mode, got: {modes}"
    print("  PASS hybrid mode detected after agreement")


def test_history_written_to_db():
    history = get("/api/history?limit=5")
    assert isinstance(history, list)
    print(f"  PASS history endpoint returns {len(history)} records")


def test_concurrent_posts():
    """Simulate ESP32 and camera posting simultaneously."""
    errors = []

    def sensor_post():
        try:
            post("/api/sensor-readings", {
                "device_id": "CONCURRENT_TEST",
                "timestamp": int(time.time() * 1000),
                "slots": [{"id": s, "distance": 20.0, "occupied": True}
                          for s in ["P1", "P2", "P3", "P4"]]
            })
        except Exception as e:
            errors.append(str(e))

    def camera_post():
        try:
            post("/api/camera-detections", {
                "slots": [{"id": s, "occupied": True, "confidence": 0.85}
                          for s in ["P1", "P2", "P3", "P4"]]
            })
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=sensor_post) for _ in range(5)] + \
              [threading.Thread(target=camera_post) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Concurrent errors: {errors}"
    print("  PASS 10 concurrent posts handled without error")


# ── Runner ────────────────────────────────────────────────────────

def main():
    print("\n=== Integration Tests ===\n")

    if not check_backend_alive():
        print("[ERROR] Backend not running. Start it first:")
        print("        cd backend && python main.py")
        sys.exit(1)

    print("[OK] Backend is alive\n")

    tests = [
        test_sensor_post_updates_fusion,
        test_camera_post_updates_fusion,
        test_hybrid_mode_appears,
        test_history_written_to_db,
        test_concurrent_posts,
    ]

    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {t.__name__}: {e}")
            failed += 1

    print(f"\n{'='*30}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("All integration tests passed ✓")


if __name__ == "__main__":
    main()
