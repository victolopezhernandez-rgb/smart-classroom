import { useEffect, useState, useRef } from "react";

export function useClassroomWebSocket(url = "ws://localhost:8000/ws") {
  const [state, setState]           = useState(null);
  const [lastDecision, setDecision] = useState(null);
  const [connected, setConnected]   = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    function connect() {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        setConnected(true);
        console.log("Connected to classroom backend");
      };

      ws.onclose = () => {
        setConnected(false);
        console.log("Disconnected — retrying in 3 seconds...");
        setTimeout(connect, 3000);
      };

      ws.onerror = () => ws.close();

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === "STATE_UPDATE")      setState(msg.payload);
        if (msg.type === "LIGHTING_DECISION") setDecision(msg.payload);
      };

      // Keepalive ping every 25 seconds
      const ping = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send("ping");
      }, 25000);

      wsRef.current = { ws, ping };
    }

    connect();

    return () => {
      if (wsRef.current) {
        clearInterval(wsRef.current.ping);
        wsRef.current.ws.close();
      }
    };
  }, [url]);

  return { state, lastDecision, connected };
}
