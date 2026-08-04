from fastapi import APIRouter
from pydantic import BaseModel

from agents.orchestrator import orchestrator

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


@router.get("/status")
def get_status():
    """Current lighting state, mode, cycle count, and total watts."""
    return orchestrator.get_status()


@router.post("/cycle")
async def trigger_cycle():
    """Manually trigger one decision cycle (useful for testing)."""
    lighting_state = await orchestrator.run_cycle()
    return {
        "message":       "Cycle executed",
        "lighting_state": lighting_state,
    }


@router.get("/history")
def get_history(limit: int = 20):
    """Last N decision records (most recent first) with reasons and energy data."""
    history = orchestrator.get_history()
    return {
        "count":   len(history),
        "history": history[:limit],
    }


class ModeRequest(BaseModel):
    mode: str  # "AUTO" or "MANUAL"


@router.post("/mode")
def set_mode(body: ModeRequest):
    """
    Switch between AUTO (AI) and MANUAL mode.
    Switching to AUTO clears any active voice override.
    """
    if body.mode not in ("AUTO", "MANUAL"):
        return {"error": "mode must be 'AUTO' or 'MANUAL'"}
    if body.mode == "AUTO":
        orchestrator.clear_override()
    return {"mode": body.mode, "message": f"Switched to {body.mode} mode"}


@router.post("/clear-override")
def clear_override():
    """Clear any active voice override and return to AI mode."""
    orchestrator.clear_override()
    return {"message": "Override cleared, AI mode active"}
