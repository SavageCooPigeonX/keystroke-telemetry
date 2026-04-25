"""entropy_to_deepseek — full-loop orchestrator.

Flow:
  1. accumulate_entropy() → refresh logs/entropy_map.json
  2. get_high_entropy_targets() → pick top-N modules by red score
  3. resolve each module stem → concrete src/*.py path
  4. void_probe.probe_file() → counterfactual contract analysis
  5. file_sim.run_sim() → LLM grade (if API key) OR local cosine-only (dry)
  6. assemble DeepSeek-coder prompt: INTENT + SOURCE + VOID_PROBE + SIM_GRADE
  7. _call_deepseek() → surgical patch (or dry-run: just capture the prompt)
  8. write full transcript to logs/entropy_deepseek_transcript.jsonl

Invocation:
  python scripts/entropy_to_deepseek.py              # dry-run, 1 target, no API call
  python scripts/entropy_to_deepseek.py --top 3      # 3 targets
  python scripts/entropy_to_deepseek.py --live       # actually call DeepSeek
  python scripts/entropy_to_deepseek.py --intent "..." # override intent text
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
TRANSCRIPT = ROOT / 'logs' / 'entropy_deepseek_transcript.jsonl'


def _load_module(folder: str, pattern: str):
    matches = sorted((ROOT / folder).glob(f'{pattern}.py'))
    if not matches:
        return None
    path = matches[-1]
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = mod
    try:
        spec.loader.exec_module(mod)
        return mod
    except Exception as e:
        print(f'  [import failed] {path.name}: {e}')
        return None


def _resolve_stem_to_path(stem: str) -> Path | None:
    """Same resolver logic as deepseek_daemon._do_fix."""
    for folder in ('src', 'pigeon_compiler', 'pigeon_compiler/git_plugin', 'client', 'scripts'):
        matches = sorted((ROOT / folder).glob(f'{stem}*.py'))
        if matches:
            return matches[-1]
        # try prefix match — entropy keys sometimes are short like "enricher"
        matches = sorted((ROOT / folder).glob(f'*{stem}*.py'))
        if matches:
            return matches[0]
    return None


def _append_transcript(entry: dict):
    TRANSCRIPT.parent.mkdir(parents=True, exist_ok=True)
    entry['ts'] = datetime.now(timezone.utc).isoformat()
    with open(TRANSCRIPT, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def _build_deepseek_prompt(fpath: Path, intent: str, void_summary: str,
                           sim_grade: dict | None, entropy_info: dict) -> tuple[str, str]:
    """Return (system, user) for deepseek-coder."""
    source = fpath.read_text('utf-8', errors='ignore')
    src_lines = source.split('\n')
    # truncate to 400 lines like the daemon does
    if len(src_lines) > 400:
        source_trunc = '\n'.join(src_lines[:400]) + '\n# ... (truncated)'
    else:
        source_trunc = source

    sim_block = ''
    if sim_grade:
        sim_block = (
            f"\nSIM GRADE (file_sim lane):\n"
            f"  needs_change={sim_grade.get('needs_change')} "
            f"confidence={sim_grade.get('confidence')} "
            f"reason={sim_grade.get('reason', '')[:200]}\n"
        )

    entropy_block = (
        f"\nENTROPY CONTEXT:\n"
        f"  red_score={entropy_info.get('red'):.3f} "
        f"(higher = more uncertain, 0..1)\n"
        f"  avg_entropy={entropy_info.get('avg_entropy'):.3f} "
        f"samples={entropy_info.get('samples')}\n"
        f"  confidence_goal={entropy_info.get('confidence_goal')}\n"
    )

    system = (
        "You are DeepSeek-Coder acting as a uncertainty-reducing surgeon. "
        "A file has high entropy (Copilot has been uncertain about it repeatedly). "
        "You are given: the source, a void_probe report (which contracts would shatter "
        "if removed), and the entropy score. Your job: propose the MINIMAL surgical "
        "change that reduces uncertainty without expanding blast radius.\n\n"
        "Rules:\n"
        "- If fragility is high (>0.5), do NOT touch exported symbols — only internal refactor.\n"
        "- If blast_radius is 0, the file is isolated — safe to restructure.\n"
        "- Output surgical search-replace blocks:\n"
        "  <<<SEARCH\n  <exact context>\n  ===\n  <replacement>\n  >>>REPLACE\n"
        "- If nothing should change, output exactly: NO_CHANGES\n"
    )

    user = f"""INTENT: {intent}

FILE: {fpath.name}
{entropy_block}{sim_block}
{void_summary}

SOURCE:
```python
{source_trunc}
```

Apply the minimal entropy-reducing fix (or output NO_CHANGES)."""
    return system, user


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--top', type=int, default=1, help='number of high-entropy targets to process')
    ap.add_argument('--live', action='store_true', help='actually call DeepSeek (otherwise dry-run)')
    ap.add_argument('--intent', type=str, default='', help='override intent text')
    ap.add_argument('--threshold', type=float, default=0.35,
                    help='min red score to consider (default 0.35)')
    ap.add_argument('--skip-sim', action='store_true', help='skip file_sim grading step')
    args = ap.parse_args()

    print('=' * 70)
    print('entropy_to_deepseek — full loop')
    print('=' * 70)

    # ── stage 1: refresh entropy ──────────────────────────────────────────
    print('\n[1/5] refreshing entropy_map...')
    sys.path.insert(0, str(SRC))
    from entropy_shedding_seq001_v001 import accumulate_entropy, get_high_entropy_targets
    ent = accumulate_entropy(ROOT)
    print(f'      tracked_modules={ent.get("tracked_modules")} '
          f'global_H={ent.get("global_avg_entropy"):.4f} '
          f'edit_pair_modules={ent.get("edit_pair_modules")}')

    # ── stage 2: pick targets ────────────────────────────────────────────
    print(f'\n[2/5] picking top-{args.top} targets (red >= {args.threshold})...')
    # pull a generous pool — many entropy keys are phantom modules (mentioned
    # in responses but with no source file). We filter those out here.
    targets = get_high_entropy_targets(ROOT, threshold=args.threshold, limit=max(args.top * 10, 30))
    if not targets:
        print('      no targets above threshold — nothing to do')
        return 0

    # resolve each to a path, skip unresolvable
    resolved: list[tuple[dict, Path]] = []
    for t in targets:
        stem = t['module']
        p = _resolve_stem_to_path(stem)
        if p is None:
            print(f'      [skip] {stem}: no source file')
            continue
        resolved.append((t, p))
        if len(resolved) >= args.top:
            break
    if not resolved:
        print('      no resolvable targets — nothing to do')
        return 0

    for t, p in resolved:
        print(f'      -> {t["module"]:35s} red={t["red"]:.3f} -> {p.relative_to(ROOT)}')

    # ── stage 3+4+5: per-target loop ─────────────────────────────────────
    from void_probe_seq001_v001 import probe_file, format_probe_summary

    sim_mod = None if args.skip_sim else _load_module('src', 'file_sim_seq001_v005*')
    if sim_mod is None and not args.skip_sim:
        print('[warn] file_sim not loadable — continuing without sim grade')

    # only import deepseek if live
    deepseek_mod = None
    api_key = None
    if args.live:
        deepseek_mod = _load_module('src', 'deepseek_daemon_seq001_v001')
        if deepseek_mod:
            api_key = deepseek_mod._load_api_key()
            if not api_key:
                print('[warn] --live but no DEEPSEEK_API_KEY — falling back to dry-run')
                args.live = False

    for idx, (tgt_meta, fpath) in enumerate(resolved, 1):
        print(f'\n{"-" * 70}\n[target {idx}/{len(resolved)}] {fpath.relative_to(ROOT)}')
        transcript_entry = {
            'target': str(fpath.relative_to(ROOT)),
            'module': tgt_meta['module'],
            'entropy': tgt_meta,
        }

        # ── void probe ───────────────────────────────────────────────────
        print('\n[3/5] running void_probe...')
        probe = probe_file(fpath, ROOT)
        void_summary = format_probe_summary(probe)
        print(void_summary)
        transcript_entry['void_probe'] = probe

        # ── sim grade ────────────────────────────────────────────────────
        sim_grade = None
        intent_text = args.intent or (
            f"reduce uncertainty in {fpath.stem}: entropy red={tgt_meta['red']:.3f}. "
            f"most fragile contract: {probe['probes'][0]['symbol'] if probe.get('probes') else 'none'}."
        )
        transcript_entry['intent'] = intent_text

        if sim_mod and hasattr(sim_mod, 'run_sim') and not args.skip_sim:
            print('\n[4/5] running file_sim.run_sim...')
            try:
                sim_result = sim_mod.run_sim(intent_text, top_n=3, root=ROOT)
                # sim_result is a list of {stem, grade, confidence, reason, ...}
                if isinstance(sim_result, list):
                    # find the record matching our stem
                    stem_match = fpath.stem.split('_seq')[0]
                    for r in sim_result:
                        if stem_match in r.get('stem', ''):
                            sim_grade = r
                            break
                    if sim_grade is None and sim_result:
                        sim_grade = sim_result[0]
                transcript_entry['sim_grade'] = sim_grade
                if sim_grade:
                    print(f"      grade={sim_grade.get('grade')} "
                          f"conf={sim_grade.get('confidence')} "
                          f"10q={sim_grade.get('10q_score')}")
                else:
                    print('      (no grade returned)')
            except Exception as e:
                print(f'      sim failed: {e}')
                transcript_entry['sim_error'] = str(e)
        else:
            print('\n[4/5] skipped file_sim')

        # ── deepseek prompt ──────────────────────────────────────────────
        print('\n[5/5] assembling deepseek-coder prompt...')
        system, user = _build_deepseek_prompt(
            fpath, intent_text, void_summary, sim_grade, tgt_meta
        )
        transcript_entry['deepseek_prompt'] = {
            'system_len': len(system),
            'user_len': len(user),
            'user_preview': user[:800],
        }
        print(f'      system: {len(system)} chars, user: {len(user)} chars')

        if args.live and deepseek_mod and api_key:
            print('\n      [LIVE] calling deepseek-coder...')
            completion = deepseek_mod._call_deepseek(system, user, api_key, max_tokens=1500)
            transcript_entry['deepseek_response'] = {
                'received': completion is not None,
                'len': len(completion) if completion else 0,
                'text': completion,
            }
            if completion:
                print('\n      ── deepseek response ──')
                print(completion[:2000])
                print('      ── /deepseek response ──')
            else:
                print('      deepseek returned nothing')
        else:
            print('      (dry-run — prompt assembled but NOT sent)')
            print('\n      ── prompt preview (first 60 lines) ──')
            for line in user.split('\n')[:60]:
                print(f'      {line}')

        _append_transcript(transcript_entry)
        print(f'\n      transcript row appended -> {TRANSCRIPT.relative_to(ROOT)}')

    print(f'\n{"=" * 70}\ndone. transcript: {TRANSCRIPT.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
