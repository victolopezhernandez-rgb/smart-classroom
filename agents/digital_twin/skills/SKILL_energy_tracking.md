# SKILL: Energy Tracking

## What This Skill Does

Records power consumption over time and provides the data needed to prove that the AI system saves electricity. This is the **scientific measurement** part of the project — without this, we can't compare before/after.

## Energy Model

```
Classroom lighting:
  - 4 zones × 2 fixtures = 8 total light fixtures
  - Each fixture: 40W fluorescent bulb
  - Maximum total: 8 × 40W = 320W

Per-zone power:
  - Zone ON  (2 fixtures): 80W
  - Zone DIM (2 fixtures at 50%): 40W  
  - Zone OFF: 0W
```

## Implementation

```python
# backend/skills/energy_tracker.py

import csv
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import Literal

BASELINE_WATTS = 320.0   # All lights on (no AI)
LOG_FILE = "data/energy_logs.csv"

@dataclass
class EnergyReading:
    timestamp: str
    watts: float
    zone_states: dict   # {"zone_A": "ON", "zone_B": "OFF", ...}
    mode: Literal["BASELINE", "AI"]
    session_id: str

class EnergyTracker:
    """
    Records energy consumption readings every 5 seconds.
    Compares AI-controlled consumption vs baseline (all lights on).
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.readings: list[EnergyReading] = []
        self._init_csv()

    def log_reading(self, lighting_state: dict, mode: str = "AI"):
        """
        Records one energy reading. Called every 5 seconds by DigitalTwinAgent.
        
        Args:
            lighting_state: {"zone_A": {"state": "ON"}, ...}
            mode: "AI" or "BASELINE"
        """
        watts = self._calculate_watts(lighting_state)
        zone_states = {
            zone: data.get("state", "OFF")
            for zone, data in lighting_state.items()
            if isinstance(data, dict)
        }

        reading = EnergyReading(
            timestamp=datetime.now().isoformat(),
            watts=watts,
            zone_states=zone_states,
            mode=mode,
            session_id=self.session_id
        )
        self.readings.append(reading)
        self._write_to_csv(reading)
        return reading

    def get_session_stats(self) -> dict:
        """
        Returns statistics for the current session.
        Used by the dashboard and report generator.
        """
        if not self.readings:
            return {"error": "No readings yet"}

        ai_readings    = [r for r in self.readings if r.mode == "AI"]
        base_readings  = [r for r in self.readings if r.mode == "BASELINE"]

        avg_ai_watts   = sum(r.watts for r in ai_readings)    / len(ai_readings)   if ai_readings   else 0
        avg_base_watts = sum(r.watts for r in base_readings)  / len(base_readings) if base_readings else BASELINE_WATTS

        savings_watts   = avg_base_watts - avg_ai_watts
        savings_percent = (savings_watts / avg_base_watts * 100) if avg_base_watts > 0 else 0

        # Project daily kWh (8-hour school day)
        ai_kwh_day   = avg_ai_watts   / 1000 * 8
        base_kwh_day = avg_base_watts / 1000 * 8

        return {
            "session_id":        self.session_id,
            "total_readings":    len(self.readings),
            "avg_ai_watts":      round(avg_ai_watts, 1),
            "avg_baseline_watts": round(avg_base_watts, 1),
            "savings_watts":     round(savings_watts, 1),
            "savings_percent":   round(savings_percent, 1),
            "projected_ai_kwh_per_day":       round(ai_kwh_day, 3),
            "projected_baseline_kwh_per_day": round(base_kwh_day, 3),
            "projected_savings_kwh_per_day":  round(base_kwh_day - ai_kwh_day, 3),
            "projected_savings_per_month_kwh": round((base_kwh_day - ai_kwh_day) * 22, 2),
        }

    def get_history_for_chart(self, last_n: int = 60) -> list[dict]:
        """
        Returns the last N readings formatted for the frontend Recharts component.
        """
        recent = self.readings[-last_n:]
        return [
            {
                "time": r.timestamp[11:19],   # HH:MM:SS only
                "watts": r.watts,
                "baseline": BASELINE_WATTS,
            }
            for r in recent
        ]

    def _calculate_watts(self, lighting_state: dict) -> float:
        watts_map = {"ON": 80.0, "DIM": 40.0, "OFF": 0.0}
        return sum(
            watts_map.get(data.get("state", "OFF"), 0)
            for data in lighting_state.values()
            if isinstance(data, dict)
        )

    def _init_csv(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", newline="") as f:
                csv.writer(f).writerow([
                    "timestamp", "session_id", "mode",
                    "watts", "zone_A", "zone_B", "zone_C", "zone_D"
                ])

    def _write_to_csv(self, reading: EnergyReading):
        with open(LOG_FILE, "a", newline="") as f:
            csv.writer(f).writerow([
                reading.timestamp,
                reading.session_id,
                reading.mode,
                reading.watts,
                reading.zone_states.get("zone_A", "?"),
                reading.zone_states.get("zone_B", "?"),
                reading.zone_states.get("zone_C", "?"),
                reading.zone_states.get("zone_D", "?"),
            ])
```

## Baseline Mode

To capture the "before AI" baseline, the frontend has a toggle that puts the system in BASELINE mode. In this mode:
- All lights are forced ON (320W)
- Energy readings are logged with `mode="BASELINE"`
- After switching back to AI mode, the comparison becomes visible in the chart

```python
# In DigitalTwinAgent — how to switch modes

def set_mode(self, mode: str):
    """Switch between 'AI' and 'BASELINE' modes."""
    self.mode = mode
    if mode == "BASELINE":
        # Force all lights ON for baseline measurement
        forced_state = {
            zone: {"state": "ON", "reason": "Baseline measurement"}
            for zone in ["zone_A", "zone_B", "zone_C", "zone_D"]
        }
        self.apply_state(forced_state)
```

## Step-by-Step Build Instructions for Claude Code

1. **Create** `backend/skills/energy_tracker.py` with the EnergyTracker class
2. **Instantiate** it in `DigitalTwinAgent.__init__()` with a session ID (use the startup timestamp)
3. **Call** `tracker.log_reading(lighting_state)` inside `DigitalTwinAgent.apply_state()`
4. **Add** `GET /api/twin/energy/history` endpoint that calls `tracker.get_history_for_chart()`
5. **Add** `GET /api/twin/energy/stats` endpoint that calls `tracker.get_session_stats()`
6. **Add** `POST /api/twin/mode` endpoint that switches between AI and BASELINE modes
