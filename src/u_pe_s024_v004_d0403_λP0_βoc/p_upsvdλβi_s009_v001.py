"""u_pe_s024_v004_d0403_λP0_βoc_injector_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
import re

def inject_query_block(root: Path, raw_query: str,
                       deleted_words: list | None = None,
                       cognitive_state: dict | None = None,
                       open_files: list | None = None) -> bool:
    """Enrich the prompt and write the <!-- pigeon:current-query --> block."""
    root = Path(root)
    cp = root / COPILOT_PATH
    if not cp.exists():
        return False

    enriched = enrich_prompt(root, raw_query, deleted_words, cognitive_state, open_files)
    if not enriched:
        return False

    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    # Extract COPILOT_QUERY line from enriched output to place it prominently
    copilot_query_line = ''
    unsaid_recon_line = ''
    rest_lines = []
    for line in enriched.splitlines():
        if line.startswith('COPILOT_QUERY:'):
            copilot_query_line = line
        elif line.startswith('UNSAID_RECONSTRUCTION:'):
            unsaid_recon_line = line.split(':', 1)[1].strip()
        else:
            rest_lines.append(line)
    rest = '\n'.join(rest_lines).strip()

    block = (
        f'{BLOCK_START}\n'
        f'## What You Actually Mean Right Now\n\n'
        f'*Enriched {now} · raw: "{raw_query[:80]}"*\n\n'
        + (f'**{copilot_query_line}**\n\n' if copilot_query_line else '')
        + (f'UNSAID_RECONSTRUCTION: {unsaid_recon_line}\n\n'
           if unsaid_recon_line and unsaid_recon_line.lower() != 'none'
           else '')
        + f'{rest}\n'
        f'{BLOCK_END}'
    )

    text = cp.read_text('utf-8')
    text, had_block = _strip_query_blocks(text)
    if had_block:
        idx = _find_insert_anchor(text)
        if idx >= 0:
            text = text[:idx] + block + '\n\n' + text[idx:]
        else:
            text = text.rstrip() + '\n\n' + block + '\n'
    else:
        idx = _find_insert_anchor(text)
        if idx >= 0:
            text = text[:idx] + block + '\n\n' + text[idx:]
        else:
            text = text.rstrip() + '\n\n---\n\n' + block + '\n'

    cp.write_text(text, 'utf-8')
    return True
