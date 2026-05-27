import React, { useEffect, useMemo, useState } from 'react';

function compactList(values, limit = 3) {
  return (values || []).slice(0, limit).join(' | ');
}

function lowerText(value) {
  return String(value || '').toLowerCase();
}

function queueTrigger(queryText, audit) {
  const trigger = {
    request_id: `qm-${Date.now()}`,
    status: 'queued_local',
    query_text: queryText,
    source_probe_id: audit?.probe?.probe_id || 'manual',
    source_audit_id: audit?.audit_id || 'manual',
    created_at: new Date().toISOString(),
  };
  const key = 'query_monitoring_trigger_queue';
  let queue = [];
  try {
    queue = JSON.parse(localStorage.getItem(key) || '[]');
  } catch {
    queue = [];
  }
  queue.unshift(trigger);
  localStorage.setItem(key, JSON.stringify(queue.slice(0, 50)));
  return trigger;
}

function QueryCard({ audit, selected, onSelect, onTrigger }) {
  const probe = audit.probe || {};
  return (
    <div
      className={`qm-card ${selected ? 'selected' : ''}`}
      role="button"
      tabIndex={0}
      onClick={() => onSelect(audit)}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onSelect(audit);
        }
      }}
    >
      <div className="qm-card-top">
        <span className="qm-class">{probe.probe_class || 'QUERY'}</span>
        <span className="qm-status">{audit.status || 'ready'}</span>
      </div>
      <div className="qm-name">{audit.name}</div>
      <div className="qm-query">{probe.query_text}</div>
      <div className="qm-meta">{compactList(probe.bias_dimensions, 4)}</div>
      <div className="qm-related">
        {(audit.related_queries || []).slice(0, 3).map((query) => (
          <button
            type="button"
            key={query}
            className="qm-chip"
            onClick={(event) => {
              event.stopPropagation();
              onTrigger(query, audit);
            }}
          >
            {query}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function QueryMonitoring() {
  const [payload, setPayload] = useState(null);
  const [query, setQuery] = useState('');
  const [selectedAudit, setSelectedAudit] = useState(null);
  const [lastTrigger, setLastTrigger] = useState(null);

  useEffect(() => {
    let cancelled = false;
    fetch('/query_monitoring_audits.json')
      .then((response) => response.json())
      .then((data) => {
        if (cancelled) {
          return;
        }
        setPayload(data);
        setSelectedAudit((data.audits || [])[0] || null);
      })
      .catch(() => {
        if (!cancelled) {
          setPayload({ audits: [] });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const audits = payload?.audits || [];
  const filteredAudits = useMemo(() => {
    const needle = lowerText(query).trim();
    if (!needle) {
      return audits;
    }
    return audits.filter((audit) => {
      const probe = audit.probe || {};
      const haystack = [
        audit.name,
        audit.status,
        probe.probe_id,
        probe.query_text,
        probe.probe_class,
        ...(probe.secondary_classes || []),
        ...(probe.location_scope || []),
        ...(probe.bias_dimensions || []),
        ...(audit.related_queries || []),
      ].map(lowerText).join(' ');
      return haystack.includes(needle);
    });
  }, [audits, query]);

  const triggerQuery = (queryText, audit = selectedAudit) => {
    setQuery(queryText);
    setSelectedAudit(audit);
    setLastTrigger(queueTrigger(queryText, audit));
  };

  const submitSearch = () => {
    const text = query.trim();
    if (!text) {
      return;
    }
    const best = filteredAudits[0] || selectedAudit;
    setSelectedAudit(best || null);
    setLastTrigger(queueTrigger(text, best));
  };

  if (!payload) {
    return <div className="query-monitoring"><div className="sm-loading">Loading query profiles...</div></div>;
  }

  const selectedProbe = selectedAudit?.probe || {};

  return (
    <div className="query-monitoring">
      <div className="qm-header">
        <div>
          <div className="qm-title">Query Monitoring</div>
          <div className="qm-subtitle">{audits.length} profiles ready for search</div>
        </div>
      </div>

      <div className="qm-search">
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => event.key === 'Enter' && submitSearch()}
          placeholder="Search probes, entities, places, drift..."
        />
        <button type="button" onClick={submitSearch} disabled={!query.trim()}>
          Run
        </button>
      </div>

      {lastTrigger && (
        <div className="qm-trigger">
          queued: {lastTrigger.query_text}
        </div>
      )}

      <div className="qm-stats">
        <span>{filteredAudits.length} matches</span>
        <span>{payload.schema || 'query profiles'}</span>
      </div>

      <div className="qm-list">
        {filteredAudits.map((audit) => (
          <QueryCard
            key={audit.audit_id}
            audit={audit}
            selected={selectedAudit?.audit_id === audit.audit_id}
            onSelect={setSelectedAudit}
            onTrigger={triggerQuery}
          />
        ))}
      </div>

      {selectedAudit && (
        <div className="qm-detail">
          <div className="qm-detail-title">{selectedAudit.name}</div>
          <div className="qm-detail-query">{selectedProbe.query_text}</div>
          <div className="qm-detail-grid">
            <span>shape</span><strong>{selectedProbe.expected_answer_shape}</strong>
            <span>scope</span><strong>{compactList(selectedProbe.location_scope, 4) || 'global'}</strong>
            <span>coverage</span><strong>{selectedAudit.model_coverage?.coverage_status || 'unknown'}</strong>
          </div>
          <div className="qm-related full">
            {(selectedAudit.related_queries || []).map((related) => (
              <button key={related} type="button" className="qm-chip button" onClick={() => triggerQuery(related, selectedAudit)}>
                {related}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
