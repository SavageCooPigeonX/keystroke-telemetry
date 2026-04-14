const STEM_LABELS = {
  ba: 'backward',
  cpm: 'copilot prompt manager',
  dp: 'dynamic prompt',
  fc: 'file consciousness',
  fhm: 'file heat map',
  ir: 'import rewriter',
  mb: 'manifest builder',
  pe: 'prompt enricher',
  ph: 'pulse harvest',
  pj: 'prompt journal',
  pn: 'push narrative',
  ps: 'prediction scorer',
  reg: 'registry',
  rwd: 'rework detector',
  sa: 'staleness alert',
  sf: 'self fix',
  sl: 'streaming layer',
  tp: 'training pairs',
};

async function safeFetchJson(url) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      return null;
    }
    return await response.json();
  } catch {
    return null;
  }
}

export async function loadNarrativeFeeds() {
  const [narrativeMemory, intentNumeric, semanticLayer] = await Promise.all([
    safeFetchJson('/narrative_memory.json'),
    safeFetchJson('/intent_numeric.json'),
    safeFetchJson('/file_semantic_layer.json'),
  ]);

  return {
    narrativeMemory,
    intentNumeric,
    semanticLayer,
  };
}

export function normalizeModuleKey(value) {
  if (!value) {
    return '';
  }

  const raw = String(value).trim().replace(/\\/g, '/').toLowerCase();
  const base = raw.split('/').pop() || raw;

  return base
    .replace(/\.(py|jsx?|tsx?|md|jsonl?|txt)$/i, '')
    .replace(/_seq\d+.*$/i, '')
    .replace(/_s\d+.*$/i, '');
}

export function getNodeAliases(node) {
  const aliases = new Set();
  [node?.name, node?.label, node?.path].forEach((value) => {
    const key = normalizeModuleKey(value);
    if (key) {
      aliases.add(key);
    }
  });
  return Array.from(aliases);
}

export function humanizeModuleName(value) {
  const key = normalizeModuleKey(value);
  if (!key) {
    return 'unknown';
  }
  if (STEM_LABELS[key]) {
    return STEM_LABELS[key];
  }

  const parts = key.split('_').filter(Boolean);
  const suffix = parts[parts.length - 1];
  if (suffix && STEM_LABELS[suffix]) {
    return STEM_LABELS[suffix];
  }

  return key.replace(/_/g, ' ');
}

function pickFirstMatchingRecord(recordMap, aliases) {
  if (!recordMap) {
    return null;
  }
  for (const alias of aliases) {
    if (recordMap[alias]) {
      return recordMap[alias];
    }
  }
  return null;
}

export function mergeAliasLists(recordMap, aliases, limit = 12) {
  const seen = new Set();
  const merged = [];

  aliases.forEach((alias) => {
    (recordMap?.[alias] || []).forEach((entry) => {
      const entryId = `${entry.ts || ''}-${entry.preview || ''}`;
      if (!seen.has(entryId)) {
        seen.add(entryId);
        merged.push(entry);
      }
    });
  });

  return merged
    .sort((left, right) => String(right.ts || '').localeCompare(String(left.ts || '')))
    .slice(0, limit);
}

export function resolveNumericWords(intentNumeric, aliases, limit = 14) {
  const weights = pickFirstMatchingRecord(intentNumeric?.file_weights || {}, aliases);
  if (!weights) {
    return [];
  }

  return Object.entries(weights)
    .map(([word, weight]) => ({ word, weight: Number(weight || 0) }))
    .sort((left, right) => right.weight - left.weight)
    .slice(0, limit);
}

export function resolveTouchCount(intentNumeric, aliases) {
  const touchCounts = intentNumeric?.touch_counts || {};
  for (const alias of aliases) {
    if (touchCounts[alias] != null) {
      return Number(touchCounts[alias] || 0);
    }
  }
  return 0;
}

export function resolveSemanticDossier(semanticLayer, aliases) {
  return pickFirstMatchingRecord(semanticLayer || {}, aliases);
}

export function resolveContextVein(narrativeMemory, aliases) {
  const matchModule = (entry) => aliases.includes(normalizeModuleKey(entry?.module));

  return {
    clot: (narrativeMemory?.context_veins?.clots || []).find(matchModule) || null,
    artery: (narrativeMemory?.context_veins?.arteries || []).find(matchModule) || null,
  };
}

export function getStorageEntries(narrativeMemory) {
  return Object.entries(narrativeMemory?.storage || {}).map(([label, path]) => ({
    label: label.replace(/_/g, ' '),
    path,
  }));
}

export function formatRelativeTime(value) {
  if (!value) {
    return 'unknown';
  }

  const time = new Date(value).getTime();
  if (!Number.isFinite(time)) {
    return value;
  }

  const deltaSeconds = Math.max(0, Math.round((Date.now() - time) / 1000));
  if (deltaSeconds < 60) {
    return `${deltaSeconds}s ago`;
  }
  const deltaMinutes = Math.round(deltaSeconds / 60);
  if (deltaMinutes < 60) {
    return `${deltaMinutes}m ago`;
  }
  const deltaHours = Math.round(deltaMinutes / 60);
  if (deltaHours < 24) {
    return `${deltaHours}h ago`;
  }
  const deltaDays = Math.round(deltaHours / 24);
  return `${deltaDays}d ago`;
}