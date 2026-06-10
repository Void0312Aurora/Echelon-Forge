# WP22-E 结构性 God File 拆分

状态：`2026-05-22` 当前 structural implementation wave 已对两个入口头拆分切片完成
本地验收。`counterfactual_replay_contracts.h` 现在是低于 `1500` 阈值的 umbrella
header，`runtime_window_coordinator.h` 现在低于 `1000` 阈值。后续集成也已完成
validation family 拆分，把手写 naval post-`step()` fire loop 退场到命名 helper
system，将 direct GPU visual binding raw-world access 收窄到命名
`WorldBatchRuntime` helper，并把 default-factory legacy seed ownership 移入
`default_factory_legacy_spawn_compat.h`。WP22-E 仍开放，因为 `runtime_facade.cpp`、
`default_unit_factory.h`、broad bindings、`WorldBatchRuntime` service 体量与公开
compatibility/diagnostics escape hatches 仍是结构债。
第八轮 Banach 与 Planck 切片收窄了两个结构 seam：maintained binding reads
现在使用 kernel-owned query methods，visual-binding compatibility scene assembly
也已移入 private helper。这些只是 scoped pass；broad bindings、diagnostics/legacy
raw ECS、公开 raw `world()` 与更广义 `WorldBatchRuntime` service surface 仍开放。

Noether pass：结构残留现在只允许以“命名 blocker + owner + failing guard”的形态保留。
只要新的入口头阈值回归，或把结构债当作无 guard residual，`WP22-E` 就不能被表述为通过。
`PilotWeaponRelease` 与 naval mission weapon release 现在都通过命名 helper system 注册。
`default_unit_factory.h` 已不再 direct include `legacy_command.h`，但新的
`default_factory_legacy_spawn_compat.h` seed seam 在 typed control-state
replacement 落地前仍只是 evaluation/guard。

Guard wording checkpoint：
`counterfactual_replay_contracts.h` 入口头已低于 `1500` 行；
`runtime_window_coordinator.h` 入口头已低于 `1000` 行；
`counterfactual_replay_contract_validation.h` 现在是委托 validation family headers 的薄 umbrella；
`PilotWeaponRelease` 与 naval mission weapon release 现在都通过命名 helper system 注册；
`default_factory_legacy_spawn_compat.h` 持有剩余 default-factory legacy seed seam，
在本轮仍只是 evaluation/guard。
`bindings_core.cpp` 现在已拆出 maintained、diagnostics、legacy 与
diagnostics-override registration helper；maintained binding reads 现在经由
kernel-owned query methods。broad binding surface 与 diagnostics/legacy raw-ECS
block 仍开放。

输入：

- [WP22 main plan](legacy_compatibility_retirement_wp22_20260522.zh.md)
- [WP22-A fact ledger](wp22_retirement_fact_ledger_cluster_20260522.zh.md)

## 目的

把最大的旧实现文件从“可容忍结构债”转为显式的 behavior-preserving extraction
工作，带 owner、测试和 guard。只要源码仍显示 mixed responsibility 或 live
compatibility escape hatch，WP22-E 就不能把这些 god-file surface 视为可接受 residual。

## 源事实复核范围快照

| ID | 已核验 live fact | Source anchors | Retirement mode | Implementation dependency |
|----|------------------|----------------|-----------------|---------------------------|
| `F-001` | `counterfactual_replay_contracts.h` 现在是 `130` 行 umbrella header，`counterfactual_replay_contract_validation.h` 现在是委托 helper/replay/counterfactual/experiment validation family headers 的薄 umbrella。 | `wc -l src/runtime/contracts/counterfactual_replay_contracts.h src/runtime/contracts/counterfactual_replay_contract_validation.h src/runtime/contracts/counterfactual_replay_*validation*.h`; validation family headers under `src/runtime/contracts/` | `pass for validation-family split` | 保持 family ownership 显式，并防止 umbrella 回归。 |
| `F-002` | `runtime_facade.cpp` 仍是 2809 行混合 TU，包含 typed-spawn compatibility materialization 与 raw runtime escape-hatch access。 | `wc -l src/runtime/facade/runtime_facade.cpp`; `src/runtime/facade/runtime_facade.cpp:261-279`; `src/runtime/facade/runtime_facade.cpp:320-478`; `src/runtime/facade/runtime_facade.cpp:2360-2364` | `migrate` | 必须与 `WP22-C` 协调 raw-runtime boundary，并与 `WP22-D` 协调 typed setup ownership；不得并行修改共享 boundary range。 |
| `F-003` | `runtime_window_coordinator.h` 现在是 `405` 行入口头，selection、callback、cadence-trace 与 execution helpers 已进入命名 companion headers。 | `wc -l src/runtime/facade/runtime_window_coordinator.h src/runtime/facade/runtime_window_coordinator_*.h`; `src/runtime/facade/runtime_window_coordinator_selection_helpers.h`; `src/runtime/facade/runtime_window_coordinator_callback_helpers.h`; `src/runtime/facade/runtime_window_coordinator_cadence_trace_helpers.h`; `src/runtime/facade/runtime_window_coordinator_execution_helpers.h` | `migrate / pass for entry-header slice` | 入口头拆分已通过。保持 helper ownership 显式，不要在此 stream 重开 runtime-boundary semantics。 |
| `F-004` | `default_unit_factory.h` 仍是 `1459` 行混合 header，负责 capability bundle / spawn plan 与 entity spawn。它已不再 direct include `legacy_command.h`；剩余 legacy command seed 隔离在 `default_factory_legacy_spawn_compat.h`，仍阻塞 typed control-state closure。 | `wc -l src/models/core/default_unit_factory.h src/components/command/default_factory_legacy_spawn_compat.h`; `src/models/core/default_unit_factory.h:14`; `src/models/core/default_unit_factory.h:1259-1277`; `src/components/command/default_factory_legacy_spawn_compat.h:3-58` | `migrate / scoped seed-narrowing pass` | 必须与 `WP22-D` 协调，因为 spawn ownership 与 legacy-command retirement 共用此文件/helper 对；spawn-init range 同时只能有一个 worker 持有。helper seam 在 typed control-state replacement 落地前仍只是 evaluation/guard。 |
| `F-005` | runtime contract header 总数为 `11`，其中 `9/11` 已超过 300 行。这仍是 live mixed-responsibility cluster，不是已关闭 residual。 | `find src/runtime/contracts -maxdepth 1 -name '*.h' -print0 | xargs -0 wc -l | sort -n`; `src/runtime/contracts/fidelity_profile_contracts.h`; `src/runtime/contracts/world_batch_contracts.h`; `src/runtime/contracts/parity_budget_contracts.h`; `src/runtime/contracts/counterfactual_replay_contracts.h` | `migrate` | 可立即启动 constants/types/validation 抽取；不得让并发 worker 拆同一张 normative table。 |
| `S-004` | `WorldBatchRuntime` 仍暴露 fat public surface，包括 raw `world()` access、setup、mutation、export 与 query 职责。Direct `bindings_gpu.cpp` raw-world drilling 已关闭，visual-binding compatibility scene assembly 已抽到 private helper，但 batch service 仍然很宽。 | `src/core/engine/world_batch_runtime.h:65-68`; `src/core/engine/world_batch_runtime.h:137-142`; `src/core/engine/world_batch_runtime.cpp:337-342`; `src/core/engine/world_batch_runtime.cpp:1105-1130`; `src/core/engine/world_batch_visual_binding_compatibility_helper.h`; `src/interfaces/python/bindings_gpu.cpp:520-527` | `migrate / scoped service split pass` | 必须与 `WP22-C` 协调，因为 service-split decision 依赖 maintained facade/runtime boundary。 |
| `S-005` | `bindings_core.cpp` 仍暴露 `75` 个 `.def`，但 registration 现在明确拆成 maintained、diagnostics-introspection、legacy-compatibility 与 diagnostics-override helpers。Maintained binding reads 现在使用 kernel-owned query methods，不再依赖本地 raw-entity lookup；diagnostics 与 legacy helper block 仍有意 raw-drill。 | `wc -l src/interfaces/python/bindings_core.cpp src/interfaces/python/bindings_gpu.cpp`; `src/interfaces/python/bindings_core.cpp`; `src/core/engine/simulation_kernel.h`; `src/core/engine/simulation_kernel_observation_api.cpp`; `tests/architecture/structural_boundaries` | `quarantine / maintained seam pass` | 下一步应减少 broad public binding surface，或把更多 maintained API 迁向 facade/kernel-owned methods，同时保持 debug/legacy block 显式 quarantine。改 public maintained binding 前需与 `WP22-C` 对齐。 |
| `S-006` | 本切片的 inline ordering residual 已退场。`PilotWeaponRelease` 与 naval mission weapon release 都通过命名 helper systems 注册，旧的手写 naval post-step query loop 已不存在。 | `src/core/engine/simulation_kernel_systems.cpp`; `src/systems/combat/pilot_weapon_release_system.h`; `src/systems/naval/naval_mission_weapon_release_system.h`; `src/core/engine/simulation_kernel.cpp` | `pass for ordering helper seams` | 保持 helper registration guard；更广义 execution-phase dependency design 是后续结构债，不是本 blocker。 |

## 可复现命令

以下命令用于本次 source pass，任何实现 worker 在宣称 decomposition 进展前都应重跑。

```bash
git diff --check
find src/runtime/contracts -maxdepth 1 -name '*.h' -print0 | xargs -0 wc -l | sort -n
wc -l src/runtime/facade/runtime_facade.cpp src/runtime/facade/runtime_window_coordinator.h src/models/core/default_unit_factory.h src/components/command/default_factory_legacy_spawn_compat.h src/interfaces/python/bindings_core.cpp
rg -n "PilotWeaponRelease|register_pilot_weapon_release_system|query<const MissionCommand, const NavalWeaponSystem>|RuntimeFacade::runtime\\(|^\\s*\\.def\\(\"" src/interfaces/python/bindings_core.cpp src/core/engine/simulation_kernel_systems.cpp src/core/engine/simulation_kernel.cpp src/runtime/facade/runtime_facade.cpp
rg -n "^struct |^inline constexpr |validate_" src/runtime/contracts/counterfactual_replay_contracts.h
rg -n "class WorldBatchRuntime|WorldBatchRuntime::world\\(|collect_visual_binding_compatibility_scenes_batch|spawn_units_batch\\(|apply_world_setup\\(|export_|set_|get_|clear_|reset_" src/core/engine/world_batch_runtime.h src/core/engine/world_batch_runtime.cpp
rg -n "build_platform_capability_bundle_template|resolve_platform_spawn_plan|compatibility_path_preserved|legacy_command|default_factory_legacy_spawn_compat|spawn\\(" src/models/core/default_unit_factory.h src/components/command/default_factory_legacy_spawn_compat.h
```

本次执行结果：

- `git diff --check`：没有 whitespace 或 conflict-marker 输出。
- contract-header count：总计 `11` 个 header，其中 `9` 个超过 300 行。
- god-file count 每次 structural dispatch 前都应重新测量；最新本地检查为
  `runtime_facade.cpp = 2951`、`runtime_window_coordinator.h = 405`、
  `default_unit_factory.h = 1459`、`default_factory_legacy_spawn_compat.h = 58`、
  `bindings_core.cpp = 965`。
- binding-surface count：`bindings_core.cpp:433-962` 中共有 `75` 个 `.def`。
- 第八轮 binding 复核：maintained reads 现在使用 `get_instrument_state`、
  `get_egi_state`、`get_unit_heading`、`get_unit_type`、`is_unit_active` 等
  kernel-owned methods；diagnostics/legacy raw ECS 仍是 quarantine，而不是已退场。
- 第八轮 service split：visual-binding compatibility scene assembly 已移动到
  `world_batch_visual_binding_compatibility_helper.h`；公开
  `WorldBatchRuntime::world()` 仍是显式 compatibility/diagnostics escape hatch。
- ordering `rg`：确认 `PilotWeaponRelease` 与 naval mission weapon release
  都通过命名 helper systems 注册。`simulation_kernel_systems.cpp` 已不再携带
  registered-in-place inline `OnUpdate` 例外，旧 manual naval query loop 已缺失。

## 并行与依赖规则

| 工作分片 | 派发姿态 | 规则 |
|----------|----------|------|
| `F-001`、`F-003`、`F-005` | `可立即启动` | 只要不改变 public semantics，就可以立刻开始 behavior-preserving extraction。 |
| `S-005` | `可立即启动但需协调` | 可先做 broad binding-surface reduction，或补充 facade/kernel-owned maintained methods，但 public maintained binding 变更必须与 `WP22-C` 对齐。 |
| `F-002`、`S-004` | `等待 WP22-C 协调` | 任何改变 `RuntimeFacade::runtime()`、`WorldBatchRuntime::world()` 或 maintained runtime service boundary 的 split 都不得与 `WP22-C` 竞争。 |
| `F-004` | `需与 WP22-D 协调` | spawn-plan extraction 与 legacy-command seeding 是和 `WP22-D` 的共享 ownership 区域；范围包括 `default_unit_factory.h` 与 `default_factory_legacy_spawn_compat.h`。 |
| `S-006` | `scoped pass / guard follow-up` | 保持命名 helper-system ordering guard；更广义 phase/dependency design 是后续结构工作。 |
| 共享 normative table 或相同行区间 | `串行持有 ownership` | 不允许并发 worker 拆同一张 contract table，或并行改同一段 `runtime_facade.cpp` / `default_unit_factory.h`。 |

## Fail / Pass Gate

在实现 claim 后，只要仍满足以下任一条件，就必须判失败：

- god file 被改写成“可接受 residual”，但没有落地 split 或防止继续增长的 guard；
- source pass 试图以 Noether 式 closure 结案，但 `counterfactual_replay_contracts.h`
  又回升到 `1500` 行以上，或 `runtime_window_coordinator.h` 又回升到 `1000` 行以上；
- structural split 改变了 runtime behavior，但对应行为变化并未由 `WP22-C`
  或 `WP22-D` 拥有并验证；
- raw runtime escape hatch、broad binding 或 unresolved ordering blocker 仍然 live，
  却被表述为已退场；
- `PilotWeaponRelease` 或 naval mission weapon release 漂移出命名 helper-system
  注册，或重新引入 manual query loop；
- 并发 worker 拆了同一张 normative table 或同一段 boundary range。

只有以下全部被 source-backed 证明时才可判通过：

- 至少一个高价值结构拆分在不改变行为的前提下落地；
- 剩余大型文件都有 owner、下一条 split seam，以及防止继续增长的 guard，而不是
  residual acceptance；
- maintained-vs-debug binding ownership 已明确；
- runtime-ordering exception 已被提取为显式 system/phase，或被明确记录为带 guard 的
  blocker。

## Noether Guard Register

| Gate | 当前事实 | 为什么仍阻塞 |
|------|----------|---------------|
| `G-001` | `counterfactual_replay_contracts.h = 130` 行；`counterfactual_replay_contract_validation.h = 4` 行加 validation family headers | 入口头和 validation-family split 已通过；防止 umbrella 回归。 |
| `G-002` | `runtime_window_coordinator.h = 405` 行 | 入口头阈值已通过；必须保持 helper ownership，并防止回归到 `1000` 行以上。 |
| `G-003` | `PilotWeaponRelease` 与 naval mission weapon release 都通过命名 helper systems 注册 | 保持 `simulation_kernel_systems.cpp` 不再出现 registered-in-place inline `OnUpdate` 例外，并防止 manual query-loop 回归。 |
| `G-004` | `default_factory_legacy_spawn_compat.h` 保留命名 `SpawnCompatibilityLegacyCommandSeed` seam，`default_unit_factory.h` 通过窄 helper 调用 | 这是 quarantined seed ownership，不是 typed control-state replacement。 |
| `G-005` | Maintained binding reads 使用 kernel-owned query methods；diagnostics/legacy block 仍 raw-drill | maintained raw-entity reads 在此切片已关闭，但 broad public binding count 与 debug/legacy raw ECS 仍是结构债。 |
| `G-006` | Visual-binding compatibility scene assembly 现在是 private helper code；公开 `WorldBatchRuntime::world()` 仍 live | 这收窄了一条 service seam，但没有退场 public compatibility/diagnostics escape hatch 或更广义 fat service surface。 |

## 第一轮实现快照

| 字段 | 值 |
|------|----|
| `status` | `partial` |
| `commands run` | `git diff --check` -> 通过；`find src/runtime/contracts -maxdepth 1 -name '*.h' -print0 | xargs -0 wc -l | sort -n` -> `11` 个 header，`9` 个超过 300 行；`wc -l src/runtime/facade/runtime_facade.cpp src/runtime/facade/runtime_window_coordinator.h src/models/core/default_unit_factory.h src/interfaces/python/bindings_core.cpp` -> `2809 / 1299 / 1457 / 965`；聚焦结构 guard 现已包含显式 line-threshold 与 inline-order blocker gate |
| `remaining blockers` | runtime-facade boundary mix 仍是结构债；factory spawn 与 legacy-command ownership 仍通过 `default_factory_legacy_spawn_compat.h` 耦合；公开 raw `WorldBatchRuntime::world()` 仍是 compatibility/diagnostics public surface；fat service 与 broad binding surfaces 仍 live |
| `integration notes` | 继续高价值 structural split，但 `runtime_facade.cpp` 相关工作要与 `WP22-C` 串行，`default_unit_factory.h` 相关工作要与 `WP22-D` 串行；不要把文件变小本身当成功，也不要把剩余阈值或 inline blocker 说成“residual closure” |

## Return Packet

- `status`：本次 source-verification 与 document-refresh 为 `pass`；
  structural retirement 本身仍然 mixed 且 dependency-gated。
- `touched files`：
  `docs/task/simulation_architecture/archive/wp22_legacy_compatibility_retirement/wp22_structural_god_file_decomposition_cluster_20260522.md`，
  `docs/task/simulation_architecture/archive/wp22_legacy_compatibility_retirement/wp22_structural_god_file_decomposition_cluster_20260522.zh.md`
- `commands run`：
  `git diff --check`；
  `find src/runtime/contracts -maxdepth 1 -name '*.h' -print0 | xargs -0 wc -l | sort -n`；
  `wc -l src/runtime/facade/runtime_facade.cpp src/runtime/facade/runtime_window_coordinator.h src/models/core/default_unit_factory.h src/components/command/default_factory_legacy_spawn_compat.h src/interfaces/python/bindings_core.cpp`；
  `rg -n "PilotWeaponRelease|register_pilot_weapon_release_system|query<const MissionCommand, const NavalWeaponSystem>|RuntimeFacade::runtime\\(|^\\s*\\.def\\(\"" src/interfaces/python/bindings_core.cpp src/core/engine/simulation_kernel_systems.cpp src/core/engine/simulation_kernel.cpp src/runtime/facade/runtime_facade.cpp`；
  `rg -n "^struct |^inline constexpr |validate_" src/runtime/contracts/counterfactual_replay_contracts.h`；
  `rg -n "class WorldBatchRuntime|WorldBatchRuntime::world\\(|collect_visual_binding_compatibility_scenes_batch|spawn_units_batch\\(|apply_world_setup\\(|export_|set_|get_|clear_|reset_" src/core/engine/world_batch_runtime.h src/core/engine/world_batch_runtime.cpp`；
  `rg -n "build_platform_capability_bundle_template|resolve_platform_spawn_plan|compatibility_path_preserved|legacy_command|default_factory_legacy_spawn_compat|spawn\\(" src/models/core/default_unit_factory.h src/components/command/default_factory_legacy_spawn_compat.h`
- `remaining blockers`：
  `F-002` runtime-facade boundary mix 仍 live；
  `F-004` factory spawn 与 legacy-command ownership 仍通过
  `default_factory_legacy_spawn_compat.h` 耦合；
  `S-004` 公开 raw `WorldBatchRuntime::world()` 与 fat service surface 仍 live，
  direct GPU binding raw-world access 与 visual-binding scene assembly 已退到命名 helper；
  `S-005` maintained binding reads 现在使用 kernel-owned query methods，而
  diagnostics/legacy raw ECS 与 broad binding count 仍开放；
  `S-006` helper-system ordering 现在已有 scoped pass，需保留防回归 guard。
- `integration notes`：
  `WP22-E` 现在可以立刻启动 `F-001`、`F-003`、`F-005` 与受限的 `S-005`
  quarantine 工作。
  `WP22-E` 对 `runtime_facade.cpp` 的 boundary work 必须与 `WP22-C` 串行；
  对 `default_unit_factory.h` / `default_factory_legacy_spawn_compat.h` 的 spawn
  work 必须与 `WP22-D` 串行。
  不得把 file-count reduction 本身当成成功；split 必须保持行为不变，并暴露更紧的
  ownership seam。
- `WP22-E implementation dispatch allowed?`：`yes`，但只限
  `F-001`、`F-003`、`F-005` 与受限的 `S-005` 工作。
  `F-002`、`F-004`、`S-004` 仍然 coordination-gated；`S-006` 是 guard follow-up。

## Verification Notes

- 本文档只记录 source-backed decomposition fact；本次没有进行 structural code 改动。
- 本次没有运行 `pytest`，因为任务范围是事实复核与 cluster 文档补强，而不是
  runtime behavior 改动。
- 不得把“文件很大”当成唯一问题表述。已核验债务是 mixed responsibility，加上
  live compatibility escape hatch 与 ordering exception。

## 当前结构实现快照

| 字段 | 值 |
|------|----|
| `status` | `partial`：`F-001` validation-family split、`F-003` entry-header split、`S-006` helper-system ordering、maintained binding query ownership 与 visual-binding helper extraction 已通过；更广义 structural retirement 仍开放。 |
| `commands run` | `git diff --check` -> 通过；`python3 -m pytest -q tests/architecture/platform_spawn/test_default_factory_legacy_seed_guard.py tests/architecture/structural_boundaries tests/architecture/runtime_facade -k "wp22 or bindings or world_batch_runtime or gpu_visual_binding or visual_binding_raw_world_access or escape_hatch or batch_runtime"` -> `32 passed, 16 deselected`；`cmake --build build-workshop --target ef_py -j4` 在返回的实现 packet 中通过。 |
| `remaining blockers` | `runtime_facade.cpp = 2951`；`default_unit_factory.h = 1459` 加 behavior-bearing `default_factory_legacy_spawn_compat.h`；broad binding surface 仍存在；diagnostics/legacy raw ECS 仍是 quarantine；raw `WorldBatchRuntime::world()` 仍是 public compatibility/diagnostics surface；`WorldBatchRuntime` 仍是 fat service surface。 |
| `integration notes` | 下一轮 structural dispatch 除非收紧 guard，否则应避开已拆入口头、validation-family split、helper-system ordering slice、maintained binding query seam 与 visual-binding helper。优先独立切片：runtime facade boundary split、factory/spawn typed control-state replacement、broad binding-surface reduction 或另一条 world-batch service decomposition。 |
