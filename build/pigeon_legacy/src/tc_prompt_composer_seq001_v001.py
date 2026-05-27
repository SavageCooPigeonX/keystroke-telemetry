"""Controlled prompt composer for thought_completer.

This is the opt-in surface where prompts can be written before Copilot sees
them. It captures deletions and hesitation locally, runs the pre-prompt
pipeline, injects dynamic state, then copies the final prompt for handoff.
"""
from __future__ import annotations

import importlib.util
import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PAUSE_THRESHOLD_MS = 2000
PAUSE_COOLDOWN_S = 2.0
MIN_PAUSE_CHARS = 4


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _words(text: str) -> list[str]:
    out: list[str] = []
    for part in str(text).split():
        word = part.strip(".,;:!?()[]{}\"'`")
        if len(word) >= 3:
            out.append(word)
    return out


def _diff_text(old: str, new: str) -> dict[str, Any]:
    if old == new:
        return {"pos": 0, "deleted": "", "inserted": "", "deleted_len": 0, "inserted_len": 0}
    prefix = 0
    max_prefix = min(len(old), len(new))
    while prefix < max_prefix and old[prefix] == new[prefix]:
        prefix += 1

    old_suffix = len(old)
    new_suffix = len(new)
    while old_suffix > prefix and new_suffix > prefix and old[old_suffix - 1] == new[new_suffix - 1]:
        old_suffix -= 1
        new_suffix -= 1

    deleted = old[prefix:old_suffix]
    inserted = new[prefix:new_suffix]
    return {
        "pos": prefix,
        "deleted": deleted,
        "inserted": inserted,
        "deleted_len": len(deleted),
        "inserted_len": len(inserted),
    }


def _unique_words(fragments: list[str]) -> list[str]:
    seen: set[str] = set()
    words: list[str] = []
    for fragment in fragments:
        for word in _words(fragment):
            key = word.lower()
            if key in seen:
                continue
            seen.add(key)
            words.append(word)
    return words[:30]


@dataclass
class CompositionTracker:
    text: str = ""
    started_ms: int = 0
    last_change_ms: int = 0
    inserted_chars: int = 0
    deleted_chars: int = 0
    deleted_fragments: list[str] = field(default_factory=list)
    hesitation_windows: list[dict[str, Any]] = field(default_factory=list)

    def apply_text(self, new_text: str, now_ms: int | None = None) -> dict[str, Any]:
        now_ms = now_ms or int(time.time() * 1000)
        old_text = self.text
        if old_text == new_text:
            return _diff_text(old_text, new_text)
        if not self.started_ms:
            self.started_ms = now_ms
        if self.last_change_ms and now_ms - self.last_change_ms >= PAUSE_THRESHOLD_MS:
            self.hesitation_windows.append({
                "ts": self.last_change_ms,
                "duration_ms": now_ms - self.last_change_ms,
                "buffer_at": old_text[-300:],
            })

        diff = _diff_text(old_text, new_text)
        self.inserted_chars += diff["inserted_len"]
        self.deleted_chars += diff["deleted_len"]
        if diff["deleted"].strip():
            self.deleted_fragments.append(diff["deleted"].strip())
        self.text = new_text
        self.last_change_ms = now_ms
        return diff

    def clear(self) -> None:
        self.text = ""
        self.started_ms = 0
        self.last_change_ms = 0
        self.inserted_chars = 0
        self.deleted_chars = 0
        self.deleted_fragments.clear()
        self.hesitation_windows.clear()

    def state(self, final_text: str | None = None) -> dict[str, Any]:
        final = self.text if final_text is None else final_text
        total = self.inserted_chars + self.deleted_chars
        duration_ms = 0
        if self.started_ms and self.last_change_ms:
            duration_ms = max(0, self.last_change_ms - self.started_ms)
        deleted_words = _unique_words(self.deleted_fragments)
        return {
            "ts": _utc_now(),
            "final_text": final,
            "deleted_text": " ".join(self.deleted_fragments[-20:]),
            "deleted_words": deleted_words,
            "deletion_ratio": round(self.deleted_chars / max(total, 1), 3),
            "inserted_chars": self.inserted_chars,
            "deleted_chars": self.deleted_chars,
            "hesitation_count": len(self.hesitation_windows),
            "hesitation_windows": list(self.hesitation_windows[-20:]),
            "duration_ms": duration_ms,
            "source": "thought_completer_composer",
        }


@dataclass
class PauseGate:
    cooldown_s: float = PAUSE_COOLDOWN_S
    min_chars: int = MIN_PAUSE_CHARS
    last_fire_time: float = 0.0
    last_text: str = ""
    busy: bool = False

    def check(self, text: str, now_s: float) -> tuple[bool, str, float]:
        stripped = text.strip()
        if len(stripped) < self.min_chars:
            return False, "short", 0.0
        if self.busy:
            return False, "busy", 0.0
        if stripped == self.last_text:
            return False, "duplicate", 0.0
        remaining = self.cooldown_s - (now_s - self.last_fire_time)
        if remaining > 0:
            return False, "cooldown", remaining
        return True, "ready", 0.0

    def mark_fire(self, text: str, now_s: float) -> None:
        self.last_fire_time = now_s
        self.last_text = text.strip()
        self.busy = True

    def mark_done(self) -> None:
        self.busy = False


def _load_codex_compat(root: Path):
    path = root / "codex_compat.py"
    if not path.exists():
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location("codex_compat", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _generate_intent_key(root: Path, text: str, deleted_words: list[str]) -> dict[str, Any]:
    try:
        from src.tc_intent_keys_seq001_v001 import generate_intent_key
        return generate_intent_key(root, text, deleted_words=deleted_words, emit_prompt_box=True, inject=True)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


class PromptComposer:
    def __init__(self, root: Path, sim_timeout_s: int = 20, auto_clear: bool = False):
        import tkinter as tk

        self.repo_root = Path(root).resolve()
        self.sim_timeout_s = sim_timeout_s
        self.auto_clear = auto_clear
        self.tracker = CompositionTracker()
        self.pause_gate = PauseGate()
        self._pause_after_id: str | None = None
        self._last_pause_record: dict[str, Any] | None = None
        self._reward_count = 0
        self._tk = tk
        self.window = tk.Tk()
        self.window.title("thought completer prompt composer")
        self.window.geometry("760x360")
        self.window.attributes("-topmost", True)
        self.window.configure(bg="#0d1117")
        self._submitting = False
        self._build_ui()
        self._keep_on_top()

    def _build_ui(self) -> None:
        tk = self._tk
        font = "Cascadia Code"
        surface = "#161b22"
        text_c = "#e6edf3"
        dim = "#8b949e"
        accent = "#58a6ff"

        header = tk.Frame(self.window, bg=surface, height=28)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="thought completer composer", bg=surface, fg=accent,
                 font=(font, 9, "bold")).pack(side="left", padx=8)
        self.metrics = tk.Label(header, text="del 0% | pause 0", bg=surface, fg=dim, font=(font, 8))
        self.metrics.pack(side="right", padx=8)

        self.input = tk.Text(self.window, bg="#0d1117", fg=text_c, insertbackground=text_c,
                             font=(font, 12), wrap="word", padx=10, pady=10,
                             borderwidth=0, highlightthickness=1,
                             highlightbackground="#30363d", undo=True)
        self.input.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        self.input.bind("<<Modified>>", self._on_modified)
        self.input.bind("<Control-Return>", self._submit)
        self.input.bind("<Control-Shift-R>", self._reward_last)
        self.input.bind("<Control-Shift-r>", self._reward_last)
        self.input.bind("<Control-Shift-C>", self._copy_own_words)
        self.input.bind("<Control-Shift-c>", self._copy_own_words)
        self.input.bind("<Control-l>", self._clear)
        self.input.focus_set()

        footer = tk.Frame(self.window, bg=surface, height=34)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        self.status = tk.Label(footer, text="Ctrl+Enter injects state and copies prompt", bg=surface,
                               fg=dim, font=(font, 8), anchor="w")
        self.status.pack(side="left", fill="x", expand=True, padx=8)
        tk.Button(footer, text="Inject + copy", command=self._submit, bg="#238636",
                  fg="#ffffff", relief="flat", font=(font, 8, "bold")).pack(side="right", padx=6)
        tk.Button(footer, text="Reward", command=self._reward_last, bg="#735c0f",
                  fg="#ffffff", relief="flat", font=(font, 8)).pack(side="right", padx=0)
        tk.Button(footer, text="Copy words", command=self._copy_own_words, bg="#1f6feb",
                  fg="#ffffff", relief="flat", font=(font, 8)).pack(side="right", padx=6)
        tk.Button(footer, text="Clear", command=self._clear, bg="#30363d",
                  fg="#ffffff", relief="flat", font=(font, 8)).pack(side="right", padx=0)

    def _on_modified(self, _event=None) -> None:
        if not self.input.edit_modified():
            return
        self.input.edit_modified(False)
        text = self.input.get("1.0", "end-1c")
        self.tracker.apply_text(text)
        state = self.tracker.state(text)
        self.metrics.config(text=f"del {state['deletion_ratio']:.0%} | pause {state['hesitation_count']}")
        self._schedule_pause_fire(text)

    def _clear(self, _event=None) -> str:
        if self._pause_after_id:
            self.window.after_cancel(self._pause_after_id)
            self._pause_after_id = None
        self.input.delete("1.0", "end")
        self.tracker.clear()
        self.pause_gate = PauseGate()
        self.metrics.config(text="del 0% | pause 0")
        self.status.config(text="cleared", fg="#8b949e")
        return "break"

    def _copy_to_clipboard(self, text: str) -> None:
        self.window.clipboard_clear()
        self.window.clipboard_append(text)
        self.window.update_idletasks()

    def _copy_own_words(self, _event=None) -> str:
        text = self.input.get("1.0", "end-1c")
        self._copy_to_clipboard(text)
        _append_jsonl(self.repo_root / "logs" / "thought_composer_actions.jsonl", {
            "ts": _utc_now(),
            "action": "copy_own_words",
            "chars": len(text),
            "source": "thought_completer_composer",
        })
        self.status.config(text="copied your words/code", fg="#58a6ff")
        return "break"

    def _reward_last(self, _event=None) -> str:
        if not self._last_pause_record:
            self.status.config(text="nothing to reward yet", fg="#f0c040")
            return "break"
        self._reward_count += 1
        record = {
            "ts": _utc_now(),
            "action": "reward_pause",
            "reward_n": self._reward_count,
            "buffer": (self._last_pause_record.get("final_text") or "")[:1000],
            "context_selection": self._last_pause_record.get("context_selection") or {},
            "sim_latest": self._last_pause_record.get("sim_latest") or {},
            "source": "thought_completer_composer",
        }
        _append_jsonl(self.repo_root / "logs" / "thought_composer_rewards.jsonl", record)
        self.status.config(text=f"rewarded pause #{self._reward_count}", fg="#f0c040")
        return "break"

    def _submit(self, _event=None) -> str:
        if self._pause_after_id:
            self.window.after_cancel(self._pause_after_id)
            self._pause_after_id = None
        if self._submitting:
            return "break"
        final_text = self.input.get("1.0", "end-1c").strip()
        if not final_text:
            self.status.config(text="nothing to inject", fg="#f85149")
            return "break"

        self._submitting = True
        self.status.config(text="running pre-prompt injection...", fg="#58a6ff")
        state = self.tracker.state(final_text)

        def worker() -> None:
            try:
                from src.tc_prompt_brain_seq001_v001 import assemble_prompt_brain
                prompt_brain = assemble_prompt_brain(
                    self.repo_root,
                    final_text,
                    deleted_words=state["deleted_words"],
                    source="thought_completer_composer",
                    trigger="submit",
                    emit_prompt_box=True,
                    inject=True,
                )
                compat = _load_codex_compat(self.repo_root)
                result = compat.run_pre_prompt_pipeline(
                    self.repo_root,
                    final_text,
                    deleted_text=state["deleted_text"],
                    deleted_words=state["deleted_words"],
                    hesitation_count=state["hesitation_count"],
                    duration_ms=state["duration_ms"],
                    run_sim=True,
                    sim_timeout_s=self.sim_timeout_s,
                    inject=True,
                )
                result["intent_key"] = prompt_brain.get("intent") or prompt_brain.get("intent_key")
                result["prompt_brain"] = prompt_brain
                record = {
                    "ts": _utc_now(),
                    "composition": state,
                    "intent_key": prompt_brain.get("intent") or prompt_brain.get("intent_key"),
                    "prompt_brain": prompt_brain,
                    "pre_prompt": result,
                    "handoff": "clipboard",
                }
                _append_jsonl(self.repo_root / "logs" / "thought_composer_submits.jsonl", record)
                self.window.after(0, lambda: self._finish_submit(final_text, result))
            except Exception as exc:
                self.window.after(0, lambda: self._fail_submit(exc))

        threading.Thread(target=worker, daemon=True).start()
        return "break"

    def _schedule_pause_fire(self, text: str) -> None:
        if self._pause_after_id:
            self.window.after_cancel(self._pause_after_id)
            self._pause_after_id = None
        if self._submitting or len(text.strip()) < self.pause_gate.min_chars:
            return
        self.status.config(text=f"pause arms in {PAUSE_THRESHOLD_MS / 1000:.1f}s", fg="#8b949e")
        self._pause_after_id = self.window.after(PAUSE_THRESHOLD_MS, self._fire_pause_if_ready)

    def _fire_pause_if_ready(self) -> None:
        self._pause_after_id = None
        text = self.input.get("1.0", "end-1c").strip()
        now_s = time.time()
        ready, reason, wait_s = self.pause_gate.check(text, now_s)
        if not ready:
            if reason == "cooldown":
                self.status.config(text=f"cooldown {wait_s:.1f}s", fg="#8b949e")
                self._pause_after_id = self.window.after(max(100, int(wait_s * 1000)), self._fire_pause_if_ready)
            elif reason == "duplicate":
                self.status.config(text="pause idle; buffer already simulated", fg="#8b949e")
            elif reason == "busy":
                self.status.config(text="pause sim already running", fg="#8b949e")
            return

        self.pause_gate.mark_fire(text, now_s)
        state = self.tracker.state(text)
        self.status.config(text="pause fired: context + sim...", fg="#58a6ff")

        def worker() -> None:
            try:
                from src.tc_prompt_brain_seq001_v001 import assemble_prompt_brain
                prompt_brain = assemble_prompt_brain(
                    self.repo_root,
                    text,
                    deleted_words=state["deleted_words"],
                    source="thought_completer_composer",
                    trigger="pause",
                    emit_prompt_box=True,
                    inject=True,
                )
                compat = _load_codex_compat(self.repo_root)
                sim = compat._run_sim_buffer(self.repo_root, text, timeout_s=self.sim_timeout_s)
                sim_latest = compat._latest_json(self.repo_root / "logs" / "tc_sim_results.jsonl") or {}
                reinjection = compat._load_json(self.repo_root / "logs" / "tc_intent_reinjection.json") or {}
                handoff_ready = sim.get("status") == "ok"
                pre_prompt = {
                    "ts": _utc_now(),
                    "final_text": text,
                    "trigger": "pause",
                    "hesitation_count": state["hesitation_count"],
                    "duration_ms": state["duration_ms"],
                    "handoff_ready": handoff_ready,
                    "block_reason": "" if handoff_ready else f"thought-completer sim {sim.get('status', 'did_not_finish')}",
                    "composition": state,
                    "intent_key": prompt_brain.get("intent") or prompt_brain.get("intent_key"),
                    "prompt_brain": prompt_brain,
                    "context_selection": prompt_brain.get("context_selection") or {},
                    "sim": sim,
                    "sim_latest": sim_latest,
                    "tc_intent_reinjection": reinjection,
                }
                record = {"ts": _utc_now(), "trigger": "pause", "pre_prompt": pre_prompt}
                _append_jsonl(self.repo_root / "logs" / "thought_composer_pauses.jsonl", record)
                self.window.after(0, lambda: self._finish_pause(text, pre_prompt))
            except Exception as exc:
                self.window.after(0, lambda: self._fail_pause(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_pause(self, text: str, pre_prompt: dict[str, Any]) -> None:
        self.pause_gate.mark_done()
        current = self.input.get("1.0", "end-1c").strip()
        if current != text:
            self.status.config(text="pause result stale; typing changed", fg="#f0c040")
            return
        try:
            compat = _load_codex_compat(self.repo_root)
            logs = self.repo_root / "logs"
            logs.mkdir(parents=True, exist_ok=True)
            (logs / "pre_prompt_state.json").write_text(
                json.dumps(pre_prompt, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            (logs / "pre_prompt_state.md").write_text(
                compat._render_pre_prompt_block(pre_prompt) + "\n",
                encoding="utf-8",
            )
            pre_prompt["injected"] = compat._inject_pre_prompt_state(self.repo_root, pre_prompt)
            (logs / "pre_prompt_state.json").write_text(
                json.dumps(pre_prompt, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            self.status.config(text=f"pause inject failed: {exc}", fg="#f85149")
            return

        files = (pre_prompt.get("context_selection") or {}).get("files") or []
        top_file = files[0].get("name", "no file") if files else "no file"
        sim_status = (pre_prompt.get("sim") or {}).get("status", "unknown")
        self._last_pause_record = pre_prompt
        self.status.config(text=f"pause fired: {top_file}, sim {sim_status}", fg="#3fb950")

    def _fail_pause(self, exc: Exception) -> None:
        self.pause_gate.mark_done()
        self.status.config(text=f"pause failed: {exc}", fg="#f85149")

    def _finish_submit(self, final_text: str, result: dict[str, Any]) -> None:
        self._submitting = False
        self._copy_to_clipboard(final_text)
        sim_status = (result.get("sim") or {}).get("status", "unknown")
        ready = result.get("handoff_ready", False)
        if ready:
            self.status.config(text=f"injected, sim {sim_status}, prompt copied", fg="#3fb950")
        else:
            reason = result.get("block_reason") or sim_status
            self.status.config(text=f"injected but blocked: {reason}; prompt copied", fg="#f0c040")
        if self.auto_clear:
            self._clear()

    def _fail_submit(self, exc: Exception) -> None:
        self._submitting = False
        self.status.config(text=f"inject failed: {exc}", fg="#f85149")

    def _keep_on_top(self) -> None:
        try:
            self.window.attributes("-topmost", True)
            self.window.lift()
        finally:
            self.window.after(3000, self._keep_on_top)

    def run(self) -> None:
        self.window.mainloop()


def run_prompt_composer(root: Path | None = None, sim_timeout_s: int = 20, auto_clear: bool = False) -> None:
    repo_root = Path(root).resolve() if root is not None else Path(__file__).resolve().parent.parent
    composer = PromptComposer(repo_root, sim_timeout_s=sim_timeout_s, auto_clear=auto_clear)
    composer.run()


if __name__ == "__main__":
    run_prompt_composer()
