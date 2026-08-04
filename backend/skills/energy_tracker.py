from __future__ import annotations
import csv
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Literal

from shared.thresholds import BASELINE_WATTS

LOG_FILE = "data/energy_logs.csv"


@dataclass
class EnergyReading:
    timestamp: str
    watts: float
    zone_states: dict
    mode: Literal["BASELINE", "AI"]
    session_id: str


class EnergyTracker:
    """
    Records energy consumption readings every 5 seconds.
    Compares AI-controlled consumption vs baseline (all lights on).
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.readings: list[EnergyReading] = []
        self._init_csv()

    def log_reading(self, lighting_state: dict, mode: str = "AI") -> EnergyReading:
        watts = self._calculate_watts(lighting_state)
        zone_states = {
            zone: data.get("state", "OFF")
            for zone, data in lighting_state.items()
            if isinstance(data, dict)
        }

        reading = EnergyReading(
            timestamp=datetime.now().isoformat(),
            watts=watts,
            zone_states=zone_states,
            mode=mode,
            session_id=self.session_id,
        )
        self.readings.append(reading)
        self._write_to_csv(reading)
        return reading

    def get_session_stats(self) -> dict:
        if not self.readings:
            return {
                "session_id": self.session_id,
                "total_readings": 0,
                "avg_ai_watts": 0,
                "avg_baseline_watts": BASELINE_WATTS,
                "savings_watts": BASELINE_WATTS,
                "savings_percent": 100.0,
                "projected_ai_kwh_per_day": 0,
                "projected_baseline_kwh_per_day": round(BASELINE_WATTS / 1000 * 8, 3),
                "projected_savings_kwh_per_day": round(BASELINE_WATTS / 1000 * 8, 3),
                "projected_savings_per_month_kwh": round(BASELINE_WATTS / 1000 * 8 * 22, 2),
            }

        ai_readings   = [r for r in self.readings if r.mode == "AI"]
        base_readings = [r for r in self.readings if r.mode == "BASELINE"]

        avg_ai_watts   = sum(r.watts for r in ai_readings)   / len(ai_readings)   if ai_readings   else 0
        avg_base_watts = sum(r.watts for r in base_readings) / len(base_readings) if base_readings else BASELINE_WATTS

        savings_watts   = avg_base_watts - avg_ai_watts
        savings_percent = (savings_watts / avg_base_watts * 100) if avg_base_watts > 0 else 0

        ai_kwh_day   = avg_ai_watts   / 1000 * 8
        base_kwh_day = avg_base_watts / 1000 * 8

        return {
            "session_id":                        self.session_id,
            "total_readings":                    len(self.readings),
            "avg_ai_watts":                      round(avg_ai_watts, 1),
            "avg_baseline_watts":                round(avg_base_watts, 1),
            "savings_watts":                     round(savings_watts, 1),
            "savings_percent":                   round(savings_percent, 1),
            "projected_ai_kwh_per_day":          round(ai_kwh_day, 3),
            "projected_baseline_kwh_per_day":    round(base_kwh_day, 3),
            "projected_savings_kwh_per_day":     round(base_kwh_day - ai_kwh_day, 3),
            "projected_savings_per_month_kwh":   round((base_kwh_day - ai_kwh_day) * 22, 2),
        }

    def get_history_for_chart(self, last_n: int = 60) -> list[dict]:
        recent = self.readings[-last_n:]
        return [
            {
                "time": r.timestamp[11:19],
                "watts": r.watts,
                "baseline": BASELINE_WATTS,
            }
            for r in recent
        ]

    def _calculate_watts(self, lighting_state: dict) -> float:
        watts_map = {"ON": 80.0, "DIM": 40.0, "OFF": 0.0}
        return sum(
            watts_map.get(data.get("state", "OFF"), 0)
            for data in lighting_state.values()
            if isinstance(data, dict)
        )

    def _init_csv(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", newline="") as f:
                csv.writer(f).writerow([
                    "timestamp", "session_id", "mode",
                    "watts", "zone_A", "zone_B", "zone_C", "zone_D",
                ])

    def _write_to_csv(self, reading: EnergyReading):
        with open(LOG_FILE, "a", newline="") as f:
            csv.writer(f).writerow([
                reading.timestamp,
                reading.session_id,
                reading.mode,
                reading.watts,
                reading.zone_states.get("zone_A", "?"),
                reading.zone_states.get("zone_B", "?"),
                reading.zone_states.get("zone_C", "?"),
                reading.zone_states.get("zone_D", "?"),
            ])
