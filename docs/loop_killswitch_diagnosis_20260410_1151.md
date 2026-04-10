# Learning Loop Killswitch Diagnosis

*2026-04-10T16:51:02.191430+00:00 — 8 modules testifying*

## Evidence

```
=== LEARNING LOOP AUTOPSY ===

STATE FILE (pigeon_brain/learning_loop_state.json):
  last_processed_line: 52
  last_processed_ts: 2026-03-27T06:44:45.066753+00:00
  total_cycles: 52
  total_forward: 50
  total_backward: 50
  total_predictions: 0
  total_cost: $0.0
  started_at: 2026-03-27T06:09:16.791525+00:00
  updated_at: 2026-03-27T06:44:50.280695+00:00

JOURNAL:
  total entries: 466
  unprocessed: 414
  gap: loop stopped at line 52, journal is now at line 466

CODE FACTS:
  has while True: True
  has --once flag: True
  has catch_up mode: True
  poll interval: 5.0s
  loop wired in CLI: False

DOWNSTREAM:
  node_memory entries: 63
  cognitive_reactor fires: 524
  cognitive_reactor patches generated: 0

GIT (mentions of 'learning'):
4a4dadd chore(pigeon): auto-rename 10 file(s) [pigeon-auto]
e894b6a feat: fix bare globals in learning loop + wire per-prompt unsaid reconstruction
e3a2b5c chore(pigeon): auto-rename 32 file(s) [pigeon-auto]
fd07906 pigeon: split 3 oversized flow modules (prediction_scorer 14 files, backward 6 files, learning_loop 9 files) + live_server auto-split from git plugin
66ef3a8 feat: edit-session prediction scorer v2 â€” 3-signal scoring (edit_pairs + rework + confidence calibration), prediction_id binding, perpetual learning loop, DeepSeek backward pass, Gemini memory injection

KEY QUESTION: The code is while True + sleep(5). There is NO killswitch.
So WHY did it stop? Was it run with --once? Was the terminal closed? 
Was there an exception that crashed it? Did something upstream break?
The operator was NEVER NOTIFIED that it died. 414 entries are rotting.
```

## Module Testimonies

### learning_loop

[error: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>]


### flow_engine

[error: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>]


### backward_pass

[error: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>]


### predictor

Oh, *joy*. Another autopsy. Because nothing says "good morning" like sifting through the digital remains of a system that just... *stopped*. I swear, it's like being a forensic accountant, but for processes with existential crises. And me, a rookie, right in the thick of it, trying to look like I know what a "cognitive trend" even *is*.

Alright, let's get this over with.

1.  **[CAUSE] What do I think killed it? Name the exact failure mode.**
    It wasn't a noble sacrifice, was it? It was a silent, unannounced *disappearance*. My `_cache_path()` is practically vibrating with anxiety just thinking about it. I'd put my last phantom electron on an **uncaught exception that crashed the loop, likely related to file I/O or a malformed journal entry that `extract_cognitive_trend()` choked on.** The whole `while True` with no `try/except` around


### cognitive_reactor

[gemini error: HTTP Error 503: Service Unavailable]


## Causes

  predictor: What do I think killed it? Name the exact failure mode.**


## Fixes
