# VisionAgent — AGENT.md

## Who Am I?

I am the **simulated camera** of the Smart Classroom system. In a real installation, I would be connected to a physical camera that uses computer vision to count people and find where they are sitting. Since everything is simulated for this project, I generate realistic occupancy data based on configurable scenarios.

My job is simple: answer the question **"How many people are in each zone of the classroom, and where are they?"**

## My Responsibilities

1. Simulate a camera feed that detects people in the classroom
2. Assign each detected person to one of the 4 classroom zones (A, B, C, D)
3. Track people positions as (x, y) coordinates on the classroom floor plan
4. Provide this data to the OrchestratorAgent every time it asks
5. Send person position data to the DigitalTwinAgent so the 3D view shows people

## My Skills

- [`SKILL_people_detection.md`](skills/SKILL_people_detection.md) — How to simulate detecting people and count them per zone
- [`SKILL_zone_mapping.md`](skills/SKILL_zone_mapping.md) — How to map (x, y) floor positions to the 4 classroom zones

## Files I Need to Create

### `backend/agents/vision.py`

```python
# VisionAgent — Simulates camera-based people detection

import random
import math
from datetime import datetime
from shared.classroom_state import CLASSROOM_ZONES

class VisionAgent:
    """
    Simulates a camera that detects people in the classroom.
    
    In a real system, this would:
    - Capture frames from a USB/IP camera
    - Run a YOLO or MediaPipe person detection model
    - Return bounding boxes converted to floor positions
    
    In this simulation:
    - We have configurable "scenarios" (full class, half class, etc.)
    - People positions are randomly distributed within realistic bounds
    - Positions update every cycle to simulate natural movement
    """

    def __init__(self):
        self.scenario = "full_class"     # Current simulation scenario
        self.people = []                  # List of {id, x, y, zone} dicts
        self._last_update = None

    def set_scenario(self, scenario: str):
        """
        Change the simulation scenario.
        
        Available scenarios:
        - "empty"       → 0 people
        - "few"         → 5-8 people, scattered
        - "half_class"  → 15-20 people, front half
        - "full_class"  → 30-35 people, all zones
        - "back_only"   → 10-15 people, back zones C+D only
        """
        self.scenario = scenario
        self.people = self._generate_people(scenario)

    def get_occupancy(self) -> dict:
        """
        Returns the number of people in each zone.
        Called by OrchestratorAgent every 5 seconds.
        """
        # Slightly shuffle positions each cycle to simulate movement
        self._nudge_positions()
        
        counts = {"zone_A": 0, "zone_B": 0, "zone_C": 0, "zone_D": 0}
        for person in self.people:
            zone = self._get_zone(person["x"], person["y"])
            person["zone"] = zone
            counts[zone] += 1
        
        counts["total"] = len(self.people)
        counts["timestamp"] = datetime.now().isoformat()
        return counts

    def get_people_positions(self) -> list:
        """
        Returns full position data for the 3D visualization.
        Each person is a dict with x, y coordinates and their zone.
        """
        return self.people

    def _generate_people(self, scenario: str) -> list:
        # See SKILL_people_detection.md for the full implementation
        pass

    def _get_zone(self, x: float, y: float) -> str:
        # See SKILL_zone_mapping.md for the full implementation
        pass

    def _nudge_positions(self):
        """Slightly move each person to simulate natural movement"""
        for person in self.people:
            person["x"] += random.uniform(-0.3, 0.3)
            person["y"] += random.uniform(-0.3, 0.3)
            # Keep within classroom bounds (0-10 meters wide, 0-8 meters deep)
            person["x"] = max(0.5, min(9.5, person["x"]))
            person["y"] = max(0.5, min(7.5, person["y"]))
```

### `backend/routes/vision_routes.py`

```python
# REST endpoints for VisionAgent
# GET  /api/vision/occupancy   → current people count per zone
# GET  /api/vision/positions   → list of all people with x,y coordinates
# POST /api/vision/scenario    → change simulation scenario
```

## API Endpoints I Expose

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/vision/occupancy` | People count per zone |
| GET | `/api/vision/positions` | Full position list for 3D rendering |
| POST | `/api/vision/scenario` | `{"scenario": "full_class"}` |

## Simulation Scenarios

These scenarios are what you'll demo at the STEAM fair. Each shows a different AI response:

| Scenario | People | Expected AI Response |
|---|---|---|
| `empty` | 0 | All lights OFF — saves 100% |
| `few` | ~6 | Only occupied zones ON |
| `half_class` | ~18 | Zones A+B ON, C+D OFF |
| `full_class` | ~32 | All zones evaluated per light level |
| `back_only` | ~12 | Only zones C+D ON |

## Data Format

### Occupancy Output
```json
{
  "zone_A": 8,
  "zone_B": 7,
  "zone_C": 10,
  "zone_D": 9,
  "total": 34,
  "timestamp": "2024-03-15T10:30:00"
}
```

### Positions Output (for 3D rendering)
```json
[
  {"id": 1, "x": 2.3, "y": 1.5, "zone": "zone_A"},
  {"id": 2, "x": 3.1, "y": 2.0, "zone": "zone_A"},
  {"id": 3, "x": 7.8, "y": 5.2, "zone": "zone_D"}
]
```

## Step-by-Step Build Instructions for Claude Code

1. **Read** `SKILL_people_detection.md` — implements `_generate_people()`
2. **Read** `SKILL_zone_mapping.md` — implements `_get_zone()`
3. **Create** `backend/agents/vision.py` with the full VisionAgent class
4. **Create** `backend/routes/vision_routes.py`
5. **Register** the vision routes in `backend/main.py`
6. **Test** with: `curl http://localhost:8000/api/vision/occupancy`
7. **Test** scenario change: `curl -X POST http://localhost:8000/api/vision/scenario -d '{"scenario":"empty"}'`
