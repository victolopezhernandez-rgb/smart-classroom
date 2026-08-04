# SHARED SKILL: WebSocket Broadcast

## What This Skill Does

Handles real-time communication between the Python backend and the React frontend. Every time the OrchestratorAgent makes a decision, the result is broadcast instantly to all open browser tabs via WebSocket — so the 3D model updates without the user needing to refresh.

## Why WebSocket and not REST?

REST (regular HTTP requests) requires the frontend to repeatedly ask "what's new?" every few seconds (called polling). WebSocket is a persistent connection where the server can push updates to the browser the instant they happen. This makes the 3D visualization respond in real time, which is much more impressive for the STEAM fair.

## Full Implementation

```python
# backend/shared/broadcaster.py

import asyncio
import json
from fastapi import WebSocket

# In-memory list of all connected browser tabs
_clients: list[WebSocket] = []

def register(websocket: WebSocket):
    """Call when a browser connects."""
    _clients.append(websocket)

def unregister(websocket: WebSocket):
    """Call when a browser disconnects."""
    if websocket in _clients:
        _clients.remove(websocket)

async def broadcast(message_type: str, payload: dict):
    """
    Sends a message to ALL connected browser clients.
    
    Args:
        message_type: A string tag like "STATE_UPDATE" or "LIGHTING_DECISION"
        payload:      The data to send (will be JSON-serialized)
    
    Message format sent to browser:
        {"type": "STATE_UPDATE", "payload": {...}}
    """
    if not _clients:
        return   # No one connected, skip

    message = json.dumps({"type": message_type, "payload": payload})
    
    dead_clients = []
    for client in _clients:
        try:
            await client.send_text(message)
        except Exception:
            dead_clients.append(client)
    
    # Clean up disconnected clients
    for client in dead_clients:
        unregister(client)
```

## WebSocket Endpoint (add to main.py)

```python
# backend/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from shared.broadcaster import register, unregister, broadcast

app = FastAPI(title="Smart Classroom API")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    register(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        unregister(websocket)
```

## Message Types Reference

All messages follow the format: `{"type": "...", "payload": {...}}`

| type | When sent | Payload content |
|---|---|---|
| `STATE_UPDATE` | Every 5 seconds | Full classroom state (zones, watts, people) |
| `LIGHTING_DECISION` | After each decision cycle | Zone, new state, reason |
| `VOICE_RECEIVED` | When voice command arrives | Raw text + parsed command |
| `ALERT` | When consumption > 280W | Warning message |

## Frontend Hook (React)

```javascript
// frontend/src/hooks/useClassroomWebSocket.js

import { useEffect, useState, useRef } from "react";

export function useClassroomWebSocket(url = "ws://localhost:8000/ws") {
  const [state, setState]           = useState(null);
  const [lastDecision, setDecision] = useState(null);
  const [connected, setConnected]   = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setConnected(true);
      console.log("🔌 Connected to classroom backend");
    };

    ws.onclose = () => {
      setConnected(false);
      console.log("🔌 Disconnected — retrying in 3 seconds...");
      setTimeout(() => {
        wsRef.current = new WebSocket(url);
      }, 3000);
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "STATE_UPDATE")      setState(msg.payload);
      if (msg.type === "LIGHTING_DECISION") setDecision(msg.payload);
    };

    // Keepalive ping every 25 seconds
    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send("ping");
    }, 25000);

    wsRef.current = ws;

    return () => {
      clearInterval(ping);
      ws.close();
    };
  }, [url]);

  return { state, lastDecision, connected };
}
```

## Usage in App.jsx

```jsx
// frontend/src/App.jsx

import { useClassroomWebSocket } from "./hooks/useClassroomWebSocket";
import { Classroom3D } from "./components/Classroom3D";
import { EnergyDashboard } from "./components/EnergyDashboard";

export default function App() {
  const { state, lastDecision, connected } = useClassroomWebSocket();

  return (
    <div>
      <header>
        <h1>🏫 Smart Classroom AI</h1>
        <span>{connected ? "🟢 Connected" : "🔴 Connecting..."}</span>
      </header>
      <Classroom3D classroomState={state} />
      <EnergyDashboard currentState={state} lastDecision={lastDecision} />
    </div>
  );
}
```

## Step-by-Step Build Instructions for Claude Code

1. **Create** `backend/shared/broadcaster.py` with the code above
2. **Add** the `/ws` WebSocket route to `backend/main.py`
3. **Import** `broadcast` in `backend/agents/orchestrator.py`
4. **Call** `await broadcast("STATE_UPDATE", classroom_state.to_dict())` at the end of each decision cycle
5. **Create** `frontend/src/hooks/useClassroomWebSocket.js`
6. **Use** the hook in `frontend/src/App.jsx`
7. **Test**: open the browser console, you should see "Connected to classroom backend" and state updates every 5 seconds
