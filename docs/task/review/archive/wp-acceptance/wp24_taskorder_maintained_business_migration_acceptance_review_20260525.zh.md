# WP24 TaskOrder Maintained Business Migration 验收审查

状态：`2026-05-25` accepted / closed，仅限 WP24 已声明的有边界范围。

语言：

- English canonical:
  [wp24_taskorder_maintained_business_migration_acceptance_review_20260525.md](wp24_taskorder_maintained_business_migration_acceptance_review_20260525.md)
- 中文 companion:
  `wp24_taskorder_maintained_business_migration_acceptance_review_20260525.zh.md`

输入：

- [WP24 TaskOrder Maintained Business Migration](../../../simulation_architecture/archive/wp24_taskorder_maintained_business_migration/taskorder_maintained_business_migration_wp24_20260524.zh.md)
- [WP24 Integration Assessment And Cleanup Close-Out](../../../simulation_architecture/archive/wp24_taskorder_maintained_business_migration/wp24_integration_assessment_and_next_dispatch_20260524.zh.md)
- [WP24 Facade Boundary Closure Task Package](../../../simulation_architecture/archive/wp24_taskorder_maintained_business_migration/wp24_facade_boundary_closure_task_package_20260524.zh.md)
- [TM01 Architecture Closure Remediation](../../../simulation_architecture/archive/tm01_architecture_closure_remediation/README.md)
- [TM02 WP24 Acceptance Closure](../../../simulation_architecture/archive/tm02_wp24_acceptance_closure/README.md)

## 1. 结论

WP24 作为一个有边界的 maintained-business migration 与 facade-boundary closure
增量通过验收。

验收结果是：

- public TaskOrder whole-shell batch/facade/Python writer surfaces 已删除；
- maintained TaskOrder business flow 使用 `TaskOrderMaintainedBatchContract`；
- observation export 已与 tasking export 分离；
- MissionCommand、LeaderIntent、PilotReport 的 maintained business slice 通过
  maintained contracts 路由，而不是 public facade whole-shell API；
- normal setup、full-batch stepping、runtime-window action injection 与 legacy
  visual fallback 均已被 guard，使 raw-runtime 或 compatibility path 不能默认静默回到
  maintained production flow；
- `agent_shim.py` 默认值是 maintained；compatibility/raw provenance 必须显式标记。

WP24 验收范围内没有剩余阻塞项。

## 2. Gate Verdicts

| Gate | Verdict | Evidence |
|------|---------|----------|
| TaskOrder public whole-shell deletion | pass | Runtime/facade/binding/Python public TaskOrder whole-shell writer surfaces 已删除；architecture guards 防止已删除名称回归。 |
| Observation/tasking export split | pass | `ObservationBatchPacket` 是纯 observation export；tasking reads 使用 `TaskingBatchRequest` 与 `TaskingBatchPacket`。 |
| Command-chain maintained contracts | pass | MissionCommand、LeaderIntent、PilotReport、TaskOrder 的业务读写在 maintained path 上经由 maintained batch contracts。 |
| Scenario setup and stepping boundary | pass | Normal batch setup/step paths 使用 maintained facade/adapter APIs；raw setup 与 partial raw stepping 仍是显式 compatibility-only behavior。 |
| Provenance and Law 14 guard | pass | `single_agent_role()` 与 `roster_slot_role()` 默认 maintained metadata；guards 会拒绝 relabeled raw 或 compatibility provenance。 |
| TM01 ground regression | pass | WP24 close-out 后发现的 ground tasking-shell enum regression 已修复并验证，不阻塞 WP24 acceptance。 |

## 3. Validation Rollup

`2026-05-25` 验收验证：

```bash
git diff --check
cmake --build build-workshop --target ef_py -j4
PYTHONPATH=build-workshop python -m py_compile python/scenario/runtime/batch_apply.py python/scenario/runtime/world_setup.py python/rl/runtime/world_batch/adapter.py python/rl/runtime/world_batch/command_chain_cache.py python/rl/runtime/world_batch_vec_env.py python/rl/runtime/cooperative_world_batch_vec_env.py python/rl/runtime/multi_agent_runtime.py python/rl/runtime/agent_shim.py gym_envs/universal_env.py train.py
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/test_agent_shim.py
PYTHONPATH=build-workshop python -m pytest -q tests/architecture/runtime_facade tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py tests/architecture/command_tasking/test_dto_domain_shell_guard.py
PYTHONPATH=build-workshop python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "observation or batch_runtime or task_order or command_chain or visual"
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py -k "observation or batch_runtime or task_order or command_chain"
PYTHONPATH=build-workshop python -m pytest -q tests/runtime/ground/test_ground_mvp_scenario.py tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py tests/leader/test_ground_profile_semantics.py tests/leader/test_common_core_semantics.py
```

观察结果：

- `git diff --check`：通过。
- `cmake --build build-workshop --target ef_py -j4`：通过。
- `py_compile`：通过；当前树使用 `python/scenario/runtime/world_setup.py`。旧 WP24
  验证文本中提到的 `world_setup_compat.py` 已相对当前树滞后。
- Runtime binding DTO 与 agent-shim 组：`54 passed`。
- Architecture guard 组：`71 passed`。
- World-batch VecEnv 切片：`23 passed, 38 deselected`。
- Cooperative world-batch VecEnv 切片：`7 passed, 23 deselected`。
- TM01 ground/leader regression 组：`26 passed`。

## 4. Residuals

以下 residual 被接受为 WP24 范围外事项：

- `SimulationKernel::set_task_order/get_task_order` 仍是 maintained batch contract
  下方的 implementation storage details；它们不是 public maintained business APIs。
- Raw `SimulationKernel`、`WorldBatchRuntime`、diagnostics 与 compatibility APIs
  仍可用于显式 tests、diagnostics 与 compatibility。WP24 只验收它们不再是默认
  maintained production path。
- TM01 已记录窄的 `systems -> SimulationKernel` weapon-release bridge residual，
  位于 `pilot_weapon_release_system.h` 与 `naval_mission_weapon_release_system.h`。
  该 residual 不是 WP24 blocker，也不由本验收关闭。
- 完整 ground runtime、广义 P7 launch/fire-control redesign，以及 public escape-hatch
  retirement 仍是后续工作。

## 5. Closure Verdict

WP24 在其有边界 maintained-business migration 范围内 accepted / closed。后续工作不得为了
解决 TM01-B launch-bridge ownership、ground runtime expansion 或 public raw-runtime
retirement 而重开 WP24；这些事项需要独立的有限 task lane 与自己的 validation gates。
