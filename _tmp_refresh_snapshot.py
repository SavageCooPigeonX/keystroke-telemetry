"""Refresh push snapshot and narrative glove."""
from pathlib import Path
from src.push_snapshot_seq001_v001_seq001_v001 import capture_snapshot
from src.narrative_glove_seq001_v001_seq001_v001 import inject_narrative

root = Path('.')

# Build fresh snapshot
print("Building fresh snapshot...")
snap = capture_snapshot(root, 'health_audit', 'prompt_layer_audit', [])
if snap:
    print(f"Compliance: {snap.get('modules',{}).get('compliance_pct', '?')}%")
    print(f"Bugs: {snap.get('bugs',{}).get('total', '?')}")
    print("Saved snapshot")
else:
    print("Snapshot returned None")

# Now regenerate narrative glove
print("\nRegenerating narrative glove...")
inject_narrative(root)
print("Done!")
