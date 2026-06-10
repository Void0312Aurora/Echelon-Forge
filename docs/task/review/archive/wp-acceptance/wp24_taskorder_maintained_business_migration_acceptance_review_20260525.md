# WP24 TaskOrder Maintained Business Migration Acceptance Review

Status: `2026-05-25` accepted / closed for the bounded WP24 scope.

Language:

- English canonical:
  `wp24_taskorder_maintained_business_migration_acceptance_review_20260525.md`
- Chinese companion:
  [wp24_taskorder_maintained_business_migration_acceptance_review_20260525.zh.md](wp24_taskorder_maintained_business_migration_acceptance_review_20260525.zh.md)

Inputs:

- [WP24 TaskOrder Maintained Business Migration](../../../simulation_architecture/archive/wp24_taskorder_maintained_business_migration/taskorder_maintained_business_migration_wp24_20260524.md)
- [WP24 Integration Assessment And Cleanup Close-Out](../../../simulation_architecture/archive/wp24_taskorder_maintained_business_migration/wp24_integration_assessment_and_next_dispatch_20260524.md)
- [WP24 Facade Boundary Closure Task Package](../../../simulation_architecture/archive/wp24_taskorder_maintained_business_migration/wp24_facade_boundary_closure_task_package_20260524.md)
- [TM01 Architecture Closure Remediation](../../../simulation_architecture/archive/tm01_architecture_closure_remediation/README.md)
- [TM02 WP24 Acceptance Closure](../../../simulation_architecture/archive/tm02_wp24_acceptance_closure/README.md)

## 1. Verdict

WP24 is accepted as a bounded maintained-business migration and facade-boundary
closure increment.

The accepted result is:

- public TaskOrder whole-shell batch/facade/Python writer surfaces are removed;
- maintained TaskOrder business flow uses `TaskOrderMaintainedBatchContract`;
- observation export is split from tasking export;
- MissionCommand, LeaderIntent, and PilotReport maintained business slices are
  routed through maintained contracts instead of public facade whole-shell APIs;
- normal setup, full-batch stepping, runtime-window action injection, and legacy
  visual fallback are guarded so raw-runtime or compatibility paths cannot
  silently re-enter maintained production flow by default;
- `agent_shim.py` defaults are maintained, and compatibility/raw provenance must
  be explicit when used.

No blocking findings remain inside the WP24 acceptance scope.

## 2. Gate Verdicts

| Gate | Verdict | Evidence |
|------|---------|----------|
| TaskOrder public whole-shell deletion | pass | Runtime/facade/binding/Python public TaskOrder whole-shell writer surfaces are removed; architecture guards protect against deleted names returning. |
| Observation/tasking export split | pass | `ObservationBatchPacket` is pure observation export, while tasking reads use `TaskingBatchRequest` and `TaskingBatchPacket`. |
| Command-chain maintained contracts | pass | MissionCommand, LeaderIntent, PilotReport, and TaskOrder business writers/readers route through maintained batch contracts on the maintained path. |
| Scenario setup and stepping boundary | pass | Normal batch setup/step paths use maintained facade/adapter APIs; raw setup and partial raw stepping remain explicit compatibility-only behavior. |
| Provenance and Law 14 guard | pass | `single_agent_role()` and `roster_slot_role()` default to maintained metadata, and guards reject relabeled raw or compatibility provenance at maintained entry points. |
| TM01 ground regression | pass | The ground tasking-shell enum regression found after WP24 close-out is fixed and validated, so it does not block WP24 acceptance. |

## 3. Validation Rollup

Recorded acceptance validation on `2026-05-25`:

```bash
git diff --check
cmake --build build-workshop --target ef_py -j4
PYTHONPATH=build-workshop python -m py_compile python/scenario/runtime/batch_apply.py python/scenario/runtime/world_setup.py python/rl/runtime/world_batch/adapter.py python/rl/runtime/world_batch/command_chain_cache.py python/rl/runtime/world_batch_vec_env.py python/rl/runtime/cooperative_world_batch_vec_env.py python/rl/runtime/multi_agent_runtime.py python/rl/runtime/agent_shim.py gym_envs/universal_env.py train.py
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/test_agent_shim.py
PYTHONPATH=build-workshop python -m pytest -q tests/architecture/runtime_facade/test_layering.py tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py tests/architecture/command_tasking/test_dto_domain_shell_guard.py
PYTHONPATH=build-workshop python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "observation or batch_runtime or task_order or command_chain or visual"
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py -k "observation or batch_runtime or task_order or command_chain"
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/ground/test_ground_mvp_scenario.py tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py tests/leader/test_ground_profile_semantics.py tests/leader/test_common_core_semantics.py
```

Observed outcomes:

- `git diff --check`: passed.
- `cmake --build build-workshop --target ef_py -j4`: passed.
- `py_compile`: passed using the current `python/scenario/runtime/world_setup.py`
  module. The older WP24 validation text that named `world_setup_compat.py` is
  stale relative to the current tree.
- Runtime binding DTO and agent-shim batch: `54 passed`.
- Architecture guard batch: `71 passed`.
- World-batch VecEnv slice: `23 passed, 38 deselected`.
- Cooperative world-batch VecEnv slice: `7 passed, 23 deselected`.
- TM01 ground/leader regression batch: `26 passed`.

## 4. Residuals

The following are accepted residuals outside WP24:

- `SimulationKernel::set_task_order/get_task_order` remain implementation storage
  details beneath the maintained batch contract; they are not public maintained
  business APIs.
- Raw `SimulationKernel`, `WorldBatchRuntime`, diagnostics, and compatibility
  APIs remain available for explicit tests, diagnostics, and compatibility use.
  WP24 only accepts that they are not the default maintained production path.
- TM01 recorded a narrow `systems -> SimulationKernel` weapon-release bridge
  residual in `pilot_weapon_release_system.h` and
  `naval_mission_weapon_release_system.h`. That residual is not a WP24 blocker
  and is not closed by this review.
- Full ground runtime behavior, broad P7 launch/fire-control redesign, and public
  escape-hatch retirement remain future work.

## 5. Closure Verdict

WP24 is accepted and closed for its bounded maintained-business migration scope.
Future work must not reopen WP24 to solve TM01-B launch-bridge ownership, ground
runtime expansion, or public raw-runtime retirement. Those require separate
finite task lanes with their own validation gates.
