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
            "half_class": "12 people in front half — zones A+B only",
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


# ── Live camera vision ────────────────────────────────────────────────────────


class Detection(BaseModel):
    x: float   # 0..1, mirrored camera space (0 = left of displayed video)
    y: float   # 0..1, top of frame = front of classroom


class LiveDetectionsRequest(BaseModel):
    people: list[Detection]


@router.post("/live")
def post_live_detections(body: LiveDetectionsRequest):
    """
    Receive real people detections from the browser webcam.
    Coordinates are normalized (0..1); the agent maps them to room meters.
    """
    count = vision_agent.set_live_detections([p.model_dump() for p in body.people])
    return {"received": count, "source": vision_agent.source}


class SourceRequest(BaseModel):
    source: str   # "simulated" | "live_camera"


@router.post("/mode")
def set_source(body: SourceRequest):
    """Explicitly switch the VisionAgent between simulated and live_camera."""
    try:
        vision_agent.set_source(body.source)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"source": vision_agent.source}


@router.get("/mode")
def get_source():
    """Current vision source and how stale the live feed is (seconds)."""
    return {
        "source": vision_agent.source,
        "stale_seconds": round(vision_agent.live_stale_seconds(), 1),
    }

