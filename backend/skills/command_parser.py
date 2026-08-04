from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

ZoneTarget  = Literal["zone_A", "zone_B", "zone_C", "zone_D", "all", None]
LightAction = Literal["on", "off", "dim", "auto", None]

CLASSROOM_ZONES = ["zone_A", "zone_B", "zone_C", "zone_D"]


@dataclass
class ParsedCommand:
    action: LightAction
    target: ZoneTarget
    raw_text: str
    confidence: float   # 1.0 = certain match, 0.5 = best guess

    def is_valid(self) -> bool:
        return self.action is not None

    def to_dict(self) -> dict:
        return {
            "action":     self.action,
            "target":     self.target,
            "raw":        self.raw_text,
            "confidence": self.confidence,
        }


def parse_command(text: str) -> ParsedCommand:
    """
    Parses a speech recognition result into a structured lighting command.

    Handles English and Spanish keywords.

    Examples:
        "all lights off"         → action="off",  target="all"
        "lights on zone a"       → action="on",   target="zone_A"
        "dim zone b"             → action="dim",  target="zone_B"
        "turn off zone c please" → action="off",  target="zone_C"
        "auto mode"              → action="auto", target=None
        "hello world"            → action=None    (invalid)
    """
    text = text.lower().strip()

    # ── Detect ACTION ─────────────────────────────────────────────────────────
    action = None
    if any(w in text for w in ["auto", "automático", "automatico", "modo auto", "modo automático", "modo automatico", "ai mode", "smart mode"]):
        action = "auto"
    elif any(w in text for w in ["atenuar", "atenúa", "atenua", "dim", "dimmer", "reduce", "reducir", "medio", "mitad", "50%", "media luz", "medias luces"]):
        action = "dim"
    elif any(w in text for w in ["apagar", "apaga", "apaguen", "apaga las", "off", "turn off", "deactivate", "switch off", "sin luz", "sin luces"]):
        action = "off"
    elif any(w in text for w in ["encender", "enciende", "enciendan", "prender", "prende", "prendan", "on", "turn on", "activate", "switch on", "con luz", "con luces"]):
        action = "on"

    if action is None:
        return ParsedCommand(action=None, target=None, raw_text=text, confidence=0.0)

    # ── Detect TARGET ZONE ────────────────────────────────────────────────────
    target = None

    if any(w in text for w in ["todo", "toda", "todas", "todos", "all", "everything", "every", "general"]):
        target = "all"
    elif any(w in text for w in ["zona a", "zone a", "sección a", "seccion a", "frente izquierda", "frente izq"]):
        target = "zone_A"
    elif any(w in text for w in ["zona b", "zone b", "sección b", "seccion b", "frente derecha", "frente der"]):
        target = "zone_B"
    elif any(w in text for w in ["zona c", "zone c", "sección c", "seccion c", "atrás izquierda", "atras izquierda", "atrás izq", "atras izq"]):
        target = "zone_C"
    elif any(w in text for w in ["zona d", "zone d", "sección d", "seccion d", "atrás derecha", "atras derecha", "atrás der", "atras der"]):
        target = "zone_D"
    else:
        target = "all"

    confidence = 1.0 if (target != "all" or any(w in text for w in ["todo", "toda", "todas", "todos", "all"])) else 0.8

    return ParsedCommand(
        action=action,
        target=target,
        raw_text=text,
        confidence=confidence,
    )


def command_to_lighting_state(parsed: ParsedCommand) -> dict | None:
    """
    Converts a ParsedCommand into a lighting state dict consumed by OrchestratorAgent.
    Returns None if the command is invalid.
    Returns {"__clear_override__": True} for "auto mode".
    """
    if not parsed.is_valid():
        return None

    if parsed.action == "auto":
        return {"__clear_override__": True}

    light_state = {"on": "ON", "off": "OFF", "dim": "DIM"}[parsed.action]
    reason = f"Voice: \"{parsed.raw_text}\""

    if parsed.target == "all":
        return {z: {"state": light_state, "reason": reason} for z in CLASSROOM_ZONES}
    else:
        return {parsed.target: {"state": light_state, "reason": reason}}
