import { useParking } from "./hooks/useParking";
import { useHistory } from "./hooks/useHistory";
import StatsBar     from "./components/StatsBar";
import SlotCard     from "./components/SlotCard";
import HistoryChart from "./components/HistoryChart";
import StatusBar    from "./components/StatusBar";

export default function App() {
  const { summary, connected, lastUpdate } = useParking();
  const history = useHistory();

  return (
    <div style={{
      minHeight:   "100vh",
      background:  "#0d0d1a",
      color:       "#fff",
      fontFamily:  "system-ui, sans-serif",
      padding:     "24px 32px",
      boxSizing:   "border-box",
    }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: "#fff" }}>
          🅿️ Smart Parking Dashboard
        </h1>
        <p style={{ margin: "4px 0 0", color: "#666", fontSize: 13 }}>
          AI-powered real-time parking management
        </p>
      </div>

      {/* Connection + mode legend */}
      <StatusBar connected={connected} lastUpdate={lastUpdate} />

      {/* Stats */}
      <StatsBar summary={summary} />

      {/* Slot grid */}
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 16, color: "#aaa", marginBottom: 12, fontWeight: 600 }}>
          Parking Slots
        </h2>
        {summary ? (
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
            {summary.slots.map((slot) => (
              <SlotCard key={slot.slot_id} slot={slot} />
            ))}
          </div>
        ) : (
          <div style={{
            color: "#555", padding: 40, textAlign: "center",
            border: "1px dashed #333", borderRadius: 12,
          }}>
            {connected ? "Waiting for first detection..." : "Backend offline — start FastAPI server"}
          </div>
        )}
      </div>

      {/* History chart */}
      <div style={{
        background: "#111827", borderRadius: 12,
        padding: "20px 24px", border: "1px solid #1f2937",
      }}>
        <h2 style={{ fontSize: 16, color: "#aaa", marginBottom: 16, fontWeight: 600, margin: "0 0 16px" }}>
          Occupancy History
        </h2>
        <HistoryChart data={history} />
      </div>
    </div>
  );
}
