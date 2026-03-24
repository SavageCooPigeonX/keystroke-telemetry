/* NodeNeuron — compact brain cell with region color + heat glow */
import React from 'react';
import { Handle, Position } from '@xyflow/react';

function severity(score) {
  if (score > 0.5) return 'critical';
  if (score > 0.3) return 'hot';
  if (score > 0.15) return 'warm';
  return 'safe';
}

export default function NodeNeuron({ data, selected }) {
  const {
    label, ver, dualScore, agentDeaths, agentCalls,
    active, degree, cardW, liveHeat, testStatus,
    regionColor, tokens,
  } = data;

  const sev = severity(dualScore);
  const shortName = label.replace(/_seq\d+.*/, '');
  const isHub = (degree || 0) >= 8;

  const heat = liveHeat || { calls: 0, deaths: 0, lastSeen: 0 };
  const heatIntensity = Math.min(1, heat.calls / 20);
  const isAlive = testStatus === 'alive';
  const isDead = testStatus === 'dead';
  const narrative = data.narrative;
  const deadPaths = data.deadPaths || [];

  /* Permanent growth from LLM touches (ver) + live heat */
  const verGrowth = Math.min(0.18, ((ver || 1) - 1) * 0.012);
  const heatGrowth = Math.min(0.14, heat.calls * 0.005);
  const growthScale = 1 + verGrowth + heatGrowth;

  /* Dynamic glow */
  let glowStyle = {};
  if (isDead) {
    glowStyle = {
      borderColor: '#ff2222',
      boxShadow: `0 0 ${8 + heatIntensity * 12}px rgba(255,34,34,${0.3 + heatIntensity * 0.4})`,
    };
  } else if (active) {
    glowStyle = {
      borderColor: '#00ff88',
      boxShadow: `0 0 ${8 + heatIntensity * 14}px rgba(0,255,136,${0.3 + heatIntensity * 0.5})`,
    };
  } else if (isAlive && heatIntensity > 0.1) {
    glowStyle = {
      borderColor: `rgba(0,255,136,${0.3 + heatIntensity * 0.5})`,
      boxShadow: `0 0 ${4 + heatIntensity * 8}px rgba(0,255,136,${0.1 + heatIntensity * 0.2})`,
    };
  }

  return (
    <div
      className={`neuron-cell sev-${sev} ${selected ? 'selected' : ''} ${active ? 'cell-active' : ''} ${isHub ? 'cell-hub' : ''} ${isDead ? 'cell-dead' : ''}`}
      style={{
        borderLeftColor: regionColor || '#448aff',
        transform: `scale(${growthScale})`,
        transformOrigin: 'center center',
        transition: 'transform 1.2s ease-out, box-shadow 0.3s',
        ...glowStyle,
      }}
    >
      {active && <div className="ping-ring ping-ring-1" />}
      {active && <div className="ping-ring ping-ring-2" />}

      <Handle type="target" position={Position.Left} className="cell-handle" />
      <Handle type="source" position={Position.Right} className="cell-handle" />

      <div className="cell-top">
        {testStatus && (
          <span className={`cell-dot ${isDead ? 'dot-dead' : 'dot-alive'}`} />
        )}
        <span className="cell-name" title={label}>{shortName}</span>
      </div>

      <div className="cell-meta">
        <span className="cell-ver">v{ver}</span>
        {dualScore > 0.1 && <span className={`cell-score sev-${sev}`}>{dualScore.toFixed(2)}</span>}
        {heat.calls > 0 && <span className="cell-heat">{heat.calls}⚡</span>}
        {agentDeaths > 0 && <span className="cell-deaths">{agentDeaths}☠</span>}
        {isHub && <span className="cell-degree">{degree}↔</span>}
      </div>

      {/* Tiny heat bar at bottom */}
      {dualScore > 0 && (
        <div className="cell-bar-track">
          <div className={`cell-bar-fill sev-${sev}`} style={{ width: `${Math.min(100, dualScore * 100)}%` }} />
        </div>
      )}

      {/* Narrative note from push narratives */}
      {narrative && (
        <div className="cell-narrative" title={narrative.text}>
          {narrative.intent && <span className="cell-narr-tag">{narrative.intent}</span>}
        </div>
      )}

      {/* Dead paths detected by vein tests */}
      {deadPaths.length > 0 && (
        <div className="cell-dead-paths" title={deadPaths.join(', ')}>
          ✂{deadPaths.length}
        </div>
      )}
    </div>
  );
}
