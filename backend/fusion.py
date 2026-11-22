"""
fusion.py — Intelligent Occupancy Fusion Engine
Combines camera (YOLO) predictions and ultrasonic sensor readings.
Supports camera-only, sensor-only, and hybrid modes.
"""

from dataclasses import dataclass, field
from typing import Optional
from collections import deque
import time

# Confidence weights
CAMERA_WEIGHT  = 0.6
SENSOR_WEIGHT  = 0.4

# Temporal stability: require N consistent readings before changing state
STABILITY_WINDOW = 3

# Max age of a reading before it's considered stale (seconds)
CAMERA_STALE_SEC = 2.0
SENSOR_STALE_SEC = 2.0


@dataclass
class SlotReading:
    slot_id: str
    camera_occupied: Optional[bool] = None
    camera_confidence: float = 0.0
    camera_ts: float = 0.0
    sensor_occupied: Optional[bool] = None
    sensor_distance: float = -1.0
    sensor_ts: float = 0.0


@dataclass
class FusionState:
    slot_id: str
    occupied: bool = False
    confidence: float = 0.0
    mode: str = "none"           # camera | sensor | hybrid | conflict | none
    stable_count: int = 0
    history: deque = field(default_factory=lambda: deque(maxlen=STABILITY_WINDOW))
    entry_time: Optional[float] = None   # when slot became occupied
    last_free_time: Optional[float] = None  # when slot last became free


class FusionEngine:
    def __init__(self, slot_ids: list[str]):
        self.states: dict[str, FusionState] = {sid: FusionState(sid) for sid in slot_ids}
        self.readings: dict[str, SlotReading] = {sid: SlotReading(sid) for sid in slot_ids}

    # ── Ingest updates ────────────────────────────────────────────

    def update_camera(self, slot_id: str, occupied: bool, confidence: float):
        r = self.readings[slot_id]
        r.camera_occupied = occupied
        r.camera_confidence = confidence
        r.camera_ts = time.time()
        self._fuse(slot_id)

    def update_sensor(self, slot_id: str, occupied: bool, distance: float):
        r = self.readings[slot_id]
        r.sensor_occupied = occupied
        r.sensor_distance = distance
        r.sensor_ts = time.time()
        self._fuse(slot_id)

    # ── Core fusion logic ─────────────────────────────────────────

    def _fuse(self, slot_id: str):
        r = self.readings[slot_id]
        s = self.states[slot_id]
        now = time.time()

        camera_fresh = r.camera_ts > 0 and (now - r.camera_ts) < CAMERA_STALE_SEC
        sensor_fresh = r.sensor_ts > 0 and (now - r.sensor_ts) < SENSOR_STALE_SEC

        # ── Determine mode ────────────────────────────────────────
        if camera_fresh and sensor_fresh:
            if r.camera_occupied == r.sensor_occupied:
                # Agreement → high confidence hybrid
                occupied   = r.camera_occupied
                confidence = min(1.0, r.camera_confidence * CAMERA_WEIGHT +
                                      SENSOR_WEIGHT)
                mode = "hybrid"
            else:
                # Conflict → trust camera more but flag it
                occupied   = r.camera_occupied
                confidence = r.camera_confidence * CAMERA_WEIGHT
                mode = "conflict"

        elif camera_fresh:
            occupied   = r.camera_occupied
            confidence = r.camera_confidence
            mode = "camera"

        elif sensor_fresh:
            occupied   = r.sensor_occupied
            confidence = 0.75  # sensor alone is reliable but no confidence score
            mode = "sensor"

        else:
            # No fresh data — keep last known state, drop confidence
            s.confidence = max(0.0, s.confidence - 0.1)
            s.mode = "none"
            return

        # ── Temporal stability check ──────────────────────────────
        s.history.append(occupied)
        if len(s.history) == STABILITY_WINDOW:
            # Only commit if all recent readings agree
            if all(v == occupied for v in s.history):
                prev_occupied = s.occupied
                s.occupied   = occupied
                s.confidence = confidence
                s.mode       = mode
                # Track entry/exit times
                if occupied and not prev_occupied:
                    s.entry_time = now
                elif not occupied and prev_occupied:
                    s.last_free_time = now
                    s.entry_time = None
        else:
            # Not enough history yet — use raw result
            prev_occupied = s.occupied
            s.occupied   = occupied
            s.confidence = confidence
            s.mode       = mode
            if occupied and not prev_occupied:
                s.entry_time = now
            elif not occupied and prev_occupied:
                s.last_free_time = now
                s.entry_time = None

    # ── Query ─────────────────────────────────────────────────────

    def get_state(self, slot_id: str) -> dict:
        s = self.states[slot_id]
        r = self.readings[slot_id]
        now = time.time()
        duration = round(now - s.entry_time) if s.occupied and s.entry_time else None
        camera_fresh = r.camera_ts > 0 and (now - r.camera_ts) < CAMERA_STALE_SEC
        sensor_fresh = r.sensor_ts > 0 and (now - r.sensor_ts) < SENSOR_STALE_SEC
        return {
            "slot_id":        s.slot_id,
            "occupied":       s.occupied,
            "confidence":     round(s.confidence, 3),
            "mode":           s.mode,
            "entry_time":     round(s.entry_time) if s.entry_time else None,
            "duration_sec":   duration,
            "last_free_time": round(s.last_free_time) if s.last_free_time else None,
            "camera": {
                "active":   camera_fresh,
                "occupied": r.camera_occupied,
                "confidence": round(r.camera_confidence, 2) if camera_fresh else None,
            },
            "sensor": {
                "active":   sensor_fresh,
                "occupied": r.sensor_occupied if sensor_fresh else None,
                "distance": round(r.sensor_distance, 1) if sensor_fresh else None,
            },
        }

    def get_all_states(self) -> list[dict]:
        return [self.get_state(sid) for sid in self.states]

    def summary(self) -> dict:
        states = self.get_all_states()
        occupied = sum(1 for s in states if s["occupied"])
        return {
            "total":    len(states),
            "occupied": occupied,
            "free":     len(states) - occupied,
            "slots":    states,
        }
