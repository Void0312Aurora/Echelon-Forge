# WP18 Subagent Dispatch Queue

Status: `2026-05-21` closed / accepted.

Language:

- English canonical: `wp18_subagent_dispatch_queue_20260521.md`
- Chinese companion:
  [wp18_subagent_dispatch_queue_20260521.zh.md](wp18_subagent_dispatch_queue_20260521.zh.md)

Use this queue when launching subagents. The main thread owns integration and
final acceptance.

## First Wave

| Stream | Agent type | Model / reasoning | Task | Write scope |
|--------|------------|-------------------|------|-------------|
| `WP18-A` | explorer or lightweight worker | `gpt-5.4-mini`, xhigh | Verify ownership facts, hot paths, C++ assets, and first-slice candidates. | WP18 docs/fixtures/architecture inventory tests only; no runtime behavior changes. |
| `WP18-B` | worker | `gpt-5.4`, xhigh | Implement or preflight one execution-episode ownership sink after A identifies the slice. | Execution episode facade/runtime seams and focused tests; do not split `ScenarioLoader`. |
| `WP18-C` | worker | `gpt-5.4`, high | Split or guard `ScenarioLoader` responsibilities between scenario/content adapter, runtime mirror, and frontend helper. | `ScenarioLoader` boundary files/tests only; do not edit C++ runtime logic. |
| `WP18-D` | worker | `gpt-5.4`, high | Harden facade/compatibility guards and allowlists after A, then integrate B/C surfaces. | Architecture guard tests, facade shape checks, compatibility allowlists. |
| `WP18-E` | worker | `gpt-5.4`, xhigh | Build migration matrix and implement one bounded C++ hot-path slice if safe. | Matrix docs plus selected C++ runtime or request build/consume files; coordinate with B/C. |

## Release Rules

| Stream | Release condition |
|--------|-------------------|
| `WP18-A` | Release immediately; it is the first-wave fact authority. |
| `WP18-B` | Release after A returns the selected ownership slice, or as preflight-only if A is still running. |
| `WP18-C` | Release after A names loader owner/mirror/helper categories, or as responsibility-map preflight. |
| `WP18-D` | Release after A for guard prework; final hardening waits for B/C replacement surfaces. |
| `WP18-E` | Release after A; implementation part waits until B/C conflict risks are known. |
| `WP18-F` | Do not release until A-E return mergeable or blocked packets. |

## First-Wave Return State

| Stream | Agent | Return status | Planning consequence |
|--------|-------|---------------|----------------------|
| `WP18-A` | Socrates | `pass` | Ownership facts are frozen in the WP18-A ledger. First implementation should start with the execution-episode ownership sink behind `ExecutionEpisodeController` and existing C++ runtime helpers, not a broad `ScenarioLoader` split or VecEnv rewrite. |
| `WP18-C` | Volta | `preflight-only / pass` | `ScenarioLoader` is already modular but still presents one mixed object. The safest first C slice is a field-classification guard for `SCENARIO_LOADER_STATE_SHELL_ATTRS`, not a behavioral split. |
| `WP18-D` | Copernicus | `preflight-only / pass` | Existing facade guards are strong around `leader_world_batch_runtime` and `WorldBatchVecEnv`, but global maintained-path `.world()` / `.batch_runtime.` coverage can be tightened without deleting public APIs. |
| `WP18-E` | Ampere | `preflight-only / pass` | The safest E first slice is replacing Python reward-breakdown / termination reconstruction on the default compiled path with C++-generated metadata. Request build/consume and episode-state sync remain high-risk and should coordinate with B/C. |

## Second Wave

| Stream | Agent type | Model / reasoning | Task | Write scope |
|--------|------------|-------------------|------|-------------|
| `WP18-B` | worker | `gpt-5.4`, xhigh | Implement the first execution-episode ownership sink using `ExecutionEpisodeController` and existing facade/runtime state exports. | Execution episode facade/runtime seams and focused tests. Do not edit `ScenarioLoader` internals or C++ hot-path reward logic. |
| `WP18-C` | worker | `gpt-5.4`, high | Add a `ScenarioLoader` state-shell responsibility classification guard, preserving public loader APIs. | `gym_envs/scenario_loader/runtime_state.py`, narrow loader classification tests, and WP18-C docs only. Do not edit C++ runtime logic. |
| `WP18-D` | worker | `gpt-5.4`, high | Add guard prework for maintained-path raw runtime/world/batch access without deleting compatibility APIs. | `tests/architecture/runtime_facade` and allowlist docs/comments only. Wait for B/C before final hard bans. |
| `WP18-E` | worker | `gpt-5.4`, xhigh | Implement the low-risk reward/termination metadata first slice if it can avoid B/C ownership conflicts. | C++ reward/termination metadata helper/binding or Python compiled-path consume seam plus focused tests. Do not change request build/consume ownership. |

## Second-Wave Return State

| Stream | Agent | Return status | Integration consequence |
|--------|-------|---------------|-------------------------|
| `WP18-B` | Mendel | `pass` | `ExecutionBatchStepResult.execution_episode_states` now carries facade/runtime-owned post-step episode state. `WorldBatchVecEnv` mainline consumes this field before legacy `step_result.controller_state`; compatibility payloads remain. |
| `WP18-C` | Herschel | `pass` | `ScenarioLoaderStateShell` fields now have immutable responsibility classifications and import-time contract validation. This is guard-only and does not split public loader behavior. |
| `WP18-D` | Bohr | `pass` | Facade-layer architecture tests now block new maintained `.batch_runtime.` and `RuntimeFacade.runtime()` consumers outside named compatibility/diagnostic allowlists. Public compatibility APIs remain. |
| `WP18-E` | Linnaeus | `pass` | Default compiled path now prefers C++ reward-breakdown metadata through a Python-visible helper. Python keeps narrow mirror/fallback behavior; request-build and episode-state sync ownership remain separate. |

Main-thread validation after second wave:

- `cmake --build build-workshop --target ef_core ef_py -j4` passed.
- `git diff --check` passed.
- `python3 tools/maintenance/wp_doc_closure_audit.py --wp WP18 --summary` passed; acceptance review remains intentionally absent while WP18 is active.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/runtime_facade` passed: `17 passed`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/runtime_spine/test_runtime_spine_inventory_gates.py` passed: `6 passed`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_state.py` passed: `5 passed`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_scenario_loader_execution_step_runtime.py -k "state or runtime or reward or termination"` passed: `11 passed, 8 subtests passed`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "execution or episode or batch"` passed: `4 passed, 14 deselected`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_facade_step_evidence_gates.py` passed: `1 passed`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "execution_episode_controller_mainline or compatibility_view"` passed: `6 passed, 31 deselected`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "execution_episode"` passed: `3 passed, 18 deselected`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py` passed after syncing cadence DTO public-field expectations: `17 passed`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_step_runtime.py` passed: `14 passed`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_scenario_loader_execution_step_runtime.py -k "cxx_reward_metadata or selected_paths_match_legacy_runtime or flight_shaping_backends_match_legacy_runtime"` passed: `3 passed, 8 deselected, 4 subtests passed`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_batch_prepare.py` passed: `2 passed`; the narrower `-k "reward or termination or breakdown"` filter is not a useful coverage gate in the current tree.

## Third Wave

| Stream | Agent type | Model / reasoning | Task | Write scope |
|--------|------------|-------------------|------|-------------|
| `WP18-B/D` | worker | `gpt-5.4`, high | Add regression evidence that maintained vec-env/facade consumers prefer facade-owned batch fields (`execution_episode_states`, reward, termination, status, reward breakdown) before legacy `step_result` payloads. | Focused tests in `tests/world_batch/test_world_batch_vec_env.py` and/or `tests/runtime/facade/test_facade_step_evidence_gates.py`. Do not edit runtime implementation unless a test exposes a real bug. |
| `WP18-C/D` | worker | `gpt-5.4`, high | Lift the `ScenarioLoaderStateShell` responsibility classification into an architecture guard or narrowly scoped ownership test so future loader fields cannot bypass classification. | Classification/architecture tests only. Prefer a new focused test or existing execution-state tests; avoid editing runtime behavior. |
| `WP18-E` | worker | `gpt-5.4`, high | Close the hot-path matrix coverage hole: document the second-wave reward metadata slice, replace the no-op `-k` validation with a meaningful test anchor, and identify the next safe migration candidate without implementing it. | WP18-E matrix docs plus focused test coverage if needed. Do not change B/C ownership seams or start request-build migration in this wave. |

## Third-Wave Return State

| Stream | Agent | Return status | Integration consequence |
|--------|-------|---------------|-------------------------|
| `WP18-B/D` | Raman | `pass` | Added focused vec-env regression evidence that facade-owned batch fields win over poisoned legacy `step_result` values for reward, done/truncated, status vector, termination reason, reward breakdown JSON, and state-change flag. Runtime implementation was not edited. |
| `WP18-C/D` | Helmholtz | `pass` | Added architecture-owned classification contract for `ScenarioLoaderStateShell`, pinning dataclass fields, bucket membership, and allowed buckets. Runtime behavior and C++ logic were not edited. |
| `WP18-E` | Godel | `pass` | Documented the reward metadata migration slice in the hot-path matrix and replaced the previously no-op batch-prepare `-k` gate with a real reward/termination/breakdown test anchor. Request-build migration remains deferred. |

Main-thread validation after third wave:

- `git diff --check` passed.
- `python3 tools/maintenance/wp_doc_closure_audit.py --wp WP18 --summary` passed; acceptance review remains intentionally absent while WP18 is active.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/runtime_facade` passed: `18 passed`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_state.py` passed: `5 passed`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "execution_episode_controller_mainline or compatibility_view or facade"` passed: `11 passed, 27 deselected`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_facade_step_evidence_gates.py` passed: `1 passed`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_step_runtime.py` passed: `14 passed`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_scenario_loader_execution_step_runtime.py -k "cxx_reward_metadata or selected_paths_match_legacy_runtime or flight_shaping_backends_match_legacy_runtime"` passed: `3 passed, 8 deselected, 4 subtests passed`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_batch_prepare.py` passed: `2 passed`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/execution/test_execution_episode_batch_prepare.py -k "reward or termination or breakdown"` passed: `1 passed, 1 deselected`.

## Required Worker Return Packet

```md
Stream:
Status: pass | fail | blocked | preflight-only
Touched files:
Commands run:
Evidence:
Residuals:
Integration notes:
Closure impact:
```

Worker reminder:

- You are not alone in the codebase; do not revert unrelated edits or edits made
  by other workers.
- Keep write scopes disjoint.
- Stop at a named blocker rather than broadening into WP19/WP20/WP21.
