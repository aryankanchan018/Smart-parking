"""
test_backend.py — Verify all API endpoints without hardware.
Run backend first: cd backend && python main.py
Then: python test_backend.py
"""

import urllib.request
import urllib.error
import json
import sys

BASE = "http://localhost:8000"

def post(path, data):
    payload = json.dumps(data).encode()
    req = urllib.request.Request(
        BASE + path,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=3) as r:
        return json.loads(r.read())

def get(path):
    with urllib.request.urlopen(BASE + path, timeout=3) as r:
        return json.loads(r.read())

def test(name, fn):
    try:
        result = fn()
        print(f"  [PASS] {name}: {result}")
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")

print("\n=== Backend API Tests ===\n")

test("GET /api/slots", lambda: get("/api/slots"))

test("POST /api/sensor-readings", lambda: post("/api/sensor-readings", {
    "device_id": "TEST_ESP32",
    "timestamp": 12345,
    "slots": [
        {"id": "P1", "distance": 15.0, "occupied": True},
        {"id": "P2", "distance": 120.0, "occupied": False},
        {"id": "P3", "distance": 20.0, "occupied": True},
        {"id": "P4", "distance": 110.0, "occupied": False},
    ]
}))

test("POST /api/camera-detections", lambda: post("/api/camera-detections", {
    "slots": [
        {"id": "P1", "occupied": True,  "confidence": 0.91},
        {"id": "P2", "occupied": False, "confidence": 0.0},
        {"id": "P3", "occupied": True,  "confidence": 0.85},
        {"id": "P4", "occupied": False, "confidence": 0.0},
    ]
}))

test("GET /api/summary", lambda: get("/api/summary"))
test("GET /api/history", lambda: get("/api/history?limit=5"))

print("\n=== Done ===\n")
