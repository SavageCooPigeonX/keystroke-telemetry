/* ObserverPanel — side panel showing failure patterns + selected node detail + live feed */
import React from 'react';

export default function ObserverPanel({ graphData, selectedNode, liveEvents = [], connected = false }) {
  if (!graphData) return null;

  const nodes = graphData.nodes || [];
  const dangerNodes = nodes.filter(n => n.dual_score > 0.3)
    .sort((a, b) => b.dual_score - a.dual_score)
    .slice(0, 8);

  const totalDeaths = nodes.reduce((s, n) => s + (n.agent_deaths || 0), 0);
  const dualHotspots = nodes.filter(n =>
    (n.human_hesitation || 0) > 0.3 && (n.agent_deaths || 0) > 0
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
        <h3>⚠️ Danger Zones</h3>
        {dangerNodes.map(n => (
          <div key={n.name} className="danger-item">
            <div className="danger-bar" style={{
              width: `${Math.min(100, n.dual_score * 100)}%`,
              background: n.dual_score > 0.6 ? '#ff2222' : '#ff8800',
            }} />
            <span className="danger-name">{n.name.replace(/_seq\d+.*/, '')}</span>
            <span className="danger-score">{n.dual_score.toFixed(3)}</span>
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
