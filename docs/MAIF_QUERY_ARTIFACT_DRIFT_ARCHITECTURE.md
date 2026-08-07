# MAIF Query Artifact Drift Architecture

## Purpose

This document captures the safe integration plan for moving MAIF toward drift-primary query and artifact intelligence without damaging the current auditor.

The corrected architecture is:

> Queries begin as blank measurement surfaces. Query monitoring senses the public information space over time. Query artifact leaderboards rank what surfaced inside the query. Entity artifact leaderboards rank what matters to a durable entity graph. Grok maps sources, artifacts, entities, duplicates, and information-space edges. Compound drift stages source-backed probes. The existing auditor remains the profile mutation authority.

This is not "query bad, artifact good" and it is not "artifact primary." It is drift-primary:

```text
Queries sense.
Grok maps.
Artifacts explain.
Leaderboards rank.
Staged probes verify.
Predictions can move.
Profiles compile only after gated confidence.
```

## Current implementation findings

The current repository is not the full production LinkRouter/MyAIFingerprint app. It contains the local Pigeon/IRT/query-monitoring substrate and documentation describing the external production auditor.

### Production auditor is external

`docs/LINKROUTER_AI_MAP.md` describes the production MAIF stack as living in the LinkRouter.ai codebase:

- `production_auditor/`: 8-model queries, consensus building, drift detection, entity extraction, persona building, news auditing.
- `integrations/`: GPT, Gemini, Grok, DeepSeek, Perplexity, Qwen, Kimi, GLM, OpenRouter, Claude.
- `consensus/`: Gemini synthesis with Grok fallback.
- `storage_maif/`: entity CRUD, link storage, consensus storage, shard writes, credit engine, MFS.
- `drift_tracker/`: perception drift over time.

The local repo therefore should not pretend to mutate production entity truth. It should define the staging contracts and local proof surfaces that can be bridged into the production auditor later.

### Current query monitoring is a seed catalog and local queue

`scripts/generate_query_monitoring_profiles.py` generates static query monitoring profiles with:

- `schema: maif_query_monitoring_audits/v1`
- expected models: `gpt`, `claude`, `gemini`, `grok`, `deepseek`, `perplexity`, `local_baseline`
- `coverage_status: not_run`
- `MODEL_COVERAGE_DRIFT`
- `requires_audit: true`
- `do_not_update_entity_profiles_from_model_answers: true`

`pigeon_brain/ui/src/QueryMonitoring.jsx` fetches `/query_monitoring_audits.json`, renders searchable query cards, and queues "Run" actions into `localStorage` under `query_monitoring_trigger_queue`.

There is no live backend worker in this repo that consumes that queue, calls Grok, runs multi-model consensus, stores model answers, builds query artifact leaderboards, or mutates entity profiles.

### Current Grok architecture in this repo is role-level, not a live sensor client

The local repo references Grok in three main ways:

1. Expected query target in `scripts/generate_query_monitoring_profiles.py`.
2. External production map in `docs/LINKROUTER_AI_MAP.md`, where the full product has Grok integrations and Grok fallback in consensus.
3. Role inference in `scripts/analyze_prompt_behavior.py`, where Grok is framed as retrieval/probe intelligence: void search, artifact extraction, entity expansion, and network discovery.

That means the Grok sensor role is architecturally present, but the local query monitoring surface does not yet contain a Grok HTTP client, async Grok runner, artifact extraction worker, query consensus drift job, or persistent results table.

### Current query consensus drift is left out of initial query monitoring

The answer to the user's specific question is:

> In this workspace, asynchronous query consensus drift is not running as part of initial query monitoring. It is represented as seed metadata and pending architecture, not as an implemented async pipeline.

Evidence:

- Query profiles mark expected models but `observed_models` is empty.
- `MODEL_COVERAGE_DRIFT` is emitted as a placeholder finding.
- The UI queues runs locally only.
- No worker consumes query triggers.
- No Grok client or multi-model consensus runner is present locally.
- Profile mutation from model answers is explicitly blocked by `do_not_update_entity_profiles_from_model_answers`.

Therefore, the safe design is not to bolt consensus drift directly into the initial query UI. Instead, implement it as an asynchronous staged worker with its own result store and gating layer.

### Current IRT stage-only gate is the right safety pattern

`build/pigeon_legacy/src/irt_field_profile_seq001_v001.py` already has a stage-only evidence packet path:

- `build_irt_evidence_packet(...)`
- `audit_irt_evidence_packet(...)`

The packet is explicitly:

```text
mode: stage_only
stage_only: true
```

The auditor decision explicitly returns:

```text
durable_profile_mutated: false
```

This is exactly the pattern the query/artifact drift system should use:

1. Detect.
2. Rank.
3. Stage.
4. Probe.
5. Emit mutation candidates.
6. Let the existing auditor/profile compiler decide durable changes.

### Current artifact coupling exists partially but is not the main path

The local IRT simulator has live artifact drift scoring in the main artifact probe path, and it also has Bayesian coupling helpers such as `_artifact_edge_weight`, `_coupled_prior`, `coupling_edges`, `artifact_memory`, and `source_reliability`.

However, the Bayesian coupling path is not the main query monitoring flow. The current query monitoring artifacts do not populate with model comments, query drift scores, source coupling, or full artifact leaderboard state.

That gap should be fixed by adding first-class query and entity artifact leaderboard contracts before touching durable profiles.

## Architectural principles

### 1. Query starts blank

A monitored query should begin as a measurement container, not as an entity mutation request.

Bad:

```text
query = update Trump profile
```

Correct:

```text
query = blank public-info-space measurement surface
```

The system measures what appears:

- links
- source domains
- primary-source candidates
- derivative artifacts
- entities
- claims
- repeated phrases
- model disagreement
- novelty
- drift against previous runs
- prediction relevance

Only after the measurement pass should the system map artifacts and claims onto entity graphs.

### 2. Query artifact leaderboard and entity artifact leaderboard are separate

There must be two leaderboards.

#### Query Artifact Leaderboard

This belongs to the query series or query run.

It answers:

> What did the public information space surface for this query?

It should feel like filtering a comment section:

- top mentioned links
- newest links
- high novelty
- high query drift
- high source originality
- high duplication/amplification
- primary-source candidates
- high contradiction potential
- high prediction relevance
- high model disagreement
- fastest rising artifacts
- top linked entities

This leaderboard is not entity truth. It is a query-local measurement.

#### Entity Artifact Leaderboard

This belongs to the entity profile workspace.

It answers:

> Which artifacts matter most to this entity graph?

It should rank:

- entity coupling
- intent-key coupling
- artifact drift
- source reliability
- source originality
- contradiction potential
- novelty
- model/source mentions
- prediction relevance
- probe eligibility
- mutation-candidate status

The entity artifact leaderboard is the working intelligence surface for Grok and operators.

### 3. Artifact intent cards power the entity workspace

The entity leaderboard should not be a raw link table. Its primary work object should be an artifact intent card.

```json
{
  "schema": "maif_artifact_intent_card/v1",
  "artifact_id": "artifact_...",
  "canonical_url": "https://...",
  "title": "...",
  "source_domain": "...",
  "source_kind": "primary_source | reporting | commentary | social | model_citation | unknown",
  "linked_entities": [],
  "matched_intent_keys": [],
  "claim_summary": "...",
  "drift_reason": "...",
  "source_coupling": {
    "source_reliability": 0.0,
    "source_originality": 0.0,
    "primary_source_likelihood": 0.0,
    "derivative_cluster_id": null,
    "entity_overlap": 0.0,
    "intent_key_overlap": 0.0,
    "claim_overlap": 0.0,
    "contradiction_potential": 0.0
  },
  "scores": {
    "query_drift": 0.0,
    "entity_coupling": 0.0,
    "novelty": 0.0,
    "prediction_relevance": 0.0,
    "probe_eligibility": 0.0
  },
  "staging": {
    "status": "watch | staged | probed | mutation_candidate | rejected_noise",
    "suggested_probe_depth": "grok_only | light_panel | panel | full_auditor",
    "mutation_allowed": false
  }
}
```

These cards are compact enough to inject into staged probes without dumping three or four full profiles into every query monitoring run.

### 4. Source coupling must become first-class

The current issue is not just "we need artifacts." It is that artifacts need source coupling and drift scoring that can be reused by both query surfaces and entity surfaces.

Separate the terms:

- Source reliability: is the source likely trustworthy?
- Source originality: is this the first or primary source, or recycled commentary?
- Source coupling: how strongly does this artifact/source connect to this query, entity, claim, or intent key?
- Artifact drift: how much does this artifact change, contradict, or mutate the current graph?
- Compound drift: how often this source/artifact/claim creates pressure across multiple query surfaces over time.

Recommended scoring object:

```json
{
  "source_coupling": {
    "primary_source_likelihood": 0.91,
    "source_reliability": 0.84,
    "source_originality": 0.88,
    "derivative_cluster_id": "cluster_x",
    "mentioned_by_models": ["grok", "perplexity"],
    "mentioned_by_queries": ["trump_iran_strategy", "war_powers_query"],
    "entity_overlap": 0.76,
    "intent_key_overlap": 0.81,
    "claim_overlap": 0.69,
    "contradiction_potential": 0.72
  }
}
```

### 5. Profile mutation is downstream

Profile mutation should happen only after:

1. query drift is observed,
2. artifacts are classified,
3. entity/source/claim matching is complete,
4. compound drift has enough support,
5. staged probes run at the chosen target depth,
6. confidence threshold is met,
7. the existing auditor/profile compiler accepts the mutation candidate.

This preserves the current auditor.

## Recommended end-state flow

```text
Blank monitored query
   |
   v
Query measurement run
   |
   v
Grok/search sensor maps links, sources, entities, claims, duplicate clusters
   |
   v
Query Artifact Leaderboard
   |
   v
Entity/source/claim matching
   |
   v
Entity Artifact Leaderboards
   |
   v
Artifact Intent Cards
   |
   v
Compound Drift Layer
   |
   v
Staged Probes
   |
   v
Operator-selected model depth
   |
   v
Prediction updates and/or mutation candidates
   |
   v
Existing auditor/profile compiler
```

## Async design for query consensus drift

Because local query monitoring currently does not run async consensus drift, the safest design is to introduce it as a separate worker, not inside the first UI click path.

### Initial query monitoring path

The first pass should remain fast and non-mutating:

```text
UI query run
   |
   v
query_run created
   |
   v
Grok/search sensor job enqueued
   |
   v
query_run status = sensing
   |
   v
query artifact leaderboard populated
   |
   v
no entity profile mutation
```

### Async consensus drift path

Consensus drift should be a staged async job:

```text
High query drift or operator request
   |
   v
query_consensus_drift_job created
   |
   v
selected model targets run
   |
   v
answers normalized
   |
   v
artifact/entity/claim deltas scored
   |
   v
compound drift updated
   |
   v
staged probes or mutation candidates emitted
```

Do not block query monitoring UI on this job. The UI can display:

- not requested
- queued
- running
- partial coverage
- consensus ready
- failed
- skipped due to cost or operator setting

### Why consensus drift should be async

It prevents:

- expensive model calls on every query keystroke,
- accidental duplication of the production auditor,
- profile instability,
- billing chaos,
- UI latency,
- direct writes from raw model answers.

It enables:

- configurable model depth,
- retryable workers,
- partial coverage reporting,
- operator-selected escalation,
- cost-aware staged intelligence.

## Target stack strategy

The target stack should be configurable by stage.

### Sensor mode: Grok/search only

Purpose:

- public-info-space mapping,
- artifact collection,
- source/entity expansion,
- dedup,
- query artifact leaderboard,
- low-cost drift sensing.

Use this as default.

### Light panel mode: Grok plus one or two models

Purpose:

- spot-check disagreement,
- confirm whether drift is model-specific,
- score reliability before deeper escalation.

Use this for medium compound drift or paid/user-selected probes.

### Panel mode: three or four models

Purpose:

- robust staged probe,
- stronger model disagreement signal,
- better mutation-candidate evidence.

Use this for high-value artifacts and prediction-relevant drift.

### Full auditor mode: existing production auditor

Purpose:

- durable entity audit,
- consensus report,
- profile mutation,
- directory-visible changes,
- MFS/profile scoring.

Use this only after threshold confidence or operator approval.

## Profile-context injection dilemma

The user raised the key question: do we inject three or four profiles into monitoring to get proper drift scores, keep query to one target, or run query monitoring as its own consensus loop?

Recommended answer:

> Do not inject full profiles into default query monitoring. Run the query blank, then compare measured artifacts against compact entity state cards after retrieval.

Default query monitoring should receive:

- the query text,
- optional location/time constraints,
- operator target settings,
- no durable profile dump.

After Grok/search returns artifacts, the matching layer compares against:

- entity state cards,
- active intent keys,
- current artifact intent cards,
- prediction hooks,
- known contradiction candidates.

For staged probes only, inject compact context:

```json
{
  "entity_state_card": {
    "entity_id": "...",
    "canonical_name": "...",
    "active_intent_keys": [],
    "current_claims_under_dispute": [],
    "top_artifact_intent_cards": []
  },
  "artifact_under_test": {},
  "probe_question": "Does this artifact confirm, contradict, or mutate the active intent key?"
}
```

This gives drift scoring enough context without turning every query into a full audit.

## Query Artifact Leaderboard data contract

```json
{
  "schema": "maif_query_artifact_leaderboard/v1",
  "query_series_id": "qm_trump_iran_strategy",
  "query_run_id": "qr_...",
  "query_text": "What is Donald Trump's current Iran strategy?",
  "blank_measurement": true,
  "run_at": "2026-06-02T00:00:00Z",
  "targets": ["grok"],
  "status": "sensed | partial | consensus_pending | consensus_ready",
  "ranked_artifacts": [
    {
      "artifact_id": "artifact_...",
      "rank": 1,
      "canonical_url": "https://...",
      "title": "...",
      "source_domain": "...",
      "mention_count": 4,
      "novelty_score": 0.82,
      "query_drift_score": 0.76,
      "source_originality": 0.91,
      "prediction_relevance": 0.67,
      "dedup_cluster_id": "cluster_...",
      "linked_entities": [],
      "top_claims": []
    }
  ],
  "top_linked_entities": [],
  "top_sources": [],
  "top_claims": [],
  "model_coverage": {
    "requested_models": ["grok"],
    "observed_models": ["grok"],
    "missing_models": []
  }
}
```

## Entity Artifact Leaderboard data contract

```json
{
  "schema": "maif_entity_artifact_leaderboard/v1",
  "entity_id": "entity_...",
  "entity_name": "...",
  "updated_at": "2026-06-02T00:00:00Z",
  "ranked_artifacts": [
    {
      "artifact_id": "artifact_...",
      "rank": 1,
      "artifact_intent_card_id": "aic_...",
      "intent_keys": [],
      "coupling_score": 0.88,
      "artifact_drift_score": 0.74,
      "contradiction_score": 0.66,
      "source_reliability": 0.81,
      "source_originality": 0.9,
      "probe_eligibility": 0.79,
      "mutation_candidate": false
    }
  ],
  "active_compound_drift": []
}
```

## Compound Drift Layer data contract

```json
{
  "schema": "maif_compound_drift_record/v1",
  "compound_drift_id": "cdr_...",
  "artifact_id": "artifact_...",
  "claim_cluster_id": "claim_cluster_...",
  "linked_entities": [],
  "appeared_in_query_series": [],
  "source_cluster": {
    "primary_artifact_id": "artifact_...",
    "derivative_artifact_ids": [],
    "amplification_score": 0.0
  },
  "scores": {
    "query_recurrence": 0.0,
    "artifact_drift": 0.0,
    "entity_coupling": 0.0,
    "model_disagreement": 0.0,
    "prediction_relevance": 0.0,
    "compound_drift": 0.0
  },
  "recommended_actions": [
    "watch",
    "stage_grok_probe",
    "stage_light_panel",
    "create_temporal_tracker"
  ],
  "mutation_allowed": false
}
```

## Staged Probe data contract

```json
{
  "schema": "maif_staged_probe/v1",
  "probe_id": "sp_...",
  "artifact_id": "artifact_...",
  "entity_id": "entity_...",
  "query_series_id": "qm_...",
  "reason": "high compound drift",
  "affected_intent_keys": [],
  "suggested_prompt": "Given this artifact and the current entity intent graph, does this artifact confirm, contradict, or mutate the active intent key?",
  "target_depth": "grok_only | light_panel | panel | full_auditor",
  "target_models": [],
  "estimated_cost_class": "free | low | medium | high",
  "expected_output": "warning | prediction_update | mutation_candidate | temporal_tracker | no_op",
  "status": "staged | approved | running | complete | rejected",
  "durable_profile_mutation_allowed": false
}
```

## Operator controls

Operators should be able to choose:

- ignore,
- watch,
- probe with Grok,
- probe with two models,
- probe with three or four models,
- send to full auditor,
- create temporal tracker,
- promote mutation candidate,
- mark false/noise,
- add source to watchlist,
- add entity to watchlist.

This turns query monitoring into a controlled intelligence workspace instead of an auto-spending profile mutation daemon.

## Prediction resolution integration

Prediction scores can update live from query/artifact drift, but durable profile claims should not.

Prediction score updates can consume:

- artifact novelty,
- source originality,
- source reliability,
- entity coupling,
- query recurrence,
- model disagreement,
- contradiction potential,
- temporal proximity,
- confidence trend.

Prediction update output should be marked as sensor state:

```json
{
  "prediction_id": "pred_...",
  "score_delta": 0.04,
  "reason": "high-originality artifact surfaced across three monitored queries",
  "source_artifacts": [],
  "profile_mutation": false
}
```

This lets Grok update prediction framing live without turning prediction movement into profile truth.

## Integration phases

### Phase 1: Shadow contracts

Add schemas and local fixture outputs for:

- query artifact leaderboard,
- entity artifact leaderboard,
- artifact intent cards,
- compound drift records,
- staged probes.

No live model calls. No profile mutation.

### Phase 2: Query workspace UI

Extend the query monitoring UI from a flat seed catalog into a query workspace:

- query artifact leaderboard panel,
- top linked entities panel,
- top sources panel,
- top claims panel,
- staged probes panel,
- model coverage panel,
- filters for top mentioned/new/novel/high drift/primary source/duplicate/prediction relevant.

Still no profile mutation.

### Phase 3: Grok/search async sensor worker

Introduce a worker that consumes query trigger jobs and writes query measurement results.

Required outputs:

- artifacts,
- source domains,
- claims,
- linked entities,
- duplicate clusters,
- query drift score,
- source coupling draft,
- query artifact leaderboard.

Still no durable profile mutation.

### Phase 4: Entity matching and artifact intent cards

Map query artifacts to entity state cards and produce entity artifact leaderboards.

This is where query evidence enters the entity workspace, but only as ranked pressure, not truth.

### Phase 5: Async query consensus drift

Add configurable model-depth runs:

- Grok only,
- Grok plus one or two models,
- three/four model panel,
- full auditor escalation.

This remains asynchronous and writes staged probe results.

### Phase 6: Auditor bridge

Only mutation candidates above confidence threshold should cross into the existing production auditor.

The bridge should send:

- artifact intent card,
- evidence packet,
- staged probe results,
- model coverage,
- compound drift record,
- requested mutation type.

It should not send raw query monitoring output as durable truth.

## Specific answer on initial async consensus drift

Initial query monitoring should not include async consensus drift as the default required path.

Recommended default:

```text
Initial query run = Grok/search sensor job + query artifact leaderboard.
Consensus drift = optional async escalation after query artifacts show drift, recurrence, prediction relevance, or operator selection.
```

That gives the product the correct shape:

- blank query measurement,
- query-local artifact ranking,
- entity dedup/mapping,
- staged compound drift,
- operator-controlled model depth,
- existing auditor protected.

## The MyAIFingerprint open-source repo bug under this architecture

Current failure:

```text
Model says repos are not open source.
```

Correct pipeline:

```text
Recurring query detects repeated model claim.
   |
   v
Query artifact leaderboard surfaces GitHub repo, README, LICENSE, package metadata.
   |
   v
Source coupling marks GitHub/LICENSE as high-originality artifacts.
   |
   v
Entity artifact leaderboard attaches open-source/public-source evidence to MyAIFingerprint.
   |
   v
Artifact intent card summarizes the contradiction.
   |
   v
Staged probe asks selected model depth to classify public/source-available/open-source status.
   |
   v
Mutation candidate says: correct profile if license/source evidence crosses threshold.
   |
   v
Existing auditor compiles durable profile update.
```

Important distinction:

```text
public repo != legally open source unless license evidence confirms it
```

So the profile can safely distinguish:

- public repo,
- source-available,
- open-source licensed,
- private/closed source,
- unknown.

## Non-goals for the first integration

Do not:

- replace the production auditor,
- mutate profiles directly from query answers,
- run all models for every monitored query by default,
- inject full entity profiles into every query run,
- treat a single high-drift artifact as truth,
- make Grok the durable profile compiler,
- hide missing model coverage,
- merge query and entity leaderboards into one surface.

## Final architecture sentence

MAIF uses recurring blank queries as public-info-space sensors. Grok maps the links, artifacts, sources, entities, duplicate clusters, and claims surfaced by those queries. Query artifact leaderboards rank the local information surface. Entity artifact leaderboards rank what matters to durable entity graphs. Compound drift stages source-backed probes with operator-selected model depth. Predictions can move from sensor evidence, but profiles mutate only after the existing auditor accepts a confidence-gated mutation candidate.
