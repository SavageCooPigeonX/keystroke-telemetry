"""Gemini chat — project-aware LLM assistant for Pigeon Brain.

Calls Gemini API with live project context (graph, telemetry, modules,
operator prompt history) so the LLM sees what the operator sees in the UI.

Gemini can also write files to the codebase via structured action blocks.

Uses stdlib only (urllib) — no extra deps.
"""

import json
import os
import re
import urllib.request
import urllib.error
from pathlib import Path

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

# How many operator prompts to inject into Gemini context
MAX_PROMPT_HISTORY = 100


def _load_dotenv(root: Path | None = None) -> None:
    """Load .env file from project root into os.environ (stdlib only)."""
    if root is None:
        root = Path(__file__).resolve().parent.parent
    env_file = root / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        # Strip surrounding quotes
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
            val = val[1:-1]
        if key and key not in os.environ:
            os.environ[key] = val


def _get_api_key() -> str | None:
    _load_dotenv()
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


def _build_system_context(root: Path) -> str:
    """Build a system prompt with live project state."""
    parts = ["You are a project assistant embedded in Pigeon Brain — a neural graph visualizer for a keystroke telemetry codebase.",
             "You can see the same graph, modules, and telemetry the operator sees.",
             "Be concise. Use code when helpful. You know Python, React, and this codebase well.",
             "",
             "## File Writing Capability",
             "You can write files to the codebase. When you want to create or modify a file,",
             "include an ACTION BLOCK in your response using this exact format:",
             "",
             "```action",
             '{"action": "write_file", "path": "relative/path/to/file.py", "content": "file content here"}',
             "```",
             "",
             "Rules for file writes:",
             "- Paths must be relative to the project root (no .. traversal, no absolute paths)",
             "- You can create new files or overwrite existing ones",
             "- Only write to folders within the project: src/, pigeon_brain/, pigeon_compiler/, client/, docs/, logs/",
             "- The operator will see what you wrote and can review it",
             "- Include a brief explanation before each action block",
             "- You can include multiple action blocks in one response",
             ""]

    # Directory tree overview
    parts.append("## Project Structure:")
    parts.append("```")
    for d in sorted(set(p.parent.relative_to(root) for p in root.rglob("*.py")
                        if ".venv" not in str(p) and "__pycache__" not in str(p)
                        and "node_modules" not in str(p))):
        depth = len(d.parts)
        indent = "  " * depth
        parts.append(f"{indent}{d.name}/" if depth else f"{d}/")
    parts.append("```")
    parts.append("")

    # Graph summary
    dual = root / "pigeon_brain" / "dual_view.json"
    if dual.exists():
        try:
            d = json.loads(dual.read_text("utf-8"))
            nodes = d.get("nodes", [])
            edges = d.get("edges", [])
            parts.append(f"## Graph: {len(nodes)} nodes, {len(edges)} edges")
            danger = [n for n in nodes if (n.get("dual_score") or 0) > 0.3]
            if danger:
                parts.append("### Hot zones (dual_score > 0.3):")
                for n in sorted(danger, key=lambda x: -x.get("dual_score", 0))[:8]:
                    parts.append(f"  - {n['name']} (score={n['dual_score']:.3f}, deaths={n.get('agent_deaths',0)})")
            iso = [n for n in nodes if (n.get("in_degree") or 0) == 0 and (n.get("out_degree") or 0) == 0]
            if iso:
                parts.append(f"### Isolated nodes: {len(iso)}")
            parts.append("")
        except Exception:
            pass

    # Module list — organized by folder
    reg = root / "pigeon_registry.json"
    if reg.exists():
        try:
            r = json.loads(reg.read_text("utf-8"))
            files = r.get("files", [])
            # Group by folder
            folders: dict[str, list] = {}
            for f in files:
                p = f.get("path", "").replace("\\", "/")
                folder = "/".join(p.split("/")[:-1]) or "(root)"
                folders.setdefault(folder, []).append(f)
            parts.append(f"## Codebase: {len(files)} modules across {len(folders)} folders")
            parts.append("```")
            for folder in sorted(folders):
                parts.append(f"{folder}/")
                for m in sorted(folders[folder], key=lambda x: x.get("name", "")):
                    tok = m.get("tokens", 0)
                    ver = m.get("ver", 1)
                    desc = m.get("desc", "").replace("_", " ")
                    parts.append(f"  {m['name']} v{ver} ({tok}tok) — {desc}")
            parts.append("```")
            parts.append("")
        except Exception:
            pass

    # Infrastructure files (non-pigeon)
    infra = []
    for pattern in ("*.py", "client/*.py", "vscode-extension/*.py"):
        infra.extend(root.glob(pattern))
    infra = [f for f in infra if f.is_file() and f.stem not in ("__init__",)]
    if infra:
        parts.append("## Infrastructure (non-pigeon):")
        for f in sorted(infra, key=lambda x: x.name):
            parts.append(f"  - {f.relative_to(root)}")
        parts.append("")

    # Operator state
    op = root / "operator_profile.md"
    if op.exists():
        try:
            text = op.read_text("utf-8")[:800]
            parts.append("## Operator Profile (excerpt):")
            parts.append(text)
            parts.append("")
        except Exception:
            pass

    # Known issues from self-fix
    sf = root / "docs" / "self_fix"
    if sf.is_dir():
        reports = sorted(sf.glob("*.md"))[-3:]
        for rpt in reports:
            try:
                parts.append(f"## Self-fix report: {rpt.name}")
                parts.append(rpt.read_text("utf-8")[:400])
                parts.append("")
            except Exception:
                pass

    # Operator prompt history — last N prompts from the journal
    journal = root / "logs" / "prompt_journal.jsonl"
    if journal.exists():
        try:
            lines = journal.read_text("utf-8").strip().splitlines()
            entries = []
            for line in lines[-MAX_PROMPT_HISTORY:]:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    continue
            if entries:
                parts.append(f"## Operator Prompt History (last {len(entries)} messages):")
                for e in entries:
                    ts = e.get("ts", "?")[:19]
                    msg = e.get("msg", "")[:200]
                    state = e.get("cognitive_state", "?")
                    intent = e.get("intent", "?")
                    sig = e.get("signals", {})
                    wpm = sig.get("wpm", "") if isinstance(sig, dict) else ""
                    dele = sig.get("deletion_ratio", "") if isinstance(sig, dict) else ""
                    deleted = e.get("deleted_words", [])
                    line_parts = [f"[{ts}] ({state}/{intent})"]
                    if wpm:
                        line_parts.append(f"wpm={wpm}")
                    if dele:
                        line_parts.append(f"del={dele:.0%}" if isinstance(dele, (int, float)) else f"del={dele}")
                    if deleted:
                        line_parts.append(f"deleted={deleted}")
                    line_parts.append(f": {msg}")
                    parts.append("  " + " ".join(line_parts))
                parts.append("")
        except Exception:
            pass

    # AI Cognitive State — how the AI itself is performing
    _inject_ai_cognitive_state(root, parts)

    # Rework log — which AI responses landed vs missed
    _inject_rework_summary(root, parts)

    # Recurring queries — what the operator keeps asking twice
    _inject_query_memory(root, parts)

    return "\n".join(parts)


def _inject_ai_cognitive_state(root: Path, parts: list[str]) -> None:
    """Inject AI self-awareness: its own cognitive state and struggling modules."""
    try:
        from pigeon_brain.ai_cognitive_log import get_ai_state
        state = get_ai_state(root)
        if state.get("window_size", 0) > 0:
            parts.append("## AI Self-Assessment (Copilot needs therapy too)")
            parts.append(f"AI cognitive state: **{state.get('ai_state', 'unknown')}**")
            parts.append(f"Error rate: {state.get('error_rate', 0):.0%} | "
                         f"Miss rate: {state.get('miss_rate', 0):.0%} | "
                         f"Uncertainty: {state.get('uncertainty_rate', 0):.0%}")
            chains = state.get("fix_chains", [])
            if chains:
                parts.append("### Fix attempt chains (AI kept retrying):")
                for c in chains[:3]:
                    parts.append(f"  - {', '.join(c['modules'][:3])}: "
                                 f"{c['attempts']} attempts, {c['errors']} errors")
            struggling = state.get("struggling_modules", [])
            if struggling:
                parts.append("### Modules AI struggles with:")
                for m in struggling[:5]:
                    parts.append(f"  - {m['module']}: {m['attempts']} attempts, "
                                 f"{m['misses']} misses (badness={m['badness']})")
            parts.append("")
    except Exception:
        pass


def _inject_rework_summary(root: Path, parts: list[str]) -> None:
    """Inject AI response quality — how often did the human rework AI answers."""
    rework_path = root / "rework_log.json"
    if not rework_path.exists():
        return
    try:
        data = json.loads(rework_path.read_text("utf-8"))
        if not isinstance(data, list) or not data:
            return
        recent = data[-20:]  # Last 20 rework entries
        verdicts = {"ok": 0, "miss": 0, "partial": 0}
        for r in recent:
            v = r.get("verdict", "ok")
            verdicts[v] = verdicts.get(v, 0) + 1
        total = sum(verdicts.values()) or 1
        parts.append("## AI Response Quality (last 20 interactions):")
        parts.append(f"  OK: {verdicts['ok']}/{total} ({verdicts['ok']/total:.0%}) | "
                     f"Partial: {verdicts['partial']}/{total} | "
                     f"Miss: {verdicts['miss']}/{total}")
        misses = [r for r in recent if r.get("verdict") == "miss"]
        if misses:
            parts.append("  Recent misses (human deleted/reworked AI response):")
            for m in misses[-5:]:
                parts.append(f"    - query: {m.get('query_hint', '?')[:80]}")
        parts.append("")
    except Exception:
        pass


def _inject_query_memory(root: Path, parts: list[str]) -> None:
    """Inject recurring queries — what does the operator keep asking?"""
    qm_path = root / "query_memory.json"
    if not qm_path.exists():
        return
    try:
        data = json.loads(qm_path.read_text("utf-8"))
        queries = data.get("queries", []) if isinstance(data, dict) else []
        if not queries:
            return
        # Detect recurring queries by fingerprint frequency
        fp_counts: dict[str, list] = {}
        for q in queries:
            fp = q.get("fingerprint", "")
            if fp:
                fp_counts.setdefault(fp, []).append(q.get("text", ""))
        recurring = [(fp, texts) for fp, texts in fp_counts.items() if len(texts) >= 2]
        recurring.sort(key=lambda x: -len(x[1]))
        if recurring:
            parts.append("## Recurring Queries (operator keeps asking these):")
            for fp, texts in recurring[:8]:
                parts.append(f"  - ({len(texts)}x) {texts[-1][:100]}")
        # Abandoned themes / unsaid
        abandoned = data.get("abandoned_themes", []) if isinstance(data, dict) else []
        if abandoned:
            parts.append("### Unsaid thoughts (operator deleted these from prompts):")
            for u in abandoned[:5]:
                text = u.get("text", u) if isinstance(u, dict) else str(u)
                parts.append(f'  - "{text[:80]}"')
        if recurring or abandoned:
            parts.append("")
    except Exception:
        pass


# Allowed folder prefixes for write_file actions
_ALLOWED_PREFIXES = ("src/", "pigeon_brain/", "pigeon_compiler/", "client/", "docs/", "logs/",
                     "streaming_layer/", "vscode-extension/", "pigeon_brain/ui/")

_ACTION_BLOCK_RE = re.compile(r"```action\s*\n(.*?)\n```", re.DOTALL)


def parse_file_actions(response_text: str) -> list[dict]:
    """Extract file-write action blocks from a Gemini response.

    Returns list of {"action": "write_file", "path": ..., "content": ...} dicts.
    """
    actions = []
    for match in _ACTION_BLOCK_RE.finditer(response_text):
        try:
            data = json.loads(match.group(1))
            if data.get("action") == "write_file" and data.get("path") and data.get("content") is not None:
                actions.append(data)
        except (json.JSONDecodeError, TypeError):
            pass
    return actions


def execute_file_action(root: Path, action: dict) -> dict:
    """Execute a single file-write action. Returns a result dict.

    Security: validates path is relative, within allowed folders, no traversal.
    """
    rel_path = action.get("path", "")
    content = action.get("content", "")

    # Normalize path separators
    rel_path = rel_path.replace("\\", "/")

    # Security: reject absolute paths, traversal, and paths outside allowed folders
    if not rel_path or rel_path.startswith("/") or rel_path.startswith("\\"):
        return {"path": rel_path, "ok": False, "error": "Absolute paths not allowed"}
    if ".." in rel_path.split("/"):
        return {"path": rel_path, "ok": False, "error": "Path traversal not allowed"}

    # Check allowed prefix
    if not any(rel_path.startswith(p) for p in _ALLOWED_PREFIXES):
        return {"path": rel_path, "ok": False, "error": f"Path must start with one of: {', '.join(_ALLOWED_PREFIXES)}"}

    target = (root / rel_path).resolve()
    # Double-check the resolved path is within root
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return {"path": rel_path, "ok": False, "error": "Resolved path escapes project root"}

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"path": rel_path, "ok": True, "size": len(content)}
    except Exception as e:
        return {"path": rel_path, "ok": False, "error": str(e)}


def strip_action_blocks(text: str) -> str:
    """Remove action blocks from response text for clean display."""
    return _ACTION_BLOCK_RE.sub("", text).strip()


def chat(root: Path, messages: list[dict], selected_node: dict | None = None) -> str:
    """Send a chat message to Gemini with project context.

    Also fires a background forward→backward training cycle so nodes
    learn from every interaction.

    Args:
        root: project root
        messages: list of {"role": "user"|"model", "text": "..."}
        selected_node: currently selected node data from UI (optional)

    Returns:
        Gemini's response text, or an error string.
    """
    api_key = _get_api_key()
    if not api_key:
        return "Error: No GEMINI_API_KEY or GOOGLE_API_KEY environment variable set."

    system_ctx = _build_system_context(root)

    # Inject node learning memory into context
    system_ctx += _build_node_memory_context(root)

    if selected_node:
        system_ctx += f"\n\n## Currently selected node: {selected_node.get('name', '?')}\n"
        for k in ("ver", "tokens", "lines", "desc", "personality", "dual_score",
                   "human_hesitation", "agent_deaths", "agent_calls", "fears", "partners", "path"):
            if selected_node.get(k):
                system_ctx += f"  {k}: {selected_node[k]}\n"

    # Build Gemini API contents
    contents = []
    for m in messages:
        role = "user" if m.get("role") == "user" else "model"
        contents.append({"role": role, "parts": [{"text": m["text"]}]})

    payload = {
        "system_instruction": {"parts": [{"text": system_ctx}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 8192,
        },
    }

    url = API_URL.format(model=MODEL, key=api_key)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            candidates = result.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                response_text = parts[0].get("text", "") if parts else "No response generated."
            else:
                response_text = "No response from Gemini."
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        response_text = f"Gemini API error ({e.code}): {body}"
    except urllib.error.URLError as e:
        response_text = f"Network error: {e.reason}"
    except Exception as e:
        response_text = f"Error: {e}"

    # Fire background training cycle (non-blocking, best-effort)
    _fire_training_cycle(root, messages)

    return response_text


def _build_node_memory_context(root: Path) -> str:
    """Build context from node learning memory for Gemini injection."""
    try:
        memory_path = root / "pigeon_brain" / "node_memory.json"
        if not memory_path.exists():
            return ""
        memory = json.loads(memory_path.read_text(encoding="utf-8"))
        if not memory:
            return ""

        parts = ["\n\n## Node Learning Memory (accumulated from backward passes)"]
        # Sort by rolling score, show top performers and struggling nodes
        nodes_with_policy = [
            (name, rec.get("policy", {}))
            for name, rec in memory.items()
            if rec.get("policy", {}).get("sample_count", 0) > 0
        ]
        if not nodes_with_policy:
            return ""

        ranked = sorted(nodes_with_policy, key=lambda x: x[1].get("rolling_score", 0.5))

        # Struggling nodes (bottom 5)
        struggling = [n for n in ranked[:5] if n[1].get("rolling_score", 0.5) < 0.4]
        if struggling:
            parts.append("\n**Struggling nodes (need help):**")
            for name, pol in struggling:
                parts.append(
                    f"- {name}: score={pol.get('rolling_score', '?'):.3f}, "
                    f"directive='{pol.get('behavioral_directive', 'none')[:80]}'"
                )
                fails = pol.get("failure_patterns", [])
                if fails:
                    parts.append(f"  failures: {'; '.join(fails[:2])}")

        # Top performers (top 5)
        top = [n for n in reversed(ranked[-5:]) if n[1].get("rolling_score", 0.5) > 0.6]
        if top:
            parts.append("\n**Top performing nodes:**")
            for name, pol in top:
                parts.append(
                    f"- {name}: score={pol.get('rolling_score', '?'):.3f}, "
                    f"samples={pol.get('sample_count', 0)}"
                )

        total_samples = sum(p.get("sample_count", 0) for _, p in nodes_with_policy)
        parts.append(f"\n*{len(nodes_with_policy)} nodes trained, {total_samples} total backward passes*")
        return "\n".join(parts)
    except Exception:
        return ""


def _fire_training_cycle(root: Path, messages: list[dict]) -> None:
    """Best-effort training cycle from the latest user message."""
    try:
        # Extract the latest user message as task seed
        user_msgs = [m for m in messages if m.get("role") == "user"]
        if not user_msgs:
            return
        task_seed = user_msgs[-1].get("text", "")
        if len(task_seed) < 10:
            return

        import threading

        def _train():
            try:
                from pigeon_brain.flow.learning_loop_seq013_v001_d0327__perpetual_forward_backward_training_lc_deepseek_backprop import (
                    run_single_cycle, _load_state, _save_state,
                )
                state = _load_state(root)
                # Construct a synthetic journal entry from the chat message
                from datetime import datetime, timezone
                entry = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "msg": task_seed,
                    "cognitive_state": "focused",
                    "rework_score": 0.0,
                    "signals": {"deletion_ratio": 0.0},
                }
                result = run_single_cycle(root, entry, state, use_deepseek=False)
                state["total_cycles"] += 1
                _save_state(root, state)
            except Exception:
                pass  # Best effort — don't crash chat

        t = threading.Thread(target=_train, daemon=True)
        t.start()
    except Exception:
        pass
