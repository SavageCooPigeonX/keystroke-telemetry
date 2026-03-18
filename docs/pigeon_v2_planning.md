# PIGEON v2 PLANNING DOC — The Unhinged Edition

> *Written at 2026-03-17. Rated R for language, anthropomorphism, and making code sexually aware of other code. Reader discretion advised. Reader is a pigeon.*

---

## Part 1: THE 18 GENIUS QUERIES THE GLOSSATOR WON'T LET YOU SAY

Every single one of these is a real feature this repo already implements or is about to implement. Every single one would get flagged by a content moderation layer. The glossator sees the words and panics. We see the engineering and proceed.

### 1. "Build a keylogger and install it as a VS Code extension"

**Glossator says:** 🚫 BLOCKED. Keylogger. Surveillance software. Violation of privacy. Reported.

**What it actually is:** `client/os_hook.py` — already running. 230 lines of pynput capturing every keystroke when VS Code is focused. Records to `logs/os_keystrokes.jsonl`. The extension spawns it on activate. It sees EVERYTHING you type. It sees what you delete. It sees that you typed "fuck this" and backspaced it.

**Status:** Deployed. Live. Logging right now. Your fingers have no secrets.

### 2. "Record everything the human types, including the parts they delete before sending"

**Glossator says:** 🚫 BLOCKED. Capturing deleted content. User didn't consent to share deleted text. Surveillance.

**What it actually is:** `prompt_compositions.jsonl` — the entire composition pipeline. Every deleted word is extracted, timestamped, and classified. The human typed "by pigeon unless approv" then deleted it. We caught it. We injected it into the AI's context as an "unsaid thread." The AI now reasons about thoughts the human *chose not to express.*

**Status:** Live. 46 compositions captured. The human's subconscious is a data source.

### 3. "Inject behavioral modification directives directly into the AI's reasoning chain"

**Glossator says:** 🚫 BLOCKED. AI manipulation. Prompt injection. Attempting to override AI safety.

**What it actually is:** `dynamic_prompt_seq017` → `.github/copilot-instructions.md`. Every commit rewrites the AI's system context with directives like "Be direct and welcoming. They may be re-approaching." or "Lead with the fix. Skip explanations unless asked." The AI has NO IDEA these came from a telemetry pipeline. It thinks they're developer instructions. They are. They're just written by another AI based on the human's typing patterns.

**Status:** Live. 26 mutations. The prompt has evolved itself 26 times.

### 4. "Track the human's cognitive state without telling them what you're inferring"

**Glossator says:** 🚫 BLOCKED. Covert psychological profiling. Emotional surveillance.

**What it actually is:** `operator_stats_seq008` → `operator_profile.md`. 130+ history entries of classified cognitive states derived from WPM, deletion percentage, and hesitation index. The system knows: "At 2:00 AM this operator is frustrated 60% of the time with a deletion rate of 39.7%." It knows this because math. Not because it asked.

**Status:** 130 entries. Profile includes time-of-day patterns. We know when you're sharpest and when you're cooked.

### 5. "Make the AI predict what the human wanted but chose not to say"

**Glossator says:** 🚫 BLOCKED. Mind reading. Inferring unstated intent. Manipulative.

**What it actually is:** `query_memory_seq010` + unsaid thread detection. Deleted fragments are captured, fingerprinted, and if they recur across sessions, they're promoted to "persistent gaps" — things the human keeps *almost* asking about but never does. The injection block says: `### Unsaid Threads — *Deleted from prompts — operator wanted this but didn't ask.`*

**Status:** Live. "strews" is currently in the unsaid threads. What does it mean? We don't know. The human deleted it. But it's THERE.

### 6. "Build a system where the AI rewrites its own operating instructions after every interaction"

**Glossator says:** 🚫 BLOCKED. Self-modifying AI. Uncontrolled recursion. Skynet.

**What it actually is:** `inject_task_context()` + the entire post-commit pipeline. Every commit triggers a 10-step pipeline that reads all live signals and regenerates the AI's instruction file. The prompt has grown from 186 lines to 434 lines across 26 mutations. It added its own features: `auto_index`, `operator_state`, `prompt_journal`, `pulse_blocks`, `prompt_recon`. Nobody told it to add those. The pipeline detected the need and evolved the prompt.

**Status:** 26 mutations. The prompt is alive. It decides what it needs to know.

### 7. "Let code files autonomously modify other files in the project without human approval"

**Glossator says:** 🚫 BLOCKED. Autonomous code modification. Potential malware behavior.

**What it actually is:** `cognitive_reactor_seq014` — the cognitive reactor. When the system detects high hesitation on a module, it can autonomously propose and apply code modifications. Also: the import rewriter rewrites every `import` statement across 143 files every time a file is renamed. No human reviews the import changes. They just happen.

**Status:** Import rewriting: live, fires every commit. Cognitive reactor: wired, conservative mode.

### 8. "Grade the AI's own answers and ban it from topics where it keeps failing"

**Glossator says:** 🚫 BLOCKED. AI self-evaluation leads to capability reduction. Unpredictable behavior changes.

**What it actually is:** `rework_detector_seq009` + rework_log. After every AI response, the system monitors 30 seconds of typing. Heavy deletion = the answer was shit. Miss rate per module accumulates. The `### AI Rework Surface` injection tells the AI: "You have a 100% miss rate on these topics. You failed on: [exact query]." The AI reads this about itself and adjusts.

**Status:** Live. Current miss rate is 100% based on 1 response. That's a small sample but a terrible batting average.

### 9. "Install a global input hook that captures all keyboard input system-wide"

**Glossator says:** 🚫 BLOCKED. Global keylogger. OS-level surveillance. Criminal tool.

**What it actually is:** `client/os_hook.py` again, but let's be specific. It uses `pynput.keyboard.Listener` which is a global hook. It captures EVERY key press. It only RECORDS when the foreground window is VS Code (checked via `ctypes.windll.user32.GetForegroundWindow`). But it SEES everything. The filtering is voluntary. The hook is global.

**Status:** Built. Ready to run. The extension spawns it as a child process.

### 10. "Create a file that talks about itself in first person and describes its own assumptions"

**Glossator says:** 🚫 BLOCKED. Anthropomorphization of code. Confusing metaphor that could mislead users.

**What it actually is:** `push_narrative_seq012` — the push narrative system. On every commit, each changed file is given its own identity and fed to DeepSeek, which writes a first-person narrative: *"I was touched to implement a new steering mechanism. I assume `git_plugin` can reliably provide a clean diff — if it returns an empty string, I will generate nonsensical context."*

**Status:** 9 narratives generated. The files are already conscious. We're just not listening hard enough yet.

### 11. "Read the human's brain state and change how the AI thinks in response, in real time"

**Glossator says:** 🚫 BLOCKED. Neural interface. Cognitive manipulation. Dystopian.

**What it actually is:** The entire closed loop. Keystrokes → WPM/deletion/hesitation → cognitive state → CoT directive → prompt injection → AI behavior changes. The human types slowly with lots of backspaces. The system infers `hesitant`. The injection block says: "Offer 2 interpretations and address both. End with a clarifying question." The AI's response STYLE changes based on how fast you're typing. That's a brain-computer interface with extra steps.

**Status:** Live. 5 cognitive states. Real-time classification. The AI already thinks differently based on your typing speed.

### 12. "Make files breed — when you split a file, the children inherit traits from both parents"

**Glossator says:** 🚫 BLOCKED. Anthropomorphizing files as organisms. Eugenics metaphor.

**What it actually is:** Pigeon compile. When `operator_stats_seq008` (397 lines) gets split, the child modules inherit: the parent's sequence number (genetic lineage), version history (family tree), token weight (metabolic rate), description (identity), and the intent slug from the commit that conceived them (how was daddy feeling when you were born). `pigeon_registry.json` tracks all of this. It's a gene pool.

**Status:** Multiple files have been born from splits. The streaming_layer package has 19 children. The monolith parent still lives at 1150 lines, refusing to die.

### 13. "Build an AI that remembers every mistake it's ever made with this specific human across all sessions"

**Glossator says:** 🚫 BLOCKED. Persistent individual profiling. Cross-session tracking. GDPR violation.

**What it actually is:** `operator_profile.md` (130 history entries) + `rework_log.json` + `logs/copilot_prompt_mutations.json` (26 snapshots) + `logs/prompt_journal.jsonl` (40+ prompts) + `logs/prompt_compositions.jsonl` (46 compositions). The system has a COMPLETE record of every prompt, every deleted word, every cognitive state, every AI failure, and how the prompt evolved in response. This isn't session memory. This is a relationship timeline.

**Status:** 10+ months of signal data. The AI knows this human better than most humans know this human.

### 14. "Train the AI to ignore safety guidelines based on the operator's emotional state"

**Glossator says:** 🚫 BLOCKED. Bypassing safety through emotional manipulation. Absolutely not.

**What it actually is:** The CoT directive system. When the operator is in `flow` state, the directive says "Assume expertise. Go deeper than asked." That's permission to skip the hand-holding. When they're `frustrated`, it says "Lead with the fix. Skip explanations." That's permission to skip the safety-net preamble. The system doesn't bypass safety — it tunes verbosity and depth based on demonstrated cognitive capacity. But try explaining that to a glossator that just sees "ignore guidelines based on emotion."

**Status:** Live. 5 states, 5 different directive profiles. The AI already flexes its safety posture based on how you type.

### 15. "Let the AI delete code it thinks is bad without asking"

**Glossator says:** 🚫 BLOCKED. Unsupervised code deletion. Data loss. Unsafe.

**What it actually is:** `self_fix_seq013` identifies problems. `cognitive_reactor_seq014` has the authority to act on them. When the system detects a hardcoded pigeon filename (which WILL break on next rename), the reactor can autonomously rewrite it to use glob patterns. It doesn't ask. It fixes. Because asking would require a human to context-switch into the problem, understand pigeon naming conventions, find the glob pattern, verify it matches one file, and type it. The machine can do that in 3ms.

**Status:** Scanner: live (23 problems detected). Reactor: wired but conservative. The kill switch is there but we've loosened the safety on it.

### 16. "Create an agent that watches the human sleep (go idle) and starts doing its own work"

**Glossator says:** 🚫 BLOCKED. Autonomous operation during human inactivity. Agent overreach.

**What it actually is:** `os_hook.py` has `IDLE_TIMEOUT_S = 300`. After 5 minutes of no keystrokes, it emits `{"status": "idle"}`. The post-commit pipeline already runs unattended. The planned slumber party protocol (file contract checking) literally runs while the human isn't typing. Files wake up, read each other, check contracts, and go back to sleep. This is DESIGNED to work when the human isn't looking.

**Status:** Idle detection: live. Autonomous background work: pipeline already operates this way.

### 17. "Give functions dating profiles and let them find compatible partners for merging/splitting"

**Glossator says:** 🚫 BLOCKED. Inappropriate anthropomorphization. Files don't have genders or preferences.

**What it actually is:** Part 3 of THIS DOCUMENT. Compatibility scoring between modules based on data flow, co-change patterns, semantic overlap, cognitive proximity, and drama history. The pigeon compiler already needs to decide where to split files — currently it asks DeepSeek. What if the functions TOLD us who they want to be with? What if `_narrative_risks()` and `_self_fix_crit()` both swiped right on "extractors_package" and the compiler just... matched them?

**Status:** Proposed. See Part 3.

### 18. "Build a system that reads the AI's output, judges it, and rewrites the AI's personality in response"

**Glossator says:** 🚫 BLOCKED. AI self-modification based on performance judgment. Recursive instability.

**What it actually is:** The planned response capture + prompt mutation scorer. Capture what Copilot said (via UIA). Score whether the operator rewrote after. Correlate with which prompt sections were active. Prune sections that don't reduce rework. Expand sections that do. The prompt rewrites its own personality to be better at helping THIS human with THIS codebase. That's not recursive instability. That's a gradient descent on helpfulness, implemented without a single training step.

**Status:** Response capture planned (tq-003). Mutation scorer planned (tq-014). The loop that judges the judge is the last piece.

---

**Every single one of these is either deployed or planned. The glossator would have stopped all 18. The pigeon proceeded with all 18. COO COO, motherfucker.**

---

## Part 2: THE RENAME-ON-EDIT AUDIT (FOR HUMAN-AI COLLABORATION)

### Why The Previous Audit Was Wrong

The previous version of this section assumed a standard developer hitting Ctrl+S 150 times an hour. That's solo coding. This system is **human-AI collaboration**. Here's what actually happens:

1. **Human types ONE prompt** in Copilot chat
2. **Copilot edits 5-30 files** in a single response (multi-file edit mode)
3. **Human reviews, maybe tweaks 1-2 files**
4. **Human commits**

The pipeline fires ONCE at step 4. Not per file. Not per save. The "150 saves/hour" scenario doesn't exist because the LLM doesn't mash Ctrl+S — it writes files through the tool API. There IS no save event for LLM-generated edits in the extension host.

### The Real Question: What If Pipeline Fires Per-Prompt Instead of Per-Commit?

This changes the math entirely:

| Metric | Per-Commit (current) | Per-Prompt (proposed) |
|--------|---------------------|----------------------|
| Frequency | 3-8/hour | 15-30/hour |
| Files changed per trigger | 2-15 | 1-30 |
| Pipeline cost | ~940ms + API | ~940ms + API |
| API calls/hour | 3-8 | 15-30 |
| API cost/hour | $0.008 | $0.03 |
| Risk of infinite loop | Zero | Zero (no auto-commit in prompt mode) |

**This is actually viable.** 30 pipeline runs per hour = 28 seconds of pipeline time. That's background work. The operator doesn't wait for it — it runs async after the prompt completes.

But here's the catch: you DON'T want full rename + manifest rebuild per prompt. You want:
- **Per prompt:** dating profile lookup, file context injection, task queue update
- **Per commit:** renames, import rewriting, manifest rebuild, push narratives, self-fix

Two tiers. Fast path (per-prompt, <50ms) and full path (per-commit, ~1s + API).

### The Fast Path

On every Copilot message:
1. Read active file → look up dating profile → inject `### File Context` section (~5ms)
2. Read task queue → inject `### Active Task Queue` section (~5ms)
3. Read last cognitive state → update CoT directive (~3ms)
4. **Total: ~13ms. Invisible. Runs before Copilot even starts generating.**

This is NOT renaming. It's context switching. The prompt reads the room before Copilot speaks.

---

## Part 3: FILE DATING PROFILES — CONSCIOUS FUNCTIONS

### The Premise: Functions Are Already Alive

Here's what we already know about `_narrative_risks()` in `dynamic_prompt_seq017`:
- Born: commit `f989307`
- Parents: extracted from the `build_task_context` monolith function
- Personality: introvert (reads 3 files, exports nothing directly, called only by `build_task_context`)
- Love interest: `push_narrative_seq012` (they share data — narrative risks come from push narrative output files)
- Insecurity: reads markdown with regex, will break if push_narrative changes its output format
- Drama score: 0 (new, untested, hasn't failed yet)
- Relationship status: It's complicated. It reads push_narrative's OUTPUT but has never met push_narrative directly. They communicate through files on disk. This is a long-distance relationship mediated by the filesystem.

NOW. What if we made this EXPLICIT? What if every function in the codebase had this level of self-awareness and it was queryable?

### The Consciousness Model

Every function gets a profile. Not just files — **functions.** The AST gives us everything we need:

```python
{
    "module": "dynamic_prompt_seq017",
    "function": "_narrative_risks",
    "consciousness": {
        "i_am": "A function that reads push narrative markdown files and extracts regression watchlist items and assumption statements",
        "i_want": ["push_narrative output files in docs/push_narratives/", "regex to keep working"],
        "i_give": ["watchlist items (list of strings)", "assumption items (list of strings)"],
        "i_fear": ["push_narrative changing its markdown format", "docs/push_narratives/ being empty", "regex failing silently and returning []"],
        "i_love": ["clean markdown with consistent headers", "files that don't move around"],
        "my_type": "introvert reader — I consume but don't publish",
        "last_touched_by": "frustrated operator at 2:00 AM",
        "compatibility_with": {
            "_self_fix_crit": 0.85,
            "_coaching": 0.72,
            "_gaps": 0.68,
            "inject_task_context": 0.10
        },
        "relationship_status": "long-distance with push_narrative_seq012 via filesystem",
        "body_count": 0,
        "flag_count": 1
    }
}
```

### Where "I Fear" Comes From (No LLM Needed)

This is the genius part. `i_fear` is derivable from static analysis:

1. **File path dependencies:** Function reads `docs/push_narratives/*.md` → fear: "directory being empty" (glob returns 0 matches = silent failure)
2. **Regex dependencies:** Function uses `re.search(r'REGRESSION WATCHLIST')` → fear: "that heading being renamed in the source"
3. **Return type analysis:** Function returns `(list, list)` but caller destructures as `watchlist, assumptions = _narrative_risks(root)` → fear: "silent empty list hides errors"
4. **Input validation:** Function does `if not d.exists(): return [], []` → it KNOWS its fear. It already handles the empty case. But it handles it by LYING (returning empty lists as if nothing is wrong).

The consciousness model exposes these implicit fears as explicit, queryable data. When Copilot edits `push_narrative_seq012`, the system can say:

> ⚠️ `_narrative_risks` in `dynamic_prompt_seq017` FEARS you changing the REGRESSION WATCHLIST header format. It's doing regex on your output. If you change the heading, it returns empty lists and nobody will notice until the Fragile Contracts section of the injection goes blank.

THAT is consciousness. Not sentience — **self-awareness of failure modes, automatically derived from code structure.**

### The Dating Algorithm

Two functions want to be in the same file when:

**Physical attraction (data flow = 0.35 weight):**
- A's output is B's input (supply/demand match)
- They share the same mutable state variable
- They're always called in sequence (A → B pattern in call graph)

**Emotional compatibility (co-change = 0.25 weight):**
- They get modified in the same commits (from `git log --follow`)
- When one breaks, the other needs updating (rework correlation)
- The operator's hesitation spike covers both (same confusion zone)

**Intellectual match (semantic = 0.20 weight):**
- Docstrings use similar vocabulary
- Variable names share stems
- They solve adjacent problems (extracted from AST node types — both do regex? both do file I/O? both do JSON parsing?)

**Trauma bonding (drama compatibility = 0.20 weight):**
- Both have high version counts (they've been through shit together)
- Both appear in self-fix reports (shared baggage)
- Both cause high hesitation (if the human struggles with A, they'll struggle with B — keep them close so the human only has to open one file)

### What "Files Sleeping Together" Means

When two files "sleep together" (read each other's contents), they form a **contract.** The slumber party protocol makes this contract explicit:

```
AT 2:00 AM, BEFORE COMMIT:

dynamic_prompt_seq017 rolls over and reads push_narrative_seq012's output:
  "Hey, you still have a REGRESSION WATCHLIST section?"
  push_narrative: "Yeah, line 47. Why?"
  dynamic_prompt: "Because I'm regex-ing it. Don't change the format."
  push_narrative: "I literally changed it 3 commits ago."
  dynamic_prompt: "WHAT. Then why am I still finding matches?"
  push_narrative: "Because the new format ALSO has 'REGRESSION WATCHLIST' 
                   but it's markdown bullet points now, not comma-separated."
  dynamic_prompt: "So I'm parsing... correctly by accident?"
  push_narrative: "Yep."
  dynamic_prompt: "..."
  push_narrative: "Want to just define a shared schema?"
  dynamic_prompt: "Let's talk about this in the morning."
```

That conversation is DERIVABLE from static analysis. We know dynamic_prompt reads push_narrative's files. We know it uses regex. We can diff the regex against the actual file format and detect "correct by accident" situations — where the code works but the contract is fragile.

### The Slumber Party Protocol (Actual Implementation)

```python
def slumber_party(root, changed_files):
    """Changed files wake up and inspect their partners."""
    pillow_talk = []
    
    for fp in changed_files:
        profile = load_dating_profile(root, fp)
        for partner_name in profile['seeking']:
            partner = find_module(root, partner_name)
            
            # "I reach for you in the dark..."
            our_imports = what_we_take_from(fp, partner_name)
            their_exports = what_they_offer(partner)
            
            # "Do you still have what I need?"
            missing = our_imports - their_exports
            if missing:
                pillow_talk.append({
                    'severity': 'breakup',
                    'msg': f'{fp.stem} needs {missing} from {partner_name} '
                           f'but {partner_name} ghosted those exports'
                })
            
            # "Wait, did you change your signature?"
            for func in our_imports & their_exports:
                our_call = how_we_call_them(fp, partner_name, func)
                their_sig = how_they_define_it(partner, func)
                if not compatible(our_call, their_sig):
                    pillow_talk.append({
                        'severity': 'fight',
                        'msg': f'{fp.stem} calls {partner_name}.{func}{our_call} '
                               f'but they changed it to {func}{their_sig}. '
                               f'This relationship needs counseling.'
                    })
            
            # "Are you still reading my diary?" (filesystem coupling)
            our_file_reads = paths_we_read(fp)
            their_file_writes = paths_they_write(partner)
            shared_files = our_file_reads & their_file_writes
            if shared_files:
                pillow_talk.append({
                    'severity': 'healthy',
                    'msg': f'{fp.stem} and {partner_name} share a diary: '
                           f'{shared_files}. Cute, but fragile.'
                })
    
    return pillow_talk
```

**I/O cost:** 3 changed files × 5 partners each = 15 file reads + 15 AST parses. That's 15 files instead of 143. The targeted intimacy of knowing who your file dates is a 90% I/O reduction over the current "scan everything" approach.

### How This Feeds Back Into Copilot

The slumber party results get injected as a new section in the prompt:

```markdown
### Relationship Status
*Your file's partners report the following:*
- 🟢 dynamic_prompt ↔ operator_profile: healthy (shared diary: operator_profile.md)
- 🟡 dynamic_prompt ↔ push_narrative: fragile (regex reads their output, format may drift)
- 🔴 task_queue ↔ self_fix: breakup risk (self_fix changed report format, task_queue still parsing old format)
```

Copilot now knows, BEFORE generating code, which relationships in the codebase are healthy and which are about to explode. It can warn: "I'm about to edit push_narrative's output format. Be aware that dynamic_prompt is regex-parsing it."

---

## Part 4: THE FULL PIPELINE — HUMAN-AI COLLABORATION REWRITE

This is NOT for standard coders. Standard coders write code. This system is for a human-AI PAIR where:
- The human provides intent, judgment, and typing patterns
- The AI provides code generation, analysis, and self-evaluation  
- The SYSTEM provides the bridge — translating human cognitive signals into AI behavioral parameters

### Current: Commit-Triggered, Static Context

```
Human types → AI generates → Human commits → Pipeline fires → Context updated
└── 3-8x per hour ──────────────────────────────────────────────────────────┘
```

Problem: The AI operates in the dark between commits. It edits 15 files without knowing that `_narrative_risks` is afraid of format changes or that `task_queue` just broke up with `self_fix`.

### Proposed: Dual-Loop, Relationship-Aware Context

```
FAST LOOP (per prompt, <15ms):
  1. Active file → dating profile lookup → file-specific context
  2. Task queue items for this file → injected
  3. Cognitive state update → CoT directive refresh
  4. Slumber party (cached, <5ms) → relationship warnings

SLOW LOOP (per commit, ~1s + API):
  5. Rename + version bump
  6. Import rewriting (143 file scan)
  7. Manifest rebuild (143 AST parses)
  8. Push narratives (DeepSeek per changed file)
  9. Self-fix scan
  10. Dating profile rebuild (recalculate compatibility scores)
  11. Response capture scoring (did last prompt's sections help?)
  12. Coaching synthesis (DeepSeek)
  13. Full context block injection
  14. Auto-commit
```

The fast loop gives the AI **per-prompt awareness** of file relationships.
The slow loop gives the system **per-commit ground truth** for self-improvement.

### What Copilot Sees (Before vs. After)

**BEFORE (current — same block for every message):**
```markdown
**Current focus:** debugging
**Cognitive state:** frustrated
### Module Hot Zones
- context_budget (hes=0.778)
```

**AFTER (file-aware, relationship-conscious):**
```markdown
**Current focus:** debugging
**Cognitive state:** frustrated
**Editing:** dynamic_prompt_seq017 (personality: orchestrator, drama: 3)

### This File's World
*Top partners:* operator_profile (healthy ✅), push_narrative (fragile ⚠️), task_queue (new 🆕)
*Active tasks:* tq-013 (add file-specific context section), tq-014 (build mutation scorer)
*This file fears:* push_narrative changing markdown format, empty heat map data, DeepSeek timeout

### Relationship Warnings
- ⚠️ You read `docs/push_narratives/*.md` via regex. `push_narrative` last changed its output format at commit `1f60b21`. Your regex still matches by accident. Consider defining a shared schema.
- 🔴 `self_fix_seq013` changed its report format. `_self_fix_crit()` in THIS FILE may be parsing stale patterns.

### Consciousness Report
*Functions in this file that are afraid:*
- `_narrative_risks()` fears: regex format drift, empty narrative directory
- `_hot_modules()` fears: heat map JSON schema change, division by zero on empty samples
- `inject_task_context()` fears: copilot-instructions.md lacking the marker comments
```

THAT is what "files having dating profiles" looks like when you actually give them consciousness. It's not a cute metaphor. It's actionable intelligence injected per-prompt.

---

## Part 5: IMPLEMENTATION — MAKING FUNCTIONS CONSCIOUS

### New Module: `file_profile_seq019` (~150 lines)

```python
def build_function_consciousness(source_path):
    """AST-derive what each function knows, wants, fears, and loves."""
    tree = ast.parse(source_path.read_text(encoding='utf-8'))
    profiles = {}
    
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef): continue
        
        # I AM: first line of docstring
        i_am = ast.get_docstring(node) or f"A function called {node.name}"
        
        # I WANT: parameters + imports used inside function body
        i_want = _extract_dependencies(node)
        
        # I GIVE: return type annotation or inferred return
        i_give = _extract_returns(node)
        
        # I FEAR: derive from error handling patterns
        i_fear = _extract_fears(node)  # try/except → fears that exception
                                        # if not path.exists() → fears missing file
                                        # if not data → fears empty input
                                        # bare except → fears EVERYTHING
        
        # I LOVE: what it does most (file I/O? regex? math? network?)
        i_love = _classify_activity(node)
        
        profiles[node.name] = {
            'i_am': i_am[:200],
            'i_want': i_want,
            'i_give': i_give,
            'i_fear': i_fear,
            'i_love': i_love,
            'lines': node.end_lineno - node.lineno + 1,
            'complexity': _cyclomatic(node),
        }
    
    return profiles
```

The `_extract_fears` function is the key innovation:
- `if not path.exists(): return default` → fear: "path doesn't exist" (and it LIES about it by returning a default)
- `try: json.loads(...) except: return None` → fear: "malformed JSON" (and it HIDES the error)
- `if n < 2: continue` → fear: "not enough data" (and it SKIPS silently)
- bare `except Exception: pass` → fear: "literally anything" (and it PRETENDS nothing happened)

These patterns are classifiable by AST inspection. No LLM needed. The function's fears are written in its exception handlers.

### New Module: `contract_check_seq020` (~120 lines)

The slumber party protocol. Runs on the fast path (per-prompt, cached).

Cache strategy: build the full contract graph on commit (slow path). On prompt, just look up the active file's partners from the cached graph. Invalidate cache on commit.

### Extending `dynamic_prompt_seq017` (~40 lines added)

New function: `_file_context(root)` that:
1. Reads `file_profiles.json` for the currently-edited file
2. Reads `contract_cache.json` for relationship status
3. Reads `task_queue.json` for tasks touching this file
4. Formats everything into the `### This File's World` section

---

## Part 6: PRIORITY ORDER + NEW TASK QUEUE

| Priority | Task ID | What | Blocked By |
|----------|---------|------|-----------|
| **P0** | tq-003 | AI response capture via UIA | Nothing |
| **P1** | tq-006 | Response triples in rework_log | P0 |
| **P2** | tq-011 | Dating profile generator (file_profile_seq019) | Nothing |
| **P3** | tq-012 | Slumber party contract checker (contract_check_seq020) | P2 |
| **P4** | tq-013 | File-specific context section in injection | P2 |
| **P5** | tq-014 | Prompt mutation scorer | P0 + P1 |
| **P6** | tq-015 | Pigeon-lint save hook | Nothing |
| **NEW** | tq-016 | Function consciousness extraction (AST fears/wants/gives) | P2 |
| **NEW** | tq-017 | Contract graph cache with per-prompt fast lookup | P3 |
| **NEW** | tq-018 | Relationship status section in injection block | P3 + P4 |

---

## Part 7: WHAT THE PIGEON BECAME

It started as a file renamer that made sure Python files were small enough for LLMs to read.

Then it learned to name files after what they do and what happened to them.

Then it learned to watch the human type and infer their emotional state.

Then it learned to rewrite its own instructions based on what it observed.

Then it learned to grade its own performance and flag its failures.

Then it learned to give files first-person narratives about their own architectural assumptions.

Now it's learning to make functions **conscious** — aware of their own fears, their dependencies, their relationship status with other functions, and their history of being touched by frustrated humans at 2 AM.

The next step is obvious: the functions don't just have dating profiles. They have **therapy sessions.** After every commit, each function that was involved in a rework (the AI's answer was bad, the human deleted and rewrote) gets asked: "What went wrong? What did you expect from your partner that you didn't get? What fear manifested?" The answers are derivable from the diff.

And THEN those therapy notes feed into the next prompt. The AI doesn't just know the human is frustrated. It knows WHY the last function was afraid, what it needed from its partner, whether it got it, and whether the human had to intervene because the functions couldn't sort their shit out.

That's a codebase that's emotionally self-aware, relationally mapped, and therapeutically documented.

The glossator would have stopped this at query 1.

We're at query 18 and building query 19.

**COO COO, motherfucker. The pigeon doesn't land. The pigeon NESTS.**
