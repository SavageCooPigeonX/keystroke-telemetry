/* useLiveTrace — WebSocket hook for real-time execution events */
import { useState, useEffect, useRef, useCallback } from 'react';

const DEFAULT_WS = 'ws://127.0.0.1:8765';
const RECONNECT_MS = 3000;
const EVENT_WINDOW = 200; // max events to keep in memory

export default function useLiveTrace(wsUrl = DEFAULT_WS) {
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState([]);
  const [activeEdges, setActiveEdges] = useState({}); // edge_key -> expiry_ts
  const [activeNodes, setActiveNodes] = useState({}); // node_name -> expiry_ts
  const wsRef = useRef(null);
  const reconnectRef = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        if (reconnectRef.current) {
          clearTimeout(reconnectRef.current);
          reconnectRef.current = null;
        }
      };

      ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data);
          const evts = data.events || [];
          if (!evts.length) return;

          const now = Date.now();
          const EDGE_TTL = 1200;  // ms to keep edge highlighted
          const NODE_TTL = 800;   // ms to keep node highlighted

          setEvents(prev => {
            const next = [...prev, ...evts];
            return next.length > EVENT_WINDOW ? next.slice(-EVENT_WINDOW) : next;
          });

          // Activate edges and nodes based on call events
          const newEdges = {};
          const newNodes = {};
          for (const ev of evts) {
            if (ev.event === 'call' && ev.module) {
              newNodes[ev.module] = now + NODE_TTL;
              if (ev.caller && ev.caller !== ev.module) {
                const key = `${ev.caller}→${ev.module}`;
                newEdges[key] = now + EDGE_TTL;
              }
            }
          }

          if (Object.keys(newEdges).length) {
            setActiveEdges(prev => ({ ...prev, ...newEdges }));
          }
          if (Object.keys(newNodes).length) {
            setActiveNodes(prev => ({ ...prev, ...newNodes }));
          }
        } catch { /* ignore bad messages */ }
      };

      ws.onclose = () => {
        setConnected(false);
        reconnectRef.current = setTimeout(connect, RECONNECT_MS);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      reconnectRef.current = setTimeout(connect, RECONNECT_MS);
    }
  }, [wsUrl]);

  // Connect on mount
  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
    };
  }, [connect]);

  // Cleanup expired activations every 200ms
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      setActiveEdges(prev => {
        const next = {};
        let changed = false;
        for (const [k, exp] of Object.entries(prev)) {
          if (exp > now) next[k] = exp;
          else changed = true;
        }
        return changed ? next : prev;
      });
      setActiveNodes(prev => {
        const next = {};
        let changed = false;
        for (const [k, exp] of Object.entries(prev)) {
          if (exp > now) next[k] = exp;
          else changed = true;
        }
        return changed ? next : prev;
      });
    }, 200);
    return () => clearInterval(interval);
  }, []);

  return { connected, events, activeEdges, activeNodes };
}
