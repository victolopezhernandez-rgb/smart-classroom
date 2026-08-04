# SKILL: Report Generator

## What This Skill Does

Generates the before/after energy comparison report — the scientific conclusion of the STEAM fair project. The report includes real-time charts, statistics, and projected annual savings expressed in both kWh and money (Colombian pesos).

## Report Components

### 1. Live Energy Chart (Recharts)
Shows watts consumed over time, with two lines:
- 🔴 **Baseline line** (flat at 320W) — what would happen without AI
- 🟢 **AI line** (varies) — actual consumption with the system

### 2. Summary Statistics Card
Shows the key numbers judges and visitors will want to see.

### 3. Zone Status Grid
4 boxes showing each zone: state (ON/DIM/OFF) + current reason.

## Frontend Components

```jsx
// frontend/src/components/EnergyDashboard.jsx

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { useEffect, useState } from "react";

export function EnergyDashboard({ currentState }) {
  const [history, setHistory] = useState([]);
  const [stats, setStats]     = useState(null);

  // Fetch history every 5 seconds
  useEffect(() => {
    const fetchData = async () => {
      const [histRes, statsRes] = await Promise.all([
        fetch("/api/twin/energy/history"),
        fetch("/api/twin/energy/stats"),
      ]);
      setHistory(await histRes.json());
      setStats(await statsRes.json());
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="energy-dashboard">
      {/* Live chart */}
      <div className="chart-container">
        <h2>⚡ Real-Time Energy Consumption</h2>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={history}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" tick={{ fontSize: 11 }} />
            <YAxis domain={[0, 350]} unit="W" />
            <Tooltip formatter={(value) => [`${value}W`]} />
            <Legend />
            <Line
              type="monotone"
              dataKey="baseline"
              stroke="#e74c3c"
              strokeWidth={2}
              dot={false}
              name="Baseline (all lights on)"
              strokeDasharray="5 5"
            />
            <Line
              type="monotone"
              dataKey="watts"
              stroke="#27ae60"
              strokeWidth={2}
              dot={false}
              name="AI-optimized"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Stats cards */}
      {stats && <StatsCards stats={stats} />}

      {/* Zone status */}
      {currentState && <ZoneStatusGrid lighting={currentState.lighting} />}
    </div>
  );
}

function StatsCards({ stats }) {
  // Colombian electricity rate: ~$800 COP per kWh (2024 approximate)
  const COP_PER_KWH = 800;
  const monthly_savings_cop = Math.round(stats.projected_savings_per_month_kwh * COP_PER_KWH);
  const annual_savings_cop  = monthly_savings_cop * 10;   // 10 school months

  return (
    <div className="stats-grid">
      <StatCard
        icon="⚡"
        label="Current Consumption"
        value={`${stats.avg_ai_watts}W`}
        sub={`vs 320W baseline`}
        color="blue"
      />
      <StatCard
        icon="📉"
        label="Energy Saved"
        value={`${stats.savings_percent}%`}
        sub={`${stats.savings_watts}W saved right now`}
        color="green"
      />
      <StatCard
        icon="📅"
        label="Daily Savings"
        value={`${stats.projected_savings_kwh_per_day} kWh`}
        sub={`per school day (8 hours)`}
        color="orange"
      />
      <StatCard
        icon="💰"
        label="Annual Savings"
        value={`$${annual_savings_cop.toLocaleString()} COP`}
        sub={`${stats.projected_savings_per_month_kwh * 10} kWh/year`}
        color="purple"
      />
    </div>
  );
}

function StatCard({ icon, label, value, sub, color }) {
  return (
    <div className={`stat-card stat-card--${color}`}>
      <span className="stat-icon">{icon}</span>
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
      <span className="stat-sub">{sub}</span>
    </div>
  );
}

function ZoneStatusGrid({ lighting }) {
  const zones = ["zone_A", "zone_B", "zone_C", "zone_D"];
  const labels = { zone_A: "A — Front Left", zone_B: "B — Front Right", zone_C: "C — Back Left", zone_D: "D — Back Right" };
  const stateColors = { ON: "#27ae60", DIM: "#f39c12", OFF: "#95a5a6" };

  return (
    <div className="zone-grid">
      {zones.map(zone => {
        const data = lighting?.[zone] ?? {};
        return (
          <div key={zone} className="zone-card" style={{ borderColor: stateColors[data.state] }}>
            <span className="zone-name">{labels[zone]}</span>
            <span className="zone-state" style={{ color: stateColors[data.state] }}>
              {data.state === "ON" ? "💡 ON" : data.state === "DIM" ? "🔅 DIM" : "⭕ OFF"}
            </span>
            <span className="zone-reason">{data.reason}</span>
          </div>
        );
      })}
    </div>
  );
}
```

## Backend Report Endpoint

```python
# backend/routes/twin_routes.py

@router.get("/api/twin/report")
async def get_report():
    """
    Returns a complete summary report of the session.
    Used to print or display at the end of a demo.
    """
    stats = digital_twin.tracker.get_session_stats()
    
    # Add contextual interpretation
    if stats["savings_percent"] >= 40:
        verdict = "✅ Target achieved! AI saved over 40% energy."
    elif stats["savings_percent"] >= 20:
        verdict = "⚠️ Partial savings achieved. Optimize scenarios for better results."
    else:
        verdict = "❌ Low savings. Check decision thresholds or scenario settings."

    return {
        **stats,
        "verdict": verdict,
        "methodology": "Comparison of simulated AI-controlled lighting vs baseline (all lights on) during the same session.",
        "baseline_description": "Baseline: all 8 fixtures at 40W = 320W total, 8h/day = 2.56 kWh/day"
    }
```

## Step-by-Step Build Instructions for Claude Code

1. **Install** Recharts: `npm install recharts` in `frontend/`
2. **Create** `frontend/src/components/EnergyDashboard.jsx` with all components above
3. **Create** the stat card CSS in `frontend/src/styles/dashboard.css`
4. **Add** `GET /api/twin/energy/history` endpoint in `backend/routes/twin_routes.py`
5. **Add** `GET /api/twin/energy/stats` endpoint
6. **Add** `GET /api/twin/report` endpoint
7. **Import** EnergyDashboard in `frontend/src/App.jsx` and render below the 3D view
8. **Test:** run the system for 60 seconds, then open `/api/twin/report` — you should see savings stats
