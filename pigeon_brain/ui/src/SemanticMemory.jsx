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

function PromptSnippet({ prompt }) {
  return (
    <div className="sm-prompt-card">
      <div className="sm-prompt-meta">
        <span>{formatRelativeTime(prompt.ts)}</span>
        <span>{prompt.intent || 'unknown'}</span>
      </div>
      <div className="sm-prompt-text">{prompt.preview}</div>
    </div>
  );
}

export default function SemanticMemory({ selectedNode }) {
  const [feeds, setFeeds] = useState({
    narrativeMemory: null,
    intentNumeric: null,
    semanticLayer: null,
  });

  const aliases = useMemo(() => getNodeAliases(selectedNode), [selectedNode]);
  const promptHistory = useMemo(
    () => mergeAliasLists(feeds.narrativeMemory?.by_module, aliases, 6),
    [feeds.narrativeMemory, aliases],
  );
  const numericWords = useMemo(
    () => resolveNumericWords(feeds.intentNumeric, aliases, 10),
    [feeds.intentNumeric, aliases],
  );
  const touchCount = useMemo(
    () => resolveTouchCount(feeds.intentNumeric, aliases),
    [feeds.intentNumeric, aliases],
  );
  const semanticDossier = useMemo(
    () => resolveSemanticDossier(feeds.semanticLayer, aliases),
    [feeds.semanticLayer, aliases],
  );
  const semanticLatest = semanticDossier?.latest || null;
  const contextVein = useMemo(
    () => resolveContextVein(feeds.narrativeMemory, aliases),
    [feeds.narrativeMemory, aliases],
  );
  const storageEntries = useMemo(
    () => getStorageEntries(feeds.narrativeMemory),
    [feeds.narrativeMemory],
  );
  const recentPrompts = feeds.narrativeMemory?.recent_prompts || [];
  const organism = feeds.narrativeMemory?.organism || {};
  const veins = feeds.narrativeMemory?.context_veins || {};

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
  }, [selectedNode?.label, selectedNode?.name]);

  if (!selectedNode) {
    return (
      <div className="semantic-memory empty">
        <div className="sm-header">
          <span className="sm-icon">📚</span>
          <span className="sm-name">Narrative Memory</span>
        </div>

        <div className="sm-section wide">
          <div className="sm-section-header">Organism</div>
          <div className="sm-organism">{organism.organism_narrative || 'No organism narrative is currently available.'}</div>
          <div className="sm-organism-meta">intent: {organism.copilot_intent || 'unknown'}</div>
        </div>

        <div className="sm-section wide">
          <div className="sm-section-header">Prompt Vault</div>
          <div className="sm-storage">
            {storageEntries.map((entry) => (
              <div key={entry.path} className="storage-row">
                <span>{entry.label}</span>
                <span className="storage-path">{entry.path}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="sm-section wide">
          <div className="sm-section-header">Recent Prompts</div>
          <div className="sm-prompt-list">
            {recentPrompts.slice(0, 4).map((prompt) => (
              <PromptSnippet key={`${prompt.ts}-${prompt.preview}`} prompt={prompt} />
            ))}
          </div>
        </div>

        <div className="sm-section wide">
          <div className="sm-section-header">Codebase Circulation</div>
          <div className="sm-circulation">
            <span>alive: {veins.stats?.alive ?? 0}</span>
            <span>clots: {veins.stats?.clots ?? 0}</span>
            <span>arteries: {veins.stats?.arteries ?? 0}</span>
            <span>avg health: {veins.stats?.avg_vein_health ?? 0}</span>
          </div>
          {(veins.clots || []).slice(0, 3).map((entry) => (
            <div key={entry.module} className="sm-fear">clot: {humanizeModuleName(entry.module)} | {entry.clot_signals.join(', ')}</div>
          ))}
        </div>
      </div>
    );
  }

  const nodeName = humanizeModuleName(selectedNode.label || selectedNode.name);
  const entropy = selectedNode.dualScore || selectedNode.dual_score || 0;
  const version = selectedNode.ver || 1;

  return (
    <div className="semantic-memory">
      <div className="sm-header">
        <span className="sm-icon">🧠</span>
        <span className="sm-name">{nodeName}</span>
        <span className="sm-ver">v{version}</span>
      </div>

      <div className="sm-stats">
        <div className="sm-stat">
          <span className="sm-stat-val">{touchCount || 0}</span>
          <span className="sm-stat-label">touches</span>
        </div>
        <div className="sm-stat">
          <span className="sm-stat-val">{formatPercent(entropy)}</span>
          <span className="sm-stat-label">entropy</span>
        </div>
        <div className="sm-stat">
          <span className="sm-stat-val">{promptHistory.length}</span>
          <span className="sm-stat-label">prompts</span>
        </div>
      </div>

      {numericWords.length > 0 && (
        <div className="sm-section">
          <div className="sm-section-header">Numeric Encoding</div>
          <div className="sm-word-list">
            {numericWords.map(({ word, weight }) => (
              <div key={word} className="sm-word">
                <span className="sm-word-text">{word}</span>
                <span className="sm-word-weight">{weight.toFixed(3)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="sm-section">
        <div className="sm-section-header">Prompt Mentions</div>
        <div className="sm-prompt-list">
          {promptHistory.length > 0 ? (
            promptHistory.map((prompt) => (
              <PromptSnippet key={`${prompt.ts}-${prompt.preview}`} prompt={prompt} />
            ))
          ) : (
            <div className="sm-empty">No prompt journal entries currently map to this file.</div>
          )}
        </div>
      </div>

      <div className="sm-section">
        <div className="sm-section-header">Semantic State</div>
        {semanticLatest ? (
          <>
            <div className="sm-fear-list">
              <div className="sm-partner">state: {semanticLatest.thinking?.state || 'unknown'}</div>
              <div className="sm-partner">voids: {semanticLatest.thinking?.void_count ?? 0}</div>
              <div className="sm-partner">operator intent: {semanticLatest.plans?.operator_intent || 'unknown'}</div>
            </div>
            {semanticLatest.history?.void_history?.[0]?.top_questions?.slice(0, 2).map((question) => (
              <div key={question} className="sm-fear">{question}</div>
            ))}
          </>
        ) : (
          <div className="sm-empty">Semantic layer has not profiled this file yet.</div>
        )}
      </div>

      {(contextVein.clot || contextVein.artery) && (
        <div className="sm-section">
          <div className="sm-section-header">Circulation</div>
          {contextVein.artery && <div className="sm-partner">artery: {contextVein.artery.vein_signals.join(', ')}</div>}
          {contextVein.clot && <div className="sm-fear">clot: {contextVein.clot.clot_signals.join(', ')}</div>}
        </div>
      )}

      <div className="sm-section">
        <div className="sm-section-header">Stored In</div>
        <div className="sm-storage">
          {storageEntries.map((entry) => (
            <div key={entry.path} className="storage-row">
              <span>{entry.label}</span>
              <span className="storage-path">{entry.path}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}