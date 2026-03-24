/* ObserverPanel — side panel showing failure patterns + selected node detail + live feed */
import React from 'react';

export default function ObserverPanel({ graphData, selectedNode, liveEvents = [], connected = false, narratives = {}, cascadeStats = {}, nodeHeat = {} }) {
  if (!graphData) return null;

  const nodes = graphData.nodes || [];

  // Blend static dual_score with live heat (deaths/calls ratio)
  const scoredNodes = nodes.map(n => {
    const heat = nodeHeat[n.name] || { calls: 0, deaths: 0 };
    const liveRisk = heat.calls > 0 ? heat.deaths / heat.calls : 0;
    const liveCalls = Math.min(1, heat.calls / 50); // normalize call volume
    const blended = (n.dual_score || 0) * 0.6 + liveRisk * 0.25 + liveCalls * 0.15;
    return { ...n, live_score: blended, live_calls: heat.calls, live_deaths: heat.deaths };
  });

  const dangerNodes = scoredNodes.filter(n => n.live_score >= 0.15 || n.dual_score >= 0.15)
    .sort((a, b) => b.live_score - a.live_score)
    .slice(0, 12);

  const totalDeaths = nodes.reduce((s, n) => s + (n.agent_deaths || 0), 0)
    + Object.values(nodeHeat).reduce((s, h) => s + (h.deaths || 0), 0);
  const dualHotspots = scoredNodes.filter(n =>
    ((n.human_hesitation || 0) > 0.3 && (n.agent_deaths || 0) > 0)
    || (n.live_deaths > 0 && n.live_calls > 3)
  );

  return (
    <div className="observer-panel">
      <h2>🐦🧠 Pigeon Brain</h2>
      <div className="stats-row">
        <div className="stat">
          <span className="stat-num">{graphData.total_nodes}</span>
          <span className="stat-label">neurons</span>
        </div>
        <div className="stat">
          <span className="stat-num">{(graphData.edges || []).length}</span>
          <span className="stat-label">synapses</span>
        </div>
        <div className="stat">
          <span className="stat-num">{totalDeaths}</span>
          <span className="stat-label">deaths</span>
        </div>
      </div>

      {/* Live trace feed */}
      <div className="section live-feed">
        <h3>
          <span className={`feed-dot ${connected ? 'feed-on' : 'feed-off'}`} />
          {connected ? 'Live Trace' : 'Trace Offline'}
        </h3>
        {connected && liveEvents.length > 0 ? (
          <div className="feed-scroll">
            {liveEvents.slice(-15).reverse().map((ev, i) => (
              <div key={ev.seq || i} className={`feed-event feed-${ev.event}`}>
                <span className="feed-ts">
                  {new Date(ev.ts).toLocaleTimeString('en', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </span>
                <span className="feed-type">{ev.event}</span>
                <span className="feed-mod">{(ev.module || '').replace(/_seq\d+.*/, '')}</span>
                <span className="feed-func">{ev.func}</span>
                {ev.caller && ev.caller !== ev.module && (
                  <span className="feed-arrow">← {(ev.caller || '').replace(/_seq\d+.*/, '')}</span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="feed-empty">
            {connected ? 'Waiting for events...' : 'Run: py -m pigeon_brain live'}
          </div>
        )}
      </div>

      {/* Vein cascade stats */}
      <div className="section cascade-stats">
        <h3>🩸 Vein Cascade</h3>
        <div className="stats-row">
          <div className="stat">
            <span className="stat-num" style={{color: '#00ff88'}}>{cascadeStats.cascades || 0}</span>
            <span className="stat-label">cascades</span>
          </div>
          <div className="stat">
            <span className="stat-num" style={{color: '#4488ff'}}>{cascadeStats.tested || 0}</span>
            <span className="stat-label">tested</span>
          </div>
          <div className="stat">
            <span className="stat-num" style={{color: cascadeStats.errors > 0 ? '#ff4444' : '#888'}}>{cascadeStats.errors || 0}</span>
            <span className="stat-label">errors</span>
          </div>
          <div className="stat">
            <span className="stat-num" style={{color: cascadeStats.debt > 1 ? '#ff8800' : '#888'}}>{cascadeStats.debt?.toFixed(1) || '0.0'}</span>
            <span className="stat-label">cog debt</span>
          </div>
        </div>
      </div>

      {dualHotspots.length > 0 && (
        <div className="section dual-hotspots">
          <h3>🔴 Dual-Substrate Hotspots</h3>
          <p className="section-desc">
            These neurons kill BOTH human thoughts AND agent electrons.
          </p>
          {dualHotspots.map(n => (
            <div key={n.name} className="hotspot-item">
              <span className="hotspot-name">{n.name.replace(/_seq\d+.*/, '')}</span>
              <span className="hotspot-detail">
                🧠 {n.human_hesitation.toFixed(2)} · 💀 {n.agent_deaths}
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="section danger-zones">
        <h3>⚠️ Danger Zones {connected && <span style={{fontSize:'0.6em',color:'#0f0'}}>LIVE</span>}</h3>
        {dangerNodes.length === 0 && <div className="feed-empty">All clear</div>}
        {dangerNodes.map(n => (
          <div key={n.name} className="danger-item">
            <div className="danger-bar" style={{
              width: `${Math.min(100, n.live_score * 130)}%`,
              background: n.live_score > 0.5 ? '#ff2222' : n.live_score > 0.3 ? '#ff8800' : '#cc6600',
            }} />
            <span className="danger-name">{n.name.replace(/_seq\d+.*/, '')}</span>
            <span className="danger-score">{n.live_score.toFixed(3)}</span>
            {n.live_calls > 0 && (
              <span className="danger-live" style={{fontSize:'0.7em',color:'#888',marginLeft:4}}>
                {n.live_calls}c{n.live_deaths > 0 ? ` ${n.live_deaths}💀` : ''}
              </span>
            )}
          </div>
        ))}
      </div>

      {selectedNode && (
        <div className="section selected-node">
          <h3>{selectedNode.label.replace(/_seq\d+.*/, '')}</h3>
          {selectedNode.desc && (
            <div className="profile-desc">{selectedNode.desc.replace(/_/g, ' ')}</div>
          )}
          {selectedNode.path && (
            <div className="profile-path">{selectedNode.path}</div>
          )}
          {/* Push narrative — semantic self-description */}
          {narratives[selectedNode.label] && (
            <div className="profile-narrative">
              <div className="profile-section-head">NARRATIVE</div>
              <p className="narrative-text">{narratives[selectedNode.label].text}</p>
              <span className="narrative-commit">
                {narratives[selectedNode.label].intent} · {narratives[selectedNode.label].date} · {narratives[selectedNode.label].commit}
              </span>
            </div>
          )}
          <table className="profile-table">
            <tbody>
              <tr><td>version</td><td className="pv">v{selectedNode.ver}</td></tr>
              <tr><td>tokens</td><td className="pv">{selectedNode.tokens}</td></tr>
              <tr><td>lines</td><td className="pv">{selectedNode.lines || '\u2014'}</td></tr>
              <tr><td>personality</td><td className="pv">{selectedNode.personality || 'unknown'}</td></tr>
              <tr className="sep"><td colSpan={2}>HUMAN SUBSTRATE</td></tr>
              <tr><td>hesitation</td><td className="pv">{selectedNode.humanHes?.toFixed(3)}</td></tr>
              <tr className="sep"><td colSpan={2}>AGENT SUBSTRATE</td></tr>
              <tr><td>calls</td><td className="pv">{selectedNode.agentCalls || 0}</td></tr>
              <tr><td>deaths</td><td className={`pv ${selectedNode.agentDeaths > 0 ? 'val-danger' : ''}`}>{selectedNode.agentDeaths || 0}</td></tr>
              <tr><td>death rate</td><td className="pv">{selectedNode.deathRate?.toFixed(3) || '0.000'}</td></tr>
              <tr><td>loops</td><td className="pv">{selectedNode.agentLoops || 0}</td></tr>
              <tr><td>latency</td><td className="pv">{selectedNode.agentLatency || 0} ms</td></tr>
              <tr><td>last called</td><td className="pv">{selectedNode.lastCalled || '\u2014'}</td></tr>
              <tr className="sep"><td colSpan={2}>GRAPH</td></tr>
              <tr><td>in-degree</td><td className="pv">{selectedNode.inDegree || 0}</td></tr>
              <tr><td>out-degree</td><td className="pv">{selectedNode.outDegree || 0}</td></tr>
              <tr><td>dual score</td><td className={`pv ${selectedNode.dualScore > 0.3 ? 'val-danger' : ''}`}>{selectedNode.dualScore?.toFixed(3)}</td></tr>
            </tbody>
          </table>
          {selectedNode.fears?.length > 0 && (
            <div className="profile-section">
              <div className="profile-section-head">FEARS</div>
              {selectedNode.fears.map((f, i) => <div key={i} className="fear-item">{f}</div>)}
            </div>
          )}
          {selectedNode.partners?.length > 0 && (
            <div className="profile-section">
              <div className="profile-section-head">COUPLED TO</div>
              {selectedNode.partners.map((p, i) => <div key={i} className="partner-item">{p}</div>)}
            </div>
          )}
          {selectedNode.deathCauses && Object.keys(selectedNode.deathCauses).length > 0 && (
            <div className="profile-section">
              <div className="profile-section-head">DEATH CAUSES</div>
              {Object.entries(selectedNode.deathCauses).map(([cause, count]) => (
                <div key={cause} className="death-cause-item">
                  <span>{cause}</span><span className="val-danger">{count}</span>
                </div>
              ))}
            </div>
          )}
          {selectedNode.edgesIn?.length > 0 && (
            <div className="profile-section">
              <div className="profile-section-head">IMPORTED BY ({selectedNode.edgesIn.length})</div>
              {selectedNode.edgesIn.slice(0, 5).map((e, i) => <div key={i} className="edge-item">{e}</div>)}
            </div>
          )}
          {selectedNode.edgesOut?.length > 0 && (
            <div className="profile-section">
              <div className="profile-section-head">IMPORTS ({selectedNode.edgesOut.length})</div>
              {selectedNode.edgesOut.slice(0, 5).map((e, i) => <div key={i} className="edge-item">{e}</div>)}
            </div>
          )}
        </div>
      )}

      <div className="section legend">
        <h3>Legend</h3>
        <div className="legend-item">
          <span className="dot" style={{background: '#4488ff'}} /> Safe
        </div>
        <div className="legend-item">
          <span className="dot" style={{background: '#ffcc00'}} /> Warm
        </div>
        <div className="legend-item">
          <span className="dot" style={{background: '#ff8800'}} /> Hot
        </div>
        <div className="legend-item">
          <span className="dot" style={{background: '#ff2222'}} /> Critical
        </div>
        <div className="legend-item">
          <span className="dot" style={{background: '#00ff88'}} /> ⚡ Electron
        </div>
      </div>
    </div>
  );
}
