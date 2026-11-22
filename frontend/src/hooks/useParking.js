import { useState, useEffect, useRef, useCallback } from "react";

const WS_URL = "ws://localhost:8000/ws";
const RECONNECT_DELAY = 3000;

export function useParking() {
  const [summary, setSummary]     = useState(null);
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const wsRef = useRef(null);
  const timerRef = useRef(null);

  const connect = useCallback(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      clearTimeout(timerRef.current);
    };

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.data) {
        setSummary(msg.data);
        setLastUpdate(new Date().toLocaleTimeString());
      }
    };

    ws.onclose = () => {
      setConnected(false);
      timerRef.current = setTimeout(connect, RECONNECT_DELAY);
    };

    ws.onerror = () => ws.close();
  }, []);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(timerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { summary, connected, lastUpdate };
}
