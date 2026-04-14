/* EntropyChart — Module entropy visualization */
import React, { useState, useEffect, useMemo } from 'react';

function getEntropyColor(entropy) {
  if (entropy > 0.7) return '#f85149';  // critical
  if (entropy > 0.4) return '#d29922';  // warning
  if (entropy > 0.15) return '#58a6ff'; // warm
  return '#3fb950';                     // safe
}

export default function EntropyChart({ graphData, onFileClick }) {
  const [filter, setFilter] = useState('');
  const [sortBy, setSortBy] = useState('entropy');
  const [selected, setSelected] = useState(null);

  const sortedNodes = useMemo(() => {
    if (!graphData?.nodes) return [];
    
    let nodes = graphData.nodes.map(n => ({
      ...n,
      entropy: n.dual_score || 0,
      deaths: n.agent_deaths || 0,
      hes: n.human_hesitation || 0,
      bugs: (n.bugs || []).length,
      displayName: (n.name || '').replace(/_seq\d+.*/, ''),
    }));
    
    // Filter
    if (filter) {
      const q = filter.toLowerCase();
      nodes = nodes.filter(n => n.displayName.toLowerCase().includes(q));
    }
    
    // Sort
    nodes.sort((a, b) => {
      if (sortBy === 'entropy') return b.entropy - a.entropy;
      if (sortBy === 'deaths') return b.deaths - a.deaths;
      if (sortBy === 'name') return a.displayName.localeCompare(b.displayName);
      return b.entropy - a.entropy;
    });
    
    return nodes.slice(0, 50); // Top 50
  }, [graphData, filter, sortBy]);

  const globalStats = useMemo(() => {
    if (!graphData?.nodes) return { avg: 0, hot: 0, total: 0, deaths: 0 };
    const nodes = graphData.nodes;
    const avg = nodes.reduce((s, n) => s + (n.dual_score || 0), 0) / nodes.length;
    const hot = nodes.filter(n => (n.dual_score || 0) > 0.5).length;
    const deaths = nodes.reduce((s, n) => s + (n.agent_deaths || 0), 0);
    return { avg: avg.toFixed(2), hot, total: nodes.length, deaths };
  }, [graphData]);

  const handleClick = (node) => {
    setSelected(node.name);
    if (onFileClick) onFileClick(node);
  };

  return (
    <div className="entropy-chart">
      <div className="entropy-header">
        <span className="entropy-title">🌡️ Entropy Map</span>
      </div>
      
      <div className="entropy-stats">
        <div className="e-stat">
          <span className="e-stat-val">{globalStats.avg}</span>
          <span className="e-stat-label">avg</span>
        </div>
        <div className="e-stat">
          <span className="e-stat-val" style={{ color: '#f85149' }}>{globalStats.hot}</span>
          <span className="e-stat-label">hot</span>
        </div>
        <div className="e-stat">
          <span className="e-stat-val">{globalStats.total}</span>
          <span className="e-stat-label">total</span>
        </div>
        <div className="e-stat">
          <span className="e-stat-val">{globalStats.deaths}</span>
          <span className="e-stat-label">deaths</span>
        </div>
      </div>
      
      <div className="entropy-filters">
        <input
          type="text"
          placeholder="filter..."
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="e-filter-input"
        />
        <select value={sortBy} onChange={e => setSortBy(e.target.value)} className="e-filter-select">
          <option value="entropy">by entropy</option>
          <option value="deaths">by deaths</option>
          <option value="name">by name</option>
        </select>
      </div>
      
      <div className="entropy-bars">
        {sortedNodes.map(n => (
          <div 
            key={n.name} 
            className={`e-bar-row ${selected === n.name ? 'selected' : ''}`}
            onClick={() => handleClick(n)}
          >
            <span className="e-bar-name">{n.displayName}</span>
            <div className="e-bar-container">
              <div 
                className="e-bar-fill" 
                style={{ 
                  width: `${Math.max(2, n.entropy * 100)}%`,
                  background: getEntropyColor(n.entropy),
                }}
              >
                <span className="e-bar-label">{(n.entropy * 100).toFixed(0)}%</span>
              </div>
            </div>
            <div className="e-bar-badges">
              {n.bugs > 0 && <span className="e-badge bug">🐛{n.bugs}</span>}
              {n.deaths > 0 && <span className="e-badge death">💀{n.deaths}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
