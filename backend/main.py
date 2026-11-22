"""
main.py — FastAPI Backend
Endpoints: sensor readings, camera predictions, parking summary, history
WebSocket: real-time dashboard updates
"""

import os
import json
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from fusion import FusionEngine

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = os.getenv("DB_NAME", "smart_parking")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "parking_slots.json")

# ── Load slot IDs from config ─────────────────────────────────────
with open(CONFIG_PATH) as f:
    _cfg = json.load(f)
SLOT_IDS = [s["id"] for s in _cfg["parking_slots"]]

# ── Global state ──────────────────────────────────────────────────
fusion   = FusionEngine(SLOT_IDS)
db       = None
ws_clients: list[WebSocket] = []


# ── Lifespan (startup/shutdown) ───────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global db
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    await db["slots"].create_index("slot_id")
    await db["history"].create_index("timestamp")
    print(f"[DB] Connected to MongoDB: {DB_NAME}")
    yield
    client.close()


app = FastAPI(title="Smart Parking API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic models ───────────────────────────────────────────────

class SensorSlot(BaseModel):
    id: str
    distance: float
    occupied: bool

class SensorPayload(BaseModel):
    device_id: str
    timestamp: int
    slots: list[SensorSlot]

class CameraSlot(BaseModel):
    id: str
    occupied: bool
    confidence: float = 0.0

class CameraPayload(BaseModel):
    slots: list[CameraSlot]


# ── WebSocket broadcast ───────────────────────────────────────────

async def broadcast(data: dict):
    dead = []
    for ws in ws_clients:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        ws_clients.remove(ws)


# ── Routes ────────────────────────────────────────────────────────

@app.get("/api/slots")
async def get_slots():
    return fusion.summary()


@app.post("/api/sensor-readings")
async def receive_sensor(payload: SensorPayload):
    for slot in payload.slots:
        fusion.update_sensor(slot.id, slot.occupied, slot.distance)

    # Persist to MongoDB
    doc = payload.model_dump()
    doc["received_at"] = time.time()
    await db["sensor_readings"].insert_one(doc)

    summary = fusion.summary()
    await broadcast({"type": "update", "source": "sensor", "data": summary})
    return {"status": "ok"}


@app.post("/api/camera-detections")
async def receive_camera(payload: CameraPayload):
    for slot in payload.slots:
        fusion.update_camera(slot.id, slot.occupied, slot.confidence)

    doc = payload.model_dump()
    doc["received_at"] = time.time()
    await db["camera_detections"].insert_one(doc)

    # Save occupancy snapshot to history
    summary = fusion.summary()
    await db["history"].insert_one({
        "timestamp": time.time(),
        "occupied":  summary["occupied"],
        "free":      summary["free"],
        "slots":     summary["slots"],
    })

    await broadcast({"type": "update", "source": "camera", "data": summary})
    return {"status": "ok"}


@app.get("/api/summary")
async def get_summary():
    return fusion.summary()


@app.get("/api/history")
async def get_history(limit: int = 100):
    cursor = db["history"].find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
    return await cursor.to_list(length=limit)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    ws_clients.append(ws)
    # Send current state immediately on connect
    await ws.send_json({"type": "init", "data": fusion.summary()})
    try:
        while True:
            await ws.receive_text()  # keep alive
    except WebSocketDisconnect:
        ws_clients.remove(ws)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=os.getenv("HOST", "0.0.0.0"),
                port=int(os.getenv("PORT", 8000)), reload=True)
