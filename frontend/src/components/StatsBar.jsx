export default function StatsBar({ summary }) {
  if (!summary) return null;
  const { total, occupied, free } = summary;
  const pct = total > 0 ? Math.round((occupied / total) * 100) : 0;

  const cards = [
    { label: "Total Slots",  value: total,    color: "#3b82f6" },
    { label: "Occupied",     value: occupied, color: "#ef4444" },
    { label: "Available",    value: free,     color: "#22c55e" },
    { label: "Utilization",  value: `${pct}%`,color: pct > 75 ? "#ef4444" : pct > 50 ? "#f59e0b" : "#22c55e" },
  ];

  return (
    <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 24 }}>
      {cards.map((c) => (
        <div key={c.label} style={{
          flex:         "1 1 120px",
          background:   "#1a1a2e",
          border:       `1px solid ${c.color}33`,
          borderRadius: 10,
          padding:      "16px 20px",
          textAlign:    "center",
        }}>
          <div style={{ fontSize: 32, fontWeight: 700, color: c.color }}>{c.value}</div>
          <div style={{ fontSize: 12, color: "#aaa", marginTop: 4 }}>{c.label}</div>
        </div>
      ))}
    </div>
  );
}
