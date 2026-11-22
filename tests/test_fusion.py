"""
test_fusion.py — Unit tests for the fusion engine.
Run: python -m pytest tests/test_fusion.py -v
  or: python tests/test_fusion.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from fusion import FusionEngine

SLOTS = ["P1", "P2", "P3", "P4"]


def make_engine():
    return FusionEngine(SLOTS)


# ── Helpers ───────────────────────────────────────────────────────

def push_camera(engine, slot_id, occupied, conf=0.9, n=3):
    for _ in range(n):
        engine.update_camera(slot_id, occupied, conf)

def push_sensor(engine, slot_id, occupied, dist=15.0, n=3):
    for _ in range(n):
        engine.update_sensor(slot_id, occupied, dist)


# ── Tests ─────────────────────────────────────────────────────────

def test_camera_only_occupied():
    e = make_engine()
    push_camera(e, "P1", True, conf=0.85)
    s = e.get_state("P1")
    assert s["occupied"] is True
    assert s["mode"] == "camera"
    print("PASS test_camera_only_occupied")


def test_camera_only_free():
    e = make_engine()
    push_camera(e, "P1", False, conf=0.0)
    s = e.get_state("P1")
    assert s["occupied"] is False
    assert s["mode"] == "camera"
    print("PASS test_camera_only_free")


def test_sensor_only_occupied():
    e = make_engine()
    push_sensor(e, "P2", True, dist=12.0)
    s = e.get_state("P2")
    assert s["occupied"] is True
    assert s["mode"] == "sensor"
    print("PASS test_sensor_only_occupied")


def test_hybrid_agreement():
    e = make_engine()
    for _ in range(3):
        e.update_camera("P3", True, 0.92)
        e.update_sensor("P3", True, 10.0)
    s = e.get_state("P3")
    assert s["occupied"] is True
    assert s["mode"] == "hybrid"
    assert s["confidence"] > 0.5
    print("PASS test_hybrid_agreement")


def test_conflict_trusts_camera():
    e = make_engine()
    for _ in range(3):
        e.update_camera("P4", True,  0.88)
        e.update_sensor("P4", False, 120.0)
    s = e.get_state("P4")
    assert s["occupied"] is True   # camera wins
    assert s["mode"] == "conflict"
    print("PASS test_conflict_trusts_camera")


def test_temporal_stability_requires_3():
    """State should not flip on a single contradicting reading."""
    e = make_engine()
    push_camera(e, "P1", True, n=3)   # establish occupied
    e.update_camera("P1", False, 0.0) # single contradicting read
    s = e.get_state("P1")
    assert s["occupied"] is True      # still occupied — not enough history to flip
    print("PASS test_temporal_stability_requires_3")


def test_stale_data_drops_confidence():
    e = make_engine()
    push_camera(e, "P1", True, n=3)
    # Manually age the timestamp
    e.readings["P1"].camera_ts = time.time() - 10.0
    e.readings["P1"].sensor_ts = 0.0
    e._fuse("P1")
    s = e.get_state("P1")
    assert s["confidence"] < 0.5 or s["mode"] == "none"
    print("PASS test_stale_data_drops_confidence")


def test_summary_counts():
    e = make_engine()
    push_camera(e, "P1", True,  n=3)
    push_camera(e, "P2", False, n=3)
    push_camera(e, "P3", True,  n=3)
    push_camera(e, "P4", False, n=3)
    sm = e.summary()
    assert sm["total"]    == 4
    assert sm["occupied"] == 2
    assert sm["free"]     == 2
    print("PASS test_summary_counts")


def test_all_slots_free_on_init():
    e = make_engine()
    sm = e.summary()
    assert sm["occupied"] == 0
    assert sm["free"]     == 4
    print("PASS test_all_slots_free_on_init")


# ── Runner ────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_all_slots_free_on_init,
        test_camera_only_occupied,
        test_camera_only_free,
        test_sensor_only_occupied,
        test_hybrid_agreement,
        test_conflict_trusts_camera,
        test_temporal_stability_requires_3,
        test_stale_data_drops_confidence,
        test_summary_counts,
    ]

    passed = failed = 0
    print("\n=== Fusion Engine Unit Tests ===\n")
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR {t.__name__}: {e}")
            failed += 1

    print(f"\n{'='*34}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    if failed == 0:
        print("All tests passed - OK")
