import React, { useEffect, useMemo, useState } from 'react';
import {
  formatRelativeTime,
  getNodeAliases,
  getStorageEntries,
  humanizeModuleName,
  loadNarrativeFeeds,
  mergeAliasLists,
  resolveContextVein,
  resolveNumericWords,
  resolveSemanticDossier,
  resolveTouchCount,
} from './narrativeData';

function formatPercent(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function formatCompactCount(value) {
  const numeric = Number(value || 0);
  if (numeric >= 1000) {
    return `${(numeric / 1000).toFixed(1)}K`;
  }
  return String(numeric);
}

function buildNarrativeBlurb(node, semanticLatest, fallbackNarrative) {
  if (fallbackNarrative) {
    return fallbackNarrative;
  }

  const state = semanticLatest?.thinking?.state || node.personality || 'stable';
  const region = semanticLatest?.knows?.brain_region || 'the graph surface';
  const entropy = semanticLatest?.thinking?.entropy ?? node.dual_score ?? 0;
  const voidCount = semanticLatest?.thinking?.void_count ?? 0;
  const relationships = (node.edges_in?.length || 0) + (node.edges_out?.length || 0);

  if (voidCount > 0) {
    return `${humanizeModuleName(node.name)} is currently ${state}. It is living in ${region}, carrying ${formatPercent(entropy)} entropy, and still has ${voidCount} open semantic questions pulling on it.`;
  }

  return `${humanizeModuleName(node.name)} is currently ${state}. It is living in ${region}, carrying ${formatPercent(entropy)} entropy, and speaking mostly through ${relationships} graph relationships plus prompt memory rather than a fully written semantic dossier.`;
}

function ModuleLink({ targetNode, onOpen }) {
  return (
    <span
      className="module-link"
      onClick={() => onOpen && onOpen(targetNode)}
      title={`Open ${humanizeModuleName(targetNode?.name)}`}
    >
      {humanizeModuleName(targetNode?.name)}
    </span>
  );
}

function PromptCard({ prompt }) {
  return (
    <div className="prompt-card">
      <div className="prompt-meta">
        <span>{formatRelativeTime(prompt.ts)}</span>
        <span>{prompt.intent || 'unknown'}</span>
        <span>{prompt.state || 'unknown'}</span>
      </div>
      <div className="prompt-preview">{prompt.preview}</div>
      {(prompt.deleted_words?.length || prompt.rewrites?.length) > 0 && (
        <div className="prompt-flags">
          {prompt.deleted_words?.length > 0 && (
            <span>deleted: {prompt.deleted_words.join(', ')}</span>
          )}
          {prompt.rewrites?.length > 0 && (
            <span>
              rewrites: {prompt.rewrites.map((rewrite) => `${rewrite.old || '…'} -> ${rewrite.new || '…'}`).join(' | ')}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

export default function ProfilePage({
  node,
  graphData,
  narratives,
  onNavigate,
  onClose,
}) {
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [wakeLoading, setWakeLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [chatHistory, setChatHistory] = useState([]);
  const [feeds, setFeeds] = useState({
    narrativeMemory: null,
    intentNumeric: null,
    semanticLayer: null,
  });

  const aliases = useMemo(() => getNodeAliases(node), [node]);
  const readableName = useMemo(() => humanizeModuleName(node?.name), [node?.name]);
  const semanticDossier = useMemo(
    () => resolveSemanticDossier(feeds.semanticLayer, aliases),
    [feeds.semanticLayer, aliases],
  );
  const semanticLatest = semanticDossier?.latest || null;
  const promptHistory = useMemo(
    () => mergeAliasLists(feeds.narrativeMemory?.by_module, aliases, 10),
    [feeds.narrativeMemory, aliases],
  );
  const numericWords = useMemo(
    () => resolveNumericWords(feeds.intentNumeric, aliases, 14),
    [feeds.intentNumeric, aliases],
  );
  const touchCount = useMemo(
    () => resolveTouchCount(feeds.intentNumeric, aliases),
    [feeds.intentNumeric, aliases],
  );
  const storageEntries = useMemo(
    () => getStorageEntries(feeds.narrativeMemory),
    [feeds.narrativeMemory],
  );
  const contextVein = useMemo(
    () => resolveContextVein(feeds.narrativeMemory, aliases),
    [feeds.narrativeMemory, aliases],
  );
  const organism = feeds.narrativeMemory?.organism || {};

  const relatedNodes = useMemo(() => {
    if (!graphData || !node) {
      return { importers: [], imports: [] };
    }
    const nodeMap = Object.fromEntries((graphData.nodes || []).map((item) => [item.name, item]));
    return {
      importers: (node.edges_in || []).map((name) => nodeMap[name]).filter(Boolean),
      imports: (node.edges_out || []).map((name) => nodeMap[name]).filter(Boolean),
    };
  }, [graphData, node]);

  useEffect(() => {
    let cancelled = false;
    loadNarrativeFeeds().then((nextFeeds) => {
      if (!cancelled) {
        setFeeds(nextFeeds);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [node?.name]);

  useEffect(() => {
    if (!node) {
      return;
    }
    // Wake up the module with a REAL LLM call for self-analysis
    setWakeLoading(true);
    setChatMessages([{ role: 'file', text: `waking up ${readableName}...` }]);

    const CHAT_SERVER = 'http://localhost:8234';
    fetch(`${CHAT_SERVER}/wake`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ module: node.name }),
    })
      .then((response) => response.json())
      .then((data) => {
        setWakeLoading(false);
        if (data.response) {
          setChatMessages([{ role: 'file', text: data.response }]);
        } else {
          setChatMessages([{ role: 'file', text: `${readableName} is awake but silent.` }]);
        }
      })
      .catch((error) => {
        setWakeLoading(false);
        console.error('wake failed:', error);
        // Fallback to static greeting
        const entropy = node.dual_score || 0;
        const deaths = node.agent_deaths || 0;
        let greeting = `${readableName} here. wake server offline — running on cached state.`;
        if (entropy > 0.5) {
          greeting += ` entropy is ${formatPercent(entropy)}.`;
        }
        if (deaths > 2) {
          greeting += ` ${deaths} deaths logged.`;
        }
        setChatMessages([{ role: 'file', text: greeting }]);
      });

    // Also fetch chat history for this module
    fetch(`${CHAT_SERVER}/history/${encodeURIComponent(node.name)}`)
      .then((response) => response.json())
      .then((data) => {
        if (data.entries) {
          setChatHistory(data.entries);
        }
      })
      .catch(() => {});
  }, [node, readableName]);

  if (!node) {
    return null;
  }

  const narrativeText = buildNarrativeBlurb(node, semanticLatest, narratives?.[node.name]?.text);

  const CHAT_SERVER = 'http://localhost:8234';

  const handleChatSend = () => {
    const text = chatInput.trim();
    if (!text || chatLoading) {
      return;
    }

    setChatMessages((current) => [...current, { role: 'user', text }]);
    setChatInput('');
    setChatLoading(true);

    const history = chatMessages.map((msg) => ({ who: msg.role, text: msg.text }));

    fetch(`${CHAT_SERVER}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        module: node.name,
        message: text,
        history,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        setChatLoading(false);
        if (data.response) {
          setChatMessages((current) => [...current, { role: 'file', text: data.response }]);
        } else {
          setChatMessages((current) => [...current, { role: 'file', text: '[no response]' }]);
        }
      })
      .catch((error) => {
        setChatLoading(false);
        console.error('chat failed:', error);
        setChatMessages((current) => [...current, { role: 'error', text: `chat error: ${error.message}` }]);
      });
  };

  return (
    <div className="profile-page">
      <div className="profile-header">
        <button className="profile-back" onClick={onClose}>Back to Graph</button>
        <div className="profile-title-row">
          <span className="profile-icon">{contextVein.clot ? '🩸' : contextVein.artery ? '🫀' : '📄'}</span>
          <h1 className="profile-title">{readableName}</h1>
          <span className="profile-ver">v{node.ver || 1}</span>
        </div>
        <p className="profile-desc">{(node.desc || '').replace(/_/g, ' ')}</p>
      </div>

      <div className="profile-layout">
        <div className="profile-content">
          <div className="profile-tabs">
            <button className={`profile-tab ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>Overview</button>
            <button className={`profile-tab ${activeTab === 'memory' ? 'active' : ''}`} onClick={() => setActiveTab('memory')}>Memory</button>
            <button className={`profile-tab ${activeTab === 'runtime' ? 'active' : ''}`} onClick={() => setActiveTab('runtime')}>Runtime</button>
            <button className={`profile-tab ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>History</button>
          </div>

          {activeTab === 'overview' && (
            <>
              <section className="profile-section">
                <h2>Narrative</h2>
                <p className="profile-narrative">{narrativeText}</p>
              </section>

              {(contextVein.clot || contextVein.artery) && (
                <section className="profile-section">
                  <h2>Circulation</h2>
                  {contextVein.artery && (
                    <div className="vein-status artery">
                      Critical artery. In-degree {contextVein.artery.in_degree}, out-degree {contextVein.artery.out_degree}, vein score {contextVein.artery.vein_score}.
                    </div>
                  )}
                  {contextVein.clot && (
                    <div className="vein-status clot">
                      Clot candidate. Signals: {contextVein.clot.clot_signals.join(', ')}.
                    </div>
                  )}
                </section>
              )}

              <section className="profile-section">
                <h2>Dossier</h2>
                <div className="profile-dossier-grid">
                  <div className="dossier-card">
                    <h3>What It Knows</h3>
                    <div className="dossier-list">
                      <span>brain region: {semanticLatest?.knows?.brain_region || 'graph only'}</span>
                      <span>exports: {(semanticLatest?.knows?.exports || []).length || 0}</span>
                      <span>imports: {(semanticLatest?.knows?.imports || []).length || 0}</span>
                      <span>genesis: {semanticLatest?.knows?.genesis_hash || 'not profiled yet'}</span>
                    </div>
                  </div>
                  <div className="dossier-card">
                    <h3>What It Thinks</h3>
                    <div className="dossier-list">
                      <span>state: {semanticLatest?.thinking?.state || node.personality || 'stable'}</span>
                      <span>heat: {semanticLatest?.thinking?.heat ?? node.dual_score ?? 0}</span>
                      <span>entropy: {formatPercent(semanticLatest?.thinking?.entropy ?? node.dual_score ?? 0)}</span>
                      <span>semantic voids: {semanticLatest?.thinking?.void_count ?? 0}</span>
                    </div>
                  </div>
                  <div className="dossier-card">
                    <h3>What It Plans</h3>
                    <div className="dossier-list">
                      <span>needs test: {semanticLatest?.plans?.needs_test ? 'yes' : 'no'}</span>
                      <span>needs split: {semanticLatest?.plans?.needs_split ? 'yes' : 'no'}</span>
                      <span>needs docstrings: {semanticLatest?.plans?.needs_docstrings ? 'yes' : 'no'}</span>
                      <span>operator intent: {semanticLatest?.plans?.operator_intent || 'unknown'}</span>
                    </div>
                  </div>
                </div>
              </section>

              {node.fears?.length > 0 && (
                <section className="profile-section">
                  <h2>Fears</h2>
                  <ul className="profile-fears">
                    {node.fears.map((fear) => (
                      <li key={fear} className="profile-fear">{fear}</li>
                    ))}
                  </ul>
                </section>
              )}

              <section className="profile-section">
                <h2>Relationships</h2>
                {relatedNodes.importers.length > 0 && (
                  <div className="profile-rels">
                    <h3>Who Imports Me</h3>
                    <div className="profile-links">
                      {relatedNodes.importers.map((targetNode) => (
                        <ModuleLink key={targetNode.name} targetNode={targetNode} onOpen={onNavigate} />
                      ))}
                    </div>
                  </div>
                )}
                {relatedNodes.imports.length > 0 && (
                  <div className="profile-rels">
                    <h3>Who I Import</h3>
                    <div className="profile-links">
                      {relatedNodes.imports.map((targetNode) => (
                        <ModuleLink key={targetNode.name} targetNode={targetNode} onOpen={onNavigate} />
                      ))}
                    </div>
                  </div>
                )}
                {node.partners?.length > 0 && (
                  <div className="profile-rels">
                    <h3>Partners</h3>
                    <div className="profile-links">
                      {node.partners.map((partner) => (
                        <span key={partner} className="module-link partner">{humanizeModuleName(partner)}</span>
                      ))}
                    </div>
                  </div>
                )}
              </section>
            </>
          )}

          {activeTab === 'memory' && (
            <>
              <section className="profile-section">
                <h2>Numeric Encoding</h2>
                <p className="profile-note">
                  This file learns through weighted tokens in the intent matrix. Touch count: {touchCount || 0}.
                </p>
                {numericWords.length > 0 ? (
                  <div className="badge-list">
                    {numericWords.map(({ word, weight }) => (
                      <span key={word} className="badge-item">{word} {weight.toFixed(3)}</span>
                    ))}
                  </div>
                ) : (
                  <p className="profile-note">No numeric weights have been written for this file yet.</p>
                )}
              </section>

              <section className="profile-section">
                <h2>Prompt Memory</h2>
                {promptHistory.length > 0 ? (
                  <div className="profile-timeline">
                    {promptHistory.map((prompt) => (
                      <PromptCard key={`${prompt.ts}-${prompt.preview}`} prompt={prompt} />
                    ))}
                  </div>
                ) : (
                  <p className="profile-note">No prompt journal entries currently map cleanly to this file.</p>
                )}
              </section>

              <section className="profile-section">
                <h2>Prompt Storage</h2>
                <div className="storage-list">
                  {storageEntries.map((entry) => (
                    <div key={entry.path} className="storage-row">
                      <span>{entry.label}</span>
                      <span className="storage-path">{entry.path}</span>
                    </div>
                  ))}
                </div>
              </section>
            </>
          )}

          {activeTab === 'runtime' && (
            <>
              <section className="profile-section">
                <h2>Live Narrative</h2>
                <p className="profile-narrative">
                  {organism.organism_narrative || 'No organism narrative is currently available.'}
                </p>
                <p className="profile-note">
                  Copilot intent: {organism.copilot_intent || 'unknown'}
                </p>
              </section>

              <section className="profile-section">
                <h2>Prompt Surface</h2>
                <div className="dossier-card">
                  <div className="dossier-list">
                    <span>latest prompt: {organism.latest_prompt?.preview || 'n/a'}</span>
                    <span>prompt state: {organism.latest_prompt?.state || 'unknown'}</span>
                    <span>prompt intent: {organism.latest_prompt?.intent || 'unknown'}</span>
                    <span>wpm: {Math.round(organism.signals?.wpm || 0)}</span>
                    <span>deletion ratio: {formatPercent(organism.signals?.deletion_ratio || 0)}</span>
                  </div>
                </div>
              </section>

              <section className="profile-section">
                <h2>Semantic Questions</h2>
                {semanticLatest?.history?.void_history?.[0]?.top_questions?.length > 0 ? (
                  <div className="profile-timeline">
                    {semanticLatest.history.void_history[0].top_questions.map((question) => (
                      <div key={question} className="prompt-card">
                        <div className="prompt-preview">{question}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="profile-note">No semantic questions are recorded for this file yet.</p>
                )}
              </section>
            </>
          )}

          {activeTab === 'history' && (
            <>
              <section className="profile-section">
                <h2>Conversation History</h2>
                <p className="profile-note">
                  All file chats are logged to prompt_journal.jsonl. These are the conversations involving {readableName}.
                </p>
                {chatHistory.length > 0 ? (
                  <div className="profile-timeline">
                    {chatHistory.map((entry, idx) => (
                      <div key={`${entry.ts}-${idx}`} className="prompt-card">
                        <div className="prompt-meta">
                          <span>{formatRelativeTime(entry.ts)}</span>
                          <span>{entry.intent || 'file_chat'}</span>
                          <span>{entry.source || 'operator'}</span>
                        </div>
                        <div className="prompt-preview">{entry.msg}</div>
                        {entry.response && (
                          <div className="prompt-flags">
                            <span className="file-response">→ {entry.response}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="profile-note">No conversation history yet. Chat with this file to build history.</p>
                )}
              </section>

              <section className="profile-section">
                <h2>RSI Goals</h2>
                <p className="profile-note">
                  Recursive self-improvement tracking. Files wake up, analyze themselves, and set goals toward interlinked system coherence.
                </p>
                <div className="dossier-card">
                  <div className="dossier-list">
                    <span>loop status: {chatHistory.length > 0 ? 'active' : 'dormant'}</span>
                    <span>wake count: {chatHistory.filter((e) => e.intent === 'file_wake').length}</span>
                    <span>chat count: {chatHistory.filter((e) => e.intent === 'file_chat').length}</span>
                    <span>interlink target: improve stability and reduce entropy</span>
                  </div>
                </div>
              </section>
            </>
          )}
        </div>

        <div className="profile-sidebar">
          <div className="profile-infobox">
            <div className="infobox-header">{readableName}</div>
            <div className="infobox-row">
              <span className="infobox-label">path</span>
              <span className="infobox-value path" title={node.path}>{(node.path || '').split('/').pop() || node.path}</span>
            </div>
            <div className="infobox-row">
              <span className="infobox-label">tokens</span>
              <span className="infobox-value">{formatCompactCount(node.tokens)}</span>
            </div>
            <div className="infobox-row">
              <span className="infobox-label">graph entropy</span>
              <span className="infobox-value">{formatPercent(node.dual_score || 0)}</span>
            </div>
            <div className="infobox-row">
              <span className="infobox-label">prompt mentions</span>
              <span className="infobox-value">{promptHistory.length}</span>
            </div>
            <div className="infobox-row">
              <span className="infobox-label">numeric touches</span>
              <span className="infobox-value">{touchCount || 0}</span>
            </div>
            <div className="infobox-row">
              <span className="infobox-label">deaths</span>
              <span className="infobox-value">{node.agent_deaths || 0}</span>
            </div>
            <div className="infobox-row">
              <span className="infobox-label">hesitation</span>
              <span className="infobox-value">{formatPercent(node.human_hesitation || 0)}</span>
            </div>
          </div>

          <div className="profile-chat">
            <div className="profile-chat-header">
              <span>Chat with {readableName}</span>
              <span className={`chat-status ${wakeLoading ? 'waking' : 'online'}`}>
                {wakeLoading ? 'waking...' : 'ready'}
              </span>
            </div>
            <div className="profile-chat-messages">
              {chatMessages.map((message, index) => (
                <div key={`${message.role}-${index}`} className={`profile-chat-msg ${message.role}`}>
                  <span className="chat-msg-role">
                    {message.role === 'file' ? readableName : message.role === 'user' ? 'You' : message.role === 'error' ? '⚠️' : 'Gemini'}
                  </span>
                  <span className="chat-msg-text">{message.text}</span>
                </div>
              ))}
              {chatLoading && (
                <div className="profile-chat-msg model">
                  <span className="chat-msg-role">Gemini</span>
                  <span className="chat-msg-text loading">thinking...</span>
                </div>
              )}
            </div>
            <div className="profile-chat-input">
              <input
                type="text"
                value={chatInput}
                onChange={(event) => setChatInput(event.target.value)}
                onKeyDown={(event) => event.key === 'Enter' && handleChatSend()}
                placeholder={`Ask ${readableName}...`}
                disabled={wakeLoading}
              />
              <button onClick={handleChatSend} disabled={!chatInput.trim() || chatLoading || wakeLoading}>➤</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}