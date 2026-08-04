# SKILL: Decision Engine

## What This Skill Does

This skill contains the core AI logic that decides which lights to turn ON, DIM, or OFF. It is used exclusively by the OrchestratorAgent inside its `decide()` method.

## Decision Rules (in priority order)

Rules are checked from top to bottom. The first rule that matches wins.

```
Priority 1 — Voice Command Override
  IF voice_command is not None
  THEN apply the voice command exactly as given
  REASON: Human always has final say

Priority 2 — Empty Classroom
  IF total_people == 0
  THEN ALL zones → OFF
  REASON: No one in the room, no lights needed

Priority 3 — Natural Light Sufficient
  FOR EACH zone:
    IF natural_light[zone] >= 0.75
    THEN zone → OFF
    REASON: Enough sunlight, no electricity needed

Priority 4 — Natural Light Partial
  FOR EACH zone:
    IF 0.40 <= natural_light[zone] < 0.75
    THEN zone → DIM (50% power)
    REASON: Some sunlight, reduce electricity usage

Priority 5 — Zone Unoccupied
  FOR EACH zone:
    IF occupancy[zone] == 0
    THEN zone → OFF
    REASON: No people in this zone

Priority 6 — Default
  zone → ON (100% power)
  REASON: Zone is occupied and needs full light
```

## Python Implementation

```python
# backend/skills/decision_engine.py

NATURAL_LIGHT_OFF_THRESHOLD = 0.75   # 75% natural light → lights off
NATURAL_LIGHT_DIM_THRESHOLD = 0.40   # 40-75% natural light → lights dimmed

def run_decision_engine(occupancy: dict, natural_light: dict, voice_cmd: str | None) -> dict:
    """
    Returns a dict with the lighting state for each zone.
    
    Args:
        occupancy:     {"zone_A": 5, "zone_B": 0, "zone_C": 12, "zone_D": 3}
        natural_light: {"zone_A": 0.85, "zone_B": 0.60, "zone_C": 0.20, "zone_D": 0.15}
        voice_cmd:     "lights on zone A" | "all lights off" | None

    Returns:
        {
            "zone_A": {"state": "OFF", "reason": "High natural light"},
            "zone_B": {"state": "DIM", "reason": "Partial natural light"},
            "zone_C": {"state": "ON",  "reason": "Occupied, low natural light"},
            "zone_D": {"state": "ON",  "reason": "Occupied, low natural light"},
        }
    """
    zones = ["zone_A", "zone_B", "zone_C", "zone_D"]
    result = {}

    # Priority 1: Voice command override
    if voice_cmd:
        return apply_voice_command(voice_cmd, zones)

    total_people = sum(occupancy.values())

    # Priority 2: Empty classroom
    if total_people == 0:
        return {zone: {"state": "OFF", "reason": "Classroom is empty"} for zone in zones}

    # Priority 3-6: Zone-by-zone analysis
    for zone in zones:
        light_level = natural_light.get(zone, 0.0)
        people_count = occupancy.get(zone, 0)

        if light_level >= NATURAL_LIGHT_OFF_THRESHOLD:
            result[zone] = {
                "state": "OFF",
                "reason": f"Natural light at {int(light_level * 100)}% — sufficient"
            }
        elif light_level >= NATURAL_LIGHT_DIM_THRESHOLD:
            result[zone] = {
                "state": "DIM",
                "reason": f"Natural light at {int(light_level * 100)}% — dimming to save energy"
            }
        elif people_count == 0:
            result[zone] = {
                "state": "OFF",
                "reason": f"No people in {zone}"
            }
        else:
            result[zone] = {
                "state": "ON",
                "reason": f"{people_count} people present, low natural light"
            }

    return result


def apply_voice_command(command: str, zones: list) -> dict:
    """
    Parses a voice command string and returns the corresponding lighting state.
    
    Supported commands:
    - "all lights on"         → all zones ON
    - "all lights off"        → all zones OFF
    - "lights on zone A"      → zone_A ON, others unchanged
    - "lights off zone B"     → zone_B OFF, others unchanged
    - "dim all lights"        → all zones DIM
    """
    command = command.lower().strip()
    
    if "all lights on" in command:
        return {zone: {"state": "ON", "reason": "Voice command: all on"} for zone in zones}
    
    if "all lights off" in command:
        return {zone: {"state": "OFF", "reason": "Voice command: all off"} for zone in zones}
    
    if "dim all" in command:
        return {zone: {"state": "DIM", "reason": "Voice command: dim all"} for zone in zones}

    # Zone-specific commands
    zone_map = {"a": "zone_A", "b": "zone_B", "c": "zone_C", "d": "zone_D"}
    result = {}
    for letter, zone_key in zone_map.items():
        if f"zone {letter}" in command:
            if "on" in command:
                result[zone_key] = {"state": "ON", "reason": f"Voice command: {zone_key} on"}
            elif "off" in command:
                result[zone_key] = {"state": "OFF", "reason": f"Voice command: {zone_key} off"}
    
    return result if result else {}


def calculate_energy_watts(lighting_state: dict) -> float:
    """
    Calculates total power consumption in watts based on current lighting state.
    Each zone has 2 fixtures × 40W each = 80W per zone maximum.
    """
    watts_per_zone = {
        "ON":  80.0,   # 2 fixtures × 40W
        "DIM": 40.0,   # 50% power
        "OFF":  0.0
    }
    total = 0.0
    for zone, data in lighting_state.items():
        state = data.get("state", "OFF")
        total += watts_per_zone.get(state, 0.0)
    return total
```

## Energy Calculation Reference

| Scenario | Zones ON | Watts | kWh/day (8h) |
|---|---|---|---|
| Baseline (all on) | 4 | 320W | 2.56 kWh |
| AI — partial occupancy | 2 | 160W | 1.28 kWh |
| AI — half natural light | 4 DIM | 160W | 1.28 kWh |
| AI — mixed (typical) | 2 ON + 1 DIM | 200W | 1.60 kWh |
| AI — best case | 0 | 0W | 0 kWh |

## How to Test This Skill

```python
# Run this to verify the decision engine works correctly

from skills.decision_engine import run_decision_engine

# Test 1: Empty classroom
result = run_decision_engine(
    occupancy={"zone_A": 0, "zone_B": 0, "zone_C": 0, "zone_D": 0},
    natural_light={"zone_A": 0.5, "zone_B": 0.5, "zone_C": 0.5, "zone_D": 0.5},
    voice_cmd=None
)
assert all(z["state"] == "OFF" for z in result.values()), "Empty classroom test failed"

# Test 2: High natural light → lights off
result = run_decision_engine(
    occupancy={"zone_A": 10, "zone_B": 5, "zone_C": 8, "zone_D": 3},
    natural_light={"zone_A": 0.9, "zone_B": 0.8, "zone_C": 0.2, "zone_D": 0.1},
    voice_cmd=None
)
assert result["zone_A"]["state"] == "OFF",  "High natural light test failed"
assert result["zone_C"]["state"] == "ON",   "Low natural light test failed"

# Test 3: Voice command overrides everything
result = run_decision_engine(
    occupancy={"zone_A": 0, "zone_B": 0, "zone_C": 0, "zone_D": 0},
    natural_light={"zone_A": 0.9, "zone_B": 0.9, "zone_C": 0.9, "zone_D": 0.9},
    voice_cmd="all lights on"
)
assert all(z["state"] == "ON" for z in result.values()), "Voice override test failed"

print("All tests passed!")
```
