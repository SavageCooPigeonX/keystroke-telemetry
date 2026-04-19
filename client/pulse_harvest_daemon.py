"""Pulse harvest daemon — polls src/ every 30s for stamped pulse blocks, writes pulse_harvest_latest.json."""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

from src.脉p_ph_s015_v004_d0403_读唤任_λP0_βoc import harvest_all_pulses  # type: ignore[import]

OUT = ROOT / 'logs' / 'pulse_harvest_latest.json'
INTERVAL = 30


def run():
    print('[pulse-daemon] started', flush=True)
    while True:
        try:
            pairs = harvest_all_pulses(ROOT)
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps({
                'ts': datetime.now(timezone.utc).isoformat(),
                'pairs': pairs,
                'total': len(pairs),
            }, ensure_ascii=False, indent=2), encoding='utf-8')
            if pairs:
                print(f'[pulse-daemon] harvested {len(pairs)} pair(s)', flush=True)
        except Exception as e:
            print(f'[pulse-daemon] error: {e}', flush=True)
        time.sleep(INTERVAL)


if __name__ == '__main__':
    run()
