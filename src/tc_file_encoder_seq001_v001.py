"""tc_file_encoder_seq001_v001 — semantic intent profiling per file.

Architecture:
  1. encode_file(path)      → extract keyword intent profile (TF-IDF-weighted)
  2. encode_directory(root) → bulk encode src/ → file_intent_profiles.json
  3. get_file_profile(name) → lookup module intent by name
  4. run_push_encoder()     → called by push cycle, measures intent dropoff
  5. match_prompt_to_files()→ numeric intent matching (prompt → ranked files)

Intent profiles live at: logs/file_intent_profiles.json
Intent dropoff log:       logs/intent_dropoff.jsonl

The numeric memory integration:
  - Each file gets a keyword weight vector
  - match_prompt_to_files() does dot-product of prompt tokens vs file vectors
  - intent_numeric.record_touch() then trains the word→file matrix on matches
  - Push cycle compares this run vs last run: files losing keyword overlap = intent dropoff
"""
from __future__ import annotations

import ast
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROFILES_PATH = ROOT / "logs" / "file_intent_profiles.json"
DROPOFF_LOG = ROOT / "logs" / "intent_dropoff.jsonl"

# Intent-boosted term categories — these carry extra weight in profile scoring
_INTENT_BOOST = {
    # pigeon system terms
    "pigeon", "registry", "compiler", "encoder", "resolver", "seq001",
    # code operation terms
    "import", "export", "record", "train", "predict", "score", "simulate",
    "emit", "inject", "extract", "parse", "classify", "encode", "decode",
    # operator workflow terms
    "operator", "profile", "intent", "buffer", "pause", "completion", "gemini",
    "baseline", "heat", "map", "surface", "numeric", "watcher", "tracker",
    # system health terms
    "fix", "patch", "audit", "shrink", "scan", "validate", "verify",
}

_STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "from", "into", "about",
    "are", "was", "will", "not", "have", "has", "had", "can", "its",
    "def", "cls", "self", "return", "none", "true", "false", "pass",
    "str", "int", "float", "list", "dict", "set", "tuple", "bool", "any",
    "import", "from", "try", "except", "if", "else", "elif", "while", "for",
    "class", "raise", "with", "as", "in", "is", "not", "and", "or",
}


# ── tokenization ──────────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    """Split text into intent-bearing tokens, expanding snake_case."""
    # snake_case → individual words
    expanded = re.sub(r'([a-z])([A-Z])', r'\1_\2', text)
    tokens = re.findall(r'[a-z][a-z0-9]{2,}', expanded.lower())
    return [t for t in tokens if t not in _STOPWORDS]


def _extract_ast_symbols(source: str) -> list[str]:
    """Extract function names, class names, docstrings from Python AST."""
    symbols: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return symbols
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(node.name)
            # Docstring
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                symbols.extend(_tokenize(node.body[0].value.value))
        elif isinstance(node, ast.ClassDef):
            symbols.append(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    symbols.append(t.id)
    return symbols


# ── single-file encoder ───────────────────────────────────────────────────

def encode_file(path: Path) -> dict[str, Any]:
    """Encode one file into an intent profile.
    
    Returns:
        {
          "name": str,          # module stem
          "path": str,          # relative path
          "keywords": {word: weight},
          "top_intents": [str], # top-10 intent terms
          "intent_score": float,# 0-1 how intent-rich this file is
          "encoded_at": str,
        }
    """
    try:
        source = path.read_text("utf-8", errors="ignore")
    except Exception:
        return {}

    # AST symbols (boosted weight)
    ast_symbols = _extract_ast_symbols(source)
    # Full text tokens
    all_tokens = _tokenize(source) + ast_symbols

    # Term frequency
    tf: dict[str, int] = {}
    for tok in all_tokens:
        tf[tok] = tf.get(tok, 0) + 1

    total = max(sum(tf.values()), 1)
    weights: dict[str, float] = {}
    for term, count in tf.items():
        freq = count / total
        boost = 2.5 if term in _INTENT_BOOST else 1.0
        # bonus for AST symbols (appear as both raw token and extracted)
        ast_bonus = 1.5 if term in {t.lower() for t in ast_symbols} else 1.0
        weights[term] = round(freq * boost * ast_bonus, 5)

    # Normalize
    max_w = max(weights.values(), default=1.0)
    if max_w > 0:
        weights = {k: round(v / max_w, 5) for k, v in weights.items()}

    # Top intents: prefer boosted terms
    top_terms = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:30]
    top_intents = [t for t, _ in top_terms if len(t) > 4][:10]

    # Intent score: fraction of top-20 tokens that are intent-boosted
    intent_hits = sum(1 for t, _ in top_terms[:20] if t in _INTENT_BOOST)
    intent_score = round(intent_hits / 20, 3)

    stem = path.stem.split("_seq0")[0]  # strip pigeon suffix for lookup

    return {
        "name": stem,
        "full_name": path.stem,
        "path": str(path.relative_to(ROOT)),
        "keywords": weights,
        "top_intents": top_intents,
        "intent_score": intent_score,
        "line_count": source.count("\n"),
        "encoded_at": datetime.now(timezone.utc).isoformat(),
    }


# ── directory encoder ─────────────────────────────────────────────────────

def encode_directory(
    root: Path = ROOT,
    patterns: list[str] | None = None,
    max_files: int = 400,
) -> dict[str, Any]:
    """Encode all matching files in the repo and save to PROFILES_PATH."""
    if patterns is None:
        patterns = ["src/**/*.py"]

    profiles: dict[str, dict] = {}
    count = 0
    for pattern in patterns:
        for p in sorted(root.glob(pattern)):
            if p.name.startswith("_") and "__init__" not in p.name:
                continue  # skip hidden/internal
            if count >= max_files:
                break
            prof = encode_file(p)
            if prof:
                profiles[prof["full_name"]] = prof
                count += 1

    PROFILES_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROFILES_PATH.write_text(
        json.dumps({"generated": datetime.now(timezone.utc).isoformat(),
                    "count": len(profiles), "profiles": profiles},
                   ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(f"[file_encoder] encoded {len(profiles)} files → {PROFILES_PATH.name}")
    return profiles


# ── lookup ────────────────────────────────────────────────────────────────

def get_file_profile(name: str) -> dict[str, Any]:
    """Look up a file's intent profile by module name or full pigeon name."""
    if not PROFILES_PATH.exists():
        return {}
    try:
        data = json.loads(PROFILES_PATH.read_text("utf-8", errors="ignore"))
        profiles = data.get("profiles", {})
        # exact match on full_name or name stem
        if name in profiles:
            return profiles[name]
        for key, prof in profiles.items():
            if prof.get("name") == name:
                return prof
        # fuzzy: startswith
        for key, prof in profiles.items():
            if key.startswith(name) or prof.get("name", "").startswith(name):
                return prof
    except Exception:
        pass
    return {}


# ── prompt → file matching ────────────────────────────────────────────────

def match_prompt_to_files(
    prompt: str,
    top_n: int = 8,
    profiles: dict[str, dict] | None = None,
) -> list[tuple[str, float]]:
    """Dot-product of prompt tokens vs file keyword vectors.
    
    Complements intent_numeric (word→file matrix) with semantic profile matching.
    Returns: [(module_name, score), ...] ranked by match strength.
    """
    if profiles is None:
        if not PROFILES_PATH.exists():
            return []
        try:
            data = json.loads(PROFILES_PATH.read_text("utf-8", errors="ignore"))
            profiles = data.get("profiles", {})
        except Exception:
            return []

    prompt_tokens = set(_tokenize(prompt))
    if not prompt_tokens:
        return []

    scores: dict[str, float] = {}
    for full_name, prof in profiles.items():
        kw = prof.get("keywords", {})
        name = prof.get("name", full_name)
        score = sum(kw.get(tok, 0.0) for tok in prompt_tokens)
        # boost by intent_score
        score *= (1 + prof.get("intent_score", 0))
        if score > 0:
            scores[name] = max(scores.get(name, 0), score)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    # Normalize
    total = sum(s for _, s in ranked) or 1.0
    return [(name, round(score / total, 4)) for name, score in ranked]


# ── push cycle: intent dropoff ────────────────────────────────────────────

def run_push_encoder(root: Path = ROOT, changed_files: list[str] | None = None) -> dict:
    """Called by push cycle. Encode changed files and measure intent dropoff.
    
    Intent dropoff = files that had high intent scores last push but score
    lower now (keywords dropped out = that intent thread is dying).
    """
    # Load previous profiles
    prev_profiles: dict[str, dict] = {}
    if PROFILES_PATH.exists():
        try:
            data = json.loads(PROFILES_PATH.read_text("utf-8", errors="ignore"))
            prev_profiles = data.get("profiles", {})
        except Exception:
            pass

    # Encode — only changed files if provided, else full directory
    if changed_files:
        new_profiles: dict[str, dict] = {}
        for rel in changed_files:
            p = root / rel
            if p.exists() and p.suffix == ".py":
                prof = encode_file(p)
                if prof:
                    new_profiles[prof["full_name"]] = prof
        # Merge with existing
        merged = {**prev_profiles, **new_profiles}
        PROFILES_PATH.parent.mkdir(parents=True, exist_ok=True)
        PROFILES_PATH.write_text(
            json.dumps({"generated": datetime.now(timezone.utc).isoformat(),
                        "count": len(merged), "profiles": merged},
                       ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
    else:
        new_profiles = encode_directory(root)
        merged = new_profiles

    # Intent dropoff detection
    dropoff_entries: list[dict] = []
    for full_name, prev in prev_profiles.items():
        curr = merged.get(full_name)
        if not curr:
            # File removed — complete dropoff
            dropoff_entries.append({
                "file": full_name,
                "type": "removed",
                "prev_score": prev.get("intent_score", 0),
                "curr_score": 0.0,
                "drift": prev.get("intent_score", 0),
            })
            continue
        prev_s = prev.get("intent_score", 0)
        curr_s = curr.get("intent_score", 0)
        drift = prev_s - curr_s
        if drift > 0.15:  # significant intent loss
            # Which keywords dropped?
            prev_kw = set(prev.get("keywords", {}).keys())
            curr_kw = set(curr.get("keywords", {}).keys())
            lost = list(prev_kw - curr_kw)[:10]
            dropoff_entries.append({
                "file": full_name,
                "type": "intent_loss",
                "prev_score": prev_s,
                "curr_score": curr_s,
                "drift": round(drift, 3),
                "lost_keywords": lost,
            })

    # Write dropoff log
    if dropoff_entries:
        DROPOFF_LOG.parent.mkdir(parents=True, exist_ok=True)
        with DROPOFF_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(),
                "entries": dropoff_entries,
            }) + "\n")
        print(f"[file_encoder] intent dropoff: {len(dropoff_entries)} files flagged")
    else:
        print("[file_encoder] no intent dropoff detected")

    return {
        "encoded": len(new_profiles),
        "dropoff_count": len(dropoff_entries),
        "dropoff": dropoff_entries[:5],
    }


# ── baseline collection ───────────────────────────────────────────────────

def collect_baseline_from_buffers(
    buffers: list[str],
    root: Path = ROOT,
) -> dict:
    """Build operator baseline profile from a list of typing buffers.
    
    Called by popup after 'Collect Baseline' button listen session.
    Returns baseline dict + writes logs/operator_baseline.json.
    """
    from collections import Counter

    baseline_path = root / "logs" / "operator_baseline.json"

    all_tokens: list[str] = []
    lengths: list[int] = []
    for buf in buffers:
        toks = _tokenize(buf)
        all_tokens.extend(toks)
        lengths.append(len(buf))

    if not all_tokens:
        return {"error": "no buffers"}

    # Token frequency
    tf = Counter(all_tokens)
    top_terms = [t for t, _ in tf.most_common(40) if len(t) > 3][:20]

    # Match to file profiles
    combined = " ".join(buffers)
    hot_files = match_prompt_to_files(combined, top_n=10)

    # Intent score for baseline
    intent_terms = [t for t in top_terms if t in _INTENT_BOOST]

    baseline = {
        "created": datetime.now(timezone.utc).isoformat(),
        "sample_count": len(buffers),
        "avg_buffer_len": round(sum(lengths) / len(lengths), 1) if lengths else 0,
        "top_terms": top_terms,
        "intent_terms": intent_terms,
        "hot_files": [{"name": n, "score": s} for n, s in hot_files],
        "total_tokens": len(all_tokens),
        "vocab_size": len(tf),
    }

    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(json.dumps(baseline, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[file_encoder] baseline locked: {len(buffers)} samples, {len(top_terms)} terms, {len(hot_files)} hot files")
    return baseline


# ── CLI ───────────────────────────────────────────────────────────────────

def main() -> int:
    import argparse
    p = argparse.ArgumentParser(description="tc_file_encoder — semantic intent profiling")
    p.add_argument("--encode", action="store_true", help="encode all src/ files now")
    p.add_argument("--file", help="encode a single file and print profile")
    p.add_argument("--match", help="match a prompt to files")
    p.add_argument("--top-n", type=int, default=8)
    args = p.parse_args()

    if args.file:
        prof = encode_file(Path(args.file))
        print(json.dumps({k: v for k, v in prof.items() if k != "keywords"}, indent=2))
        print(f"  keywords (top 15): {list(prof.get('keywords', {}).keys())[:15]}")
        return 0

    if args.encode:
        profs = encode_directory()
        print(f"encoded {len(profs)} files")
        return 0

    if args.match:
        results = match_prompt_to_files(args.match, top_n=args.top_n)
        for name, score in results:
            bar = "█" * int(score * 40)
            print(f"  {bar:<40} {score:.4f}  {name}")
        return 0

    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
