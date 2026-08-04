from __future__ import annotations
from datetime import datetime

from shared.classroom_state import CLASSROOM_ZONES
from shared.logger import get_logger
from skills.people_detection import generate_people, nudge_positions, SCENARIO_CONFIG
from skills.zone_mapping import get_zone

logger = get_logger("VisionAgent")

VALID_SCENARIOS = list(SCENARIO_CONFIG.keys())


class VisionAgent:
    """
    Simulates a camera-based people detection system.

    In a real installation this would run YOLO/MediaPipe on a camera feed.
    Here it generates realistic desk-based positions per configurable scenario.
    """

    def __init__(self):
        self.scenario = "full_class"
        self.people: list[dict] = []
        self._regenerate()
        logger.info(f"VisionAgent started — scenario: {self.scenario}")

    # ── Public interface (called by Orchestrator + Routes) ────────────────────

    def set_scenario(self, scenario: str):
        """Switch simulation scenario and regenerate people positions."""
        if scenario not in VALID_SCENARIOS:
            raise ValueError(f"Unknown scenario '{scenario}'. Valid: {VALID_SCENARIOS}")
        self.scenario = scenario
        self._regenerate()
        logger.info(f"Scenario → {scenario} ({len(self.people)} people)")

    def get_occupancy(self) -> dict:
        """
        Returns people count per zone + total.
        Nudges positions slightly each call to simulate movement.
        Called by OrchestratorAgent every cycle.
        """
        nudge_positions(self.people)
        self._assign_zones()

        counts = {z: 0 for z in CLASSROOM_ZONES}
        for person in self.people:
            counts[person["zone"]] += 1

        counts["total"] = len(self.people)
        counts["timestamp"] = datetime.now().isoformat()
        counts["scenario"] = self.scenario
        return counts

    def get_people_positions(self) -> list[dict]:
        """Returns full position list for 3D visualization."""
        return self.people

    # ── Private ───────────────────────────────────────────────────────────────

    def _regenerate(self):
        self.people = generate_people(self.scenario)
        self._assign_zones()

    def _assign_zones(self):
        for person in self.people:
            person["zone"] = get_zone(person["x"], person["y"])


# Singleton
vision_agent = VisionAgent()
