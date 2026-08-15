from __future__ import annotations
import time
from datetime import datetime

from shared.classroom_state import CLASSROOM_ZONES
from shared.logger import get_logger
from shared.thresholds import (
    LIVE_STALE_SECONDS,
    ROOM_WIDTH_M,
    ROOM_DEPTH_M,
    MAX_LIVE_DETECTIONS,
)
from skills.people_detection import generate_people, nudge_positions, SCENARIO_CONFIG
from skills.zone_mapping import get_zone

logger = get_logger("VisionAgent")

VALID_SCENARIOS = list(SCENARIO_CONFIG.keys())


class VisionAgent:
    """
    Camera-based people detection system with two operating modes.

    - "simulated": generates realistic desk-based positions per scenario.
    - "live_camera": receives real detections from the browser webcam
      (normalized camera coordinates), maps them to room coordinates and
      feeds them to the rest of the system.

    The Orchestrator, decision engine and digital twin are completely
    agnostic to which mode is active — only this sensor layer changes.
    """

    def __init__(self):
        self.scenario = "full_class"
        self.source = "simulated"          # "simulated" | "live_camera"
        self.people: list[dict] = []
        self._live_people: list[dict] = []
        self._live_updated_at: float = 0.0
        self._regenerate()
        logger.info(f"VisionAgent started — scenario: {self.scenario}")

    # ── Public interface (called by Orchestrator + Routes) ────────────────────

    def set_scenario(self, scenario: str):
        """Switch simulation scenario and regenerate people positions."""
        if scenario not in VALID_SCENARIOS:
            raise ValueError(f"Unknown scenario '{scenario}'. Valid: {VALID_SCENARIOS}")
        self.scenario = scenario
        if self.source != "simulated":
            logger.info("Scenario selected — vision mode back to simulated")
        self.source = "simulated"
        self._regenerate()
        logger.info(f"Scenario → {scenario} ({len(self.people)} people)")

    def set_source(self, mode: str):
        """Explicitly switch between 'simulated' and 'live_camera'."""
        if mode not in ("simulated", "live_camera"):
            raise ValueError(f"Unknown vision mode '{mode}'. Use 'simulated' or 'live_camera'")
        if mode == "simulated":
            if self.source != "simulated":
                logger.info("Vision mode → simulated")
            self.source = "simulated"
            self._regenerate()
        else:
            self.source = "live_camera"
            self._live_people = []
            self._live_updated_at = time.monotonic()
            logger.info("Vision mode → live_camera (waiting for detections)")

    def set_live_detections(self, normalized: list[dict]) -> int:
        """
        Receive real detections from the browser camera.

        Each item is {"x": 0..1, "y": 0..1} in MIRRORED camera space
        (x=0 is the left edge of the displayed video). Coordinates are
        mapped to room meters and a zone is assigned.

        Switches the agent to live_camera mode. Returns the accepted count.
        """
        people = []
        for i, det in enumerate(normalized[:MAX_LIVE_DETECTIONS]):
            try:
                cx = float(det.get("x", 0.5))
                cy = float(det.get("y", 0.5))
            except (TypeError, ValueError):
                continue
            cx = max(0.0, min(1.0, cx))
            cy = max(0.0, min(1.0, cy))
            x = round(cx * ROOM_WIDTH_M, 2)
            y = round(cy * ROOM_DEPTH_M, 2)
            people.append({"id": i + 1, "x": x, "y": y, "zone": get_zone(x, y)})

        if self.source != "live_camera":
            logger.info(f"Vision mode → live_camera (first detections: {len(people)} people)")
        self.source = "live_camera"
        self._live_people = people
        self._live_updated_at = time.monotonic()
        return len(people)

    def live_stale_seconds(self) -> float:
        """Seconds since the last live detection (0 if not in live mode)."""
        if self.source != "live_camera" or not self._live_updated_at:
            return 0.0
        return time.monotonic() - self._live_updated_at

    def get_occupancy(self) -> dict:
        """
        Returns people count per zone + total.
        In simulated mode nudges positions slightly to fake movement.
        Called by OrchestratorAgent every cycle.
        """
        if self.source == "live_camera":
            stale = self.live_stale_seconds()
            if stale > LIVE_STALE_SECONDS:
                logger.warning(
                    f"Live camera data stale ({stale:.1f}s) — falling back to simulation"
                )
                self.source = "simulated"
                self._regenerate()
            else:
                counts = {z: 0 for z in CLASSROOM_ZONES}
                for person in self._live_people:
                    counts[person["zone"]] += 1
                counts["total"] = len(self._live_people)
                counts["timestamp"] = datetime.now().isoformat()
                counts["scenario"] = "live_camera"
                return counts

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
        if self.source == "live_camera":
            return self._live_people
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
