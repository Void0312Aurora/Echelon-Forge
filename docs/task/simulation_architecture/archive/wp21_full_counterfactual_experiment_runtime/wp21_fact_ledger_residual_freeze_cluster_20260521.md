# WP21-A Fact Ledger And Residual Freeze

Status: `2026-05-22` pass / source-backed facts accepted.

Language:

- English canonical: `wp21_fact_ledger_residual_freeze_cluster_20260521.md`
- Chinese companion:
  [wp21_fact_ledger_residual_freeze_cluster_20260521.zh.md](wp21_fact_ledger_residual_freeze_cluster_20260521.zh.md)

Inputs:

- [WP21 main plan](full_counterfactual_experiment_runtime_wp21_20260521.md)
- [WP15 counterfactual contracts](../wp15_counterfactual_experiment_generation/counterfactual_experiment_generation_wp15_20260521.md)
- [WP17 counterfactual runtime slice](../wp17_stage3_runtime_materialization_cleanup/wp17_counterfactual_runtime_closure_cluster_20260521.md)
- [WP18 ownership residuals](../wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.md)
- [WP19 resident-state boundary](../wp19_cuda_resident_state_alignment/wp19_resident_state_sync_shard_contract_cluster_20260521.md)
- [WP20 typed setup baseline](../wp20_public_capability_platform_composition/wp20_public_capability_fact_ledger_cluster_20260521.md)

## Purpose

Freeze the source-backed facts before any WP21 implementation wave starts. This
is the last safety rail for the route: real residuals must be named, and
anything outside the refactor route must stay explicitly retained as
compatibility. This file is the `WP21-A` closure artifact; it is not an
implementation pass and does not promote runtime behavior.

## Scope

In scope:

- source/test ledger for counterfactual contracts, selected-slice runtime,
  Python bindings, scenario generation requests, experiment evidence bridge,
  `ScenarioLoader` mirror residuals, typed setup baseline, and the
  backend/resident-state boundary;
- final residual register with owner stream and pass/block criteria;
- first-wave readiness decision for `WP21-B` and `WP21-D`.

Out of scope:

- runtime behavior edits;
- acceptance review creation;
- changing final-stage scope without citing source facts;
- adding a new stage to absorb leftover work.

## Freeze Decision

- `WP21-A` passes as a docs-only source-backed freeze.
- `WP21-B` and `WP21-D` are released for first-wave dispatch after this ledger.
- No runtime, binding, scenario, or test behavior is accepted by this file
  alone; later streams still need implementation evidence and focused tests.
- Exact GPU, resident-state, truth/support promotion, raw authoritative
  mutation, forced scenario-schema migration, and unbounded worldline trees stay
  blocked.

## Source-Backed Facts

Evidence paths below were checked against the current tree during this freeze.
They are intentionally repo-relative so follow-on workers can re-run focused
source and test probes before editing.

| Area | Current fact | Evidence | Current support state |
|---|---|---|---|
| Counterfactual contracts | `src/runtime/contracts/counterfactual_replay_contracts.h` owns the replay envelope, branch point, worldline branch metadata, counterfactual request/admission, scenario-generation metadata, and experiment evidence bridge vocabulary. Validation keeps restore support unsupported, rejects raw authoritative-state mutation, and fails closed on truth/support promotion. | `src/runtime/contracts/counterfactual_replay_contracts.h`; `tests/architecture/causal_runtime/test_replay_envelope_contracts.py`; `tests/architecture/causal_runtime/test_worldline_branch_metadata.py`; `tests/architecture/causal_runtime/test_experiment_evidence_bridge.py`; `tests/architecture/causal_runtime/test_counterfactual_admission.py` | Source-backed, metadata-only restore boundary, fail-closed. |
| Selected-slice runtime | `RuntimeFacade::snapshot_counterfactual_entity()` and `RuntimeFacade::run_counterfactual_branch()` are public. `RuntimeFacade::capabilities()` keeps resident-state, exact-GPU, and shadow support false, while the branch path builds parent/branch worlds from explicit setup, admits only the maintained reference CPU fidelity request, rejects raw mutation, and compares snapshots on `counterfactual_selected_slice`. | `src/runtime/facade/runtime_facade.h`; `src/runtime/facade/runtime_facade.cpp`; `tests/runtime/facade/test_runtime_facade.py` | Implemented bounded selected-slice runtime only. |
| Python bindings | `bindings_runtime.cpp` exposes `RuntimeCapabilities`, fidelity request/admission, `RuntimeCounterfactualSnapshot`, `RuntimeWorldlineComparison`, `RuntimeCounterfactualBranchRequest`, `RuntimeCounterfactualBranchResult`, `DeviceResidentOutputDescriptor`, and the `RuntimeFacade` methods for counterfactual snapshot/branch and setup. | `src/interfaces/python/bindings_runtime.cpp`; `tests/runtime/bindings/test_bindings_runtime_dto_surface.py`; `tests/runtime/facade/test_runtime_facade.py` | Public Python surface exists; no promoted counterfactual mainline consume bridge. |
| Scenario generation request surface | `python/scenario/compiler/generation_request.py` defines `wp15.scenario_generation_request.v1`, allowed generation kinds, sources, evidence kinds, fail-closed validation, and metadata-only artifact cloning. Tests keep the request deterministic, reject missing/unsupported fields, and prove the artifact does not mutate the baseline. | `python/scenario/compiler/generation_request.py`; `tests/scenario/test_scenario_generation_contracts.py` | Validated metadata surface, not a maintained generator/runtime. |
| Experiment evidence bridge | WP15 contracts link counterfactual admission, generated input metadata, and profile observations into the experiment evidence bridge vocabulary. The bridge is non-truth-claim only and rejects support promotion and generated-input mutation drift. | `src/runtime/contracts/counterfactual_replay_contracts.h`; `tests/architecture/causal_runtime/test_experiment_evidence_bridge.py` | Implemented as evidence bridge, not truth/support promotion. |
| ScenarioLoader / runtime mirror residual | WP18 still classifies `gym_envs/scenario_loader/core.py` as both scenario adapter and runtime-state mirror, and keeps `python/rl/runtime/world_batch/adapter.py` plus `python/rl/runtime/world_batch_vec_env.py` as frontend/compatibility mirrors. The raw runtime escape hatch stays narrow and explicitly allowlisted; WP18 also names the loader mirror split/pre-gate as `WP21-R2` before broad counterfactual/experiment runtime migration. | `docs/task/simulation_architecture/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.md`; `tests/runtime/execution/test_scenario_loader_execution_step_runtime.py`; `tests/architecture/runtime_facade` | Retained compatibility, not a WP21 implementation target. |
| Typed setup baseline | WP20 already made typed platform spawn requests public: `TypedPlatformSpawnRequest`, `ResolvedPlatformSpawnPlan`, `BatchWorldSetupRequest.typed_platform_spawn_requests`, and the facade/binding surface exist. The current path remains compatibility-preserving, validates `compatibility_path_preserved`, and still routes admitted typed setup through legacy setup materialization rather than replacing it. | `docs/task/simulation_architecture/wp20_public_capability_platform_composition/wp20_public_capability_fact_ledger_cluster_20260521.md`; `src/runtime/facade/runtime_facade.cpp`; `src/interfaces/python/bindings_runtime.cpp`; `tests/runtime/facade/test_runtime_facade.py` | Additive compatibility seam, not a forced scenario-schema migration. |
| Backend / resident-state boundary | `RuntimeFacade::capabilities()` hard-codes `supports_resident_state`, `supports_exact_gpu_backend`, and `supports_shadow_compare` to false, while still surfacing candidate ids and rejection reasons. `RuntimeFacade.runtime()` is documented as compatibility/diagnostics-only. WP19 keeps the maintained truth host-owned and resident-state blocked. | `src/runtime/facade/runtime_facade.cpp`; `src/runtime/facade/runtime_facade.h`; `docs/task/simulation_architecture/wp19_cuda_resident_state_alignment/wp19_resident_state_sync_shard_contract_cluster_20260521.md`; `tests/runtime/facade/test_runtime_facade.py` | Explicitly fail-closed; no promotion of exact GPU or resident-state support. |

## Non-Goals

- Exact GPU support stays blocked.
- Resident-state support stays blocked.
- Experiment outputs, observations, or comparisons do not become truth or
  support claims.
- Arbitrary unbounded worldline trees are not introduced.
- Scenario schema migration is not forced.
- Authoritative runtime state is not mutated outside facade/request contracts.

## Final Residual Register

| Residual ID | Owner / disposition | What remains | Pass / block criterion |
|---|---|---|---|
| `WP21-A-R1` Counterfactual contract vocabulary | all WP21 streams | Consume or extend the WP15 replay/envelope/branch/admission/generation/evidence vocabulary; do not fork a parallel schema. | Pass when downstream code cites and reuses the contract vocabulary; block if a new runtime schema bypasses admission, replay, or evidence bridge guards. |
| `WP21-A-R2` Selected-slice runtime boundary | `WP21-B`, then `WP21-C` | Broaden the existing selected-slice runtime into a bounded, facade-owned snapshot/restore and worldline boundary with explicit barrier, seed, provider, and evidence refs. | Pass when restore stays bounded and fail-closed; block if it claims full restore, exact GPU, resident-state, or arbitrary unbounded worldline trees. |
| `WP21-A-R3` Scenario generation request surface | `WP21-D` | Turn the WP15 request surface into deterministic scenario/intervention generation with non-mutation guards and artifact lineage. | Pass when generation is deterministic, metadata-backed, and non-mutating; block if it forces scenario schema migration, mutates runtime state, or edits C++ rollout. |
| `WP21-A-R4` Counterfactual rollout and causal difference | `WP21-C` | Execute parent/branch worldlines and causal-difference runtime after B. | Pass when rollout consumes B's boundary and keeps raw mutation out; block until B is complete. |
| `WP21-A-R5` Experiment evidence collection | `WP21-E` | Expose the maintained experiment facade, collect observations/comparisons/traces, and preserve ancestry without truth or support promotion. | Pass when evidence collection is ancestry-safe and non-promotional; block until C and D are complete. |
| `WP21-A-R6` Final cleanup and acceptance handoff | `WP21-F` | Integrate A-E, close legacy residuals, sync indexes/docs, and prepare final acceptance after implementation evidence exists. | Pass only after A-E are complete; block if it tries to accept planned docs alone. |
| `WP21-A-R7` ScenarioLoader/runtime mirror compatibility | retained compatibility | Keep `ScenarioLoader` and the Python world-batch mirrors gated as frontend/compatibility surfaces until the WP18 split/gate residual is handled or explicitly retained at final acceptance. | Pass when the mirror stays narrow and guarded; block if it becomes maintained truth. |
| `WP21-A-R8` Typed setup compatibility baseline | retained compatibility | Keep the WP20 typed setup path additive and compatibility-preserving; do not force scenario-schema migration or replace the legacy setup path wholesale. | Pass when typed setup remains additive; block if it is promoted into a mandatory mainline schema change. |
| `WP21-A-R9` Backend/resident-state boundary | retained compatibility | Keep resident-state and exact-GPU support blocked, with `RuntimeFacade.runtime()` remaining diagnostics-only. | Pass when capability projection stays fail-closed; block any promotion of resident-state or exact GPU support. |

## First-Wave Readiness

| Stream | Readiness | Preconditions | Blockers |
|---|---|---|---|
| `WP21-B` | Ready after A | `WP21-A` freezes the selected-slice facts; selected-slice runtime evidence and fail-closed restore boundary already exist. | Cannot claim full restore, exact GPU, resident-state, or arbitrary unbounded worldline trees. |
| `WP21-D` | Ready after A | `WP21-A` freezes the request-surface facts; the WP15 request/artifact surface already exists and is metadata-only. | Cannot force scenario schema migration, mutate authoritative runtime state, or edit C++ rollout. |

Verdict: `WP21-B` and `WP21-D` can run in parallel after `WP21-A`. Their write scopes are disjoint, and the only shared dependency is the frozen fact ledger plus the same non-goal boundaries.

## Integration Notes

- `WP21-B` must start from `WP21-A-R2` and keep restore proof bounded to
  facade-owned, host-visible state.
- `WP21-D` must start from `WP21-A-R3` and stay in Python
  scenario/intervention generation; it must not edit C++ rollout behavior.
- `WP21-C` waits for B and must consume the B boundary rather than inventing a
  second branch execution path.
- `WP21-E` waits for C and D and must preserve non-truth-claim ancestry through
  the experiment evidence bridge.
- `WP21-F` is the only stream that can close retained compatibility residuals,
  and only after implementation evidence exists.

## Closure Impact

`WP21-A` closes the first-wave entry gate, not the WP21 route. The immediate
effect is dispatch readiness for `WP21-B` and `WP21-D`; the remaining effect is
that every later WP21 stream has a named pass/block criterion for contracts,
selected runtime, generation, loader mirrors, typed setup, and backend support
boundaries.

## Suggested Validation

```bash
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP21 --summary
```

## Handoff

Return the fact table, residual IDs, first-wave dispatch recommendation,
touched files, commands run and outcomes, blockers/residuals, and confirmation
that unrelated edits were not reverted.
