import fs from 'fs';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

const repoRoot = path.resolve(__dirname, '..', '..');

function sendJson(res, payload, statusCode = 200) {
  res.statusCode = statusCode;
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.end(JSON.stringify(payload));
}

function sendJsonFile(res, filePath) {
  if (!fs.existsSync(filePath)) {
    sendJson(res, {});
    return;
  }
  try {
    res.statusCode = 200;
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.end(fs.readFileSync(filePath, 'utf-8'));
  } catch {
    sendJson(res, {});
  }
}

function readJsonFile(filePath, fallback = {}) {
  if (!fs.existsSync(filePath)) {
    return fallback;
  }
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  } catch {
    return fallback;
  }
}

function loadJsonLines(filePath, maxLines = 800) {
  if (!fs.existsSync(filePath)) {
    return [];
  }
  try {
    return fs
      .readFileSync(filePath, 'utf-8')
      .split(/\r?\n/)
      .filter(Boolean)
      .slice(-maxLines)
      .flatMap((line) => {
        try {
          return [JSON.parse(line)];
        } catch {
          return [];
        }
      });
  } catch {
    return [];
  }
}

function normalizeModuleKey(value) {
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

function compactText(value, maxLength = 220) {
  const text = String(value || '').replace(/\s+/g, ' ').trim();
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength - 1)}…`;
}

function compactRewrite(value) {
  if (!value || typeof value !== 'object') {
    return null;
  }
  const oldText = compactText(value.old || '', 80);
  const newText = compactText(value.new || '', 80);
  if (!oldText && !newText) {
    return null;
  }
  return { old: oldText, new: newText };
}

function shouldSkipPromptEntry(entry) {
  if (!entry || entry.prompt_kind === 'meta_hook') {
    return true;
  }
  const message = String(entry.msg || '').trim();
  if (!message) {
    return true;
  }
  return /task complete reminder/i.test(message);
}

function collectPromptKeys(entry) {
  const rawKeys = [];
  (entry.module_refs || []).forEach((item) => rawKeys.push(item));
  (entry.files_open || []).forEach((item) => rawKeys.push(item));
  (entry.hot_modules || []).forEach((item) => {
    rawKeys.push(typeof item === 'string' ? item : item?.module);
  });
  return [...new Set(rawKeys.map(normalizeModuleKey).filter(Boolean))];
}

function compactPromptEntry(entry) {
  const deletedWords = (entry.deleted_words || [])
    .map((item) => (typeof item === 'string' ? item : item?.word))
    .filter(Boolean)
    .map((item) => compactText(item, 60))
    .slice(-4);

  const rewrites = (entry.rewrites || [])
    .map(compactRewrite)
    .filter(Boolean)
    .slice(-3);

  return {
    ts: entry.ts || '',
    session_n: entry.session_n || 0,
    preview: compactText(entry.msg || '', 220),
    intent: entry.intent || 'unknown',
    state: entry.cognitive_state || entry.state || 'unknown',
    module_refs: (entry.module_refs || []).map(normalizeModuleKey).filter(Boolean).slice(0, 6),
    files_open: (entry.files_open || []).map((item) => String(item)).slice(0, 4),
    deleted_words: deletedWords,
    rewrites,
    normalized_keys: collectPromptKeys(entry),
  };
}

function extractNarrativeFields() {
  const instructionsPath = path.resolve(repoRoot, '.github', 'copilot-instructions.md');
  if (!fs.existsSync(instructionsPath)) {
    return { organism_narrative: '', copilot_intent: '' };
  }
  try {
    const text = fs.readFileSync(instructionsPath, 'utf-8');
    const narrativeMatch = text.match(/> (the organism .+?)$/m);
    const intentMatch = text.match(/INTERPRETED INTENT: (.+?)$/m);
    return {
      organism_narrative: narrativeMatch?.[1]?.trim() || '',
      copilot_intent: intentMatch?.[1]?.trim() || '',
    };
  } catch {
    return { organism_narrative: '', copilot_intent: '' };
  }
}

function buildNarrativeMemoryPayload() {
  const promptTelemetryPath = path.resolve(repoRoot, 'logs', 'prompt_telemetry_latest.json');
  const promptJournalPath = path.resolve(repoRoot, 'logs', 'prompt_journal.jsonl');
  const contextVeinsPath = path.resolve(repoRoot, 'pigeon_brain', 'context_veins.json');

  const compactEntries = loadJsonLines(promptJournalPath, 800)
    .filter((entry) => !shouldSkipPromptEntry(entry))
    .map(compactPromptEntry)
    .filter((entry) => entry.preview);

  const byModule = {};
  compactEntries.forEach((entry) => {
    entry.normalized_keys.forEach((key) => {
      if (!byModule[key]) {
        byModule[key] = [];
      }
      byModule[key].push(entry);
      if (byModule[key].length > 12) {
        byModule[key].shift();
      }
    });
  });

  const recentPrompts = compactEntries
    .slice(-18)
    .reverse()
    .map(({ normalized_keys, ...entry }) => entry);

  Object.keys(byModule).forEach((key) => {
    byModule[key] = byModule[key]
      .slice()
      .reverse()
      .map(({ normalized_keys, ...entry }) => entry);
  });

  const telemetry = readJsonFile(promptTelemetryPath, {});
  const latestPrompt = telemetry.latest_prompt || {};
  const signals = telemetry.signals || {};
  const contextVeins = readJsonFile(contextVeinsPath, {});
  const narrativeFields = extractNarrativeFields();

  return {
    schema: 'narrative_memory_ui/v1',
    generated: new Date().toISOString(),
    storage: {
      prompt_journal: 'logs/prompt_journal.jsonl',
      prompt_telemetry: 'logs/prompt_telemetry_latest.json',
      intent_matrix: 'logs/intent_matrix.json',
      intent_vocab: 'logs/intent_vocab.json',
      file_semantic_layer: 'logs/file_semantic_layer.json',
      context_veins: 'pigeon_brain/context_veins.json',
    },
    organism: {
      ...narrativeFields,
      latest_prompt: {
        preview: compactText(latestPrompt.preview || '', 80),
        intent: latestPrompt.intent || 'unknown',
        state: latestPrompt.state || 'unknown',
      },
      signals: {
        wpm: Number(signals.wpm || 0),
        deletion_ratio: Number(signals.deletion_ratio || 0),
        hesitation_count: Number(signals.hesitation_count || 0),
        rewrite_count: Number(signals.rewrite_count || 0),
      },
    },
    recent_prompts: recentPrompts,
    by_module: byModule,
    context_veins: {
      stats: contextVeins.stats || {},
      clots: (contextVeins.clots || []).slice(0, 8),
      arteries: (contextVeins.arteries || []).slice(0, 8),
      trim_recommendations: (contextVeins.trim_recommendations || []).slice(0, 6),
    },
  };
}

function buildIntentNumericPayload() {
  const matrixPath = path.resolve(repoRoot, 'logs', 'intent_matrix.json');
  const vocabPath = path.resolve(repoRoot, 'logs', 'intent_vocab.json');
  if (!fs.existsSync(matrixPath) || !fs.existsSync(vocabPath)) {
    return { file_weights: {}, touch_counts: {} };
  }

  try {
    const matrix = JSON.parse(fs.readFileSync(matrixPath, 'utf-8'));
    const vocab = JSON.parse(fs.readFileSync(vocabPath, 'utf-8'));
    const wordToId = vocab.word_to_id || {};
    const idToWord = Object.fromEntries(
      Object.entries(wordToId).map(([word, id]) => [String(id), word]),
    );

    const decoded = {};
    for (const [fileKey, weights] of Object.entries(matrix.matrix || {})) {
      const wordWeights = {};
      for (const [wordId, weight] of Object.entries(weights || {})) {
        const word = idToWord[String(wordId)];
        if (!word) continue;
        wordWeights[word] = Number(weight);
      }
      decoded[fileKey] = wordWeights;
    }

    return {
      schema: 'intent_numeric_ui/v1',
      generated: new Date().toISOString(),
      file_weights: decoded,
      touch_counts: matrix.touch_counts || {},
      vocab_size: Object.keys(wordToId).length,
      file_count: Object.keys(decoded).length,
    };
  } catch {
    return { file_weights: {}, touch_counts: {} };
  }
}

function installSignalRoutes(server) {
  const jsonFiles = [
    ['/dual_view.json', path.resolve(__dirname, '..', 'dual_view.json')],
    ['/prompt_telemetry.json', path.resolve(repoRoot, 'logs', 'prompt_telemetry_latest.json')],
    ['/file_semantic_layer.json', path.resolve(repoRoot, 'logs', 'file_semantic_layer.json')],
    ['/context_veins.json', path.resolve(repoRoot, 'pigeon_brain', 'context_veins.json')],
  ];

  jsonFiles.forEach(([route, filePath]) => {
    server.middlewares.use(route, (_, res) => {
      sendJsonFile(res, filePath);
    });
  });

  server.middlewares.use('/intent_numeric.json', (_, res) => {
    sendJson(res, buildIntentNumericPayload());
  });

  server.middlewares.use('/narrative_memory.json', (_, res) => {
    sendJson(res, buildNarrativeMemoryPayload());
  });
}

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'serve-pigeon-signals',
      configureServer(server) {
        installSignalRoutes(server);
      },
      configurePreviewServer(server) {
        installSignalRoutes(server);
      },
    },
  ],
  server: { port: 3333 },
});
