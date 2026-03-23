/* Pigeon Brain — main graph component */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  ReactFlow, Background, Controls, MiniMap,
  useNodesState, useEdgesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import NodeNeuron from './NodeNeuron';
import ObserverPanel from './ObserverPanel';
import useLiveTrace from './useLiveTrace';
import './styles.css';

const nodeTypes = { neuron: NodeNeuron };

/* Color scale: blue (safe) → yellow (warm) → red (danger) */
function heatColor(score) {
  if (score > 0.7) return '#ff2222';
  if (score > 0.4) return '#ff8800';
  if (score > 0.15) return '#ffcc00';
  return '#4488ff';
}

/* Layout: grid-spiral — cards need more space than circles */
const CARD_W = 200;
const CARD_H = 160;

function layoutNodes(graphData) {
  const nodes = graphData.nodes || [];
  /* Sort: highest dual_score first */
  const sorted = [...nodes].sort((a, b) => (b.dual_score || 0) - (a.dual_score || 0));
  const COLS = Math.ceil(Math.sqrt(sorted.length * 1.5));
  const GAP_X = CARD_W + 40;
  const GAP_Y = CARD_H + 30;

  return sorted.map((n, i) => {
    const col = i % COLS;
    const row = Math.floor(i / COLS);

    return {
      id: n.name,
      type: 'neuron',
      position: { x: col * GAP_X, y: row * GAP_Y },
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
        active: false, // will be overridden by live trace
      },
    };
  });
}

function layoutEdges(graphData) {
  return (graphData.edges || []).map((e, i) => ({
    id: `e-${e.from}-${e.to}`,
    source: e.from,
    target: e.to,
    animated: false,
    style: { stroke: '#555', strokeWidth: 1.5, opacity: 0.3 },
  }));
}

export default function PigeonBrain() {
  const [graphData, setGraphData] = useState(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const { connected, events, activeEdges, activeNodes } = useLiveTrace();

  /* Load dual_view.json */
  useEffect(() => {
    fetch('/dual_view.json')
      .then(r => r.json())
      .then(data => {
        setGraphData(data);
        setNodes(layoutNodes(data));
        setEdges(layoutEdges(data));
      })
      .catch(() => {
        fetch('../../dual_view.json')
          .then(r => r.json())
          .then(data => {
            setGraphData(data);
            setNodes(layoutNodes(data));
            setEdges(layoutEdges(data));
          })
          .catch(console.error);
      });
  }, []);

  /* Update node active state from live trace */
  useEffect(() => {
    if (!nodes.length) return;
    setNodes(nds =>
      nds.map(n => ({
        ...n,
        data: {
          ...n.data,
          active: !!activeNodes[n.id],
        },
      }))
    );
  }, [activeNodes]);

  /* Update edge styles from live trace — active edges glow */
  useEffect(() => {
    if (!edges.length) return;
    setEdges(eds =>
      eds.map(e => {
        const fwd = `${e.source}→${e.target}`;
        const rev = `${e.target}→${e.source}`;
        const isActive = !!activeEdges[fwd] || !!activeEdges[rev];
        if (isActive) {
          return {
            ...e,
            animated: true,
            style: {
              stroke: '#00ff88',
              strokeWidth: 3,
              opacity: 1,
              filter: 'drop-shadow(0 0 6px #00ff88)',
              transition: 'stroke 0.3s, opacity 0.3s, stroke-width 0.3s',
            },
          };
        }
        return {
          ...e,
          animated: false,
          style: { stroke: '#555', strokeWidth: 1.5, opacity: 0.3, transition: 'stroke 0.5s, opacity 0.5s' },
        };
      })
    );
  }, [activeEdges]);

  const onNodeClick = useCallback((_, node) => {
    setSelectedNode(node.data);
  }, []);

  /* Event log for observer panel */
  const recentEvents = useMemo(() => events.slice(-30), [events]);

  if (!graphData) {
    return (
      <div className="loading">
        <h1>🐦🧠 Pigeon Brain</h1>
        <p>Loading graph... Run: <code>py -m pigeon_brain dual</code></p>
      </div>
    );
  }

  return (
    <div className="pigeon-brain">
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
            nodeColor={n => n.data?.color || '#4488ff'}
            maskColor="rgba(0,0,0,0.8)"
          />
        </ReactFlow>
        {/* Connection status indicator */}
        <div className={`live-indicator ${connected ? 'live-on' : 'live-off'}`}>
          <span className="live-dot" />
          {connected ? 'LIVE' : 'OFFLINE'}
        </div>
      </div>
      <ObserverPanel
        graphData={graphData}
        selectedNode={selectedNode}
        liveEvents={recentEvents}
        connected={connected}
      />
    </div>
  );
}
