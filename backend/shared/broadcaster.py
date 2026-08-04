from __future__ import annotations
import json
from fastapi import WebSocket

_clients: list[WebSocket] = []


def register(websocket: WebSocket):
    _clients.append(websocket)


def unregister(websocket: WebSocket):
    if websocket in _clients:
        _clients.remove(websocket)


async def broadcast(message_type: str, payload: dict):
    if not _clients:
        return

    message = json.dumps({"type": message_type, "payload": payload})

    dead_clients = []
    for client in _clients:
        try:
            await client.send_text(message)
        except Exception:
            dead_clients.append(client)

    for client in dead_clients:
        unregister(client)
