from fastapi import APIRouter
from pydantic import BaseModel

from agents.voice import voice_agent
from agents.emergency import emergency_agent
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

    # Si lo que se oyó fue una emergencia, el que manda es el EmergencyAgent y
    # no la cola de voz. Se despacha aquí mismo, sin esperar al siguiente ciclo
    # del Orchestrator: entre gritar "¡fuego!" y ver la ruta iluminada no puede
    # haber cinco segundos de nada.
    #
    # Apagarla también exige decirlo explícitamente ("ya pasó", "falsa alarma").
    # Ninguna orden de luces la cancela, por diseño: la voz manda sobre la
    # comodidad, no sobre la seguridad.
    kind = parsed.get("emergency")
    if kind == "clear":
        emergency_agent.clear()
    elif kind:
        emergency_agent.trigger(kind)

    # Broadcast immediately so the UI can show what was heard
    await broadcast("VOICE_RECEIVED", {
        "raw":    body.command,
        "parsed": parsed,
    })

    return {
        "received": body.command,
        "parsed":   parsed,
        "status":   "queued" if (parsed.get("action") or kind) else "ignored",
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
