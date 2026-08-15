# Shared constants used across all agents

NATURAL_LIGHT_OFF_THRESHOLD  = 0.75   # Above this: turn zone lights OFF
NATURAL_LIGHT_DIM_THRESHOLD  = 0.40   # Above this: DIM the lights (50% power)
HIGH_CONSUMPTION_ALERT_WATTS = 280.0  # Alert if consumption exceeds this
DECISION_INTERVAL_SECONDS = 5        # How often the orchestrator runs
BASELINE_WATTS = 320.0               # All 8 fixtures on
WATTS_PER_ZONE_ON = 80.0             # 2 × 40W fixtures per zone
WATTS_PER_ZONE_DIM = 40.0
WATTS_PER_ZONE_OFF = 0.0
MIN_PEOPLE_TO_KEEP_LIGHTS_ON = 1     # Zone needs at least 1 person for lights to stay on
TARGET_SAVINGS_PERCENT       = 40    # Goal: save at least 40% vs baseline

# ── Emergencias ──────────────────────────────────────────────────────────────
# La puerta del salón está al fondo a la derecha → zona D.
EMERGENCY_EXIT_ZONE = "zone_D"

# Qué zonas colindan con cuál. Sirve para calcular por dónde pasa la gente
# camino a la salida. La zona diagonal a la salida no aparece como vecina:
# para llegar tiene que cruzar por una de las otras dos.
EMERGENCY_ZONE_NEIGHBORS = {
    "zone_A": ["zone_B", "zone_C"],
    "zone_B": ["zone_A", "zone_D"],
    "zone_C": ["zone_A", "zone_D"],
    "zone_D": ["zone_B", "zone_C"],
}

# Milisegundos de cada medio ciclo de parpadeo. Más urgente = más rápido:
# la frecuencia comunica gravedad antes de que nadie lea un cartel.
EMERGENCY_BLINK_MS = {
    "fire":       350,   # incendio: sal ya
    "earthquake": 600,   # sismo: primero cubrirse, luego evacuar
    "drill":      900,   # simulacro: ritmo calmado, es un ensayo
}

# Una lámpara que parpadea está encendida la mitad del tiempo, así que
# consume la mitad. El gemelo lo contabiliza igual que cualquier otro estado:
# una emergencia gasta energía y eso también se mide.
WATTS_PER_ZONE_BLINK = 40.0
