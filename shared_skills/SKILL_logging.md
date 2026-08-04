# SHARED SKILL: Logging

## What This Skill Does

Provides a unified logging system used by all agents. Every important event — a lighting decision, a voice command, a sensor reading, an energy spike — gets recorded in a structured log so you can trace exactly what happened and when.

## Implementation

```python
# backend/shared/logger.py

import logging
import json
from datetime import datetime
from pathlib import Path

# Create logs directory
Path("logs").mkdir(exist_ok=True)

# Configure the main logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/system.log"),
        logging.StreamHandler()   # Also print to terminal
    ]
)

def get_logger(agent_name: str) -> logging.Logger:
    """
    Returns a logger for the given agent.
    
    Usage in any agent:
        from shared.logger import get_logger
        logger = get_logger("OrchestratorAgent")
        logger.info("Decision made: Zone A OFF")
    """
    return logging.getLogger(agent_name)


def log_decision(lighting_state: dict, occupancy: dict, natural_light: dict, voice_cmd: str | None):
    """
    Logs a complete decision cycle in a structured JSON format.
    Saved to logs/decisions.jsonl (one JSON object per line).
    """
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
```

## Step-by-Step Build Instructions for Claude Code

1. **Create** `backend/shared/logger.py` with the code above
2. **Import** `get_logger` in every agent file:
   - `from shared.logger import get_logger`
   - `logger = get_logger("AgentName")`
3. **Import** `log_decision` in `backend/agents/orchestrator.py`
4. **Call** `log_decision(...)` at the end of every decision cycle
5. **Verify** by running the system and checking `logs/system.log` — you should see one line per cycle
