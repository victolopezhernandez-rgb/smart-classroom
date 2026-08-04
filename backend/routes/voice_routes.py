from fastapi import APIRouter
from pydantic import BaseModel

from agents.voice import voice_agent
from shared.broadcaster import broadcast

router = APIRouter(prefix="/api/voice", tags=["voice"])


class VoiceCommandRequest(BaseModel):
    command: str


@router.post("/command")
async def receive_command(body: VoiceCommandRequest):
    """
    Receives a raw speech transcript from the browser.
    Parses it, stores it for the OrchestratorAgent, and broadcasts it via WebSocket.
    """
    parsed = voice_agent.receive(body.command)

    # Broadcast immediately so the UI can show what was heard
    await broadcast("VOICE_RECEIVED", {
        "raw":    body.command,
        "parsed": parsed,
    })

    return {
        "received": body.command,
        "parsed":   parsed,
        "status":   "queued" if parsed.get("action") else "ignored",
    }


@router.get("/latest")
def get_latest():
    """
    Reads and clears the pending voice command.
    Called by OrchestratorAgent each decision cycle.
    """
    lighting_state = voice_agent.consume()
    return {"command": lighting_state}


@router.get("/pending")
def get_pending():
    """Returns the pending parsed command without consuming it (for debugging)."""
    return {"pending": voice_agent.peek()}


@router.get("/history")
def get_history():
    """Returns the last 20 voice commands received (most recent first)."""
    return {"history": voice_agent.get_history()}


@router.post("/clear")
def clear_command():
    """Manually clear any pending voice command."""
    voice_agent.clear()
    return {"message": "Voice command queue cleared"}
