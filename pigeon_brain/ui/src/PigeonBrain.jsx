/* Pigeon Brain — main graph component */
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  ReactFlow, Background, Controls, MiniMap,
  useNodesState, useEdgesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import NodeNeuron from './NodeNeuron';
import RegionLabel from './RegionLabel';
import ObserverPanel from './ObserverPanel';
import ChatPanel from './ChatPanel';
import EntropyChart from './EntropyChart';
import SemanticMemory from './SemanticMemory';
import KeystrokeTelemetry from './KeystrokeTelemetry';
import ProfilePage from './ProfilePage';
import useLiveTrace from './useLiveTrace';
import './styles.css';

const nodeTypes = { neuron: NodeNeuron, regionLabel: RegionLabel };

/* Color scale: blue (safe) → yellow (warm) → red (danger) */
function heatColor(score) {
  if (score > 0.7) return '#ff2222';
  if (score > 0.4) return '#ff8800';
  if (score > 0.15) return '#ffcc00';
  return '#4488ff';
}

/* ── Brain Regions — each folder maps to a cortical area ── */
const REGIONS = {
  consciousness: { cx: 3000, cy: 350,  color: '#b388ff', name: 'Consciousness', icon: '🧠' },
  cortex:        { cx: 3000, cy: 1400, color: '#448aff', name: 'Cortex',        icon: '💎' },
  language:      { cx: 700,  cy: 800,  color: '#00e5ff', name: 'Language',      icon: '💬' },
  motor:         { cx: 5300, cy: 800,  color: '#ff6e40', name: 'Motor',         icon: '⚡' },
  stem:          { cx: 3000, cy: 2500, color: '#69f0ae', name: 'Stem',          icon: '🐦' },
  naming:        { cx: 500,  cy: 2200, color: '#ffab40', name: 'Naming',        icon: '🏷' },
  spatial:       { cx: 5500, cy: 2200, color: '#ff4081', name: 'Spatial',       icon: '✂' },
  analysis:      { cx: 4900, cy: 3300, color: '#ea80fc', name: 'Analysis',      icon: '🔍' },
  coordination:  { cx: 1100, cy: 3300, color: '#bcaaa4', name: 'Coordination',  icon: '🔄' },
  transport:     { cx: 3000, cy: 3800, color: '#80cbc4', name: 'Transport',     icon: '📡' },
};

function getRegion(path) {
  const folder = (path || '').replace(/\\/g, '/').split('/').slice(0, -1).join('/');
  if (folder.startsWith('src/cognitive_reactor')) return 'motor';
  if (folder.startsWith('src/copilot_prompt_manager')) return 'language';
  if (folder.startsWith('src/cognitive')) return 'consciousness';
  if (folder.startsWith('src')) return 'cortex';
  if (folder.startsWith('pigeon_brain')) return 'stem';
  if (folder.startsWith('pigeon_compiler/rename_engine')) return 'naming';
  if (folder.startsWith('pigeon_compiler/cut_executor')) return 'spatial';
  if (folder.startsWith('pigeon_compiler/state_extractor') ||
      folder.startsWith('pigeon_compiler/bones') ||
      folder.startsWith('pigeon_compiler/integrations') ||
      folder.startsWith('pigeon_compiler/weakness_planner')) return 'analysis';
  if (folder.startsWith('pigeon_compiler/runners')) return 'coordination';
  if (folder.startsWith('streaming_layer')) return 'transport';
  return 'cortex';
}

/* Phyllotaxis (sunflower spiral) — organic neural packing */
function phyllotaxis(count, cx, cy, scale) {
  const golden = Math.PI * (3 - Math.sqrt(5));
  const pts = [];
  for (let i = 0; i < count; i++) {
    const r = scale * Math.sqrt(i + 0.5);
    const theta = i * golden;
    pts.push({ x: cx + r * Math.cos(theta), y: cy + r * Math.sin(theta) });
  }
  return pts;
}

/* Size tiers — compact brain neurons */
function nodeDims(degree) {
  if (degree >= 8)  return { w: 155, h: 56 };
  if (degree >= 4)  return { w: 140, h: 50 };
  if (degree >= 2)  return { w: 125, h: 46 };
  if (degree >= 1)  return { w: 112, h: 42 };
  return { w: 100, h: 38 };
}

function buildLayout(graphData) {
  const rawNodes = graphData.nodes || [];
  const rawEdges = graphData.edges || [];

  /* Group nodes by brain region */
  const groups = {};
  for (const n of rawNodes) {
    const region = getRegion(n.path);
    if (!groups[region]) groups[region] = [];
    groups[region].push(n);
  }

  /* Sort within each region: highest importance first (center of spiral) */
  for (const regionNodes of Object.values(groups)) {
    regionNodes.sort((a, b) =>
      ((b.dual_score || 0) + ((b.in_degree || 0) + (b.out_degree || 0)) * 0.05)
      - ((a.dual_score || 0) + ((a.in_degree || 0) + (a.out_degree || 0)) * 0.05)
    );
  }

  /* Position nodes using phyllotaxis per region */
  const positions = {};
  const rfNodes = [];

  for (const [regionId, regionNodes] of Object.entries(groups)) {
    const def = REGIONS[regionId];
    if (!def) continue;

    const spacing = 38 + Math.sqrt(regionNodes.length) * 16;
    const pts = phyllotaxis(regionNodes.length, def.cx, def.cy, spacing);

    regionNodes.forEach((n, i) => {
      const deg = (n.in_degree || 0) + (n.out_degree || 0);
      const { w, h } = nodeDims(deg);
      positions[n.name] = { x: pts[i].x - w / 2, y: pts[i].y - h / 2 };
    });

    /* Region label floating above cluster */
    const minY = pts.length > 0 ? Math.min(...pts.map(p => p.y)) : def.cy;
    rfNodes.push({
      id: `region-${regionId}`,
      type: 'regionLabel',
      position: { x: def.cx - 90, y: minY - 60 },
      data: { name: def.name, icon: def.icon, color: def.color, count: regionNodes.length },
      selectable: false,
      draggable: false,
    });
  }

  /* Build React Flow neuron nodes */
  for (const n of rawNodes) {
    const region = getRegion(n.path);
    const def = REGIONS[region] || REGIONS.cortex;
    const deg = (n.in_degree || 0) + (n.out_degree || 0);
    const { w, h } = nodeDims(deg);
    const pos = positions[n.name] || { x: 0, y: 0 };

    rfNodes.push({
      id: n.name,
      type: 'neuron',
      position: pos,
      style: { width: w, height: h },
      data: {
        label: n.name,
        ver: n.ver,
        tokens: n.tokens,
        lines: n.lines || 0,
        desc: n.desc || '',
        personality: n.personality || 'unknown',
        dualScore: n.dual_score || 0,
        humanHes: n.human_hesitation || 0,
        agentDeaths: n.agent_deaths || 0,
        agentCalls: n.agent_calls || 0,
        agentLatency: n.agent_latency_ms || 0,
        agentLoops: n.agent_loops || 0,
        deathRate: n.death_rate || 0,
        lastCalled: n.last_called || null,
        deathCauses: n.death_causes || {},
        fears: n.fears || [],
        partners: n.partners || [],
        inDegree: n.in_degree || 0,
        outDegree: n.out_degree || 0,
        edgesOut: n.edges_out || [],
        edgesIn: n.edges_in || [],
        path: n.path || '',
        color: heatColor(n.dual_score || 0),
        region: region,
        regionColor: def.color,
        regionName: def.name,
        active: false,
        degree: deg,
        cardW: w,
        cardH: h,
      },
    });
  }

  /* Build edges — smoothstep for organic curves */
  const nodeIds = new Set(rfNodes.map(n => n.id));
  const nodeMap = {};
  for (const n of rawNodes) nodeMap[n.name] = n;

  const rfEdges = rawEdges
    .filter(e => nodeIds.has(e.from) && nodeIds.has(e.to))
    .map(e => {
      const fromRegion = getRegion((nodeMap[e.from] || {}).path || '');
      const toRegion = getRegion((nodeMap[e.to] || {}).path || '');
      const crossRegion = fromRegion !== toRegion;
      return {
        id: `e-${e.from}-${e.to}`,
        source: e.from,
        target: e.to,
        type: 'smoothstep',
        animated: false,
        style: {
          stroke: crossRegion ? '#333344' : (REGIONS[fromRegion]?.color || '#555') + '88',
          strokeWidth: crossRegion ? 1 : 1.5,
          opacity: crossRegion ? 0.12 : 0.3,
        },
      };
    });

  return { rfNodes, rfEdges };
}

export default function PigeonBrain() {
  const [graphData, setGraphData] = useState(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [narratives, setNarratives] = useState({});
  const [veinPulses, setVeinPulses] = useState({});  // edgeId -> { intensity, color, ts }
  const [cascadeStats, setCascadeStats] = useState({ errors: 0, debt: 0, tested: 0, cascades: 0 });
  const [viewMode, setViewMode] = useState('graph'); // 'graph' | 'profile'
  const [profileNode, setProfileNode] = useState(null); // full node data for profile view
  const graphRef = useRef({ adjList: {}, edgeIndex: {}, nodeNames: [] });
  const cascadeRef = useRef([]);  // active cascade chains
  const { connected, events, activeEdges, activeNodes, nodeHeat, testStatus, deadPaths, sendMessage, onRawMessageRef } = useLiveTrace();

  /* Handle chat responses from WS */
  useEffect(() => {
    onRawMessageRef.current = (data) => {
      if (data.type === 'chat_response' && data.text) {
        if (ChatPanel.onChatResponse) ChatPanel.onChatResponse(data.text, data.file_actions || null, data.ai_state || null);
      }
    };
  }, [onRawMessageRef]);

  /* Load narratives.json */
  useEffect(() => {
    fetch('/narratives.json')
      .then(r => r.json())
      .then(setNarratives)
      .catch(() => setNarratives({}));
  }, []);

  /* Load dual_view.json */
  useEffect(() => {
    fetch('/dual_view.json')
      .then(r => r.json())
      .then(data => {
        setGraphData(data);
        const { rfNodes, rfEdges } = buildLayout(data);
        setNodes(rfNodes);
        setEdges(rfEdges);
      })
      .catch(() => {
        fetch('../../dual_view.json')
          .then(r => r.json())
          .then(data => {
            setGraphData(data);
            const { rfNodes, rfEdges } = buildLayout(data);
            setNodes(rfNodes);
            setEdges(rfEdges);
          })
          .catch(console.error);
      });
  }, []);

  /* Update node active state + heat + test status + narrative + dead paths from live trace */
  useEffect(() => {
    if (!nodes.length) return;
    setNodes(nds =>
      nds.map(n => {
        const heat = nodeHeat[n.id] || { calls: 0, deaths: 0, lastSeen: 0 };
        const status = testStatus[n.id] || null;
        const narr = narratives[n.id] || null;
        const dp = deadPaths[n.id] || [];
        return {
          ...n,
          data: {
            ...n.data,
            active: !!activeNodes[n.id],
            liveHeat: heat,
            testStatus: status,
            narrative: narr,
            deadPaths: dp,
          },
        };
      })
    );
  }, [activeNodes, nodeHeat, testStatus, narratives, deadPaths]);

  /* Build adjacency list + edge index for cascade walking */
  useEffect(() => {
    if (!graphData) return;
    const adj = {};  // node -> [neighbor, ...]
    const idx = {};  // "src->tgt" -> edgeId
    const names = (graphData.nodes || []).map(n => n.name);
    for (const e of (graphData.edges || [])) {
      if (!adj[e.from]) adj[e.from] = [];
      if (!adj[e.to]) adj[e.to] = [];
      adj[e.from].push(e.to);
      adj[e.to].push(e.from);  // bidirectional walking
      idx[`${e.from}->${e.to}`] = `e-${e.from}-${e.to}`;
      idx[`${e.to}->${e.from}`] = `e-${e.from}-${e.to}`;
    }
    graphRef.current = { adjList: adj, edgeIndex: idx, nodeNames: names.filter(n => adj[n]) };
  }, [graphData]);

  /* Update edge styles — vein pulses + active trace edges */
  useEffect(() => {
    if (!edges.length) return;
    setEdges(eds =>
      eds.map(e => {
        const fwd = `${e.source}→${e.target}`;
        const rev = `${e.target}→${e.source}`;
        const isTraceActive = !!activeEdges[fwd] || !!activeEdges[rev];
        const pulse = veinPulses[e.id];

        if (isTraceActive) {
          const srcStatus = testStatus[e.source];
          const tgtStatus = testStatus[e.target];
          const edgeColor = (srcStatus === 'dead' || tgtStatus === 'dead')
            ? '#ff4444' : '#00ff88';
          return {
            ...e,
            animated: true,
            style: {
              stroke: edgeColor,
              strokeWidth: 4,
              opacity: 1,
              filter: `drop-shadow(0 0 8px ${edgeColor})`,
              transition: 'stroke 0.3s, opacity 0.3s, stroke-width 0.3s',
            },
          };
        }

        if (pulse && pulse.intensity > 0) {
          const c = pulse.color || '#00ff88';
          const w = 1.5 + pulse.intensity * 3.5;
          const op = 0.3 + pulse.intensity * 0.7;
          const glow = Math.round(pulse.intensity * 10);
          return {
            ...e,
            animated: true,
            style: {
              stroke: c,
              strokeWidth: w,
              opacity: op,
              filter: glow > 2 ? `drop-shadow(0 0 ${glow}px ${c})` : 'none',
              transition: 'stroke 0.4s, opacity 0.4s, stroke-width 0.4s',
            },
          };
        }

        // Default: subtle dim vein
        return {
          ...e,
          animated: false,
          style: { stroke: '#2a2a4e', strokeWidth: 1.5, opacity: 0.25, transition: 'stroke 0.6s, opacity 0.6s' },
        };
      })
    );
  }, [activeEdges, testStatus, veinPulses]);

  /* ── Touch-triggered vein cascades — tap node to test its paths ── */
  useEffect(() => {
    const PULSE_DURATION = 1400;    // ms per edge glow
    const STEP_INTERVAL = 200;      // ms between steps within a cascade

    const tick = () => {
      const { adjList, edgeIndex } = graphRef.current;
      const now = Date.now();
      const cascades = cascadeRef.current;
      if (!cascades.length) {
        // Nothing active — just decay lingering pulses
        setVeinPulses(prev => {
          const next = {};
          let any = false;
          for (const [id, p] of Object.entries(prev)) {
            const rem = 1 - (now - p.ts) / (p.duration || PULSE_DURATION);
            if (rem > 0.05) { next[id] = { ...p, intensity: rem * rem }; any = true; }
          }
          return any ? next : (Object.keys(prev).length ? {} : prev);
        });
        return;
      }

      const newPulses = {};
      const statsUpdate = { errors: 0, tested: 0, debt: 0 };
      const finished = [];

      for (let i = 0; i < cascades.length; i++) {
        const c = cascades[i];
        if (now - c.stepTs < STEP_INTERVAL) continue;

        const neighbors = (adjList[c.current] || []).filter(n => !c.visited.has(n));

        if (neighbors.length === 0 || c.depth >= c.maxDepth) {
          finished.push(i);
          statsUpdate.tested += c.visited.size;
          statsUpdate.errors += c.errors;
          continue;
        }

        const next = neighbors[Math.floor(Math.random() * neighbors.length)];
        const edgeId = edgeIndex[`${c.current}->${next}`];
        if (edgeId) {
          /* Use real dead-path data instead of random failure */
          const nextDead = (deadPaths[next] || []).length > 0;
          const isFail = nextDead || Math.random() < 0.04;
          newPulses[edgeId] = {
            intensity: 1,
            color: nextDead ? '#ff2222' : (isFail ? '#ff8800' : c.color),
            ts: now,
            duration: nextDead ? PULSE_DURATION * 1.5 : PULSE_DURATION,
          };
          if (isFail) {
            c.errors++;
            statsUpdate.debt += 0.1;
          }
        }

        c.visited.add(next);
        c.current = next;
        c.depth++;
        c.stepTs = now;
      }

      // Remove finished cascades (reverse order)
      for (let i = finished.length - 1; i >= 0; i--) {
        cascades.splice(finished[i], 1);
      }

      // Decay existing pulses + merge new
      setVeinPulses(prev => {
        const next = {};
        for (const [id, p] of Object.entries(prev)) {
          const rem = 1 - (now - p.ts) / (p.duration || PULSE_DURATION);
          if (rem > 0.05) next[id] = { ...p, intensity: rem * rem };
        }
        for (const [id, p] of Object.entries(newPulses)) next[id] = p;
        return next;
      });

      if (statsUpdate.tested > 0 || statsUpdate.errors > 0) {
        setCascadeStats(prev => ({
          errors: prev.errors + statsUpdate.errors,
          debt: Math.round((prev.debt + statsUpdate.debt) * 100) / 100,
          tested: prev.tested + statsUpdate.tested,
          cascades: prev.cascades + finished.length,
        }));
      }
    };

    const interval = setInterval(tick, 120);
    return () => clearInterval(interval);
  }, []);

  /* Spawn a cascade from a touched node + request real server tests */
  const spawnCascade = useCallback((nodeName) => {
    const { adjList } = graphRef.current;
    if (!adjList[nodeName]) return;  // isolated node, no connections
    const colors = ['#00ff88', '#4488ff', '#ff8800', '#aa44ff', '#00ccff', '#ff44aa'];
    cascadeRef.current.push({
      current: nodeName,
      visited: new Set([nodeName]),
      stepTs: Date.now(),
      depth: 0,
      maxDepth: 4 + Math.floor(Math.random() * 6),  // 4-9 hops — explore deep
      color: colors[Math.floor(Math.random() * colors.length)],
      errors: 0,
    });
    setCascadeStats(prev => ({ ...prev, cascades: prev.cascades + 1 }));
    // Ask Python backend to run real tests on this node
    sendMessage({ type: 'test_node', node: nodeName });
  }, [sendMessage]);

  const onNodeClick = useCallback((_, node) => {
    // Find full node data from graphData
    const fullNode = graphData?.nodes?.find(n => n.name === node.id);
    if (fullNode) {
      setProfileNode(fullNode);
      setViewMode('profile');
    }
    setSelectedNode(node.data);
    spawnCascade(node.id);  // touch → cascade + real test
  }, [graphData, spawnCascade]);

  /* Navigate to another profile (cross-linking) */
  const handleProfileNavigate = useCallback((targetNode) => {
    setProfileNode(targetNode);
    setSelectedNode(nodes.find(n => n.id === targetNode.name)?.data || null);
  }, [nodes]);

  /* Close profile and return to graph */
  const handleProfileClose = useCallback(() => {
    setViewMode('graph');
    setProfileNode(null);
  }, []);

  /* Event log for observer panel */
  const recentEvents = useMemo(() => events.slice(-30), [events]);

  /* Unified panel view state */
  const [activePanel, setActivePanel] = useState('observer'); // observer | entropy | memory

  /* Handle file click from entropy chart */
  const handleEntropyFileClick = useCallback((node) => {
    // Find the matching full node data and open profile
    const fullNode = graphData?.nodes?.find(n => 
      n.name === node.name || n.name?.includes(node.displayName)
    );
    if (fullNode) {
      setProfileNode(fullNode);
      setViewMode('profile');
    }
    const graphNode = nodes.find(n => n.id === node.name || n.data?.label?.includes(node.displayName));
    if (graphNode) {
      setSelectedNode(graphNode.data);
      spawnCascade(graphNode.id);
    }
  }, [graphData, nodes, spawnCascade]);

  if (!graphData) {
    return (
      <div className="loading">
        <h1>🐦🧠 Pigeon Brain</h1>
        <p>Loading graph... Run: <code>py -m pigeon_brain dual</code></p>
      </div>
    );
  }

  /* Profile View — Wikipedia-style page */
  if (viewMode === 'profile' && profileNode) {
    return (
      <div className="pigeon-brain unified">
        <div className="unified-topbar">
          <div className="topbar-title">
            <span className="topbar-icon">🐦🧠</span>
            <span className="topbar-text">Pigeon Brain Observatory</span>
          </div>
          <KeystrokeTelemetry />
          <div className={`live-indicator-inline ${connected ? 'live-on' : 'live-off'}`}>
            <span className="live-dot" />
            {connected ? 'LIVE' : 'OFFLINE'}
          </div>
        </div>
        <ProfilePage
          node={profileNode}
          graphData={graphData}
          narratives={narratives}
          onNavigate={handleProfileNavigate}
          onClose={handleProfileClose}
        />
      </div>
    );
  }

  return (
    <div className="pigeon-brain unified">
      {/* Top Bar — Keystroke Telemetry + Live Status */}
      <div className="unified-topbar">
        <div className="topbar-title">
          <span className="topbar-icon">🐦🧠</span>
          <span className="topbar-text">Pigeon Brain Observatory</span>
        </div>
        <KeystrokeTelemetry />
        <div className={`live-indicator-inline ${connected ? 'live-on' : 'live-off'}`}>
          <span className="live-dot" />
          {connected ? 'LIVE' : 'OFFLINE'}
        </div>
      </div>

      {/* Main Layout — Graph + Panels */}
      <div className="unified-main">
        <div className="graph-container">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
            minZoom={0.1}
            maxZoom={3}
          >
            <Background color="#1a1a2e" gap={20} />
            <Controls />
            <MiniMap
              nodeColor={n => n.data?.regionColor || n.data?.color || '#4488ff'}
              maskColor="rgba(0,0,0,0.8)"
            />
          </ReactFlow>
        </div>

        {/* Right Side — Tabbed Panel */}
        <div className="unified-sidebar">
          <div className="sidebar-tabs">
            <button 
              className={`sidebar-tab ${activePanel === 'observer' ? 'active' : ''}`}
              onClick={() => setActivePanel('observer')}
            >
              👁️ Observer
            </button>
            <button 
              className={`sidebar-tab ${activePanel === 'entropy' ? 'active' : ''}`}
              onClick={() => setActivePanel('entropy')}
            >
              🌡️ Entropy
            </button>
            <button 
              className={`sidebar-tab ${activePanel === 'memory' ? 'active' : ''}`}
              onClick={() => setActivePanel('memory')}
            >
              📚 Memory
            </button>
          </div>

          <div className="sidebar-content">
            {activePanel === 'observer' && (
              <ObserverPanel
                graphData={graphData}
                selectedNode={selectedNode}
                liveEvents={recentEvents}
                connected={connected}
                narratives={narratives}
                cascadeStats={cascadeStats}
                nodeHeat={nodeHeat}
              />
            )}
            {activePanel === 'entropy' && (
              <EntropyChart 
                graphData={graphData}
                onFileClick={handleEntropyFileClick}
              />
            )}
            {activePanel === 'memory' && (
              <SemanticMemory 
                selectedNode={selectedNode}
                graphData={graphData}
              />
            )}
          </div>
        </div>
      </div>

      {/* Chat Panel — Dormant until file clicked */}
      <ChatPanel
        sendMessage={sendMessage}
        selectedNode={selectedNode}
        connected={connected}
      />
    </div>
  );
}
