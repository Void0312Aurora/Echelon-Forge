# WP22-A 退场事实账本与 Kill List

状态：`2026-05-22` WP21 owner-rejected；source-backed ledger 已更新。最新
implementation wave 已对四个限定切片完成本地验收：`RTE-003` raw-loader seam
收窄到两个 production 锚点，`RTE-007` setup/type/schema ownership 通过聚焦验证，
`A-001` maintained typed setup promotion、`F-001` validation-family split 与 `F-003`
入口头拆分通过聚焦 guard。WP22 仍开放，因为 runtime/facade compatibility escape
hatches、default-factory typed control-state replacement、aggregate DTO shells、
fat world-batch/binding surfaces 与更广义 structural blockers 仍然 live。最新
implementation round 还已完成 direct GPU visual-binding raw-world quarantine 与
default-factory legacy seed helper extraction 两个 scoped pass。最新 guard wave
又验收了 DTO transport-shell marking、`bindings_core.cpp`
maintained/diagnostics/legacy registration separation，以及 repo 级
`batch_runtime` consumer guard hardening。第八轮关闭了 maintained binding
raw-entity seam，并验收了 private visual-binding service extraction。第九轮又获得
`WorldBatchRuntime` setup orchestration split 的 scoped pass，并获得 typed
command-control replacement inventory 的只读 pass。该 inventory 识别出
`MissionCommandControlState` 是下一条最小 typed seam。Meitner 已返回
`partial / interrupted / unvalidated` implementation packet；主线程修复了其中
`CommandLag` target-overwrite 风险，并重跑 focused guards/build。第十轮随后关闭了
剩余 typed ingress/link sync blocker，并收紧了对应 guard。default-factory typed seed
工作仍为 `partial`，因为 `MovementCommand` / `LaggedCommand` projection 仍是
compatibility mirror，而不是已退场 ownership。WP22 仍开放，因为这不是
compatibility surface 的删除。

Closure note：

- Lagrange、Laplace 与 Raman 返回了可用 findings，可作为本 ledger 初始依据。
- Python source-pass subagent 超时并被关闭，没有完整 return packet。
- Turing 重新派发并完成了有边界的 `WP22-B0` 只读 Python verification，返回
  `status: blocked`、`touched files: none` 的完整 packet。
- 因此 Python source-pass 缺口不再是 missing evidence，而是 source-verified
  blocker。`WP22-B` 现在已经完成维护中业务退场，而 `command_chain_cache`
  里的 import-time `ef_py.TaskOrder` 后续只是一条 C/F guard lane 的
  validation-only follow-up，不是 blocker。

下一批事实核验与文档补强任务已通过 WP22 队列派发，并且已经返回 packet。Zeno
与 Arendt 为 pass，Tesla 对有边界的 `RTE-003` runtime 切片返回 partial。后续
implementation wave 又返回四个限定 `pass` packet，但它们只在各自切片内验收。
这是进展证据，不是 closure evidence。

最新 scoped-pass 同步：

- `Singer` 被接纳为 operation/command-link mirror dependency reduction 切片的 scoped `pass`。主线程重新验证了 `architecture WP9/WP22/DTO` focused guards、`runtime/naval` focused tests、`ef_py` build 与 `git diff --check`，并在 link args 前通过 `-x none` 修复了 `tests/architecture/test_wp9_guard_enforcement.py::_compile_and_run`。
- `Nietzsche` 被接纳为 naval maintained DTO consumer migration 切片的 scoped `pass`。同样的主线程验证通过，同时保留了 `command_code` compatibility fallback。
- 这些都只是 scoped pass，不改变 `WP22 overall` 仍然开放，也不让 `WP22-F` 获得资格。

第二轮刷新：

- `WP22-B` 现在 pass，因为 `common_core_profile` 与 `loading.py` 已被收为
  compatibility-only guard surfaces，raw sim seam 也已转入 C/F compatibility
  guard ownership；剩余的 `ef_py.TaskOrder` 仅是 validation-only follow-up。
- `WP22-D` 现在 pass，因为 legacy command consumers 已迁移或隔离到
  bridge，只剩 specific bridge/default-factory seam 在 allowlist 内。
- WP22-specific tests 已通过，且 aggregate sweep 在 WP16/WP20 drift cleanup
  后已通过，所以第三轮后续同步处于 active 状态。

## Corrected Audit Facts

| 审计区域 | 修正后的事实 | 证据锚点 | 含义 |
|----------|--------------|----------|------|
| `F-005` contract-header 计数 | Runtime contract headers 总数为 `11`，其中 `9/11` 超过 300 行，不是 “7 of 9”。这 `9` 个大头文件里有 `8` 个同时混合 constants、DTO 与 inline helper/validation 职责。 | `src/runtime/contracts/backend_profile_contracts.h:11`; `src/runtime/contracts/counterfactual_replay_contracts.h:16`; `src/runtime/contracts/world_batch_contracts.h:47` | 后续 split 规划必须使用修正后的计数与 mixed-responsibility 表述。 |
| `L-001` legacy command consumers | “`legacy_command.h` 有 11 个 active consumers” 的说法不精确。直接 system include 为 `10` 个，计入 bridge/间接 use 后至少有 `12` 个 maintained users。`control_input_resolution.h` 只是 partial bridge；`propulsion_system.h` 仍保留 legacy throttle fallback。 | `src/components/command/legacy_command.h:6`; `src/systems/core/operation_system.h:34`; `src/systems/physics/propulsion_system.h:38`; `src/systems/systems/command_link_system.h:20`; `src/components/command/air/control_input_resolution.h:13`; `src/systems/physics/ground_contact_system.h:178`; `src/systems/physics/propulsion_system.h:44` | `WP22-D` 必须把 legacy command retirement 当成活跃 maintained-path 迁移处理。 |
| `L-002` raw escape hatch 表述 | “default path” 的说法过重。`RuntimeFacade.runtime()` 已不是 maintained 默认主 API，但 raw escape 仍活着；`RuntimeFacadeAdapter` 仍缓存 raw runtime，`WorldBatchRuntime::world()` 也仍公开暴露。原 direct GPU binding raw-world residual 现在已通过 `WorldBatchRuntime::collect_visual_binding_compatibility_scenes_batch(...)` 收窄。 | `python/rl/runtime/world_batch/adapter.py:49`; `tests/architecture/test_runtime_facade_layering.py:379`; `src/runtime/facade/runtime_facade.cpp:2498`; `src/core/engine/world_batch_runtime.h:65`; `src/core/engine/world_batch_runtime.cpp:337`; `src/interfaces/python/bindings_gpu.cpp:520`; `src/core/engine/world_batch_runtime.cpp:1105`; `src/runtime/facade/runtime_facade.cpp:592` | `WP22-C` 应将公开 raw access 归类为 `quarantine`，而不是“已退场”；direct GPU binding raw-world use 是 scoped pass。 |
| `A-003` WP21 gated 表述 | WP21 接受的 typed/setup 与 facade 进展本身不等于 legacy setup/runtime surface 已退场。WP22 后续已在 `RuntimeFacade.apply_world_setup` 中提升 maintained typed setup，但显式 legacy compatibility setup、`legacy` runtime mode 与 raw escape hatches 仍是 quarantined surfaces。 | `src/runtime/facade/runtime_facade.cpp`; `src/core/engine/world_batch_runtime.cpp`; `python/env_config.py`; `python/rl/runtime/world_batch/adapter.py` | 保持 maintained typed setup pass 与剩余 compatibility/diagnostics residual 的区分。 |
| `S-004` world-batch 体量 | `WorldBatchRuntime` 的 public methods 实数为 `41`，不是 `36`，至少横跨七类职责，并且仍公开 `world()`。 | `src/core/engine/world_batch_runtime.h:15`; `src/core/engine/world_batch_runtime.h:30`; `src/core/engine/world_batch_runtime.h:45`; `src/core/engine/world_batch_runtime.cpp:526`; `src/core/engine/world_batch_runtime.cpp:703`; `src/core/engine/world_batch_runtime.cpp:817` | `WP22-E` 应按 service seam 分拆，而不是接受 fat runtime shell。 |
| `S-005` Python binding 定性 | `bindings_core.cpp` 在 `431-956` 区间实际暴露 `75` 个 `.def`，不是 “55+”；多个 lambda 仍直接深入 `self.get_world().entity(...)`。Direct GPU visual batching 已不再从 `bindings_gpu.cpp` 直接调用 `.world(`，所以剩余 binding debt 是 broad maintained/debug surface mix，而不是该 direct residual。 | `src/interfaces/python/bindings_core.cpp:431`; `src/interfaces/python/bindings_core.cpp:433`; `src/interfaces/python/bindings_core.cpp:708`; `src/interfaces/python/bindings_core.cpp:949`; `src/interfaces/python/bindings_gpu.cpp:520` | `WP22-E` 应把 direct-kernel bindings 收口到显式 debug/diagnostics allowlist，并保持 GPU direct raw-world guard。 |
| `S-006` inline-system 表述 | 已被后续 implementation packets 覆盖：`PilotWeaponRelease` 与 naval mission weapon release 现在都通过命名 helper systems 注册，manual naval post-step query loop 已不存在。 | `src/core/engine/simulation_kernel_systems.cpp`; `src/systems/combat/pilot_weapon_release_system.h`; `src/systems/naval/naval_mission_weapon_release_system.h`; `src/core/engine/simulation_kernel.cpp` | `WP22-E` 应保持 helper-system ordering guards，并把更广义 phase/dependency design 视为后续结构债。 |

## Kill List

| ID | Surface | 状态 | Retirement | Owner | Replacement | Guard / validation |
|----|---------|------|------------|-------|-------------|--------------------|
| `RTE-001` | `RuntimeFacade.runtime()` raw escape hatch | 已非 mainline default，但仍是存活的 compatibility/diagnostics surface；adapter 仍缓存 raw runtime。 | `quarantine` | `WP22-C` | Facade APIs、`run_wp10_window()`、adapter batch methods | 禁止 allowlist 外新增 maintained `.runtime()` caller。`python -m pytest -q tests/architecture/test_runtime_facade_layering.py -k "runtime_facade_runtime_consumers or leader_world_batch_runtime_does_not_call_runtime_facade_runtime"` |
| `RTE-002` | `vec_env.batch_runtime` public compatibility view | 仍公开暴露，并受测试保护。 | `quarantine` | `WP22-C` | `runtime_facade`、`RuntimeFacadeAdapter`、显式 vec-env accessor | 禁止新增生产代码 `.batch_runtime.` 消费者。`python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k batch_runtime && python -m pytest -q tests/architecture/test_runtime_facade_layering.py -k batch_runtime` |
| `RTE-003` | runtime wrappers 中的 `loader.sim` | `gym_envs` 与 `python/rl` 的 production `loader.sim.*` / `loader.sim,` usage 现在为空；剩余出现是显式 test/guard 字符串。 | `pass for production raw-loader cleanup` | `WP22-C` / C/F guard lane | 命名 loader-backed compatibility seam、typed mission-command helpers、facade/bridge-owned setters | `rg -n "loader\\.sim\\.|loader\\.sim," gym_envs python/rl -S` -> no matches |
| `RTE-004` | `execution_step_runtime_mode="legacy"` | 非默认值；只有设置 `runtime_compatibility_enabled=True` 时才是 quarantined compatibility opt-in。 | `quarantine / explicit opt-in` | `WP22-C` | Maintained path 固定 `compiled`；`legacy` 仅允许显式 compat opt-in | `python -m pytest -q tests/runtime/core/test_env_config.py -k runtime_mode && python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "execution_step_runtime_mode or runtime_compatibility"` |
| `RTE-005` | `CMO_EXECUTION_STEP_RUNTIME` / `set_execution_step_runtime_mode(None)` | silent global legacy selection 已移除；`None` 解析为 `compiled`，loader init 显式设置 `compiled`，env/None-setter 扫描为空。 | `pass for silent-selection removal` | `WP22-C` | 仅显式 parameter/fixture；无 env-silent runtime selection | `rg -n "CMO_EXECUTION_STEP_RUNTIME|set_execution_step_runtime_mode\\(None\\)" gym_envs python tests -S` -> no matches |
| `RTE-006` | `compatibility_fallback_world_batch_step_worlds_wp16c` | 非默认 fallback 仅作为命名 compatibility cadence path 保留，并被测试守住。 | `quarantine / explicit fallback` | `WP22-C` | `RuntimeFacade.run_wp10_window()` maintained path；fallback 只保留为 opt-in/diagnostic | `python -m pytest -q tests/world_batch/test_single_world_batch_runtime.py -k compatibility_fallback` |
| `RTE-007` | `terrain_type` 非 legacy 默认值 | terrain source、compiler metadata、runtime apply、facade setup 与 world-batch setup 现在共享显式非 legacy 默认 ownership。missing/blank terrain 解析为带 `default_mainline` 来源的 `flat`；显式 legacy terrain 是命名 compatibility。 | `pass for setup/type/schema slice` | `WP22-C`，依赖 `WP22-D` | 显式 schema 值或同步后的非 legacy 默认 enum | `cmake --build build-workshop --target ef_py -j4 && bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "terrain or world_setup or setup"` |
| `PY-001` | `leader_tasking.py` 硬编码 `_air_profile.build_kernel_mission_command(loader)` | maintained path 已退场；`leader_tasking` 现在通过 bridge 构建 kernel mission-command。 | `pass for maintained-business scope` | `WP22-B` | `tasking_bridge.build_kernel_mission_command(loader)` | `python -m pytest -q tests/architecture/test_wp22_tasking_bridge_retirement.py -k kernel_dispatch` |
| `PY-002` | `leader_tasking.py` 直接写 `loader.sim.*` | maintained tasking raw writes 已退场；raw synchronization 集中到 `LoaderOwnedRawSimCompatibilityFacade`，production `loader.sim` 扫描为空。 | `pass for maintained-business scope` | `WP22-B`，受 `WP22-C` guard ownership 管理 | facade/tasking-bridge setters 与命名 compatibility seam | `rg -n "loader\\.sim\\." python/rl/tasking python/rl/runtime gym_envs -S` -> no matches |
| `PY-003` | 通过 `get_agent_observation()` 读取 raw truth | maintained policy reads 现在通过 loader-owned policy observation/instrument seams，而不是 direct raw truth helpers。 | `pass for maintained-business scope` | `WP22-B`，与 `WP22-C` 协调 | observation/information-state facade / loader-owned policy seams | `python -m pytest -q tests/architecture/test_wp22_tasking_bridge_retirement.py -k policy_state_reads` |
| `PY-004` | 原始 `loader.mission_cmd` dict patterns | maintained tasking/runtime-state consumers 使用 typed mission-command helpers 与 views；raw `mission_cmd` dict 作为 scenario-loader compatibility payload 保留，而不是 tasking bypass。 | `pass for maintained-business scope / compatibility payload remains` | `WP22-B`，共享 loader/runtime-state 协调 | typed `MissionCommand` adapter / DTO | `python -m pytest -q tests/architecture/test_wp22_tasking_bridge_retirement.py -k typed_mission_command_helpers` |
| `PY-005` | `common_core_profile.py` air/default coupling 与 `ef_py` injection | air-only default/profile helpers 已从 maintained common-core layer 退场；production `ef_py =` monkey-patching 被 guard 禁止。 | `pass for maintained-business scope` | `WP22-B` | bridge-owned profile dispatch and import boundary | `python -m pytest -q tests/architecture/test_wp22_tasking_bridge_retirement.py -k common_core_profile` |
| `L-001` | `legacy_command.h` 与 `MovementCommand` / `ActionCommand` / `LaggedCommand` | 仍是 maintained C++ 主路径；审计 consumer 计数偏低。 | `migrate` | `WP22-D` | `PilotAction`、`MissionCommand`、单一 command-resolution bridge | `rg -n "legacy_command\\.h|MovementCommand|ActionCommand|LaggedCommand" src/systems src/components tests` |
| `L-001a` | `control_input_resolution.h` partial bridge | 集中了一部分 fallback，但不是唯一入口。 | `quarantine` | `WP22-D` | 单一 bridge-owned compatibility shim | `rg -n "active_legacy_movement_command|resolved_pilot_or_legacy_throttle|resolve_pilot_or_legacy_ground_control" src tests` |
| `L-001b` | spawn-time 播种 legacy command state | Aircraft spawn legacy command seeding 已隔离到 `default_factory_legacy_spawn_compat.h`；`default_unit_factory.h` 调用命名 helper，且已不再 direct include `legacy_command.h`。helper 现在也 seed `MissionCommandControlState`，但仍 materialize `MovementCommand` / `LaggedCommand` 作为 compatibility mirrors。 | `partial / guarded quarantine` | `WP22-D` | neutral `PilotAction` 加 typed control-state seed；legacy DTO 必须保持 mirror-only，或在安全时删除。 | `python -m pytest -q tests/architecture/test_wp22_default_factory_legacy_seed_guard.py tests/architecture/test_wp9_guard_enforcement.py -k "legacy_command or default_factory or command"` |
| `A-001` | `WorldSpawnRequest.type_name` / `spawn_unit(type_name)` maintained typed setup blocker | Maintained typed setup 现在消费 maintained validator，并通过 batch-owned typed helper materialize，不再重建 `WorldSpawnRequest`；显式 legacy compatibility setup 仍命名分离。 | `pass for maintained typed setup / compatibility branch remains` | `WP22-D`，与 `WP22-C` 协调 | 保持 `typed_platform_spawn_requests` 一线化，并保留显式 legacy compatibility path 分离。 | `python -m pytest -q tests/architecture/test_wp20_runtime_setup_consume_bridge.py tests/architecture/test_wp14_boundary_guards.py tests/runtime/facade/test_runtime_facade.py -k "typed_platform_spawn or world_setup or setup"` |
| `S-001` | flat aggregate DTO shells | `MissionCommand`、`TaskOrder`、`LeaderIntent` 与 `PilotReport` 仍存在，但现在明确标成 compatibility transport shell，并带 owner-slice projection helper；world-batch assignment wrapper 也被 guard 为 transport-only。这是 guard/quarantine，不是 retirement。 | `migrate / guarded quarantine` | `WP22-D`，协调 `WP22-E` | maintained code 消费的 domain/lifecycle-specific slices 或 variant DTOs | `python -m pytest -q tests/architecture/test_wp22_dto_domain_shell_guard.py && rg -n "struct .*: .*Air, .*Naval|World(MissionCommand|TaskOrder|LeaderIntent|PilotReport)Assignment|get_.*_batch|set_.*_batch" src tests` |
| `S-002` | air recovery/takeoff 重复 | 字段在三个 DTO 阶段重复出现。 | `migrate` | `WP22-D` | 共享 air slice 加 bridge-owned projection rules | `rg -n "recovery_base_id|recovery_runway_id|recovery_approach_type|takeoff_procedure_id|takeoff_clearance_id|takeoff_interval_s|runway_slot_id|formation_" src/components/command src/components/tasking tests` |
| `S-003` | naval DTO 不对称 | 不对称 lifecycle split 仍经 aggregate DTO 流通。 | `migrate` | `WP22-D` | 显式 naval-stage DTO 与 projection rules | `rg -n "MissionCommandNaval|TaskOrderNaval|LeaderIntentNaval|PilotReportNaval|warfare_role_code|officer_in_tactical_command|reference_entity_id|launch_helo|recover_helo" src/components tests` |
| `F-001` | `counterfactual_replay_contracts.h` | 入口头现在是 130 行 umbrella，原 1643 行 validation follow-up 已拆成 4 行 validation umbrella，加 replay/counterfactual/experiment/helper validation family headers。 | `pass for validation-family split` | `WP22-E` | 保持 validation family ownership 显式，并防止 umbrella 回归。 | `wc -l src/runtime/contracts/counterfactual_replay_contracts.h src/runtime/contracts/counterfactual_replay_contract_validation.h src/runtime/contracts/counterfactual_replay_*validation*.h` |
| `F-002` | `runtime_facade.cpp` | 大型 mixed TU 仍混合 spawn/counterfactual/export/window 与 compatibility surfaces；最新本地行数为 `2951`。 | `migrate` | `WP22-E`，依赖 `WP22-C` | 拆成 core/spawn/counterfactual/export/window 文件 | `wc -l src/runtime/facade/runtime_facade.cpp && rg -n 'RuntimeFacade::runtime\\(|using namespace runtime::counterfactual|run_counterfactual|run_wp10_window|export_engagement_event_packet' src/runtime/facade/runtime_facade.cpp` |
| `F-003` | `runtime_window_coordinator.h` | 入口头现在是 405 行，并把 selection/callback/cadence/execution helpers 委托到命名 companion headers。 | `migrate / pass for entry-header slice` | `WP22-E` | 保持 helper ownership 显式，并防止回归超过阈值。 | `wc -l src/runtime/facade/runtime_window_coordinator.h src/runtime/facade/runtime_window_coordinator_*.h` |
| `F-004` | `default_unit_factory.h` / `default_factory_legacy_spawn_compat.h` | 仍是 large mixed factory header。Spawn 现在先 seed typed `MissionCommand` shell，再投影剩余 compatibility seed，但 `default_factory_legacy_spawn_compat.h` 仍 include `legacy_command.h`，并持有 behavior-bearing `MovementCommand` / `LaggedCommand` projection。 | `partial / typed-seed reduction` | `WP22-E`，依赖 `WP22-D` | 在声称退场前，必须用 typed command-control state 替换 `MovementCommand` / `LaggedCommand` projection。 | `wc -l src/models/core/default_unit_factory.h src/components/command/default_factory_legacy_spawn_compat.h && python -m pytest -q tests/architecture/test_wp22_default_factory_legacy_seed_guard.py` |
| `F-005` | 大型 mixed runtime contract headers | `9/11` large headers 承载 mixed responsibilities。 | `migrate` | `WP22-E`，依赖 `WP22-C/D` | `*_constants.h`、`*_types.h`、`*_validation.cpp` | `find src/runtime/contracts -maxdepth 1 -name '*.h' -print0 | xargs -0 wc -l | sort -n` |
| `L-002` | `RuntimeFacade.runtime()` / `WorldBatchRuntime::world()` raw access | Maintained facade internals 已不再通过 public raw accessors 下钻；`runtime()` / `world()` 仅保留为显式 compatibility/diagnostics escape hatches。 | `pass for maintained facade internals / quarantine remains` | `WP22-C` | facade-owned 窄方法；raw access 仅 opt-in 保留 | `python -m pytest -q tests/architecture/test_runtime_facade_layering.py -k "runtime_facade_cpp_maintained_paths_do_not_drill_through_raw_runtime_or_world"` |
| `A-002` | 依赖 registration order 与手工循环的隐式 ECS 顺序 | `PilotWeaponRelease` 与 naval mission weapon release 现在都通过命名 helper systems 注册；manual post-`step()` naval query loop 已消失。 | `pass for naval fire-loop seam` | `WP22-E`，依赖 `WP22-D` | 保持 helper-system ordering guards；更广义 phase/dependency work 是后续 structural debt。 | `python -m pytest -q tests/architecture/test_wp22_structural_guardrails.py tests/runtime/naval -k "weapon or mission or fire"` |
| `S-004` | `WorldBatchRuntime` fat surface | `41` 个 public methods，至少七类职责。Visual-binding compatibility scene assembly 已抽到 private helper，但 public raw `world()` 与更广义 setup/command/episode/query 职责仍存在。 | `migrate / scoped service split pass` | `WP22-E`，依赖 `WP22-C` | 继续抽取 setup/command/episode/query services，且不得改变 public raw-world compatibility semantics。 | `python -m pytest -q tests/architecture/test_runtime_facade_layering.py -k "world_batch_runtime or gpu_visual_binding or visual_binding_raw_world_access or escape_hatch"` |
| `S-005` | 大块 `SimulationKernel` Python bindings | `75` 个 direct `.def` binding 仍存在。`bindings_core.cpp` registration 已按 role 拆分，maintained binding entity reads 现在使用 kernel-owned query methods，不再本地 raw ECS lookup。Diagnostics 与 legacy block 仍有意 raw-drill。 | `quarantine / maintained seam pass` | `WP22-E`，依赖 `WP22-C` | 继续减少 broad public binding surface，或把 maintained API 迁向 facade/kernel-owned methods，同时保持 debug/legacy quarantine。 | `python -m pytest -q tests/architecture/test_wp22_structural_guardrails.py -k "bindings"` |
| `S-006` | 内联 `PilotWeaponRelease` `OnUpdate` 例外 | 该 inline 例外已在本切片退场；registration 现在委托给 `register_pilot_weapon_release_system(ecs, *this)`。 | `pass for ordering residual slice` | `WP22-E`，如 fire-control contract 改动则可能依赖 `WP22-D` | 独立 combat helper system 加防回归 guard | `rg -n 'PilotWeaponRelease|register_pilot_weapon_release_system' src/core/engine/simulation_kernel_systems.cpp src/systems` |

## 第一轮实现结果

| Stream | 本地结果 | 证据摘要 | 含义 |
|--------|----------|----------|------|
| `WP22-B` | `historical blocked, superseded by later pass` | 早期 `leader_tasking` 路径受 raw truth/instrument replacement 阻塞。后续 WP22-B packets 已退场 maintained-business path，并把 raw-loader ownership 转入 C/F guard lane。 | 该历史 blocker 只作 provenance；不得重新打开 maintained-business blocker 语义。 |
| `WP22-C` | `historical partial, superseded for RTE-003/RTE-005/RTE-007` | 早期 runtime opt-in/quarantine 测试已通过，但 raw-loader seam 与 setup ownership 仍开放。Russell、Bernoulli 与 Hubble 后续关闭了 production raw-loader cleanup、silent-selection removal 与 setup/type/schema ownership。 | 当前 C lane 是 `L-002` raw facade/world access，加 explicit compatibility surfaces 的 guard follow-up。 |
| `WP22-D` | `historical blocked, superseded by later passes for command bridge and A-001` | air-control bridge 早期落地时仍有 broader consumers。后续 guard work 已把 legacy command consumers 迁移或隔离到 bridge/default-factory seams，并且 A-001 已提升 maintained typed setup。 | 剩余 D work 是 default-factory typed control-state replacement 与 aggregate DTO/domain shell 退场，不是旧 direct-sim 或 A-001 blocker。 |
| `WP22-E` | `historical partial, superseded for entry-header and PilotWeaponRelease slices` | constants/helper split 与 structural guard 已落地；Carver/Noether/Parfit 后续关闭了 entry-header 与 inline weapon-release 切片。 | structural decomposition 后续聚焦 validation split、runtime facade TU、broad bindings、default factory 与 naval fire-loop ordering。 |
| `WP22-F` | `pending` | 暂无 closure evidence；只能消费锁定后的 B-E 证据集。 | 串行 closure 继续后置。 |

## Parallel Readiness

| Stream / item set | Readiness | 规则 |
|-------------------|-----------|------|
| `WP22-C`: `RTE-001`, `RTE-002`, `RTE-004`, `RTE-005`, `RTE-006` | `ready` | 基于已核 runtime 证据，可立即启动 quarantine/guard 工作。 |
| `WP22-D`: `L-001`, `L-001a`, `L-001b`, `S-001`, `S-002`, `S-003` | `ready with coordination` | 可开工，但 public boundary flip 必须与 `WP22-C` 和 structural 后续协调。 |
| `WP22-E`: `F-001`, `F-003`, `F-005`, `S-005`, `S-006` | `ready with guard discipline` | Structural split/quarantine 可开工，但不得漂移 public boundary ownership。 |
| `WP22-B`: `PY-001` 到 `PY-005` | `source-verified retired for maintained-business scope` | `WP22-B` 现在对维护中业务退场为 `pass`；`command_chain_cache` 中的 import-time `ef_py.TaskOrder` 只是一条 C/F guard lane 的 validation-only follow-up。 |
| `RTE-003` | `pass for production raw-loader cleanup` | Production `loader.sim.*` / `loader.sim,` scan 现在为空；只剩显式 test/guard 字符串。 |
| `RTE-007` | `pass for setup/type/schema slice` | source、重建 binding verification、facade setup、world-batch setup、compiler metadata 与 runtime apply 现在对齐到非 legacy 默认 ownership。 |
| `A-001` | `scoped pass` | maintained facade execution 现在消费 maintained typed setup validator 与 batch-owned typed spawn helper；显式 compatibility branch 仍分离。 |
| `F-002` | `dependency-gated` | 不能与 `WP22-C` 在 `runtime_facade.cpp` 的 public/raw-access 行区间对撞。 |
| `F-004` | `partial / seed seam pass` | legacy command seed ownership 已隔离；更广义 factory split 仍是 structural debt。 |
| `L-002` | `scoped pass / quarantine remains` | maintained facade internals 与 direct GPU binding raw-world access 已不再通过 public raw world access 下钻；公开 `runtime()` / `world()` escape hatches 仍只可作为 compatibility/diagnostics。 |
| `A-002` | `scoped pass` | naval post-step fire loop 已退场为命名 helper system；更广义 execution-phase design 是后续 structural debt。 |
| `S-004` | `dependency-gated` | World-batch service split 依赖 `WP22-C` 先划清 maintained facade/query boundary。 |

## 第七轮核验

| Stream | 状态 | 证据摘要 | 含义 |
|--------|------|----------|------|
| `Pauli` | `pass` | Aggregate command/tasking DTO 与 world-batch assignment wrapper 现在明确标成 compatibility transport shell，并带 owner-slice projection helper；DTO/shell 聚焦 guard 与 `ef_py` build 通过。 | `S-001` 已 guard，但未 retired；下一步必须把 maintained consumer 迁往 owner slice 或 domain-specific DTO。 |
| `Ramanujan` | `pass` | `bindings_core.cpp` registration 已按 maintained/diagnostics/legacy role 拆分，architecture guard 确保 maintained/override helper block 不再直接书写 `self.get_world().entity(...)`；binding 聚焦 guard 与 `ef_py` build 通过。 | `S-005` 隔离更清楚，但仍过宽；下一步应减少 maintained raw-entity seam，或迁到 kernel-owned query method。 |
| `Beauvoir` | `preflight-only` | repo 级 non-test Python `batch_runtime` consumer guard 现在会扫描 explicit compatibility/diagnostics allowlist 外的使用；文档与 audit summary 保持 `WP22-F` not eligible，acceptance reviews 为 `0`。 | guard hardening 不等于 public escape hatch 退场；`WP22-F` 仍 blocked。 |

## 第八轮核验

| Stream | 状态 | 证据摘要 | 含义 |
|--------|------|----------|------|
| `Harvey` | `partial` | Default-factory spawn 现在 seed typed `MissionCommand` shell，并从 `MissionCommandCore` 投影 compatibility commands；聚焦 guards、mission/naval tests 与 `ef_py` build 通过。 | `F-004/L-001b` 仍受 behavior-bearing `MovementCommand` / `LaggedCommand` projection 阻塞。下一步必须 inventory 并替换 typed control path。 |
| `Banach` | `pass` | Maintained binding reads 已迁到 kernel-owned query methods；`bindings_core.cpp` 本地 `lookup_entity(...)` 已移除；binding 聚焦 guard 与 `ef_py` build 通过。 | `S-005` maintained raw-entity seam 在本切片关闭；broad binding count 与 diagnostics/legacy raw ECS 仍开放。 |
| `Planck` | `pass` | Visual-binding compatibility scene assembly 已迁到 private helper；runtime facade layering guards 与 `ef_py` build 通过。 | `S-004` 已抽取一条 service seam，但 `WorldBatchRuntime` 仍 fat，public raw `world()` 仍 quarantine。 |

## 第九轮核验

| Stream | 状态 | 证据摘要 | 含义 |
|--------|------|----------|------|
| `Maxwell` | `pass` | 新增 `src/core/engine/world_batch_setup_helper.h`；`WorldBatchRuntime::apply_world_setup_batch` 的 setup orchestration、terrain/wind/zone/reset seed resolution 现在经由 private helper 运行。 | `S-004` 再次收窄了一条 service seam，但 public `WorldBatchRuntime::world()` 仍是 compatibility/diagnostics escape hatch，`WP22-F` 仍不 eligible。 |
| `Hooke typed-control inventory` | `pass / read-only` | 未编辑文件。Inventory 确认 `default_factory_legacy_spawn_compat.h`、`operation_system.h` 与 `control_system.h` 是最小第一实现 seam，并建议在 `MissionCommandCore` 旁增加 `MissionCommandControlState`。 | 可作为 Meitner implementation dispatch 的输入，但本身不退场 `MovementCommand` / `LaggedCommand`。 |
| `Poincare docs cleanup` | `partial / no edits` | discovery 后停止；packet 未运行 audit 或 diff-check。 | 最小 queue/ledger sync 由主线程接管；无 closure evidence。 |
| `Meitner typed-control implementation` | `partial / main-thread repaired` | worker 在新增 `MissionCommandControlState` 并让 operation/control/default-control 朝 typed state 接入后停止，未自行验证。主线程修复 `CommandLag` lagged 初始化覆盖新 target 的问题，并重跑 architecture guards `21 passed`、mission/naval/link tests `18 passed`、`ef_py` build 与 `git diff --check`。 | 该切片本身不是 retirement；它暴露了第十轮消费的 ingress/link 缺口。 |
| `Descartes typed-control fact verification` | `partial / read-only` | 未编辑文件。核验确认 typed state 仍是 source-of-truth island，并识别出 command ingress/link 与 default-factory compatibility projection 仍是 blocker。 | 只读 blocker evidence，不是 closure。 |
| `Averroes typed ingress/link sync` | `pass` | non-ship immediate `set_unit_command` 与 deferred `CommandLinkMovement` 现在先更新 `MissionCommandControlState`，再刷新 legacy mirrors；stick command 被命名为 quarantined legacy-only DTO write。主线程复验：`ef_py` build passed，runtime mission/naval/link suite `19 passed`，`git diff --check` clean。 | `PendingMovementCommand`、legacy movement debug、stick DTO compatibility、`ActionCommand` / `PendingActionCommand`、下游 mirror consumers 与 default-factory compatibility projection 仍开放。 |
| `Parfit typed-control guard hardening` | `pass` | architecture guards 现在锚定 default-factory helper 为 compatibility-only 且必须 seed typed state，要求 command ingress 使用 bridge helpers，并 guard bridge typed-state mirror helpers。主线程复验：default-factory/WP9/structural suite `21 passed`，`git diff --check` clean。 | Guard hardening 不是 closure；它只在剩余 compatibility seams 迁移期间防回归。 |
| `Copernicus forced-retirement fact check` | `partial / read-only` | 未编辑文件。确认 `WP22-F eligibility = no`，并重新锚定 live legacy movement mirrors、pending command transport shells、debug legacy movement hooks 与 default-factory projection。 | 只读 blocker evidence，不是 closure。 |
| `Gauss default-factory typed control-state ownership` | `pass` | spawn default ownership 现在明确为 `MissionCommandControlState`；legacy movement/lagged mirrors 在 apply 时投影，不再作为 seed struct state 保存。主线程与 Dalton patch 集成后复验：`ef_py` build passed，architecture suite `21 passed`，runtime mission/naval/link suite `19 passed`，`git diff --check` clean。 | 只是 scoped semantic narrowing；下游 consumer 仍需要 mirrors，因此 mirrors 仍 live。 |
| `Dalton command mirror consumer migration` | `partial` | `control_input_resolution.h` 与 `force_system.h` 朝 state-first consumer resolution 迁移；主线程复验后 patch 可本地构建，并通过 focused architecture/runtime gates。 | `propulsion_system.h`、`instrument_system.h` 与 `ground_contact_system.h` 仍缺 typed throttle/brake 语义；embarked-air、debug/pending transport、operation/link mirrors 仍开放。 |
| `Boole debug/pending transport narrowing` | `pass` | debug legacy movement setter 现在通过 bridge helpers 同步，legacy/pending getters 标记为 diagnostics mirror 或 diagnostics transport shell。主线程复验通过 runtime/architecture/build/diff gates。 | debug 与 pending surfaces 仍以 diagnostics/transport shell 存在；不是删除。 |
| `Hume embarked-air state-first write-chain` | `pass` | launch/recover 写入不再依赖预先存在的 `MovementCommand*`；bridge helpers 会按需 materialize typed state 与 mirrors。主线程复验通过 runtime/architecture/build/diff gates。 | 剩余 command-control blockers 在 embarked-air 之外：command-link、operation、default-factory projection 与 DTO/runtime surfaces。 |
| `Curie air-control typed resolver` | `partial / main-thread repaired` | Curie 留下 instrument 与 ground-contact 继续走 raw source-pointer branches；主线程把 physics consumers 接到 bridge 输出的 `ResolvedAirControlInput`。主线程复验：architecture suite `23 passed`，runtime suite `20 passed`，`ef_py` build passed，`git diff --check` clean。 | throttle/brake 仍是 bridge 内 compatibility fallback，因为 `MissionCommandControlState` 没有 throttle/brake owner。这是 scoped narrowing，不是完整 command retirement。 |
| `Bohr operation-system mirror quarantine` | `pass` | operation 本地 legacy seed/refresh helpers 已迁到 bridge-owned helpers；主线程复验通过 architecture、mission runtime、build 与 diff-check。 | operation system signatures 仍带 legacy mirror components；不是删除。 |
| `Schrodinger default-factory projection fact check` | `blocked / read-only` | 未编辑文件。确认 spawn-time `MovementCommand` / `LaggedCommand` projection 现在还不能删除。 | 阻塞 consumer 仍在 air-control bridge fallback、operation mirrors、command-link delivery 与 movement readers。 |

本地验证：runtime facade layering focused guard `10 passed, 26 deselected`；world_batch setup focused tests `3 passed, 21 deselected`；`cmake --build build-workshop --target ef_py -j4` 通过；`git diff --check` clean。

## Blockers

| ID | 阻塞面 | 为什么阻塞 | 所需下一步 |
|----|--------|------------|------------|
| `PY-B0-001` | Source-verified Python bypass set | `WP22-B0` 返回 `status: blocked`、`touched files: none`；`PY-001` 至 `PY-005` 五个 kill-list items 在 source-pass 时全部 live，但 `WP22-B` 已经完成维护中业务退场。 | 剩余的 import-time `ef_py.TaskOrder` 后续只受 C/F guard lane 管理；不得重新写回维护中业务 blocker 语义。 |

## 第二轮结果

| Stream | 本地结果 | 证据摘要 | 含义 |
|--------|----------|----------|------|
| `WP22-B` | `pass` | policy-read seam 已落地，`common_core_profile` 与 `loading.py` 现在都是 compatibility-only guard surfaces，raw sim seam 则已转入 C/F compatibility guard ownership。WP22-specific tests 已通过。 | 维护中业务退场已完成；剩余的 import-time `TaskOrder` 验证只是 C/F lane follow-up。 |
| `WP22-D` | `pass` | legacy command consumers 已被迁移或隔离到 bridge；direct-include allowlist 现在只剩 specific bridge/default-factory seams。WP22-specific tests 已通过。 | command DTO 与 legacy-surface 退场可以进入第三轮文档同步和 guard 清理，但还不能验收。 |
| `Validation sweep` | `pass` | WP22-specific tests 已通过，且 aggregate sweep 在 WP16/WP20 drift cleanup 后已通过。 | drift cleanup 已完成；第四轮后续工作现在转向 TaskOrder import unlock、RTE-003/RTE-007 下一切片与文档同步。 |

## 当前验证轮

| Stream | 状态 | 证据摘要 | 含义 |
|--------|------|----------|------|
| `Zeno` | `pass` | 恢复 datalink command cleanup 变量，成功重建 `ef_py`，并验证 terrain/setup 聚焦切片：facade/world-batch 合计 `7` passed。 | 之前的 `data_link_system.h:284` build blocker 已关闭。 |
| `Tesla` | `partial` | `python/rl/runtime` 中 runtime reward/info call sites 现在走命名 loader-backed seam，聚焦 runtime 测试通过；repo 级 raw loader seam 仍在有边界切片外存活。 | 不得把 `RTE-003` 升级为 pass；下一轮应派发更窄的 residual seams。 |
| `Arendt` | `pass` | 文档同步返回时完整，但它发生在 Zeno 修复 build blocker 之前，因此需要本次事实纠偏。 | 文档同步在本纠偏后可接受；仍不创建 acceptance review。 |

## 后续验证轮

| Stream | 状态 | 证据摘要 | 含义 |
|--------|------|----------|------|
| `Russell` | `pass` | Production `loader.sim.*` / `loader.sim,` scan 为空；return packet 中 runtime facade guard、WP22 tasking bridge guard 与聚焦 mission/execution tests 均通过。 | `RTE-003` 可作为 production raw-loader cleanup 的 scoped pass 被消费。 |
| `Bernoulli` | `pass` | silent env/default legacy selection 已移除；`legacy`、`batch_runtime`、raw runtime fallback 与 fallback cadence 都保留为显式 compatibility opt-in，并有聚焦测试通过。 | `RTE-005` 可作为 scoped pass 被消费；`RTE-001/002/004/006` 仍是 guarded compatibility surfaces。 |
| `Parfit` | `pass` | `PilotWeaponRelease` 现在通过 `register_pilot_weapon_release_system(ecs, *this)` 注册；packet 中 structural/WP9 guards 与 `ef_py` build 均通过。 | `S-006` 可作为 pilot helper-system 切片 scoped pass 被消费。 |
| `Raman` | `done` | Queue sync 已记录 scoped passes，并保持 `WP22-F` ineligible；doc closure audit 仍报告 `0` canonical acceptance reviews 与 `8/8` zh peers。 | 文档同步只作为 status tracking 接受，不作为 closure evidence。 |

## 第五轮验证

| Stream | 状态 | 证据摘要 | 含义 |
|--------|------|----------|------|
| `Hooke` | `pass` | Maintained facade internals 现在使用 facade/batch-owned 窄方法；`ef_py` build、runtime facade layering guard 与 runtime facade tests 均通过。 | `L-002` 可作为 maintained facade internals 的 scoped pass 被消费；repo-level diagnostics residuals 仍是 allowlisted follow-up。 |
| `Socrates` | `pass` | Default factory legacy seed 已移入 `SpawnCompatibilityLegacyCommandSeed`；default-factory/WP9 guards 通过。 | `L-001b/F-004` seed ownership 已 quarantine；typed control-state replacement 是后续工作。 |
| `Epicurus` | `blocked, superseded by main-thread follow-up` | Contract-level maintained typed setup evidence 与 blocker guards 已落地，但 runtime facade maintained execution 不在该 worker 写域内。 | 后续实现已在 maintained facade path 关闭 A-001；保留 Epicurus 作为 provenance，不作为当前 blocker。 |
| `Main-thread A-001 follow-up` | `pass` | Maintained typed setup 现在通过 `validate_maintained_typed_platform_spawn_request(...)` 校验，通过 `WorldBatchRuntime::spawn_typed_platform_unit(...)` materialize，`setup_surface` 已暴露给 Python，并通过 focused setup/facade guards。 | `WP22-F` 不会因此自动 eligible；剩余 residual 是 default-factory control-state replacement、aggregate DTO shells、compatibility/diagnostics escape hatches 与 structural/binding debt。 |
| `Pascal` | `pass` | Direct GPU visual binding raw-world access 已移入 `WorldBatchRuntime::collect_visual_binding_compatibility_scenes_batch(...)`；build、architecture guard 与 focused GPU binding test 通过。 | 公开 raw world access 仍是 compatibility/diagnostics；更广义 world-batch service split 仍开放。 |
| `Bohr` | `pass after main-thread behavior-preservation fix` | Default factory legacy seed ownership 已移入 `default_factory_legacy_spawn_compat.h`；`default_unit_factory.h` 不再 direct include `legacy_command.h`；build 与 focused guards 通过。 | typed control-state/default initialization replacement 仍开放。 |
| `Poincare` | `timeout/shutdown` | Closure preflight 没有返回完整 packet。 | 无 closure evidence；`WP22-F` 仍不 eligible。 |
| `Hume` | `pass` | Naval post-step manual query loop 已移入 `register_naval_mission_weapon_release_system(ecs, *this)`；structural/naval/build checks 通过。 | `A-002` 可作为 naval fire-loop ordering seam 的 scoped pass 被消费。 |
| `Mencius` | `integration recheck 后 pass` | Counterfactual validation monolith 已按 family 拆分；初始 build blocker 已由 Hooke 清除；structural/build checks 通过。 | `F-001` validation-family split 可作为 scoped pass 被消费。 |
