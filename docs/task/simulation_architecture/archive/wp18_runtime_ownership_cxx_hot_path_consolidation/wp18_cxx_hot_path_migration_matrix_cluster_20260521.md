# WP18-E C++ Hot Path Migration Matrix

Status: `2026-05-21` complete / accepted.

Language:

- English canonical: `wp18_cxx_hot_path_migration_matrix_cluster_20260521.md`
- Chinese companion:
  [wp18_cxx_hot_path_migration_matrix_cluster_20260521.zh.md](wp18_cxx_hot_path_migration_matrix_cluster_20260521.zh.md)

Inputs:

- [WP18 main plan](runtime_ownership_cxx_hot_path_consolidation_wp18_20260521.md)
- [WP18-A ownership fact ledger](wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.md)
- [WP18 dispatch queue](wp18_subagent_dispatch_queue_20260521.md)
- [Architecture and performance follow-up](../../../plan/architecture/architecture_and_performance_research_followup.md)

## Purpose

Turn performance-route advice into a bounded migration matrix and document the
first completed WP18-E slice. WP18-E does not rewrite every hot path. It ranks
candidate paths, records the safe migration already completed, and leaves the
next candidate named but unimplemented.

## Scope

In scope:

- migration matrix for reward/termination metadata, route/approach/post-transition
  metadata, request build/consume, observation export, and episode-state sync;
- complexity, owner, risk, test anchors, and dependency notes for each row;
- concrete second-wave reward metadata closure and residuals;
- a meaningful validation anchor for batch-prepare reward/termination/breakdown
  coverage.

Out of scope:

- CUDA/resident-state migration;
- full Gym frontend rewrite;
- request-build migration in this wave;
- B/C ownership seam changes.

## Second-Wave Result

The selected first slice is complete. The default compiled `ScenarioLoader`
path now prefers C++ reward-breakdown metadata generated through
`ef_py.build_episode_reward_breakdown_json` before falling back to Python mirror
reconstruction. This keeps reward total, termination reason, status, and
reward-breakdown terms aligned with the C++ `ExecutionEpisodeRuntimeInputs` /
`ExecutionEpisodeRuntimeProducts` contract while preserving narrow Python
compatibility behavior.

The previous batch-prepare validation selector,
`tests/runtime/execution/test_execution_episode_batch_prepare.py -k "reward or termination or breakdown"`,
matched no tests. The coverage anchor is now the renamed
`test_batch_prepare_reward_termination_breakdown_matches_direct_runtime_inputs`,
which compares prepared batch runtime inputs against direct runtime inputs and
also validates the C++ reward-breakdown JSON generated from both sides.

## Migration Matrix

| Rank | Candidate | Status | Value | Complexity | Owner / seam | Risk | Test anchor | Routing |
|---|---|---|---|---|---|---|---|---|
| 1 | Reward/termination breakdown metadata on default compiled path | `closed in second wave` | high | low-medium | C++ `core/mission/runtime`, `episode/detail/episode_reward_breakdown`, Python compiled consume seam | low | `test_compiled_episode_runtime_prefers_cxx_reward_metadata`, `test_episode_reward_breakdown_builder_matches_reward_total_and_terms`, `test_batch_prepare_reward_termination_breakdown_matches_direct_runtime_inputs` | Keep as WP18-E closure evidence. No further runtime change in third wave. |
| 2 | Route/approach/post-transition metadata handoff | `next safe candidate / not implemented` | high | medium | C++ episode detail helpers plus `ScenarioLoader` runtime mirror | medium | Existing route/approach controller and scenario-loader parity tests; needs a new narrow metadata-preference test before migration | Safe next candidate because C++ transition/detail helpers already exist, but it must be a metadata handoff only, not a request-build rewrite. |
| 3 | Episode-state sync and facade-owned batch consume | `partially advanced by WP18-B` | high | medium-high | `ExecutionEpisodeController`, facade DTOs, `WorldBatchVecEnv` consume path | medium-high | facade/world-batch regression anchors from WP18-B/D | Route through B/D. WP18-E should not alter the ownership seam in this wave. |
| 4 | Observation export | `defer` | medium | medium-high | facade observation DTOs and compatibility adapter | medium | observation runtime and world-batch compatibility tests | Revisit after facade-owned batch evidence is stable. |
| 5 | Request build/consume loop migration | `defer / blocked for this wave` | high | high | `WorldBatchVecEnv`, facade adapter, request DTO contracts | high | would require broad vec-env/facade coverage | Do not start in WP18-E third wave. Wait until B/C seams and compatibility payloads are settled. |

## Residuals

| Residual | Impact | Owner / next action |
|---|---|---|
| Python fallback for reward metadata remains | Compatibility is intentional, but the maintained default path should continue to prefer C++ metadata. | Keep focused tests around C++ metadata preference; remove fallback only after compatibility consumers retire. |
| Batch-prepare coverage previously had a no-op `-k` gate | Main-thread validation could pass without selecting any batch-prepare reward tests. | Use `-k "reward or termination or breakdown"` only now that it selects the renamed anchor, or run the full batch-prepare file. |
| Route/approach/post-transition metadata still has Python mirror work | It is the next safe migration candidate, but it has not been implemented. | Preflight a narrow metadata-preference test before any runtime edit. |
| Request build/consume remains hot Python frontend code | High performance value but high ownership risk. | Defer until B/C ownership seams and facade compatibility contracts are fully stable. |

## Validation

Required third-wave validation:

```bash
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP18 --summary
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_step_runtime.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_scenario_loader_execution_step_runtime.py -k "cxx_reward_metadata or selected_paths_match_legacy_runtime or flight_shaping_backends_match_legacy_runtime"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_batch_prepare.py
```

Optional narrow anchor check:

```bash
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_batch_prepare.py -k "reward or termination or breakdown"
```

## Handoff

WP18-E closure impact: the first hot-path metadata slice is documented as
complete, the default compiled path preference is explicit, the prior no-op
validation selector now maps to real coverage, and the next safe migration
candidate is route/approach/post-transition metadata handoff without starting
request-build migration.
