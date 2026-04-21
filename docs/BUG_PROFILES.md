# Bug Profiles — The Rogues Gallery

*Auto-generated 2026-04-21 23:15 UTC · 13 modules carrying bugs · 2 species identified*

> Every bug here is alive. They have names, habits, and a body count.
> This page tells you who they are, what they're doing to your codebase, and what to do about it.

## The Lineup

**Dead Export Shade** (`de`) — 3 modules, 10 total sightings. *Leaves dead functions standing so everyone thinks they matter.*

**Overcap Maw** (`oc`) — 13 modules, 29 total sightings. *Swells files past the hard cap. Split before it eats context.*

## Filename β Check

The β suffix in a filename is the bug's brand. If it's missing, pigeon lost track.

- `file_sim` — should be βdeoc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `intent_numeric` — should be βdeoc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `interlink_debugger` — should be βoc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `tc_10q` — should be βoc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `tc_context_agent` — should be βdeoc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `tc_gemini` — should be βoc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `tc_observatory` — should be βoc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `tc_popup` — should be βoc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `tc_sim_engine` — should be βoc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `tc_sim` — should be βoc, filename says β(nothing). Pigeon needs to re-stamp this one.

3/13 branded correctly. 10 missing — next rename cycle should catch them.

---
## Dead Export Shade

*Leaves dead functions standing so everyone thinks they matter.* — 3 known hosts.

### intent_numeric

*Demon name: Export Shade of intentnu*

`intent_numeric` has 1 dead export(s) still standing at attention like they matter. Nobody imports them. Nobody calls them. They just… sit there, consuming mental space. Remove them or give them a job. Right now they're decoration.

Spotted 4x across 4 versions. β in filename: **MISSING**.

### file_sim

*Demon name: Dead Echo of filesim*

`file_sim` has 1 dead export(s) still standing at attention like they matter. Nobody imports them. Nobody calls them. They just… sit there, consuming mental space. Remove them or give them a job. Right now they're decoration.

Spotted 3x across 5 versions. β in filename: **MISSING**.

### tc_context_agent

*Demon name: Null Moth of tccontex*

`tc_context_agent` has 1 dead export(s) still standing at attention like they matter. Nobody imports them. Nobody calls them. They just… sit there, consuming mental space. Remove them or give them a job. Right now they're decoration.

Spotted 3x across 4 versions. β in filename: **MISSING**.


---
## Overcap Maw

*Swells files past the hard cap. Split before it eats context.* — 13 known hosts.

### intent_numeric

*Demon name: Overcap Maw of intentnu*

`intent_numeric` came in wheezing at 6819 tokens — that's 241% over the 2000-token hard cap. Every push it gains weight. v4, still unsplit. This one's CODE RED — 2.5x the cap, actively eating context window. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 4x across 4 versions. β in filename: **MISSING**.

### file_sim

*Demon name: Shard Hunger of filesim*

`file_sim` came in wheezing at 4116 tokens — that's 106% over the 2000-token hard cap. Every push it gains weight. v5, still unsplit. Significant bloat. Every prompt that touches this file pays the tax. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 3x across 5 versions. β in filename: **MISSING**.

### tc_context_agent

*Demon name: Split Fiend of tccontex*

`tc_context_agent` came in wheezing at 6804 tokens — that's 240% over the 2000-token hard cap. Every push it gains weight. v4, still unsplit. This one's CODE RED — 2.5x the cap, actively eating context window. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 3x across 4 versions. β in filename: **MISSING**.

### tc_gemini

*Demon name: Split Fiend of tcgemini*

`tc_gemini` came in wheezing at 11314 tokens — that's 466% over the 2000-token hard cap. Every push it gains weight. v4, still unsplit. This one's CODE RED — 2.5x the cap, actively eating context window. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 3x across 4 versions. Last touched: live copilot layer. β in filename: **MISSING**.

### w_gpmo

*Demon name: Split Fiend of wgpmo*

`w_gpmo` came in wheezing at 6982 tokens — that's 249% over the 2000-token hard cap. Every push it gains weight. v11, still unsplit. This one's CODE RED — 2.5x the cap, actively eating context window. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 2x across 11 versions. β in filename: yes.

### tc_observatory

*Demon name: Overcap Maw of tcobserv*

`tc_observatory` came in wheezing at 11262 tokens — that's 463% over the 2000-token hard cap. Every push it gains weight. v2, still unsplit. This one's CODE RED — 2.5x the cap, actively eating context window. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 2x across 2 versions. β in filename: **MISSING**.

### tc_popup

*Demon name: Split Fiend of tcpopup*

`tc_popup` came in wheezing at 6993 tokens — that's 250% over the 2000-token hard cap. Every push it gains weight. v4, still unsplit. This one's CODE RED — 2.5x the cap, actively eating context window. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 2x across 4 versions. β in filename: **MISSING**.

### tc_sim_engine

*Demon name: Overcap Maw of tcsimeng*

`tc_sim_engine` came in wheezing at 2627 tokens — that's 31% over the 2000-token hard cap. Every push it gains weight. v4, still unsplit. Over the line but not emergency. Schedule a split this push cycle. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 2x across 4 versions. β in filename: **MISSING**.

### tc_sim

*Demon name: Shard Hunger of tcsim*

`tc_sim` came in wheezing at 14095 tokens — that's 605% over the 2000-token hard cap. Every push it gains weight. v2, still unsplit. This one's CODE RED — 2.5x the cap, actively eating context window. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 2x across 2 versions. β in filename: **MISSING**.

### u_pj

*Demon name: Split Fiend of upj*

`u_pj` came in wheezing at 10995 tokens — that's 450% over the 2000-token hard cap. Every push it gains weight. v6, still unsplit. This one's CODE RED — 2.5x the cap, actively eating context window. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 2x across 6 versions. β in filename: yes.

### 脉p_ph

*Demon name: Shard Hunger of pph*

`脉p_ph` came in wheezing at 2607 tokens — that's 30% over the 2000-token hard cap. Every push it gains weight. v6, still unsplit. Over the line but not emergency. Schedule a split this push cycle. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 2x across 6 versions. β in filename: yes.

### interlink_debugger

*Demon name: Shard Hunger of interlin*

`interlink_debugger` came in wheezing at 3336 tokens — that's 67% over the 2000-token hard cap. Every push it gains weight. v2, still unsplit. Significant bloat. Every prompt that touches this file pays the tax. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 1x across 2 versions. Last touched: initial build -. β in filename: **MISSING**.

### tc_10q

*Demon name: Split Fiend of tc10q*

`tc_10q` came in wheezing at 2843 tokens — that's 42% over the 2000-token hard cap. Every push it gains weight. v2, still unsplit. Over the line but not emergency. Schedule a split this push cycle. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 1x across 2 versions. Last touched: initial build -. β in filename: **MISSING**.

