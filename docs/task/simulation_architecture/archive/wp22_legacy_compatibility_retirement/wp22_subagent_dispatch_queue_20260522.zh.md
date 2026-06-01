# WP22 Subagent 派发队列

状态：`2026-05-23` frozen / historical only；已由
[`WP23 Legacy Retirement Recovery And Reset`](../wp23_legacy_retirement_recovery/legacy_retirement_recovery_wp23_20260523.zh.md)
取代。本 queue 中任何条目都不得直接派发。所有未来工作必须重写为 WP23 cluster，
通过 WP23 delete-or-block gate，并获得新的有边界 dispatch packet。

冻结前历史状态：`2026-05-22` WP21 owner-rejected；WP22 remediation active。第五轮加主线程
A-001 follow-up 已对 maintained typed setup、maintained facade raw-drilling removal、
default-factory seed quarantine、naval helper-system ordering 与 validation-family
split 给出 scoped pass。最新 implementation round 又增加了 direct GPU visual-binding
raw-world quarantine 与 default-factory legacy seed helper extraction 的 scoped pass。
最新 guard-and-quarantine round 又验收了 DTO transport-shell guards、
`bindings_core.cpp` maintained/diagnostics/legacy registration separation，以及
repo 级 `batch_runtime` consumer guard hardening。
第八轮关闭了 maintained binding raw-entity seam，并验收了 private visual-binding
service extraction。第九轮验收了 Maxwell 的 scoped `WorldBatchRuntime` setup
orchestration split。Hooke 后续 typed command-control inventory 是只读 `pass`
证据：最小下一 replacement seam 是一层薄的 `MissionCommandControlState`。Meitner
已返回 `partial / interrupted / unvalidated`；主线程修复了观察到的 `CommandLag`
target-overwrite 风险，并完成 focused architecture/runtime/build 本地复验。第十轮
现已返回完整 packets：Descartes 确认 ingress/link 缺口，Averroes 落地 typed
ingress/link sync，Parfit 收紧 guard。早先 default-factory typed seed 工作仍是
`partial`，因为 `MovementCommand` / `LaggedCommand` projection 仍是 compatibility
mirror，而不是已退场 ownership。
第十一轮 follow-up 已回收 Copernicus、Gauss 与 Dalton packets：Copernicus 是只读
blocker evidence，Gauss 是 scoped default-factory state-owner clarification pass，
Dalton 是可本地编译/过 focused gate 的 `partial` consumer-migration patch，不是
closure。
`WP22 overall` 仍然开放：在剩余 compatibility/diagnostics escape hatches、
DTO/default-factory replacement 与 structural/binding debt 返回完整证据前，acceptance
或最终 closure 工作都不 eligible。`R3` 已经重划为有限 replacement cluster；只有剩余任务簇文档里的三个子切片可派发，public escape-hatch deletion 仍被阻断。最新回收的 packets 已将 R0/R1-1 command-link pending transport narrowing、R2 `MissionCommand` owner-slice migration、R1-3 exact-stage contract ledger demotion、R3-1 scenario-loader construction、R3-2 world layout/time-step access、R3-3 visual/candidate helper centralization 验收为 scoped pass。R3 在这里已没有继续 implementation 派发，public escape-hatch deletion 仍被阻断。R2 在任何后续 implementation 前必须先正式重切边界。
这次正式重切是 docs-only；R2 的残余目标只剩 `TaskOrder`、`LeaderIntent`、
`PilotReport` 与 world-batch assignment shells，不授权 implementation、
`WP22-F`、`R4` 或 closure。

语言：

- 英文主文：[wp22_subagent_dispatch_queue_20260522.md](wp22_subagent_dispatch_queue_20260522.md)
- 中文辅文：`wp22_subagent_dispatch_queue_20260522.zh.md`

输入：

- [WP22 main plan](legacy_compatibility_retirement_wp22_20260522.zh.md)
- [Subagent Usage Policy](../../../../standards/governance/subagent_usage_policy.md)

## 队列

| Stream | 依赖 | 派发状态 | 写入范围 |
|--------|------|----------|----------|
| `WP22-A Retirement Fact Ledger And Kill List` | none | source-backed；Python blocker verified | 仅 docs/source inventory：修正审计事实、kill list、owner/gate map。 |
| `WP22-B0 Python Source-Pass Verification` | A Python gap | complete：`blocked`，touched files `none` | 只读核验 Python tasking/profile/mission-command bypasses。 |
| `WP22-B Python Business Bypass Retirement` | B0 blocked result，维护中业务退场 pass | maintained-business slice 已完成；剩余 raw-loader seam 已在 C/F guard ownership 下派发 | Python tasking/profile/mission-command 退场已完成；`RTE-003` repo-level raw loader seam 尚未闭合，归当前 guard-lane implementation wave 所有。不编辑 C++ facade internals。 |
| `WP22-C Runtime Escape-Hatch And Legacy Mode Closure` | A runtime readiness；与 B 协调 | production raw-loader、silent-selection、maintained facade raw-drilling、direct GPU binding raw-world 与 repo-level `batch_runtime` guard slices 已接受；公开 escape hatch 仍是 quarantine | Runtime facade/batch escape-hatch gating、legacy-mode opt-in、facade tests、公开 `L-002` guard follow-up 与 service-boundary narrowing。 |
| `WP22-D Command DTO And Legacy Surface Retirement` | A 与 C boundary decisions | terrain/setup、A-001 maintained typed setup、default-factory seed helper extraction 与 DTO transport-shell guards 已接受；typed control-state replacement 与真实 DTO retirement 仍开放 | C++ command resolution、DTO legacy gates、typed setup guards，以及 default-factory typed control-state replacement。 |
| `WP22-E Structural God-File Decomposition` | A readiness；避开 C 的行冲突 | entry-header splits、validation-family split、helper-system ordering、GPU binding quarantine、default-factory helper extraction 与 binding-surface registration split 已接受 | 剩余 runtime facade/factory/binding/world-batch service seams 的 behavior-preserving extraction。 |
| `WP22-F Guardrail And Acceptance Closure` | B-E | not eligible | Guards、validation rollup、residual rejection、indexes、bilingual closure、acceptance draft 需要等证据存在后再做。 |

## 第一轮派发状态

| Stream | 建议模型 / 推理预算 | 派发包 |
|--------|---------------------|--------|
| `WP22-A` | `gpt-5.4-mini`, xhigh | 已派发。Lagrange、Laplace 与 Raman 返回了可用 runtime/C++/structural findings；缺失的 Python pass 后续由 `WP22-B0` 闭合为 source-verified blocker。 |

## WP22-B 前置重派

| Stream | 建议模型 / 推理预算 | 派发包 |
|--------|---------------------|--------|
| `WP22-B0 Python Source-Pass Verification` | `gpt-5.4-mini`, xhigh | 已完成为 `blocked`，touched files 为 `none`。它核验出 `PY-001` 至 `PY-005` 全部 live，因此 `WP22-B` 只能进入 implementation remediation，不能进入 pass/acceptance。 |

## 第二轮派发

| Stream | 建议模型 / 推理预算 | 派发包 |
|--------|---------------------|--------|
| `WP22-B` | `gpt-5.4`, high | 维护中业务退场已完成。`command_chain_cache` 的 import-time `TaskOrder` unlock 只是 C/F guard lane 的 validation-only follow-up，不是 blocker。 |
| `WP22-C` | `gpt-5.4`, xhigh | validation unlock：只推进 quarantine ready subset。runtime escape hatches 与 silent legacy mode 仍是 partial；拥有 runtime/batch/env config guards，并与 B 协调 tasking call-site changes，但 raw-sim seam 已归 C/F guard ownership。 |

## 第三轮派发

| Stream | 建议模型 / 推理预算 | 派发包 |
|--------|---------------------|--------|
| `TaskOrder import unlock` | `gpt-5.4-mini`, high | 验证 `command_chain_cache` 里的 import-time `ef_py.TaskOrder` 路径，并将其保持为 validation-only 的 C/F guard lane follow-up。 |
| `RTE-003/RTE-007 next slice` | `gpt-5.4`, xhigh | 继续让 raw-sim compatibility seam 与 terrain-default retirement 在 C/F 与 D ownership 之间协调推进；保留 quarantine 与 setup ownership fences。 |
| `R2 formal re-scope` | `gpt-5.4-mini`, xhigh | 仅 WP22 R2 / remaining-task / queue docs。不改代码。 | 把已接受的 `MissionCommand` 切片重切为有限 residual list：`TaskOrder`、`LeaderIntent`、`PilotReport` 与 world-batch assignment shells；保留硬停条件，并保持 `WP22-F`、`R4` 与 closure 在 scope 外。 |
| `R3 adapter raw-world replacement re-scope` | `gpt-5.4-mini`, xhigh | 仅 docs 与 queue 同步；不改代码。 | 把有限 replacement 任务簇重划成仅能派发 `R3-1` scenario-loader construction、`R3-2` world layout/time-step access、`R3-3` visual compatibility export/candidate helpers；`RuntimeFacade::runtime()`、`WorldBatchRuntime::world()`、`vec_env.batch_runtime` 与 diagnostics bindings 继续 quarantine-only。 |
| `WP22-E/D residual gates` | `gpt-5.4-mini`, xhigh | 收紧 structural decomposition 与 command DTO retirement 的剩余 residual gate，避免把开放工作写成完成证据。 |
| `Documentation fourth sync` | `gpt-5.4-mini`, xhigh | 在下一切片完成后，重新对齐账本、队列与双语文档到当前 pass/block 状态。 |

## 最新 scoped pass packet

| Worker | Scoped result | 本地验证 | 剩余 blocker |
|--------|---------------|----------|--------------|
| `Locke` | 早期 `RTE-003` raw-loader seam 切片 `pass`。Maintained tasking、command-chain、time-step、naval-screen 与 scripted-opponent 路径现在经由命名 compatibility seam。 | 历史 packet：`git diff --check`；当时 raw-loader scan 还报告 `gym_envs/scenario_loader/runtime_state.py:329` 与 `gym_envs/scenario_loader/loading.py:348`；runtime facade guard `8 passed`；tasking/naval/execution 聚焦套件 `34 passed`。Russell 后续关闭了这些最终 production anchors。 | raw-loader cleanup 已被 Russell 覆盖；更广义 runtime escape hatches 另行追踪。 |
| `Hubble` | `pass`，对应 `RTE-007` setup/type/schema ownership。缺失 terrain 默认解析为带 `default_mainline` 来源的 `flat`；显式 legacy terrain 被命名为 compatibility。 | `cmake --build build-workshop --target ef_py -j4`；facade terrain/setup `5 passed`；world-batch terrain/setup `5 passed`；scenario compiler terrain/layout `7 passed`；world setup compat `5 passed`。 | 历史显式 `legacy` fixture consumer 仍是 compatibility consumer；A-001 后续已由主线程关闭。 |
| `Carver` | counterfactual contract 入口头拆分 `pass`。`counterfactual_replay_contracts.h` 现在是低于 `1500` 阈值的 umbrella header。 | structural/WP9 guards `16 passed`；build passed。 | 后续 Mencius/main integration 已拆 validation family headers；本行保留为 historical provenance。 |
| `Noether` | runtime-window 入口头拆分 `pass`。`runtime_window_coordinator.h` 现在低于 `1000` 阈值，并委托给命名 helper headers。 | structural/WP9 guards `16 passed`；build passed。 | 更广义结构 blocker 仍存在：`runtime_facade.cpp`、`default_unit_factory.h`、broad bindings 与 fat world-batch service surface。 |

这些 packet 只在自身限定分片内被验收，不能授权 `WP22-F` 或 acceptance review。

## 后续实现轮次验收

| Worker | 分片结果 | 本地验证 | 剩余 blocker |
|--------|----------|----------|--------------|
| `Russell` | final production raw-loader cleanup `pass`。Production `loader.sim.*` / `loader.sim,` scan 现在为空。 | `git diff --check`；raw-loader scan 无匹配；runtime facade guard `8 passed`；WP22 tasking bridge guard `7 passed`；聚焦 mission/execution tests `4 + 2 + 1` passed。 | 只剩显式 test/guard 字符串；更广义 runtime escape hatches 另行追踪。 |
| `Bernoulli` | requested Python runtime quarantine slice `pass`。silent env/default legacy selection 已移除；`legacy` mode、`batch_runtime`、raw runtime fallback 与 fallback cadence 都是显式 compatibility opt-in。 | `git diff --check`；env config `6 passed`；vec-env runtime/batch tests `3 passed`；single-runtime fallback tests `8 passed`；runtime facade architecture tests `4 passed`。 | 后续 Hooke 已移除 maintained facade raw drilling；public raw access 仅作为 compatibility/diagnostics 保留。 |
| `Parfit` | `PilotWeaponRelease` ordering residual slice `pass`。该 system 现在经由 `register_pilot_weapon_release_system(ecs, *this)` 注册。 | `git diff --check`；structural/WP9 guards `16 passed`；`ef_py` build passed；聚焦 engagement/facade tests passed。 | Hume 后续关闭了 naval helper-system slice；default-factory seed 与 DTO work 另行追踪。 |
| `Raman` | 仅 queue sync `done`。队列记录 scoped passes，并保持 `WP22-F` pending next implementation evidence。 | `git diff --check`；WP22 doc closure audit advisory summary 报告 `0` canonical acceptance reviews 与 `8/8` zh peers。 | acceptance review 仍不存在；review/index sync 继续后置。 |

这些 packet 只在自身限定分片内被验收，`WP22-F` 仍不 eligible。

## 第十四轮 scoped pass 结果

| Worker | Stream | Scoped result | Local verification | Remaining blocker |
|--------|--------|---------------|--------------------|-------------------|
| `Singer` | `Operation/command-link mirror dependency reduction` | 仅对 scoped slice `pass`：operation 和 command-link systems 现在先运行 `MissionCommandControlState`，再选择性刷新 legacy mirrors。 | 主线程复验：architecture WP9/WP22/DTO focused suite `30 passed`；runtime/naval focused suite `27 passed`；`cmake --build build-workshop --target ef_py -j4` 通过；`git diff --check` clean。主线程还修复了 `tests/architecture/test_wp9_guard_enforcement.py::_compile_and_run`，在 link args 前加入 `-x none`，避免把 static library input 当作 C++ source 编译。 | operation 与 command-link mirror dependency reduction 仅是 scoped pass，不授权 deletion 或 closure。 |
| `Nietzsche` | `Naval maintained DTO consumer migration` | 仅对 scoped slice `pass`：`ship_motion_system.h` 与 `embarked_air_ops_system.h` 现在通过 naval directive helpers 处理 stationing/embarked-helo maintained reads，同时保留 `command_code` compatibility fallback。 | 与 Singer 相同的主线程复验：architecture WP9/WP22/DTO focused suite `30 passed`；runtime/naval focused suite `27 passed`；`cmake --build build-workshop --target ef_py -j4` 通过；`git diff --check` clean。 | naval maintained DTO consumer migration 仅是 scoped pass；compatibility fallback 仍 live，`WP22-F` 继续 not eligible。 |

这些 packet 仍不授权 `WP22-F`。`WP22 overall` 仍然开放，最新结果只是在收窄剩余
mirror/consumer surfaces。

## 第五轮派发结果

| Worker | Stream | 分片结果 | 本地验证 | 剩余 blocker |
|--------|--------|----------|----------|--------------|
| `Hooke` | `C++ raw facade/world retirement` | `pass`：maintained `runtime_facade.cpp` raw drilling 已移除；`RuntimeFacade::runtime()` 与 `WorldBatchRuntime::world()` 只保留为 compatibility/diagnostics escape hatches。 | `ef_py` build passed；runtime facade layering focused guard `4` passed；facade runtime/world/facade tests `29` passed；`git diff --check` passed。 | repo-level raw world residual 仍在 `src/interfaces/python/bindings_gpu.cpp:618`，不属于本切片。 |
| `Socrates` | `Default factory legacy seed retirement` | `pass`：default factory legacy command seeding 已隔离到 `SpawnCompatibilityLegacyCommandSeed`，不再是 unlabeled spawn-body `e.set(...)`。 | default-factory guard `2` passed；WP9 legacy/default focused guard `4` passed；structural guard `8` passed；`git diff --check` passed。 | compatibility seam 仍保留，直到 typed control-state/default initialization 接管。 |
| `Epicurus` | `Typed setup promotion` | `blocked`：contract-level maintained typed setup evidence 已存在，但 maintained execution 仍在 `runtime_facade.cpp`，该文件有意不在本写域。 | WP14/WP20 setup guards `12` passed；facade setup typed/world_setup tests `5` passed；`git diff --check` passed。 | `A-001` 需要 runtime-facade implementation slice 消费 `validate_maintained_typed_platform_spawn_request(...)`，并移除 maintained legacy rematerialization。 |
| `Hume` | `Naval fire-loop ordering seam` | `pass`：manual post-`step()` naval fire loop 已退场到 `register_naval_mission_weapon_release_system(ecs, *this)`。 | structural guard `8` passed；naval focused tests `9` passed；`ef_py` build passed；后续组合 WP22/WP9 structural sweep `17` passed。 | 无本切片 blocker；更广义 structural debt 另行追踪。 |
| `Mencius` | `Counterfactual validation split` | integration recheck 后为 `pass`：validation monolith 已拆为 umbrella 加 helper/replay/counterfactual/experiment validation headers。初始 out-of-scope build blocker 已被 Hooke 的 runtime facade 修复覆盖。 | validation line-count 显示原 `1643` 行 header 现在是 `4` 行加 family headers；WP22/WP9 structural sweep `17` passed；`ef_py` build passed；`git diff --check` passed。 | 无本切片 blocker；`runtime_facade.cpp` 与 bindings/factory structural debt 是独立 lane。 |
| `Main-thread follow-up` | `A-001 runtime-facade typed setup promotion` | `pass`：maintained typed setup 现在消费 maintained validator 和 batch-owned typed spawn helper，不再通过 maintained legacy request-shape rematerialization。 | `git diff --check`；`ef_py` build passed；focused setup/facade tests `12` passed；runtime facade raw-drilling guard `1` passed。 | 剩余工作是 guard/closure preflight、default-factory control-state replacement、aggregate DTO shells、compatibility/diagnostics escape hatches 与 structural/binding debt。 |

这些 packet 仍不授权 `WP22-F`。当前开放 implementation work 已收窄到
guard/closure preflight、repo-level diagnostics quarantine follow-ups、
default-factory control-state replacement、DTO/domain shell retirement 与 structural/binding debt。

## 第六轮派发结果

| Worker | Stream | 分片结果 | 本地验证 | 剩余 blocker |
|--------|--------|----------|----------|--------------|
| `Pascal` | `GPU visual binding raw-world quarantine` | `pass`：`bindings_gpu.cpp` 不再直接调用 `runtime.world(...)`；visual scene collection 现在通过 `WorldBatchRuntime::collect_visual_binding_compatibility_scenes_batch(...)`。 | `cmake --build build-workshop --target ef_py -j4`；`pytest -q tests/architecture/test_runtime_facade_layering.py -k "gpu_visual_binding or visual_binding_raw_world_access"` -> `2 passed`；`pytest -q tests/test_gpu_runtime_bindings.py -k "world_batch_visual_export_dlpack_matches_host"` -> `1 passed`。 | 公开 `WorldBatchRuntime::world()` 仍是 compatibility/diagnostics escape hatch；更广义 `WorldBatchRuntime` service decomposition 仍开放。 |
| `Bohr` | `Default factory legacy seed helper extraction` | `pass after main-thread behavior-preservation fix`：`default_unit_factory.h` 不再 direct include `legacy_command.h`；default action seed 与 flight legacy seed 经由 `default_factory_legacy_spawn_compat.h`，main thread 补充 helper call 保留非飞行单位 `ActionCommand` 行为。 | `cmake --build build-workshop --target ef_py -j4`；`python -m pytest -q tests/architecture/test_wp22_default_factory_legacy_seed_guard.py tests/architecture/test_wp9_guard_enforcement.py -k "legacy or default_factory or wp22"` -> `9 passed, 2 deselected`。 | `default_factory_legacy_spawn_compat.h` 在 typed control-state/default initialization replacement 前仍是显式 compatibility seed ownership。 |
| `Poincare` | `WP22-F closure preflight` | `timeout/shutdown`：未返回完整 packet。 | 无 accepted validation packet | 不解锁 WP22-F；remaining implementation blockers 解决后需要重跑 closure preflight，或由 main thread 接管。 |

这些 packet 仍不授权 `WP22-F`。`Pascal` 与 `Bohr` 只是 scoped implementation
pass；`Poincare` 是 transport cleanup，不能算 closure evidence。

## 第七轮 Guard 与 Quarantine 结果

| Worker | Stream | 分片结果 | 本地验证 | 剩余 blocker |
|--------|--------|----------|----------|--------------|
| `Pauli` | `DTO/domain shell guard-and-slice` | `pass`：四个 aggregate DTO 仍存在，但现在带 compatibility-transport-shell marker、owner-slice projection helper，以及 world-batch assignment wrapper guard。 | `python -m pytest -q tests/architecture -k "wp22 and (dto or shell or command or tasking)"` -> `17 passed, 212 deselected`；`ef_py` build passed；组合 WP22 guard sweep `48 passed, 13 deselected`。 | 真正 aggregate DTO retirement 仍开放；下游 maintained consumer 还需要迁移到 owner slice。 |
| `Ramanujan` | `bindings_core maintained/debug/legacy quarantine` | `pass`：`bindings_core.cpp` registration 已拆成 maintained、diagnostics-introspection、legacy-compatibility 与 diagnostics-override helpers；maintained 和 override helper block 不再直接书写 `self.get_world().entity(...)`。 | `python -m pytest -q tests/architecture/test_wp22_structural_guardrails.py -k "bindings"` -> `3 passed, 7 deselected`；`ef_py` build passed；组合 WP22 guard sweep `48 passed, 13 deselected`。 | maintained raw-entity seam 已关闭；broad binding count 仍为 `75`，diagnostics/legacy binding block 仍是 raw-ECS quarantine。 |
| `Beauvoir` | `WP22-C/F public escape-hatch preflight guard` | `preflight-only`：repo-level non-test Python `batch_runtime` consumer 现在会在 explicit compatibility/diagnostics allowlist 外被扫描；文档保持 `WP22-F` not eligible。 | `python -m pytest -q tests/architecture/test_runtime_facade_layering.py -k "runtime_facade_runtime_consumers or escape_hatch or batch_runtime or world_batch_vec_env"` -> `16 passed, 19 deselected`；WP22 doc audit summary 报告 `0` acceptance reviews。 | 公开 `RuntimeFacade::runtime()`、`WorldBatchRuntime::world()`、`vec_env.batch_runtime`、显式 `legacy` mode 与 fallback cadence 仍是 compatibility/diagnostics surfaces。 |

这些 packet 仍不授权 `WP22-F`；它们提升 guard 覆盖与 quarantine 清晰度，但没有移除剩余 compatibility surfaces。

## 第九轮实现结果

| Worker | Stream | 分片结果 | 本地验证 | 剩余 blocker |
|--------|--------|----------|----------|--------------|
| `Maxwell` | `WorldBatchRuntime setup orchestration split` | `pass`：新增 `src/core/engine/world_batch_setup_helper.h`；`WorldBatchRuntime::apply_world_setup_batch` 的 setup orchestration、terrain/wind/zone/reset seed resolution 移入 private helper，同时保持公开 `WorldBatchRuntime::world()` compatibility/diagnostics escape hatch 不变。 | runtime facade layering focused guard `10 passed, 26 deselected`；world_batch setup focused tests `3 passed, 21 deselected`；`cmake --build build-workshop --target ef_py -j4` 通过；`git diff --check` clean。 | 公开 `WorldBatchRuntime::world()` 仍是 compatibility/diagnostics escape hatch；更广义 world-batch service decomposition 仍开放；default-factory typed control-state blocker 仍开放。 |
| `Hooke` | `Typed command-control replacement inventory` | 只读 `pass`，`touched files: none`：确认 `default_factory_legacy_spawn_compat.h`、`operation_system.h` 与 `control_system.h` 是最小第一实现 seam，`force/propulsion/ground/instrument/embarked/command_link` 后续继续留在 compatibility bridge。 | architecture default-factory/WP9/structural guards `21 passed`；mission/naval/link focused tests `18 passed`；无文件编辑。 | inventory 不是 retirement。必须等 `MissionCommandControlState` 或等价 typed seam 落地后，`L-001b/F-004` 才能升级。 |
| `Poincare` | `Docs/state cleanup` | `partial`，`touched files: none`：按要求停止，只定位了 stale queue/ledger/main-plan 区域。 | packet 未运行 audit 或 diff-check；主线程保持 closure audit 为 `0` 个 acceptance review。 | 除 discovery 外没有 docs cleanup evidence；最小同步由主线程接管。 |
| `Meitner` | `Typed command-control implementation` | `partial / interrupted / unvalidated`：新增 `MissionCommandControlState`，并让 operation/control/default-control 朝 typed state 接入，但在 command ingress/link/default-factory validation 前停止。主线程修复了 `CommandLag` lagged 初始化覆盖 target 的风险。 | 主线程复验：architecture default-factory/WP9/structural guards `21 passed`；mission/naval/link focused tests `18 passed`；`cmake --build build-workshop --target ef_py -j4` 通过；`git diff --check` clean。 | `set_unit_command`、`set_unit_stick_command` 与 `CommandLinkMovement` 仍需要 typed-state sync 或 quarantine hardening；default-factory helper 仍 materialize compatibility `MovementCommand` / `LaggedCommand`。 |

这些 packet 仍不授权 `WP22-F`。`Maxwell` 与 Hooke 分别记录为 scoped/read-only
pass；Meitner 明确记录为 `partial`，不是 closure。

## 第十轮实现与 Guard 结果

| Worker | Stream | 分片结果 | 本地验证 | 剩余 blocker |
|--------|--------|----------|----------|--------------|
| `Descartes` | `Typed-control fact verification` | `partial / read-only`：确认第十轮实现前 `MissionCommandControlState` 仍只是 source-of-truth island，default-factory spawn 仍 materialize live legacy DTO mirrors。 | 只读 `rg` / `nl` source inspection；`touched files: none`。 | Inventory 不是 retirement；它为 Averroes 与 Parfit 提供 ingress/link guard 缺口输入。 |
| `Averroes` | `Typed ingress/link sync implementation` | `pass`：non-ship immediate `set_unit_command` 与 deferred `CommandLinkMovement` 现在先更新 `MissionCommandControlState`，再刷新 `MovementCommand` / `LaggedCommand` compatibility mirrors；stick command 明确 quarantine 为 legacy-only。 | 主线程复验：`cmake --build build-workshop --target ef_py -j4`；runtime mission/naval/link focused suite `19 passed`；`git diff --check` clean。worker packet 也报告同一 runtime suite `19 passed` 与 build pass。 | `PendingMovementCommand` 仍携带 legacy transport payload；legacy movement debug、stick DTO compatibility、`ActionCommand` / `PendingActionCommand` 与下游 mirror consumers 仍开放。 |
| `Parfit` | `Typed-control guard hardening` | `pass`：default-factory helper 被 guard 为 compatibility-only 且必须同时 seed typed state；command ingress 被 guard 为经由 `legacy_command_bridge.h` helper；bridge helper 锚定 typed-state mirror sync。 | 主线程复验：architecture default-factory/WP9/structural suite `21 passed`；`git diff --check` clean。worker packet 也报告 `21 passed`。 | Guard hardening 不是 closure；default-factory helper 在 typed replacement 完全接管 spawn defaults 前仍是命名 compatibility seam。 |

这些 packet 仍不授权 `WP22-F`。它们关闭 ingress/link typed-state blocker，但 legacy
transport shell、debug surfaces、下游 mirror consumers、default-factory compatibility
projection、aggregate DTO shells、runtime escape hatches 与 structural debt 仍开放。

## 第十一轮 Command-Control Follow-Up 结果

| Worker | Stream | 分片结果 | 本地验证 | 剩余 blocker |
|--------|--------|----------|----------|--------------|
| `Copernicus` | `Read-only forced-retirement fact check` | `partial / read-only`：确认 `WP22-F eligibility = no`；live `MovementCommand` / `LaggedCommand`、pending transport shell、debug legacy movement hook 与 default-factory projection 仍可在源码中定位。 | worker packet：WP22 default-factory/DTO/structural/naval debug focused suite `21 passed`；`touched files: none`。 | 只读证据，不是 retirement；下一步 implementation 应聚焦 spawn projection replacement、live consumer migration/quarantine 与 debug/pending transport narrowing。 |
| `Gauss` | `Default-factory typed control-state ownership slice` | `pass`：spawn default ownership 明确为 `MissionCommandControlState`；`SpawnCompatibilityLegacyCommandSeed` 现在只是 compatibility alias，`MovementCommand` / `LaggedCommand` 在 apply 时由 control state 投影，不再作为 seed struct state 保存。 | 主线程与 Dalton patch 集成后复验：architecture default-factory/WP9/structural suite `21 passed`；runtime mission/naval/link suite `19 passed`；`cmake --build build-workshop --target ef_py -j4` 通过；`git diff --check` clean。 | 下游 consumer 仍需要 mirrors，因此 mirror 仍 live；这是 scoped semantic narrowing，不是 spawn projection 退场。 |
| `Dalton` | `Command mirror consumer migration slice` | `partial`：`control_input_resolution.h` 增加 state-first resolver 形态，`force_system.h` 现在把 active `MissionCommandControlState` 视作 primary control-input source。`propulsion_system.h`、`instrument_system.h` 与 `ground_contact_system.h` 只是 plumbing，尚未消费 typed throttle/brake 语义。 | 主线程复验：architecture default-factory/WP9/structural suite `21 passed`；runtime mission/naval/link suite `19 passed`；`cmake --build build-workshop --target ef_py -j4` 通过；`git diff --check` clean。worker packet 未运行验证。 | `MissionCommandControlState` 不承载 throttle/brake，因此 propulsion/instrument/ground-contact 仍是 bridge-fallback consumers；`embarked_air_ops_system.h`、pending transport、debug legacy movement hook 与 operation/link mirrors 仍开放。 |

这些 packet 仍不授权 `WP22-F`。`Gauss` 只作为 scoped pass 接受；
`Copernicus` 与 `Dalton` 均是 `partial` evidence。下一轮必须闭合更小写域，
不得宣称全局退场。

## 第八轮实现结果

| Worker | Stream | 分片结果 | 本地验证 | 剩余 blocker |
|--------|--------|----------|----------|--------------|
| `Harvey` | `Default-factory typed seed reduction` | `partial`：default-factory flight-model spawn 现在 seed typed `MissionCommand` shell，并从 `MissionCommandCore` 投影剩余 legacy seed；重复 flight-model `ActionCommand` seeding 已减少。 | default-factory/WP9 guards `9 passed, 2 deselected`；mission/naval focused tests `5 passed`；`ef_py` build passed；`git diff --check` passed。 | `default_factory_legacy_spawn_compat.h` 仍持有 behavior-bearing `MovementCommand` / `LaggedCommand` projection；typed control-state replacement 缺失。 |
| `Banach` | `Bindings maintained raw-entity seam reduction` | `pass`：maintained binding reads 现在使用 kernel-owned query methods，不再使用 `bindings_core.cpp` 本地 raw-entity lookup。 | binding guard `3 passed, 7 deselected`；`ef_py` build passed；组合 WP22 guard sweep `45 passed, 16 deselected`。 | diagnostics 与 legacy binding block 仍是 raw-ECS quarantine；broad binding count 仍为 `75`。 |
| `Planck` | `WorldBatchRuntime service-surface split` | `pass`：visual-binding compatibility scene assembly 已移到 private helper，并保持公开 compatibility method 行为不变。 | runtime facade layering guard `9 passed, 26 deselected`；`ef_py` build passed；`git diff --check` passed。 | 公开 `WorldBatchRuntime::world()` 仍是 compatibility/diagnostics escape hatch；更广义 service decomposition 仍开放。 |

这些 packet 仍不授权 `WP22-F`。`Harvey` 必须记录为 `partial`，不是 pass。

## 下一轮派发

| Stream | 建议模型 / 推理预算 | 写入范围 | 派发包 |
|--------|---------------------|----------|--------|
| `Air-control typed resolver slice` | `gpt-5.4`, xhigh | `control_input_resolution.h`、physics consumers 与聚焦 runtime/architecture tests。 | 闭合 Dalton 的 partial：maintained physics consumers 只能消费 bridge-owned resolved inputs，legacy probing 只能留在 bridge seam 内。 |
| `Embarked-air state-first write-chain slice` | `gpt-5.4`, high | `embarked_air_ops_system.h`、必要的小型 bridge helper、naval focused tests。 | 移除基于 `MovementCommand*` 是否存在来决定 launch/recover 写入的逻辑；通过 state-first bridge helper 同步 typed state 与 mirrors。 |
| `Debug/pending transport narrowing slice` | `gpt-5.4`, high | `bindings_core.cpp`、binding/naval/link focused tests 与 guards。 | legacy movement debug injection 走 bridge；pending movement/action getter 明确 diagnostics transport shell；禁止 debug setter 绕过 typed state。 |
| `Docs/state cleanup` | `gpt-5.4-mini`, xhigh | 仅 WP22 queue/ledger docs。 | 清理重复或过时的 queue/ledger 段落，不改变 acceptance status。保持 `WP22-F` not eligible。 |
| `WP22-F closure preflight` | `gpt-5.4-mini`, xhigh | 仅 WP22 docs、architecture guard reports、closure-audit output。 | 当前仍不 eligible；必须等上述 implementation slice 返回完整 packet 后再重跑。 |

## 活跃派发映射

| Worker | Stream | Agent id | 状态 |
|--------|--------|----------|------|
| `Hooke` | `C++ raw facade/world retirement` | `019e4f62-0190-7e42-bba1-983a0079f07e` | scoped pass accepted |
| `Socrates` | `Default factory legacy seed retirement` | `019e4f62-023b-7962-a728-ebb5bca50d0b` | scoped pass accepted |
| `Epicurus` | `Typed setup promotion` | `019e4f62-02d5-7252-9ab1-92ec4d8431b8` | blocked packet accepted；需要 follow-up |
| `Hume` | `Naval fire-loop ordering seam` | `019e4f62-0308-74a2-94d5-1538661b48b3` | scoped pass accepted |
| `Mencius` | `Counterfactual validation split` | `019e4f62-0344-7fd1-b23a-60676b355b9e` | integration recheck 后 scoped pass accepted |
| `Mill` | `A-001 runtime-facade typed setup promotion` | `019e4f94-b16f-7592-8419-2b56dc2f7936` | closed without packet；主线程完成并验证 follow-up |
| `Halley` | `Documentation fact sync` | `019e4f94-fd79-7932-8aea-c2a495038671` | closed without packet；主线程完成事实同步 |
| `Pascal` | `GPU visual binding raw-world quarantine` | `019e4fb3-9d6d-76c3-88ad-0c15f1510232` | scoped pass accepted after local recheck |
| `Bohr` | `Default factory legacy seed helper extraction` | `019e4fb3-9dd5-7103-81ac-ef9bbdf73b3e` | scoped pass accepted after main-thread behavior-preservation fix |
| `Poincare` | `WP22-F closure preflight` | `019e4fb3-9c9c-7f31-945f-b66ccef44a24` | shutdown without packet；无 closure evidence |
| `Pauli` | `DTO/domain shell guard-and-slice` | `019e4fd9-317e-7e53-8e51-68c3ad7c00d9` | scoped pass accepted after local recheck |
| `Ramanujan` | `bindings_core maintained/debug/legacy quarantine` | `019e4fd9-3218-7bd3-86d6-61e1fff6f3e7` | scoped pass accepted after local recheck |
| `Beauvoir` | `WP22-C/F public escape-hatch guard preflight` | `019e4fd9-3252-7d71-b016-ae47dcc6aa33` | preflight-only accepted；无 closure evidence |
| `Harvey` | `Default-factory typed seed reduction` | `019e4ff3-7e4c-7412-85be-c62a3be69f4e` | partial accepted as blocker evidence |
| `Banach` | `Bindings maintained raw-entity seam reduction` | `019e4ff3-7eaa-7822-a2f4-a06b17c77800` | scoped pass accepted after local recheck |
| `Planck` | `WorldBatchRuntime service-surface split` | `019e4ff3-7efd-72d2-977e-dac2fd4e1536` | scoped pass accepted after local recheck |
| `Maxwell` | `WorldBatchRuntime setup orchestration split` | `019e501f-4f93-7c90-bc8b-b9842dfa3654` | scoped pass accepted after local fix/recheck |
| `Hooke` | `Typed command-control replacement inventory` | `019e501f-19ee-76f3-aed0-2394ad743ac2` | read-only pass accepted；无编辑 |
| `Poincare` | `Docs/state cleanup` | `019e501f-b17d-7801-b81c-c6ed5f14f9e7` | partial；无编辑；最小同步由主线程接管 |
| `Meitner` | `Typed command-control implementation` | `019e502e-acf2-7c11-9844-43d15802be83` | partial packet 已作为 blocker evidence 接受；主线程行为修复/复验完成 |
| `Descartes` | `Typed-control fact verification` | `019e5043-0407-7c23-a6d4-c2da4740d5b5` | partial/read-only packet accepted as blocker evidence；已关闭 |
| `Averroes` | `Typed ingress/link sync implementation` | `019e5046-c1f1-7382-82bc-92b8ff29f770` | scoped pass accepted after local recheck；已关闭 |
| `Parfit` | `Typed-control guard hardening` | `019e5046-c242-7e00-a6cf-72263289a957` | scoped guard pass accepted after local recheck；已关闭 |
| `Copernicus` | `Read-only forced-retirement fact check` | `019e5059-f4a2-7da3-ba64-195c3816570a` | partial/read-only packet accepted as blocker evidence；已关闭 |
| `Gauss` | `Default-factory typed control-state ownership slice` | `019e5059-f42f-70f1-bda7-c61b47f4236d` | scoped pass accepted after local recheck；已关闭 |
| `Dalton` | `Command mirror consumer migration slice` | `019e5059-f339-7322-b61c-a5c2674ca8e2` | partial packet accepted only as buildable blocker evidence；已关闭 |
| `Curie` | `Air-control typed resolver slice` | `019e5067-3d10-7991-9536-7f5c46b62061` | partial packet；主线程修复并本地复验 |
| `Noether` | `Embarked-air state-first write-chain slice` | `019e5067-7c8a-70b1-bd3b-de6995b27d53` | transport failure: 429；无 packet；无证据 |
| `Hume` | `Embarked-air state-first write-chain slice` | `019e5069-802b-7d03-90b0-ece7b219f7b7` | scoped pass accepted after local recheck |
| `Boole` | `Debug/pending transport narrowing slice` | `019e5067-bd55-7170-b77e-66bc31109502` | scoped pass accepted after local recheck |

## 第十二轮窄化结果

| Worker | Stream | 分片结果 | 本地验证 | 剩余 blocker |
|--------|--------|----------|----------|--------------|
| `Boole` | `Debug/pending transport narrowing slice` | `pass`：`debug_set_legacy_movement_command` 现在通过 bridge helpers 写入，并同步 `MissionCommandControlState` 与 legacy mirrors；legacy/pending getters 标记为 diagnostics mirror 或 diagnostics transport shell，并在相关处暴露 control-state mirror context。 | 主线程复验：runtime naval/link/mission focused suite `16 passed`；architecture structural/WP9 suite `20 passed`；combined naval/architecture sweep `24 passed`；`cmake --build build-workshop --target ef_py -j4` 通过；`git diff --check` clean。 | debug getters 与 pending transport shells 仍存在；这是 quarantine/narrowing，不是删除或 DTO retirement。 |
| `Hume` | `Embarked-air state-first write-chain slice` | `pass`：launch/recover 写入不再依赖预先存在的 `MovementCommand*`；系统直接调用 bridge helpers，且 `compatibility_mutable_legacy_movement_command(...)` 已从 bridge surface 移除。 | 主线程复验：combined naval/architecture sweep `24 passed`；`cmake --build build-workshop --target ef_py -j4` 通过；`git diff --check` clean。worker packet 也报告 naval debug `4 passed`、architecture suite `20 passed`、build pass 与 diff-check clean。 | command-link、operation、air-control resolver、default-factory projection 以及更广义 DTO/runtime escape hatches 仍开放。 |
| `Curie / main-thread repair` | `Air-control typed resolver slice` | `partial packet, repaired to scoped pass`：Curie 留下 `instrument` 与 `ground_contact` 继续查看 raw source pointers。主线程将 `force`、`propulsion`、`instrument` 与 `ground_contact` 接到 `control_input_resolution.h` 输出的 `ResolvedAirControlInput`，同时把 throttle/brake legacy fallback 保持在 bridge seam 内。 | 主线程复验：architecture default-factory/WP9/structural suite `23 passed`；runtime mission/naval/link suite `20 passed`；`cmake --build build-workshop --target ef_py -j4` 通过；`git diff --check` clean。 | `MissionCommandControlState` 仍不表达 throttle/brake；legacy fallback 仍是 bridge-owned compatibility。command-link、operation、default-factory projection、DTO shell 与 runtime escape hatch 仍开放。 |

这些 scoped pass 仍不授权 `WP22-F`。它们收窄了三个 residual surfaces，但
command-link、operation、default-factory projection、DTO shell、runtime escape
hatches 与更广义 structural debt 仍开放。

## 第十三轮 Operation 与 Projection 结果

| Worker | Stream | 分片结果 | 本地验证 | 剩余 blocker |
|--------|--------|----------|----------|--------------|
| `Bohr` | `Operation-system legacy mirror quarantine` | `pass`：`operation_system.h` 不再持有本地 legacy mirror seed/refresh helpers，改用 bridge-owned control-state seed 与 mirror refresh helpers。`MovementCommand` / `LaggedCommand` 仍作为 compatibility mirrors 留在 system signatures 中。 | 主线程复验：architecture default-factory/WP9/structural suite `23 passed`；mission runtime suite `6 passed`；`cmake --build build-workshop --target ef_py -j4` 通过；`git diff --check` clean。 | `operation_system.h` 仍 direct include `legacy_command.h`，因为 system signatures 保留 `ActionCommand`、`MovementCommand` 与 `LaggedCommand` mirrors。 |
| `Schrodinger` | `Default-factory projection readiness fact check` | `blocked / read-only`：`can_delete_projection = no`；default-factory 仍投影 `MovementCommand` / `LaggedCommand` mirrors，且剩余 consumers 仍需要它们。 | worker packet：default-factory/WP9 command-focused guard `7 passed, 5 deselected`；`git diff --check` clean；`touched files: none`。 | projection deletion 受 bridge fallback、operation mirrors、command-link delivery 与仍 live 的 MovementCommand readers 阻塞。 |
| `Epicurus` | `Command-link pending transport narrowing` | `blocked / 无 packet` | 尚无 packet | pending transport 要等完整 packet 后才能验收或记录为 partial/blocked。 |

这些 packet 仍不授权 `WP22-F`。operation helper ownership 已收窄，但
command-link pending transport 与 default-factory mirror projection 仍是 active blockers。

## 第十五轮有限任务簇结果

| Worker | Stream | Scoped result | 本地验证 | 剩余 blocker |
|--------|--------|---------------|----------|--------------|
| `Banach` | `Command-link pending transport narrowing` | `pass`：delayed movement delivery 由 typed state 拥有，`PendingMovementCommand.command` 只是 diagnostics shell，`PendingActionCommand.typed_air_control_bridge` 承载 typed overlay projection，action transport 仍保持 quarantine。 | 主线程复验：`ef_py` 构建通过；command/pending architecture suite `17 passed, 13 deselected`；DTO shell guard `7 passed`；runtime/facade/world-batch/GPU focused suites `98 passed, 64 deselected`；`git diff --check` clean。 | `ActionCommand`、pending action transport、legacy mirrors、default-factory projection 与 diagnostics bindings 仍是 live compatibility surfaces。 |
| `Franklin` | `MissionCommand owner-slice migration` | limited `MissionCommand` mission-episode consumer slice `pass`：shared-core maintained reads 现在使用显式 owner-slice helpers，不再 flat aggregate shell 直读。 | 主线程复验包括 DTO shell guard `7 passed`、`ef_py` build pass 与 diff-check clean。 | `TaskOrder`、`LeaderIntent`、`PilotReport`、world-batch assignment shells 与更广义 aggregate DTO retirement 仍开放；R2 后续 implementation 前必须正式重切边界。 |
| `Planck` | `R3 finite re-scope` | `pass`：R3 被限制为 `R3-1`、`R3-2`、`R3-3`；public escape-hatch deletion 仍阻塞。 | 主线程检查 docs 并随后同步；diff-check clean。 | 本身不是 implementation evidence；只限定后续 R3 切片。 |
| `Wegener` | `Exact-stage contract demotion/alignment` | R1-3 `pass`：exact-stage inventory 现在是 guarded contract ledger，不是 maintained implementation truth。 | 主线程复验：command/exact-stage architecture suite `17 passed, 13 deselected`；diff-check clean。 | `R1-B` 仍被阻塞；ledger demotion 不授权 default-factory projection deletion。 |
| `Heisenberg` | `Scenario-loader construction` | R3-1 `pass`：adapter scenario-loader construction 使用命名 runtime-world-layout request/result seam，未新增 maintained raw-world construction call site。 | 主线程复验：world setup/world-batch/facade suites `81 passed, 29 deselected`；diff-check clean。 | `adapter.py::world()` 与 `get_time_step()` raw compat fallback 仍归 R3-2。 |
| `Descartes` | `Visual compatibility export/candidate helpers` | R3-3 `pass`：facade-owned visual candidate assembly 与 GPU wrappers 现在显式分离 facade-owned 和 compatibility-runtime paths。 | 主线程复验：visual/GPU/facade focused suites `17 passed, 35 deselected`；`ef_py` build pass；diff-check clean。 | 公开 `RuntimeFacade::runtime()`、`WorldBatchRuntime::world()`、`vec_env.batch_runtime`、diagnostics bindings 与 R3-2 仍是 blockers。 |

这些 packet 仅作为 scoped pass 接受。`WP22-F`、public escape-hatch deletion 与 default-factory projection deletion 仍不 eligible。

## 第十六轮 R3-2 结果

| Worker | Stream | Scoped result | 本地验证 | 剩余 blocker |
|--------|--------|---------------|----------|--------------|
| `Popper` | `R3-2 World layout/time-step access` | R3-2 `pass`：`RuntimeFacadeAdapter::world()` 现在返回受控 proxy 用于 layout/time-step read，`get_time_step()` 优先走 facade/runtime helper，adapter-owned layout snapshot 避免新增 maintained raw-world layout/time-step call site。 | 主线程复验：`ef_py` 构建通过；runtime facade layering `10 passed, 28 deselected`；world setup/world-batch `52 passed, 4 deselected`；facade/multi-agent runtime `33 passed, 24 deselected`；`git diff --check` clean；WP22 closure audit 仅保留预期的 missing-acceptance warning。 | `RuntimeFacade::runtime()`、`WorldBatchRuntime::world()`、公开 `batch_runtime` / `vec_env.batch_runtime`、显式 `legacy` mode、diagnostics bindings 与 raw-world compatibility forwarding 仍是 quarantine-only。这不是 deletion-ready 或 closure evidence。 |

`R3-1`、`R3-2`、`R3-3` 现在都是 scoped pass。不要从该 cluster 继续派发 R3
implementation；下一批有限工作切换到 R2 owner-slice implementation。

## 下一批有限派发

| Stream | 建议模型 / 推理预算 | 写入范围 | 派发包 |
|--------|---------------------|----------|--------|
| `R2 TaskOrder owner-slice implementation` | `gpt-5.4`, xhigh | `src/components/tasking/task_order.h`、必要时现有 TaskOrder owner-slice headers、`tests/architecture/test_wp22_dto_domain_shell_guard.py` 与 focused tasking/mission tests。不要编辑 runtime facade、command-link、public escape-hatch 或 R3 文件。 | 将 maintained TaskOrder evidence 推向显式 owner-slice directives/guards，不发明新 DTO shape，不扩宽 compatibility shell。如果 maintained flat-shell truth 仍存在，返回 `partial` 或 `blocked`。 |
| `R2 read-only maintained-consumer fact check` | `gpt-5.4-mini`, xhigh | 只读源码检查；touched files 必须是 `none`。 | 找出 `LeaderIntent`、`PilotReport` 与 world-batch assignment shells 仍消费 flat aggregate truth 的精确 maintained call sites。返回源码锚点和最小下一 implementation slice；不改文件、不授权 closure。 |

## 第十七轮 R2 partial/blocked evidence

| Worker | Stream | Scoped result | 本地验证 | 剩余 blocker |
|--------|--------|---------------|----------|--------------|
| `Volta` | `R2 TaskOrder owner-slice implementation` | `partial`：`TaskOrder` shared-core evidence 现在有 `TaskOrderSharedCoreOwnerSlice`、`TaskOrderSharedCoreDirective`、`kTaskOrderSharedCoreOwnedSurface` 与 `task_order_shared_core_directive(...)`；没有新增 DTO shape，也没有扩宽 compatibility shell。 | 主线程复验：DTO shell guard `8 passed`；focused mission/tasking runtime `9 passed, 35 deselected`；`ef_py` 构建通过；`git diff --check` clean。 | `TaskOrder` flat aggregate shell、world-batch assignment shell、kernel/facade batch APIs、Python bindings 与 maintained Python/runtime callers 仍整包移动 `TaskOrder`；这只是 guard/evidence narrowing，不是 retirement。 |
| `Noether` | `R2 maintained-consumer fact check` | `blocked / read-only`：未改文件；源码锚点显示 maintained Python command-chain paths 仍 snapshot/assign 整包 `LeaderIntent` / `PilotReport` shell。 | 主线程在 diff-check 和本地验证后接受为 blocker evidence。 | `world_batch_vec_env.py`、`cooperative_world_batch_vec_env.py` 与 `command_chain_cache.py` 是最小下一步不冲突 implementation slice。`cooperative_director.py`、core batch/facade APIs 与 bindings 仍是更广义 blocker。 |

这些 packet 不完成 R2，也不授权 `WP22-F`、R4、DTO shell retirement 或 public escape-hatch deletion。

## R2 evidence 后的下一批有限派发

| Stream | 建议模型 / 推理预算 | 写入范围 | 派发包 |
|--------|---------------------|----------|--------|
| `R2 Python command-chain owner-slice sync` | `gpt-5.4`, xhigh | `python/rl/runtime/world_batch/command_chain_cache.py`、`python/rl/runtime/world_batch_vec_env.py`、`python/rl/runtime/cooperative_world_batch_vec_env.py` 与 focused world-batch command-chain sync tests。不要编辑 C++ tasking headers、DTO guard、runtime facade、command-link、R3 文件，除记录结果外不要改 docs。 | 尽可能把 `LeaderIntent` / `PilotReport` 的 whole-shell snapshot/assignment 语义替换为显式 owner-slice projection helpers。assignment wrappers 保持 transport-only。如果 Python bound APIs 缺少 owner-slice fields 或仍需要 whole-shell transport，就返回 `partial` 或 `blocked`。 |

## 第十八轮 R2 partial evidence

| Worker | Stream | Scoped result | 本地验证 | 剩余 blocker |
|--------|--------|---------------|----------|--------------|
| `Herschel` | `R2 Python command-chain owner-slice sync` | `partial`：Python command-chain snapshots 现在使用显式命名的 `LeaderIntent` / `PilotReport` owner-slice projection buckets，world-batch assignment writes 也收口到命名 compatibility transport projection helpers。 | 主线程复验：相关 runtime 文件 `py_compile` 通过；focused world-batch/cooperative command-chain tests `24 passed, 52 deselected`；focused mission/tasking tests `9 passed, 35 deselected`；`ef_py` 构建通过；`git diff --check` clean；WP22 closure audit 仍只有预期 missing-acceptance warning。 | 整包 `LeaderIntent` / `PilotReport` shell 仍作为 transport payload live。Python bindings 仍只暴露 flat shell，未暴露 `LeaderIntentCore` / `LeaderIntentAir` / `LeaderIntentNaval`、`PilotReportCore` / `PilotReportAir` / `PilotReportNaval` 或 bound owner-slice helper functions。`TaskOrder` Python whole-shell path 也仍开放。 |

这个 packet 不完成 R2，也不授权 `WP22-F`、R4、DTO shell retirement 或 public escape-hatch deletion。

## command-chain partial 后的下一批有限派发

| Stream | 建议模型 / 推理预算 | 写入范围 | 派发包 |
|--------|---------------------|----------|--------|
| `R2 Python binding owner-slice exposure` | `gpt-5.4`, xhigh | `src/interfaces/python/bindings_command.cpp`、focused binding/DTO guard tests，以及证明 owner-slice visibility 所需的最小 Python tests。不要编辑 runtime facade、command-link、R3 文件、public escape hatches 或 world-batch runtime APIs。 | 将现有 `LeaderIntent` / `PilotReport` owner-slice types 与 projection helpers 暴露到 Python；不能发明新 DTO shape，不能扩宽 compatibility shells。如果 nanobind 无法安全暴露 base-slice references，或 helper 暴露后 maintained callers 仍需要 whole-shell transport，就返回 `partial` 或 `blocked`。 |

## 第十九轮 R2 partial evidence

| Worker | Stream | Scoped result | 本地验证 | 剩余 blocker |
|--------|--------|---------------|----------|--------------|
| `Lovelace` | `R2 Python binding owner-slice exposure` | `partial`：Python 现在暴露 `LeaderIntentCore` / `LeaderIntentAir` / `LeaderIntentNaval`、`PilotReportCore` / `PilotReportAir` / `PilotReportNaval`，以及经 `nb::inst_reference(...)` 返回 live owner-slice view 的 `leader_intent_*` / `pilot_report_*` projection helpers。没有新增 DTO shape，也没有扩宽 flat shell。 | 主线程复验：`ef_py` build 通过；binding command surface `4 passed`；DTO shell guard `9 passed`；focused world-batch command-chain snapshot tests `2 passed, 46 deselected`；`git diff --check` clean；WP22 closure audit 仍只有预期 missing-acceptance warning。 | `LeaderIntent` / `PilotReport` flat shells 与 `WorldLeaderIntentAssignment` / `WorldPilotReportAssignment` 仍是 live compatibility transport。Python command-chain snapshot code 仍使用手工维护字段列表，而不是新绑定的 owner-slice helpers；`TaskOrder` Python whole-shell path 也仍开放。 |

这个 packet 解除 binding visibility blocker，但不完成 R2，也不授权 `WP22-F`、R4、DTO shell retirement 或 public escape-hatch deletion。

## binding visibility 后的下一批有限派发

| Stream | 建议模型 / 推理预算 | 写入范围 | 派发包 |
|--------|---------------------|----------|--------|
| `R2 Python command-chain bound owner-slice consumption` | `gpt-5.4`, xhigh | `python/rl/runtime/world_batch/command_chain_cache.py`、focused world-batch/cooperative command-chain tests，以及必要时最小 binding-surface assertions。不要编辑 C++ bindings、DTO headers、runtime facade、command-link、public escape hatches、R3 文件，除记录结果外不要改 docs。 | 尽可能把 `LeaderIntent` / `PilotReport` owner-slice snapshot 从手工维护字段列表改为消费新绑定的 `ef_py.leader_intent_*` 与 `ef_py.pilot_report_*` owner-slice helpers。assignment wrappers 保持 transport-only。如果 snapshot consumption 后 whole-shell transport 仍 live，则返回 `partial`；如果 helper consumption 不安全或需要扩宽 shell，则返回 `blocked`。 |

## 第二十轮 R2 partial evidence

| Worker | Stream | Scoped result | 本地验证 | 剩余 blocker |
|--------|--------|---------------|----------|--------------|
| `Peirce` | `R2 Python command-chain bound owner-slice consumption` | `partial`：`LeaderIntent` / `PilotReport` command-chain snapshots 现在消费 bound `ef_py.leader_intent_*` 与 `ef_py.pilot_report_*` owner-slice helper views，而不是本地手工维护字段 tuple。projection names 保持稳定，assignment wrappers 仍 transport-only。 | 主线程复验：`command_chain_cache.py` 的 `py_compile` 通过；focused world-batch/cooperative command-chain tests `24 passed, 52 deselected`；binding command surface `4 passed`；focused mission/tasking runtime `9 passed, 35 deselected`；`ef_py` build 通过；`git diff --check` clean；WP22 closure audit 仍只有预期 missing-acceptance warning。 | Whole-shell transport 仍通过 `WorldLeaderIntentAssignment` / `WorldPilotReportAssignment`、batch/facade APIs 与 maintained runtime/tasking construction paths live。`TaskOrder` Python owner-slice visibility/consumption 也仍开放。这是 helper-consumption evidence，不是 DTO shell retirement。 |

这个 packet 不完成 R2，也不授权 `WP22-F`、R4、DTO shell retirement 或 public escape-hatch deletion。

## R2-C 后的下一批并行派发

下一轮只在写入范围互不重叠时并行；不要让两个 writer 同时写 binding/command-chain
同一片文件。

| Stream | 建议模型 / 推理预算 | 写入范围 | 派发包 |
|--------|---------------------|----------|--------|
| `R2 TaskOrder Python owner-slice exposure` | `gpt-5.4`, xhigh | `src/interfaces/python/bindings_command.cpp`、`tests/runtime/bindings/test_bindings_command_surface.py`、`tests/architecture/test_wp22_dto_domain_shell_guard.py`，必要时最小 TaskOrder command-chain tests。不要和另一 writer 并行编辑 Python command-chain runtime files。 | 将现有 `TaskOrderCore` / `TaskOrderAir` / `TaskOrderNaval` owner slices 与 `task_order_*` projection helpers 暴露到 Python；不能发明 DTO shape，不能扩宽 compatibility shell。如果 whole-shell TaskOrder transport 仍 live，则返回 `partial`。 |
| `R2 residual whole-shell fact check` | `gpt-5.4-mini`, xhigh | 只读；touched files 必须是 `none` | 核验 Peirce 后 `TaskOrder`、`LeaderIntent`、`PilotReport` 与 assignment wrappers 的剩余 whole-shell paths。返回精确 file/line anchors，区分 compatibility-only 与 maintained truth，并给出最小不冲突 implementation slices。 |
| `WP22 readiness/documentation gate check` | `gpt-5.4-mini`, xhigh | 优先 docs/read-only；如需编辑，只能编辑 WP22 queue/remaining-task docs | 检查当前 queue 是否还残留已消费的 stale “next” rows，并汇总精确 closure blockers。不能宣称 `WP22-F` eligible；返回 docs-only sync patch 或 no-edit report。 |

## 第二十一轮 R2 partial/fact evidence

| Worker | Stream | Scoped result | 本地验证 | 剩余 blocker |
|--------|--------|---------------|----------|--------------|
| `Feynman` | `R2 TaskOrder Python owner-slice exposure` | `partial`：Python 现在暴露 `TaskOrderCore`、`TaskOrderAir`、`TaskOrderNaval`，live `task_order_shared_core` / `task_order_air_owner_slice` / `task_order_naval_owner_slice` views，以及 value-returning `task_order_*_directive` helpers。没有新增 DTO shape，也没有扩宽 `TaskOrder` compatibility shell。 | 主线程复验：`ef_py` build 通过；binding command surface `4 passed`；DTO shell guard `9 passed`；focused mission/tasking runtime `9 passed, 35 deselected`；focused world-batch/cooperative command-chain tests `24 passed, 52 deselected`；`git diff --check` clean；WP22 closure audit 仍只有预期 missing-acceptance warning。 | `TaskOrder` whole-shell command-chain snapshot 与 `WorldTaskOrderAssignment.order` transport 仍 live。这只是 binding visibility evidence，不是 TaskOrder shell retirement。 |
| `Kierkegaard` | `R2 residual whole-shell fact check` | `partial / read-only`：未改文件；确认 Peirce 与文档一致，并定位剩余 `TaskOrder` snapshot/transport path，以及 live `LeaderIntent` / `PilotReport` transport/facade/public binding paths。 | 主线程在本地复验和 `git diff --check` clean 后接受。 | 下一步非重叠 implementation slice 是 Python runtime files 中的 `TaskOrder` command-chain consumption。更广义 batch/facade/public binding transport retirement 仍在 scope 外，并继续阻塞 R2/WP22 closure。 |
| `Nash` | `R2 TaskOrder command-chain bound owner-slice consumption` | `partial`：`task_order_snapshot(...)` 现在消费 bound `task_order_shared_core`、`task_order_air_owner_slice` 与 `task_order_naval_owner_slice` helper views，不再通过 whole-shell `_bound_fields("TaskOrder")` reflection 取快照。projection names 保持稳定，也没有扩宽 compatibility shell。 | 主线程复验：`command_chain_cache.py` 的 `py_compile` 通过；focused world-batch/cooperative command-chain tests `25 passed, 52 deselected`；binding command surface `4 passed`；DTO shell guard `9 passed`；`git diff --check` clean；WP22 closure audit 仍只有预期 missing-acceptance warning。 | `WorldTaskOrderAssignment.order` 仍是 live transport，vec-env/cooperative assignment writes 仍携带 whole task-order shell，更广义 batch/facade/public binding transport 仍开放。 |
| `Beauvoir` | `WP22 readiness/documentation gate check` | `preflight-only`：未改文件；queue/remaining-task docs 中没有把 `partial` evidence 提升为 `pass`、`WP22-F`、R4、DTO shell retirement 或 public escape-hatch deletion 的 stale claim。 | 主线程在本地验证和 `git diff --check` clean 后接受；`wp_doc_closure_audit.py --wp WP22` 仍只报告 missing acceptance review。 | WP22 closure 继续被 R2 whole-shell transport、public compatibility escape hatches、default-factory projection 与 structural/binding debt 阻塞。 |

这些 packet 不完成 R2，也不授权 `WP22-F`、R4、DTO shell retirement 或 public escape-hatch deletion。

## R2-F 后的下一批并行派发

| Stream | 建议模型 / 推理预算 | 写入范围 | 派发包 |
|--------|---------------------|----------|--------|
| `R2 assignment transport owner-slice feasibility fact check` | `gpt-5.4-mini`, xhigh | 只读；touched files 必须是 `none` | 核验 `WorldTaskOrderAssignment.order`、`WorldLeaderIntentAssignment.intent` 与 `WorldPilotReportAssignment.report` 是否能用现有 owner-slice helpers 替换或收窄，且不发明新 DTO shape。返回 Python vec-env writes、C++ batch/facade setters/getters、Python public bindings 的精确 file/line anchors，并区分 compatibility-only transport、maintained truth 与 deletion-blocking public API。 |
| `R2 Python assignment write narrowing` | `gpt-5.4`, xhigh | `python/rl/runtime/world_batch/command_chain_cache.py`、`python/rl/runtime/world_batch_vec_env.py`、`python/rl/runtime/cooperative_world_batch_vec_env.py` 与 focused world-batch/cooperative tests。不要编辑 C++ contracts、C++ runtime facade、Python bindings、command-link、R3 文件，除记录结果外不要改 docs。 | 如果现有 assignment wrappers 必须保持 transport-only，就把所有 `TaskOrder`、`LeaderIntent` 与 `PilotReport` assignment writes 收口到命名 compatibility projection helpers，尽可能移除 vec-env 里的 direct whole-shell writes。如果底层 assignment payload fields 仍要求 whole shells，则返回 `partial`。 |

## 第二十二轮 R2 partial/preflight evidence

| Worker | Stream | Scoped result | 本地验证 | 剩余 blocker |
|--------|--------|---------------|----------|--------------|
| `Cicero` | `R2 Python assignment write narrowing` | `partial`：Python vec-env 与 cooperative assignment writes 现在都通过命名 compatibility transport helpers 写入 `TaskOrder`、`LeaderIntent` 与 `PilotReport`。`project_world_task_order_assignment_transport(...)` 已补到现有 intent/report helper 旁边，focused tests 也覆盖三类 helper path。 | 主线程复验：相关 runtime 文件 `py_compile` 通过；focused world-batch/cooperative command-chain tests `25 passed, 52 deselected`；binding command surface `4 passed`；focused architecture guards `27 passed, 20 deselected`；`git diff --check` clean；WP22 closure audit 仍只有预期 missing-acceptance warning。 | helper functions 仍写入 whole-shell payload 字段 `.order`、`.intent` 与 `.report`。这只移除了 vec-env inline writes，并未退场 `WorldTaskOrderAssignment`、`WorldLeaderIntentAssignment`、`WorldPilotReportAssignment`、batch/facade APIs 或 public bindings。 |
| `Hilbert` | `R2 assignment transport owner-slice feasibility fact check` | `preflight-only`：未改文件；确认剩余 deletion blockers 是 `world_batch_contracts.h` 里的 shell-shaped assignment fields、batch runtime setters/getters、runtime facade setters/getters、Python runtime bindings 与 public Python adapter shim。read-side owner-slice helpers 本身不足以形成可删除的 write-side public API。 | 主线程在同一组本地验证与 `git diff --check` clean 后接受。Hilbert 并行观察到 `TaskOrder` 缺少 write-side projector，这一点已被 Cicero 的 helper addition 覆盖；但更深层 blocker 仍存在：helper 仍因 public contract shape 未改变而传输 whole shell。 | 实际 shell retirement 需要 contract/API replacement 或 narrowing pass。`TaskOrder`、`LeaderIntent`、`PilotReport` 必须拆成串行切片处理，因为每个 family 都会触碰 `world_batch_contracts.h`、`world_batch_runtime.{h,cpp}`、`runtime_facade.{h,cpp}`、`bindings_runtime.cpp`、Python adapters 与 focused tests。 |

这些 packet 不完成 R2，也不授权 `WP22-F`、R4、DTO shell retirement 或 public escape-hatch deletion。

## assignment write narrowing 后的下一批串行派发

| Stream | 建议模型 / 推理预算 | 写入范围 | 派发包 |
|--------|---------------------|----------|--------|
| `R2 TaskOrder public contract replacement feasibility/implementation` | `gpt-5.4`, xhigh | `src/runtime/contracts/world_batch_contracts.h`、`src/core/engine/world_batch_runtime.{h,cpp}`、`src/runtime/facade/runtime_facade.{h,cpp}`、`src/interfaces/python/bindings_runtime.cpp`、`python/rl/runtime/world_batch/adapter.py`、`python/rl/runtime/world_batch/command_chain_cache.py`、`python/rl/runtime/world_batch_vec_env.py`、`python/rl/runtime/cooperative_world_batch_vec_env.py`、focused world-batch/runtime-facade/binding/DTO guard tests。除保持 shared compilation 外，不要在本切片编辑 `LeaderIntent` / `PilotReport` contract shapes。 | 先只处理 `TaskOrder`。判断是否存在 owner-slice-compatible assignment/setter/getter shape，能替换或收窄 `WorldTaskOrderAssignment.order`，且不发明 uncontrolled DTO truth。如果可行，实现最小兼容的 TaskOrder public contract replacement，并让 legacy shell transport 保持显式 quarantine。如果需要超出现有 owner slices 的新 public DTO/setter shape，必须停为 `blocked` 或 `partial`，给出精确 anchors 与 guard failures，不得扩宽 shell。 |

## 第二十三轮 R2 TaskOrder contract evidence

| Worker | Stream | Scoped result | 本地验证 | 剩余 blocker |
|--------|--------|---------------|----------|--------------|
| `Boyle` | `R2 TaskOrder public contract replacement feasibility/implementation` | `partial`：feasibility 是 `no`，仅靠现有 owner slices 不能直接替代公共 batch assignment/read shape。当前 public seams 仍硬编码 whole `TaskOrder` shell transport，因此 Boyle 只做 quarantine tightening：adapter-owned `set_task_order(...)` 现在通过 `project_world_task_order_assignment_transport(...)`，`WorldBatchRuntime::set_task_orders_batch(...)` 通过 `world_batch_assignment_compatibility_shell(item)` 消费 assignment，不再直接取 `.order`。 | 主线程复验：`ef_py` build 通过；focused world-batch/runtime tests `30 passed, 72 deselected`；binding command surface `4 passed`；focused architecture guards `18 passed, 29 deselected`；`git diff --check` clean；WP22 closure audit 仍只有预期 missing-acceptance warning。 | 真正的 TaskOrder shell retirement 仍被阻塞，直到项目定义出 owned maintained batch write/read contract：它需要组合现有 `TaskOrderCore` / `TaskOrderAir` / `TaskOrderNaval` slices，或提供显式的 maintained batch slice surfaces。现有 owner-slice projections 本身不是公共 assignment/read API。 |

这个 packet 不完成 R2，也不授权 `WP22-F`、R4、DTO shell retirement 或 public escape-hatch deletion。

## TaskOrder feasibility 后的下一批串行派发

| Stream | 建议模型 / 推理预算 | 写入范围 | 派发包 |
|--------|---------------------|----------|--------|
| `R2 TaskOrder maintained batch contract definition` | `gpt-5.4`, xhigh | 优先 design + guard-first edits：`src/runtime/contracts/world_batch_contracts.h`、`tests/architecture/test_wp22_dto_domain_shell_guard.py`、`tests/architecture/test_runtime_facade_layering.py`，仅在证明编译需要时添加最小 runtime/facade/binding declarations。避免编辑 `LeaderIntent` / `PilotReport` shapes。 | 定义受控的 TaskOrder maintained batch write/read contract shape，为后续替代或收窄 `WorldTaskOrderAssignment.order` 铺路。该 shape 必须组合现有 `TaskOrderCore` / `TaskOrderAir` / `TaskOrderNaval` owner slices，或拆成显式 slice surfaces，不能成为第二个 uncontrolled aggregate DTO。补充 guard，禁止把 `WorldTaskOrderAssignment.order` 当作 maintained truth。如果最安全结果是 design-only 或 blocked，就带精确 anchors 返回；不得扩宽 compatibility shells。 |

## 第二十四轮 R2 TaskOrder maintained contract evidence

| Worker | Stream | Scoped result | 本地验证 | 剩余 blocker |
|--------|--------|---------------|----------|--------------|
| `Hubble` | `R2 TaskOrder maintained batch contract definition` | `partial`：定义了受控的 `TaskOrderMaintainedBatchContract`，由现有 owner-slice directive surfaces 组合而成：`TaskOrderSharedCoreDirective`、`TaskOrderAir::RecoveryDirective`、`TaskOrderAir::TakeoffDirective` 与 `TaskOrderNaval::CommandAuthorityDirective`；同时新增 `WorldTaskOrderMaintainedAssignment` 与 projection/accessor helpers。`WorldTaskOrderAssignment::kMaintainedBatchTruth` 现在是 `false`，因此 `.order` 被明确标记为 compatibility transport only。 | 主线程复验：`ef_py` build 通过；focused architecture guards `20 passed, 29 deselected`；binding command surface `4 passed`；`git diff --check` clean；WP22 closure audit 仍只有预期 missing-acceptance warning。 | maintained contract 已定义，但尚未接入 runtime/facade/binding/Python write/read APIs。whole-shell public surfaces 仍存在于 `WorldBatchRuntime`、`RuntimeFacade`、`ObservationBatchPacket`、runtime bindings 与 `project_world_task_order_assignment_transport(...)`。 |

这个 packet 不完成 R2，也不授权 `WP22-F`、R4、DTO shell retirement 或 public escape-hatch deletion。

## maintained contract definition 后的下一批串行派发

| Stream | 建议模型 / 推理预算 | 写入范围 | 派发包 |
|--------|---------------------|----------|--------|
| `R2 TaskOrder maintained runtime/facade/binding API wiring` | `gpt-5.4`, xhigh | `src/core/engine/world_batch_runtime.{h,cpp}`、`src/runtime/facade/runtime_facade.{h,cpp}`、`src/interfaces/python/bindings_runtime.cpp`、`python/rl/runtime/world_batch/command_chain_cache.py`、`python/rl/runtime/world_batch/adapter.py`、`python/rl/runtime/world_batch_vec_env.py`、`python/rl/runtime/cooperative_world_batch_vec_env.py`、`tests/world_batch`、`tests/runtime/bindings` 与 architecture guards 中的 focused tests。不要编辑 `LeaderIntent` / `PilotReport` public contract shapes。 | 围绕 `WorldTaskOrderMaintainedAssignment` / `TaskOrderMaintainedBatchContract` 增加 maintained TaskOrder batch write/read APIs，同时保留旧 whole-shell APIs 为显式 compatibility-only surfaces。尽可能把 Python TaskOrder assignment helpers/callers 移到 maintained path。如果 maintained path 存在后 legacy whole-shell getters 或 `ObservationBatchPacket.task_orders` 仍必须 live，则返回 `partial`。本切片不得删除或扩宽 compatibility shells。 |

第一次尝试派发曾使用 default model routing，并已在被消费前关闭。那些 closed
threads 只是 transport cleanup，不是 completion evidence。

## 收尾轮派发

| Stream | 建议模型 / 推理预算 | 派发包 |
|--------|---------------------|--------|
| `WP22-F` | `gpt-5.4-mini`, xhigh | not eligible；`Poincare` shutdown 未返回 packet，且公开 compatibility escape hatches、DTO/factory/structural debt 仍开放 |

队列仍在等待 next implementation return packets，这不计为 closure evidence。

## Worker 返回包

每个 worker 必须返回：

- status：`pass`、`blocked`、`partial`、`timeout` 或 `preflight-only`；
- touched files；
- validation commands and outcomes；
- remaining legacy paths；
- blockers 以及暴露每个 blocker 的 failing guard；
- integration notes for the next stream；
- 确认未 revert unrelated edits。

## Return Packet Completeness Gate

worker return packet 只有在覆盖上面列出的全部必填字段，并且覆盖 stream-specific
dispatch packet 后，才算 complete。线程关闭本身不是完成证据。

状态含义如下：

- `pass`：packet complete，所有必填字段都存在，且没有命名 blocker。`pass` packet
  可以作为下一步 implementation 的 readiness evidence，但不能跳过后续 closure 或
  acceptance lane。
- `blocked`：worker 已识别出命名 blocker。packet 对失败原因的说明是完整的，但下游
  stream 仍保持 blocked，直到 blocker 有 owner、replacement 与 failing guard。
- `partial`：worker 返回了部分证据，但 packet 不完整，或只覆盖了部分 scope。
  `partial` 绝不解锁下游 implementation 或 acceptance。
- `timeout`：worker 在返回完整 packet 前停止。按需要记录为 `timeout` 或
  `blocked`，但绝不能把关闭的线程当作完成证明。`timeout` 绝不解锁下游
  implementation 或 acceptance。
- `preflight-only`：worker 仅限只读核验或 scope discovery。它可以建议下一步，但
  不能单独授权 implementation 或 acceptance。

规则：

- 只有完整的 `pass` packet 才能作为下一 stream 的 readiness evidence。
- `partial`、`timeout` 和 `preflight-only` 不能替代 completion state。
- 关闭 worker thread 是 transport event，不是 completion event。
- 已关闭的线程永远不能解锁下游 readiness 或 acceptance。

## WP22-B0 Return Packet Template

`WP22-B0 Python Source-Pass Verification` 除了通用 worker 要求外，还必须返回以下字段：

- `status`：`pass`、`blocked`、`partial`、`timeout` 或 `preflight-only`。
- `touched files`：必须是 `none`。
- `source anchors`：每个 Python bypass claim 对应的精确文件路径与行锚点。
- `rg commands`：用于验证每个 claim 的精确 `rg` 命令。
- `remaining blockers`：任何未解决的 bypass 或缺失证据。
- `WP22-B implementation allowed?`：必须明确给出 `yes` 或 `no`，并附简短理由。
- `integration notes`：下一 stream 应消费或避开的内容。

如果以上任意字段缺失或含糊不清，这个 packet 就是不完整的。`B0` 的
`timeout`、`partial`、`preflight-only` 或已关闭线程 packet 绝不授权
`WP22-B`。已完成的 `WP22-B0` packet 只授权 remediation implementation
dispatch，因为它返回的是 `blocked`，不是 `pass`。

## 停止规则

- 不得把 compatibility residual 标为 pass。
- 不得保留 silent default legacy behavior。
- 不得在 explicit compatibility allowlists 之外新增 raw runtime、loader 或 legacy command callers。
- 不得让多个并发 worker 编辑同一 normative table 或 runtime facade 行范围。
- 遇到 blocker 要停止并命名，而不是削弱 retirement gate。
- worker 超时时，stream 必须记录为 blocked 或 partial；不得标为 pass，也不得把线程关闭当作完成证据。
- 已关闭的线程永远不能解锁下游 readiness 或 acceptance。
