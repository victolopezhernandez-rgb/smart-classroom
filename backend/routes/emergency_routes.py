from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.emergency import emergency_agent
from agents.orchestrator import orchestrator
from skills.emergency_protocol import EMERGENCY_TYPES

router = APIRouter(prefix="/api/emergency", tags=["emergency"])


class TriggerRequest(BaseModel):
    kind: str   # "earthquake" | "fire" | "drill"


@router.get("/status")
def get_status():
    """Emergencia activa (si la hay), ruta de evacuación y tipos disponibles."""
    return emergency_agent.get_status()


@router.get("/types")
def get_types():
    """Catálogo de emergencias con su etiqueta, consejo y ritmo de parpadeo."""
    return {
        kind: {
            "label_es":  info["label_es"],
            "label_en":  info["label_en"],
            "advice_es": info["advice_es"],
            "advice_en": info["advice_en"],
            "blink_ms":  info["blink_ms"],
        }
        for kind, info in EMERGENCY_TYPES.items()
    }


@router.post("/trigger")
async def trigger(body: TriggerRequest):
    """
    Declara una emergencia. En una instalación real esto lo llamaría el
    acelerómetro, el detector de humo o el sistema de alerta temprana.

    Corre un ciclo de decisión enseguida para que la señalización aparezca
    de inmediato en vez de esperar al siguiente tick del orquestador.
    """
    try:
        emergency_agent.trigger(body.kind)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    await orchestrator.run_cycle()
    return {"message": f"Emergencia '{body.kind}' declarada", **emergency_agent.get_status()}


@router.post("/clear")
async def clear():
    """Da por terminada la emergencia y devuelve el control a la IA."""
    emergency_agent.clear()
    await orchestrator.run_cycle()
    return {"message": "Emergencia finalizada — control devuelto a la IA"}
