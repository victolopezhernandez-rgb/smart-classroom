# SKILL: Zone Mapping

## What This Skill Does

Converts an (x, y) floor position in meters into one of the 4 classroom zones (A, B, C, D). This is what VisionAgent uses to group people by zone and tell the OrchestratorAgent which zones are occupied.

## Zone Boundaries

```
Zone A: x ∈ [0, 5),  y ∈ [0, 4)   → Front-Left
Zone B: x ∈ [5, 10], y ∈ [0, 4)   → Front-Right
Zone C: x ∈ [0, 5),  y ∈ [4, 8]   → Back-Left
Zone D: x ∈ [5, 10], y ∈ [4, 8]   → Back-Right
```

Visual:
```
x=0          x=5          x=10
 ┌────────────┬────────────┐  y=0 (front wall / whiteboard)
 │            │            │
 │   Zone A   │   Zone B   │
 │            │            │
 ├────────────┼────────────┤  y=4 (middle of room)
 │            │            │
 │   Zone C   │   Zone D   │
 │            │            │
 └────────────┴────────────┘  y=8 (back wall / door)
```

## Implementation

```python
# backend/skills/zone_mapping.py

def get_zone(x: float, y: float) -> str:
    """
    Maps a floor coordinate (x, y) to a classroom zone.
    
    Args:
        x: Horizontal position in meters (0 = left wall, 10 = right wall)
        y: Depth position in meters (0 = front/whiteboard, 8 = back/door)
    
    Returns:
        One of: "zone_A", "zone_B", "zone_C", "zone_D"
    """
    if x < 5:
        return "zone_A" if y < 4 else "zone_C"
    else:
        return "zone_B" if y < 4 else "zone_D"


def get_zone_bounds(zone: str) -> dict:
    """
    Returns the x,y boundary box for a given zone.
    Used by the 3D renderer to draw zone highlight overlays.
    
    Returns:
        {"x_min": float, "x_max": float, "y_min": float, "y_max": float}
    """
    bounds = {
        "zone_A": {"x_min": 0, "x_max": 5, "y_min": 0, "y_max": 4},
        "zone_B": {"x_min": 5, "x_max": 10, "y_min": 0, "y_max": 4},
        "zone_C": {"x_min": 0, "x_max": 5, "y_min": 4, "y_max": 8},
        "zone_D": {"x_min": 5, "x_max": 10, "y_min": 4, "y_max": 8},
    }
    return bounds.get(zone, {})


def get_zone_center(zone: str) -> tuple[float, float]:
    """
    Returns the center (x, y) of a zone.
    Used to position light fixtures above zones in the 3D model.
    """
    centers = {
        "zone_A": (2.5, 2.0),
        "zone_B": (7.5, 2.0),
        "zone_C": (2.5, 6.0),
        "zone_D": (7.5, 6.0),
    }
    return centers.get(zone, (5.0, 4.0))


def get_light_positions(zone: str) -> list[tuple[float, float]]:
    """
    Returns the (x, y) positions of the 2 light fixtures in each zone.
    Used to render lights in the correct positions on the 3D ceiling.
    """
    lights = {
        "zone_A": [(1.5, 1.5), (3.5, 2.5)],
        "zone_B": [(6.5, 1.5), (8.5, 2.5)],
        "zone_C": [(1.5, 5.5), (3.5, 6.5)],
        "zone_D": [(6.5, 5.5), (8.5, 6.5)],
    }
    return lights.get(zone, [])
```

## Tests

```python
# Quick tests to verify zone mapping is correct

from skills.zone_mapping import get_zone

assert get_zone(1.0, 1.0) == "zone_A"   # Front-left corner
assert get_zone(9.0, 1.0) == "zone_B"   # Front-right corner
assert get_zone(1.0, 7.0) == "zone_C"   # Back-left corner
assert get_zone(9.0, 7.0) == "zone_D"   # Back-right corner
assert get_zone(5.0, 4.0) == "zone_D"   # Center point → zone D (boundary)

print("Zone mapping tests passed!")
```

## Step-by-Step Build Instructions for Claude Code

1. **Create** `backend/skills/zone_mapping.py` with all four functions
2. **Import** `get_zone` into `backend/agents/vision.py`
3. **Wire** `get_zone(x, y)` → `VisionAgent._get_zone()`
4. **Import** `get_light_positions` into `backend/agents/digital_twin.py` for 3D rendering
5. **Test** with the assertions above before moving on
