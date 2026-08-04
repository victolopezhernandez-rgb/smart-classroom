import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

// Datos de referencia fijos
const COP_PER_KWH      = 800;   // Tarifa eléctrica Colombia 2024
const BASELINE_W       = 320;   // 8 lámparas × 40W
const SCHOOL_HOURS_DAY = 8;     // Horas de clase por día
const SCHOOL_DAYS_YEAR = 200;   // 10 meses × 20 días

export function EnergyDashboard({ classroomState }) {
  const [history, setHistory] = useState([]);
  const [stats, setStats]     = useState(null);
  const [mode, setMode]       = useState("AI");

  // Fetch energy history + stats every 5 seconds
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [histRes, statsRes] = await Promise.all([
          fetch("/api/twin/energy/history"),
          fetch("/api/twin/energy/stats"),
        ]);
        if (histRes.ok)  setHistory(await histRes.json());
        if (statsRes.ok) setStats(await statsRes.json());
      } catch {
        // Backend not yet running — silently skip
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleModeSwitch = async (newMode) => {
    setMode(newMode);
    await fetch("/api/twin/mode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: newMode }),
    });
  };

  const handleReset = async () => {
    await fetch("/api/twin/reset", { method: "POST" });
    setHistory([]);
    setStats(null);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      {/* Mode controls */}
      <div className="panel">
        <h2>Mode Control</h2>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <button
            onClick={() => handleModeSwitch("AI")}
            style={btnStyle(mode === "AI", "#14532d", "#4ade80")}
          >
            AI Mode
          </button>
          <button
            onClick={() => handleModeSwitch("BASELINE")}
            style={btnStyle(mode === "BASELINE", "#450a0a", "#f87171")}
          >
            Baseline Mode
          </button>
          <button onClick={handleReset} style={btnStyle(false, "#1e2232", "#94a3b8")}>
            Reset Session
          </button>
        </div>
      </div>

      {/* Live chart */}
      <div className="panel">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2 style={{ margin: 0 }}>Real-Time Energy Consumption</h2>
          <span style={{ fontSize: "0.72rem", color: "#64748b", background: "#1e2232", padding: "0.2rem 0.6rem", borderRadius: "0.375rem", border: "1px solid #2d3148" }}>
            Tarifa: <strong style={{ color: "#a78bfa" }}>${COP_PER_KWH} COP/kWh</strong>
          </span>
        </div>
        {history.length === 0 ? (
          <div className="placeholder" style={{ height: "200px" }}>
            Waiting for data — start the backend to see readings
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={history} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2232" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#64748b" }} />
              <YAxis domain={[0, 350]} unit="W" tick={{ fontSize: 10, fill: "#64748b" }} />
              <Tooltip
                contentStyle={{ background: "#1a1d27", border: "1px solid #2d3148", borderRadius: "0.5rem" }}
                labelStyle={{ color: "#94a3b8" }}
                formatter={(v) => [`${v}W`]}
              />
              <Legend wrapperStyle={{ fontSize: "0.75rem" }} />
              <Line
                type="monotone"
                dataKey="baseline"
                stroke="#ef4444"
                strokeWidth={2}
                dot={false}
                name="Baseline (320W)"
                strokeDasharray="5 5"
              />
              <Line
                type="monotone"
                dataKey="watts"
                stroke="#4ade80"
                strokeWidth={2}
                dot={false}
                name="AI-optimized"
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Panel comparativo */}
      <ComparisonPanel stats={stats} />

      {/* Zone status */}
      {classroomState && <ZoneStatusGrid zones={classroomState.zones} />}
    </div>
  );
}

function ComparisonPanel({ stats }) {
  // ── Datos fijos de referencia ──────────────────────────────────────────
  const refs = [
    { label: "Tarifa eléctrica", value: `$${COP_PER_KWH.toLocaleString()} COP/kWh`, note: "Colombia 2024" },
    { label: "Potencia base",    value: `${BASELINE_W} W`,                           note: "8 lámparas × 40W" },
    { label: "Horas de clase",   value: `${SCHOOL_HOURS_DAY} h/día`,                 note: "jornada escolar" },
    { label: "Días escolares",   value: `${SCHOOL_DAYS_YEAR} días/año`,              note: "10 meses × 20 días" },
  ];

  // ── Cálculos ────────────────────────────────────────────────────────────
  const ai_w = stats?.avg_ai_watts ?? null;

  const calc = (w) => {
    const kwh_h = w / 1000;
    const cop_h = kwh_h * COP_PER_KWH;
    const kwh_d = kwh_h * SCHOOL_HOURS_DAY;
    const cop_d = kwh_d * COP_PER_KWH;
    const kwh_y = kwh_d * SCHOOL_DAYS_YEAR;
    const cop_y = kwh_y * COP_PER_KWH;
    return { kwh_h, cop_h, kwh_d, cop_d, kwh_y, cop_y };
  };

  const base = calc(BASELINE_W);
  const ai   = ai_w !== null ? calc(ai_w) : null;

  const fmt  = (n, dec = 2) => n.toFixed(dec);
  const cop  = (n) => `$${Math.round(n).toLocaleString()} COP`;

  const rows = [
    {
      label: "Potencia activa",
      base:  `${BASELINE_W} W`,
      ai:    ai ? `${ai_w} W` : "—",
      saved: ai ? `${BASELINE_W - ai_w} W (${stats.savings_percent}%)` : "—",
      highlight: false,
    },
    {
      label: "Consumo por hora",
      base:  `${fmt(base.kwh_h, 3)} kWh`,
      ai:    ai ? `${fmt(ai.kwh_h, 3)} kWh` : "—",
      saved: ai ? `${fmt(base.kwh_h - ai.kwh_h, 3)} kWh` : "—",
      highlight: false,
    },
    {
      label: "Costo por hora",
      base:  cop(base.cop_h),
      ai:    ai ? cop(ai.cop_h) : "—",
      saved: ai ? cop(base.cop_h - ai.cop_h) : "—",
      highlight: false,
    },
    {
      label: `Consumo diario (${SCHOOL_HOURS_DAY}h)`,
      base:  `${fmt(base.kwh_d)} kWh`,
      ai:    ai ? `${fmt(ai.kwh_d)} kWh` : "—",
      saved: ai ? `${fmt(base.kwh_d - ai.kwh_d)} kWh` : "—",
      highlight: false,
    },
    {
      label: "Costo diario",
      base:  cop(base.cop_d),
      ai:    ai ? cop(ai.cop_d) : "—",
      saved: ai ? cop(base.cop_d - ai.cop_d) : "—",
      highlight: false,
    },
    {
      label: `Consumo anual (${SCHOOL_DAYS_YEAR} días)`,
      base:  `${fmt(base.kwh_y, 0)} kWh`,
      ai:    ai ? `${fmt(ai.kwh_y, 0)} kWh` : "—",
      saved: ai ? `${fmt(base.kwh_y - ai.kwh_y, 0)} kWh` : "—",
      highlight: true,
    },
    {
      label: "Ahorro anual",
      base:  cop(base.cop_y),
      ai:    ai ? cop(ai.cop_y) : "—",
      saved: ai ? cop(base.cop_y - ai.cop_y) : "—",
      highlight: true,
    },
  ];

  const thStyle = { padding: "0.4rem 0.6rem", fontSize: "0.68rem", color: "#64748b", fontWeight: 600, textAlign: "center", whiteSpace: "nowrap" };
  const tdBase  = { padding: "0.35rem 0.6rem", fontSize: "0.72rem", textAlign: "center", color: "#f87171" };
  const tdAI    = { padding: "0.35rem 0.6rem", fontSize: "0.72rem", textAlign: "center", color: "#4ade80" };
  const tdSaved = { padding: "0.35rem 0.6rem", fontSize: "0.72rem", textAlign: "center", color: "#a78bfa", fontWeight: 700 };
  const tdLabel = { padding: "0.35rem 0.6rem", fontSize: "0.7rem",  color: "#94a3b8", whiteSpace: "nowrap" };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>

      {/* Datos de referencia fijos */}
      <div className="panel" style={{ padding: "0.75rem" }}>
        <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#64748b", marginBottom: "0.5rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
          Datos de referencia
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.4rem" }}>
          {refs.map(({ label, value, note }) => (
            <div key={label} style={{ background: "#141820", borderRadius: "0.375rem", padding: "0.5rem 0.65rem", border: "1px solid #facc1530" }}>
              <div style={{ fontSize: "0.62rem", color: "#64748b" }}>{label}</div>
              <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#facc15" }}>{value}</div>
              <div style={{ fontSize: "0.6rem", color: "#475569" }}>{note}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Tabla comparativa */}
      <div className="panel" style={{ padding: "0.75rem", overflowX: "auto" }}>
        <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#64748b", marginBottom: "0.5rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
          Comparativo Sin IA vs Con IA
        </div>
        {!stats ? (
          <div style={{ fontSize: "0.75rem", color: "#475569", padding: "1rem 0", textAlign: "center" }}>
            Inicia el backend para ver el comparativo en tiempo real
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #1e2232" }}>
                <th style={{ ...thStyle, textAlign: "left" }}>Métrica</th>
                <th style={{ ...thStyle, color: "#f87171" }}>Sin IA</th>
                <th style={{ ...thStyle, color: "#4ade80" }}>Con IA</th>
                <th style={{ ...thStyle, color: "#a78bfa" }}>Ahorro</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ label, base: b, ai: a, saved, highlight }) => (
                <tr
                  key={label}
                  style={{
                    borderBottom: "1px solid #1e223280",
                    background: highlight ? "#a78bfa08" : "transparent",
                  }}
                >
                  <td style={{ ...tdLabel, fontWeight: highlight ? 700 : 400 }}>{label}</td>
                  <td style={tdBase}>{b}</td>
                  <td style={tdAI}>{a}</td>
                  <td style={{ ...tdSaved, fontSize: highlight ? "0.78rem" : "0.72rem" }}>{saved}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function ZoneStatusGrid({ zones }) {
  const LABELS = {
    zone_A: "A — Front Left",
    zone_B: "B — Front Right",
    zone_C: "C — Back Left",
    zone_D: "D — Back Right",
  };
  const STATE_COLOR = { ON: "#4ade80", DIM: "#f97316", OFF: "#475569" };
  const STATE_ICON  = { ON: "💡", DIM: "🔅", OFF: "⬛" };

  return (
    <div className="panel">
      <h2>Zone Status</h2>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
        {Object.entries(zones ?? {}).map(([zone, data]) => {
          const state = data?.light ?? "OFF";
          return (
            <div
              key={zone}
              style={{
                border: `1px solid ${STATE_COLOR[state]}40`,
                borderRadius: "0.375rem",
                padding: "0.625rem",
                background: "#141820",
              }}
            >
              <div style={{ fontSize: "0.75rem", fontWeight: 600 }}>{LABELS[zone]}</div>
              <div style={{ color: STATE_COLOR[state], fontWeight: 700, margin: "0.125rem 0" }}>
                {STATE_ICON[state]} {state}
              </div>
              <div style={{ fontSize: "0.65rem", color: "#475569" }}>{data?.reason}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function btnStyle(active, bg, color) {
  return {
    padding: "0.4rem 1rem",
    borderRadius: "0.375rem",
    border: `1px solid ${color}40`,
    background: active ? bg : "transparent",
    color,
    cursor: "pointer",
    fontSize: "0.8rem",
    fontWeight: 600,
  };
}
