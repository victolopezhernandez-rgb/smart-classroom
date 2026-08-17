from __future__ import annotations

from shared.logger import get_logger
from shared import clock
from skills.command_parser import parse_command, command_to_lighting_state, ParsedCommand

logger = get_logger("VoiceAgent")


class VoiceAgent:
    """
    Stores and serves voice commands from the browser.

    Flow:
      Browser (Web Speech API) → POST /api/voice/command
          → VoiceAgent.receive(text)
          → OrchestratorAgent.get_voice_command() reads + clears it
    """

    def __init__(self):
        self._pending: ParsedCommand | None = None
        self._history: list[dict] = []
        logger.info("VoiceAgent started")

    def receive(self, raw_text: str) -> dict:
        """
        Parse and store a raw speech transcript.
        Returns the parsed command dict for immediate API response.
        """
        parsed = parse_command(raw_text)
        if parsed.is_valid():
            # Una emergencia se registra en el historial, pero NO se encola como
            # orden de luces: no es un override de comodidad, y quien la atiende
            # es el EmergencyAgent (ver routes/voice_routes.py).
            if parsed.emergency is None:
                self._pending = parsed
            entry = {
                **parsed.to_dict(),
                "timestamp": clock.now().isoformat(),
            }
            self._history.append(entry)
            # Keep only last 20 commands
            if len(self._history) > 20:
                self._history = self._history[-20:]
            if parsed.emergency:
                logger.warning(f"Voz → EMERGENCIA '{raw_text}' → {parsed.emergency}")
            elif parsed.scene:
                logger.info(f"Voz → escena '{raw_text}' → {parsed.scene} {parsed.zones}")
            else:
                logger.info(f"Command received: '{raw_text}' → action={parsed.action}, target={parsed.target}")
        else:
            logger.info(f"Unrecognized speech: '{raw_text}'")
        return parsed.to_dict()

    def consume(self) -> dict | None:
        """
        Returns the pending lighting state dict and clears it.
        Called by OrchestratorAgent each cycle. Returns None if nothing pending.
        """
        if self._pending is None:
            return None
        cmd = self._pending
        self._pending = None
        return command_to_lighting_state(cmd)

    def peek(self) -> dict | None:
        """Returns the pending parsed command without clearing it."""
        return self._pending.to_dict() if self._pending else None

    def get_history(self) -> list[dict]:
        return list(reversed(self._history))

    def clear(self):
        self._pending = None


# Singleton
voice_agent = VoiceAgent()
