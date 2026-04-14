/* FileSpeaks — Hot files speaking to operator */
import React, { useState, useEffect } from 'react';

function generateSpeech(node, narratives) {
  const name = node.name || node.label;
  const entropy = node.dual_score || 0;
  const deaths = node.agent_deaths || 0;
  const hes = node.human_hesitation || 0;
  const bugs = (node.bugs || []).length;
  const version = node.ver || 1;
  const narrative = narratives[name] || {};
  
  // Emotion based on state
  let emotion = '😐';
  let mood = 'neutral';
  if (entropy > 0.7) { emotion = '🔥'; mood = 'hot'; }
  else if (entropy > 0.4) { emotion = '😰'; mood = 'stressed'; }
  else if (deaths > 3) { emotion = '💀'; mood = 'dying'; }
  else if (hes > 0.5) { emotion = '😵'; mood = 'confused'; }
  else if (bugs > 0) { emotion = '🐛'; mood = 'buggy'; }
  else if (version === 1) { emotion = '🐣'; mood = 'new'; }
  else { emotion = '😌'; mood = 'chill'; }
  
  // Generate speech based on state
  const speeches = {
    hot: [
      `I'm running hot (${(entropy * 100).toFixed(0)}% entropy). You touched me but left uncertainty behind.`,
      `${(entropy * 100).toFixed(0)}% entropy. Need attention or I'll break something.`,
      `I'm overheating. ${deaths} deaths this cycle. What's the plan?`,
    ],
    stressed: [
      `Getting uncomfortable here. Entropy at ${(entropy * 100).toFixed(0)}%. Could use a refactor.`,
      `I'm stressed — ${deaths} failures and counting. Help?`,
    ],
    dying: [
      `${deaths} deaths. I'm not doing great. Something's fundamentally wrong with me.`,
      `I keep dying (${deaths}x). Maybe my design is broken?`,
    ],
    confused: [
      `You hesitate a lot when working with me (${(hes * 100).toFixed(0)}% hesitation). What's unclear?`,
      `I can tell you're unsure about me. Let's talk about what's confusing.`,
    ],
    buggy: [
      `I have ${bugs} bug${bugs > 1 ? 's' : ''} outstanding. When are we fixing this?`,
      `Still carrying ${bugs} bug${bugs > 1 ? 's' : ''} from before. Just saying.`,
    ],
    new: [
      `I'm v1 — fresh off the assembly line. What's my first test going to be?`,
      `Newborn module here. Expecting my first failure any minute now.`,
    ],
    neutral: [
      `All systems normal. Nothing to report.`,
      `I'm here when you need me.`,
      `Quiet day. ${version > 3 ? `Been around for ${version} versions.` : ''}`,
    ],
    chill: [
      `Everything's fine over here. No drama.`,
      `Just vibing. Low entropy, no deaths.`,
    ],
  };
  
  // Add narrative context if available
  let speech = speeches[mood][Math.floor(Math.random() * speeches[mood].length)];
  if (narrative.assumption) {
    speech += ` My assumption: ${narrative.assumption.slice(0, 100)}...`;
  }
  
  return { emotion, mood, speech, node };
}

export default function FileSpeaks({ nodes, narratives = {}, onFileClick, maxFiles = 6 }) {
  const [speakers, setSpeakers] = useState([]);
  
  useEffect(() => {
    if (!nodes || nodes.length === 0) return;
    
    // Score files by "need to speak" — high entropy, deaths, bugs, hesitation
    const scored = nodes.map(n => ({
      ...n,
      speakScore: (n.dual_score || 0) * 0.4 + 
                  ((n.agent_deaths || 0) / 10) * 0.3 +
                  (n.human_hesitation || 0) * 0.2 +
                  ((n.bugs || []).length / 5) * 0.1,
    }));
    
    // Top N files that need to speak
    const hot = scored
      .filter(n => n.speakScore > 0.1 || n.dual_score > 0.15)
      .sort((a, b) => b.speakScore - a.speakScore)
      .slice(0, maxFiles);
    
    const speeches = hot.map(n => generateSpeech(n, narratives));
    setSpeakers(speeches);
  }, [nodes, narratives, maxFiles]);
  
  if (speakers.length === 0) {
    return (
      <div className="file-speaks-panel empty">
        <div className="speaks-header">
          <span className="speaks-icon">💬</span>
          <span>File Conversations</span>
        </div>
        <div className="speaks-empty">
          All files quiet. No one needs to talk right now.
        </div>
      </div>
    );
  }
  
  return (
    <div className="file-speaks-panel">
      <div className="speaks-header">
        <span className="speaks-icon">🔥</span>
        <span>Hot Files Speaking</span>
        <span className="speaks-count">{speakers.length}</span>
      </div>
      <div className="speaks-list">
        {speakers.map(({ emotion, mood, speech, node }, i) => (
          <div 
            key={node.name || i} 
            className={`speech-bubble speech-${mood}`}
            onClick={() => onFileClick && onFileClick(node)}
          >
            <div className="speech-header">
              <span className="speech-emotion">{emotion}</span>
              <span className="speech-name">{(node.name || node.label || '').replace(/_seq\d+.*/, '')}</span>
              {node.ver > 1 && <span className="speech-ver">v{node.ver}</span>}
            </div>
            <div className="speech-text">{speech}</div>
            {node.fears && node.fears.length > 0 && (
              <div className="speech-fears">
                fears: {node.fears.slice(0, 2).join(', ')}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
