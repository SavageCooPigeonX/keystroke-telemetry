/* ChatPanel — Gemini-powered project assistant embedded in Pigeon Brain */
import React, { useState, useRef, useEffect } from 'react';

/* Generate probe questions based on file state - vibe coder aware */
function generateProbeQuestions(node) {
  if (!node) return [];
  const name = (node.label || node.name || '').replace(/_seq\d+.*/, '');
  const entropy = node.dualScore || node.dual_score || 0;
  const deaths = node.agentDeaths || node.agent_deaths || 0;
  const hes = node.humanHes || node.human_hesitation || 0;
  const bugs = (node.bugs || []).length;
  const ver = node.ver || 1;
  const fears = node.fears || [];
  
  const probes = [];
  
  // Always start with personality-driven greeting
  if (entropy > 0.5) {
    probes.push(`yo - i'm running hot (${(entropy * 100).toFixed(0)}% entropy). what's the vibe - fixing me or just browsing?`);
  } else if (deaths > 2) {
    probes.push(`${deaths} deaths and counting. you here to help or just watch me suffer?`);
  } else if (bugs > 0) {
    probes.push(`got ${bugs} bug${bugs > 1 ? 's' : ''} in my system. you feeling like debugging today?`);
  } else if (ver === 1) {
    probes.push(`fresh spawn - v1. everyone expects me to break. what's your prediction?`);
  } else {
    probes.push(`sup. ${name} here. what brings you to my code?`);
  }
  
  // Add context-aware follow-ups
  if (hes > 0.4) {
    probes.push(`i notice you hesitate around me (${(hes * 100).toFixed(0)}% of the time). what's confusing?`);
  }
  if (fears.length > 0) {
    probes.push(`my fears: ${fears.slice(0, 2).join(', ')}. any of these actually biting you?`);
  }
  if (entropy > 0.3 && deaths > 0) {
    probes.push(`real talk - should i be refactored or am i still useful as-is?`);
  }
  
  return probes;
}

export default function ChatPanel({ sendMessage, selectedNode, connected }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [aiState, setAiState] = useState(null);
  const [lastProbed, setLastProbed] = useState(null); // track which file we probed
  const scrollRef = useRef(null);
  const inputRef = useRef(null);
  const wsHandlerRef = useRef(null);

  /* Auto-scroll to bottom on new messages */
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  /* Focus input when opened */
  useEffect(() => {
    if (open && inputRef.current) inputRef.current.focus();
  }, [open]);

  /* FILE WAKE-UP: When a new file is selected, it probes the operator */
  useEffect(() => {
    if (!selectedNode) return;
    const nodeName = selectedNode.label || selectedNode.name;
    if (!nodeName || nodeName === lastProbed) return;
    
    // File wakes up - generate probe questions
    const probes = generateProbeQuestions(selectedNode);
    if (probes.length === 0) return;
    
    // Open chat and add file's probe as a system message
    setOpen(true);
    setLastProbed(nodeName);
    
    const name = nodeName.replace(/_seq\d+.*/, '');
    const ver = selectedNode.ver || 1;
    const entropy = selectedNode.dualScore || selectedNode.dual_score || 0;
    
    // Determine emotion based on state
    let emotion = '🔵';
    if (entropy > 0.6) emotion = '🔥';
    else if (entropy > 0.3) emotion = '😤';
    else if ((selectedNode.agentDeaths || 0) > 2) emotion = '💀';
    else if ((selectedNode.bugs || []).length > 0) emotion = '🐛';
    else if (ver === 1) emotion = '🐣';
    else emotion = '😎';
    
    // Add file's probe message
    setMessages(prev => [
      ...prev,
      {
        role: 'file',
        speaker: name,
        emotion,
        text: probes.join('\n\n'),
        probes: probes.slice(1), // additional probes for UI
      }
    ]);
  }, [selectedNode, lastProbed]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || loading || !connected) return;

    setMessages(prev => [...prev, { role: 'user', text }]);
    setInput('');
    setLoading(true);

    sendMessage({
      type: 'chat',
      message: text,
      selectedNode: selectedNode ? {
        name: selectedNode.label,
        ver: selectedNode.ver,
        tokens: selectedNode.tokens,
        desc: selectedNode.desc,
        path: selectedNode.path,
        dual_score: selectedNode.dualScore,
        human_hesitation: selectedNode.humanHes,
        agent_deaths: selectedNode.agentDeaths,
        fears: selectedNode.fears,
        partners: selectedNode.partners,
      } : null,
    });
  };

  const handleClear = () => {
    setMessages([]);
    sendMessage({ type: 'chat', message: '', clear: true });
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  /* Register handler for chat_response — called from parent via ref */
  ChatPanel.onChatResponse = (text, fileActions, aiStateData) => {
    if (aiStateData) setAiState(aiStateData);
    setMessages(prev => {
      const next = [...prev, { role: 'model', text }];
      // Append file action results if Gemini wrote files
      if (fileActions && fileActions.length > 0) {
        next.push({
          role: 'system',
          text: null,
          fileActions,
        });
      }
      return next;
    });
    setLoading(false);
  };

  if (!open) {
    return (
      <button className="chat-toggle" onClick={() => setOpen(true)} title="Open Gemini Chat">
        <span className="chat-toggle-icon">✦</span>
        {messages.length > 0 && <span className="chat-badge">{messages.length}</span>}
      </button>
    );
  }

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <span className="chat-title">✦ Gemini</span>
        {aiState && aiState.ai_state && aiState.ai_state !== 'unknown' && (
          <span className={`chat-ai-state chat-ai-${aiState.ai_state}`}>
            {aiState.ai_state}
          </span>
        )}
        <div className="chat-header-actions">
          <button className="chat-btn-clear" onClick={handleClear} title="Clear chat">⟲</button>
          <button className="chat-btn-close" onClick={() => setOpen(false)}>✕</button>
        </div>
      </div>

      <div className="chat-messages" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="chat-empty">
            <div className="chat-dormant">💤 dormant</div>
            <div className="chat-dormant-hint">
              click a neuron in the brain to wake up a file — it'll probe you
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg chat-msg-${m.role}`}>
            {m.role === 'system' && m.fileActions ? (
              <div className="chat-file-actions">
                <div className="chat-file-actions-header">📁 File Actions</div>
                {m.fileActions.map((fa, j) => (
                  <div key={j} className={`chat-file-action ${fa.ok ? 'success' : 'error'}`}>
                    <span className="chat-file-icon">{fa.ok ? '✓' : '✗'}</span>
                    <span className="chat-file-path">{fa.path}</span>
                    {fa.ok && <span className="chat-file-size">({fa.size} bytes)</span>}
                    {!fa.ok && <span className="chat-file-error">{fa.error}</span>}
                  </div>
                ))}
              </div>
            ) : m.role === 'file' ? (
              /* File wakes up and probes operator */
              <div className="chat-file-probe">
                <div className="chat-file-header">
                  <span className="chat-file-emotion">{m.emotion}</span>
                  <span className="chat-file-speaker">{m.speaker} woke up</span>
                </div>
                <div className="chat-file-text">{m.text}</div>
                {m.probes && m.probes.length > 0 && (
                  <div className="chat-file-probes">
                    {m.probes.map((p, j) => (
                      <div key={j} className="chat-probe-q">{p}</div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <>
                <div className="chat-msg-role">{m.role === 'user' ? 'You' : '✦ Gemini'}</div>
                <div className="chat-msg-text">{m.text}</div>
              </>
            )}
          </div>
        ))}
        {loading && (
          <div className="chat-msg chat-msg-model">
            <div className="chat-msg-role">✦ Gemini</div>
            <div className="chat-msg-text chat-loading">
              <span className="dot-pulse" />
            </div>
          </div>
        )}
      </div>

      <div className="chat-input-row">
        <textarea
          ref={inputRef}
          className="chat-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={connected ? 'Ask Gemini...' : 'WS offline'}
          disabled={!connected}
          rows={1}
        />
        <button
          className="chat-send"
          onClick={handleSend}
          disabled={!input.trim() || loading || !connected}
        >
          ➤
        </button>
      </div>
    </div>
  );
}
