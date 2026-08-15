from __future__ import annotations
from datetime import datetime

from shared.classroom_state import classroom_state
from shared.logger import get_logger
from shared.thresholds import EMERGENCY_EXIT_ZONE
from skills.emergency_protocol import (
    EMERGENCY_TYPES,
    build_emergency_state,
    compute_route,
)

logger = get_logger("EmergencyAgent")


class EmergencyAgent:
    """
    Sexto agente del sistema: convierte una alerta de desastre natural en
    un patrón de iluminación de evacuación.

    En una instalación real la alerta no la escribe nadie a mano: llega de
    un acelerómetro (sismo), de un detector de humo (incendio) o del Sistema
    de Alerta Temprana. Aquí entra por una llamada HTTP, que es exactamente
    lo que haría ese sensor. El resto del sistema no cambia — es la misma
    arquitectura por capas del VisionAgent: hoy la señal se simula, mañana
    se conecta el sensor y ningún otro agente se entera.

    Prioridad: por encima de todo, incluida la voz. La regla "la voz manda"
    vale para comodidad, no para seguridad. Un profesor no debería poder
    apagar la señalización de evacuación sin antes declarar que la
    emergencia terminó.
    """

    def __init__(self):
        self.active: str | None = None        # "earthquake" | "fire" | "drill"
        self.started_at: str | None = None
        self._route: list = []
        logger.info("EmergencyAgent initialized — no active emergency")

    # ── Control ───────────────────────────────────────────────────────────────

    def trigger(self, kind: str):
        """Declara una emergencia. Sustituye a la que estuviera activa."""
        if kind not in EMERGENCY_TYPES:
            raise ValueError(
                f"Tipo de emergencia desconocido '{kind}'. "
                f"Válidos: {list(EMERGENCY_TYPES)}"
            )
        self.active = kind
        self.started_at = datetime.now().isoformat()
        logger.warning(f"EMERGENCIA DECLARADA: {kind} — salida por {EMERGENCY_EXIT_ZONE}")

    def clear(self):
        """Da por terminada la emergencia y devuelve el control a la IA."""
        if self.active:
            logger.warning(f"Emergencia finalizada: {self.active}")
        self.active = None
        self.started_at = None
        self._route = []
        classroom_state.emergency = None

    # ── Usado por el Orchestrator en cada ciclo ───────────────────────────────

    def get_lighting_state(self, occupancy: dict) -> dict:
        """
        Estado de iluminación para la emergencia activa, en el mismo formato
        que devuelve el motor de decisión normal. También deja en
        classroom_state.emergency el detalle que el navegador necesita para
        animar el parpadeo.
        """
        info = EMERGENCY_TYPES[self.active]
        self._route = compute_route(occupancy)

        classroom_state.emergency = {
            "kind":       self.active,
            "label_es":   info["label_es"],
            "label_en":   info["label_en"],
            "advice_es":  info["advice_es"],
            "advice_en":  info["advice_en"],
            "blink_ms":   info["blink_ms"],
            "route":      self._route,
            "exit_zone":  EMERGENCY_EXIT_ZONE,
            "started_at": self.started_at,
        }

        return build_emergency_state(self.active, occupancy)

    def get_status(self) -> dict:
        return {
            "active":     self.active is not None,
            "kind":       self.active,
            "started_at": self.started_at,
            "route":      self._route,
            "exit_zone":  EMERGENCY_EXIT_ZONE,
            "types":      list(EMERGENCY_TYPES),
        }


# Singleton
emergency_agent = EmergencyAgent()
