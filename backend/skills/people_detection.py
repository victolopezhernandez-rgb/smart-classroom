from __future__ import annotations
import random
from typing import Literal

# Valid desk positions (x, y) in meters — 6 columns × 5 rows = 30 desks
DESK_POSITIONS = [
    (x, y)
    for x in [1.2, 2.8, 4.4, 5.6, 7.2, 8.8]
    for y in [1.0, 2.5, 4.0, 5.5, 7.0]
]

ScenarioName = Literal["empty", "few", "half_class", "full_class", "back_only"]

SCENARIO_CONFIG = {
    "empty":      {"count": 0,  "desks": DESK_POSITIONS},
    "few":        {"count": 6,  "desks": DESK_POSITIONS},
    "half_class": {"count": 12, "desks": [d for d in DESK_POSITIONS if d[1] < 4.0]},
    "full_class": {"count": 30, "desks": DESK_POSITIONS},
    "back_only":  {"count": 12, "desks": [d for d in DESK_POSITIONS if d[1] > 4.0]},
}


def generate_people(scenario: ScenarioName) -> list[dict]:
    """
    Returns a list of people with desk-based positions for the given scenario.
    Each person: {"id": int, "x": float, "y": float, "zone": None}
    Zone is filled in later by zone_mapping.
    """
    config = SCENARIO_CONFIG.get(scenario, SCENARIO_CONFIG["full_class"])
    count = config["count"]
    available = config["desks"]

    if count == 0:
        return []

    selected = random.sample(available, min(count, len(available)))
    return [
        {
            "id": i + 1,
            "x": round(dx + random.uniform(-0.2, 0.2), 2),
            "y": round(dy + random.uniform(-0.2, 0.2), 2),
            "zone": None,
        }
        for i, (dx, dy) in enumerate(selected)
    ]


def nudge_positions(people: list[dict]) -> list[dict]:
    """Slightly move each person each cycle to simulate natural movement."""
    for person in people:
        person["x"] = round(person["x"] + random.uniform(-0.15, 0.15), 2)
        person["y"] = round(person["y"] + random.uniform(-0.15, 0.15), 2)
        person["x"] = max(0.3, min(9.7, person["x"]))
        person["y"] = max(0.3, min(7.7, person["y"]))
    return people
