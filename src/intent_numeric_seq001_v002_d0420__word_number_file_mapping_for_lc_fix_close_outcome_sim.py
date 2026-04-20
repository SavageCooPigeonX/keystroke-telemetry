"""intent_numeric_seq001_v001.py — word→number→file mapping for computed intent prediction.

The idea: instead of using LLM to guess which files are relevant to a prompt,
we learn the mapping numerically over time.

Architecture:
1. Vocabulary: word → numeric ID (grows as we see new words)
2. Prompt vector: bag-of-words → sparse vector of word IDs
3. File touch log: tracks which files get touched after which prompts
4. Correlation matrix: learned weights from prompt_vectors → file_relevance
5. Prediction: given new prompt, compute file relevance scores numerically

This is basically a simple neural net without calling it that — learned weights
from input (prompt) to output (file relevance), updated by observation.

The key insight: if prompt with words [thought, completer, buffer] is followed
by edits to tc_gemini_seq001_v001.py and tc_sim_seq001_v001.py, we increase the association:
  thought → tc_gemini_seq001_v001, completer → tc_gemini_seq001_v001, buffer → tc_sim_seq001_v001, etc.

Over time, this builds a "numeric surface" where intent predicts files
without any LLM inference — pure math.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v002 | 777 lines | ~6,751 tokens
# DESC:   word_number_file_mapping_for
# INTENT: fix_close_outcome_sim
# LAST:   2026-04-20 @ 6ae8700
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations
import difflib
import json
import re
import math
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from typing import Any

# ── Paths ──────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
VOCAB_PATH = ROOT / 'logs' / 'intent_vocab.json'
MATRIX_PATH = ROOT / 'logs' / 'intent_matrix.json'
TOUCH_LOG_PATH = ROOT / 'logs' / 'intent_touches.jsonl'

# ── Vocabulary ─────────────────────────────────────────────────────────────

_vocab: dict[str, int] = {}
_vocab_inverse: dict[int, str] = {}
_next_id: int = 1
_vocab_loaded: bool = False
_surface_healed: bool = False
_lexicon_cache: set[str] | None = None


def _load_vocab():
    """Load vocabulary from disk."""
    global _vocab, _vocab_inverse, _next_id, _vocab_loaded
    if VOCAB_PATH.exists():
        data = json.loads(VOCAB_PATH.read_text(encoding='utf-8'))
        _vocab = data.get('word_to_id', {})
        _next_id = data.get('next_id', 1)
        _vocab_inverse = {v: k for k, v in _vocab.items()}
    _vocab_loaded = True


def _save_vocab():
    """Persist vocabulary to disk."""
    VOCAB_PATH.parent.mkdir(parents=True, exist_ok=True)
    VOCAB_PATH.write_text(json.dumps({
        'word_to_id': _vocab,
        'next_id': _next_id,
        'updated': datetime.now(timezone.utc).isoformat(),
    }, ensure_ascii=False, indent=1), encoding='utf-8')


def _assign_word_id(word: str) -> int:
    """Assign a numeric ID without persisting on every internal merge."""
    global _next_id, _lexicon_cache
    wid = _vocab.get(word)
    if wid is not None:
        return wid
    wid = _next_id
    _next_id += 1
    _vocab[word] = wid
    _vocab_inverse[wid] = word
    _lexicon_cache = None
    return wid


def word_to_id(word: str, create: bool = True) -> int:
    """Get or create numeric ID for a word."""
    if not _vocab_loaded:
        _load_vocab()

    word = _normalize_token(word.lower().strip())
    if not word or len(word) < 2:
        return 0

    if word not in _vocab:
        if not create:
            return 0
        _assign_word_id(word)
        _save_vocab()

    return _vocab[word]


def id_to_word(wid: int) -> str:
    """Reverse lookup: ID → word."""
    if not _vocab_loaded:
        _load_vocab()
    return _vocab_inverse.get(wid, '')


# Stopwords — common words that don't carry intent signal
_STOPWORDS = frozenset([
    'the', 'and', 'for', 'this', 'that', 'with', 'from', 'have',
    'but', 'not', 'are', 'was', 'were', 'been', 'being', 'has',
    'had', 'its', 'you', 'your', 'can', 'will', 'would', 'could',
    'should', 'what', 'when', 'where', 'which', 'who', 'how', 'why',
    'just', 'now', 'also', 'too', 'very', 'more', 'most', 'some',
    'any', 'all', 'each', 'every', 'both', 'few', 'other', 'such',
    'only', 'same', 'than', 'then', 'there', 'here', 'these', 'those',
])

_COMMON_INTENT_WORDS = frozenset([
    'audit', 'stale', 'data', 'point', 'points', 'clean', 'cleanup',
    'garbage', 'file', 'files', 'sim', 'sims', 'simulate', 'simulation',
    'effective', 'effectively', 'prompt', 'prompts', 'numeric', 'number',
    'encoding', 'encode', 'decoding', 'decode', 'touch', 'touches',
    'touching', 'per', 'work', 'works', 'working', 'proper', 'properly',
    'make', 'check', 'bug', 'bugs', 'profile', 'profiles', 'context',
    'thought', 'completer', 'completion', 'engine', 'vector', 'matrix',
    'predict', 'prediction', 'registry', 'heat', 'journal', 'composition',
    'binding', 'module', 'modules', 'codebase', 'training', 'surface',
    'intent', 'file_sim', 'tc_sim_engine', 'intent_numeric', 'seed',
    'prompt_journal', 'chat_compositions', 'predict_files', 'record_touch',
    'self_score', 'operator', 'telemetry', 'repair', 'heal', 'merge',
])


def _looks_noisy_token(token: str) -> bool:
    """Detect UIA/echo-style duplication inside a token."""
    if len(token) < 4:
        return False
    return bool(
        re.search(r'(.)\1{2,}', token)
        or re.search(r'(.{2,4})\1+', token)
    )


def _collapse_char_runs(token: str) -> str:
    return re.sub(r'(.)\1+', r'\1', token)


def _collapse_repeated_ngrams(token: str, max_ngram: int = 4) -> str:
    """Collapse immediate repeated substrings like `owowow` -> `ow`."""
    changed = True
    while changed:
        changed = False
        upper = min(max_ngram, max(len(token) // 2, 1))
        for size in range(upper, 1, -1):
            collapsed = re.sub(rf'(.{{{size}}})\1+', r'\1', token)
            if collapsed != token:
                token = collapsed
                changed = True
    return token


def _looks_like_clean_word(word: str) -> bool:
    if len(word) < 3:
        return False
    if not re.fullmatch(r'[a-z_][a-z0-9_]*', word):
        return False
    if _looks_noisy_token(word):
        return False
    return True


def _build_normalization_lexicon() -> set[str]:
    """Build a correction lexicon from common intent words and clean vocab."""
    global _lexicon_cache
    if _lexicon_cache is not None:
        return _lexicon_cache

    lexicon = set(_COMMON_INTENT_WORDS)
    for word in _vocab:
        if _looks_like_clean_word(word):
            lexicon.add(word)
    if _matrix_loaded:
        for file_key in _matrix:
            canonical = canonicalize_file_key(file_key)
            for token in re.findall(r'[a-z_][a-z0-9_]*', canonical):
                if len(token) >= 3:
                    lexicon.add(token)
    _lexicon_cache = lexicon
    return lexicon


def _best_lexicon_match(token: str, lexicon: set[str], cutoff: float = 0.74) -> str | None:
    if len(token) < 4:
        return None
    matches = difflib.get_close_matches(token, list(lexicon), n=1, cutoff=cutoff)
    if not matches:
        return None
    match = matches[0]
    if abs(len(match) - len(token)) > 3:
        return None
    if token[0] != match[0] and token[-1] != match[-1]:
        return None
    return match


def _normalize_token(token: str) -> str:
    """Normalize a token by collapsing duplicated UIA/echo patterns."""
    token = token.lower().strip('_')
    if not token:
        return token
    if '_' in token:
        return '_'.join(
            part for part in (_normalize_token(part) for part in token.split('_')) if part
        )

    noisy = _looks_noisy_token(token)
    candidate = _collapse_char_runs(token)
    candidate = _collapse_repeated_ngrams(candidate)
    candidate = _collapse_char_runs(candidate)
    candidate = re.sub(r'[^a-z0-9]+', '', candidate)
    if not candidate:
        return ''
    if len(candidate) < 3:
        return candidate

    lexicon = _build_normalization_lexicon()
    if candidate in lexicon:
        return candidate
    if noisy or candidate != token:
        match = _best_lexicon_match(candidate, lexicon)
        if match:
            return match
    if len(candidate) >= 6:
        match = _best_lexicon_match(candidate, lexicon, cutoff=0.84)
        if match:
            return match
    return candidate


def normalize_prompt_text(text: str) -> str:
    """Normalize echoed prompt text into cleaner tokens for training/prediction."""
    chunks = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*|[^a-zA-Z0-9_]+', text.lower())
    normalized = []
    for chunk in chunks:
        if re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*', chunk):
            normalized.append(_normalize_token(chunk))
        else:
            normalized.append(chunk)
    return re.sub(r'\s+', ' ', ''.join(normalized)).strip()


def _should_skip_file_key(file_key: str) -> bool:
    file_key = file_key.lower().strip()
    return (
        not file_key
        or file_key.startswith('.')
        or file_key in {'__init__', '__main__'}
        or file_key.startswith(('test_', '_tmp_', '_fix_', 'audit_'))
        or file_key.startswith(('stress_test', 'deep_test'))
        or file_key in {'test_all', 'test_public_release'}
    )


def canonicalize_file_key(file_path: str) -> str:
    """Normalize versioned/verbose file stems into a stable learned key."""
    stem = Path(file_path).stem.lower().strip()
    if not stem:
        return stem

    stem = stem.split('__', 1)[0]
    stem = re.sub(r'[^a-z0-9_\.]+', '_', stem)
    stem = re.sub(r'_s\d{3}(?=_|$)', '', stem)
    stem = re.sub(r'_seq\d+(?=_|$)', '', stem)
    stem = re.sub(r'_v\d+(?=_|$)', '', stem)
    stem = re.sub(r'_d\d{4}(?=_|$)', '', stem)
    stem = re.sub(r'_[a-z]{0,2}lc_[a-z0-9_]+$', '', stem)
    stem = re.sub(r'_+', '_', stem).strip('_')
    parts = [part for part in stem.split('_') if part]
    while len(parts) > 1 and len(parts[-1]) <= 2:
        parts.pop()
    stem = '_'.join(parts)
    return stem or Path(file_path).stem.lower()


def _extract_prompt_match_terms(text: str) -> set[str]:
    """Extract normalized prompt terms for lexical file-name matching."""
    normalized = normalize_prompt_text(text)
    terms: set[str] = set()
    for token in re.findall(r'[a-z_][a-z0-9_]*', normalized):
        if '_' in token:
            terms.add(token)
            for part in token.split('_'):
                if len(part) >= 3 and part not in _STOPWORDS:
                    terms.add(part)
            continue
        if len(token) >= 3 and token not in _STOPWORDS:
            terms.add(token)
    return terms


def _file_term_doc_frequency(file_keys: list[str]) -> dict[str, int]:
    """Count how often each canonical file-name segment appears across files."""
    frequencies: dict[str, int] = defaultdict(int)
    for file_key in file_keys:
        canonical = canonicalize_file_key(file_key)
        seen_terms = {part for part in canonical.split('_') if len(part) >= 3}
        for term in seen_terms:
            frequencies[term] += 1
    return dict(frequencies)


def _lexical_file_prior(file_key: str, normalized_prompt: str,
                        prompt_terms: set[str], term_doc_freq: dict[str, int],
                        total_files: int) -> float:
    """Small file-name prior so explicit prompt mentions can beat stale history."""
    canonical = canonicalize_file_key(file_key)
    if _should_skip_file_key(canonical):
        return 0.0

    prior = 0.0
    phrase = canonical.replace('_', ' ')
    segments = [part for part in canonical.split('_') if len(part) >= 3]
    overlap = [part for part in segments if part in prompt_terms]

    if canonical in prompt_terms:
        prior += 0.04
    if len(segments) > 1 and phrase in normalized_prompt:
        prior += 0.06

    for term in overlap:
        idf = math.log(1 + (total_files / max(1, term_doc_freq.get(term, 1))))
        prior += 0.014 * min(idf, 4.0)

    if len(overlap) >= 2:
        prior += 0.02

    return round(min(prior, 0.14), 4)


def _heal_surface() -> None:
    """Merge noisy historical vocab/file keys into canonical forms."""
    global _matrix, _touch_counts, _surface_healed, _lexicon_cache
    if _surface_healed:
        return

    _surface_healed = True
    if not _vocab_loaded:
        _load_vocab()
    if not _matrix_loaded:
        _load_matrix()

    vocab_changed = False
    original_vocab = list(_vocab.items())
    wid_remap: dict[int, int | None] = {}
    for word, wid in original_vocab:
        canonical = _normalize_token(word)
        if canonical == word:
            continue
        vocab_changed = True
        if len(canonical) < 3 or canonical in _STOPWORDS:
            wid_remap[wid] = None
        else:
            wid_remap[wid] = _assign_word_id(canonical)

    if wid_remap:
        for word, wid in original_vocab:
            if wid in wid_remap:
                _vocab.pop(word, None)
                _vocab_inverse.pop(wid, None)
        for file_key, weights in list(_matrix.items()):
            merged: dict[int, float] = {}
            for wid, weight in weights.items():
                target = wid_remap.get(wid, wid)
                if target is None:
                    continue
                merged[target] = merged.get(target, 0.0) + float(weight)
            _matrix[file_key] = merged

    canonical_matrix: dict[str, dict[int, float]] = {}
    canonical_counts: dict[str, int] = {}
    file_keys_changed = False
    for file_key, weights in _matrix.items():
        canonical_key = canonicalize_file_key(file_key)
        if _should_skip_file_key(canonical_key):
            file_keys_changed = True
            continue
        if canonical_key != file_key:
            file_keys_changed = True
        bucket = canonical_matrix.setdefault(canonical_key, {})
        for wid, weight in weights.items():
            bucket[wid] = bucket.get(wid, 0.0) + float(weight)
        canonical_counts[canonical_key] = canonical_counts.get(canonical_key, 0) + int(_touch_counts.get(file_key, 0))

    if file_keys_changed:
        _matrix = canonical_matrix
        _touch_counts = canonical_counts

    if vocab_changed or file_keys_changed:
        _lexicon_cache = None
        _save_vocab()
        _save_matrix()


def tokenize(text: str) -> list[int]:
    """Convert text to list of word IDs."""
    if not _vocab_loaded:
        _load_vocab()
    # Extract words (alphanumeric + underscores, preserve snake_case)
    words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', normalize_prompt_text(text))
    tokens = []
    for w in words:
        if len(w) >= 3 and w not in _STOPWORDS:
            tokens.append(word_to_id(w))
    return tokens


def prompt_to_vector(text: str) -> dict[int, float]:
    """Convert prompt text to sparse vector (word_id → weight).
    
    Uses TF weighting: weight = log(1 + count) / sqrt(total_words)
    Returns dict for sparse representation (most entries are 0).
    """
    tokens = tokenize(text)
    if not tokens:
        return {}
    
    # Count occurrences
    counts: dict[int, int] = defaultdict(int)
    for t in tokens:
        if t > 0:
            counts[t] += 1
    
    # TF weighting with sqrt normalization
    total = math.sqrt(len(tokens))
    vector = {}
    for wid, count in counts.items():
        vector[wid] = math.log(1 + count) / total
    
    return vector


# ── Correlation Matrix ─────────────────────────────────────────────────────

# Structure: {file_key: {word_id: weight}}
# Each file has a learned vector of word associations
_matrix: dict[str, dict[int, float]] = {}
_touch_counts: dict[str, int] = {}  # how many times each file was touched
_matrix_loaded: bool = False


def _load_matrix():
    """Load correlation matrix from disk."""
    global _matrix, _touch_counts, _matrix_loaded
    if MATRIX_PATH.exists():
        data = json.loads(MATRIX_PATH.read_text(encoding='utf-8'))
        # Convert string keys back to ints for word IDs
        _matrix = {}
        for file_key, weights in data.get('matrix', {}).items():
            _matrix[file_key] = {int(k): v for k, v in weights.items()}
        _touch_counts = data.get('touch_counts', {})
    _matrix_loaded = True


def _save_matrix():
    """Persist correlation matrix to disk."""
    MATRIX_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Convert int keys to strings for JSON
    serializable = {}
    for file_key, weights in _matrix.items():
        serializable[file_key] = {str(k): v for k, v in weights.items()}
    MATRIX_PATH.write_text(json.dumps({
        'matrix': serializable,
        'touch_counts': _touch_counts,
        'updated': datetime.now(timezone.utc).isoformat(),
        'vocab_size': len(_vocab),
        'file_count': len(_matrix),
    }, ensure_ascii=False, indent=1), encoding='utf-8')


def record_touch(prompt_text: str, files_touched: list[str], learning_rate: float = 0.1):
    """Record that these files were touched after this prompt.
    
    This is the training signal — we learn which words correlate with which files.
    Learning rate controls how fast we update (0.1 = blend 10% new signal).
    """
    global _matrix, _touch_counts
    if not _matrix_loaded:
        _load_matrix()
    _heal_surface()
    
    prompt_vec = prompt_to_vector(prompt_text)
    if not prompt_vec:
        return
    
    for file_path in files_touched:
        # Normalize file key (just the filename stem)
        file_key = canonicalize_file_key(file_path)
        if _should_skip_file_key(file_key):
            continue
        
        # Skip meta-files that pollute the matrix with self-referential noise.
        # test_*, _tmp_*, audit_*, _fix_* dominate predictions because they get
        # touched every time we write infrastructure about infrastructure.
        fk_lower = file_key.lower()
        if _should_skip_file_key(fk_lower):
            continue
        
        # Strip pigeon prefixes for cleaner matching
        # e.g., "管w_cpm_s020_v003" → "copilot_prompt_manager" if possible
        # For now, keep the stem as-is
        
        # Initialize if new file
        if file_key not in _matrix:
            _matrix[file_key] = {}
            _touch_counts[file_key] = 0
        
        _touch_counts[file_key] += 1
        
        # Update weights: exponential moving average
        for wid, weight in prompt_vec.items():
            old = _matrix[file_key].get(wid, 0.0)
            _matrix[file_key][wid] = old * (1 - learning_rate) + weight * learning_rate
    
    # Log the touch for debugging/replay
    TOUCH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TOUCH_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps({
            'ts': datetime.now(timezone.utc).isoformat(),
            'prompt_preview': prompt_text[:100],
            'files': [canonicalize_file_key(f) for f in files_touched],
            'vector_size': len(prompt_vec),
        }, ensure_ascii=False) + '\n')
    
    _save_matrix()


def predict_files(prompt_text: str, top_n: int = 5) -> list[tuple[str, float]]:
    """Predict which files are relevant to this prompt.
    
    Returns: list of (file_key, relevance_score) sorted by score descending.
    This is the numeric alternative to LLM-based context selection.
    """
    if not _matrix_loaded:
        _load_matrix()
    _heal_surface()
    
    if not _matrix:
        return []
    
    prompt_vec = prompt_to_vector(prompt_text)
    if not prompt_vec:
        return []

    normalized_prompt = normalize_prompt_text(prompt_text)
    prompt_terms = _extract_prompt_match_terms(normalized_prompt)
    all_file_keys = list(_matrix.keys())
    total_files = max(1, len(all_file_keys))
    term_doc_freq = _file_term_doc_frequency(all_file_keys)
    
    scores: list[tuple[str, float]] = []
    
    for file_key, file_weights in _matrix.items():
        # Dot product between prompt vector and file weights
        score = 0.0
        for wid, prompt_weight in prompt_vec.items():
            if wid in file_weights:
                score += prompt_weight * file_weights[wid]
        
        # Normalize by file touch count (popular files shouldn't dominate)
        touch_count = _touch_counts.get(file_key, 1)
        # Dampening: log to reduce impact of very popular files
        score = score / math.log(1 + touch_count) if touch_count > 0 else score

        score += _lexical_file_prior(
            file_key,
            normalized_prompt,
            prompt_terms,
            term_doc_freq,
            total_files,
        )
        
        if score > 0.001:  # threshold for noise
            scores.append((file_key, round(score, 4)))
    
    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_n]


# ── Bigram Tracking (word pairs for phrase-level signals) ──────────────────

# Maps (wid1, wid2) → how many times this pair appears together
_bigrams: dict[str, int] = {}


def bigram_key(wid1: int, wid2: int) -> str:
    """Create consistent key for word pair (order matters)."""
    return f"{wid1}:{wid2}"


def extract_bigrams(text: str) -> list[tuple[int, int]]:
    """Extract adjacent word pairs for phrase-level matching."""
    tokens = tokenize(text)
    bigrams = []
    for i in range(len(tokens) - 1):
        if tokens[i] > 0 and tokens[i+1] > 0:
            bigrams.append((tokens[i], tokens[i+1]))
    return bigrams


# ── Analysis & Stats ───────────────────────────────────────────────────────

def get_stats() -> dict[str, Any]:
    """Return current state of the numeric surface."""
    if not _vocab_loaded:
        _load_vocab()
    if not _matrix_loaded:
        _load_matrix()
    _heal_surface()
    
    return {
        'vocab_size': len(_vocab),
        'files_tracked': len(_matrix),
        'total_touches': sum(_touch_counts.values()),
        'top_files': sorted(_touch_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        'recent_words': [(id_to_word(i), i) for i in list(_vocab_inverse.keys())[-20:]],
    }


def visualize_file(file_key: str, top_n: int = 10) -> list[tuple[str, float]]:
    """Show top word associations for a file."""
    if not _matrix_loaded:
        _load_matrix()
    _heal_surface()

    file_key = canonicalize_file_key(file_key)
    
    if file_key not in _matrix:
        return []
    
    weights = _matrix[file_key]
    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    return [(id_to_word(wid), round(weight, 4)) for wid, weight in sorted_weights[:top_n]]


def find_similar_files(file_key: str, top_n: int = 5) -> list[tuple[str, float]]:
    """Find files with similar word association patterns (cosine similarity)."""
    if not _matrix_loaded:
        _load_matrix()
    _heal_surface()

    file_key = canonicalize_file_key(file_key)
    
    if file_key not in _matrix:
        return []
    
    target = _matrix[file_key]
    target_norm = math.sqrt(sum(v*v for v in target.values()))
    if target_norm == 0:
        return []
    
    similarities = []
    for other_key, other_weights in _matrix.items():
        if other_key == file_key:
            continue
        
        # Cosine similarity
        dot = sum(target.get(wid, 0) * w for wid, w in other_weights.items())
        other_norm = math.sqrt(sum(v*v for v in other_weights.values()))
        if other_norm > 0:
            sim = dot / (target_norm * other_norm)
            if sim > 0.1:
                similarities.append((other_key, round(sim, 4)))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_n]


# ── Integration Hooks ──────────────────────────────────────────────────────

def hook_post_edit(prompt_text: str, files_changed: list[str]):
    """Call this after Copilot edits files based on a prompt.
    
    This is the training signal for the numeric surface.
    """
    if files_changed:
        record_touch(prompt_text, files_changed)


def select_context_numeric(prompt_text: str, top_n: int = 5) -> list[str]:
    """Use numeric surface for context selection instead of LLM.
    
    Returns list of file stems that are likely relevant.
    Falls back to empty list if not enough training data.
    """
    predictions = predict_files(prompt_text, top_n=top_n)
    if not predictions:
        return []
    
    # Only return predictions with reasonable confidence
    return [f for f, score in predictions if score > 0.01]


# ── CLI ────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == 'stats':
            stats = get_stats()
            print(f"Vocab: {stats['vocab_size']} words")
            print(f"Files: {stats['files_tracked']} tracked")
            print(f"Touches: {stats['total_touches']} total")
            print("\nTop files:")
            for f, c in stats['top_files']:
                print(f"  {f}: {c} touches")
        
        elif cmd == 'predict':
            prompt = ' '.join(sys.argv[2:])
            results = predict_files(prompt)
            print(f"Predicting for: '{prompt[:50]}...'")
            if results:
                for f, score in results:
                    print(f"  {f}: {score}")
            else:
                print("  (no predictions yet — need more training data)")
        
        elif cmd == 'visualize' and len(sys.argv) > 2:
            file_key = sys.argv[2]
            words = visualize_file(file_key)
            if words:
                print(f"Word associations for {file_key}:")
                for word, weight in words:
                    print(f"  {word}: {weight}")
            else:
                print(f"No data for {file_key}")
        
        elif cmd == 'similar' and len(sys.argv) > 2:
            file_key = sys.argv[2]
            similar = find_similar_files(file_key)
            if similar:
                print(f"Files similar to {file_key}:")
                for f, sim in similar:
                    print(f"  {f}: {sim}")
            else:
                print(f"No similar files found")
        
        elif cmd == 'train':
            # Manual training: py -m src.intent_numeric_seq001_v001 train "prompt text" file1 file2
            if len(sys.argv) > 3:
                prompt = sys.argv[2]
                files = sys.argv[3:]
                record_touch(prompt, files)
                print(f"Recorded: '{prompt[:40]}...' → {files}")
            else:
                print("Usage: train 'prompt text' file1 file2 ...")
        
        else:
            print("Usage: py -m src.intent_numeric_seq001_v001 [stats|predict <prompt>|visualize <file>|similar <file>|train <prompt> <files...>]")
    else:
        stats = get_stats()
        print(f"Intent Numeric Surface — {stats['vocab_size']} words, {stats['files_tracked']} files, {stats['total_touches']} touches")
        if stats['vocab_size'] == 0:
            print("\nNo training data yet. Use 'train' command or wire into learning loop.")
