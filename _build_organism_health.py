"""
Organism Health Synthesis — the root MANIFEST.md is the organism itself.

Reads every data pipeline in the codebase and writes a living health document.
Run: py _build_organism_health.py
Wire into git_plugin post-commit for auto-refresh.
"""
import json, os, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter

ROOT = Path(__file__).resolve().parent


def _sanitize(text: str) -> str:
    """Remove surrogate characters that break utf-8 encoding."""
    return text.encode('utf-8', errors='replace').decode('utf-8')


# ── helpers ──────────────────────────────────────────────────────────────────

def _load_json(path):
    try:
        return json.loads(path.read_text("utf-8"))
    except Exception:
        return None


def _load_jsonl(path, limit=None):
    try:
        lines = path.read_text("utf-8").strip().splitlines()
        if limit:
            lines = lines[-limit:]
        return [json.loads(l) for l in lines if l.strip()]
    except Exception:
        return []


def _ago(iso_ts):
    """Human-readable time-ago from ISO timestamp string."""
    try:
        if not iso_ts:
            return "never"
        dt = datetime.fromisoformat(iso_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        secs = int(delta.total_seconds())
        if secs < 0:
            return "just now"
        if secs < 60:
            return f"{secs}s ago"
        if secs < 3600:
            return f"{secs // 60}m ago"
        if secs < 86400:
            return f"{secs // 3600}h ago"
        return f"{secs // 86400}d ago"
    except Exception:
        return "?"


def _freshness_icon(iso_ts, stale_hours=24):
    """Green if recent, yellow if aging, red if stale."""
    try:
        dt = datetime.fromisoformat(iso_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        if hours < 1:
            return "🟢"
        if hours < stale_hours:
            return "🟡"
        return "🔴"
    except Exception:
        return "⚫"


def _count_py_files(root):
    """Count .py files by top-level folder, excluding junk."""
    skip = {"__pycache__", ".venv", "pigeon_code.egg-info", "node_modules", ".git", "build"}
    counts = Counter()
    total = 0
    for f in root.rglob("*.py"):
        rel = f.relative_to(root)
        parts = rel.parts
        if any(s in parts for s in skip):
            continue
        pkg_dir = f.parent / f.stem
        if pkg_dir.is_dir() and (pkg_dir / "__init__.py").exists():
            continue
        fname = f.name
        if fname.startswith("_tmp_") or fname.startswith("."):
            continue
        if f.parent == root and fname.startswith(("test_", "stress_test", "deep_test", "deep_stress")):
            continue
        folder = parts[0] if len(parts) > 1 else "(root)"
        counts[folder] += 1
        total += 1
    return total, counts


def _compliance_scan(root):
    """Return (compliant, over, details) for all .py files."""
    skip = {"__pycache__", ".venv", "pigeon_code.egg-info", "node_modules", ".git", "build"}
    compliant = 0
    over = []
    total = 0
    for f in root.rglob("*.py"):
        rel = f.relative_to(root)
        parts = rel.parts
        if any(s in parts for s in skip):
            continue
        # Skip monolith originals — a .py file whose stem matches a sibling
        # package directory (with __init__.py). Python ignores the .py when
        # both exist, so counting it is double-counting.
        pkg_dir = f.parent / f.stem
        if pkg_dir.is_dir() and (pkg_dir / "__init__.py").exists():
            continue
        # Skip temporary scripts, test harnesses, and compiler artifacts
        fname = f.name
        if fname.startswith("_tmp_") or fname.startswith("."):
            continue
        if f.parent == root and fname.startswith(("test_", "stress_test", "deep_test", "deep_stress")):
            continue
        total += 1
        try:
            lines = len(f.read_text("utf-8").splitlines())
        except Exception:
            continue
        if lines <= 200:
            compliant += 1
        else:
            over.append((str(rel).replace("\\", "/"), lines))
    over.sort(key=lambda x: -x[1])
    return total, compliant, over


# ── section builders ─────────────────────────────────────────────────────────

def _build_vitals(journal_entries, heat_map, reactor_state):
    """Operator cognitive vitals from latest journal + heat map."""
    lines = []
    lines.append("## Vitals\n")

    # From latest journal entry
    latest = journal_entries[-1] if journal_entries else {}
    signals = latest.get("signals", {})
    state = latest.get("state", latest.get("intent", "unknown"))
    wpm = signals.get("wpm", latest.get("wpm", "?"))
    del_ratio = signals.get("deletion_ratio", latest.get("deletion_ratio", "?"))
    hes = signals.get("hesitation_count", "?")
    session_n = latest.get("session_n", "?")
    ts = latest.get("ts", "")

    # Running summary from latest
    summary = latest.get("running_summary", {})
    total_prompts = summary.get("total_prompts", len(journal_entries))
    avg_wpm = summary.get("avg_wpm", "?")
    dominant = summary.get("dominant_state", state)
    baselines = summary.get("baselines", {})

    lines.append(f"| Metric | Value | Baseline |")
    lines.append(f"|---|---|---|")
    lines.append(f"| Cognitive State | **{dominant}** | — |")
    if isinstance(wpm, (int, float)):
        bl_wpm = baselines.get("avg_wpm", "?")
        lines.append(f"| WPM (latest) | {wpm:.1f} | {bl_wpm} |")
    if isinstance(del_ratio, (int, float)):
        bl_del = baselines.get("avg_del", "?")
        lines.append(f"| Deletion Ratio | {del_ratio:.1%} | {bl_del} |")
    lines.append(f"| Prompts Analyzed | {total_prompts} | — |")
    lines.append(f"| Session Message | #{session_n} | — |")
    lines.append(f"| Last Active | {_ago(ts)} ({_freshness_icon(ts)}) | — |")

    # Reactor fires
    if reactor_state:
        fires = reactor_state.get("total_fires", 0)
        lines.append(f"| Reactor Fires | {fires} | — |")

    lines.append("")
    return "\n".join(lines)


def _build_blood_flow(root):
    """Data pipeline health — every artery the organism depends on."""
    pipelines = [
        ("prompt_journal", "logs/prompt_journal.jsonl", "jsonl", "Enriched prompts"),
        ("chat_compositions", "logs/chat_compositions.jsonl", "jsonl", "Keystroke compositions"),
        ("edit_pairs", "logs/edit_pairs.jsonl", "jsonl", "Prompt → file pairings"),
        ("push_cycles", "logs/push_cycles.jsonl", "jsonl", "Push cycle reports"),
        ("os_keystrokes", "logs/os_keystrokes.jsonl", "jsonl", "OS-level keystrokes"),
        ("keystroke_live", "logs/keystroke_live.jsonl", "jsonl", "Live keystroke stream"),
        ("rework_log", "rework_log.json", "json_list", "AI answer quality"),
        ("file_heat_map", "file_heat_map.json", "json_dict", "Cognitive load per module"),
        ("file_profiles", "file_profiles.json", "json_dict", "Module consciousness"),
        ("pigeon_registry", "pigeon_registry.json", "json_dict", "Module registry"),
        ("execution_deaths", "execution_death_log.json", "json_list", "Electron failures"),
        ("context_veins_seq001_v001", "pigeon_brain/context_veins_seq001_v001.json", "json_dict", "Vein/clot health"),
        ("mutation_scores", "logs/mutation_scores.json", "json_dict", "Prompt mutation correlation"),
        ("task_queue", "task_queue.json", "json_dict", "Copilot task queue"),
        ("push_cycle_state", "logs/push_cycle_state.json", "json_dict", "Push cycle state"),
        ("reactor_state", "logs/cognitive_reactor_state.json", "json_dict", "Reactor state"),
    ]

    lines = []
    lines.append("## Blood Flow (Data Pipelines)\n")
    lines.append("| Pipeline | Entries | Size | Freshness | Role |")
    lines.append("|---|---:|---:|---|---|")

    for name, relpath, fmt, role in pipelines:
        path = root / relpath
        if not path.exists():
            lines.append(f"| {name} | — | — | ⚫ MISSING | {role} |")
            continue

        size = path.stat().st_size
        size_str = f"{size:,}" if size < 1_000_000 else f"{size / 1_000_000:.1f}M"
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        mtime_iso = mtime.isoformat()
        fresh = f"{_freshness_icon(mtime_iso)} {_ago(mtime_iso)}"

        if fmt == "jsonl":
            try:
                count = len(path.read_text("utf-8").strip().splitlines())
            except Exception:
                count = "?"
        elif fmt == "json_list":
            data = _load_json(path)
            count = len(data) if isinstance(data, list) else "?"
        elif fmt == "json_dict":
            data = _load_json(path)
            if isinstance(data, dict):
                # Try common patterns
                if "files" in data:
                    count = len(data["files"])
                elif "tasks" in data:
                    count = len(data["tasks"])
                elif "total" in data:
                    count = data["total"]
                else:
                    count = len(data)
            else:
                count = "?"
        else:
            count = "?"

        lines.append(f"| {name} | {count} | {size_str} | {fresh} | {role} |")

    lines.append("")
    return "\n".join(lines)


def _build_structure(root):
    """Module compliance and file structure."""
    total, compliant, over = _compliance_scan(root)
    total_files, folder_counts = _count_py_files(root)
    pct = (compliant / total * 100) if total else 0

    lines = []
    lines.append("## Structure (Module Compliance)\n")
    lines.append(f"**{total_files} Python files** across {len(folder_counts)} packages "
                 f"· **{compliant}/{total} compliant** ({pct:.0f}%) "
                 f"· **{len(over)} over cap**\n")

    lines.append("| Package | Files |")
    lines.append("|---|---:|")
    for folder, count in folder_counts.most_common():
        lines.append(f"| `{folder}` | {count} |")
    lines.append("")

    if over:
        lines.append("### Over-Cap Files (>200 lines)\n")
        lines.append("| File | Lines | Severity |")
        lines.append("|---|---:|---|")
        for filepath, lc in over[:20]:
            sev = "🔴 CRIT" if lc > 500 else ("🟠 WARN" if lc > 300 else "⚠️ OVER")
            lines.append(f"| `{filepath}` | {lc} | {sev} |")
        if len(over) > 20:
            lines.append(f"| ... | +{len(over)-20} more | |")
        lines.append("")

    return "\n".join(lines)


def _build_circulation(veins_data):
    """Dependency health — arteries, clots, vein scores."""
    if not veins_data:
        return "## Circulation\n\n*No context_veins_seq001_v001.json found.*\n"

    stats = veins_data.get("stats", {})
    arteries = veins_data.get("arteries", [])
    clots = veins_data.get("clots", [])

    lines = []
    lines.append("## Circulation (Dependency Health)\n")
    lines.append(f"**{stats.get('alive', '?')}/{stats.get('total_nodes', '?')} alive** "
                 f"· {stats.get('clots', '?')} clots "
                 f"· {stats.get('arteries', '?')} arteries "
                 f"· avg vein health: {stats.get('avg_vein_health', '?'):.2f} "
                 f"· {stats.get('total_edges', '?')} edges\n")

    if arteries:
        lines.append("### Critical Arteries (do NOT break)\n")
        lines.append("| Module | In-Degree | Vein Score |")
        lines.append("|---|---:|---:|")
        for a in arteries[:10]:
            lines.append(f"| `{a['module']}` | {a['in_degree']} | {a.get('vein_score', '?')} |")
        lines.append("")

    if clots:
        lines.append("### Clots (dead/bloated)\n")
        lines.append("| Module | Score | Signals |")
        lines.append("|---|---:|---|")
        for c in clots:
            sigs = ", ".join(c.get("clot_signals", []))
            lines.append(f"| `{c['module']}` | {c['clot_score']} | {sigs} |")
        lines.append("")

    return "\n".join(lines)


def _build_push_cycle(state, cycles):
    """Push cycle status."""
    lines = []
    lines.append("## Push Cycle\n")
    if state:
        lines.append(f"| Metric | Value |")
        lines.append(f"|---|---|")
        lines.append(f"| Total Cycles | {state.get('total_cycles', 0)} |")
        lines.append(f"| Last Commit | `{state.get('last_commit', '?')}` |")
        lines.append(f"| Last Sync Score | {state.get('last_sync_score', '?')} |")
        lines.append(f"| Journal Line | {state.get('last_journal_line', '?')} |")
        lines.append(f"| Updated | {_ago(state.get('updated_at', ''))} |")
    else:
        lines.append("*No push cycle state found.*")
    lines.append("")
    return "\n".join(lines)


def _build_prompt_consolidation(journal_entries):
    """Prompt evolution — intent distribution, rewrites, unsaid threads."""
    lines = []
    lines.append("## Prompt Consolidation\n")

    if not journal_entries:
        lines.append("*No journal entries.*\n")
        return "\n".join(lines)

    # Intent distribution
    intents = Counter()
    states = Counter()
    total_rewrites = 0
    total_deletions = 0
    deleted_words_all = []

    for entry in journal_entries:
        intent = entry.get("intent", "unknown")
        intents[intent] += 1
        state = entry.get("state", "unknown")
        states[state] += 1
        total_rewrites += len(entry.get("rewrites", []))
        deleted = entry.get("deleted_words", [])
        total_deletions += len(deleted)
        deleted_words_all.extend(deleted)

    n = len(journal_entries)
    lines.append(f"**{n} prompts** · {total_rewrites} rewrites "
                 f"· {total_deletions} deleted words\n")

    lines.append("### Intent Distribution\n")
    lines.append("| Intent | Count | % |")
    lines.append("|---|---:|---:|")
    for intent, count in intents.most_common():
        lines.append(f"| {intent} | {count} | {count/n*100:.0f}% |")
    lines.append("")

    lines.append("### Cognitive State Distribution\n")
    lines.append("| State | Count | % |")
    lines.append("|---|---:|---:|")
    for state, count in states.most_common():
        lines.append(f"| {state} | {count} | {count/n*100:.0f}% |")
    lines.append("")

    # Most deleted words (the unsaid)
    if deleted_words_all:
        word_counts = Counter(w.strip().lower() for w in deleted_words_all if w.strip())
        lines.append("### Unsaid Words (most deleted)\n")
        lines.append("| Word | Times Deleted |")
        lines.append("|---|---:|")
        for word, count in word_counts.most_common(15):
            lines.append(f"| {word} | {count} |")
        lines.append("")

    return "\n".join(lines)


def _build_rework_surface(rework_log):
    """AI response quality from rework scoring."""
    lines = []
    lines.append("## Rework Surface (AI Response Quality)\n")

    if not rework_log or not isinstance(rework_log, list):
        lines.append("*No rework data.*\n")
        return "\n".join(lines)

    verdicts = Counter(r.get("verdict", "?") for r in rework_log)
    avg_score = sum(r.get("rework_score", 0) for r in rework_log) / max(len(rework_log), 1)
    recent = rework_log[-10:]

    lines.append(f"**{len(rework_log)} responses scored** · avg rework score: {avg_score:.2f}\n")
    lines.append("| Verdict | Count | % |")
    lines.append("|---|---:|---:|")
    for v, c in verdicts.most_common():
        lines.append(f"| {v} | {c} | {c/len(rework_log)*100:.0f}% |")
    lines.append("")

    # Recent rework
    reworked = [r for r in rework_log if r.get("verdict", "ok") != "ok"]
    if reworked:
        lines.append(f"### Reworked Responses ({len(reworked)})\n")
        lines.append("| Time | Score | Del% | Query Hint |")
        lines.append("|---|---:|---:|---|")
        for r in reworked[-10:]:
            ts = _ago(r.get("ts", ""))
            score = r.get("rework_score", 0)
            dr = r.get("del_ratio", 0)
            hint = (r.get("query_hint", "") or "")[:60]
            lines.append(f"| {ts} | {score:.2f} | {dr:.0%} | {hint} |")
        lines.append("")

    return "\n".join(lines)


def _build_death_log(deaths):
    """Execution failures — electron death causes."""
    lines = []
    lines.append("## Death Log (Execution Failures)\n")

    if not deaths or not isinstance(deaths, list):
        lines.append("*No execution deaths recorded.*\n")
        return "\n".join(lines)

    lines.append(f"**{len(deaths)} deaths logged**\n")
    lines.append("| Module | Cause | Severity | Time |")
    lines.append("|---|---|---:|---|")
    for d in deaths[-10:]:
        mod = d.get("module", d.get("node", "?"))
        cause = d.get("cause", d.get("death_cause", "?"))
        sev = d.get("severity", d.get("score", "?"))
        ts = _ago(d.get("ts", d.get("timestamp", "")))
        lines.append(f"| `{mod}` | {cause} | {sev} | {ts} |")
    lines.append("")
    return "\n".join(lines)


def _build_hot_modules(heat_map):
    """Cognitive load hotspots from file_heat_map."""
    lines = []
    lines.append("## Hot Modules (Cognitive Load)\n")

    if not heat_map or not isinstance(heat_map, dict):
        lines.append("*No heat data.*\n")
        return "\n".join(lines)

    # Sort by avg_hes descending
    ranked = sorted(
        [(m, d) for m, d in heat_map.items() if isinstance(d, dict)],
        key=lambda x: x[1].get("avg_hes", 0),
        reverse=True,
    )

    lines.append(f"**{len(ranked)} modules tracked**\n")
    lines.append("| Module | Avg Hesitation | Avg WPM | Samples | Dominant State |")
    lines.append("|---|---:|---:|---:|---|")
    for mod, data in ranked[:15]:
        avg_hes = data.get("avg_hes", 0)
        avg_wpm = data.get("avg_wpm", 0)
        total = data.get("total", 0)
        # dominant state from samples
        samples = data.get("samples", [])
        if samples:
            sc = Counter(s.get("state", "?") for s in samples)
            dom_state = sc.most_common(1)[0][0]
        else:
            dom_state = "?"
        lines.append(f"| `{mod}` | {avg_hes:.3f} | {avg_wpm:.0f} | {total} | {dom_state} |")
    lines.append("")
    return "\n".join(lines)


def _build_task_queue(tq):
    """Active task queue."""
    lines = []
    lines.append("## Task Queue\n")
    tasks = (tq or {}).get("tasks", [])
    if not tasks:
        lines.append("*Queue empty.*\n")
        return "\n".join(lines)

    lines.append("| ID | Task | Status |")
    lines.append("|---|---|---|")
    for t in tasks:
        lines.append(f"| {t.get('id', '?')} | {t.get('title', t.get('desc', '?'))} | {t.get('status', '?')} |")
    lines.append("")
    return "\n".join(lines)


# ── main ─────────────────────────────────────────────────────────────────────

def build_health(root):
    """Synthesize the organism health document from all data sources."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Load everything
    journal = _load_jsonl(root / "logs/prompt_journal.jsonl")
    heat_map = _load_json(root / "file_heat_map.json")
    reactor_state = _load_json(root / "logs/cognitive_reactor_state.json")
    veins = _load_json(root / "pigeon_brain/context_veins_seq001_v001.json")
    push_state = _load_json(root / "logs/push_cycle_state.json")
    push_cycles = _load_jsonl(root / "logs/push_cycles.jsonl")
    rework_log = _load_json(root / "rework_log.json")
    task_queue = _load_json(root / "task_queue.json")
    deaths = _load_json(root / "execution_death_log.json")

    total_files, _ = _count_py_files(root)

    # Assemble
    sections = []
    sections.append(
        f"# ORGANISM HEALTH — keystroke-telemetry\n\n"
        f"*Auto-generated {now} · {total_files} Python files tracked · "
        f"{len(journal)} prompts analyzed*\n\n"
        f"**This document is the organism. Every data pipeline that flows "
        f"through this codebase is measured here. If it's not flowing, it's dying.**\n\n"
        f"---\n"
    )

    sections.append(_build_vitals(journal, heat_map, reactor_state))
    sections.append("---\n")
    sections.append(_build_blood_flow(root))
    sections.append("---\n")
    sections.append(_build_structure(root))
    sections.append("---\n")
    sections.append(_build_circulation(veins))
    sections.append("---\n")
    sections.append(_build_hot_modules(heat_map))
    sections.append("---\n")
    sections.append(_build_rework_surface(rework_log))
    sections.append("---\n")
    sections.append(_build_prompt_consolidation(journal))
    sections.append("---\n")
    sections.append(_build_push_cycle(push_state, push_cycles))
    sections.append("---\n")
    sections.append(_build_task_queue(task_queue))
    sections.append("---\n")
    sections.append(_build_death_log(deaths))
    sections.append("---\n")

    # Footer
    sections.append(
        f"\n*Regenerate: `py _build_organism_health.py` · "
        f"Wire into `git_plugin.py` post-commit for auto-refresh.*\n"
    )

    return "\n".join(sections)


BLOCK_START = '<!-- pigeon:organism-health -->'
BLOCK_END = '<!-- /pigeon:organism-health -->'


def build_prompt_block(root):
    """Condensed organism health for injection into copilot-instructions.md.

    ~2K chars max — only the signals Copilot needs to reason about the
    codebase as a living system. Full details stay in MANIFEST.md.
    """
    root = Path(root)
    now = datetime.now(timezone.utc)

    journal = _load_jsonl(root / "logs/prompt_journal.jsonl")
    heat_map = _load_json(root / "file_heat_map.json") or {}
    veins = _load_json(root / "pigeon_brain/context_veins_seq001_v001.json")
    deaths = _load_json(root / "execution_death_log.json") or []
    rework = _load_json(root / "rework_log.json") or []
    push_state = _load_json(root / "logs/push_cycle_state.json") or {}
    reactor_state = _load_json(root / "logs/cognitive_reactor_state.json") or {}
    total_files, _ = _count_py_files(root)
    total, compliant, over = _compliance_scan(root)

    L = [BLOCK_START, '## Organism Health', '',
         f'*Auto-injected {now.strftime("%Y-%m-%d %H:%M UTC")} · '
         f'{total_files} files · {compliant}/{total} compliant '
         f'({compliant/total*100:.0f}%)*', '']

    # Blood flow — only stale/dead pipelines
    stale = []
    pipelines = [
        ("prompt_journal", "logs/prompt_journal.jsonl"),
        ("chat_compositions", "logs/chat_compositions.jsonl"),
        ("edit_pairs", "logs/edit_pairs.jsonl"),
        ("context_veins_seq001_v001", "pigeon_brain/context_veins_seq001_v001.json"),
        ("execution_deaths", "execution_death_log.json"),
        ("push_cycle_state", "logs/push_cycle_state.json"),
    ]
    for name, relpath in pipelines:
        path = root / relpath
        if not path.exists():
            stale.append(f"- **{name}**: MISSING")
        else:
            hours = (now - datetime.fromtimestamp(
                path.stat().st_mtime, tz=timezone.utc)).total_seconds() / 3600
            if hours > 24:
                stale.append(f"- **{name}**: {_ago(datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat())} \U0001f534")
    if stale:
        L += ['**Stale pipelines:**'] + stale + ['']

    # Over-cap critical (>500 lines only)
    crit = [(f, lc) for f, lc in over if lc > 500]
    if crit:
        L.append(f'**Over-cap critical ({len(crit)}):** '
                 + ', '.join(f'`{f.split("/")[-1][:40]}` ({lc})' for f, lc in crit[:8]))
        L.append('')

    # Clots
    if veins:
        clots = veins.get("clots", [])
        if clots:
            L.append('**Clots:** ' + ', '.join(
                f'`{c["module"]}` ({", ".join(c.get("clot_signals", [])[:2])})'
                for c in clots))
            L.append('')
        stats = veins.get("stats", {})
        L.append(f'**Circulation:** {stats.get("alive", "?")}/{stats.get("total_nodes", "?")} alive '
                 f'· {stats.get("clots", 0)} clots · vein health {stats.get("avg_vein_health", 0):.2f}')
        L.append('')

    # Recent deaths
    recent_deaths = [d for d in deaths[-5:] if d.get("severity") in ("high", "critical")]
    if recent_deaths:
        L.append('**Recent deaths:** ' + ', '.join(
            f'`{d.get("module", "?")}` ({d.get("cause", "?")})' for d in recent_deaths))
        L.append('')

    # AI rework rate
    if rework:
        reworked = sum(1 for r in rework if r.get("verdict", "ok") != "ok")
        miss_rate = reworked / len(rework) if rework else 0
        L.append(f'**AI rework:** {reworked}/{len(rework)} responses needed rework '
                 f'({miss_rate*100:.0f}%)')
        L.append('')

    # Push cycle
    cycles = push_state.get("total_cycles", 0)
    sync = push_state.get("last_sync_score", "?")
    L.append(f'**Push cycles:** {cycles} · sync score: {sync} · '
             f'reactor fires: {reactor_state.get("total_fires", 0)}')
    L.append('')

    # Directive
    over_crit = len(crit)
    clot_n = len(veins.get("clots", [])) if veins else 0
    death_n = len(recent_deaths)
    if over_crit > 10 or clot_n > 3 or death_n > 3:
        L.append('> **Organism directive:** Multiple systems degraded. '
                 'Prioritize fixing clots and over-cap files before new features.')
    elif stale:
        L.append('> **Organism directive:** Some data pipelines are stale. '
                 'Check if post-commit hooks are firing.')
    else:
        L.append('> **Organism directive:** Systems nominal. Proceed with current task.')

    L.append(BLOCK_END)
    return '\n'.join(L)


def inject_organism_health(root):
    """Inject condensed organism health block into copilot-instructions.md."""
    root = Path(root)
    cp = root / '.github' / 'copilot-instructions.md'
    if not cp.exists():
        return False

    block = build_prompt_block(root)
    text = cp.read_text(encoding='utf-8')

    # Strip existing block
    import re
    pat = re.compile(
        r'(?ms)^\s*<!-- pigeon:organism-health -->\s*$\n.*?'
        r'^\s*<!-- /pigeon:organism-health -->\s*$\n?',
    )
    text = pat.sub('', text).rstrip() + '\n'

    # Insert before task-context (so Copilot sees organism state first)
    anchor = '<!-- pigeon:task-context -->'
    idx = text.find(anchor)
    if idx < 0:
        # Fallback: before operator-state
        anchor = '<!-- pigeon:operator-state -->'
        idx = text.find(anchor)
    if idx < 0:
        # Fallback: before auto-index
        anchor = '<!-- pigeon:auto-index -->'
        idx = text.find(anchor)

    if idx >= 0:
        text = text[:idx].rstrip() + '\n\n' + block + '\n\n' + text[idx:]
    else:
        text = text.rstrip() + '\n\n' + block + '\n'

    cp.write_text(_sanitize(text), encoding='utf-8')
    return True


if __name__ == "__main__":
    doc = build_health(ROOT)
    out = ROOT / "MANIFEST.md"
    out.write_text(_sanitize(doc), encoding="utf-8")
    print(f"[organism] Wrote {len(doc):,} chars to {out}")

    # Inject condensed block into Copilot prompt
    if inject_organism_health(ROOT):
        block = build_prompt_block(ROOT)
        print(f"[organism] Injected {len(block):,} chars into copilot-instructions.md")
    else:
        print("[organism] WARN: copilot-instructions.md not found")
