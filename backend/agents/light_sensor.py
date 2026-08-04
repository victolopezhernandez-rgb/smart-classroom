from __future__ import annotations
from datetime import datetime

from shared.logger import get_logger
from skills.natural_light_simulation import calculate_light_levels, WEATHER_MULTIPLIERS

logger = get_logger("LightSensorAgent")

VALID_WEATHER = list(WEATHER_MULTIPLIERS.keys())


class LightSensorAgent:
    """
    Simulates lux sensors measuring natural light per classroom zone.

    Zone proximity to windows (left wall, x=0):
      Zone A (front-left):  HIGH  — direct exposure
      Zone C (back-left):   MED   — one window
      Zone B (front-right): LOW   — reflected light only
      Zone D (back-right):  VERY LOW — farthest from windows
    """

    def __init__(self):
        self.weather = "clear"
        self.simulated_time: float | None = 10.0   # Default: 10 AM so weather effects are always visible
        logger.info("LightSensorAgent started")

    # ── Public interface ──────────────────────────────────────────────────────

    def set_weather(self, weather: str):
        if weather not in VALID_WEATHER:
            raise ValueError(f"Unknown weather '{weather}'. Valid: {VALID_WEATHER}")
        self.weather = weather
        logger.info(f"Weather → {weather}")

    def set_simulated_time(self, hour: float | None):
        """
        Override the real clock for demos.
        hour: 0.0–23.99  (e.g., 10.5 = 10:30 AM)
        Pass None to use the real current time.
        """
        self.simulated_time = hour
        label = f"{hour:.1f}h" if hour is not None else "real time"
        logger.info(f"Simulated time → {label}")

    def get_levels(self) -> dict:
        """
        Returns natural light level (0.0–1.0) for each zone.
        Called by OrchestratorAgent every cycle.
        """
        hour = self._current_hour()
        levels = calculate_light_levels(hour, self.weather)
        levels["timestamp"] = datetime.now().isoformat()
        levels["weather"] = self.weather
        levels["hour"] = round(hour, 2)
        return levels

    # ── Private ───────────────────────────────────────────────────────────────

    def _current_hour(self) -> float:
        if self.simulated_time is not None:
            return self.simulated_time
        now = datetime.now()
        return now.hour + now.minute / 60.0


# Singleton
light_sensor = LightSensorAgent()
