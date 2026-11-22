import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from "recharts";

export default function HistoryChart({ data }) {
  if (!data.length) return (
    <div style={{ color: "#666", textAlign: "center", padding: 40 }}>
      No history yet — data appears after first detection cycle.
    </div>
  );

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={data} margin={{ top: 8, right: 16, left: -10, bottom: 0 }}>
        <defs>
          <linearGradient id="occ" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.4} />
            <stop offset="95%" stopColor="#ef4444" stopOpacity={0}   />
          </linearGradient>
          <linearGradient id="free" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#22c55e" stopOpacity={0.4} />
            <stop offset="95%" stopColor="#22c55e" stopOpacity={0}   />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
        <XAxis dataKey="time" tick={{ fill: "#888", fontSize: 11 }} />
        <YAxis tick={{ fill: "#888", fontSize: 11 }} allowDecimals={false} />
        <Tooltip
          contentStyle={{ background: "#1a1a2e", border: "1px solid #333", borderRadius: 8 }}
          labelStyle={{ color: "#fff" }}
        />
        <Legend wrapperStyle={{ color: "#aaa", fontSize: 12 }} />
        <Area type="monotone" dataKey="occupied" stroke="#ef4444" fill="url(#occ)"  strokeWidth={2} />
        <Area type="monotone" dataKey="free"     stroke="#22c55e" fill="url(#free)" strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
