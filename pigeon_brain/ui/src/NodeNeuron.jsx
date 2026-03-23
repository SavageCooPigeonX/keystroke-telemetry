/* NodeNeuron — profiler card: mini manifest with stats like cProfile */
import React from 'react';
import { Handle, Position } from '@xyflow/react';

function severity(score) {
  if (score > 0.5) return 'critical';
  if (score > 0.3) return 'hot';
  if (score > 0.15) return 'warm';
  return 'safe';
}

function barWidth(val, max) {
  return `${Math.min(100, (val / Math.max(max, 1)) * 100)}%`;
}

export default function NodeNeuron({ data, selected }) {
  const {
    label, ver, tokens, dualScore, humanHes, agentDeaths,
    agentCalls, agentLoops, lines, desc, personality, lastCalled,
    active,
  } = data;

  const sev = severity(dualScore);
  const shortName = label.replace(/_seq\d+.*/, '');
  const shortDesc = (desc || '').replace(/_/g, ' ').slice(0, 40);
  const ago = lastCalled ? timeAgo(lastCalled) : '\u2014';

  return (
    <div className={`profiler-card sev-${sev} ${selected ? 'selected' : ''} ${active ? 'card-active' : ''}`}>
      <Handle type="target" position={Position.Left} className="card-handle" />
      <Handle type="source" position={Position.Right} className="card-handle" />

      <div className="card-header">
        <span className="card-name">{shortName}</span>
        <span className="card-ver">v{ver}</span>
      </div>

      {shortDesc && <div className="card-desc">{shortDesc}</div>}

      <div className="card-stats">
        <div className="stat-row">
          <span className="stat-key">tokens</span>
          <span className="stat-val">{tokens}</span>
        </div>
        <div className="stat-row">
          <span className="stat-key">lines</span>
          <span className="stat-val">{lines || '\u2014'}</span>
        </div>
        <div className="stat-row">
          <span className="stat-key">calls</span>
          <span className="stat-val">{agentCalls || 0}</span>
        </div>
        {agentDeaths > 0 && (
          <div className="stat-row stat-danger">
            <span className="stat-key">{'\u2620'} deaths</span>
            <span className="stat-val">{agentDeaths}</span>
          </div>
        )}
        {agentLoops > 0 && (
          <div className="stat-row stat-warn">
            <span className="stat-key">{'\u21BB'} loops</span>
            <span className="stat-val">{agentLoops}</span>
          </div>
        )}
      </div>

      <div className="card-bars">
        {humanHes > 0 && (
          <div className="bar-row">
            <span className="bar-label">hes</span>
            <div className="bar-track">
              <div className="bar-fill hes-bar" style={{ width: barWidth(humanHes, 1) }} />
            </div>
            <span className="bar-num">{humanHes.toFixed(2)}</span>
          </div>
        )}
        <div className="bar-row">
          <span className="bar-label">dual</span>
          <div className="bar-track">
            <div
              className={`bar-fill dual-bar sev-${sev}`}
              style={{ width: barWidth(dualScore, 1) }}
            />
          </div>
          <span className="bar-num">{dualScore.toFixed(2)}</span>
        </div>
      </div>

      <div className="card-footer">
        <span className="card-personality">{personality || 'unknown'}</span>
        <span className="card-last">{ago}</span>
      </div>
    </div>
  );
}

function timeAgo(isoStr) {
  try {
    const ms = Date.now() - new Date(isoStr).getTime();
    if (ms < 60_000) return `${Math.round(ms / 1000)}s ago`;
    if (ms < 3_600_000) return `${Math.round(ms / 60_000)}m ago`;
    if (ms < 86_400_000) return `${Math.round(ms / 3_600_000)}h ago`;
    return `${Math.round(ms / 86_400_000)}d ago`;
  } catch {
    return '\u2014';
  }
}
