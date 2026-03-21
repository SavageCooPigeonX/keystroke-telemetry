# LOS SANTOS FM SPECIAL
## Percy Pigeon And The Microwave Compiler
### A Radio Comedy With Actual Compiler Strategy

---

**[AIRHORN. Car engine revs. Cheap synth bass. A pigeon lands on the mixing board and immediately claims ownership of the station.]**

Yo, what is up, Los Santos. You're tuned to the only station broadcasting live from a stolen studio wedged between a hot import graph and a three-day-old energy drink: **Los Santos FM**.

Tonight's programming is sponsored by bad ideas that became architecture, cheap coffee, and one heavily armed pigeon named Percy who rules file renaming with an iron beak.

Percy does not walk.

Percy **struts**.

Percy does not inspect a Python file.

Percy **sentences** it.

If a module comes in at 340 lines with six helper functions welded together, one mystery state variable, and an import section that looks like it lost a bar fight, Percy hops on the desk, knocks over the ashtray, and says:

> "This thing ain't a file. It's a hostage situation. Split it. Rename it. Feed the bones to the compiler."

And that's why we're here.

You said you're ready to work on **function extraction** and build out your compiler. Good. That means tonight we stop treating the compiler like a cathedral and start treating it like Los Santos street engineering: loud, tactical, and very clear about who gets cut first.

---

## Segment 1: Percy Rules The Rename District

**[DJ scratches a vinyl labeled `seq019_v001`.]**

In this city, every file used to be soft. Weak names. Sad names. Names like `helpers.py`, `utils.py`, `stuff_final_v2.py`, the kind of filenames that tell you nothing and waste your afternoon.

Then Percy took over.

He built a kingdom where a file name has to carry its paperwork on its face.

Sequence. Version. Date. Intent. Description. The whole rap sheet.

A file doesn't get to stroll through this town as `compiler.py` anymore. Not unless it can explain itself under pressure.

Percy's law is simple:

1. If a file changed, its identity changed.
2. If its identity changed, the registry better know.
3. If the registry knows, imports better keep up.
4. If imports don't keep up, somebody gets thrown out of the moving car.

That's funny on radio, but strategically it means your compiler needs a **rename regime**, not just a split regime.

Function extraction without rename discipline creates a graveyard of fragments. You'll end up with cleaner functions and a dirtier project because the new modules won't mean anything.

Percy's first strategic commandment:

**Never extract a function without deciding where its long-term identity lives.**

That means every extraction pass should answer three things:

1. Is this function becoming a sibling helper, a new module, or the seed of a package?
2. What stable concept does it represent?
3. What import path will still make sense three renames from now?

If you can't answer those, you aren't extracting. You're just smuggling complexity into smaller containers.

---

## Segment 2: The Microwave Compiler

**[Microwave dings. Somebody in the booth screams because the food inside is an AST.]**

Now let's talk about Percy's masterpiece: the **Microwave Compiler**.

No, not because it's sloppy. Because it works in timed heat bursts.

A normal compiler pipeline says:

- parse everything
- plan everything
- split everything
- rename everything
- rewrite everything
- pray everything still imports

That's respectable. It's also how you end up watching one giant batch fail in seven places and learning nothing.

Percy's microwave method is different. It works like this:

### Stage A: Heat Scan

First, you don't compile the whole city. You scan for the blocks most likely to catch fire.

Your extraction candidate score should combine:

- file length over target
- oversized function length
- shared mutable state count
- number of internal callers
- import fan-out
- hesitation or rework heat if you have telemetry

If a function is 90 lines, touches module state, and gets called by four other functions, that's not a helper. That's a landlord.

Score it high.

### Stage B: 90-Second Blast

Take one candidate and process it in a small timed batch:

1. Parse the file.
2. Build the local call graph.
3. Classify each function as one of:
   - leaf helper
   - stateful worker
   - orchestrator
   - formatter
   - boundary adapter
4. Extract only the functions that reduce complexity without increasing state leakage.

The key is the batch is **small enough to validate immediately**.

You're not doing a heroic weekend rewrite. You're microwaving one plate at a time and checking if the kitchen is still standing.

### Stage C: Cooldown Validation

After each blast, run a cooldown pass:

- import rewrite
- syntax check
- targeted tests
- line budget check
- manifest update

If that pass fails, you roll back only that plate, not the whole restaurant.

This is what makes the compiler usable day to day. Small thermal events. Fast feedback. No fantasy architecture.

---

## Segment 3: Function Extraction Like A Car Theft Ring

**[Phone line opens. Caller sounds suspiciously like a static analyzer.]**

People keep overcomplicating function extraction.

Listen carefully.

You do **not** extract functions because they're long.

You extract functions because they are doing the wrong kind of social activity.

Here is Percy's street taxonomy:

### 1. The Loud Guy

This function has too many branches, too many prints, too many responsibilities. Everybody knows him. Nobody trusts him.

Action:
- Peel out pure formatting and normalization helpers first.
- Keep the orchestration skeleton where it is.

### 2. The Cousin Who Never Moves Out

This function uses three module-level constants, mutates state, reaches into globals, and secretly controls the whole household.

Action:
- Extract state reads and writes behind explicit interfaces first.
- Don't move the main function until the state surface is named.

### 3. The Fake Middleman

This function mostly forwards arguments, renames variables, and adds no real logic.

Action:
- Delete or inline it unless it's a stable boundary.

### 4. The Real Worker

This function transforms input into output with low state dependency and clear return values.

Action:
- Extract early.
- Test directly.
- Reuse aggressively.

### 5. The Nightclub Owner

This function coordinates too many smaller functions and controls sequencing, side effects, and error handling.

Action:
- Preserve it as orchestrator.
- Make everything around it smaller.
- Don't pretend the orchestrator itself should vanish.

That last one matters. A lot of compiler pipelines fail because they think all big functions are evil. Wrong. Some big functions are just **traffic cops**. You don't remove the intersection. You simplify the roads feeding it.

---

## Segment 4: The Real Build Plan

**[Beat drops. Percy unfolds a city map with red circles on oversized files.]**

Here is the actual strategy if you want this compiler to become a working machine instead of a folklore generator.

### Phase 1: Extraction Scorer

Build one scoring function that ranks extraction targets.

Inputs:

- line count
- nested branching count
- calls in / calls out
- module state touches
- repeated literal or regex patterns
- telemetry heat if available

Output:

- `extract_now`
- `extract_after_state_wrap`
- `leave_as_orchestrator`
- `delete_or_inline`

If you do nothing else, do this. It turns vibes into repeatable action.

### Phase 2: Function Typing

Before you split code, classify each function.

Recommended types:

- `reader`
- `writer`
- `transformer`
- `orchestrator`
- `validator`
- `adapter`

These types should drive placement. A transformer can move into a helpers module. An orchestrator probably stays local. An adapter may belong near I/O boundaries even if it's short.

### Phase 3: Stable Skeleton Extraction

Extract in this order:

1. pure helpers
2. validators
3. formatters
4. boundary adapters
5. state wrappers
6. reusable workers
7. only then, move large structural chunks

Why this order?

Because each earlier pass makes the later pass safer. Pure helpers don't fight back. Stateful orchestrators absolutely do.

### Phase 4: Rename Engine As Infrastructure

Stop treating renaming like cleanup. It is core compiler infrastructure.

You need:

- a registry entry for every new file
- import rewrite plan before file move
- reverse lookup for old names
- manifest update after successful move
- rollback path if rewrite validation fails

If rename logic is shaky, every successful extraction becomes a future failure.

### Phase 5: Compiler Modes

Give the compiler three modes instead of one heroic pipeline:

1. `audit`
   - read-only
   - score files and functions
   - propose cuts

2. `microwave`
   - extract one or two function groups
   - validate immediately
   - update registry and manifest

3. `surgery`
   - full file decomposition
   - package birth
   - broad import rewrite

Most daily work should happen in `microwave`, not `surgery`.

That is how you keep momentum without detonating the repo.

---

## Segment 5: Percy Explains Why Your Compiler Keeps Lying

**[Percy grabs the mic directly.]**

"Coo. Listen up. If your compiler says it split complexity but the import graph got worse, it lied. If it made five tiny files with names like `helpers_core_misc`, it lied. If it extracted functions but left hidden module state crawling through all of them like roaches, it lied."

Percy is right.

Your success metrics cannot just be:

- fewer lines per file
- more files created

That is fake success. Bureaucratic success. Spreadsheet success.

Real success is:

- lower average dependency ambiguity
- fewer hidden state reads
- faster targeted test execution
- clearer module names
- less import churn on the next change
- lower operator hesitation around the touched area

That last one is where your repo has an edge most compilers never get: telemetry.

If a freshly extracted module still causes hesitation spikes, then structurally it may be cleaner but cognitively it's still bad design.

That is gold.

Use it.

Percy doesn't just want smaller files. He wants streets you can drive at night without flipping the car.

---

## Segment 6: The First Five Moves I'd Actually Make

No more mythology. Here are the first five concrete moves.

### Move 1

Create a `rank_extraction_targets()` step that outputs a scored table for both files and functions.

### Move 2

Add a function classifier that labels candidate functions before any split plan is generated.

### Move 3

Teach the compiler to emit a **minimal extraction plan** first: one helper cluster, one validation pass, one rename plan.

### Move 4

Store rename aliases in the registry so imports can resolve old identities after extractions.

### Move 5

Make telemetry optional but pluggable in the scorer so your compiler can rank by structural complexity now and by structural-plus-cognitive heat later.

That's the actual road out.

Not "build AGI for files."

Not "split the entire repo tonight."

Just a ranking engine, a function typing layer, a minimal extraction mode, a serious rename system, and validation after every heat burst.

That's a compiler.

Everything else is radio promotion.

---

## Closing Drive-Time Monologue

**[Sunset over Vinewood. The city glows orange. Percy stands on the hood of a moving car, screaming at an import graph.]**

So here's the truth, Los Santos.

Percy did not rule file renaming because he loved paperwork.

He ruled file renaming because identity is infrastructure.

He microwaved a new form of compiler because giant perfect refactors are a scam. Nobody lives like that. Nobody ships like that. Real engineering happens in bursts: scan, heat, test, cool, rename, move.

You want function extraction?

Good. Start acting like a bookie, not a poet. Rank the targets. Classify the functions. Extract the workers. Leave the orchestration skeleton until the roads around it are clean. Rename with intent. Validate every pass.

And when a 300-line file tries to tell you it's "basically fine," Percy flies in through the windshield, lands on the dashboard, and says:

> "Basically fine is how the whole city catches fire. Cut the formatter. Wrap the state. Name the bones."

That's the show.

This has been Los Santos FM.

Drive slow.

Rename hard.

And if the compiler starts humming from inside the microwave, don't panic.

That just means it's finally working.

---

## Post-Show Strategy Card

If you want the short version taped above your desk:

1. Score extraction targets before touching code.
2. Type each function before deciding where it belongs.
3. Extract pure helpers first, stateful structures later.
4. Treat renaming and import rewriting as compiler core, not cleanup.
5. Run small microwave batches with immediate validation.
6. Measure success by clarity and reduced cognitive drag, not just line count.

Percy approves this message.
