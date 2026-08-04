# SKILL: Natural Light Simulation

## What This Skill Does

Calculates how much natural light enters each classroom zone based on the time of day, weather, and the physical position of windows. The result is a value between 0.0 (complete darkness) and 1.0 (maximum sunlight).

## The Physics Behind It (simplified)

Natural light in a classroom depends on:
1. **Sun intensity curve** — peaks at noon, zero at night (modeled as a bell curve)
2. **Weather multiplier** — clouds reduce light (clear=1.0, rainy=0.15)
3. **Zone distance from windows** — closer = more light (windows are on the left wall)

## Implementation

```python
# backend/skills/natural_light_simulation.py

import math

# School hours: 6 AM = sunrise, 18:00 = sunset (conservative)
SUNRISE_HOUR = 6.0
SUNSET_HOUR  = 18.0

# Weather multipliers (how much weather reduces natural light)
WEATHER_MULTIPLIERS = {
    "clear":    1.00,   # Full sunlight
    "cloudy":   0.55,   # Partly cloudy
    "overcast": 0.30,   # Heavy clouds
    "rainy":    0.15,   # Rain blocks most light
}

# Window exposure per zone
# Windows are on the LEFT WALL (x=0), so zones A and C face windows directly
# Zones B and D receive reflected/diffused light only
WINDOW_EXPOSURE = {
    "zone_A": 1.00,   # Front-left: direct window exposure
    "zone_C": 0.70,   # Back-left: window exposure, slightly less
    "zone_B": 0.40,   # Front-right: reflected light only
    "zone_D": 0.20,   # Back-right: minimal light, farthest from windows
}


def calculate_sun_intensity(hour: float) -> float:
    """
    Returns sun intensity (0.0 to 1.0) for a given hour of day.
    Uses a sine curve that peaks at solar noon (12:00).
    Returns 0.0 before sunrise and after sunset.
    
    Args:
        hour: Hour of day (0.0 to 23.99)
    
    Returns:
        float between 0.0 and 1.0
    """
    if hour < SUNRISE_HOUR or hour > SUNSET_HOUR:
        return 0.0
    
    # Map the hour into a 0-π range for a sine wave
    # Sunrise (6h) → 0, Noon (12h) → π/2, Sunset (18h) → π
    normalized = (hour - SUNRISE_HOUR) / (SUNSET_HOUR - SUNRISE_HOUR)
    intensity = math.sin(normalized * math.pi)
    
    return round(max(0.0, min(1.0, intensity)), 3)


def calculate_light_levels(hour: float, weather: str) -> dict:
    """
    Calculates natural light level (0.0-1.0) for each classroom zone.
    
    Args:
        hour:    Current hour (0.0-23.99)
        weather: One of "clear", "cloudy", "overcast", "rainy"
    
    Returns:
        {"zone_A": 0.82, "zone_B": 0.31, "zone_C": 0.55, "zone_D": 0.18}
    """
    sun = calculate_sun_intensity(hour)
    weather_factor = WEATHER_MULTIPLIERS.get(weather, 1.0)
    
    result = {}
    for zone, exposure in WINDOW_EXPOSURE.items():
        raw_level = sun * weather_factor * exposure
        result[zone] = round(max(0.0, min(1.0, raw_level)), 3)
    
    return result
```

## Example Values Table

| Time | Weather | Zone A | Zone B | Zone C | Zone D |
|---|---|---|---|---|---|
| 06:00 (dawn) | clear | 0.00 | 0.00 | 0.00 | 0.00 |
| 08:00 | clear | 0.64 | 0.26 | 0.45 | 0.13 |
| 10:00 | clear | 0.91 | 0.36 | 0.64 | 0.18 |
| 12:00 (noon) | clear | 1.00 | 0.40 | 0.70 | 0.20 |
| 12:00 | cloudy | 0.55 | 0.22 | 0.39 | 0.11 |
| 12:00 | rainy | 0.15 | 0.06 | 0.11 | 0.03 |
| 16:00 | clear | 0.91 | 0.36 | 0.64 | 0.18 |
| 18:00 (dusk) | clear | 0.00 | 0.00 | 0.00 | 0.00 |
| 20:00 (night) | clear | 0.00 | 0.00 | 0.00 | 0.00 |

## What the AI Decides Based on These Values

| Zone A value | OrchestratorAgent decision |
|---|---|
| ≥ 0.75 | Zone A lights → OFF (save 80W) |
| 0.40–0.74 | Zone A lights → DIM (save 40W) |
| < 0.40 | Zone A lights → ON (full power) |

## Step-by-Step Build Instructions for Claude Code

1. **Create** `backend/skills/natural_light_simulation.py` with the code above
2. **Import** `calculate_light_levels` into `backend/agents/light_sensor.py`
3. **Wire** it to `LightSensorAgent.get_levels()`
4. **Verify** with this quick test:

```python
from skills.natural_light_simulation import calculate_light_levels

# At noon, clear sky → Zone A should be very bright
levels = calculate_light_levels(12.0, "clear")
assert levels["zone_A"] == 1.0,  "Zone A at noon should be 1.0"
assert levels["zone_D"] == 0.2,  "Zone D at noon should be 0.2"

# At night → all zeros
levels = calculate_light_levels(22.0, "clear")
assert all(v == 0.0 for v in levels.values()), "Night should be all zeros"

print("Natural light simulation tests passed!")
```
