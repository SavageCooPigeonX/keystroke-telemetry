"""escalation_engine_seq001_v001_confidence_decomposed_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 56 lines | ~587 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def compute_module_confidence(
    module: str,
    entropy_conf: dict,
    dossier: dict,
    persistence: dict,
) -> float:
    """Composite confidence for whether a self-fix is safe.
    Combines: entropy confidence, bug persistence (more passes = more certain),
    dossier score, and bug-type fix readiness.
    """
    # entropy confidence (default 0.5 = unknown)
    e_conf = entropy_conf.get(module, 0.5)

    # persistence signal: chronic bugs with many appearances = well-understood
    p_entries = persistence.get(module, [])
    if p_entries:
        max_appearances = max(e.get('appearances', 0) for e in p_entries)
        is_chronic = any(e.get('status') == 'chronic' for e in p_entries)
        # chronic + 12 appearances = we KNOW this bug. the fix is well-characterized.
        persistence_conf = min(0.45, max_appearances * 0.03)
        if is_chronic:
            persistence_conf += 0.15
    else:
        persistence_conf = 0.0

    # dossier recurrence: repeated scans = well-known issue
    d = dossier.get(module, {})
    recur = d.get('recur', 0)
    recur_conf = min(0.25, recur * 0.04)

    # bug-type fix readiness: proven fix tools get a boost
    # hardcoded_import has auto_apply_import_fixes (battle-tested across 53 pushes)
    # over_hard_cap has the pigeon compiler split (proven pipeline)
    fix_readiness = 0.0
    for p in p_entries:
        bt = p.get('type', '')
        if bt == 'hardcoded_import':
            fix_readiness = max(fix_readiness, 0.25)  # auto_apply exists + tested
        elif bt == 'over_hard_cap':
            fix_readiness = max(fix_readiness, 0.15)  # split exists but needs DeepSeek
        elif bt == 'duplicate_docstring':
            fix_readiness = max(fix_readiness, 0.20)  # simple dedup
    for bk in d.get('bugs', []):
        if bk == 'hi':
            fix_readiness = max(fix_readiness, 0.25)
        elif bk == 'oc':
            fix_readiness = max(fix_readiness, 0.15)

    # composite: persistence and fix readiness dominate for well-scanned modules
    confidence = (0.15 * e_conf
                  + 0.35 * (0.5 + persistence_conf)
                  + 0.20 * (0.5 + recur_conf)
                  + 0.30 * (0.5 + fix_readiness))
    return round(min(1.0, confidence), 3)
