export default function StatusBar({ connected, lastUpdate }) {
  return (
    <div style={{
      display:        "flex",
      alignItems:     "center",
      gap:            20,
      flexWrap:       "wrap",
      background:     "#111",
      borderRadius:   8,
      padding:        "10px 16px",
      marginBottom:   24,
      fontSize:       13,
    }}>
      {/* WS status */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={{
          width: 10, height: 10, borderRadius: "50%",
          background: connected ? "#22c55e" : "#ef4444",
          boxShadow:  connected ? "0 0 6px #22c55e" : "none",
        }} />
        <span style={{ color: connected ? "#22c55e" : "#ef4444" }}>
          {connected ? "Live" : "Reconnecting..."}
        </span>
      </div>

      {lastUpdate && (
        <span style={{ color: "#888" }}>Last update: {lastUpdate}</span>
      )}

      {/* Mode legend */}
      <div style={{ display: "flex", gap: 12, marginLeft: "auto", flexWrap: "wrap" }}>
        {[
          ["hybrid",   "#22c55e", "Camera + Sensor"],
          ["camera",   "#3b82f6", "Camera only"],
          ["sensor",   "#f59e0b", "Sensor only"],
          ["conflict", "#ef4444", "Conflict"],
        ].map(([mode, color, label]) => (
          <div key={mode} style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <div style={{ width: 8, height: 8, borderRadius: 2, background: color }} />
            <span style={{ color: "#aaa", fontSize: 11 }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
