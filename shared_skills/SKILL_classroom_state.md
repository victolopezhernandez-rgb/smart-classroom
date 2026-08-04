# SHARED SKILL: Classroom State

## What This Skill Does

Defines the `ClassroomState` class — the single shared data structure that all agents read from and write to. Think of it as the "memory" of the system: it always knows the current state of every zone, every sensor, and every light.

## Implementation

```python
# backend/shared/classroom_state.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

# Zone names used throughout the system
CLASSROOM_ZONES = ["zone_A", "zone_B", "zone_C", "zone_D"]

LightState = Literal["ON", "DIM", "OFF"]

@dataclass
class ZoneState:
    light: LightState = "OFF"
    reason: str = ""
    occupancy: int = 0
    natural_light: float = 0.0

@dataclass
class ClassroomState:
    """
    The authoritative state of the classroom at any given moment.
    Shared across all agents. Updated by DigitalTwinAgent.
    
    Attributes:
        zones:          Per-zone state (light, occupancy, natural light)
        total_watts:    Current power consumption in watts
        mode:           "AUTO" (AI in control) or "MANUAL" (voice/user override)
        last_updated:   ISO timestamp of the last state update
    """
    zones: dict[str, ZoneState] = field(
        default_factory=lambda: {z: ZoneState() for z in CLASSROOM_ZONES}
    )
    total_watts: float = 0.0
    mode: Literal["AUTO", "MANUAL"] = "AUTO"
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    scenario: str = "full_class"
    weather: str = "clear"

    def update_lighting(self, zone: str, state: LightState, reason: str):
        """Update the light state of a single zone."""
        if zone in self.zones:
            self.zones[zone].light = state
            self.zones[zone].reason = reason
        self.last_updated = datetime.now().isoformat()
        self._recalculate_watts()

    def update_occupancy(self, occupancy: dict):
        """Update people count for all zones at once."""
        for zone, count in occupancy.items():
            if zone in self.zones:
                self.zones[zone].occupancy = count
        self.last_updated = datetime.now().isoformat()

    def update_natural_light(self, levels: dict):
        """Update natural light levels for all zones."""
        for zone, level in levels.items():
            if zone in self.zones:
                self.zones[zone].natural_light = level
        self.last_updated = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Serializes the full state for JSON/WebSocket transmission."""
        return {
            "zones": {
                zone: {
                    "light": s.light,
                    "reason": s.reason,
                    "occupancy": s.occupancy,
                    "natural_light": round(s.natural_light, 2),
                }
                for zone, s in self.zones.items()
            },
            "total_watts": round(self.total_watts, 1),
            "mode": self.mode,
            "last_updated": self.last_updated,
            "scenario": self.scenario,
            "weather": self.weather,
        }

    def _recalculate_watts(self):
        watts_map = {"ON": 80.0, "DIM": 40.0, "OFF": 0.0}
        self.total_watts = sum(
            watts_map.get(s.light, 0) for s in self.zones.values()
        )


# Global singleton — import this wherever you need the classroom state
classroom_state = ClassroomState()
```

## Usage Across Agents

```python
# In any agent file:
from shared.classroom_state import classroom_state, CLASSROOM_ZONES

# Read current state of a zone:
zone_a_light = classroom_state.zones["zone_A"].light   # "ON", "DIM", or "OFF"

# Update lighting after a decision:
classroom_state.update_lighting("zone_A", "OFF", "Natural light at 82%")

# Get full state for WebSocket broadcast:
state_dict = classroom_state.to_dict()
```

## Step-by-Step Build Instructions for Claude Code

1. **Create** `backend/shared/classroom_state.py` with the code above
2. **Import** `classroom_state` (the singleton) in:
   - `backend/agents/orchestrator.py`
   - `backend/agents/digital_twin.py`
3. **Never** import `ClassroomState` (the class) in agents — always use the singleton
4. **Test**: in `backend/main.py` startup, log `classroom_state.to_dict()` — should show all zones OFF
