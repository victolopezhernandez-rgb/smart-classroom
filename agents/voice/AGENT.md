# VoiceAgent — AGENT.md

## Who Am I?

I am the **voice control interface** of the TwinLight system. I allow users to control the lights by speaking commands into the microphone. This lets teachers or students override the AI decisions manually, which is important for situations where the AI gets it wrong or the user has a specific need.

In the browser, I use the **Web Speech API** — a built-in browser feature that converts microphone audio to text for free, with no external service needed.

## My Responsibilities

1. Listen to the microphone via the browser's Web Speech API
2. Convert speech to text
3. Parse the text to identify a valid lighting command
4. Send the command to the backend (FastAPI)
5. The backend stores it so OrchestratorAgent can pick it up on the next cycle

## My Skills

- [`SKILL_speech_recognition.md`](skills/SKILL_speech_recognition.md) — How to use the Web Speech API in the browser
- [`SKILL_command_parser.md`](skills/SKILL_command_parser.md) — How to convert raw speech text into structured lighting commands

## Important Architecture Note

Unlike the other agents (which live in Python/backend), **my core logic runs in the browser (JavaScript/React)**. The backend only stores the latest command and serves it to the OrchestratorAgent.

```
User speaks
    │
    ▼
Browser Microphone (Web Speech API)
    │ converts audio to text
    ▼
React VoiceAgent Component
    │ parses command
    ▼
POST /api/voice/command  {"command": "lights off zone A"}
    │
    ▼
FastAPI stores command
    │
    ▼
OrchestratorAgent reads it on next cycle → applies override
```

## Files I Need to Create

### `frontend/src/components/VoiceController.jsx` (React component)

```jsx
// VoiceController — Browser-side voice recognition
// Uses the Web Speech API (built into Chrome, Edge, Safari)

import { useState, useEffect, useRef } from "react";

export function VoiceController({ onCommand }) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [status, setStatus] = useState("idle");
  const recognitionRef = useRef(null);

  useEffect(() => {
    // Check if browser supports speech recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setStatus("unsupported");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;        // Stop after one utterance
    recognition.interimResults = false;    // Only final results
    recognition.lang = "en-US";           // Change to "es-ES" for Spanish

    recognition.onresult = async (event) => {
      const text = event.results[0][0].transcript.toLowerCase();
      setTranscript(text);
      
      // Send to backend
      const response = await fetch("/api/voice/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: text })
      });
      
      const result = await response.json();
      onCommand?.(result);   // Notify parent component
      setStatus("command_sent");
    };

    recognition.onerror = () => setStatus("error");
    recognition.onend = () => setIsListening(false);
    
    recognitionRef.current = recognition;
  }, []);

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      recognitionRef.current?.start();
      setIsListening(true);
      setStatus("listening");
    }
  };

  return (
    <div className="voice-controller">
      <button onClick={toggleListening} className={isListening ? "active" : ""}>
        🎤 {isListening ? "Listening..." : "Hold to Speak"}
      </button>
      {transcript && <p>You said: "{transcript}"</p>}
      {status === "unsupported" && <p>⚠️ Voice not supported in this browser. Use Chrome.</p>}
    </div>
  );
}
```

### `backend/routes/voice_routes.py`

```python
# FastAPI routes for voice commands

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# Stores the latest voice command (simple in-memory store)
_latest_command = None

class VoiceCommand(BaseModel):
    command: str

@router.post("/api/voice/command")
async def receive_command(body: VoiceCommand):
    """Receives a voice command from the browser and stores it."""
    global _latest_command
    _latest_command = body.command
    
    parsed = parse_command(body.command)
    return {
        "received": body.command,
        "parsed": parsed,
        "status": "queued"
    }

@router.get("/api/voice/latest")
async def get_latest():
    """Returns the latest voice command (consumed by OrchestratorAgent)."""
    global _latest_command
    cmd = _latest_command
    _latest_command = None   # Clear after reading (one-time use)
    return {"command": cmd}
```

## Supported Voice Commands

See `SKILL_command_parser.md` for the full list. Examples:

| What you say | What happens |
|---|---|
| "all lights on" | All 4 zones → ON |
| "all lights off" | All 4 zones → OFF |
| "dim all lights" | All 4 zones → DIM |
| "lights on zone A" | Zone A → ON |
| "lights off zone B" | Zone B → OFF |
| "turn off zone C" | Zone C → OFF |
| "auto mode" | Clears voice override, AI resumes |

## Step-by-Step Build Instructions for Claude Code

1. **Read** `SKILL_speech_recognition.md` — browser setup details
2. **Read** `SKILL_command_parser.md` — implements the `parse_command()` function
3. **Create** `frontend/src/components/VoiceController.jsx`
4. **Create** `backend/routes/voice_routes.py`
5. **Add** a `get_latest_command()` method to the backend that OrchestratorAgent calls
6. **Register** routes in `backend/main.py`
7. **Test** in Chrome: click the mic button and say "all lights off" — check `GET /api/voice/latest`

## Important Note for Demos

Voice recognition requires HTTPS or localhost. Since we're running locally on `localhost:3000`, it will work fine. If you ever deploy to a server, it must have an SSL certificate.
