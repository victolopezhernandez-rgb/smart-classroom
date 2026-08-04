from __future__ import annotations
import logging
import json
from datetime import datetime
from pathlib import Path

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/system.log"),
        logging.StreamHandler()
    ]
)


def get_logger(agent_name: str) -> logging.Logger:
    return logging.getLogger(agent_name)


def log_decision(lighting_state: dict, occupancy: dict, natural_light: dict, voice_cmd: str | None):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "lighting_state": {
            zone: data.get("state") for zone, data in lighting_state.items()
            if isinstance(data, dict)
        },
        "reasons": {
            zone: data.get("reason") for zone, data in lighting_state.items()
            if isinstance(data, dict)
        },
        "occupancy": occupancy,
        "natural_light": natural_light,
        "voice_command": voice_cmd,
        "total_watts": sum(
            {"ON": 80, "DIM": 40, "OFF": 0}.get(data.get("state", "OFF"), 0)
            for data in lighting_state.values() if isinstance(data, dict)
        )
    }

    with open("logs/decisions.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")

    logger = get_logger("OrchestratorAgent")
    logger.info(
        f"Decision | Watts: {entry['total_watts']}W | "
        f"Voice: {voice_cmd or 'none'} | "
        f"States: {entry['lighting_state']}"
    )
