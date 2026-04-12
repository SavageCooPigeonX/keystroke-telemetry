"""Test: trajectory building + response pairing."""
import sys, json; sys.path.insert(0, '.')
from src.tc_trajectory import build_trajectory, format_trajectory_for_prompt

traj = build_trajectory()
print(f"Turns: {len(traj['turns'])}")
print(f"Transitions: {len(traj['transitions'])}")
print(f"Phase: {traj['phase']}")
print()
for i, t in enumerate(traj['turns']):
    has_resp = 'YES' if t['response'] else 'NO'
    print(f"Turn {i+1} [{t['state']}] resp={has_resp}")
    print(f"  P: {t['prompt'][:80]}")
    if t['response']:
        print(f"  R: {t['response'][:80]}")
    if t['deleted_words']:
        print(f"  DEL: {t['deleted_words']}")
    print()
print('--- FORMATTED PROMPT BLOCK ---')
block = format_trajectory_for_prompt(traj)
print(block[:2500])
