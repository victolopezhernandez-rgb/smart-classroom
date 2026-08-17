
from shared.classroom_state import classroom_state, CLASSROOM_ZONES
from shared.thresholds import BASELINE_WATTS, HIGH_CONSUMPTION_ALERT_WATTS
from shared.logger import get_logger
from shared import clock
from skills.energy_tracker import EnergyTracker

logger = get_logger("DigitalTwinAgent")


class DigitalTwinAgent:
    """
    Maintains the authoritative classroom state and energy consumption log.

    Receives lighting decisions from OrchestratorAgent, updates the shared
    ClassroomState singleton, and records energy readings to CSV.
    """

    def __init__(self):
        session_id = clock.now().strftime("%Y%m%d_%H%M%S")
        self.tracker = EnergyTracker(session_id)
        self.mode = "AI"   # "AI" or "BASELINE"
        logger.info(f"DigitalTwinAgent started — session {session_id}")

    # ── Called by OrchestratorAgent ───────────────────────────────────────────

    def apply_state(self, lighting_state: dict):
        """
        Apply a full lighting decision from the Orchestrator.

        lighting_state format:
            {
              "zone_A": {"state": "ON",  "reason": "People detected"},
              "zone_B": {"state": "OFF", "reason": "Natural light 82%"},
              ...
            }
        """
        for zone, data in lighting_state.items():
            if isinstance(data, dict):
                classroom_state.update_lighting(zone, data.get("state", "OFF"), data.get("reason", ""))

        reading = self.tracker.log_reading(lighting_state, mode=self.mode)

        if reading.watts >= HIGH_CONSUMPTION_ALERT_WATTS:
            logger.warning(f"HIGH CONSUMPTION ALERT: {reading.watts}W")

        logger.info(f"State applied | {reading.watts}W | mode={self.mode}")

    # ── Called by VisionAgent ─────────────────────────────────────────────────

    def update_people(self, people: list):
        classroom_state.update_occupancy({
            p["zone"]: classroom_state.zones[p["zone"]].occupancy + 1
            for p in people if p.get("zone") in CLASSROOM_ZONES
        })

    def update_people_positions(self, people: list):
        """Store raw position list (for frontend 3D rendering)."""
        self._people_positions = people
        # Reset occupancy counts then recount from positions
        occupancy = {z: 0 for z in CLASSROOM_ZONES}
        for p in people:
            zone = p.get("zone")
            if zone in occupancy:
                occupancy[zone] += 1
        classroom_state.update_occupancy(occupancy)

    # ── Called by LightSensorAgent ────────────────────────────────────────────

    def update_natural_light(self, levels: dict):
        classroom_state.update_natural_light(levels)

    # ── Mode control ──────────────────────────────────────────────────────────

    def set_mode(self, mode: str):
        self.mode = mode
        classroom_state.mode = mode
        if mode == "BASELINE":
            forced = {z: {"state": "ON", "reason": "Baseline measurement"} for z in CLASSROOM_ZONES}
            self.apply_state(forced)
            logger.info("Switched to BASELINE mode — all lights forced ON")
        else:
            logger.info("Switched to AI mode")

    # ── State accessors ───────────────────────────────────────────────────────

    def get_full_state(self) -> dict:
        state = classroom_state.to_dict()
        state["people"] = getattr(self, "_people_positions", [])
        state["energy"] = {
            "current_watts":    classroom_state.total_watts,
            "baseline_watts":   BASELINE_WATTS,
            "savings_watts":    round(BASELINE_WATTS - classroom_state.total_watts, 1),
            "savings_percent":  round((BASELINE_WATTS - classroom_state.total_watts) / BASELINE_WATTS * 100, 1),
        }
        return state

    def reset_session(self):
        """Clear energy log and start a new session."""
        session_id = clock.now().strftime("%Y%m%d_%H%M%S")
        self.tracker = EnergyTracker(session_id)
        logger.info(f"Session reset — new session {session_id}")


# Singleton — imported by routes and orchestrator
digital_twin = DigitalTwinAgent()
