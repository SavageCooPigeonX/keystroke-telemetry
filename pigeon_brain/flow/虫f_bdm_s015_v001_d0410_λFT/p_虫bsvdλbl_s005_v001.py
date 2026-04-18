"""虫f_bdm_s015_v001_d0410_λFT_bug_loader_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 49 lines | ~476 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from dataclasses import dataclass, field, asdict
from pathlib import Path

def load_active_bugs(root: Path) -> list[BugManifest]:
    """Read registry; extract bugs from β-suffix in filenames.

    Registry entries carry bugs encoded as `_β<codes>` in the path stem
    (e.g. `逆f_ba_s007_v005_d0404_λNU_βoc`). `bug_keys` field doesn't exist
    in the current schema — parse the suffix instead.
    """
    files = _load_registry(root)
    manifests: list[BugManifest] = []
    for f in files:
        path_str = f.get("path", "") or ""
        name = f.get("name", "") or f.get("abbrev", "") or ""
        if not name:
            continue
        m = _BETA_RE.search(path_str)
        if not m:
            continue
        beta_codes = m.group(1)  # e.g. "oc" or "ochi" or "oc"
        # Split composite codes (e.g. "ochi" → ["oc","hi"] isn't trivially parseable)
        # Treat the whole suffix as one key first; then match known 2-char keys
        bug_keys: list[str] = []
        remaining = beta_codes
        while remaining:
            matched = False
            for bk in BUG_SEVERITY:
                if remaining.startswith(bk):
                    bug_keys.append(bk)
                    remaining = remaining[len(bk):]
                    matched = True
                    break
            if not matched:
                break  # unknown suffix — skip rest

        tokens = f.get("tokens") or 0
        for bk in bug_keys:
            notes = f"{tokens} tokens" if bk == "oc" else f"detected in {name}"
            mid = f"{bk}:{name}"
            manifests.append(BugManifest(
                bug_id=mid,
                bug_type=bk,
                severity=BUG_SEVERITY.get(bk, 0.3),
                origin_module=name,
                notes=notes,
            ))
    return manifests
