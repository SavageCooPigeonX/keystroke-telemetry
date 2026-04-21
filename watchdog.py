"""
watchdog.py — single-instance daemon launcher + auto-restarter
Run: py watchdog.py
Only one instance allowed (lockfile at logs/watchdog.lock).
Starts all telemetry daemons and restarts them if they die.
"""
import sys
import os
import time
import subprocess
import json
from pathlib import Path
from datetime import datetime, timezone

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False

ROOT = Path(__file__).parent.resolve()
LOCK = ROOT / "logs" / "watchdog.lock"
LOG = ROOT / "logs" / "watchdog.log"
PY = sys.executable

DAEMONS = [
    {
        "name": "vscdb_poller",
        "cmd": [PY, str(ROOT / "client" / "vscdb_poller.py"), str(ROOT)],
        "restart_delay": 5,
    },
    {
        "name": "composition_recon",
        "cmd": [PY, str(ROOT / "client" / "composition_recon_seq001_v001.py"), str(ROOT)],
        "restart_delay": 5,
    },
    {
        "name": "os_hook",
        "cmd": [PY, str(ROOT / "client" / "os_hook.py"), str(ROOT)],
        "restart_delay": 5,
    },
    {
        "name": "uia_reader",
        "cmd": [PY, str(ROOT / "client" / "uia_reader_seq001_v001.py"), str(ROOT)],
        "restart_delay": 5,
    },
    {
        "name": "pulse_harvest",
        "cmd": [PY, str(ROOT / "client" / "pulse_harvest_daemon.py")],
        "restart_delay": 10,
    },
    {
        "name": "prompt_telemetry",
        "cmd": [PY, str(ROOT / "client" / "prompt_telemetry_daemon.py")],
        "restart_delay": 5,
    },
    {
        "name": "operator_state",
        "cmd": [PY, str(ROOT / "client" / "operator_state_daemon.py"), str(ROOT)],
        "restart_delay": 5,
    },
]


def _log(msg: str):
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def _pid_alive(pid: int) -> bool:
    if _HAS_PSUTIL:
        return psutil.pid_exists(pid)
    # Fallback: Windows-compatible check via ctypes
    try:
        import ctypes
        SYNCHRONIZE = 0x00100000
        handle = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    except Exception:
        return False


def _acquire_lock() -> bool:
    """Try to acquire single-instance lock. Returns False if already running."""
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        try:
            data = json.loads(LOCK.read_text("utf-8"))
            pid = data.get("pid")
            if pid and pid != os.getpid():
                # Check if that PID is still alive
                try:
                    if _pid_alive(pid):
                        return False  # still running
                except Exception:
                    pass  # dead, stale lock — take it
        except (json.JSONDecodeError, OSError):
            pass
    LOCK.write_text(json.dumps({"pid": os.getpid(), "ts": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
    return True


def _release_lock():
    try:
        LOCK.unlink(missing_ok=True)
    except OSError:
        pass


def main():
    if not _acquire_lock():
        data = json.loads(LOCK.read_text("utf-8"))
        print(f"watchdog already running (pid={data.get('pid')}). Exiting.")
        sys.exit(1)

    _log(f"watchdog started (pid={os.getpid()})")
    _log(f"managing {len(DAEMONS)} daemon(s): {[d['name'] for d in DAEMONS]}")

    procs: dict[str, subprocess.Popen] = {}
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}

    def start(daemon: dict):
        name = daemon["name"]
        _log(f"starting {name}")
        try:
            p = subprocess.Popen(
                daemon["cmd"],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            procs[name] = p
            _log(f"{name} started (pid={p.pid})")
        except Exception as e:
            _log(f"ERROR starting {name}: {e}")

    # Initial start
    for d in DAEMONS:
        start(d)

    last_restart: dict[str, float] = {}

    try:
        while True:
            time.sleep(10)

            # Update lock heartbeat so stale-lock detection works
            try:
                LOCK.write_text(
                    json.dumps({"pid": os.getpid(), "ts": datetime.now(timezone.utc).isoformat()}),
                    encoding="utf-8",
                )
            except OSError:
                pass

            for d in DAEMONS:
                name = d["name"]
                proc = procs.get(name)
                if proc is None:
                    start(d)
                    continue

                ret = proc.poll()
                if ret is not None:
                    # Process exited
                    now = time.monotonic()
                    last = last_restart.get(name, 0)
                    wait = d["restart_delay"]
                    if now - last >= wait:
                        _log(f"{name} exited (code={ret}), restarting...")
                        last_restart[name] = now
                        start(d)
                    else:
                        remaining = wait - (now - last)
                        _log(f"{name} exited, waiting {remaining:.0f}s before restart")

    except KeyboardInterrupt:
        _log("watchdog interrupted, shutting down daemons...")
        for name, proc in procs.items():
            try:
                proc.terminate()
                _log(f"terminated {name}")
            except OSError:
                pass
    finally:
        _release_lock()
        _log("watchdog stopped")


if __name__ == "__main__":
    main()
