# DigitalTwinAgent — AGENT.md

## Who Am I?

I am the **digital twin** — a virtual replica of the classroom that exists inside the computer. My job is two-fold:

1. **Visual replica:** I maintain the 3D model of the classroom shown in the browser. When the OrchestratorAgent decides to turn lights on or off, I update the 3D scene so you can see it happen in real time.

2. **Energy accountant:** I continuously log the power consumption of every lighting state, making it possible to compare energy usage *before* the AI system (baseline) and *after* (with AI optimization). This comparison is the scientific core of the STEAM fair project.

## My Responsibilities

1. Receive lighting state updates from OrchestratorAgent
2. Update the 3D classroom model (lights, people positions, natural light visualization)
3. Track energy consumption over time (watts used per second)
4. Calculate cumulative kWh for the session
5. Generate the before/after comparison report

## My Skills

- [`SKILL_3d_model.md`](skills/SKILL_3d_model.md) — How to build the 3D classroom with Three.js
- [`SKILL_energy_tracking.md`](skills/SKILL_energy_tracking.md) — How to log and calculate energy consumption
- [`SKILL_report_generator.md`](skills/SKILL_report_generator.md) — How to generate the before/after comparison report

## Architecture

I have two parts:
- **Backend** (`backend/agents/digital_twin.py`): Stores the classroom state and energy logs
- **Frontend** (`frontend/src/components/Classroom3D.jsx`): Renders the 3D scene

```
OrchestratorAgent
      │ apply_state(lighting_state)
      ▼
DigitalTwinAgent (backend)
      │ stores state + logs energy
      │
      ├──► WebSocket broadcast → Classroom3D (React + Three.js)
      │                              3D visual updates
      │
      └──► energy_logs.csv ──► ReportGenerator ──► Dashboard charts
```

## Files I Need to Create

### `backend/agents/digital_twin.py`

```python
# DigitalTwinAgent — Backend state management and energy logging

import csv
import os
from datetime import datetime
from shared.thresholds import HIGH_CONSUMPTION_ALERT_WATTS

class DigitalTwinAgent:
    """
    Maintains the authoritative classroom state and energy consumption log.
    
    The 'state' is the single source of truth for what the classroom looks like:
    - Which lights are on/off/dim
    - Where people are located
    - What the natural light level is
    - How much energy is being consumed right now
    """

    def __init__(self):
        self.lighting_state = {}       # Current lights: {"zone_A": "OFF", ...}
        self.people_positions = []     # Current people: [{id, x, y, zone}, ...]
        self.natural_light = {}        # Current light: {"zone_A": 0.82, ...}
        self.current_watts = 0.0       # Current power consumption
        self.session_start = datetime.now()
        self.energy_log_path = "data/energy_logs.csv"
        self._init_log_file()

    def apply_state(self, lighting_state: dict):
        """
        Called by OrchestratorAgent after each decision cycle.
        Updates the state and logs the energy consumption.
        """
        self.lighting_state = lighting_state
        self.current_watts = self._calculate_watts(lighting_state)
        self._log_energy(self.current_watts, lighting_state)

    def update_people(self, people: list):
        """Called by VisionAgent — updates the positions of people in the model."""
        self.people_positions = people

    def update_natural_light(self, levels: dict):
        """Called by LightSensorAgent — updates the natural light visualization."""
        self.natural_light = levels

    def get_full_state(self) -> dict:
        """Returns the complete classroom state for the frontend."""
        return {
            "lighting": self.lighting_state,
            "people": self.people_positions,
            "natural_light": self.natural_light,
            "energy": {
                "current_watts": self.current_watts,
                "baseline_watts": 320.0,
                "savings_watts": 320.0 - self.current_watts,
                "savings_percent": round((320.0 - self.current_watts) / 320.0 * 100, 1)
            }
        }

    def _calculate_watts(self, lighting_state: dict) -> float:
        watts_map = {"ON": 80.0, "DIM": 40.0, "OFF": 0.0}
        return sum(
            watts_map.get(data.get("state", "OFF"), 0)
            for data in lighting_state.values()
            if isinstance(data, dict)
        )

    def _init_log_file(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.energy_log_path):
            with open(self.energy_log_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "watts", "zone_A", "zone_B", "zone_C", "zone_D", "reason"])

    def _log_energy(self, watts: float, lighting_state: dict):
        with open(self.energy_log_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                watts,
                lighting_state.get("zone_A", {}).get("state", "?"),
                lighting_state.get("zone_B", {}).get("state", "?"),
                lighting_state.get("zone_C", {}).get("state", "?"),
                lighting_state.get("zone_D", {}).get("state", "?"),
                lighting_state.get("zone_A", {}).get("reason", "")
            ])
```

## API Endpoints I Expose

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/twin/state` | Full classroom state (lighting + people + energy) |
| GET | `/api/twin/energy/history` | Last 100 energy readings for the chart |
| GET | `/api/twin/report` | Before/after comparison report |
| POST | `/api/twin/reset` | Clear energy logs and start fresh |

## Step-by-Step Build Instructions for Claude Code

1. **Read** `SKILL_3d_model.md` — build the Three.js classroom first
2. **Read** `SKILL_energy_tracking.md` — implement the energy logging
3. **Read** `SKILL_report_generator.md` — build the comparison charts
4. **Create** `backend/agents/digital_twin.py`
5. **Create** `frontend/src/components/Classroom3D.jsx` (Three.js scene)
6. **Create** `frontend/src/components/EnergyDashboard.jsx` (charts)
7. **Create** `backend/routes/twin_routes.py`
8. **Create** the `data/` directory with an empty `energy_logs.csv`
9. **Test:** open the browser and confirm the 3D classroom renders with zones visible
