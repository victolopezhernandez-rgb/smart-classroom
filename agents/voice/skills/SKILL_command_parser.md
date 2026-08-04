# SKILL: Command Parser

## What This Skill Does

Converts raw speech text (a string like "turn off zone a please") into a structured command that the OrchestratorAgent can execute. This parser is intentionally flexible — it uses keyword matching rather than exact phrases so natural variations in speech are handled correctly.

## Implementation

```python
# backend/skills/command_parser.py

from dataclasses import dataclass
from typing import Literal

ZoneTarget = Literal["zone_A", "zone_B", "zone_C", "zone_D", "all", None]
LightAction = Literal["on", "off", "dim", "auto", None]

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
            "action": self.action,
            "target": self.target,
            "raw": self.raw_text,
            "confidence": self.confidence
        }


def parse_command(text: str) -> ParsedCommand:
    """
    Parses a speech recognition result into a structured lighting command.
    
    Args:
        text: Raw transcript from Web Speech API (already lowercased)
    
    Returns:
        ParsedCommand with action and target zone
    
    Examples:
        "all lights off"         → action="off",  target="all"
        "lights on zone a"       → action="on",   target="zone_A"
        "dim zone b"             → action="dim",  target="zone_B"
        "turn off zone c please" → action="off",  target="zone_C"
        "auto mode"              → action="auto", target=None
        "hello world"            → action=None    (invalid, ignored)
    """
    text = text.lower().strip()

    # --- Detect ACTION ---
    action = None
    if any(word in text for word in ["on", "encender", "turn on", "activate"]):
        action = "on"
    if any(word in text for word in ["off", "apagar", "turn off", "deactivate"]):
        action = "off"
    if any(word in text for word in ["dim", "dimmer", "reduce", "atenuar", "half"]):
        action = "dim"
    if any(word in text for word in ["auto", "automatic", "ai mode", "smart mode"]):
        action = "auto"

    if action is None:
        return ParsedCommand(action=None, target=None, raw_text=text, confidence=0.0)

    # --- Detect TARGET ZONE ---
    target = None

    if any(word in text for word in ["all", "everything", "toda", "todas", "todo"]):
        target = "all"
    elif any(word in text for word in ["zone a", "zona a", "section a", "front left"]):
        target = "zone_A"
    elif any(word in text for word in ["zone b", "zona b", "section b", "front right"]):
        target = "zone_B"
    elif any(word in text for word in ["zone c", "zona c", "section c", "back left"]):
        target = "zone_C"
    elif any(word in text for word in ["zone d", "zona d", "section d", "back right"]):
        target = "zone_D"
    else:
        # Default: if no zone specified, apply to all
        target = "all"

    confidence = 1.0 if target != "all" or "all" in text else 0.8

    return ParsedCommand(
        action=action,
        target=target,
        raw_text=text,
        confidence=confidence
    )


def command_to_lighting_state(parsed: ParsedCommand, zones: list[str]) -> dict | None:
    """
    Converts a ParsedCommand into a lighting state dict for OrchestratorAgent.
    Returns None if the command is invalid.
    """
    if not parsed.is_valid():
        return None

    if parsed.action == "auto":
        return {"__clear_override__": True}   # Special signal to resume AI mode

    state_map = {"on": "ON", "off": "OFF", "dim": "DIM"}
    light_state = state_map[parsed.action]

    if parsed.target == "all":
        return {
            zone: {"state": light_state, "reason": f"Voice: {parsed.raw_text}"}
            for zone in zones
        }
    else:
        return {
            parsed.target: {"state": light_state, "reason": f"Voice: {parsed.raw_text}"}
        }
```

## Supported Commands Reference

| What you say (English) | What you can also say | Result |
|---|---|---|
| "all lights on" | "turn on everything" | All zones → ON |
| "all lights off" | "turn off all" | All zones → OFF |
| "dim all lights" | "half lights" | All zones → DIM |
| "lights on zone A" | "zone a on", "activate zone a" | Zone A → ON |
| "lights off zone B" | "turn off zone b" | Zone B → OFF |
| "dim zone C" | "reduce zone c", "atenuar zona c" | Zone C → DIM |
| "auto mode" | "automatic", "smart mode" | Clear override, AI resumes |

## Tests

```python
from skills.command_parser import parse_command, command_to_lighting_state

zones = ["zone_A", "zone_B", "zone_C", "zone_D"]

# Test 1: All off
cmd = parse_command("all lights off")
assert cmd.action == "off" and cmd.target == "all"

# Test 2: Specific zone on
cmd = parse_command("turn on zone b please")
assert cmd.action == "on" and cmd.target == "zone_B"

# Test 3: Auto mode
cmd = parse_command("auto mode")
state = command_to_lighting_state(cmd, zones)
assert state.get("__clear_override__") == True

# Test 4: Invalid command
cmd = parse_command("hello classroom")
assert cmd.action is None

print("Command parser tests passed!")
```

## Step-by-Step Build Instructions for Claude Code

1. **Create** `backend/skills/command_parser.py` with the code above
2. **Import** `parse_command` and `command_to_lighting_state` in `backend/routes/voice_routes.py`
3. **Call** `parse_command()` on every incoming voice command before storing it
4. **Return** the parsed result in the API response (so the frontend can show what was understood)
5. **Run** the tests to verify all cases work
