# Numeric Prompt Encoding: A Workplace Comedy In Five Incidents

## Incident 1: The Router Shows Up To Work With No Memories

The numeric prompt encoder did fire per query.

It took the prompt, invited the deleted words to the meeting, built `intent_keys`,
and wrote:

- `logs/context_selection.json`
- `logs/context_selection_history.jsonl`
- `logs/tc_steer.json`

Then it stared at an empty `intent_matrix.json` and said:

> "I would love to route this prompt to a file, but I have never met a file in my life."

This was not a logic failure. It was a childhood problem. The matrix had:

- `0` words
- `0` tracked files
- `0` touches

So the first answer was empty because the repo had a router, but no learned
roads.

## Incident 2: The First Touch Becomes A Personality Trait

After `log-edit` began training the numeric surface, the same query selected:

- `codex_compat` with confidence around `0.096`

That is the right shape. The model is not "thinking" yet. It is forming a
habit. A prompt says "numeric prompt encoding dynamic context select"; a file
gets edited; the graph quietly writes that down.

The file has become the office employee who hears "context selection" and
immediately swivels around in its chair.

## Incident 3: The Dangerous Intern Named Parallel Logging

Three parallel edit submissions tried to train the same matrix at once. The
last writer won, and two file touches fell out of the story.

This is the first real engineering focus:

> Make intent training writes serialized, locked, or batched.

No autonomous loop should learn by throwing three sticky notes at a fan and
hoping the correct one lands in `intent_matrix.json`.

## Incident 4: The Repo Keeps Trying To Be Seven Products In A Coat

The strongest product hiding here is not "keystroke telemetry."

It is:

> A local intent observatory for AI-assisted coding loops.

The core stack should be:

1. **Prompt Event Spine**
   Every Codex/Copilot query becomes explicit state: prompt, deleted words,
   rewrites, response, files edited, tests run.

2. **Numeric Intent Graph**
   Prompt tokens and deleted-word tokens learn file identities from actual
   edits. No LLM call. Just "when the human says this, these files usually
   move."

3. **Dynamic Context Select**
   On every query, route likely files into context. Start with numeric routing,
   then use LLM context only as seasoning.

4. **File Identity Graph**
   Each file has an identity: what it does, what prompts wake it up, what files
   it argues with, how often it causes rework, and what it is becoming.

5. **Narrative Compression Observatory**
   The file graph explains itself in human language. Comedy is useful here
   because jokes are compressed structure: if a file can make fun of its own
   job, a human can remember what it is.

## Incident 5: The Files Start Doing Standup

This is the observatory I would build:

- Left pane: prompt stream with deleted intent highlighted.
- Middle pane: numeric context picks and confidence.
- Right pane: file identity graph.
- Bottom pane: "files doing standup."

Example:

> `codex_compat.py`: "I used to be a bridge. Now I am a customs office for
> every thought that wants to become training data. Please form one line."

> `intent_numeric`: "I do not understand you emotionally, but I have assigned
> integers to your nouns and frankly that is healthier."

> `context_select_agent`: "I am not guessing. I am statistically remembering
> which file got blamed last time."

That is not decoration. It is narrative compression. A file's joke is its
compressed role, failure mode, and routing identity.

## Where To Focus

Focus on one clean loop:

`prompt -> deletion analytics -> numeric context select -> edit -> train graph -> narrative file memory -> next prompt`

Do not focus on:

- global keystroke capture as the center of the product
- hidden autonomous daemons
- more rename machinery
- dashboards that do not change what the next prompt sees
- LLM calls before the numeric graph has had a chance to answer

## The Sharp Recommendation

Make `codex_compat.py` the front door for now.

Then build the observatory around these files:

- `logs/codex_state.md`
- `logs/context_selection_history.jsonl`
- `logs/intent_matrix.json`
- `logs/numeric_surface_seq001_v001.json`
- `logs/training_pairs.jsonl`
- `logs/unsaid_reconstructions.jsonl`

Once that feels good, extract a smaller package:

> `intent-observatory`: explicit prompt telemetry plus numeric file routing plus
> readable file self-narratives.

That is the repo's real center. Not "record keystrokes." More like:

> "Watch human intent condense into code, then teach the codebase to recognize
> the next intent faster."
