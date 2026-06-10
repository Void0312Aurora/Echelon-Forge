# WP22-C Runtime Escape Hatch 与 Legacy Mode 关闭

状态：`2026-05-22` 最新 implementation wave 已对 `RTE-003` final production
raw-loader cleanup、main-thread `A-001` maintained typed setup promotion、
`RTE-005` silent selection removal 与 `RTE-007` setup/type/schema ownership
完成本地验收。R3 必须先重新划分，再允许任何进一步 implementation 或
closure 派发。Runtime escape hatches 仍未完全退场：
`RuntimeFacade::runtime()` / `WorldBatchRuntime::world()`、`vec_env.batch_runtime`、
diagnostics bindings、显式 `legacy` mode 与 fallback cadence 只能作为命名
compatibility/diagnostics surface 存活。最新 GPU visual binding 切片也已移除
`bindings_gpu.cpp` 对 raw world 的直接下钻，改为通过命名的
`WorldBatchRuntime` compatibility helper 收集 scene。`L-002` 因此对
maintained facade internals 与 direct GPU binding residual 是 scoped pass，但
公开 raw escape hatch 仍处于 quarantine，并继续阻塞 WP22 closure。

预检说明：这是 guard hardening，不是 acceptance。repo-level 的 maintained Python
scan 现在也覆盖非测试入口，而 `train.py` 和
`tools/diagnostics/benchmarks/world_batch_vec_env.py` 继续停留在显式
compatibility/diagnostics allowlist 中，没有被退场。
Beauvoir 的 preflight packet 只作为 guard hardening 验收：explicit non-test
compatibility/diagnostics allowlist 外的 `batch_runtime` consumer 现在会使
architecture tests 失败，但 `WP22-F` 仍不 eligible，因为公开 runtime/world
escape hatch 和 diagnostics bindings 仍 live。

输入：

- [WP22 main plan](legacy_compatibility_retirement_wp22_20260522.zh.md)
- [WP22-A fact ledger](wp22_retirement_fact_ledger_cluster_20260522.zh.md)

## 核验范围

本轮重新核对了 `RTE-001` 到 `RTE-007` 以及 `L-002` 在当前代码树中的状态。结论仍是 forced-retirement audit，而不是 compatibility pass：所有仍存活的 raw runtime、raw loader 或 silent `legacy` 路径，都只能归为 `quarantine`、`migrate` 或 `blocker`。

## Source-Verified Findings

| 台账项 | 当前事实 | 分类 | Source anchors | 复现命令 |
|---|---|---|---|---|
| `RTE-001` | `RuntimeFacade::runtime()` 仍是存活的 raw escape hatch。C++ facade 仍返回 `WorldBatchRuntime&`，adapter 仍缓存该 raw runtime，而 architecture tests 仍以 allowlist 方式守住这条口子，说明它还没有退场。 | `quarantine` | `src/runtime/facade/runtime_facade.cpp:2360-2365`; `python/rl/runtime/world_batch/adapter.py:47-50`; `tests/architecture/runtime_facade/test_runtime_escape_hatches.py` | `rg -n "RuntimeFacade::runtime\\(|\\.runtime\\(" src python tests -S` |
| `RTE-002` | `vec_env.batch_runtime` 仍是公开的 compatibility view。该 property 仍在 maintained runtime code 中暴露，leader runtime group 继续转发它，测试也显式断言这个 compatibility view 仍然存在。diagnostics bindings 在 replacement APIs 存在前仍是 compatibility/diagnostics surface。 | `quarantine` | `python/rl/runtime/world_batch_vec_env.py:280-286`; `python/rl/runtime/leader_world_batch_runtime.py:204-206`; `tests/world_batch/test_world_batch_vec_env.py:457-473`; `tests/architecture/runtime_facade/test_runtime_escape_hatches.py` | `rg -n "batch_runtime" python/rl/runtime tests/world_batch tests/architecture -S` |
| `RTE-003` | Production `loader.sim.*` / `loader.sim,` usage 现在为空。Maintained runtime reward/info、tasking command writes、time-step reads、naval-screen unit reads、scripted-opponent kernel access、runtime-state 与 loading 路径都已转入命名 loader-owned seam 或 typed helper。 | `pass for production raw-loader cleanup` | `python/rl/tasking/bridge.py`; `python/rl/tasking/leader_tasking.py`; `gym_envs/scenario_loader/runtime_state.py`; `gym_envs/scenario_loader/loading.py`; `tests/architecture/runtime_facade`; `tests/architecture/command_tasking/test_tasking_bridge_guardrails.py` | `rg -n "loader\\.sim\\.|loader\\.sim," gym_envs python/rl -S` -> no matches |
| `RTE-004` | `execution_step_runtime_mode="legacy"` 只作为显式 compatibility opt-in 被接受。Env config 与 batch envs 在没有 `runtime_compatibility_enabled=True` 时拒绝 `legacy`，maintained setup 倾向 `compiled`。 | `quarantine / explicit opt-in` | `python/env_config.py:130-134`; `python/rl/runtime/world_batch_vec_env.py:151-156`; `python/rl/runtime/cooperative_world_batch_vec_env.py:146-150`; `tests/runtime/core/test_env_config.py`; `tests/world_batch/test_world_batch_vec_env.py` | `python -m pytest -q tests/runtime/core/test_env_config.py tests/world_batch/test_world_batch_vec_env.py -k "execution_step_runtime_mode or runtime_compatibility"` |
| `RTE-005` | Silent runtime-mode selection 已移除。`normalize_execution_step_runtime_mode(None)` 解析为 `compiled`，loader init 调用 `set_execution_step_runtime_mode("compiled")`，production/test scan 找不到 `CMO_EXECUTION_STEP_RUNTIME` 或 `set_execution_step_runtime_mode(None)` 锚点。 | `pass for silent-selection removal` | `gym_envs/scenario_loader/common.py:124-132`; `gym_envs/scenario_loader/core.py:262-267`; `python/env_config.py:130-134`; `tests/runtime/core/test_env_config.py` | `rg -n "CMO_EXECUTION_STEP_RUNTIME|set_execution_step_runtime_mode\\(None\\)" gym_envs python tests -S` -> no matches |
| `RTE-006` | `compatibility_fallback_world_batch_step_worlds_wp16c` 仍作为命名 fallback cadence path 保留，并由 compatibility tests 守住。它不是 maintained default。 | `quarantine / explicit fallback` | `python/rl/runtime/single_world_batch_runtime.py:255`; `python/rl/runtime/leader_world_batch_runtime.py:278`; `tests/world_batch/test_single_world_batch_runtime.py:211`; `tests/world_batch/test_single_world_batch_runtime.py:420` | `rg -n "compatibility_fallback_world_batch_step_worlds_wp16c" python tests -S` |
| `RTE-007` | terrain source、compiler metadata、runtime apply、world-batch setup 与 facade setup 现在共享显式非 legacy 默认 ownership。missing/blank terrain 会解析为带 `default_mainline` 来源的 `flat`；显式 legacy terrain 被标注为 `explicit_legacy_compatibility`。 | `pass for setup/type/schema slice` | `python/scenario/compiler/common.py`; `python/scenario/compiler/layout_template.py`; `python/scenario/runtime/kernel_apply.py`; `python/scenario/runtime/world_setup_compat.py`; `src/core/engine/world_batch_runtime.cpp`; `tests/runtime/core/test_world_setup_compat.py`; `tests/runtime/facade/test_runtime_facade.py`; `tests/world_batch/test_world_batch_runtime.py`; `tests/scenario/test_scenario_compiler.py` | `cmake --build build-workshop --target ef_py -j4 && bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "terrain or world_setup or setup"` |
| `L-002` | Raw batch/world access 仍是公开表面，但 maintained facade 与 direct GPU binding residual 已收窄。`WorldBatchRuntime::world()` 与 `RuntimeFacade::runtime()` 仍是 public compatibility/diagnostics escape hatch；`bindings_gpu.cpp` 已不再调用 `.world(`，而是消费 `collect_visual_binding_compatibility_scenes_batch(...)`，raw scene collection 集中到 `WorldBatchRuntime` 内部。diagnostics bindings 在 replacement APIs 存在前仍是 compatibility/diagnostics surface。旧 `runtime_facade.cpp:592` 锚点是 maintained typed setup 证据，不是 raw drilling。 | `quarantine / maintained facade 与 direct binding residual scoped pass` | `src/core/engine/world_batch_runtime.h:65-68`; `src/core/engine/world_batch_runtime.cpp:337-342`; `src/runtime/facade/runtime_facade.cpp:2498-2503`; `src/interfaces/python/bindings_gpu.cpp:520-527`; `src/core/engine/world_batch_runtime.cpp:1105-1130`; `tests/architecture/runtime_facade/test_runtime_escape_hatches.py` | `rg -n "RuntimeFacade::runtime\\(|WorldBatchRuntime::world\\(|collect_visual_binding_compatibility_scenes_batch|\\.world\\(" src python tests -S` |

## Implementation Dispatch Readiness

| 范围 | 现在可开始？ | 原因 |
|---|---|---|
| `RTE-001` | `yes` | 基于已核实的 escape-hatch 位置，可以立刻开始做 guard tightening 与 compatibility-module quarantine。 |
| `RTE-002` | `yes` | 可以先把公开 `batch_runtime` 收紧成显式 compatibility naming 与 allowlist guard，无需等待其他工作包。 |
| `RTE-004` | `guard follow-up only` | 显式 compatibility opt-in 已被强制；剩余工作是 guard coverage，避免新增 default-legacy caller。 |
| `RTE-005` | `complete for silent-selection slice` | env-silent selection 与 `None` setter anchors 已从扫描范围内清空。 |
| `RTE-006` | `guard follow-up only` | compatibility fallback 仍是命名且测试可见的路径；不得把它升级为 maintained default。 |
| `RTE-003` | `complete for production raw-loader cleanup` | 最新 wave 已从 `gym_envs` 与 `python/rl` 移除最终 production `loader.sim.*` / `loader.sim,` 锚点。 |
| `RTE-007` | `complete for setup/type/schema slice` | source、重建 binding、compiler metadata、runtime apply、facade setup 与 world-batch setup 现在都对齐到非 legacy 默认值与显式 legacy compatibility 标签。 |
| `L-002` | `guard follow-up / service split` | maintained facade raw drilling 与 direct GPU binding raw-world use 已在各自 scoped slice 中关闭。公开 `RuntimeFacade::runtime()` / `WorldBatchRuntime::world()` escape hatch 与 diagnostics bindings 仍需要 guard discipline 与后续 service-boundary narrowing。 |

## Required Runtime-Closure Direction

- `migrate`：`RTE-007` 的 source、binding、setup、type 与 schema ownership
  现在已经证明默认值为 `flat`；剩余显式 `legacy` schema 值是 compatibility
  consumer，不是 maintained default。
- `migrate / pass`：`RTE-003` production raw-loader cleanup 与 `RTE-005`
  silent-selection removal 已在各自 scoped runtime lane 中本地验收。
- `quarantine`：`RTE-001`、`RTE-002`、`RTE-004` 与 `RTE-006` 只能以命名清晰、
  guard-tested、allowlist 化的 compatibility surface 形式存活。
- `quarantine`：`L-002` 对 maintained facade internals 与 direct GPU binding
  raw-world drilling 是 scoped pass，但公开 C++ facade/world raw accessors
  和 diagnostics bindings 仍是 compatibility/diagnostics escape hatch；在被
  进一步收窄或作为显式 opt-in 加 guard 前，不能作为 closure。

## 当前实现轮次快照

| 字段 | 值 |
|---|---|
| `status` | `partial overall`：`RTE-003`、`A-001`、`RTE-005`、`RTE-007` 与 direct GPU visual binding raw-world slice 已通过；`RTE-001`、`RTE-002`、`RTE-004`、`RTE-006` 与公开 `L-002` escape-hatch quarantine 仍是 compatibility/guard work。 |
| `commands run` | `git diff --check` -> 通过；`cmake --build build-workshop --target ef_py -j4` -> worker packet 中通过；`rg -n "loader\\.sim\\.|loader\\.sim," gym_envs python/rl -S` -> 无匹配；`tests/architecture/runtime_facade` focused runtime guards -> accepted packets 中合计 `8 + 4` passed；`tests/architecture/command_tasking/test_tasking_bridge_guardrails.py` -> `7` passed；env/world-batch fallback tests -> `6 + 3 + 8` passed。 |
| `remaining blockers` | 公开 `RuntimeFacade::runtime()` / `WorldBatchRuntime::world()` compatibility access 仍存在；`batch_runtime`、`legacy`、fallback cadence 与 diagnostics bindings 这些显式 compatibility surfaces 仍需 guard discipline。direct `bindings_gpu.cpp` raw-world residual 现在已隔离到 `WorldBatchRuntime::collect_visual_binding_compatibility_scenes_batch(...)`。R3 必须先重新划分，再允许任何进一步 implementation 或 closure 派发。 |
| `integration notes` | C++ raw facade/world narrowing 应与 command/setup 和 structural decomposition 分开派发。只有这些以及 structural/command blockers 关闭或显式加 guard 后，才可创建 acceptance。 |

## 第一轮实现快照

这是历史快照，用来说明后续 Russell 与 Bernoulli packet 为什么需要派发；
当前状态以上方表格为准。

| 字段 | 值 |
|---|---|
| `status` | `partial` |
| `commands run` | `git diff --check` -> 通过；`python -m pytest -q tests/architecture/runtime_facade -k "runtime_facade_runtime_consumers or leader_world_batch_runtime_does_not_call_runtime_facade_runtime or batch_runtime"` -> 受缺失 `ef_py.ConditionalObjectiveProperty` 影响而被 collection 限制；聚焦 runtime opt-in/quarantine 测试通过；聚焦 env/world_batch 测试 `2+3+2` 通过 |
| `remaining blockers` | 已被当前快照覆盖：`RTE-003` production raw-loader cleanup 与 `RTE-007` setup/type/schema ownership 后续已通过；`L-002` 仍开放。 |
| `integration notes` | 保持 quarantine allowlists 显式，不要把 escape hatches 描述成已退场；不得重新引入 production `loader.sim` 锚点。 |

## Return Packet

这是较早的 documentation verification packet。它在 `RTE-003`、`RTE-005` 与
`RTE-007` 上已被当前 implementation wave 覆盖，但仍说明 `L-002` 为什么开放。

### Verification Notes

| 字段 | 值 |
|---|---|
| `status` | `partial` |
| `touched files` | `docs/task/simulation_architecture/archive/wp22_legacy_compatibility_retirement/wp22_runtime_escape_hatch_closure_cluster_20260522.md`; `docs/task/simulation_architecture/archive/wp22_legacy_compatibility_retirement/wp22_runtime_escape_hatch_closure_cluster_20260522.zh.md` |
| `commands run` | 历史 packet：早期扫描发现 live runtime escape hatches 与 compatibility surfaces。当前 verification 已在 `loader.sim`、`CMO_EXECUTION_STEP_RUNTIME`、`set_execution_step_runtime_mode(None)` 与 terrain setup 方面覆盖此结果。 |
| `remaining blockers` | 当前 closure blocker 是公开 compatibility surface：在 replacement APIs 或显式 quarantine guards 存在前，raw facade/world access 不能完全关闭。原 direct GPU binding residual 已转入命名 `WorldBatchRuntime` compatibility helper。 |
| `integration notes` | 不得把 compatibility residual 当作 pass。Runtime quarantine work 只可在 ready 子集上推进，且不得重新引入 production `loader.sim` 锚点。 |
| `WP22-C implementation dispatch allowed?` | `no`，因为 R3 必须先重新划分。公开 `RuntimeFacade::runtime()` / `WorldBatchRuntime::world()` access 以及 `RTE-001`、`RTE-002`、`RTE-004`、`RTE-006` 与 diagnostics bindings 仍属 compatibility/diagnostics work；不要重开已完成的 direct GPU binding residual。 |

## 停止规则

- 只要 raw C++ access 与 compatibility views 仍存活，就不得把 `RuntimeFacade.runtime()`、`batch_runtime`、`vec_env.batch_runtime` 或 diagnostics bindings 描述成已退场。
- 不得把 `legacy` mode 当作 maintained path 的可接受行为；它只能是显式 compatibility opt-in。
- 不得在 `gym_envs` 或 `python/rl` 重新引入 production `loader.sim.*` / `loader.sim,` 锚点。
