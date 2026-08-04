# SKILL: People Detection Simulation

## What This Skill Does

Generates realistic simulated people detection data. Since we have no physical camera, this skill creates people with positions that make physical sense for a classroom — they sit at desks, not in the middle of the aisle or inside the walls.

## Classroom Floor Plan

```
Width: 10 meters (x: 0 → 10)
Depth: 8 meters  (y: 0 → 8)

(0,0) ─────────────────────── (10,0)
  │  [Window] [Window] [Window]  │  ← Front wall (whiteboard)
  │                               │
  │  Zone A      │   Zone B      │
  │  (x:0-5)     │   (x:5-10)   │
  │  (y:0-4)     │   (y:0-4)    │
  │              │               │
  │  Zone C      │   Zone D      │
  │  (x:0-5)     │   (x:5-10)   │
  │  (y:4-8)     │   (y:4-8)    │
  │                               │
(0,8) ─────────────────────── (10,8)
         [Door at back-right]

Windows: left wall (x=0), provide natural light to Zone A and C
```

## Desk Grid Layout

Desks are arranged in a 6×5 grid. Each desk position is a valid spawn point for a person.

```python
# backend/skills/people_detection.py

import random
from typing import Literal

# Valid desk positions (x, y) in meters
# Generated from a 6-column × 5-row desk grid
DESK_POSITIONS = [
    (x, y)
    for x in [1.2, 2.8, 4.4, 5.6, 7.2, 8.8]   # 6 columns
    for y in [1.0, 2.5, 4.0, 5.5, 7.0]          # 5 rows
]
# Total: 30 desk positions

ScenarioName = Literal["empty", "few", "half_class", "full_class", "back_only"]

def generate_people(scenario: ScenarioName) -> list[dict]:
    """
    Returns a list of people with positions based on the scenario.
    Each person is: {"id": int, "x": float, "y": float, "zone": str}
    Zone is computed later by zone_mapping skill.
    """

    scenario_config = {
        "empty":      {"count": 0,  "desks": DESK_POSITIONS},
        "few":        {"count": 6,  "desks": DESK_POSITIONS},
        "half_class": {"count": 18, "desks": [d for d in DESK_POSITIONS if d[1] <= 4.0]},
        "full_class": {"count": 30, "desks": DESK_POSITIONS},
        "back_only":  {"count": 12, "desks": [d for d in DESK_POSITIONS if d[1] > 4.0]},
    }

    config = scenario_config.get(scenario, scenario_config["full_class"])
    count = config["count"]
    available_desks = config["desks"]

    if count == 0:
        return []

    # Pick random desks (no two people at the same desk)
    selected_desks = random.sample(available_desks, min(count, len(available_desks)))

    people = []
    for i, (desk_x, desk_y) in enumerate(selected_desks):
        # Add slight random offset so people don't look like robots
        people.append({
            "id": i + 1,
            "x": round(desk_x + random.uniform(-0.2, 0.2), 2),
            "y": round(desk_y + random.uniform(-0.2, 0.2), 2),
            "zone": None  # Filled in by zone_mapping skill
        })

    return people


def nudge_positions(people: list[dict]) -> list[dict]:
    """
    Slightly moves each person each cycle to simulate natural movement.
    Called every 5 seconds to make the visualization feel alive.
    """
    for person in people:
        person["x"] = round(person["x"] + random.uniform(-0.15, 0.15), 2)
        person["y"] = round(person["y"] + random.uniform(-0.15, 0.15), 2)
        # Keep within classroom bounds
        person["x"] = max(0.3, min(9.7, person["x"]))
        person["y"] = max(0.3, min(7.7, person["y"]))
    return people
```

## How to Show This at the STEAM Fair

Use the scenario switcher in the UI to demonstrate each case:

1. **Start with `full_class`** → Show baseline energy (all lights on = 320W)
2. **Switch to AI mode** → Watch lights turn off based on zones
3. **Switch to `empty`** → All lights off instantly, show 0W
4. **Switch to `back_only`** → Only back lights on, front lights off
5. **Show the energy comparison graph** from DigitalTwinAgent

## Step-by-Step Build Instructions for Claude Code

1. **Create** `backend/skills/people_detection.py` with the code above
2. **Import** `generate_people` and `nudge_positions` into `backend/agents/vision.py`
3. **Wire** `generate_people()` → `VisionAgent._generate_people()`
4. **Wire** `nudge_positions()` → `VisionAgent._nudge_positions()`
5. **Test:** call `generate_people("half_class")` and confirm all y values are ≤ 4.0
