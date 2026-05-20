# Post-WP9 Architecture Route Plan

Status: `2026-05-21` route-selection plan; Phase 1 is accepted as `WP10`,
Phase 2 is accepted as `WP11`, Phase 3 is accepted as `WP12`, Phase 4 is
accepted as `WP13`, and Phase 5 is opened as planned / dispatch-ready `WP14`.

Language:

- English canonical: `post_wp9_architecture_route_plan_20260520.md`
- Chinese companion: [post_wp9_architecture_route_plan_20260520.zh.md](post_wp9_architecture_route_plan_20260520.zh.md)

Inputs:

- [Simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)
- [Simulation architecture task index](README.md)
- [Consolidated remaining work and forward roadmap](../review/consolidated_remaining_work_and_roadmap_20260520.md)
- [Post-WP9 gap analysis](../review/post_wp9_gap_analysis_20260520.md)
- [WP9 contract and infrastructure closure](wp9_contract_infrastructure_closure/contract_infrastructure_closure_wp9_20260520.md)
- [WP14 capability composition](wp14_capability_composition/capability_composition_wp14_20260521.md)
- [WP closure lane policy](../../standards/governance/wp_closure_lane_policy.md)

## 1. Purpose

WP0-WP9 closed the architecture baseline, contract vocabulary, facade guardrails,
backend-profile policy, learning-face vocabulary, and deferred DTO/infrastructure
items. The next phase should not create another documentation-only wave. It
should choose an implementation route that turns accepted architecture rules
into runtime facts.

This document fixes the route order, anchors Phase 1 as `WP10`, Phase 2 as
`WP11`, anchors Phase 3 as `WP12`, accepts Phase 4 as `WP13`, and opens Phase 5
as planned / dispatch-ready `WP14`. It does not assign WP numbers beyond the
currently opened phase. It defines which direction must come first, which
directions should wait, and what kind of evidence counts as real architectural
progress.

## 2. Route Decision

The post-WP9 route is:

```text
causal runtime foundation
  -> facade vertical slice
  -> information and agency enforcement
  -> backend/fidelity expansion
  -> capability composition
  -> counterfactual and experiment generation
```

This order is intentional:

1. Runtime causality must become machine-checkable before backend, fidelity,
   counterfactual, or experiment-generation work can be trusted.
2. A narrow facade-visible vertical slice should prove the foundation without
   forcing a scheduler rewrite across all systems at once.
3. Information and agency rules must become enforceable before backend/fidelity
   comparisons can be trusted as maintained decision evidence.
4. Backend and fidelity work must remain behind profile/capability contracts,
   not become a second semantic path.
5. Capability composition is a semantic upgrade and should happen after the
   runtime can expose stable state/event/evidence boundaries.
6. Counterfactual and experiment generation require deterministic replay,
   snapshot/restore, and evidence ancestry, so they should be later consumers.

## 3. Ordered Architecture Tracks

| Order | Track | First concrete outcome | Depends on | Should wait for |
|-------|-------|------------------------|------------|-----------------|
| 1 | Causal runtime foundation | Machine-readable `StageNodeManifest` registry plus a minimal scheduling-window loop: collect facade requests, inject graph inputs, run an acyclic manifest-derived window, commit through barriers, and export ordered evidence. | WP2.5, WP5, WP9, GAP-2/GAP-3 | full multi-rate scheduler |
| 2 | Facade vertical slice | One maintained chain, preferably engagement/observation first, proves `manifest -> event order -> diagnostics trace -> facade export -> tests`, while adding `ActionHoldPolicy` and information-state provenance labels needed for later policy cadence proof. | track 1 seed, GAP-1/GAP-4 | broad scheduler rewrite |
| 3 | Information and agency enforcement | Law 14 read-side guards, `AgentRole` authority validation, information-transformation evidence, and authorized intent injection become test-backed. | WP10, WP11, GAP-5/GAP-6/GAP-7 | full Agency Graph runtime |
| 4 | Backend/fidelity expansion | `RuntimeCapabilities` and model-provider/fidelity profiles become queryable, rejectable, and test-backed. | WP6, WP7, tracks 1-3 | maintained causal/evidence boundary |
| 5 | Capability composition | A bounded path from type-name spawning toward typed `Capability` / `CapabilityBundle` composition through resolved spawn plans and additive setup DTOs without breaking compatibility. | WP2, WP9, tracks 1-4, `Capability` / `CapabilityBundle` DTOs | stable setup/content contract |
| 6 | Counterfactual and experiment generation | Branchable worldline, deterministic replay envelope, scenario/adversary generation, and capability profiling evidence. | WP8, tracks 1-5 | snapshot/restore and replay proof |

### 3.1 Post-WP9 Phase Breakdown

The route is divided into no more than six implementation phases. Phases 1-5
are now assigned to `WP10` through `WP14`. Phase 6 remains a sequencing anchor,
not an opened task folder, until its prerequisites are mergeable.

| Phase | Working label | Scope | Candidate WP ownership | Opens when | Must not claim yet |
|-------|---------------|-------|------------------------|------------|--------------------|
| 1 | Causal runtime foundation | Materialize the first code-owned `StageNodeManifest` registry, minimal scheduling-window loop, cross-layer request injection, same-window edge validation, and event/snapshot evidence for the engagement/observation slice. | `WP10` | WP9 closure and post-WP9 route are accepted. | Full multi-rate scheduling, strict clock-domain enforcement, Law 14 read-side enforcement. |
| 2 | Facade vertical slice and provenance | Add `ActionHoldPolicy`, information-state provenance labels, and one facade/binding-visible chain over the Phase 1 runtime seam. | `WP11` | Phase 1 registry, barriers, and event/snapshot evidence are accepted. | Broad facade rewrite, policy/control/physics cadence support beyond the demonstrated slice. |
| 3 | Information and agency enforcement | Turn deferred `GAP-5`, `GAP-6`, and `GAP-7` into enforceable read-side, role/authority, and transformation-surfacing gates. | `WP12` | Provenance labels, consumer pre-gates, and facade slice are stable. | Full Agency Graph runtime or backend/fidelity promotion. |
| 4 | Backend/fidelity expansion | Make `RuntimeCapabilities`, model-provider profiles, fidelity profiles, and parity budgets queryable, rejectable, and evidence-backed behind the causal boundary. | `WP13` | Phase 1-3 evidence boundaries are stable enough to compare backends. | Exact GPU, resident-state, shadow, or multi-fidelity promotion without gates. |
| 5 | Capability composition | Move bounded setup/content paths toward typed `Capability` / `CapabilityBundle` composition while preserving type-name compatibility. | `WP14` | Runtime/facade/backend contracts can name stable capability effects and evidence. | Big-bang spawn rewrite, mandatory public `spawn_platform`, or scenario-schema replacement. |
| 6 | Counterfactual and experiment generation | Add branchable worldlines, deterministic replay envelopes, scenario/adversary generation, and experiment evidence ancestry. | Later WP | Snapshot/restore, replay, capability evidence, and facade provenance are stable. | Worldline branching before deterministic replay and snapshot boundaries exist. |

## 4. Gap Analysis Incorporation

The post-WP9 gap analysis accepts the five-track ordering but tightens Track 1
and Track 2. The following items are now part of the route definition rather
than optional embellishments:

| Gap | Route decision |
|-----|----------------|
| `GAP-1 ActionHoldPolicy` | Add to Track 2 as a required DTO before policy/control/physics cadence can be claimed. The first engagement/observation slice may expose the DTO without proving full cadence. |
| `GAP-2 Scheduling window loop` | Add to Track 1 as the minimal loop skeleton connecting `StateStore`, `EventQueue`, `Barrier`, and `StageNodeManifest`. |
| `GAP-3 Cross-layer request injection` | Add to Track 1 as input-injection semantics at a declared window boundary. Track 2 may demonstrate facade-visible effects. |
| `GAP-4 Information-state provenance labels` | Add to Track 2 on observation/facade packets so later Law 14 enforcement has stable vocabulary. |
| `GAP-8 Same-window edge derivation` | Add to Track 1 as schedule-construction validation, not per-tick runtime discovery. |
| `GAP-9 Clock-domain enforcement` | Defer strict enforcement until the window-loop skeleton works; advisory clock-domain declarations are acceptable in the first Track 1 slice. |

Phase 3 gates accepted as `WP12`:

- `GAP-5` Architecture Law 14 read-side enforcement now uses WP11 provenance
  labels and consumer pre-gates as its starting boundary.
- `GAP-6` Agency Graph runtime enforcement begins with role/authority boundary
  validation, not full Agency Graph dispatch.
- `GAP-7` five information-state transformation rules now become
  machine-checkable vocabulary/evidence for the selected slice.

### 4.1 Gap-Driven Work Content

The gap analysis should become implementation backlog in the following order.
These items are work content for the first implementation WP and its immediate
follow-on, not a new documentation-only phase.

| ID | Track | Work content | Required evidence | Explicit non-scope |
|----|-------|--------------|-------------------|--------------------|
| `POST9-T1-A Manifest Registry Seed` | Track 1 | Materialize a code-owned `StageNodeManifest` registry for the selected engagement/observation slice. Required fields: stable `node_id`, semantic stage, read/write state shards, advisory clock domain, latency/sync/read-snapshot/write-commit policy, and declared same-window publish intent. | Architecture test enumerates the registry and rejects missing required fields for maintained nodes. | No full inventory of every runtime system yet. |
| `POST9-T1-B Scheduling Window Loop Skeleton` | Track 1 | Add a minimal loop that connects the primitives: collect facade requests, cross the `input_injection` barrier, run a manifest-derived acyclic window, cross `window_commit`, and expose an `export` barrier. | Runtime or architecture test proves the barrier sequence and records a stable window id / barrier id for the slice. | No complete multi-rate scheduler or global scheduler replacement. |
| `POST9-T1-C Cross-Layer Request Injection` | Track 1 | Queue facade-compatible graph inputs with `source_layer`, `source_id`, `input_snapshot_version`, `effective_time`, `valid_until`, and `merge_policy`, then make accepted requests visible only after the declared injection barrier. | Tests cover accepted, future-window, and expired requests on the chosen slice. | No broad policy/control/physics cadence claim before `ActionHoldPolicy` exists. |
| `POST9-T1-D Same-Window Edge Validation` | Track 1 | Validate same-window edges at schedule construction: the consumer read set must intersect the producer write set, and the producer must declare same-window publication to that consumer/stage family. | Passing fixture for the chosen slice plus failing fixture for an undeclared or data-disjoint edge. | No per-tick edge discovery or wildcard same-window visibility. |
| `POST9-T1-E Event And Snapshot Evidence` | Track 1 | Bind ordered events, snapshot version, barrier id, source time, and diagnostics ancestry to the facade-visible engagement/observation export path. | Facade/binding-visible test proves deterministic event ordering and exported metadata presence. | No counterfactual branching or snapshot/restore claim. |
| `POST9-T2-A ActionHoldPolicy Contract` | Track 2 | Add the typed `ActionHoldPolicy` contract with hold-last, interpolate, expiry, and drop semantics plus validity duration and refresh cadence fields. | DTO shape, serialization/binding surface, and guard tests prove the contract exists without claiming runtime cadence support. | No maintained policy/control/physics multi-rate runtime until Track 1 proves the loop and a later cadence slice consumes the DTO. |
| `POST9-T2-B Information Provenance Labels` | Track 2 | Add stable information-state provenance labels to `ObservationPacket` and `DecisionBelief` export metadata so maintained packets declare whether data came from World Truth, Sensed State, Track State, Shared Tactical Picture, Agent Observation, or Decision Belief. | Tests reject unlabeled maintained facade exports and prove labels survive Python/binding-facing packets. | No Law 14 read-side enforcement yet. |
| `POST9-T2-C Facade Vertical Slice Proof` | Track 2 | Prove one maintained chain from manifest registry through event order, diagnostics trace, facade export, and Python binding smoke. | End-to-end test references the same node ids / barrier ids / event ancestry across runtime and facade layers. | No broad facade rewrite. |

Dispatch rule: `POST9-T1-A` through `POST9-T1-E` should be the first
implementation WP's mainline. `POST9-T2-A` and `POST9-T2-B` may run in parallel
only after the Track 1 seam is named, and `POST9-T2-C` should wait until both
the Track 1 skeleton and the Track 2 metadata contracts are mergeable.

## 5. First Implementation Candidate

The first implementation WP should be a causal runtime materialization slice, not
a broad scheduler rewrite.

This seed is now opened as [WP10 causal runtime foundation](wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.md).

Recommended seed:

- materialize a small `StageNodeManifest` registry in code,
- add the minimal scheduling-window loop skeleton:
  collect facade requests -> input-injection barrier -> manifest-derived acyclic
  window -> window-commit barrier -> export barrier,
- attach stable node ids and semantic stages to the engagement/observation path,
- validate same-window edges at schedule construction for the chosen slice,
- expose or assert snapshot version, barrier id, source time, and event ordering
  where the facade already returns packets,
- keep `DiagnosticsTrace` tied to event ancestry,
- add focused architecture/runtime tests proving the path.

Preferred slice:

```text
P7 FireControlLaunch / P9 EffectsDamage / P10 ObservationExport
  -> recent engagement events
  -> diagnostics traces
  -> RuntimeFacade export APIs
  -> Python binding smoke and architecture checks
```

This path is attractive because WP3-WP5 and WP9 already created the guardrails,
contracts, and tests around engagement, diagnostics, observation, and facade
exports.

Track 2 follow-on seed:

- add `ActionHoldPolicy` as a typed contract before claiming any
  policy/control/physics cadence support,
- add information-state provenance labels to observation/facade packets,
- demonstrate that facade exports can carry provenance without granting policy
  code access to `World Truth`.

This follow-on seed is now opened as
[WP11 facade vertical slice and provenance](wp11_facade_vertical_slice_provenance/facade_vertical_slice_provenance_wp11_20260520.md).

Phase 3 enforcement seed:

- promote WP11 consumer pre-gates into focused Law 14 read-side enforcement,
- validate `AgentRole` authority, information source, decision-model reference,
  and action interface before maintained outputs are authorized,
- surface information transformation evidence for the selected packet/belief
  chain,
- guard `DecisionBelief -> ActionIntentPacket` / `CoordinationIntentPacket`
  paths through facade-compatible injection,
- keep full Agency Graph runtime, backend/fidelity, capability composition, and
  counterfactual work out of scope.

This enforcement seed is now accepted as
[WP12 information and agency enforcement](wp12_information_agency_enforcement/information_agency_enforcement_wp12_20260520.md).

Phase 4 backend/fidelity seed:

- make `RuntimeCapabilities` expose conservative query metadata and stable
  rejection reasons without inferring support from GPU helper/probe availability,
- materialize code-owned backend profile records and parity budget evidence
  gates from the accepted WP6/WP7 registries,
- admit fidelity profile labels as requests bound to profile ids, budget refs,
  model-family scope, validation gate, and facade evidence,
- prove query and rejection behavior through maintained facade and Python
  binding surfaces,
- keep exact GPU, resident-state, shadow, adaptive fidelity, learned
  `ModelProvider`, and maintained multi-fidelity support out of scope until
  their own gates exist.

This backend/fidelity seed is now accepted as
[WP13 backend fidelity expansion](wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.md).

Phase 5 capability-composition seed:

- define platform-semantic `Capability`, `CapabilityBundle`, capability-family
  vocabulary, and resolved-plan evidence without reusing backend
  `RuntimeCapabilities`,
- introduce the internal compatibility chain:
  `type_name -> CapabilityBundle template -> ResolvedPlatformSpawnPlan ->
  materialization evidence`,
- route existing spawn paths through resolution before materialization while
  preserving `spawn_unit(type_name)` and `WorldSpawnRequest.type_name`,
- add additive facade/setup DTO vocabulary for future typed platform spawn
  requests without making it mandatory,
- bind capability families to existing ECS/component materialization evidence
  and unsupported-effect reasons without adding new tactical behavior,
- keep public `spawn_platform({capabilities...})` promotion, scenario-schema
  migration, backend/fidelity promotion, and broad spawn rewrites out of scope
  until their own gates exist.

This capability-composition seed is now opened, not accepted, as
[WP14 capability composition](wp14_capability_composition/capability_composition_wp14_20260521.md).

## 6. Non-Goals For The First Implementation WP

- Do not rewrite the whole scheduler.
- Do not claim strict clock-domain enforcement until the window-loop skeleton is
  proven.
- Do not promote exact GPU, resident-state, or multi-fidelity execution to
  maintained status.
- Do not migrate all platform spawning to capability composition.
- Do not make typed capability spawning mandatory before the WP14 compatibility
  bridge and additive facade/setup DTO gates pass.
- Do not claim Law 14 read-side enforcement or Agency Graph runtime enforcement
  in the first causal slice.
- Do not start counterfactual/worldline branching before deterministic replay
  and snapshot boundaries exist.
- Do not make documentation closure block implementation `Mergeable` status;
  use the closure lane for README, acceptance, archive, and bilingual sync.

## 7. Evidence Standard

After WP9, a mainline architecture WP is not complete unless it has runtime
artifacts.

Minimum evidence for an implementation WP:

- code-owned contract or runtime surface,
- focused runtime or architecture tests,
- exact validation commands and outcomes,
- at least one facade-visible or binding-visible proof when the work affects
  frontend consumers,
- when a track claims scheduler semantics, a schedule-construction or runtime
  test proving the declared edge/barrier/event rule,
- named residuals instead of hidden TODOs.

Documentation-only output may still be useful, but it should be treated as
planning or closure-lane work, not as the main implementation result.

## 8. Subagent Routing

Use the following split:

- Main implementation workers own code, tests, and English canonical handoff
  notes for one bounded track or slice.
- Closure subagents own README/review/index/archive/bilingual synchronization
  after a stream reaches `Mergeable`.
- Explorers may inspect candidate implementation seams before task dispatch, but
  should not substitute for runtime materialization.

For `WP14`, the highest-reasoning work is the compatibility-preserving
composition seam: deciding where capability contracts, content/factory lowering,
spawn resolution, facade setup DTOs, and materialization evidence attach without
creating a second spawn lifecycle or forcing callers off type-name compatibility.
