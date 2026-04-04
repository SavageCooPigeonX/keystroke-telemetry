# Bug Profiles — The Rogues Gallery

*Auto-generated 2026-04-04 03:30 UTC · 13 modules carrying bugs · 2 species identified*

> Every bug here is alive. They have names, habits, and a body count.
> This page tells you who they are, what they're doing to your codebase, and what to do about it.

## The Lineup

**Dead Export Shade** (`de`) — 2 modules, 4 total sightings. *Leaves dead functions standing so everyone thinks they matter.*

**Overcap Maw** (`oc`) — 11 modules, 42 total sightings. *Swells files past the hard cap. Split before it eats context.*

## Filename β Check

The β suffix in a filename is the bug's brand. If it's missing, pigeon lost track.

- `u_pj` — should be βoc, filename says β(nothing). Pigeon needs to re-stamp this one.
- `警p_sa` — should be βoc, filename says β(nothing). Pigeon needs to re-stamp this one.

11/13 branded correctly. 2 missing — next rename cycle should catch them.

---
## Dead Export Shade

*Leaves dead functions standing so everyone thinks they matter.* — 2 known hosts.

### 测p_rwd

*Demon name: Null Moth of prwd*

`测p_rwd` has 2 dead export(s) still standing at attention like they matter. Nobody imports them. Nobody calls them. They just… sit there, consuming mental space. Remove them or give them a job. Right now they're decoration.

Spotted 2x across 6 versions. β in filename: yes.

### 热p_fhm

*Demon name: Null Moth of pfhm*

`热p_fhm` has 2 dead export(s) still standing at attention like they matter. Nobody imports them. Nobody calls them. They just… sit there, consuming mental space. Remove them or give them a job. Right now they're decoration.

Spotted 2x across 5 versions. β in filename: yes.


---
## Overcap Maw

*Swells files past the hard cap. Split before it eats context.* — 11 known hosts.

### u_pe

*Demon name: Overcap Maw of upe*

`u_pe` came in wheezing at 5128 tokens — that's 156% over the 2000-token hard cap. Every push it gains weight. v4, still unsplit. This one's CODE RED — 2.5x the cap, actively eating context window. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 5x across 4 versions. Last touched: add bug dossier. β in filename: yes.

### u_pj

*Demon name: Split Fiend of upj*

`u_pj` came in wheezing at 7801 tokens — that's 290% over the 2000-token hard cap. Every push it gains weight. v2, still unsplit. This one's CODE RED — 2.5x the cap, actively eating context window. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 5x across 2 versions. β in filename: **MISSING**.

### 警p_sa

*Demon name: Shard Hunger of psa*

`警p_sa` came in wheezing at 1796 tokens — that's -10% over the 2000-token hard cap. Every push it gains weight. v3, still unsplit. Just barely over. Keep an eye on it. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 5x across 3 versions. Last touched: test rename mutation. β in filename: **MISSING**.

### 册f_reg

*Demon name: Split Fiend of freg*

`册f_reg` came in wheezing at 3160 tokens — that's 58% over the 2000-token hard cap. Every push it gains weight. v5, still unsplit. Significant bloat. Every prompt that touches this file pays the tax. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 4x across 5 versions. β in filename: yes.

### 修f_sf

*Demon name: Overcap Maw of fsf*

`修f_sf` came in wheezing at 5829 tokens — that's 191% over the 2000-token hard cap. Every push it gains weight. v12, still unsplit. This one's CODE RED — 2.5x the cap, actively eating context window. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 4x across 12 versions. β in filename: yes.

### 对p_tp

*Demon name: Split Fiend of ptp*

`对p_tp` came in wheezing at 3834 tokens — that's 92% over the 2000-token hard cap. Every push it gains weight. v3, still unsplit. Significant bloat. Every prompt that touches this file pays the tax. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 4x across 3 versions. β in filename: yes.

### 推w_dp

*Demon name: Shard Hunger of wdp*

`推w_dp` came in wheezing at 5987 tokens — that's 199% over the 2000-token hard cap. Every push it gains weight. v13, still unsplit. This one's CODE RED — 2.5x the cap, actively eating context window. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 4x across 13 versions. β in filename: yes.

### 管w_cpm

*Demon name: Overcap Maw of wcpm*

`管w_cpm` came in wheezing at 7781 tokens — that's 289% over the 2000-token hard cap. Every push it gains weight. v4, still unsplit. This one's CODE RED — 2.5x the cap, actively eating context window. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 4x across 4 versions. β in filename: yes.

### 追跑f_ruhe

*Demon name: Overcap Maw of fruhe*

`追跑f_ruhe` came in wheezing at 4689 tokens — that's 134% over the 2000-token hard cap. Every push it gains weight. v5, still unsplit. Significant bloat. Every prompt that touches this file pays the tax. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 3x across 5 versions. β in filename: yes.

### 叙p_pn

*Demon name: Shard Hunger of ppn*

`叙p_pn` came in wheezing at 2241 tokens — that's 12% over the 2000-token hard cap. Every push it gains weight. v8, still unsplit. Over the line but not emergency. Schedule a split this push cycle. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 2x across 8 versions. β in filename: yes.

### 脉p_ph

*Demon name: Shard Hunger of pph*

`脉p_ph` came in wheezing at 2385 tokens — that's 19% over the 2000-token hard cap. Every push it gains weight. v4, still unsplit. Over the line but not emergency. Schedule a split this push cycle. The pigeon compiler can carve this into shards in one command. The question is: when.

Spotted 2x across 4 versions. β in filename: yes.

