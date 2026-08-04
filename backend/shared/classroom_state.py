from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

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
    """
    zones: dict = field(
        default_factory=lambda: {z: ZoneState() for z in CLASSROOM_ZONES}
    )
    total_watts: float = 0.0
    mode: Literal["AUTO", "MANUAL"] = "AUTO"
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    scenario: str = "full_class"
    weather: str = "clear"

    def update_lighting(self, zone: str, state: LightState, reason: str):
        if zone in self.zones:
            self.zones[zone].light = state
            self.zones[zone].reason = reason
        self.last_updated = datetime.now().isoformat()
        self._recalculate_watts()

    def update_occupancy(self, occupancy: dict):
        for zone, count in occupancy.items():
            if zone in self.zones:
                self.zones[zone].occupancy = count
        self.last_updated = datetime.now().isoformat()

    def update_natural_light(self, levels: dict):
        for zone, level in levels.items():
            if zone in self.zones:
                self.zones[zone].natural_light = level
        self.last_updated = datetime.now().isoformat()

    def to_dict(self) -> dict:
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
