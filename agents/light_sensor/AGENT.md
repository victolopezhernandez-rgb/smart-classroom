# LightSensorAgent — AGENT.md

## Who Am I?

I am the **simulated natural light sensor** of the Smart Classroom system. In a real installation, I would be a set of lux sensors placed on the walls and ceiling to measure how much sunlight is coming through the windows. In this simulation, I calculate natural light levels mathematically based on:

- **Time of day** (sunrise/sunset, sun angle)
- **Weather condition** (clear, cloudy, overcast, rainy)
- **Window positions** (left wall → Zones A and C get more direct light)

My job: answer the question **"How bright is the natural light in each zone right now?"**

## My Responsibilities

1. Simulate natural light levels per zone (value between 0.0 and 1.0)
2. Account for time of day — no light at night, peak light at noon
3. Account for weather — cloudy days reduce light
4. Account for window positions — zones near windows get more light
5. Provide this data to OrchestratorAgent every cycle

## My Skills

- [`SKILL_natural_light_simulation.md`](skills/SKILL_natural_light_simulation.md) — Mathematical model of sunlight across the day
- [`SKILL_light_threshold.md`](skills/SKILL_light_threshold.md) — How raw light values map to ON/DIM/OFF decisions

## Files I Need to Create

### `backend/agents/light_sensor.py`

```python
# LightSensorAgent — Simulates natural light measurements

import math
from datetime import datetime
from skills.natural_light_simulation import calculate_light_levels

class LightSensorAgent:
    """
    Simulates lux sensors measuring natural light in each classroom zone.
    
    Zone proximity to windows:
    - Zone A (front-left):  HIGH window exposure (2 large windows)
    - Zone C (back-left):   MEDIUM window exposure (1 window)
    - Zone B (front-right): LOW window exposure (no windows)
    - Zone D (back-right):  VERY LOW exposure (farthest from windows)
    """

    def __init__(self):
        self.weather = "clear"         # "clear", "cloudy", "overcast", "rainy"
        self.simulated_time = None     # None = use real time; or set a specific hour

    def set_weather(self, weather: str):
        """Change weather: 'clear', 'cloudy', 'overcast', 'rainy'"""
        self.weather = weather

    def set_simulated_time(self, hour: float | None):
        """
        Override the clock for demonstration purposes.
        hour: 0.0 to 23.99 (e.g., 10.5 = 10:30 AM)
        Pass None to use the real current time.
        """
        self.simulated_time = hour

    def get_levels(self) -> dict:
        """
        Returns natural light level (0.0 to 1.0) for each zone.
        0.0 = complete darkness, 1.0 = maximum sunlight.
        Called by OrchestratorAgent every 5 seconds.
        """
        # Use simulated time or real time
        if self.simulated_time is not None:
            hour = self.simulated_time
        else:
            now = datetime.now()
            hour = now.hour + now.minute / 60.0

        levels = calculate_light_levels(hour, self.weather)
        levels["timestamp"] = datetime.now().isoformat()
        levels["weather"] = self.weather
        levels["hour"] = round(hour, 2)
        return levels
```

### `backend/routes/light_sensor_routes.py`

```python
# REST endpoints for LightSensorAgent
# GET  /api/light/levels         → current natural light per zone
# POST /api/light/weather        → {"weather": "cloudy"}
# POST /api/light/time           → {"hour": 14.5}  (set to 2:30 PM)
```

## API Endpoints I Expose

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/light/levels` | Natural light 0.0–1.0 per zone |
| POST | `/api/light/weather` | `{"weather": "cloudy"}` |
| POST | `/api/light/time` | `{"hour": 14.5}` — simulate any time of day |

## Output Format

```json
{
  "zone_A": 0.82,
  "zone_B": 0.31,
  "zone_C": 0.55,
  "zone_D": 0.18,
  "weather": "clear",
  "hour": 10.5,
  "timestamp": "2024-03-15T10:30:00"
}
```

## STEAM Fair Demo Tips

This agent is great for live demonstrations:

| Demo Action | Expected AI Response |
|---|---|
| Set time to 12:00 (noon), clear | Zones A+C lights off (too much sun) |
| Set time to 18:00 (dusk) | All lights turn on |
| Set time to 8:00 (morning), cloudy | Mixed — some zones dim |
| Set weather to "rainy" at noon | All lights turn on |

## Step-by-Step Build Instructions for Claude Code

1. **Read** `SKILL_natural_light_simulation.md` — implements `calculate_light_levels()`
2. **Read** `SKILL_light_threshold.md` — reference for understanding the thresholds used in OrchestratorAgent
3. **Create** `backend/agents/light_sensor.py`
4. **Create** `backend/routes/light_sensor_routes.py`
5. **Register** routes in `backend/main.py`
6. **Test:** `curl http://localhost:8000/api/light/levels`
7. **Test time control:** `curl -X POST http://localhost:8000/api/light/time -d '{"hour": 12.0}'`
