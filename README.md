# Smart Parking Management System

AI-powered real-time parking detection using YOLO11n computer vision and ESP32 ultrasonic sensors,
fused through an intelligent confidence-based engine with a live React dashboard.

---

## Architecture

```
                  +------------------+       +-------------------+
                  |  Webcam/DroidCam |       |  ESP32 DevKit V1  |
                  +--------+---------+       +--------+----------+
                           |                          |
                    YOLO11n inference          HC-SR04 x4 sensors
                    Polygon occupancy          Sequential reads
                           |                          |
                           v                          v
                  POST /api/camera-detections   POST /api/sensor-readings
                           |                          |
                           +----------+---------------+
                                      |
                              +-------+-------+
                              | Fusion Engine |
                              |  (backend/)   |
                              +-------+-------+
                                      |
                          +-----------+-----------+
                          |                       |
                   REST + WebSocket           MongoDB
                   FastAPI (port 8000)    (smart_parking DB)
                          |
                   +------+------+
                   | React Dashboard |
                   | (port 5173)     |
                   +-----------------+
```

---

## Project Structure

```
smart-parking/
├── vision/
│   ├── verify_setup.py        # Environment verification (run first)
│   ├── slot_configurator.py   # Click-to-define parking slot polygons
│   ├── detector.py            # YOLO detection + backend POST
│   └── requirements.txt
├── backend/
│   ├── main.py                # FastAPI app, REST + WebSocket
│   ├── fusion.py              # Intelligent data fusion engine
│   ├── .env                   # MongoDB URI, host, port
│   └── requirements.txt
├── firmware/
│   ├── esp32/
│   │   └── smart_parking_esp32.ino   # Arduino sketch
│   └── WIRING.md              # Circuit diagrams + calibration
├── frontend/
│   └── src/
│       ├── components/        # SlotCard, StatsBar, HistoryChart, StatusBar
│       ├── hooks/             # useParking (WebSocket), useHistory (polling)
│       ├── App.jsx
│       └── main.jsx
├── config/
│   └── parking_slots.json     # Slot polygons, camera source, thresholds
└── tests/
    ├── test_fusion.py         # Fusion engine unit tests (9 tests)
    ├── test_integration.py    # End-to-end API integration tests
    ├── evaluate.py            # Accuracy/F1/latency evaluation
    └── reports/
        └── evaluation_report.json
```

---

## Hardware

| Component | Quantity | Purpose |
|---|---|---|
| ESP32 DevKit V1 | 1 | Microcontroller + WiFi |
| HC-SR04 Ultrasonic Sensor | 4 | One per parking slot |
| 1k ohm Resistor | 4 | Voltage divider (ECHO pin) |
| 2k ohm Resistor | 4 | Voltage divider (ECHO pin) |
| Breadboard + jumper wires | - | Connections |
| Laptop webcam or smartphone (DroidCam) | 1 | Camera input |

### GPIO Pin Assignment

| Slot | TRIG | ECHO | Voltage Divider |
|------|------|------|-----------------|
| P1 | GPIO 5 | GPIO 18 | 1k+2k to GND |
| P2 | GPIO 19 | GPIO 21 | 1k+2k to GND |
| P3 | GPIO 22 | GPIO 23 | 1k+2k to GND |
| P4 | GPIO 25 | GPIO 26 | 1k+2k to GND |

> ECHO pins output 5V — voltage divider is mandatory to protect ESP32 GPIO (max 3.3V).

See `firmware/WIRING.md` for full circuit diagram and calibration steps.

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB (local or Atlas)
- Arduino IDE 2.x with ESP32 board support

---

### Phase 1 — Vision Module

```bash
cd smart-parking/vision
pip install -r requirements.txt

# Step 1: verify camera + YOLO work
python verify_setup.py

# Step 2: define parking slot polygons (run once)
python slot_configurator.py
# Click corners of each slot, ENTER to confirm, ESC to redo

# Step 3: run live detection
python detector.py
```

**DroidCam (smartphone camera):**
```bash
python verify_setup.py --source http://192.168.x.x:4747/video
python slot_configurator.py http://192.168.x.x:4747/video
python detector.py --source http://192.168.x.x:4747/video
```

**Vision only (no backend):**
```bash
python detector.py --no-backend
```

---

### Phase 3 — ESP32 Firmware

1. Open `firmware/esp32/smart_parking_esp32.ino` in Arduino IDE
2. Update credentials:
```cpp
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* BACKEND_URL   = "http://<laptop-ip>:8000/api/sensor-readings";
```
3. Install library: Tools > Library Manager > ArduinoJson v6.x
4. Select board: ESP32 Dev Module
5. Upload and open Serial Monitor at 115200 baud to verify readings

---

### Phase 4 — Backend

```bash
cd smart-parking/backend
pip install -r requirements.txt

# Edit .env if needed (default: localhost MongoDB)
python main.py
# API running at http://localhost:8000
# Docs at http://localhost:8000/docs
```

---

### Phase 5 — Frontend Dashboard

```bash
cd smart-parking/frontend
npm install
npm run dev
# Open http://localhost:5173
```

---

### Run Everything Together

```
Terminal 1:  cd backend   && python main.py
Terminal 2:  cd vision    && python detector.py
Terminal 3:  cd frontend  && npm run dev
ESP32:       Flash firmware, monitor Serial at 115200
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/slots` | All slot states from fusion engine |
| GET | `/api/summary` | Total / occupied / free counts |
| POST | `/api/sensor-readings` | Receive ESP32 ultrasonic data |
| POST | `/api/camera-detections` | Receive YOLO camera predictions |
| GET | `/api/history?limit=N` | Historical occupancy records |
| WS | `/ws` | Real-time WebSocket updates |

### POST /api/sensor-readings
```json
{
  "device_id": "ESP32_PARKING_01",
  "timestamp": 123456789,
  "slots": [
    { "id": "P1", "distance": 12.5, "occupied": true },
    { "id": "P2", "distance": 130.0, "occupied": false }
  ]
}
```

### POST /api/camera-detections
```json
{
  "slots": [
    { "id": "P1", "occupied": true,  "confidence": 0.91 },
    { "id": "P2", "occupied": false, "confidence": 0.0  }
  ]
}
```

### WebSocket Message Format
```json
{ "type": "update", "source": "camera", "data": {
    "total": 4, "occupied": 2, "free": 2,
    "slots": [
      { "slot_id": "P1", "occupied": true, "confidence": 0.85, "mode": "hybrid" }
    ]
}}
```

---

## Database Schema (MongoDB)

**Collection: sensor_readings**
```json
{ "device_id": "ESP32_PARKING_01", "timestamp": 123456, "slots": [...], "received_at": 1700000000.0 }
```

**Collection: camera_detections**
```json
{ "slots": [...], "received_at": 1700000000.0 }
```

**Collection: history**
```json
{ "timestamp": 1700000000.0, "occupied": 2, "free": 2, "slots": [...] }
```

---

## Fusion Engine Logic

| Condition | Mode | Confidence |
|---|---|---|
| Camera + Sensor agree | `hybrid` | camera_conf * 0.6 + 0.4 |
| Camera only (fresh) | `camera` | YOLO confidence score |
| Sensor only (fresh) | `sensor` | 0.75 fixed |
| Camera + Sensor disagree | `conflict` | camera_conf * 0.6 |
| No fresh data (> 2s) | `none` | decays by 0.1 |

State only commits after **3 consecutive consistent readings** (temporal stability window).

---

## Performance Results

Evaluated over 200 simulated trials per mode with 10% noise rate:

| Mode | Accuracy | Precision | Recall | F1-Score |
|------|----------|-----------|--------|----------|
| Camera only | ~90% | ~87% | ~93% | ~90% |
| Sensor only | ~89% | ~90% | ~90% | ~90% |
| Hybrid (fused) | ~96% | ~99% | ~94% | ~96% |

### Stress Test (Hybrid mode under degraded conditions)

| Condition | F1-Score |
|---|---|
| Normal (5% noise) | ~100% |
| Low light (15% noise) | ~97% |
| Partial occlusion (25% noise) | ~87% |
| Sensor failure (40% noise) | ~57% |

---

## Running Tests

```bash
# Unit tests (no backend needed)
python tests/test_fusion.py

# Performance evaluation (no backend needed)
python tests/evaluate.py

# Integration tests (requires backend running)
python tests/test_integration.py
```

---

## Configuration

Edit `config/parking_slots.json` to change:

```json
{
  "camera_source": 0,
  "confidence_threshold": 0.4,
  "vehicle_classes": [2, 3, 5, 7],
  "parking_slots": [
    { "id": "P1", "polygon": [[x,y], [x,y], [x,y], [x,y]], "color": [0,255,0] }
  ]
}
```

COCO vehicle class IDs: `2`=car, `3`=motorcycle, `5`=bus, `7`=truck

---

## YOLO Model

- Model: `yolo11n.pt` (YOLO11 nano — pretrained on COCO)
- Auto-downloaded by ultralytics on first run
- No custom training required for prototype
- Future: fine-tune on PKLot / CNRPark+EXT datasets for parking-specific classification

---

## Extending the System

- **More slots:** Add entries to `parking_slots.json`, re-run `slot_configurator.py`
- **Custom model:** Train on PKLot dataset, swap `MODEL_PATH` in `detector.py`
- **Multiple cameras:** Run multiple `detector.py` instances with different `--source`
- **Cloud deployment:** Replace `.env` MongoDB URI with Atlas connection string
