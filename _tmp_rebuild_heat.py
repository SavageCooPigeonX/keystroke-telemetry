"""Rebuild file_heat_map.json from edit_pairs + entropy."""
import sys, json
sys.path.insert(0, '.')
from pathlib import Path
from src.热p_fhm_s011_v005_d0403_踪稿析_λP0_βde import update_heat_map

root = Path('.')
update_heat_map(root)

hm = json.loads(Path('file_heat_map.json').read_text('utf-8'))
sorted_mods = sorted(hm.items(), key=lambda x: x[1]['heat'], reverse=True)
print(f"Total modules: {len(hm)}")
print("--- TOP 15 BY HEAT ---")
for m, d in sorted_mods[:15]:
    print(f"  {m}: heat={d['heat']}  touches={d['touch_score']}  entropy={d['entropy']}")
