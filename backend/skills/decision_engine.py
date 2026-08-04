from shared.thresholds import (
    NATURAL_LIGHT_OFF_THRESHOLD,
    NATURAL_LIGHT_DIM_THRESHOLD,
    MIN_PEOPLE_TO_KEEP_LIGHTS_ON,
)

CLASSROOM_ZONES = ["zone_A", "zone_B", "zone_C", "zone_D"]


def run_decision_engine(occupancy: dict, natural_light: dict) -> dict:
    """
    Core AI logic: decides the optimal lighting state for every zone.

    Rules (checked in priority order per zone):
      1. Natural light >= 0.75  → OFF   (enough sunlight)
      2. Natural light >= 0.40  → DIM   (partial sunlight, save 50%)
      3. Zone has 0 people      → OFF   (unoccupied)
      4. Default                → ON    (occupied, low natural light)

    Args:
        occupancy:     {"zone_A": 5, "zone_B": 0, ...}  — from VisionAgent
        natural_light: {"zone_A": 0.85, "zone_B": 0.3, ...}  — from LightSensorAgent

    Returns:
        {
          "zone_A": {"state": "OFF", "reason": "Natural light at 85% — sufficient"},
          "zone_B": {"state": "ON",  "reason": "4 people present, low natural light"},
          ...
        }
    """
    total_people = sum(
        v for k, v in occupancy.items()
        if k in CLASSROOM_ZONES
    )

    # Priority 2: Empty classroom → all OFF
    if total_people < MIN_PEOPLE_TO_KEEP_LIGHTS_ON:
        return {
            zone: {"state": "OFF", "reason": "Classroom is empty"}
            for zone in CLASSROOM_ZONES
        }

    result = {}
    for zone in CLASSROOM_ZONES:
        light_level   = natural_light.get(zone, 0.0)
        people_count  = occupancy.get(zone, 0)
        pct           = int(light_level * 100)

        if light_level >= NATURAL_LIGHT_OFF_THRESHOLD:
            result[zone] = {
                "state":  "OFF",
                "reason": f"Natural light at {pct}% — sufficient",
            }
        elif light_level >= NATURAL_LIGHT_DIM_THRESHOLD:
            result[zone] = {
                "state":  "DIM",
                "reason": f"Natural light at {pct}% — dimming to save energy",
            }
        elif people_count < MIN_PEOPLE_TO_KEEP_LIGHTS_ON:
            result[zone] = {
                "state":  "OFF",
                "reason": f"No people in {zone}",
            }
        else:
            result[zone] = {
                "state":  "ON",
                "reason": f"{people_count} people present, low natural light ({pct}%)",
            }

    return result


def calculate_energy_watts(lighting_state: dict) -> float:
    """Total power consumption in watts for the given lighting state."""
    watts_map = {"ON": 80.0, "DIM": 40.0, "OFF": 0.0}
    return sum(
        watts_map.get(data.get("state", "OFF"), 0.0)
        for data in lighting_state.values()
        if isinstance(data, dict)
    )
