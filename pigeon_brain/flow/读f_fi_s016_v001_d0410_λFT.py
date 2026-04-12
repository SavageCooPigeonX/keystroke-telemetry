# ┌──────────────────────────────────────────────┐
# │  file_interrogator — LLM learns each file    │
# │  stores autonomous_directive in node_memory  │
# │  agent reads pre-computed → zero token cost  │
# │  pigeon_brain/flow                           │
# └──────────────────────────────────────────────┘
"""
LLM reads each file ONCE, stores understanding in node_memory.file_understanding.
Autonomous agent reads the pre-computed directive → acts immediately, zero tokens.
Cache key = source hash — only re-interrogates if file changes.
Sweep priority: bug severity > heat > size.
"""

import json, os, re, hashlib, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
_MODEL_FALLBACK = "gemini-flash-latest"  # reliable fallback alias
_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
_NM_FILE = "pigeon_brain/node_memory.json"
_MAX_SRC = 5000  # chars — keeps cost low, still enough signal

_BUG_SEV = {"oc": 0.8, "hi": 0.7, "hc": 0.6, "de": 0.4, "dd": 0.3, "qn": 0.2}
_BETA_RE = re.compile(r"_β(\w+?)(?:_|\.py$|$)")


# ── Gemini call (no system context overhead — raw prompt only) ────────────────
def _call_gemini_model(prompt: str, api_key: str, model: str) -> tuple[str, bool]:
    """Returns (text, ok). ok=False on network/API error."""
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048},
    }
    url = _API_URL.format(model=model, key=api_key)
    req = urllib.request.Request(
        url, json.dumps(payload).encode(), {"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            r = json.loads(resp.read())
            parts = r.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            return (parts[0].get("text", "") if parts else ""), True
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:100]
        return f"ERR:{e.code}:{body}", (e.code not in (503, 429, 500, 404))
    except Exception as e:
        return f"ERR:{e}", False


def _call_gemini(prompt: str, api_key: str) -> str:
    text, ok = _call_gemini_model(prompt, api_key, _MODEL)
    if not ok:  # overloaded — try fallback
        text, ok = _call_gemini_model(prompt, api_key, _MODEL_FALLBACK)
    return text


# ── prompt builder ────────────────────────────────────────────────────────────
def _build_prompt(name: str, source: str, bugs: list, credit_avg: str) -> str:
    src_clip = source[:_MAX_SRC] + ("...[truncated]" if len(source) > _MAX_SRC else "")
    bugs_str = ", ".join(f"{b}(sev={_BUG_SEV.get(b,0)})" for b in bugs) or "none"
    return (
        "You are analyzing a Python module in a self-modifying autonomous codebase.\n"
        f"Module: {name}\nActive bugs: {bugs_str}\nLearning credit trend: {credit_avg}\n\n"
        f"Source:\n```python\n{src_clip}\n```\n\n"
        "Respond ONLY with valid JSON (no markdown fences, no explanation outside JSON):\n"
        '{"intent":"one sentence — what this module\'s core job is",'
        '"critical_path":true_or_false,'
        '"what_to_fix":["concrete action 1","concrete action 2"],'
        '"break_risk":["what breaks if you touch this"],'
        '"autonomous_directive":"the single most impactful code change to make RIGHT NOW — be specific about function name and what to change",'
        '"reasoning":"1-2 sentences why this directive"}'
    )


def _parse_json(text: str) -> dict | None:
    if not text or text.startswith("ERR:"):
        return None
    # Strip markdown fences (single-line or multi-line ```json ... ```)
    text = text.strip()
    text = re.sub(r"^```[a-z]*\s*", "", text)  # leading fence
    text = re.sub(r"\s*```\s*$", "", text)      # trailing fence
    text = text.strip()
    try:
        result = json.loads(text)
        if "intent" not in result and "autonomous_directive" not in result:
            return None
        return result
    except Exception:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                candidate = json.loads(m.group())
                if "intent" in candidate or "autonomous_directive" in candidate:
                    return candidate
            except Exception:
                pass
    return None


# ── node_memory I/O ───────────────────────────────────────────────────────────
def _load_nm(root: Path) -> dict:
    p = root / _NM_FILE
    return json.loads(p.read_text("utf-8")) if p.exists() else {}


def _save_nm(root: Path, nm: dict) -> None:
    (root / _NM_FILE).write_text(json.dumps(nm, indent=2, ensure_ascii=False), "utf-8")


def _credit_trend(nm: dict, node_name: str) -> str:
    entries = nm.get(node_name, {}).get("entries", [])[-5:]
    if not entries:
        return "no history"
    scores = [e.get("credit_score", 0) for e in entries]
    avg = round(sum(scores) / len(scores), 3)
    arrow = "↑" if scores[-1] > scores[0] else ("↓" if scores[-1] < scores[0] else "→")
    return f"avg={avg} {arrow}"


# ── public: agent reads this (zero cost) ─────────────────────────────────────
def get_file_understanding(root: Path, node_name: str) -> dict | None:
    """Pre-computed LLM understanding. Returns None if not interrogated yet."""
    return _load_nm(root).get(node_name, {}).get("file_understanding")


# ── interrogate single file ───────────────────────────────────────────────────
def interrogate_file(
    root: Path, file_path: str, node_name: str, bugs: list, force: bool = False
) -> dict | None:
    """LLM reads file, caches result by source hash. Skips if unchanged (unless force)."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print(f"  SKIP {node_name} — no GEMINI_API_KEY")
        return None

    src_path = root / file_path
    if not src_path.exists():
        return None

    source = src_path.read_text("utf-8", errors="replace")
    src_hash = hashlib.md5(source.encode()).hexdigest()[:12]

    nm = _load_nm(root)
    existing = nm.get(node_name, {}).get("file_understanding", {})
    if not force and existing.get("source_hash") == src_hash:
        return existing  # cache hit — file unchanged

    prompt = _build_prompt(node_name, source, bugs, _credit_trend(nm, node_name))
    raw = _call_gemini(prompt, api_key)

    understanding = _parse_json(raw)
    if not understanding:
        understanding = {
            "intent": "parse_failed",
            "autonomous_directive": raw[:300],
            "what_to_fix": [],
            "break_risk": [],
        }

    understanding.update({
        "source_hash": src_hash,
        "interrogated_at": datetime.now(timezone.utc).isoformat(),
        "model": _MODEL,
    })

    nm.setdefault(node_name, {})["file_understanding"] = understanding
    _save_nm(root, nm)
    return understanding


# ── sweep: prioritize by bug severity ────────────────────────────────────────
def _priority(entry: dict) -> float:
    bugs = [c for m in _BETA_RE.findall(entry.get("path", ""))
            for c in re.findall(r"[a-z]{2}", m)]
    return sum(_BUG_SEV.get(b, 0) for b in bugs)


def run_interrogation_sweep(
    root: Path, n: int = 10, force: bool = False
) -> list[dict]:
    """Interrogate top N files by bug priority. Each call costs 1 LLM request."""
    reg = json.loads((root / "pigeon_registry.json").read_text("utf-8"))
    entries = reg.get("files", reg) if isinstance(reg, dict) else reg
    entries = sorted(entries, key=_priority, reverse=True)

    results = []
    skipped = 0
    for entry in entries:
        if len(results) >= n:
            break
        path = entry.get("path", "")
        name = entry.get("name", Path(path).stem)
        if not path:
            continue
        bugs = [c for m in _BETA_RE.findall(path) for c in re.findall(r"[a-z]{2}", m)]
        if not bugs and not force:
            skipped += 1
            continue  # skip clean files unless forced
        result = interrogate_file(root, path, name, bugs, force=force)
        if result:
            directive = result.get("autonomous_directive", "?")
            intent = result.get("intent", "?")
            cached = "CACHE" if result.get("source_hash") and not force else "LLM"
            print(f"  [{cached}] {name[:35]:<35} bugs={bugs}")
            print(f"         intent: {intent[:70]}")
            print(f"         directive: {directive[:80]}")
            results.append({"node": name, "bugs": bugs, **result})

    print(f"\nSweep complete: {len(results)} interrogated, {skipped} clean files skipped.")
    return results


# ── agent briefing (human-readable) ──────────────────────────────────────────
def print_agent_briefing(root: Path, node_name: str) -> None:
    u = get_file_understanding(root, node_name)
    if not u:
        print(f"No understanding for '{node_name}' — run interrogate_file() first.")
        return
    print(f"\n{'='*60}")
    print(f"AGENT BRIEFING: {node_name}")
    print(f"{'='*60}")
    print(f"Intent:     {u.get('intent','?')}")
    print(f"Critical:   {u.get('critical_path','?')}")
    print(f"Fix:       ", "\n            ".join(u.get('what_to_fix', ['?'])))
    print(f"Break risk:", "\n            ".join(u.get('break_risk', ['?'])))
    print(f"\nDIRECTIVE:  {u.get('autonomous_directive','?')}")
    print(f"Why:        {u.get('reasoning','?')}")
    print(f"\nModel: {u.get('model','?')} | Hash: {u.get('source_hash','?')} | At: {u.get('interrogated_at','?')[:19]}")


if __name__ == "__main__":
    root = Path(".")
    print("File Interrogator — LLM sweep (top 5 buggy files)")
    print("Each file costs 1 Gemini call. Cached on source hash.\n")
    # force=True clears stale/failed cache entries
    results = run_interrogation_sweep(root, n=5, force=True)
    if results:
        print()
        print_agent_briefing(root, results[0]["node"])
