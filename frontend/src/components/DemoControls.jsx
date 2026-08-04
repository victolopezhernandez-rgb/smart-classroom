import { useState } from "react";

const SCENARIOS = [
  { id: "empty",      label: "Empty",      sub: "0 people" },
  { id: "few",        label: "A Few",      sub: "6 people" },
  { id: "half_class", label: "Half Class", sub: "18 people" },
  { id: "full_class", label: "Full Class", sub: "30 people" },
  { id: "back_only",  label: "Back Only",  sub: "12 people" },
];

const WEATHER = [
  { id: "clear",    label: "Clear",    icon: "☀️" },
  { id: "cloudy",   label: "Cloudy",   icon: "⛅" },
  { id: "overcast", label: "Overcast", icon: "☁️" },
  { id: "rainy",    label: "Rainy",    icon: "🌧️" },
];

const TIME_PRESETS = [
  { label: "Dawn 6h",   hour: 6.0  },
  { label: "8AM",       hour: 8.0  },
  { label: "Noon",      hour: 12.0 },
  { label: "4PM",       hour: 16.0 },
  { label: "Dusk 18h",  hour: 18.0 },
  { label: "Real time", hour: null },
];

export function DemoControls({ onUpdate }) {
  const [scenario, setScenario] = useState("full_class");
  const [weather, setWeather]   = useState("clear");
  const [timeHour, setTimeHour] = useState(null);
  const [busy, setBusy]         = useState(false);

  async function applyScenario(s) {
    setScenario(s);
    setBusy(true);
    await fetch("/api/vision/scenario", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: s }),
    });
    setBusy(false);
    onUpdate?.();
  }

  async function applyWeather(w) {
    setWeather(w);
    setBusy(true);
    await fetch("/api/light/weather", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ weather: w }),
    });
    setBusy(false);
    onUpdate?.();
  }

  async function applyTime(hour) {
    setTimeHour(hour);
    setBusy(true);
    await fetch("/api/light/time", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ hour }),
    });
    setBusy(false);
    onUpdate?.();
  }

  return (
    <div className="panel" style={{ opacity: busy ? 0.7 : 1 }}>
      <h2>STEAM Fair Demo Controls</h2>

      {/* Scenario */}
      <div style={{ marginBottom: "0.875rem" }}>
        <div style={{ fontSize: "0.7rem", color: "#64748b", marginBottom: "0.375rem" }}>OCCUPANCY SCENARIO</div>
        <div style={{ display: "flex", gap: "0.375rem", flexWrap: "wrap" }}>
          {SCENARIOS.map(({ id, label, sub }) => (
            <button
              key={id}
              onClick={() => applyScenario(id)}
              style={chipStyle(scenario === id, "#3b82f6")}
              title={sub}
            >
              {label}
              <span style={{ fontSize: "0.6rem", display: "block", opacity: 0.7 }}>{sub}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Weather */}
      <div style={{ marginBottom: "0.875rem" }}>
        <div style={{ fontSize: "0.7rem", color: "#64748b", marginBottom: "0.375rem" }}>WEATHER</div>
        <div style={{ display: "flex", gap: "0.375rem", flexWrap: "wrap" }}>
          {WEATHER.map(({ id, label, icon }) => (
            <button
              key={id}
              onClick={() => applyWeather(id)}
              style={chipStyle(weather === id, "#f97316")}
            >
              {icon} {label}
            </button>
          ))}
        </div>
      </div>

      {/* Time of day */}
      <div>
        <div style={{ fontSize: "0.7rem", color: "#64748b", marginBottom: "0.375rem" }}>TIME OF DAY</div>
        <div style={{ display: "flex", gap: "0.375rem", flexWrap: "wrap" }}>
          {TIME_PRESETS.map(({ label, hour }) => (
            <button
              key={label}
              onClick={() => applyTime(hour)}
              style={chipStyle(timeHour === hour, "#a855f7")}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function chipStyle(active, color) {
  return {
    padding: "0.3rem 0.6rem",
    borderRadius: "0.375rem",
    border: `1px solid ${color}${active ? "ff" : "40"}`,
    background: active ? color + "22" : "transparent",
    color: active ? color : "#94a3b8",
    cursor: "pointer",
    fontSize: "0.75rem",
    fontWeight: active ? 600 : 400,
    textAlign: "center",
    minWidth: "4rem",
  };
}
