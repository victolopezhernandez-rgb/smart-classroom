# SKILL: Speech Recognition

## What This Skill Does

Sets up the browser's Web Speech API to capture microphone input and convert it to text. This is a completely free, built-in browser feature — no API key, no external service, no cost.

## Browser Compatibility

| Browser | Supported? |
|---|---|
| Chrome (desktop) | ✅ Full support |
| Edge | ✅ Full support |
| Safari (Mac/iOS) | ⚠️ Partial support |
| Firefox | ❌ Not supported |

**Recommendation for the STEAM fair:** Use Chrome on a laptop.

## Full React Hook Implementation

```javascript
// frontend/src/hooks/useSpeechRecognition.js

import { useState, useEffect, useRef, useCallback } from "react";

/**
 * Custom React hook for speech recognition.
 * 
 * Usage:
 *   const { isListening, transcript, start, stop, isSupported } = useSpeechRecognition();
 */
export function useSpeechRecognition({ onResult, language = "en-US" } = {}) {
  const [isListening, setIsListening]     = useState(false);
  const [transcript, setTranscript]       = useState("");
  const [isSupported, setIsSupported]     = useState(true);
  const [error, setError]                 = useState(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setIsSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    
    // Configuration
    recognition.continuous     = false;   // One utterance at a time
    recognition.interimResults = false;   // Wait for final result only
    recognition.maxAlternatives = 1;      // Return best guess only
    recognition.lang = language;          // "en-US" or "es-ES"

    // Event handlers
    recognition.onstart = () => {
      setIsListening(true);
      setError(null);
      setTranscript("");
    };

    recognition.onresult = (event) => {
      const result = event.results[0][0].transcript;
      setTranscript(result);
      onResult?.(result.toLowerCase().trim());
    };

    recognition.onerror = (event) => {
      setError(event.error);
      setIsListening(false);
      
      // Common errors:
      // "not-allowed"    → user denied microphone permission
      // "no-speech"      → user didn't say anything
      // "network"        → browser couldn't reach speech server
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.abort();
    };
  }, [language]);

  const start = useCallback(() => {
    if (recognitionRef.current && !isListening) {
      recognitionRef.current.start();
    }
  }, [isListening]);

  const stop = useCallback(() => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
  }, [isListening]);

  return { isListening, transcript, start, stop, isSupported, error };
}
```

## Usage in VoiceController Component

```jsx
// How to use the hook inside VoiceController.jsx

import { useSpeechRecognition } from "../hooks/useSpeechRecognition";

function VoiceController() {
  const { isListening, transcript, start, stop, isSupported, error } =
    useSpeechRecognition({
      language: "en-US",
      onResult: async (text) => {
        // Send to backend immediately when speech is recognized
        await fetch("/api/voice/command", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ command: text }),
        });
      },
    });

  if (!isSupported) {
    return <p>⚠️ Please use Chrome for voice control.</p>;
  }

  return (
    <div>
      <button
        onMouseDown={start}
        onMouseUp={stop}
        onTouchStart={start}
        onTouchEnd={stop}
      >
        {isListening ? "🔴 Listening..." : "🎤 Hold to speak"}
      </button>
      {transcript && <p>Heard: "{transcript}"</p>}
      {error === "not-allowed" && <p>🚫 Please allow microphone access</p>}
    </div>
  );
}
```

## Step-by-Step Build Instructions for Claude Code

1. **Create** `frontend/src/hooks/useSpeechRecognition.js` with the hook above
2. **Import** and use it inside `frontend/src/components/VoiceController.jsx`
3. **Test** in Chrome: open the browser console and check for recognition events
4. If you get a "not-allowed" error: go to Chrome Settings → Privacy → Microphone and allow localhost
