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
  const [nodeHeat, setNodeHeat] = useState({});       // node_name -> { calls, deaths, lastSeen }
  const [testStatus, setTestStatus] = useState({});    // node_name -> 'alive' | 'dead' | null
  const [deadPaths, setDeadPaths] = useState({});      // node_name -> ['detail1', ...]
  const wsRef = useRef(null);
  const reconnectRef = useRef(null);
  const onRawMessageRef = useRef(null);  // callback for non-event messages (chat, etc.)

  const sendMessage = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

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

          // Forward non-event messages (chat_response, etc.) to raw handler
          if (data.type && data.type !== 'events' && data.type !== 'history') {
            if (onRawMessageRef.current) onRawMessageRef.current(data);
            if (!data.events) return;
          }

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
          const heatUpdates = {};
          const statusUpdates = {};
          const deadUpdates = {};  // node -> [detail, ...]

          for (const ev of evts) {
            const mod = ev.module;
            if (!mod) continue;

            if (ev.event === 'call') {
              newNodes[mod] = now + NODE_TTL;
              if (ev.caller && ev.caller !== mod) {
                const key = `${ev.caller}→${mod}`;
                newEdges[key] = now + EDGE_TTL;
              }
              // Heat: count calls
              if (!heatUpdates[mod]) heatUpdates[mod] = { calls: 0, deaths: 0 };
              heatUpdates[mod].calls++;
            }

            if (ev.event === 'return' && (ev.func === 'import_test' || ev.func === 'cascade')) {
              statusUpdates[mod] = 'alive';
            }
            if (ev.event === 'exception') {
              statusUpdates[mod] = 'dead';
              if (!heatUpdates[mod]) heatUpdates[mod] = { calls: 0, deaths: 0 };
              heatUpdates[mod].deaths++;
            }

            // Collect dead path signals (dead_import, unused_export, dead_edge)
            if (ev.status === 'dead' && (ev.func === 'dead_import' || ev.func === 'unused_export' || ev.func === 'dead_edge')) {
              if (!deadUpdates[mod]) deadUpdates[mod] = [];
              deadUpdates[mod].push(ev.detail || ev.func);
            }
          }

          if (Object.keys(newEdges).length) {
            setActiveEdges(prev => ({ ...prev, ...newEdges }));
          }
          if (Object.keys(newNodes).length) {
            setActiveNodes(prev => ({ ...prev, ...newNodes }));
          }

          // Update heat map (rolling)
          if (Object.keys(heatUpdates).length) {
            setNodeHeat(prev => {
              const next = { ...prev };
              for (const [mod, delta] of Object.entries(heatUpdates)) {
                const old = next[mod] || { calls: 0, deaths: 0, lastSeen: 0 };
                next[mod] = {
                  calls: old.calls + delta.calls,
                  deaths: old.deaths + delta.deaths,
                  lastSeen: now,
                };
              }
              return next;
            });
          }

          // Update test status
          if (Object.keys(statusUpdates).length) {
            setTestStatus(prev => ({ ...prev, ...statusUpdates }));
          }

          // Update dead paths
          if (Object.keys(deadUpdates).length) {
            setDeadPaths(prev => {
              const next = { ...prev };
              for (const [mod, details] of Object.entries(deadUpdates)) {
                next[mod] = [...(next[mod] || []), ...details];
              }
              return next;
            });
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

  return { connected, events, activeEdges, activeNodes, nodeHeat, testStatus, deadPaths, sendMessage, onRawMessageRef };
}
