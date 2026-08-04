import { useState, useCallback } from "react";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition.js";

const EXAMPLE_COMMANDS = [
  "all lights off",
  "all lights on",
  "dim all lights",
  "lights on zone A",
  "lights off zone B",
  "dim zone C",
  "auto mode",
];

export function VoiceController({ onCommandResult }) {
  const [lastResult, setLastResult]   = useState(null);
  const [sending, setSending]         = useState(false);

  const handleResult = useCallback(async (text) => {
    setSending(true);
    try {
      const res = await fetch("/api/voice/command", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ command: text }),
      });
      const data = await res.json();
      setLastResult(data);
      onCommandResult?.(data);
    } catch {
      setLastResult({ status: "error", received: text });
    } finally {
      setSending(false);
    }
  }, [onCommandResult]);

  const { isListening, transcript, start, stop, isSupported, error } =
    useSpeechRecognition({ onResult: handleResult, language: "en-US" });

  if (!isSupported) {
    return (
      <div className="panel">
        <h2>Voice Control</h2>
        <div style={{ color: "#f87171", fontSize: "0.875rem" }}>
          Voice recognition requires Chrome or Edge. Firefox is not supported.
        </div>
      </div>
    );
  }

  const micColor     = isListening ? "#ef4444" : "#4ade80";
  const actionLabel  = lastResult?.parsed?.action;
  const targetLabel  = lastResult?.parsed?.target;

  return (
    <div className="panel">
      <h2>Voice Control</h2>

      {/* Microphone button */}
      <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "0.875rem" }}>
        <button
          onMouseDown={start}
          onMouseUp={stop}
          onTouchStart={start}
          onTouchEnd={stop}
          style={{
            width: "3.5rem",
            height: "3.5rem",
            borderRadius: "50%",
            border: `2px solid ${micColor}`,
            background: isListening ? micColor + "22" : "transparent",
            color: micColor,
            fontSize: "1.5rem",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 0.2s",
            flexShrink: 0,
          }}
          title="Hold to speak"
        >
          🎤
        </button>

        <div style={{ fontSize: "0.8rem" }}>
          {isListening
            ? <span style={{ color: "#ef4444", fontWeight: 600 }}>Listening…</span>
            : sending
            ? <span style={{ color: "#f97316" }}>Sending…</span>
            : <span style={{ color: "#64748b" }}>Hold to speak</span>
          }
          {transcript && (
            <div style={{ color: "#94a3b8", marginTop: "0.2rem" }}>
              "{transcript}"
            </div>
          )}
        </div>
      </div>

      {/* Last parsed result */}
      {lastResult && (
        <div style={{
          background: "#141820",
          border: "1px solid #2d3148",
          borderRadius: "0.375rem",
          padding: "0.625rem",
          fontSize: "0.75rem",
          marginBottom: "0.875rem",
        }}>
          <div style={{ color: "#64748b", marginBottom: "0.25rem" }}>Last command</div>
          {lastResult.parsed?.action ? (
            <div>
              <span style={{ color: "#4ade80", fontWeight: 600 }}>{actionLabel?.toUpperCase()}</span>
              {" → "}
              <span style={{ color: "#94a3b8" }}>{targetLabel ?? "—"}</span>
              <span style={{ float: "right", color: "#334155" }}>
                {Math.round((lastResult.parsed?.confidence ?? 0) * 100)}% conf.
              </span>
            </div>
          ) : (
            <div style={{ color: "#f87171" }}>Not recognized — try again</div>
          )}
        </div>
      )}

      {/* Error display */}
      {error && (
        <div style={{ color: "#f87171", fontSize: "0.75rem", marginBottom: "0.5rem" }}>
          {error === "not-allowed"
            ? "Microphone access denied — allow it in browser settings"
            : error === "no-speech"
            ? "No speech detected — try again"
            : `Error: ${error}`}
        </div>
      )}

      {/* Example commands cheat sheet */}
      <details style={{ fontSize: "0.7rem" }}>
        <summary style={{ color: "#475569", cursor: "pointer", marginBottom: "0.375rem" }}>
          Example commands
        </summary>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.2rem", marginTop: "0.375rem" }}>
          {EXAMPLE_COMMANDS.map((cmd) => (
            <code
              key={cmd}
              style={{
                background: "#141820",
                padding: "0.2rem 0.4rem",
                borderRadius: "0.25rem",
                color: "#94a3b8",
              }}
            >
              "{cmd}"
            </code>
          ))}
        </div>
      </details>
    </div>
  );
}
