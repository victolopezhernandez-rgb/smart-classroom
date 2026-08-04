import { useClassroomWebSocket } from "./hooks/useClassroomWebSocket";
import { Classroom3D } from "./components/Classroom3D";
import { EnergyDashboard } from "./components/EnergyDashboard";
import { DemoControls } from "./components/DemoControls";
import { VoiceController } from "./components/VoiceController";

export default function App() {
  const { state, connected } = useClassroomWebSocket();

  return (
    <>
      <header>
        <h1>Smart Classroom AI — Digital Twin</h1>
        <span className={`badge ${connected ? "connected" : "disconnected"}`}>
          {connected ? "Connected" : "Connecting..."}
        </span>
      </header>

      <main>
        {/* Left column: 3D view + zone cards */}
        <div className="col">
          <div className="panel">
            <h2>3D Classroom View</h2>
            <Classroom3D classroomState={state} />
          </div>

          <div className="panel">
            <h2>Lighting Zones</h2>
            <div className="zone-grid">
              {["zone_A", "zone_B", "zone_C", "zone_D"].map((z) => (
                <ZoneCard key={z} name={z} data={state?.zones?.[z]} />
              ))}
            </div>
          </div>
        </div>

        {/* Right column: demo controls + energy dashboard */}
        <div className="col">
          <VoiceController />
          <DemoControls />
          <EnergyDashboard classroomState={state} />
        </div>
      </main>
    </>
  );
}

const ZONE_LABELS = {
  zone_A: "Zone A — Front Left",
  zone_B: "Zone B — Front Right",
  zone_C: "Zone C — Back Left",
  zone_D: "Zone D — Back Right",
};
const LIGHT_ICON = { ON: "💡", DIM: "🔅", OFF: "⬛" };

function ZoneCard({ name, data }) {
  const state = data?.light ?? "OFF";
  return (
    <div className={`zone-card ${state}`}>
      <div className="zone-name">{ZONE_LABELS[name]}</div>
      <div className="zone-state">{LIGHT_ICON[state]} {state}</div>
      <div className="zone-meta">
        {data?.occupancy ?? 0} people &middot; {Math.round((data?.natural_light ?? 0) * 100)}% natural light
      </div>
      {data?.reason && (
        <div className="zone-meta" style={{ marginTop: "0.25rem", color: "#475569" }}>
          {data.reason}
        </div>
      )}
    </div>
  );
}
