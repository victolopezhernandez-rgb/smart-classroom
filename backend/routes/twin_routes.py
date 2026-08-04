from fastapi import APIRouter
from pydantic import BaseModel

from agents.digital_twin import digital_twin
from shared.thresholds import BASELINE_WATTS

router = APIRouter(prefix="/api/twin", tags=["digital-twin"])


@router.get("/state")
def get_state():
    """Full classroom state: lighting, people, natural light, energy."""
    return digital_twin.get_full_state()


@router.get("/energy/history")
def get_energy_history(last_n: int = 60):
    """Last N energy readings formatted for Recharts."""
    return digital_twin.tracker.get_history_for_chart(last_n)


@router.get("/energy/stats")
def get_energy_stats():
    """Session statistics: savings, projected kWh, COP savings."""
    return digital_twin.tracker.get_session_stats()


@router.get("/report")
def get_report():
    """Full before/after comparison report."""
    stats = digital_twin.tracker.get_session_stats()

    if stats["savings_percent"] >= 40:
        verdict = "Target achieved! AI saved over 40% energy."
    elif stats["savings_percent"] >= 20:
        verdict = "Partial savings achieved. Optimize scenarios for better results."
    else:
        verdict = "Low savings. Check decision thresholds or scenario settings."

    return {
        **stats,
        "verdict": verdict,
        "methodology": "Comparison of simulated AI-controlled lighting vs baseline (all lights on) during the same session.",
        "baseline_description": f"Baseline: all 8 fixtures at 40W = {BASELINE_WATTS}W total, 8h/day = {BASELINE_WATTS/1000*8} kWh/day",
    }


class ModeRequest(BaseModel):
    mode: str  # "AI" or "BASELINE"


@router.post("/mode")
def set_mode(body: ModeRequest):
    """Switch between AI and BASELINE modes."""
    if body.mode not in ("AI", "BASELINE"):
        return {"error": "mode must be 'AI' or 'BASELINE'"}
    digital_twin.set_mode(body.mode)
    return {"mode": body.mode, "message": f"Switched to {body.mode} mode"}


@router.post("/reset")
def reset_session():
    """Clear energy logs and start a new session."""
    digital_twin.reset_session()
    return {"message": "Session reset successfully"}
