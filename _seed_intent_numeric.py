"""Seed the intent_numeric_seq001_v001 surface from historical data.

Reads:
- logs/prompt_journal.jsonl (what prompts were sent)
- git log (what files were touched in commits)

Creates correlations: prompt words → files touched after.
"""
import sys
sys.path.insert(0, '.')

import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from src._resolve import src_import

record_touch, get_stats = src_import("intent_numeric_seq001", "record_touch", "get_stats")

ROOT = Path('.')
JOURNAL_PATH = ROOT / 'logs' / 'prompt_journal.jsonl'


def load_journal() -> list[dict]:
    """Load prompt journal entries."""
    if not JOURNAL_PATH.exists():
        return []
    entries = []
    for line in JOURNAL_PATH.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except Exception:
            continue
    return entries


def get_recent_commits(n: int = 50) -> list[dict]:
    """Get recent commits with their files."""
    try:
        result = subprocess.run(
            ['git', 'log', f'-{n}', '--name-only', '--format=COMMIT:%H|%aI|%s'],
            capture_output=True, text=True, cwd=str(ROOT), encoding='utf-8'
        )
        if result.returncode != 0:
            return []
        
        commits = []
        current = None
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith('COMMIT:'):
                if current and current['files']:
                    commits.append(current)
                parts = line[7:].split('|', 2)
                current = {
                    'hash': parts[0] if len(parts) > 0 else '',
                    'ts': parts[1] if len(parts) > 1 else '',
                    'msg': parts[2] if len(parts) > 2 else '',
                    'files': [],
                }
            elif current and line.endswith('.py'):
                current['files'].append(line)
        
        if current and current['files']:
            commits.append(current)
        
        return commits
    except Exception as e:
        print(f'git error: {e}')
        return []


def correlate_prompts_to_commits(journal: list[dict], commits: list[dict]) -> list[tuple[str, list[str]]]:
    """Match prompts to files based on timestamp proximity.
    
    If a prompt was sent within 30 minutes before a commit, assume the commit
    was in response to that prompt.
    """
    correlations = []
    
    for commit in commits:
        commit_ts = commit.get('ts', '')
        if not commit_ts:
            continue
        
        try:
            commit_dt = datetime.fromisoformat(commit_ts.replace('Z', '+00:00'))
        except Exception:
            continue
        
        # Find prompts within 30 minutes before this commit
        matching_prompts = []
        for entry in journal:
            entry_ts = entry.get('ts', '')
            if not entry_ts:
                continue
            try:
                entry_dt = datetime.fromisoformat(entry_ts.replace('Z', '+00:00'))
            except Exception:
                continue
            
            # Prompt should be BEFORE commit, within 30 minutes
            delta = (commit_dt - entry_dt).total_seconds()
            if 0 < delta < 1800:  # 30 minutes
                msg = entry.get('msg', '')
                if msg and len(msg) > 10:
                    matching_prompts.append(msg)
        
        # Use commit message as additional signal
        if commit.get('msg'):
            matching_prompts.append(commit['msg'])
        
        if matching_prompts and commit['files']:
            # Combine all prompts for this commit
            combined_prompt = ' '.join(matching_prompts)
            correlations.append((combined_prompt, commit['files']))
    
    return correlations


def main():
    print('Loading journal...')
    journal = load_journal()
    print(f'  {len(journal)} entries')
    
    print('Loading git history...')
    commits = get_recent_commits(100)
    print(f'  {len(commits)} recent commits')
    
    print('Correlating prompts to files...')
    correlations = correlate_prompts_to_commits(journal, commits)
    print(f'  {len(correlations)} correlations found')
    
    print('Training intent_numeric_seq001_v001...')
    for prompt, files in correlations:
        record_touch(prompt, files, learning_rate=0.15)  # slightly higher LR for seeding
    
    stats = get_stats()
    print(f'\nResult:')
    print(f'  Vocab: {stats["vocab_size"]} words')
    print(f'  Files: {stats["files_tracked"]} tracked')
    print(f'  Touches: {stats["total_touches"]} total')
    
    if stats['top_files']:
        print('\nTop files:')
        for f, c in stats['top_files'][:10]:
            print(f'  {f}: {c} touches')


if __name__ == '__main__':
    main()
