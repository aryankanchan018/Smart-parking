# ESP32 Wiring Diagram & Calibration Guide

## Voltage Divider (REQUIRED on every ECHO pin)
HC-SR04 outputs 5V on ECHO. ESP32 GPIO max is 3.3V.
Without a divider you WILL damage the ESP32.

```
HC-SR04 ECHO (5V) ───┬─── 1kΩ ───── ESP32 GPIO (3.3V safe)
                     │
                    2kΩ
                     │
                    GND
```
Output voltage = 5V × (2kΩ / (1kΩ + 2kΩ)) = 3.33V ✓

---

## Full Wiring Table

```
┌──────────────┬─────────────────────────────────────────────────────┐
│ HC-SR04 Pin  │ Connect To                                          │
├──────────────┼─────────────────────────────────────────────────────┤
│ VCC          │ ESP32 VIN (5V from USB)                             │
│ GND          │ ESP32 GND                                           │
│ TRIG         │ ESP32 GPIO (direct, 3.3V output is enough to trigger)│
│ ECHO         │ Voltage divider → ESP32 GPIO                        │
└──────────────┴─────────────────────────────────────────────────────┘
```

## Per-Slot GPIO Assignment

```
┌──────┬───────────┬───────────┬──────────────────────────────────┐
│ Slot │ TRIG GPIO │ ECHO GPIO │ Voltage Divider                  │
├──────┼───────────┼───────────┼──────────────────────────────────┤
│  P1  │   GPIO 5  │  GPIO 18  │ ECHO→1kΩ→GPIO18, midpoint→2kΩ→GND│
│  P2  │  GPIO 19  │  GPIO 21  │ ECHO→1kΩ→GPIO21, midpoint→2kΩ→GND│
│  P3  │  GPIO 22  │  GPIO 23  │ ECHO→1kΩ→GPIO23, midpoint→2kΩ→GND│
│  P4  │  GPIO 25  │  GPIO 26  │ ECHO→1kΩ→GPIO26, midpoint→2kΩ→GND│
└──────┴───────────┴───────────┴──────────────────────────────────┘
```

## Breadboard Layout (Top View)

```
ESP32 DevKit V1
┌─────────────────────────────────┐
│ 3V3  GND  5  18  19  21  22  23 │  ← Left side pins used
│                                 │
│ VIN  GND  25  26               │  ← Right side pins used
└─────────────────────────────────┘

Power Rail:
  ESP32 VIN ──── Breadboard (+) rail  ──── all HC-SR04 VCC
  ESP32 GND ──── Breadboard (-) rail  ──── all HC-SR04 GND + divider GNDs

Sensor placement:
  Mount each HC-SR04 facing DOWN into the parking slot from above
  Recommended height: 20–40 cm above ground
  Ensure sensor faces flat ground (not angled)
```

---

## Calibration Procedure

### Step 1 — Find empty slot distance
1. Flash firmware, open Arduino Serial Monitor at 115200 baud
2. Ensure all slots are EMPTY
3. Note the distance readings (should be 80–200 cm depending on mount height)

### Step 2 — Find occupied slot distance
1. Park a vehicle in slot P1
2. Note the distance reading (should be 5–40 cm)

### Step 3 — Set threshold
In `smart_parking_esp32.ino`, update:
```cpp
const float OCCUPIED_THRESHOLD_CM = 50.0;
```
Set to a value between your empty and occupied readings.
Example: empty=120cm, occupied=15cm → threshold=50cm is safe.

### Step 4 — Verify all 4 slots
Park/unpark vehicles and confirm Serial output shows correct occupied/free status.

---

## Common Issues

| Problem | Cause | Fix |
|---------|-------|-----|
| Distance always -1 | Wiring error or timeout | Check TRIG/ECHO connections |
| ESP32 resets randomly | 5V on GPIO | Add voltage divider on ECHO |
| All slots show occupied | Threshold too high | Lower OCCUPIED_THRESHOLD_CM |
| Crosstalk between sensors | Sensors firing simultaneously | Already fixed: sequential reads + 60ms delay |
| WiFi not connecting | Wrong credentials | Update WIFI_SSID / WIFI_PASSWORD in .ino |

---

## Arduino IDE Setup

1. Install Arduino IDE 2.x
2. Add ESP32 board: File → Preferences → Additional Board URLs:
   `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
3. Tools → Board Manager → search "esp32" → install "esp32 by Espressif"
4. Install library: Tools → Library Manager → search "ArduinoJson" → install v6.x
5. Select board: Tools → Board → ESP32 Arduino → ESP32 Dev Module
6. Select port: Tools → Port → (your COM port)
7. Upload speed: 115200
