from __future__ import annotations
import asyncio
from collections import deque

from shared.classroom_state import classroom_state, CLASSROOM_ZONES
from shared.broadcaster import broadcast
from shared.logger import get_logger, log_decision
from shared.thresholds import DECISION_INTERVAL_SECONDS
from shared import clock

from agents.vision import vision_agent
from agents.light_sensor import light_sensor
from agents.voice import voice_agent
from agents.digital_twin import digital_twin
from agents.emergency import emergency_agent

from skills.decision_engine import run_decision_engine, calculate_energy_watts

logger = get_logger("OrchestratorAgent")

# Keep the last 50 decision records for the history endpoint
_history: deque = deque(maxlen=50)


class OrchestratorAgent:
    """
    Central brain of the Smart Classroom system.

    Every DECISION_INTERVAL_SECONDS seconds:
      1. Polls VisionAgent        → occupancy per zone
      2. Polls LightSensorAgent   → natural light per zone
      3. Polls VoiceAgent         → any pending manual override
      4. Runs the decision engine → optimal lighting state
      5. Applies state to DigitalTwinAgent
      6. Broadcasts full state to all browser clients via WebSocket
      7. Logs the decision

    Voice commands always have top priority and set the mode to MANUAL.
    Saying "auto mode" clears the override and returns to AI control.
    """

    def __init__(self):
        self._voice_override: dict | None = None   # Persists until cleared
        self._cycle_count = 0
        logger.info("OrchestratorAgent initialized")

    # ── Main decision cycle ───────────────────────────────────────────────────

    async def run_cycle(self) -> dict:
        """Run one full decision cycle. Returns the resulting lighting state."""
        self._cycle_count += 1

        # 1. Gather sensor data
        occupancy     = vision_agent.get_occupancy()
        natural_light = light_sensor.get_levels()
        voice_cmd     = voice_agent.consume()   # dict | {"__clear_override__": True} | None

        # Sync weather + scenario to classroom_state for WebSocket consumers
        classroom_state.weather  = natural_light.get("weather", "clear")
        classroom_state.scenario = occupancy.get("scenario", "full_class")

        # Strip metadata keys before passing to decision engine
        occ_zones   = {z: occupancy.get(z, 0)      for z in CLASSROOM_ZONES}
        light_zones = {z: natural_light.get(z, 0.0) for z in CLASSROOM_ZONES}

        # 2. Determine lighting state
        lighting_state, mode, voice_raw = self._decide(occ_zones, light_zones, voice_cmd)

        # 3. Apply to digital twin (updates classroom_state + logs to CSV)
        digital_twin.apply_state(lighting_state)

        # 4. Push people positions to digital twin for 3D rendering
        digital_twin.update_people_positions(vision_agent.get_people_positions())
        digital_twin.update_natural_light(light_zones)

        # 5. Build full state and broadcast
        full_state = digital_twin.get_full_state()
        await broadcast("STATE_UPDATE", full_state)

        # 6. Broadcast individual lighting decisions for UI notifications
        for zone, data in lighting_state.items():
            if isinstance(data, dict):
                await broadcast("LIGHTING_DECISION", {
                    "zone":         zone,
                    "state":        data.get("state"),
                    "reason":       data.get("reason"),
                    "energy_watts": classroom_state.total_watts,
                })

        # 7. Log the cycle
        log_decision(lighting_state, occ_zones, light_zones, voice_raw)
        self._record_history(lighting_state, occ_zones, light_zones, mode, voice_raw)

        if self._cycle_count % 10 == 1:   # Log summary every ~50 seconds
            logger.info(
                f"Cycle #{self._cycle_count} | {classroom_state.total_watts}W | "
                f"mode={mode} | people={occupancy.get('total', 0)} | "
                f"voice={voice_raw or 'none'}"
            )

        return lighting_state

    # ── Decision logic ────────────────────────────────────────────────────────

    def _decide(self, occ_zones: dict, light_zones: dict, voice_cmd) -> tuple:
        """
        Returns (lighting_state, mode, voice_raw_text).

        voice_cmd is the output of voice_agent.consume():
          - None                       → no command
          - {"__clear_override__": True} → "auto mode" → clear override
          - {zone: {state, reason}, ...} → lighting state dict (manual override)
        """
        voice_raw = None

        # Prioridad 0: emergencia declarada. Va por encima de la voz a
        # propósito — la voz manda sobre la comodidad, no sobre la
        # seguridad. Para recuperar el control hay que declarar
        # explícitamente que la emergencia terminó.
        if emergency_agent.active:
            classroom_state.mode = "EMERGENCY"
            return emergency_agent.get_lighting_state(occ_zones), "EMERGENCY", None

        # Fuera de emergencia el estado queda limpio para el navegador.
        classroom_state.emergency = None

        # Handle __clear_override__ signal
        if isinstance(voice_cmd, dict) and voice_cmd.get("__clear_override__"):
            self._voice_override = None
            classroom_state.mode = "AUTO"
            logger.info("Voice command: returned to AUTO mode")
            voice_cmd = None

        # New voice lighting command → store as persistent override
        elif isinstance(voice_cmd, dict) and voice_cmd:
            self._voice_override = voice_cmd
            classroom_state.mode = "MANUAL"
            # Extract human-readable text from the reason field
            sample = next(iter(voice_cmd.values()), {})
            voice_raw = sample.get("reason", "Voice command") if isinstance(sample, dict) else "Voice command"
            logger.info(f"Voice override applied: {voice_raw}")

        # Priority 1: Active voice override
        if self._voice_override is not None:
            return self._voice_override, "MANUAL", voice_raw

        # Priority 2–6: AI decision engine
        classroom_state.mode = "AUTO"
        lighting_state = run_decision_engine(occ_zones, light_zones)
        return lighting_state, "AUTO", None

    # ── History ───────────────────────────────────────────────────────────────

    def _record_history(self, lighting_state, occ, light, mode, voice_raw):
        _history.appendleft({
            "timestamp":     clock.now().isoformat(),
            "mode":          mode,
            "voice_command": voice_raw,
            "total_watts":   classroom_state.total_watts,
            "lighting": {
                zone: data.get("state") for zone, data in lighting_state.items()
                if isinstance(data, dict)
            },
            "reasons": {
                zone: data.get("reason") for zone, data in lighting_state.items()
                if isinstance(data, dict)
            },
            "occupancy":     occ,
            "natural_light": {z: round(v, 2) for z, v in light.items()},
        })

    def get_history(self) -> list:
        return list(_history)

    def get_status(self) -> dict:
        return {
            "cycle_count":  self._cycle_count,
            "mode":         classroom_state.mode,
            "total_watts":  classroom_state.total_watts,
            "has_override": self._voice_override is not None,
            "state":        classroom_state.to_dict(),
        }

    def clear_override(self):
        self._voice_override = None
        classroom_state.mode = "AUTO"


# Singleton
orchestrator = OrchestratorAgent()


# ── Background loop ───────────────────────────────────────────────────────────

async def start_decision_loop():
    """
    Starts the continuous decision loop.
    Called once from main.py on startup.
    """
    logger.info(f"Decision loop starting — interval: {DECISION_INTERVAL_SECONDS}s")
    while True:
        try:
            await orchestrator.run_cycle()
        except Exception as exc:
            logger.error(f"Error in decision cycle: {exc}", exc_info=True)
        await asyncio.sleep(DECISION_INTERVAL_SECONDS)
