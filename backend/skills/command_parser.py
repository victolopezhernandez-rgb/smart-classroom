from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

ZoneTarget  = Literal["zone_A", "zone_B", "zone_C", "zone_D", "all", None]
# "scene" = la frase describía una situación de clase y el patrón de luces
# viene resuelto zona por zona en ParsedCommand.zones.
LightAction = Literal["on", "off", "dim", "auto", "scene", None]

CLASSROOM_ZONES = ["zone_A", "zone_B", "zone_C", "zone_D"]


@dataclass
class ParsedCommand:
    action: LightAction
    target: ZoneTarget
    raw_text: str
    confidence: float   # 1.0 = certain match, 0.5 = best guess

    # Escena reconocida ("movie", "reading"…), si la frase dijo una intención
    # en vez de una orden literal. Solo sirve para mostrar y registrar.
    scene: str | None = None
    scene_es: str | None = None
    scene_en: str | None = None

    # Estado luz por luz, cuando la escena no trata todas las zonas igual.
    zones: dict | None = None

    # Emergencia declarada de viva voz: "fire" | "earthquake" | "drill",
    # o "clear" para darla por terminada.
    emergency: str | None = None

    def is_valid(self) -> bool:
        return self.action is not None or self.emergency is not None

    def to_dict(self) -> dict:
        return {
            "action":     self.action,
            "target":     self.target,
            "raw":        self.raw_text,
            "confidence": self.confidence,
            "scene":      self.scene,
            "scene_es":   self.scene_es,
            "scene_en":   self.scene_en,
            "zones":      self.zones,
            "emergency":  self.emergency,
        }


# ── Emergencias dichas de viva voz ────────────────────────────────────────────
# Nadie grita "activar protocolo de evacuación tipo incendio". Grita "¡fuego!".
# Estas frases son la forma en que una persona avisa de verdad.
#
# El orden importa: "clear" va PRIMERO porque "terminó el simulacro" contiene la
# palabra "simulacro", y si se revisara al revés, decir que la emergencia acabó
# la volvería a encender.
EMERGENCY_PHRASES = [
    ("clear", [
        "ya pasó", "ya paso", "todo despejado", "todo en orden", "falsa alarma",
        "fin de la emergencia", "terminó la emergencia", "termino la emergencia",
        "terminó el simulacro", "termino el simulacro", "cancelar emergencia",
        "all clear", "emergency over", "false alarm", "stand down",
    ]),
    ("fire", [
        "incendio", "fuego", "se quema", "se está quemando", "se esta quemando",
        "hay humo", "fire", "smoke",
    ]),
    ("earthquake", [
        "temblor", "está temblando", "esta temblando", "sismo", "terremoto",
        "earthquake", "quake", "tremor",
    ]),
    ("drill", [
        "simulacro", "practiquemos la salida", "drill", "evacuation drill",
        "practice evacuation",
    ]),
]


# ── Escenas: lo que se quiere hacer, no qué luz tocar ─────────────────────────
# Un profesor no dice "apaga las zonas A y B y atenúa C y D". Dice "vamos a ver
# una película". Estas frases traducen una intención de clase a un patrón de
# luces — que es exactamente lo que hace una instalación real: el interruptor
# de verdad no está etiquetado "zona A", está etiquetado "proyección".
#
# Fíjate que una escena puede tratar cada zona distinto. Para ver una película
# se apagan las de adelante, que son las que lavan la pantalla, y se dejan
# atenuadas las de atrás para que se pueda tomar apuntes sin quedar a oscuras.
# Eso es lo que separa una señal de un interruptor.
SCENES = [
    {
        "id": "movie",
        "es": "Proyección", "en": "Screening",
        "keywords": [
            "película", "pelicula", "peli", "proyector", "proyección", "proyeccion",
            "ver un video", "poner un video", "presentación", "presentacion",
            "diapositivas", "movie", "film", "projector", "slides", "screening",
            "watch a video",
        ],
        # A y B están al frente, junto al tablero: son las que estorban.
        "zones": {"zone_A": "OFF", "zone_B": "OFF", "zone_C": "DIM", "zone_D": "DIM"},
    },
    {
        "id": "reading",
        "es": "Lectura o examen", "en": "Reading or exam",
        "keywords": [
            "vamos a leer", "hora de leer", "lectura", "leer", "examen", "evaluación",
            "evaluacion", "prueba escrita", "taller escrito", "escribir",
            "reading", "exam", "test", "quiz", "writing",
        ],
        # Leer y escribir piden luz pareja: aquí no se ahorra a costa de la vista.
        "zones": {z: "ON" for z in CLASSROOM_ZONES},
    },
    {
        "id": "leaving",
        "es": "Salida", "en": "Leaving",
        "keywords": [
            "nos vamos", "salimos", "salida", "recreo", "descanso",
            "terminó la clase", "termino la clase", "se acabó la clase",
            "se acabo la clase", "última hora", "ultima hora", "cerrar el salón",
            "cerrar el salon", "class is over", "we are leaving", "recess",
            "break time", "going home",
        ],
        "zones": {z: "OFF" for z in CLASSROOM_ZONES},
    },
    {
        "id": "group_work",
        "es": "Trabajo en grupo", "en": "Group work",
        "keywords": [
            "trabajo en grupo", "trabajemos en grupo", "en equipos", "por equipos",
            "mesa redonda", "group work", "team work", "in teams",
        ],
        # Todos de pie y moviéndose: la IA reparte mejor que una orden fija.
        "action": "auto",
    },
]


def _match_emergency(text: str) -> str | None:
    for kind, phrases in EMERGENCY_PHRASES:
        if any(p in text for p in phrases):
            return kind
    return None


def _match_scene(text: str) -> dict | None:
    for scene in SCENES:
        if any(k in text for k in scene["keywords"]):
            return scene
    return None


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

    Antes de mirar palabra por palabra se buscan dos cosas que se dicen en
    lenguaje normal: una emergencia ("hay un incendio") y una escena de clase
    ("vamos a ver una película"). Van primero a propósito — si se revisaran
    después, "vamos a ver una película" no encontraría ningún verbo de luces y
    se perdería, y "hay un incendio" tampoco.
    """
    text = text.lower().strip()

    # ── ¿Es una emergencia? ───────────────────────────────────────────────────
    # Esto no enciende ni apaga nada por su cuenta: solo deja dicho qué pasó.
    # Quien la declara es el EmergencyAgent, que es el que manda en ese caso.
    emergency = _match_emergency(text)
    if emergency is not None:
        return ParsedCommand(
            action=None, target=None, raw_text=text, confidence=1.0,
            emergency=emergency,
        )

    # ── ¿Es una escena de clase? ──────────────────────────────────────────────
    scene = _match_scene(text)
    if scene is not None:
        if "action" in scene:
            return ParsedCommand(
                action=scene["action"], target="all", raw_text=text, confidence=1.0,
                scene=scene["id"], scene_es=scene["es"], scene_en=scene["en"],
            )
        return ParsedCommand(
            action="scene", target="all", raw_text=text, confidence=1.0,
            scene=scene["id"], scene_es=scene["es"], scene_en=scene["en"],
            zones=dict(scene["zones"]),
        )

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

    # Las emergencias no pasan por aquí: las atiende el EmergencyAgent, que
    # manda por encima de la voz. Ver routes/voice_routes.py.
    if parsed.emergency is not None:
        return None

    if parsed.action == "auto":
        return {"__clear_override__": True}

    # Escena: el patrón ya viene resuelto zona por zona.
    if parsed.action == "scene" and parsed.zones:
        reason = f"Voz: {parsed.scene_es} — \"{parsed.raw_text}\""
        return {z: {"state": s, "reason": reason} for z, s in parsed.zones.items()}

    light_state = {"on": "ON", "off": "OFF", "dim": "DIM"}[parsed.action]
    reason = f"Voice: \"{parsed.raw_text}\""

    if parsed.target == "all":
        return {z: {"state": light_state, "reason": reason} for z in CLASSROOM_ZONES}
    else:
        return {parsed.target: {"state": light_state, "reason": reason}}
