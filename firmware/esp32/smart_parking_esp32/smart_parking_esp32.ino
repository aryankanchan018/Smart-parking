/*
  smart_parking_esp32.ino
  ESP32 DevKit V1
  - 4x HC-SR04 ultrasonic sensors
  - 4x Red LEDs (occupied indicators)
  - 1x Servo motor (gate control)
  - HTTP POST to backend

  WIRING:
  ┌──────┬───────────┬───────────┬──────────────────────────────────┐
  │ Slot │ TRIG GPIO │ ECHO GPIO │ Voltage Divider                  │
  ├──────┼───────────┼───────────┼──────────────────────────────────┤
  │  P1  │  GPIO 5   │  GPIO 18  │ ECHO→1kΩ→GPIO18, mid→2kΩ→GND   │
  │  P2  │  GPIO 19  │  GPIO 21  │ ECHO→1kΩ→GPIO21, mid→2kΩ→GND   │
  │  P3  │  GPIO 22  │  GPIO 23  │ ECHO→1kΩ→GPIO23, mid→2kΩ→GND   │
  │  P4  │  GPIO 25  │  GPIO 26  │ ECHO→1kΩ→GPIO26, mid→2kΩ→GND   │
  └──────┴───────────┴───────────┴──────────────────────────────────┘

  LEDs (220Ω resistor in series):
    P1 LED → GPIO 13
    P2 LED → GPIO 12
    P3 LED → GPIO 14
    P4 LED → GPIO 27

  Servo (gate):
    Signal → GPIO 4
    VCC    → VIN (5V)
    GND    → GND

  Gate logic:
    Any slot free  → gate OPEN  (90°)
    All slots full → gate CLOSE (0°)
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// ── WiFi credentials (tries each in order) ──────────────────────
const char* WIFI_SSIDS[]     = {"Kanchan HomeNet", "AJ",         "Students"};
const char* WIFI_PASSWORDS[] = {"NoPwd@250304",    "55575557",   "00000000"};
const int   WIFI_COUNT       = 3;

// ── Backend endpoint ──────────────────────────────────────────────
const char* BACKEND_URL = "http://192.168.31.54:8000/api/sensor-readings";

// ── Sensor pins ───────────────────────────────────────────────────
const int NUM_SLOTS = 4;
const int TRIG_PINS[NUM_SLOTS] = {5,  19, 22, 25};
const int ECHO_PINS[NUM_SLOTS] = {18, 21, 23, 26};
const char* SLOT_IDS[NUM_SLOTS] = {"P1", "P2", "P3", "P4"};

// ── LED pins (one per slot) ───────────────────────────────────────
const int LED_PINS[NUM_SLOTS] = {13, 12, 14, 27};

// ── Servo ─────────────────────────────────────────────────────────
const int SERVO_PIN   = 4;
const int GATE_OPEN   = 180;  // degrees — gate open (inner direction)
const int GATE_CLOSED = 90;   // degrees — gate closed (all full)
Servo gateServo;

// ── Threshold & timing ────────────────────────────────────────────
const float OCCUPIED_MIN_CM       = 1.5;   // min range
const float OCCUPIED_MAX_CM       = 15.0;  // max range
const int   SENSOR_DELAY_MS       = 0;    // no delay
const int   PUBLISH_INTERVAL_MS   = 300;

unsigned long lastPublish = 0;

// ─────────────────────────────────────────────────────────────────
float measureDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000);
  if (duration == 0) return -1.0;
  return (duration * 0.0343) / 2.0;
}

// ─────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  // Sensor pins
  for (int i = 0; i < NUM_SLOTS; i++) {
    pinMode(TRIG_PINS[i], OUTPUT);
    pinMode(ECHO_PINS[i], INPUT);
    digitalWrite(TRIG_PINS[i], LOW);
  }

  // LED pins
  for (int i = 0; i < NUM_SLOTS; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    digitalWrite(LED_PINS[i], LOW);
  }

  // Servo — start open
  gateServo.attach(SERVO_PIN);
  gateServo.write(GATE_OPEN);

  // WiFi
  Serial.println("\n[BOOT] Smart Parking ESP32");
  for (int n = 0; n < WIFI_COUNT; n++) {
    Serial.print("[WiFi] Trying: ");
    Serial.println(WIFI_SSIDS[n]);
    WiFi.begin(WIFI_SSIDS[n], WIFI_PASSWORDS[n]);
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
      delay(500);
      Serial.print(".");
      attempts++;
    }
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("\n[WiFi] Connected to " + String(WIFI_SSIDS[n]) + " IP: " + WiFi.localIP().toString());
      break;
    }
    Serial.println(" failed.");
    WiFi.disconnect();
  }
  if (WiFi.status() != WL_CONNECTED)
    Serial.println("[WiFi] All networks failed — Serial only mode");
}

// ─────────────────────────────────────────────────────────────────
void loop() {
  unsigned long now = millis();
  if (now - lastPublish < PUBLISH_INTERVAL_MS) return;
  lastPublish = now;

  float distances[NUM_SLOTS];
  bool  occupied[NUM_SLOTS];
  int   occupiedCount = 0;

  // Read sensors + update LEDs
  for (int i = 0; i < NUM_SLOTS; i++) {
    distances[i] = measureDistance(TRIG_PINS[i], ECHO_PINS[i]);
    occupied[i]  = (distances[i] >= OCCUPIED_MIN_CM && distances[i] <= OCCUPIED_MAX_CM);
    digitalWrite(LED_PINS[i], occupied[i] ? HIGH : LOW);
    if (occupied[i]) occupiedCount++;
  }

  // Gate control — close only when ALL slots full
  bool allFull = (occupiedCount == NUM_SLOTS);
  gateServo.write(allFull ? GATE_CLOSED : GATE_OPEN);
  // Simple serial output
  for (int i = 0; i < NUM_SLOTS; i++) {
    Serial.print(SLOT_IDS[i]); Serial.print(":");
    if (distances[i] < 0) Serial.print("NO_SENSOR  ");
    else { Serial.print(distances[i],1); Serial.print("cm "); Serial.print(occupied[i] ? "OCC  " : "FREE  "); }
  }
  Serial.println(allFull ? "| GATE:CLOSED" : "| GATE:OPEN");

  // Build JSON
  StaticJsonDocument<512> doc;
  doc["device_id"] = "ESP32_PARKING_01";
  doc["timestamp"] = now;
  JsonArray slots = doc.createNestedArray("slots");
  for (int i = 0; i < NUM_SLOTS; i++) {
    JsonObject slot = slots.createNestedObject();
    slot["id"]       = SLOT_IDS[i];
    slot["distance"] = distances[i];
    slot["occupied"] = occupied[i];
  }

  String payload;
  serializeJson(doc, payload);

  // POST to backend
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(BACKEND_URL);
    http.addHeader("Content-Type", "application/json");
    int code = http.POST(payload);
    if (code != 200) Serial.println("[HTTP] Error: " + String(code));
    http.end();
  }
}
