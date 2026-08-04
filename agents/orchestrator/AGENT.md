# OrchestratorAgent — AGENT.md

## Who Am I?

I am the **central brain** of the Smart Classroom Lighting System. I receive information from all other agents and make the final decision about which lights to turn on or off. Think of me as the manager of a team: I don't do the sensing or the visualization myself — I listen to my team and make the call.

## My Responsibilities

1. Receive occupancy data from VisionAgent (how many people, where they are)
2. Receive natural light data from LightSensorAgent (how bright each zone is)
3. Receive voice commands from VoiceAgent (manual overrides)
4. Apply the **decision engine** to determine the optimal lighting state
5. Send lighting commands to DigitalTwinAgent (to update the 3D model)
6. Log every decision with a reason (for the energy report)

## My Skills

- [`SKILL_decision_engine.md`](skills/SKILL_decision_engine.md) — The core AI logic that decides which lights to turn on/off
- [`SKILL_agent_communication.md`](skills/SKILL_agent_communication.md) — How I send and receive messages from other agents

## Files I Need to Create

### `backend/agents/orchestrator.py`

```python
# OrchestratorAgent — Main orchestration logic
# This file runs as a FastAPI route handler and coordinates all agents

from fastapi import APIRouter
from shared.classroom_state import ClassroomState
from shared.logger import log_decision
from agents.vision import VisionAgent
from agents.light_sensor import LightSensorAgent
from agents.voice import VoiceAgent
from agents.digital_twin import DigitalTwinAgent

router = APIRouter()

class OrchestratorAgent:
    """
    Central coordinator. Runs a decision cycle every 5 seconds.
    Each cycle:
    1. Gathers data from all sensor agents
    2. Applies decision rules
    3. Updates the digital twin
    4. Broadcasts new state to the frontend via WebSocket
    """

    def __init__(self):
        self.state = ClassroomState()
        self.voice_override = None  # Stores any active voice command

    async def run_cycle(self):
        # Step 1: Gather data
        occupancy = VisionAgent.get_occupancy()       # {zone: count}
        natural_light = LightSensorAgent.get_levels() # {zone: 0.0-1.0}
        voice_cmd = VoiceAgent.get_latest_command()   # "lights on zone A" or None

        # Step 2: Apply decision engine
        new_state = self.decide(occupancy, natural_light, voice_cmd)

        # Step 3: Update digital twin
        DigitalTwinAgent.apply_state(new_state)

        # Step 4: Log the decision
        log_decision(new_state, occupancy, natural_light, voice_cmd)

        return new_state

    def decide(self, occupancy, natural_light, voice_cmd):
        # See SKILL_decision_engine.md for full logic
        pass
```

### `backend/routes/orchestrator_routes.py`

```python
# REST endpoints for the orchestrator
# GET  /api/orchestrator/status  → current lighting state
# POST /api/orchestrator/cycle   → manually trigger a decision cycle
# GET  /api/orchestrator/history → last 50 decisions with reasons
```

## Decision Cycle (every 5 seconds)

```
Every 5 seconds:
│
├── Ask VisionAgent:      "How many people in each zone?"
├── Ask LightSensorAgent: "How bright is natural light in each zone?"
├── Ask VoiceAgent:       "Any new voice commands?"
│
├── Run Decision Engine ──► Lighting state for each zone (ON/OFF/DIM)
│
├── Send to DigitalTwinAgent: "Apply this lighting state"
└── Broadcast to Frontend via WebSocket: "Update the 3D view"
```

## API Endpoints I Expose

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/orchestrator/status` | Current lighting state of all zones |
| POST | `/api/orchestrator/cycle` | Trigger one decision cycle manually |
| GET | `/api/orchestrator/history` | List of last decisions with reasons |
| POST | `/api/orchestrator/mode` | Switch between AUTO (AI) and MANUAL mode |

## Data Format I Work With

### Input from VisionAgent
```json
{
  "zone_A": 5,
  "zone_B": 0,
  "zone_C": 12,
  "zone_D": 3,
  "total": 20,
  "timestamp": "2024-03-15T10:30:00"
}
```

### Input from LightSensorAgent
```json
{
  "zone_A": 0.85,
  "zone_B": 0.60,
  "zone_C": 0.20,
  "zone_D": 0.15,
  "timestamp": "2024-03-15T10:30:00"
}
```

### Output to DigitalTwinAgent
```json
{
  "zone_A": "OFF",
  "zone_B": "DIM",
  "zone_C": "ON",
  "zone_D": "ON",
  "mode": "AUTO",
  "reason": "Zone A: high natural light. Zone C+D: occupied, low natural light.",
  "energy_watts": 120,
  "timestamp": "2024-03-15T10:30:00"
}
```

## Step-by-Step Build Instructions for Claude Code

> Claude Code: When you read this file, follow these steps in order.

1. **Read** `SKILL_decision_engine.md` first — the decision logic goes inside the `decide()` method
2. **Read** `SKILL_agent_communication.md` — this tells you how to connect to the other agents
3. **Read** `../../shared_skills/SKILL_classroom_state.md` — you need the ClassroomState class
4. **Create** `backend/agents/orchestrator.py` with the full OrchestratorAgent class
5. **Create** `backend/routes/orchestrator_routes.py` with the REST endpoints
6. **Add** a background task in `backend/main.py` that calls `run_cycle()` every 5 seconds
7. **Test** by running `curl http://localhost:8000/api/orchestrator/status` — should return current state

## Common Mistakes to Avoid

- Do NOT make lighting decisions inside VisionAgent or LightSensorAgent — only I decide
- Do NOT skip logging — the energy report depends on every decision being recorded
- Voice commands must always override AI decisions (voice_cmd takes priority)
- If an agent is unavailable, use the last known value, not zero
