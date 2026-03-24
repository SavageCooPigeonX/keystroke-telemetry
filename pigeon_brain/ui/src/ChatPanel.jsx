/* ChatPanel — Gemini-powered project assistant embedded in Pigeon Brain */
import React, { useState, useRef, useEffect } from 'react';

export default function ChatPanel({ sendMessage, selectedNode, connected }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [aiState, setAiState] = useState(null);
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
            Ask Gemini about your codebase. It sees the same graph, modules, and telemetry you do.
            {selectedNode && (
              <div className="chat-context-hint">
                Context: <strong>{selectedNode.label?.replace(/_seq\d+.*/, '')}</strong> selected
              </div>
            )}
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
