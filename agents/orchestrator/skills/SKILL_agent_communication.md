# SKILL: Agent Communication

## What This Skill Does

Defines how the OrchestratorAgent sends and receives messages from the other four agents. All communication happens through internal Python function calls (since all agents run in the same FastAPI process) and WebSockets (to push updates to the browser frontend).

## Communication Architecture

```
Frontend (React)
     ▲  │
     │  │ WebSocket (ws://localhost:8000/ws)
     │  ▼
OrchestratorAgent
     │
     ├──► VisionAgent.get_occupancy()       → dict
     ├──► LightSensorAgent.get_levels()     → dict
     ├──► VoiceAgent.get_latest_command()   → str | None
     └──► DigitalTwinAgent.apply_state()    → None
```

## Implementation

```python
# backend/shared/agent_bus.py
# This module handles all inter-agent communication

import asyncio
import json
from fastapi import WebSocket
from typing import Optional

# Global registry of connected WebSocket clients (browser tabs)
connected_clients: list[WebSocket] = []

class AgentBus:
    """
    Simple message bus that allows agents to communicate.
    Since all agents are in the same process, this is just
    a collection of function calls + WebSocket broadcasting.
    """

    @staticmethod
    async def broadcast_state(state: dict):
        """
        Sends the current classroom state to ALL connected browser clients.
        Called by OrchestratorAgent after every decision cycle.
        
        Args:
            state: The full classroom state including lighting, energy, people
        """
        message = json.dumps({
            "type": "STATE_UPDATE",
            "payload": state
        })
        
        # Send to all connected browser tabs
        disconnected = []
        for client in connected_clients:
            try:
                await client.send_text(message)
            except Exception:
                disconnected.append(client)
        
        # Clean up disconnected clients
        for client in disconnected:
            connected_clients.remove(client)

    @staticmethod
    async def broadcast_decision(zone: str, state: str, reason: str, watts: float):
        """
        Sends a lighting decision event to the frontend.
        The frontend uses this to show real-time notifications.
        
        Example payload:
        {
            "type": "LIGHTING_DECISION",
            "zone": "zone_A",
            "state": "OFF",
            "reason": "Natural light at 85% — sufficient",
            "energy_watts": 240
        }
        """
        message = json.dumps({
            "type": "LIGHTING_DECISION",
            "zone": zone,
            "state": state,
            "reason": reason,
            "energy_watts": watts
        })
        for client in connected_clients:
            try:
                await client.send_text(message)
            except Exception:
                pass

    @staticmethod
    def register_client(websocket: WebSocket):
        connected_clients.append(websocket)

    @staticmethod
    def unregister_client(websocket: WebSocket):
        if websocket in connected_clients:
            connected_clients.remove(websocket)
```

## WebSocket Route (in main.py)

```python
# backend/main.py — add this WebSocket endpoint

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from shared.agent_bus import AgentBus

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    AgentBus.register_client(websocket)
    try:
        while True:
            # Keep connection alive, listen for ping messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        AgentBus.unregister_client(websocket)
```

## Frontend WebSocket Connection (React)

```javascript
// frontend/src/hooks/useClassroomWebSocket.js

import { useEffect, useState } from "react";

export function useClassroomWebSocket() {
  const [classroomState, setClassroomState] = useState(null);
  const [lastDecision, setLastDecision] = useState(null);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === "STATE_UPDATE") {
        setClassroomState(message.payload);
      }

      if (message.type === "LIGHTING_DECISION") {
        setLastDecision(message);
      }
    };

    // Keep connection alive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send("ping");
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, []);

  return { classroomState, lastDecision };
}
```

## Message Types Reference

| Type | Direction | Description |
|---|---|---|
| `STATE_UPDATE` | Backend → Frontend | Full classroom state every 5 seconds |
| `LIGHTING_DECISION` | Backend → Frontend | Individual zone decision with reason |
| `VOICE_COMMAND` | Frontend → Backend | Voice command from user's microphone |
| `MANUAL_OVERRIDE` | Frontend → Backend | User clicks a light in the 3D view |

## Step-by-Step Build Instructions for Claude Code

1. **Create** `backend/shared/agent_bus.py` with the AgentBus class
2. **Add** the WebSocket endpoint to `backend/main.py`
3. **Add** `AgentBus.broadcast_state()` call at the end of `OrchestratorAgent.run_cycle()`
4. **Create** `frontend/src/hooks/useClassroomWebSocket.js`
5. **Test** by opening the browser console — you should see state updates every 5 seconds
