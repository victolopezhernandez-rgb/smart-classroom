# TwinLight — Claude Code Project

## Project Overview

This is a multi-agent AI system that optimizes electricity consumption in a classroom by intelligently controlling lights. It uses a **digital twin** (a 3D virtual replica of a real classroom) to measure and compare energy usage before and after implementing the AI system.

Built for a STEAM school fair. Everything is simulated — no physical hardware needed
(the browser webcam is an optional extra, see below).

> **This file was the original build plan, and it has been brought up to date with
> what actually got built.** For the running state of the project — what each file
> does today, known traps, and how it is published — read **[PROYECTO.md](PROYECTO.md)**,
> which is the authoritative document.

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────┐
│                  Web Browser (React)                 │
│         3D Classroom View + Dashboard UI            │
└────────────────────┬────────────────────────────────┘
                     │ HTTP / WebSocket
┌────────────────────▼────────────────────────────────┐
│              OrchestratorAgent (FastAPI)             │
│         Central brain — coordinates all agents      │
└──┬──────────┬──────────┬──────────┬─────────┬───────┘
   │          │          │          │         │
   ▼          ▼          ▼          ▼         ▼
VisionAgent  LightSensor VoiceAgent DigitalTwin Emergency
(people &    Agent       (voice     Agent       Agent
 location)   (sunlight)  commands)  (3D model + (evacuation
                                     energy)     lighting)
```

## The 6 Agents

| Agent | Code | Responsibility |
|---|---|---|
| OrchestratorAgent | `backend/agents/orchestrator.py` | Receives data from all agents, makes final lighting decisions |
| VisionAgent | `backend/agents/vision.py` | Counts people and their zone — simulated, or from the real webcam |
| LightSensorAgent | `backend/agents/light_sensor.py` | Natural light per zone, by time of day and weather |
| VoiceAgent | `backend/agents/voice.py` | Processes voice commands from the user |
| DigitalTwinAgent | `backend/agents/digital_twin.py` | Maintains the classroom model, tracks energy data |
| EmergencyAgent | `backend/agents/emergency.py` | Turns a disaster alert into evacuation lighting |

The EmergencyAgent came after the original plan. It **outranks everything,
including voice**: voice overrides comfort, not safety.

Priority inside `orchestrator._decide()`:

```
EMERGENCY  ▸  VOICE  ▸  RULE ENGINE
```

## Tech Stack

- **Backend:** Python 3.11 + FastAPI + WebSockets
- **Frontend:** React + Three.js loaded from `backend/static/vendor/`, compiled in
  the browser by Babel. **No build step, no npm, works offline.** Energy charts are
  hand-rolled `div` bars, not a charting library.
- **AI Logic:** Rule-based decisions (no external AI API required). The optional
  webcam uses BlazeFace, running entirely in the browser.
- **Communication:** REST API + WebSocket for real-time updates
- **Data:** JSON files for state, CSV for energy logs

> ⚠️ **The interface lives in `backend/static/index.html`.** The `frontend/`
> folder is the React+Vite version from the first commit and is **no longer used** —
> it is frozen and misleading. Same for `run.sh`, which starts that dead frontend.

## Project Structure

```
smart-classroom/
├── CLAUDE.md                          ← You are here
├── agents/
│   ├── orchestrator/
│   │   ├── AGENT.md                   ← Orchestrator instructions
│   │   └── skills/
│   │       ├── SKILL_decision_engine.md
│   │       └── SKILL_agent_communication.md
│   ├── vision/
│   │   ├── AGENT.md
│   │   └── skills/
│   │       ├── SKILL_people_detection.md
│   │       └── SKILL_zone_mapping.md
│   ├── light_sensor/
│   │   ├── AGENT.md
│   │   └── skills/
│   │       ├── SKILL_natural_light_simulation.md
│   │       └── SKILL_light_threshold.md
│   ├── voice/
│   │   ├── AGENT.md
│   │   └── skills/
│   │       ├── SKILL_speech_recognition.md
│   │       └── SKILL_command_parser.md
│   └── digital_twin/
│       ├── AGENT.md
│       └── skills/
│           ├── SKILL_3d_model.md
│           ├── SKILL_energy_tracking.md
│           └── SKILL_report_generator.md
├── shared_skills/
│   ├── SKILL_logging.md
│   ├── SKILL_websocket_broadcast.md
│   └── SKILL_classroom_state.md
├── backend/                           ← EVERYTHING THAT RUNS
│   ├── main.py                        FastAPI: routes, WebSocket, serves /app and /vendor
│   ├── agents/                        the 6 agents
│   ├── skills/                        pure logic, stateless
│   ├── routes/                        the REST API, one file per agent
│   ├── shared/                        state, thresholds, logging, broadcaster, clock
│   ├── static/                        ← THE REAL INTERFACE
│   │   ├── landing.html               entry page
│   │   ├── index.html                 3D digital twin + dashboard
│   │   └── vendor/                    React, Three.js, Babel, BlazeFace (offline)
│   └── data/energy_logs.csv           measurements (regenerated on every run)
├── frontend/                          ⚠️ dead React+Vite app from commit 1 — DO NOT USE
├── deploy/                            generated by scripts/build-deploy.sh; gitignored
├── .github/workflows/deploy.yml       publishes to GitHub Pages on every push to main
└── data/
    ├── classroom_config.json          ← Room layout, zones, light positions
    └── energy_logs.csv                ← Before/after energy measurements
```

## Running It

```bash
cd backend && python3 -m uvicorn main:app --reload --port 8000
```

Then open **http://localhost:8000/app/**. Do **not** use `run.sh` — it starts the
dead `frontend/` on port 5173.

> The commands that originally generated this project from the AGENT.md files are
> kept in [PROYECTO.md](PROYECTO.md). The system is already built; those `AGENT.md`
> and `SKILL_*.md` files are now documentation of how it was specified, not a to-do
> list. **Editing them does not change the running code** — the code is in `backend/`.

## Classroom Configuration

The classroom is divided into **4 lighting zones**:

```
┌─────────────────────────────────┐
│  Zone A (Front-Left)  │  Zone B (Front-Right)  │
│  2 light fixtures     │  2 light fixtures      │
├───────────────────────┼────────────────────────┤
│  Zone C (Back-Left)   │  Zone D (Back-Right)   │
│  2 light fixtures     │  2 light fixtures      │
└─────────────────────────────────┘
         [Windows on left wall]
         [Door at back-right]
         [Whiteboard at front]
```

Each fixture = 40W fluorescent bulb. Full classroom ON = 320W.

## Energy Measurement Goal

The system compares two scenarios:
- **Baseline:** All 8 lights ON for 8 hours = 2.56 kWh/day
- **AI-optimized:** Lights adjusted by occupancy + natural light = target 40-60% savings

## Key Rules the AI Follows

1. If 0 people in classroom → all lights OFF
2. If natural light > 75% in a zone → lights OFF in that zone (40–75% → DIM)
3. If people only in zones A+B → only zones A+B lights ON
4. Voice command overrides AI decisions — **but an emergency overrides voice**
5. Log every decision with timestamp and reason

## Conventions to Respect

- **Never call `datetime.now()`.** The classroom is in Colombia and the server runs
  in UTC; anything that depends on "what time is it in the room" must go through
  `backend/shared/clock.py`. Getting this wrong makes the simulated sun set five
  hours early and the AI turn every light on.
- **Never edit `deploy/`.** It is generated. The originals live in `backend/static/`.
- **Never edit `frontend/`.** It is dead code.
- Comments in the codebase are written in Spanish, explaining *why* rather than
  *what*. Match that when adding code.
