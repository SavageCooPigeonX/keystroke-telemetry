/* KeystrokeTelemetry — Live operator state from keystroke signals */
import React, { useState, useEffect } from 'react';

const STATE_CONFIG = {
  frustrated: { icon: '🔴', color: '#f85149', label: 'frustrated' },
  hesitant:   { icon: '🟡', color: '#d29922', label: 'hesitant' },
  flow:       { icon: '🟢', color: '#3fb950', label: 'flow' },
  focused:    { icon: '🔵', color: '#58a6ff', label: 'focused' },
  restructuring: { icon: '🟠', color: '#ff7b00', label: 'restructuring' },
  abandoned:  { icon: '⚫', color: '#8b949e', label: 'abandoned' },
  neutral:    { icon: '⬤', color: '#6e7681', label: 'neutral' },
};

export default function KeystrokeTelemetry() {
  const [telemetry, setTelemetry] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadTelemetry = () => {
      fetch('/prompt_telemetry.json')
        .then(r => r.json())
        .then(data => {
          setTelemetry(data);
          setLoading(false);
        })
        .catch(() => {
          // Try alternative path
          fetch('/logs/prompt_telemetry_latest.json')
            .then(r => r.json())
            .then(data => {
              setTelemetry(data);
              setLoading(false);
            })
            .catch(() => setLoading(false));
        });
    };
    
    loadTelemetry();
    const interval = setInterval(loadTelemetry, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, []);
  
  if (loading) {
    return (
      <div className="keystroke-telemetry loading">
        <span>Loading telemetry...</span>
      </div>
    );
  }
  
  if (!telemetry) {
    return (
      <div className="keystroke-telemetry offline">
        <span className="kt-icon">📡</span>
        <span>Telemetry offline</span>
      </div>
    );
  }
  
  const state = telemetry.latest_prompt?.state || 'neutral';
  const stateConfig = STATE_CONFIG[state] || STATE_CONFIG.neutral;
  const wpm = telemetry.signals?.wpm?.toFixed(0) || '—';
  const delRatio = ((telemetry.signals?.deletion_ratio || 0) * 100).toFixed(0);
  const hesCount = telemetry.signals?.hesitation_count || 0;
  const deletedWords = telemetry.deleted_words || [];
  const rewrites = telemetry.rewrites || [];
  
  return (
    <div className="keystroke-telemetry">
      <div className="kt-header">
        <span 
          className="kt-state-dot" 
          style={{ color: stateConfig.color }}
        >
          {stateConfig.icon}
        </span>
        <span className="kt-state-label" style={{ color: stateConfig.color }}>
          {stateConfig.label}
        </span>
        <span className="kt-live-indicator">LIVE</span>
      </div>
      
      <div className="kt-metrics">
        <div className="kt-metric">
          <span className="kt-metric-val">{wpm}</span>
          <span className="kt-metric-label">wpm</span>
        </div>
        <div className="kt-metric">
          <span className="kt-metric-val">{delRatio}%</span>
          <span className="kt-metric-label">del</span>
        </div>
        <div className="kt-metric">
          <span className="kt-metric-val">{hesCount}</span>
          <span className="kt-metric-label">hes</span>
        </div>
      </div>
      
      {deletedWords.length > 0 && (
        <div className="kt-deleted">
          <span className="kt-deleted-label">🗑️ deleted:</span>
          <span className="kt-deleted-words">
            {deletedWords.slice(0, 5).join(', ')}
          </span>
        </div>
      )}
      
      {rewrites.length > 0 && (
        <div className="kt-rewrites">
          <span className="kt-rewrites-label">✏️ rewrites:</span>
          {rewrites.slice(0, 2).map((r, i) => (
            <div key={i} className="kt-rewrite">
              <span className="kt-rewrite-old">{r.old?.slice(0, 20)}</span>
              <span className="kt-rewrite-arrow">→</span>
              <span className="kt-rewrite-new">{r.new?.slice(0, 20)}</span>
            </div>
          ))}
        </div>
      )}
      
      {telemetry.running_summary && (
        <div className="kt-summary">
          <span className="kt-summary-label">session:</span>
          <span className="kt-summary-val">
            {telemetry.running_summary.total_prompts} prompts
          </span>
        </div>
      )}
    </div>
  );
}
