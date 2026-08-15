"""
Protocolo de iluminación de emergencia.

La idea es sencilla y viene de cómo funciona la señalización de evacuación
real: la luz FIJA marca por dónde salir, la luz INTERMITENTE dice "aquí no
te quedes". Un salón entero parpadeando no comunica nada; parpadeando salvo
la ruta, sí.

    RUTA   → ON     luz fija, 100%, marca el camino a la puerta
    ALERTA → BLINK  parpadea para llamar la atención

La puerta del salón está al fondo a la derecha, o sea en la zona D
(ver data/classroom_config.json y skills/zone_mapping.py). Por eso la zona
de salida siempre es zone_D.

La ruta NO es fija: se calcula con la ocupación que reporta el VisionAgent.
Si hay gente adelante a la izquierda (zona A), su camino a la puerta pasa
por B o por C, así que esa zona intermedia también se enciende fija. Es la
misma integración entre agentes que usa el modo normal, aplicada a evacuar.
"""

from shared.thresholds import (
    EMERGENCY_EXIT_ZONE,
    EMERGENCY_BLINK_MS,
    EMERGENCY_ZONE_NEIGHBORS,
)

CLASSROOM_ZONES = ["zone_A", "zone_B", "zone_C", "zone_D"]

# Cada tipo de evento aporta el texto que se registra y la velocidad del
# parpadeo. Más urgente = más rápido, que es como se comportan las alarmas
# reales: la frecuencia comunica gravedad antes que cualquier cartel.
EMERGENCY_TYPES = {
    "earthquake": {
        "label_es": "Sismo",
        "label_en": "Earthquake",
        "blink_ms": EMERGENCY_BLINK_MS["earthquake"],
        "advice_es": "Cúbrete, luego evacúa por la ruta iluminada",
        "advice_en": "Take cover, then evacuate along the lit route",
    },
    "fire": {
        "label_es": "Incendio",
        "label_en": "Fire",
        "blink_ms": EMERGENCY_BLINK_MS["fire"],
        "advice_es": "Evacúa de inmediato por la ruta iluminada",
        "advice_en": "Evacuate immediately along the lit route",
    },
    "drill": {
        "label_es": "Simulacro",
        "label_en": "Drill",
        "blink_ms": EMERGENCY_BLINK_MS["drill"],
        "advice_es": "Simulacro de evacuación — sigue la ruta iluminada",
        "advice_en": "Evacuation drill — follow the lit route",
    },
}


def compute_route(occupancy: dict) -> list:
    """
    Devuelve las zonas que deben quedar con luz FIJA: la salida más las
    zonas intermedias por las que la gente tiene que pasar para llegar.

    Con 0 personas la ruta se reduce a la salida: no hay a quién guiar,
    pero la puerta se deja marcada para quien entre a verificar.
    """
    route = [EMERGENCY_EXIT_ZONE]

    for zone in CLASSROOM_ZONES:
        if zone == EMERGENCY_EXIT_ZONE or occupancy.get(zone, 0) <= 0:
            continue
        # Zona pegada a la salida: la gente sale directo por ahí.
        if zone in EMERGENCY_ZONE_NEIGHBORS[EMERGENCY_EXIT_ZONE]:
            if zone not in route:
                route.append(zone)
        else:
            # Zona diagonal (A respecto a D): su camino pasa por una
            # vecina. Se ilumina la que esté más despejada — menos gente
            # en el paso significa evacuación más rápida.
            options = EMERGENCY_ZONE_NEIGHBORS[EMERGENCY_EXIT_ZONE]
            bridge = min(options, key=lambda z: occupancy.get(z, 0))
            if bridge not in route:
                route.append(bridge)

    return route


def build_emergency_state(kind: str, occupancy: dict) -> dict:
    """
    Construye el estado de iluminación completo para una emergencia.

    Devuelve el mismo formato que run_decision_engine, para que el
    Orchestrator y el DigitalTwin no tengan que distinguir el caso:
        {"zone_A": {"state": "BLINK", "reason": "..."} , ...}
    """
    info = EMERGENCY_TYPES.get(kind, EMERGENCY_TYPES["drill"])
    route = compute_route(occupancy)
    label = info["label_es"]

    state = {}
    for zone in CLASSROOM_ZONES:
        if zone in route:
            marker = "salida" if zone == EMERGENCY_EXIT_ZONE else "paso hacia la salida"
            state[zone] = {
                "state":  "ON",
                "reason": f"{label} — ruta de evacuación ({marker})",
            }
        else:
            state[zone] = {
                "state":  "BLINK",
                "reason": f"{label} — alerta intermitente, despejar la zona",
            }

    return state
