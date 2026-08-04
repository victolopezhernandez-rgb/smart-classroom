# SKILL: Light Threshold

## What This Skill Does

Defines and explains the threshold values that determine when natural light is enough to turn off artificial lights. This skill is a **reference document** — the actual thresholds are applied in the OrchestratorAgent's decision engine, but they are defined here so they are easy to change in one place.

## Threshold Constants

```python
# backend/shared/thresholds.py
# All threshold constants used across the system

# Natural light thresholds
NATURAL_LIGHT_OFF_THRESHOLD = 0.75   # Above this: turn lights OFF
NATURAL_LIGHT_DIM_THRESHOLD = 0.40   # Above this: DIM the lights (50% power)
                                      # Below 0.40: full power ON

# Occupancy thresholds
MIN_PEOPLE_TO_KEEP_LIGHTS_ON = 1     # Zone needs at least 1 person for lights to stay on

# Energy thresholds (for alerts in the dashboard)
HIGH_CONSUMPTION_ALERT_WATTS = 280   # Alert if consuming more than this (87.5% of max)
TARGET_SAVINGS_PERCENT = 40          # Goal: save at least 40% vs baseline
```

## Why These Specific Values?

### The 0.75 threshold for turning OFF

A value of 0.75 means the zone is receiving 75% of maximum sunlight. At this level, lux measurements in a real classroom would be approximately **400–500 lux**, which exceeds the recommended minimum for reading (300 lux per ISO 8995). This means humans would be perfectly comfortable without artificial light.

### The 0.40 threshold for DIMMING

At 0.40 (roughly 200 lux), natural light is present but not sufficient alone. Dimming to 50% adds ~100 lux artificially, reaching the 300 lux target while saving 50% of the electricity cost.

## Visual Reference

```
Natural Light Level (0.0 → 1.0)
│
1.0 ████ Maximum sunlight (noon, clear sky, Zone A)
    ████
0.75 ─── THRESHOLD: Lights OFF above this line ────────────────
    ████
    ████
0.40 ─── THRESHOLD: Lights DIMMED above this line ────────────
    ████
    ████
0.0  ████ No natural light (night, rainy, Zone D)

                    ▼               ▼               ▼
              LIGHTS ON        LIGHTS DIM       LIGHTS OFF
              (full power)     (50% power)
```

## Threshold Calibration Guide

If you want to adjust the thresholds for a different classroom:

| Situation | Suggested OFF threshold | Suggested DIM threshold |
|---|---|---|
| Many large windows | 0.65 | 0.35 |
| Standard classroom (this project) | 0.75 | 0.40 |
| Few/small windows | 0.85 | 0.55 |
| Dark room / basement | 0.95 | 0.70 |

## Step-by-Step Build Instructions for Claude Code

1. **Create** `backend/shared/thresholds.py` with the constants above
2. **Import** these constants in `backend/skills/decision_engine.py` (replace the hardcoded values there with imports from this file)
3. **Expose** the thresholds via a GET endpoint so the frontend can show them in the dashboard:
   - `GET /api/config/thresholds` → returns the current threshold values
4. **Optionally:** add a POST endpoint to allow live threshold adjustment during the demo
