from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.vision import vision_agent, VALID_SCENARIOS
from skills.zone_mapping import get_zone_bounds

router = APIRouter(prefix="/api/vision", tags=["vision"])


@router.get("/occupancy")
def get_occupancy():
    """People count per zone + total. Updates positions slightly each call."""
    return vision_agent.get_occupancy()


@router.get("/positions")
def get_positions():
    """Full position list [{id, x, y, zone}] for 3D rendering."""
    return vision_agent.get_people_positions()


@router.get("/scenarios")
def list_scenarios():
    """List all available simulation scenarios."""
    return {
        "scenarios": VALID_SCENARIOS,
        "current": vision_agent.scenario,
        "descriptions": {
            "empty":      "0 people — all lights OFF",
            "few":        "6 people, scattered — only occupied zones lit",
            "half_class": "18 people in front half — zones A+B only",
            "full_class": "30 people, all zones — full AI optimization",
            "back_only":  "12 people in back — zones C+D only",
        },
    }


class ScenarioRequest(BaseModel):
    scenario: str


@router.post("/scenario")
def set_scenario(body: ScenarioRequest):
    """Change the occupancy simulation scenario."""
    try:
        vision_agent.set_scenario(body.scenario)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "scenario": vision_agent.scenario,
        "people_count": len(vision_agent.people),
        "message": f"Scenario set to '{body.scenario}'",
    }
