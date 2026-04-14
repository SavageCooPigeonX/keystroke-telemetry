/* OrganismPulse — Live organism heartbeat and health */
import React, { useState, useEffect } from 'react';

function calculateHealth(graphData, liveEvents = []) {
  const nodes = graphData?.nodes || [];
  const totalNodes = nodes.length || 1;
  
  // Calculate various health metrics
  const avgEntropy = nodes.reduce((s, n) => s + (n.dual_score || 0), 0) / totalNodes;
  const totalDeaths = nodes.reduce((s, n) => s + (n.agent_deaths || 0), 0);
  const highEntropyCount = nodes.filter(n => (n.dual_score || 0) > 0.5).length;
  const buggyCount = nodes.filter(n => (n.bugs || []).length > 0).length;
  
  // Recent activity from live events
  const recentDeaths = liveEvents.filter(e => e.event === 'death' || e.event === 'error').length;
  const recentCalls = liveEvents.filter(e => e.event === 'call' || e.event === 'enter').length;
  
  // Health score: 100 - penalties
  let health = 100;
  health -= avgEntropy * 30; // entropy penalty
  health -= Math.min(30, totalDeaths * 2); // death penalty
  health -= Math.min(20, highEntropyCount * 3); // hot module penalty
  health -= Math.min(15, buggyCount * 2); // bug penalty
  health -= Math.min(10, recentDeaths * 5); // recent death penalty
  
  health = Math.max(0, Math.min(100, health));
  
  return {
    health: Math.round(health),
    avgEntropy: avgEntropy.toFixed(2),
    totalDeaths,
    highEntropyCount,
    buggyCount,
    recentCalls,
    recentDeaths,
  };
}

function getHealthColor(health) {
  if (health >= 80) return '#4ade80'; // green
  if (health >= 60) return '#facc15'; // yellow
  if (health >= 40) return '#fb923c'; // orange
  return '#f87171'; // red
}

function getHealthEmoji(health) {
  if (health >= 80) return '💚';
  if (health >= 60) return '💛';
  if (health >= 40) return '🧡';
  return '❤️‍🔥';
}

function getHealthStatus(health) {
  if (health >= 80) return 'thriving';
  if (health >= 60) return 'stable';
  if (health >= 40) return 'recovering';
  return 'critical';
}

export default function OrganismPulse({ graphData, liveEvents = [], connected = false, lastActive = null }) {
  const [pulse, setPulse] = useState(false);
  const [metrics, setMetrics] = useState(null);
  
  // Heartbeat animation
  useEffect(() => {
    const interval = setInterval(() => {
      setPulse(p => !p);
    }, connected ? 1000 : 2000); // faster when live
    return () => clearInterval(interval);
  }, [connected]);
  
  // Calculate health
  useEffect(() => {
    if (graphData) {
      setMetrics(calculateHealth(graphData, liveEvents));
    }
  }, [graphData, liveEvents]);
  
  if (!metrics) {
    return (
      <div className="organism-pulse loading">
        <div className="pulse-heart">🫀</div>
        <div className="pulse-text">Loading organism...</div>
      </div>
    );
  }
  
  const healthColor = getHealthColor(metrics.health);
  const healthEmoji = getHealthEmoji(metrics.health);
  const healthStatus = getHealthStatus(metrics.health);
  
  // Recent speaker from live events
  const lastSpeaker = liveEvents.length > 0 
    ? (liveEvents[liveEvents.length - 1].module || '').replace(/_seq\d+.*/, '')
    : null;
  
  return (
    <div className="organism-pulse">
      <div className="pulse-main">
        <div 
          className={`pulse-heart ${pulse ? 'pulse-beat' : ''}`}
          style={{ color: healthColor }}
        >
          {healthEmoji}
        </div>
        <div className="pulse-health">
          <span className="pulse-number" style={{ color: healthColor }}>
            {metrics.health}
          </span>
          <span className="pulse-label">/100</span>
        </div>
        <div className="pulse-status" style={{ color: healthColor }}>
          {healthStatus}
        </div>
      </div>
      
      <div className="pulse-metrics">
        <div className="pulse-metric">
          <span className="metric-icon">🌡️</span>
          <span className="metric-value">{metrics.avgEntropy}</span>
          <span className="metric-label">entropy</span>
        </div>
        <div className="pulse-metric">
          <span className="metric-icon">💀</span>
          <span className="metric-value">{metrics.totalDeaths}</span>
          <span className="metric-label">deaths</span>
        </div>
        <div className="pulse-metric">
          <span className="metric-icon">🔥</span>
          <span className="metric-value">{metrics.highEntropyCount}</span>
          <span className="metric-label">hot</span>
        </div>
        <div className="pulse-metric">
          <span className="metric-icon">🐛</span>
          <span className="metric-value">{metrics.buggyCount}</span>
          <span className="metric-label">buggy</span>
        </div>
      </div>
      
      <div className="pulse-live">
        <div className={`pulse-dot ${connected ? 'connected' : 'disconnected'}`} />
        <span className="pulse-live-text">
          {connected ? 'Live' : 'Offline'}
        </span>
        {lastSpeaker && connected && (
          <span className="pulse-last-speaker">
            last: {lastSpeaker}
          </span>
        )}
      </div>
    </div>
  );
}
