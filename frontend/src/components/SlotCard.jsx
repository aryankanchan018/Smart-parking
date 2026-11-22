import { useState, useEffect } from "react";

const MODE_COLORS = {
  hybrid:   "#22c55e",
  camera:   "#3b82f6",
  sensor:   "#f59e0b",
  conflict: "#ef4444",
  none:     "#6b7280",
};

function formatDuration(sec) {
  if (sec === null || sec === undefined) return null;
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  if (h > 0) return `${h}h ${m}m ${s}s`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function formatTime(ts) {
  if (!ts) return null;
  return new Date(ts * 1000).toLocaleTimeString();
}

export default function SlotCard({ slot }) {
  const occupied  = slot.occupied;
  const modeColor = MODE_COLORS[slot.mode] ?? "#6b7280";

  // Live duration counter
  const [liveDuration, setLiveDuration] = useState(slot.duration_sec);
  useEffect(() => {
    if (!occupied || !slot.entry_time) { setLiveDuration(null); return; }
    setLiveDuration(slot.duration_sec);
    const interval = setInterval(() => {
      setLiveDuration(Math.round(Date.now() / 1000 - slot.entry_time));
    }, 1000);
    return () => clearInterval(interval);
  }, [occupied, slot.entry_time, slot.duration_sec]);

  return (
    <div style={{
      background:   occupied ? "#1e1b2e" : "#0f1a0f",
      border:       `2px solid ${occupied ? "#ef4444" : "#22c55e"}`,
      borderRadius: 12,
      padding:      "20px 16px",
      textAlign:    "center",
      position:     "relative",
      minWidth:     140,
      flex:         "1 1 140px",
    }}>
      {/* Slot ID */}
      <div style={{ fontSize: 28, fontWeight: 700, color: "#fff" }}>{slot.slot_id}</div>

      {/* Car icon */}
      <div style={{ fontSize: 36, margin: "8px 0" }}>
        {occupied ? "🚗" : "⬜"}
      </div>

      {/* Status */}
      <div style={{ fontSize: 14, fontWeight: 600, color: occupied ? "#ef4444" : "#22c55e", marginBottom: 8 }}>
        {occupied ? "OCCUPIED" : "FREE"}
      </div>

      {/* Entry time */}
      {occupied && slot.entry_time && (
        <div style={{ fontSize: 11, color: "#aaa", marginBottom: 4 }}>
          🕐 Entered: {formatTime(slot.entry_time)}
        </div>
      )}

      {/* Live duration */}
      {occupied && liveDuration !== null && (
        <div style={{ fontSize: 13, fontWeight: 600, color: "#f59e0b", marginBottom: 6 }}>
          ⏱ {formatDuration(liveDuration)}
        </div>
      )}

      {/* Last free time */}
      {!occupied && slot.last_free_time && (
        <div style={{ fontSize: 11, color: "#6b7280", marginBottom: 4 }}>
          Last freed: {formatTime(slot.last_free_time)}
        </div>
      )}

      {/* Sensor + Camera readings */}
      <div style={{ display: "flex", gap: 6, justifyContent: "center", margin: "8px 0" }}>
        {/* Camera */}
        <div style={{
          flex: 1, borderRadius: 6, padding: "4px 6px",
          background: slot.camera?.active ? (slot.camera?.occupied ? "#3b1f1f" : "#1a2e1a") : "#1a1a1a",
          border: `1px solid ${slot.camera?.active ? (slot.camera?.occupied ? "#ef4444" : "#22c55e") : "#333"}`
        }}>
          <div style={{ fontSize: 10, color: "#888" }}>📷 Camera</div>
          <div style={{ fontSize: 11, fontWeight: 600, color: slot.camera?.active ? (slot.camera?.occupied ? "#ef4444" : "#22c55e") : "#555" }}>
            {!slot.camera?.active ? "NO DATA" : slot.camera?.occupied ? "OCC" : "FREE"}
          </div>
          {slot.camera?.active && (
            <div style={{ fontSize: 10, color: "#777" }}>{Math.round((slot.camera?.confidence ?? 0) * 100)}%</div>
          )}
        </div>
        {/* Sensor */}
        <div style={{
          flex: 1, borderRadius: 6, padding: "4px 6px",
          background: slot.sensor?.active ? (slot.sensor?.occupied ? "#3b1f1f" : "#1a2e1a") : "#1a1a1a",
          border: `1px solid ${slot.sensor?.active ? (slot.sensor?.occupied ? "#ef4444" : "#22c55e") : "#333"}`
        }}>
          <div style={{ fontSize: 10, color: "#888" }}>📡 Sensor</div>
          <div style={{ fontSize: 11, fontWeight: 600, color: slot.sensor?.active ? (slot.sensor?.occupied ? "#ef4444" : "#22c55e") : "#555" }}>
            {!slot.sensor?.active ? "NO DATA" : slot.sensor?.occupied ? "OCC" : "FREE"}
          </div>
          {slot.sensor?.active && (
            <div style={{ fontSize: 10, color: "#777" }}>{slot.sensor?.distance}cm</div>
          )}
        </div>
      </div>

      {/* Confidence bar */}
      <div style={{ background: "#333", borderRadius: 4, height: 6, margin: "6px 0" }}>
        <div style={{
          width:        `${Math.round(slot.confidence * 100)}%`,
          height:       "100%",
          background:   modeColor,
          borderRadius: 4,
          transition:   "width 0.4s ease",
        }} />
      </div>
      <div style={{ fontSize: 11, color: "#aaa" }}>
        {Math.round(slot.confidence * 100)}% conf
      </div>

      {/* Mode badge */}
      <div style={{
        position:      "absolute",
        top:           8,
        right:         8,
        background:    modeColor,
        color:         "#fff",
        fontSize:      10,
        fontWeight:    700,
        padding:       "2px 6px",
        borderRadius:  4,
        textTransform: "uppercase",
      }}>
        {slot.mode}
      </div>
    </div>
  );
}
