"""叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc_generate_narrative_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
import os

def generate_push_narrative(
    root: Path, intent: str, commit_hash: str, changed_py: list[str],
    registry: dict, rework_stats: dict | None = None,
    query_mem: dict | None = None, heat_map: dict | None = None,
    cross_context: dict | None = None,
) -> Path | None:
    """Build a narrative from file-agent voices → docs/push_narratives/."""
    api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    if not api_key or not changed_py:
        return None

    # Cap file briefs to avoid massive prompts that timeout
    file_briefs = _build_file_briefs(root, changed_py[:20], registry)
    if not file_briefs:
        return None

    # Load operator composition data for this session
    comp_snapshot = _load_composition_snapshot(root)

    prompt = _build_narrative_prompt(
        intent, file_briefs, rework_stats, query_mem,
        heat_map, cross_context, comp_snapshot)
    prose = _call_deepseek(prompt, api_key)
    if not prose:
        return None

    out_dir = root / 'docs' / 'push_narratives'
    out_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    out_path = out_dir / f'{today}_{commit_hash}.md'

    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    fl = '\n'.join(f'- `{b["path"]}`' for b in file_briefs)
    dw = comp_snapshot.get('deleted_words', []) if comp_snapshot else []
    dw_l = f'**Deleted words**: {", ".join(dw[:10])}  \n' if dw else ''
    hdr = (f'# Push Narrative — {commit_hash}\n\n**Intent**: {intent}  \n'
           f'**Date**: {now}  \n**Files**: {len(changed_py)}  \n{dw_l}\n{fl}\n\n---\n\n')
    out_path.write_text(hdr + prose + '\n', encoding='utf-8')
    return out_path
