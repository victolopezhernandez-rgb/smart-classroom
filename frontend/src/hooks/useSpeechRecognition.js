import { useState, useEffect, useRef, useCallback } from "react";

/**
 * Custom React hook for the Web Speech API.
 *
 * Usage:
 *   const { isListening, transcript, start, stop, isSupported, error }
 *     = useSpeechRecognition({ onResult, language });
 *
 * Browser support: Chrome / Edge (full), Safari (partial), Firefox (none).
 * Works on localhost without HTTPS.
 */
export function useSpeechRecognition({ onResult, language = "en-US" } = {}) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript]   = useState("");
  const [isSupported, setIsSupported] = useState(true);
  const [error, setError]             = useState(null);
  const recognitionRef = useRef(null);
  // Keep a stable ref to onResult so the effect doesn't re-run on every render
  const onResultRef = useRef(onResult);
  useEffect(() => { onResultRef.current = onResult; }, [onResult]);

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setIsSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous      = false;
    recognition.interimResults  = false;
    recognition.maxAlternatives = 1;
    recognition.lang            = language;

    recognition.onstart = () => {
      setIsListening(true);
      setError(null);
      setTranscript("");
    };

    recognition.onresult = (event) => {
      const result = event.results[0][0].transcript;
      setTranscript(result);
      onResultRef.current?.(result.toLowerCase().trim());
    };

    recognition.onerror = (event) => {
      setError(event.error);
      setIsListening(false);
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
      try {
        recognitionRef.current.start();
      } catch {
        // Already started — ignore
      }
    }
  }, [isListening]);

  const stop = useCallback(() => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
  }, [isListening]);

  return { isListening, transcript, start, stop, isSupported, error };
}
