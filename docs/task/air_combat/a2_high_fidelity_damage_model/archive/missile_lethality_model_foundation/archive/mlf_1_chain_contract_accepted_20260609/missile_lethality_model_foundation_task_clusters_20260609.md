# A2 Missile Lethality Model Foundation Task Clusters

Status: `2026-06-09` MLF-1A-E accepted; this subproject is moving to the accepted/archived closure route.

Parent links:

- Parent A2: [../README.md](../README.md)
- Current subproject: [README.md](README.md)
- MLF-1 contract: [missile_lethality_chain_contract_20260609.md](missile_lethality_chain_contract_20260609.md)
- MLF-1A field inventory: [missile_lethality_field_inventory_20260609.md](missile_lethality_field_inventory_20260609.md)

## Boundary Decision

This plan advances `MLF-1 Chain Contract` only: standardize event fields,
diagnostics, training-consumer boundaries, and module ownership. It does not
tune AIM-120C/MQ-9 outcomes and does not claim real weapon Pk. After MLF-1 is
accepted, this subproject is archived; geometry, fuze, fragmentation,
continuous rod, structural breakup, and wreck/debris work must move into later
separate subprojects.

## Finite Task Cluster List

This list covers only MLF-1 closure inside the current
`missile_lethality_model_foundation/` subproject. MLF-2 and later stages must
not continue inside this folder; create a new MLF-2 subproject under the
`docs/agent` subproject standard when that work is ready.

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF-1A` | main thread or documentation worker | n/a | Inventory existing launch, approach, fuze, effect, component, damage, consequence, and lifecycle fields | `missile_lethality_field_inventory_20260609*.md` | no runtime edits, no weapon-specific values | `rg -n "[ \\t]$" missile_lethality_field_inventory_20260609*` | table covers contracts, event store, diagnostics probe, reward consumer | first, serial | 1 | pass |
| `MLF-1B` | Turing `019eac4f-0cac-7380-bc79-e62db308cda2` | inherited / high | Design common event header and DTO shapes | `src/runtime/contracts/*`, related binding/test draft | no fragmentation, rod/cutting, or breakup implementation | focused contract tests + binding smoke | every stage has chain id, status, reason, and authority labels | after `MLF-1A`; serial with 1C on API names | 2 | pass |
| `MLF-1C` | Descartes `019eac5b-0d84-7df3-b7df-26c2949467ef` | inherited / high | Add shared diagnostic projection fields for multi-stage per-munition output | `tools/diagnostics/**`, needed Python helper, diagnostics tests | reward code does not create kill facts, no legacy aliases | diagnostics pytest + controlled export sample | no dependence on `last_effect_*` and `last_damage_*` | after `MLF-1A`; parallel with 1D after names freeze | 2 | pass |
| `MLF-1D` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | inherited / high | Migrate training reward and terminal consumers, isolating legacy field dependence | `gym_envs/scenario_loader/reward_runtime/**`, `tests/runtime/air_combat/**`, related diagnostics tests | no reward semantics change, no direct-kill rule, no long-term dual field surface | reward/runtime pytest + diagnostics pytest | standard fields are preferred; legacy fields remain only as short fallback with deletion conditions | after `MLF-1B`; parallel with 1C after shared names | 2 | pass |
| `MLF-1E` | main thread | n/a | Accept module boundary and decide whether to split `lethality_chain_contracts.h` | README, chain contract, task cluster, acceptance note | event store does not become a physics model | `git diff --check` + relevant 1B-1D tests | contract, diagnostics, and training-consumer boundaries are clear | after 1B-1D; serial | 1 | pass |

## Dispatch Rules

- Every worker packet must map to exactly one cluster.
- `MLF-1B` and `MLF-1C` must not edit the same field-name table concurrently.
- Legacy fields are not a compatibility promise. Any short transition must name
  the deletion point and owner.
- Runtime behavior changes wait until the field contract is frozen.
- If a cluster exceeds its round cap, return to the main thread and re-scope.
- Do not create a new session thread. Subagents, if used, must remain within the
  current controlled workflow.
- Do not dispatch MLF-2 from this subproject. MLF-2 must be created as a
  separate subproject after MLF-1 archive routing is complete.

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Round-1 Acceptance Record

- `MLF-1A` field inventory is accepted; outputs are
  [missile_lethality_field_inventory_20260609.zh.md](missile_lethality_field_inventory_20260609.zh.md)
  and the English companion.
- `MLF-1B` read-only contract exploration returned route evidence: define the
  common header and DTOs first, then packet, binding, facade, and manifest work.
  This is not implementation completion.
- `MLF-1C` read-only diagnostics exploration returned route evidence: current
  dependency centers on `last_effect_*` / `last_damage_*`; migrate to
  `chain_id + event_id + stage` rows. This is not implementation completion.
- `MLF-1D` read-only consumer exploration returned route evidence: reward and
  terminal migration must preserve existing reward semantics and the
  `ground_lifecycle >= 2` crash meaning. This is not implementation completion.

## Round-2 Dispatch Record

- `MLF-1B` was dispatched to Turing
  `019eac4f-0cac-7380-bc79-e62db308cda2` for the common header, DTO shapes,
  minimal Python binding, and static shape tests.
- `MLF-1C/1D` implementation is intentionally not dispatched in this round;
  diagnostics and reward migration should wait for stable `MLF-1B` field names.
- Fragmentation, rod/cutting, structural breakup, Pk, and specific AIM-120C/MQ-9
  tuning remain out of scope.

## Round-2 Acceptance Record

- `MLF-1B` is accepted: it added `LethalityChainHeader` plus ten lethality-chain
  DTO shapes and exposed them through `RecentEngagementEvents`, the facade
  packet, and Python bindings.
- This acceptance covers contract/binding shape only. Runtime event writers,
  diagnostics projection, and training-consumer migration remain future work.
- Local revalidation passed: `cmake --build build-workshop --target ef_py -j2`,
  `test_engagement_contract_shape.py`, `test_bindings_engagement_surface.py`,
  `test_bindings_runtime_dto_surface.py`, and the touched-file `git diff --check`.

## Round-3 Dispatch Record

- `MLF-1C` was dispatched to Descartes
  `019eac5b-0d84-7df3-b7df-26c2949467ef` for diagnostics chain projection,
  `lethality_chain_rows`, optional chain CSV output, and diagnostics tests.
- `MLF-1D` remains held until `MLF-1C` output is stable, so reward consumers do
  not bind to temporary field names.
- This round still does not edit reward runtime, implement event-store writers,
  or add new lethality behavior.

## Round-3 Acceptance Record

- `MLF-1C` is accepted: diagnostics payloads now include
  `lethality_chain_rows`, the CLI supports `--chain_csv_out`, and each row carries
  `chain_id`, `event_id`, `stage`, source event, and evidence level.
- Old `last_effect_*` / `last_damage_*` fields were removed from the diagnostic
  tool body; tests retain only negative assertions.
- The chain rows are still transitional projections from `EffectsEvent` /
  `DamageReport`; real DTO event-store writers remain future work.
- Local revalidation passed: `test_diagnostics_probe_contracts.py`, `py_compile`,
  and the relevant `git diff --check`.

## Round-4 Dispatch Record

- `MLF-1D` was dispatched to Sartre
  `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` for training reward and terminal
  consumer migration.
- The target is standard `PlatformConsequenceEvent` / `LifecycleTransitionEvent`
  consumption first. Old `DamageReport` can only remain as a transitional
  fallback with a deletion condition.
- This round must not change reward semantics, add direct-kill rules, or treat
  any ground contact as a crash.
- CMO-DB is now recorded as a `cmo_db_proxy` source policy; this is an evidence
  and parameter-source rule, not runtime behavior.

## Round-4 Acceptance Record

- `MLF-1D` is accepted: training reward now builds consumer-side facts from
  `platform_consequence_events` / `lifecycle_transition_events` first, while old
  `DamageReport` input remains confined to `_transitional_damage_report_fact_projection()`.
- Terminal handling prefers standard lifecycle events. Ground contact still
  requires `ground_lifecycle >= 2` or the crashed-wreck state before the unit is
  treated as non-actionable; safe ground contact remains actionable.
- String parsing for old `DamageReport.platform_damage_state_delta` has not
  spread into the standard path. The fallback can be deleted once the runtime
  event store writes `PlatformConsequenceEvent` and `LifecycleTransitionEvent`
  for live scenarios.
- Local revalidation passed: `test_air_combat_reward_surface.py`,
  `test_diagnostics_probe_contracts.py`, `py_compile`, and the relevant
  `git diff --check`.

## Round-5 Acceptance Record

- `MLF-1E` is accepted, and `MLF-1 Chain Contract` may move from planned/active
  to accepted.
- Do not split `src/runtime/contracts/lethality_chain_contracts.h` yet. The
  lethality-chain DTOs are already a clear section inside
  `engagement_contracts.h` and are exposed through `RecentEngagementEvents`,
  facade packets, and Python bindings. Splitting now would mostly create
  include/binding churn.
- Reconsider the split only after standard DTO event-store writers land, or when
  future standalone MLF-2/MLF-3 subprojects create independent ownership for
  geometry, fuze, warhead, and component-load contracts.
- Responsibility boundary accepted: contracts contain data only; the event store
  records, orders, links, and exports; diagnostics project stage rows; reward and
  terminal logic consume facts; geometry/fuze, fragmentation, rod/cutting,
  structural breakup, wreck/debris entities, and AIM-120C/MQ-9-specific tuning
  are not implemented in MLF-1E.
- Legacy deletion condition remains: once the runtime event store writes
  `PlatformConsequenceEvent` and `LifecycleTransitionEvent` for live scenarios,
  delete the `DamageReport` transitional fallback and
  `platform_damage_state_delta` string parsing path.
- After MLF-1E, this subproject follows the accepted/archived route and does not
  carry MLF-2 geometry/fuze work. MLF-2 must be created later as a separate
  subproject under the `docs/agent` standard.
- This round changed docs only and did not modify runtime code.

## Future MLF-2 Holding Note

This task-cluster plan does not dispatch MLF-2. After archive closure, a future
MLF-2 subproject should state its objective as: use controlled geometry and fuze
evaluation to explain trigger, no-trigger, delay, and failure cases, then hand
detonation state to later warhead-effect models instead of directly producing a
kill result.

The minimum future MLF-2 subproject content should include:

- README: goal, scope, non-goals, entry gate, and exit gate.
- Finite task clusters: geometry scenarios, nearest-approach event, fuze
  evaluation event, diagnostic export, and validation scenarios.
- Acceptance gate: range, aspect, speed, and attitude cases produce explainable
  outcomes; no-detonation cases report reasons; contact and proximity decisions
  are recorded separately.
- Residual map: fragmentation, continuous-rod, structural breakup, wreck/debris,
  Pk, and weapon-specific calibration remain later standalone subprojects.

## Validation Plan

Documentation-only first round:

```bash
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_model_foundation
```

Later code rounds need at least:

```bash
python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
python -m pytest tests/runtime/air_combat/test_air_combat_reward_surface.py -q
```

## Acceptance Criteria

MLF-1 can be marked accepted only when:

- The event chain explains each step from launch to consequence.
- No-trigger, miss, ineffective detonation, non-terminal damage, delayed crash,
  and breakup all have explicit recording positions.
- Diagnostic fields have stable names and clear C++/Python boundaries.
- Legacy field dependence is migrated or listed for deletion; no long-term dual
  export is maintained.
- Training reward consumes facts and does not create lethality conclusions.
- Docs still refuse AIM-120C/MQ-9-specific real-world authority.

## Residual Map

| Residual | Owner | Release condition |
| --- | --- | --- |
| Current subproject archive pointer not yet written | main thread / archive workflow | move or point the accepted MLF-1 package under the task system |
| Standard DTO event-store writer not yet live | future runtime writer subproject | live runtime can produce `PlatformConsequenceEvent` / `LifecycleTransitionEvent` directly, allowing `DamageReport` fallback deletion |
| Geometry/fuze probe missing | future standalone MLF-2 subproject | handle after creating a separate MLF-2 subproject |
| Fragmentation, rod/cutting, structural breakup, wreck/debris, and Pk are missing | future standalone MLF subprojects | unfold as independent subprojects after MLF-2 |
