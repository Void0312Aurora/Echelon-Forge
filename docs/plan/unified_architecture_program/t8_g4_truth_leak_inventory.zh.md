# T8 G4 真值泄漏清单（2026-07-26）

语言：
- 英文正本：[t8_g4_truth_leak_inventory.md](t8_g4_truth_leak_inventory.md)
- 中文对照：`t8_g4_truth_leak_inventory.zh.md`

文档类型：`reference`
生命周期：`maintained`
正本：`docs/plan/unified_architecture_program/t8_g4_truth_leak_inventory.md`
归属：`unified architecture program workline`
最近核验：`2026-07-27`
基线提交：`dd292f4b`

状态：[统一架构计划](README.zh.md)的 T8（信息状态架构）登记册。它记录：(a) 维护面观测/奖励消费者普查；(b) G4 层声明机制的落地范围；(c) 策略路径上的 World Truth 直读，逐条裁定。参照
[SCAL 一致性普查](scal_conformance_census_20260720.zh.md)先例，本文为描述性登记册（`reference`）：不改变任何运行期行为。第一切片落地了 G4 声明机制（纯元数据加一个架构测试）并清点了真值泄漏，未关闭任何一条。**第二切片（§6，2026-07-21）** 在 TL13 读取 seam 上物化一个声明式观察视图，并将八个已声明消费者迁移到经其读取，从结构上收敛 11 条已声明泄漏；该迁移是把裸读纯机械地搬入一个带层标注的 owner，数值结果 bit-for-bit 不变。收敛一条泄漏意味着消费者不再读原始 World Truth：其读取经声明式视图 owner，并在此翻转其裁定。**第三切片（§7，2026-07-21）** 裁定并声明剩余五个推迟消费者（C11–C14、C19；TL14–TL16、TL20）：每个现携带 G4 声明（其信息状态层与语义阶段）。独立评审修复轮（§7.5）中，leader 观测产出者（C13）另被迁移到声明式视图——其本机读取与 `own_ship_field` 逐 token 同构，且与 fae17eb8 基线函数的逐元素数值 parity 由新聚焦测试钉住——将 TL15 翻转为*收敛*；C11/C12/C14/C19 按各自裁定保留读取（*已声明但未收敛*，宁缺毋滥）。声明为纯元数据（零行为变更）；C13 迁移为机械读取搬迁，parity 已钉住。**第四切片（§8，I60）** 把维护视图的声明变为运行期可查询的事实：C++ 运行期 facade 经 `RuntimeFacade::describe_maintained_observation_view` 导出该视图的*结构性声明*（view id + 产出/消费层 + 语义阶段），并由一致性门钉住到 Python 单一真源。这导出的是声明、不是数据——TL13 seam 的返回 bit 级不变；I60 落地时尚无消费者读取类型化 spec，I87 已接受切片是首个受限消费者。**第五切片（§9，I63）** 仅文档 + 测试：将本登记册对 I60 收账，并加固三个 G4 门之间的缝隙（一个"确经视图读取"正向门、一个清单↔代码漂移门、一个奖励面逃逸口扫描），同样零行为变更。**第六切片（§10，I76 + 本迭代记录的后续）** 关闭 §9.2 曾登记为开放的观测面逃逸口——I76 落地了逐文件维护真值读取者分类器及其门，后续则把该分类器钉为"声明待办"的两个 world-batch 消费者收账（声明为纯元数据；零行为变更）。

**第七切片（I87 已接受/落地，2026-07-27）** 刻意小于此前开放的完整类型化迁移：仅 C3/C20 消费既有 facade `ObservationViewSpec`。显式构造期 opt-in 从同一 facade 只读并结构准入一次；默认关闭时 describe 次数为零。空 required/optional 清单仅表示*结构性声明*，既不是 wildcard，也不是零字段。两个 Python `truth.x/y` 叶读改由高层注入的 `gym_envs.observation_view.own_ship_attr` reader 承担，而 opaque truth 对象仍原样传入编译内核。TL13 seam 与 `_ScenarioLoaderRuntimeProxy` 均不扩面。本段记录已接受/落地的受限切片。

全文使用的 G4 词汇即
[仿真系统架构设计](../architecture/simulation_system_architecture_design.md)§3 的权威六层信息状态集合，逐字沿用 `python/rl/runtime/world_batch/core.py` 中 I32 阶段契约白名单（由 `tests/world_batch/test_world_batch_core.py` 钉住）：World Truth、Sensed State、Track State、Shared Tactical Picture、Agent Observation、Decision Belief。

## 1. G4 声明机制（Python 侧）

核心不变量 G4（"每个观测/奖励消费者都声明其信息状态层"）在 Python 维护面上以轻量、零运行时开销的设施实现，沿用 T0 普查提出的机制（普查 §3）：

- **设施**：`python/architecture/information_layer.py` —— 一个中立、仅依赖标准库的模块（依赖方向 `gym_envs -> python.architecture <- python.rl`，与 `python.tasking_contracts` 对齐）。它发布权威层词汇（`AUTHORITATIVE_INFORMATION_LAYERS`）、规范 P0–P10 阶段词汇（`CANONICAL_SEMANTIC_STAGES`）、已声明消费者的 G5 注册表（`MAINTAINED_INFORMATION_LAYER_CONSUMERS`），以及可供未来 AST 门复用的共享校验器 `validate_information_layer_declaration`。
- **声明**：每个维护面消费者声明三个模块级常量 —— `INFORMATION_LAYER_CONSUMED`、`INFORMATION_LAYER_PRODUCED`、`SEMANTIC_STAGE` —— 均为权威字符串元组。它们是纯赋值（无每步或导入期开销），风格取自 I32 阶段契约声明与 `mission_obs_taxonomy` 的 OWNER 映射先例。
- **门**：`tests/architecture/information_state/test_g4_layer_declarations.py` 断言每个已注册消费者携带合法声明，双向交叉核对设施词汇与 I32 阶段契约白名单，并确认其覆盖 `core.py` 实际声明的每个层/阶段。白名单测试与 `core.py` 均通过静态 AST 解析读取、从不 import，故此门不依赖 `ef_py`/运行期，无需构建即可运行。声明提取器仅接受元组（列表字面量视为缺失声明）；门证明其可承载：摘掉、篡改或写成列表形式的声明均会变红。

第一切片交付声明 + 存在性门。**第二切片（§6）** 加入声明式观察视图 owner（`gym_envs/observation_view.py`）与 G4 预期的"禁止非诊断 World Truth 直读的 AST 门"（"执行从文档迁移到 AST 门"，设计文档 §15）：该门（`tests/architecture/information_state/test_g4_truth_read_ban.py`）禁止已迁移消费者的原始 World Truth 直读，白名单视图 owner 与显式诊断读取，由 §3 清单播种。

## 2. 维护面观测/奖励消费者普查

`gym_envs/**` 与 `python/rl/**` 面（以及 `tools/eval/**` 直读）上的每条维护面观测/奖励消费路径。"经声明视图？"记录该读取是否已经过声明视图/seam。

| # | 消费者 | 读取的数据面 | G4 层 | 经声明视图？ |
|---|--------|--------------|-------|--------------|
| C1 | `gym_envs/scenario_loader/mission_observation.py` —— Python 自持模式（`naval_screen_station_v1`、`air_combat_c2_roe_v1/v2`） | `truth.contacts`、`truth.missiles_remaining`、`truth.x/y`；support `get_agent_observation`/`get_unit_position`；support `get_unit_messages` | 消费 World Truth + Shared Tactical Picture；产出 Agent Observation | **本切片已收敛**（§6；经声明视图；原 V4 泄漏） |
| C2 | `gym_envs/scenario_loader/mission_observation.py` —— 编译模式（`basic`/`nav_v1`/`nav_v2`/…） | 由 `mission_command_view` + 航路引导编译 `ef_py.compute_mission_observation`（truth 传入） | 产出 Agent Observation（编译） | 编译 facade 路径；由 C1 模块声明覆盖 |
| C3 | `python/rl/runtime/world_batch/observation_batching.py` + `_observation_mixin.py` | `state.last_truth`/`state.last_inst`（truth/仪表缓存）、注入的本机 x/y reader、`inst.alt_baro` → 编译批 | 消费 World Truth（缓存）→ 产出 Agent Observation；P10 ObservationExport | **I87 已接受/落地**—— 默认关闭保持 I32 路径；opt-in 构造时只准入一次结构性 `ObservationViewSpec`，x/y 经高层声明视图 reader；opaque truth 仍作为 whole-object 内核输入；parity 与零裸叶读门已落地 |
| C4 | `gym_envs/scenario_loader/reward_runtime/air_combat.py` | `truth.missiles_remaining`；`sim.export_recent_engagement_events`；`sim.debug_get_aircraft_damage_state`/`debug_get_ground_contact_state`；`sim.is_unit_active` | 消费 World Truth；产出奖励 | **本切片已收敛**（§6；经声明视图；原 V5 泄漏） |
| C5 | `gym_envs/scenario_loader/reward_runtime/naval.py` | `truth.x/y`、`truth.contacts`；`sim.get_unit_position`/`get_agent_observation`（他体单位）；`sim.get_unit_messages` | 消费 World Truth + Shared Tactical Picture；产出奖励 | **本切片已收敛**（§6；经声明视图；原 V6 泄漏） |
| C6 | `gym_envs/scenario_loader/reward_runtime/safety.py` | 本机 `truth.health/z/pitch/speed` | 消费 World Truth；产出奖励输入 | **本切片已收敛**（§6；本机经声明视图读） |
| C7 | `gym_envs/scenario_loader/reward_runtime/shaping_inputs.py` | 本机 `truth.z/speed` + 仪表向量 | 消费 World Truth；产出奖励输入 | **本切片已收敛**（§6；本机经声明视图读） |
| C8 | `gym_envs/scenario_loader/reward_runtime/objectives.py` | 本机 `truth.z/health/heading/x/y/missiles_remaining`；目标 `truth.contacts`、`sim.is_unit_active`/`get_unit_health` | 消费 World Truth；产出奖励/目标输入 | **本切片已收敛**（§6；本机 + 目标经声明视图读） |
| C9 | `gym_envs/scenario_loader/reward_runtime/compiled_runtime.py` | 组装预构建输入 DTO；无直接信息层读取 | —（组装器，非直接消费者） | 不适用 —— 排除出注册表 |
| C10 | `gym_envs/scenario_loader/core.py::get_policy_agent_observation` / `get_policy_instrument_state` | `sim.get_agent_observation`/`get_instrument_state`（批路径上为 facade 背书代理） | World Truth 读取 seam 本身（V3） | 维护 seam；声明式观察视图（§6）从该 seam 的 `truth`/`sim` 输出读取；I87 已接受切片只在更高层 adapter 读取导出的结构性 spec，本 seam 不变 |
| C11 | `gym_envs/scenario_loader/step_evaluation.py` | 本机 `truth.x/y/z/vx/vy/vz/speed/pitch/roll/heading/health`；编排奖励面 | 消费 World Truth（本机）；跨阶段捆绑聚合器（V7）；P10 ObservationExport | **已声明（§7）**；读取保留（编排器捆绑 DTO，非叶读）—— 已声明但未收敛（TL14） |
| C12 | `gym_envs/scenario_loader/execution_runtime/mainline.py` | 本机 `truth.z/x/y/vx/vy`；编排执行步；奖励/观测经 loader | 消费 World Truth（本机）；执行步控制器；P10 ObservationExport | **已声明（§7）**；读取保留（编排器）—— 已声明但未收敛 |
| C13 | `gym_envs/leader_env_parts/decision_runtime/observations.py::build_observation` | 主要为 `inst.*`；本机 x/y 用于 ILS/跑道/锚点几何；nav 委派给 `get_mission_observation` | 消费 World Truth（位置）；产出 Agent Observation；P10 ObservationExport | **已收敛（§7.5 修复轮）**—— 本机读取经 `observation_view.own_ship_field`；受禁令门；parity 由 `tests/leader/test_leader_observation_view_parity.py` 钉住 |
| C14 | `python/rl/tasking/leader_tasking.py` | 多处 `get_policy_agent_observation`/`get_policy_instrument_state` | 消费 World Truth（本机）；脚本化 C2/leader 指挥（维护式条令）；P2 TaskingIntent + P3 CommandDelivery | **已声明（§7）**；禁止迁移（会引入 `python.rl`→`gym_envs` 反向依赖）—— 已声明但未收敛（TL16） |
| C15 | `tools/eval/waypoint_eval_utils.py`、`tools/eval/task_eval_driver.py` | `get_agent_observation`/`get_instrument_state` | eval 工具读取 | eval/诊断面 —— 维护策略路径之外 |
| C16 | `gym_envs/universal_env.py::UniversalEnv` 类构造函数 | — | 已降级的 fail-fast 壳（`__init__` 抛 `RuntimeError`） | 死路径 —— 无需声明。此处仅指被移除的原始内核环境，与其再导出的、仍活跃的 `build_universal_observation` 不同（见 C17）。 |
| C17 | `gym_envs/universal_env_parts/observations.py::build_universal_observation` —— 活跃的通用策略观测组装，由 `CooperativeWorldBatchVecEnv` 与 `MultiAgentWorldRuntimeView` 调用 | `truth.x/y`（ILS 查询）、`truth.contacts`、`truth.rwr_warnings`（Python 回退路径）；编译路径将 `truth` 传入 `ef_py.compute_execution_observation_runtime_numpy`；mission 向量委派给 `get_mission_observation` | 消费 World Truth；产出 Agent Observation | **本切片已收敛**（§6；经声明视图；修复轮加入） |
| C18 | `gym_envs/scenario_loader/navigation_runtime/waypoint_rewards.py::build_waypoint_step_state` —— 直接的航点奖励输入消费者，由 `step_evaluation.py`/`execution_runtime/mainline.py` 经 `loader._build_waypoint_step_state` 调用 | 本机 `truth.x/y`（到点距离与航路参考点）；构造 `ef_py.WaypointRewardInputs` | 消费 World Truth；产出奖励输入 | **本切片已收敛**（§6；本机经声明视图读；修复轮加入） |
| C19 | `gym_envs/scenario_loader/navigation_runtime/guidance.py` —— 共享航路引导几何辅助（`query_route_guidance_result`、`compute_waypoint_guidance_state`、`apply_waypoint_guidance_update` 等） | 本机 `truth.x/y/speed`（航路引导几何；`get_policy_agent_observation` 回退） | 消费 World Truth（本机）；跨越指令下发（P3/P4 自动驾驶目标）+ 奖励支撑（P10）；非单一面向 Agent Observation 的消费者 | **已声明（§7）**；迁移待一个指令/引导读取 owner（观察视图不是指令下发读取的正确 owner）—— 已声明但未收敛（TL20） |
| C20 | `python/rl/runtime/world_batch/_vec_env_support.py::_execution_instrument_vector` —— vec-env 执行观测支撑辅助（批路径上的逐 agent 仪表向量构建） | 注入的本机 x/y reader（ILS 查询）；opaque `truth` 随后传入 `ef_py.compute_execution_observation_runtime_numpy` | 消费 World Truth（缓存）；产出 Agent Observation；P10 ObservationExport | **I87 已接受/落地**—— 与 C3 共用构造期结构准入与默认关闭 parity；下层不新增 `gym_envs` owner import |

已收敛到声明式观察视图：C1、C4、C5、C6、C7、C8、C17、C18（第二切片 §6；C17/C18 于第一切片修复轮加入），另加 C13（第三切片修复轮 §7.5）。已声明但读取尚未收敛（位于 `DECLARED_DEFERRED_INFORMATION_LAYER_CONSUMERS`）：C11、C12、C14、C19（第三切片 §7）。I87 已接受切片通过注入 reader 与零裸叶读门把 C3/C20 移入收敛集合；权威状态为已接受/落地。`MAINTAINED_INFORMATION_LAYER_CONSUMERS` 仍为声明集合之并集。C3 此前仅由 I32 阶段契约记录为"已合规"，§10 先补齐模块级 G4 声明，I87 已接受切片再交付受限数据流试点。作为非消费者排除：C9。死路径：C16。维护策略路径之外：C15。

## 3. 真值泄漏清单

策略路径上的 World Truth 直读（策略/观测构建，或代表面向 Agent Observation 的消费者却读取 truth 的奖励）。裁定：**收敛** = 叶读现经声明式观察视图（§6）；**泄漏** = 仍需 T8 视图收敛（推迟）；**豁免** = 由声明/seam 合法化；**诊断** = 合法诊断用途（经视图的诊断面）。

| ID | 位置 | 读取 | 裁定 | 备注 |
|----|------|------|------|------|
| TL1 | `mission_observation.py::_air_combat_c2_roe_vector`（`_target_track`、`_truth_missiles_remaining`） | `truth.contacts`（目标距离/航迹龄/分类）、`truth.missiles_remaining` | **收敛**（声明视图） | V4（C1 CONSUMED World Truth）。2026-07-21 收敛（§6）：经 `observation_view.target_track` / `own_missiles_remaining` 读取，而非原始 `truth.contacts`/`truth.missiles_remaining`。 |
| TL2 | `mission_observation.py::_naval_screen_station_vector` | `truth.x/y`（本机）、`truth.contacts`（目标在场）；`runtime_view.get_agent_observation`/`get_unit_position`（support 单位） | **收敛**（声明视图） | V4（C1）。本机 `truth.x/y` 经 `observation_view.own_ship_field`；目标经 `target_track`；support 观测/位置经 `support_agent_observation`/`support_unit_position`（Shared Tactical Picture 面）。 |
| TL3 | `mission_observation.py::_naval_screen_station_vector` | `runtime_view.call_optional("get_unit_messages", support)`（报告链） | **豁免** | Shared Tactical Picture（C1）。现经 `observation_view.support_unit_messages_optional` 路由；链路分发报告仍为合法的声明层，非原始 truth。 |
| TL4 | `reward_runtime/air_combat.py::_truth_missiles_remaining`（`_air_combat_observed_release_count`、`_apply_release_shaping`） | `truth.missiles_remaining` | **收敛**（声明视图） | V5（C4）。经 `observation_view.own_missiles_remaining` 读取；本机弹量，低风险。 |
| TL5 | `reward_runtime/air_combat.py::_recent_engagement_events` / `_standard_damage_fact_projections` | `sim.export_recent_engagement_events()`（damage/lifecycle/consequence 事件） | **收敛**（声明视图） | V5（C4）。经 `observation_view.recent_engagement_events`（交战证据面）读取；`consumer_visibility == "diagnostics_only"` 过滤不变。 |
| TL6 | `reward_runtime/air_combat.py::_damage_consequence_snapshot`、`_ground_contact_terminal_state` | `sim.debug_get_aircraft_damage_state`、`sim.debug_get_ground_contact_state` | **诊断** | 显式 `debug_*` API，用于伤害后果塑形；现经 `observation_view.debug_aircraft_damage_state`/`debug_ground_contact_state`（视图的显式诊断面）路由。可接受的诊断用途。 |
| TL7 | `reward_runtime/air_combat.py::combat_entity_terminal_state` | `sim.is_unit_active(target)` | **收敛**（声明视图） | V5（C4）。经 `observation_view.unit_active`（交战证据面）读取；他体存活。 |
| TL8 | `reward_runtime/naval.py::_station_reward_terms` / `apply_naval_reward_surface` | `truth.x/y`（本机）、`truth.contacts`（目标）、`sim.get_unit_position(support)`、`sim.get_agent_observation(support)` | **收敛**（声明视图） | V6（C5）。本机 `truth.x/y` 经 `own_ship_field`；目标经 `naval_target_track`（naval 守卫变体，`target_id <= 0` 不强制转换）；support 位置/观测经 `support_unit_position`/`support_agent_observation`。 |
| TL9 | `reward_runtime/naval.py::_support_received_target_report` | `sim.get_unit_messages(support)`（报告链） | **豁免** | Shared Tactical Picture（C5）。现经 `observation_view.support_unit_messages` 路由；合法链路分发报告。 |
| TL10 | `reward_runtime/safety.py::build_safety_runtime_inputs` | 本机 `truth.health/z/pitch/speed` | **收敛**（声明视图） | C6。经 `observation_view.own_ship_field` 读取；本机自读，低风险。 |
| TL11 | `reward_runtime/shaping_inputs.py::build_flight_shaping_runtime_inputs` | 本机 `truth.z/speed` | **收敛**（声明视图） | C7。经 `observation_view.own_ship_field` 读取；本机自读，低风险。 |
| TL12 | `reward_runtime/objectives.py::build_conditional_objective_inputs`、`_combat_target_snapshot` | 本机 `truth.z/health/heading/x/y/missiles_remaining`；目标 `truth.contacts` 距离、`sim.is_unit_active`/`get_unit_health(target)` | **收敛**（声明视图） | C8。本机经 `own_ship_field`；目标 `truth.contacts` 经 `contacts`；`sim.is_unit_active`/`get_unit_health` 经 `unit_active`/`unit_health`。 |
| TL13 | `scenario_loader/core.py::get_policy_agent_observation` / `get_policy_instrument_state` | `sim.get_agent_observation`/`get_instrument_state`（批路径上为 facade 背书代理） | **豁免**（维护 seam） | V3。唯一的维护读取瓶颈；批路径上 `sim` 为 `_ScenarioLoaderRuntimeProxy`（facade 背书）。声明式观察视图（§6）从该 seam 的 `truth`/`sim` 输出读取。**已落地（§8，I60）：** 结构性声明经 C++ facade 导出并由一致性门钉住；I87 已接受切片只在 adapter 构造时为 C3/C20 消费该声明，seam 返回与 proxy 表面不变，故本裁定保持 *exempt-as-seam*。 |
| TL14 | `scenario_loader/step_evaluation.py`（`build_execution_runtime_state`、奖励输入组装） | 本机 `truth.x/y/z/vx/vy/vz/speed/pitch/roll/heading/health` | **已声明但未收敛**（本机，聚合器） | V7（C11）。2026-07-21 声明（§7）：CONSUMED World Truth，PRODUCED ()，阶段 P10 ObservationExport（I32 闭合；§7.5 修复中移除 P9）。读取保留、未收敛：跨阶段捆绑编排器，组装奖励/观测输入 DTO，非叶观测读取面。 |
| TL15 | `leader_env_parts/decision_runtime/observations.py::build_observation` | 本机 x/y（ILS/跑道/锚点几何） | **收敛**（声明视图；§7.5 修复轮） | C13。2026-07-21 声明（§7）：CONSUMED World Truth，PRODUCED Agent Observation，阶段 P10 ObservationExport。§7.5 修复轮收敛：本机读取经 `observation_view.own_ship_field`（对 `getattr(truth, "x"/"y", 0.0)` 的逐 token 同构替换）；受禁令门；与 fae17eb8 基线的逐元素 parity 由 `tests/leader/test_leader_observation_view_parity.py` 钉住（含无 x/y 默认值触发场景与视图缝损坏红证）。 |
| TL16 | `python/rl/tasking/leader_tasking.py`（多处） | `get_policy_agent_observation`/`get_policy_instrument_state` | **已声明但未收敛**（脚本指挥） | C14。2026-07-21 声明（§7）：CONSUMED World Truth，PRODUCED ()，阶段 P2 TaskingIntent + P3 CommandDelivery。裁定为维护式条令（脚本化 C2/leader 指挥合法消费本机 truth），非仅诊断。声明中立（`python.architecture`），但迁移会将 `python.rl` 读取经 `gym_envs.observation_view` 路由，引入 `python.rl`→`gym_envs` 反向依赖——禁止。 |
| TL17 | `tools/eval/waypoint_eval_utils.py`、`tools/eval/task_eval_driver.py` | `get_agent_observation`/`get_instrument_state` | **豁免**（eval 面） | eval/诊断工具，维护策略路径之外；非维护面泄漏。 |
| TL18 | `universal_env_parts/observations.py::build_universal_observation` | `truth.x/y`（ILS 查询）、`truth.contacts`、`truth.rwr_warnings`（Python 回退）；编译路径将 `truth` 传入 `ef_py.compute_execution_observation_runtime_numpy` | **收敛**（声明视图） | C17。叶读经 `observation_view.own_ship_attr` / `contacts` / `rwr_warnings`。编译路径仍将整个 `truth` 对象传入内核 —— 整体透传，非叶读；本切片不在范围内。 |
| TL19 | `navigation_runtime/waypoint_rewards.py::build_waypoint_step_state` | 本机 `truth.x/y`（到点距离、航路参考） → `ef_py.WaypointRewardInputs` | **收敛**（声明视图） | C18。本机 `truth.x/y` 经 `observation_view.own_ship_field`；引导辅助（C19/TL20）委派不变（推迟）。 |
| TL20 | `navigation_runtime/guidance.py`（`query_route_guidance_result`、`compute_waypoint_guidance_state`、`apply_waypoint_guidance_update` 等） | 本机 `truth.x/y/speed`（航路引导几何） | **已声明但未收敛**（本机） | C19。2026-07-21 声明（§7）：CONSUMED World Truth，PRODUCED ()，阶段 P3 CommandDelivery + P4 PlatformControl + P10 ObservationExport。共享辅助，跨越指令下发（自动驾驶目标）与奖励支撑；迁移待一个指令/引导读取 owner（观察视图不是指令下发读取的正确 owner）。 |

## 4. 裁定分布

| 裁定 | 数量 | 条目 |
|------|------|------|
| 收敛 —— 经声明式观察视图读取（§6；TL15 于 §7.5） | 12 | TL1、TL2、TL4、TL5、TL7、TL8、TL10、TL11、TL12、TL15、TL18、TL19 |
| 已声明但未收敛 —— G4 声明已落地（§7），读取尚未收敛 | 3 | TL14、TL16、TL20 |
| 豁免 —— 由声明/seam 合法化 | 4 | TL3、TL9、TL13、TL17 |
| 诊断 —— 合法诊断用途 | 1 | TL6 |

12 条历史收敛条目仍指既有消费者的叶读；I87 已接受切片另为 C3/C20 增加受限的注入 reader 路径。3 条"已声明但未收敛"为聚合器/指挥/引导路径（TL14、TL16、TL20），因 §7 裁定理由保留裸读。豁免/诊断读取（TL3、TL6、TL9、TL13、TL17）保持裁定。I60 导出的结构性声明现被 I87 已接受切片在 adapter 构造边界消费；TL13 seam 本身不变，更广泛类型化数据流仍是 §5 后续工作。

## 5. 后续切片（本切片未做）

- 在 I87 C3/C20 已接受切片之外继续完成观测*数据流*迁移。I60 已落地结构性导出，I87 消费该声明但不改变 TL13 返回或详细字段目录；让 seam 本身返回带字段的类型化视图、或退役 opaque `truth`/`sim` whole-object 传递，仍是由 WP4 协调的大型迁移，非本切片范围。
- 将已声明但未收敛的消费者（§7）按其裁定的阻断项收敛到视图：
  - C19（TL20）：构建一个指令/引导读取 owner（观察视图的对等物）承接指令下发读取，再将奖励支撑读取收敛到观察视图。
  - C11/C12（TL14）：当奖励/观测输入 DTO 组装能在不扰动编译运行时的前提下从视图取本机读取时，收敛聚合器的本机读取。
  - C14（TL16）：除非引入一个 `python.rl` 可达、且不产生 `python.rl`→`gym_envs` 边的中立读取 owner，否则保持仅声明。
- 随着这些"已声明但未收敛"消费者的收敛，扩展 G4 AST 真值直读禁令门：将每条从 `DECLARED_DEFERRED_INFORMATION_LAYER_CONSUMERS` 移入 `VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS`。该门已覆盖九个收敛消费者（§6 的八个加上 §7.5 的 C13 修复；`tests/architecture/information_state/test_g4_truth_read_ban.py`），且每个此类消费者另被要求确经视图读取（§9.2）。
- ~~把奖励面逃逸口扫描（§9.2）扩展到观测面。~~ **已落地（§10，I76 + 本迭代后续）。** 本条所要求的逐文件分类器已存在（`python/architecture/consumer_classification.py`），其门（`tests/architecture/information_state/test_g4_consumer_classification.py`）AST 扫描整个 `gym_envs/**` + `python/rl/**` 面——§9 `reward_runtime/**` 目录扫描的严格超集——并对每个裸 World-Truth 读取者做逐文件分类，因此合法的非消费者读取者（指令 / 动作 / 场景装载 / 行为路径——例如 `leader_env_parts/decision_runtime/commands.py`、`universal_env_parts/air_combat_event_action.py`、`scenario_loader/loading.py`、`scenario_loader/behavior_runtime/post_waypoint_transition.py`）不再误报：每个都带一条经评审的分类行。分类器最初钉为"声明待办"的两个 world-batch 消费者已在后续（§10）收账：两者现均携带 G4 声明并登记为已声明但未收敛。

## 6. 第二切片：声明视图收敛（2026-07-21）

第二个 T8 切片在 TL13 读取 seam 上物化一个声明式观察视图，并将八个已声明消费者迁移到经其读取，从结构上收敛 11 条已声明泄漏（TL1、TL2、TL4、TL5、TL7、TL8、TL10、TL11、TL12、TL18、TL19）。它是纯机械搬迁：每个视图函数执行与消费者迁移前完全相同的底层读取（同一函数/属性、同一参数、同一顺序），故观测与奖励结果 bit-for-bit 不变。

### 6.1 视图 owner 与门

- **视图 owner**：`gym_envs/observation_view.py` —— 一个依赖终端、仅依赖标准库的读取 owner（G2 中立叶节点），位于 `gym_envs` 父包层——两个消费者子包的公共下层（按 G2"共享需求下沉、绝不横向"；`universal_env_parts` 对 `scenario_loader` 保持零横向导入）。它暴露带层标注的读取面：本机 World Truth（`own_ship_field` / `own_ship_attr` / `own_missiles_remaining`）、Track State（`contacts` / `rwr_warnings` / `target_track` / `naval_target_track` —— mission-observation 与 naval 两个航迹查找守卫变体作为独立面保留，以保真）、Shared Tactical Picture（`support_agent_observation` / `support_unit_position` / `support_unit_messages` / `support_unit_messages_optional`）、交战证据（`recent_engagement_events` / `unit_active` / `unit_health`），以及显式诊断读取（`debug_aircraft_damage_state` / `debug_ground_contact_state`）。它在调用时动态查找每个属性/方法、在 import 期不绑定任何东西，故 loader / `sim` / `get_policy_agent_observation` 的 monkeypatch 缝仍可工作。
- **禁令门**：`tests/architecture/information_state/test_g4_truth_read_ban.py` 禁止已迁移消费者的原始 World Truth 直读（`truth.<attr>` / `getattr(truth, ...)`），白名单视图 owner 与显式诊断标注读取，并带可承载的负向自证（注入一个裸读即变红）。注册：`python/architecture/information_layer.py` 中的 `MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS` / `VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS`。

### 6.2 各消费者 读取 → 视图面 迁移

| 消费者 | 裸读（之前） | 声明视图面（之后） |
|--------|--------------|--------------------|
| C1 `mission_observation` | 本机 `truth.z/heading/speed/x/y`；`truth.contacts`（经 `_target_track`）；`truth.missiles_remaining`；support `get_agent_observation`/`get_unit_position`/`call_optional("get_unit_messages")` | `own_ship_field`；`target_track`；`own_missiles_remaining`；`support_agent_observation`/`support_unit_position`/`support_unit_messages_optional` |
| C4 `air_combat` | `truth.missiles_remaining`；`sim.export_recent_engagement_events()`；`sim.is_unit_active`；`sim.debug_get_aircraft_damage_state`/`debug_get_ground_contact_state` | `own_missiles_remaining`；`recent_engagement_events`；`unit_active`；`debug_aircraft_damage_state`/`debug_ground_contact_state` |
| C5 `naval` | 本机 `truth.x/y`；`truth.contacts`（经 `_target_track`）；`sim.get_unit_position`/`get_agent_observation`/`get_unit_messages` | `own_ship_field`；`naval_target_track`（naval 守卫变体）；`support_unit_position`/`support_agent_observation`/`support_unit_messages` |
| C6 `safety` | 本机 `truth.health/z/pitch/speed` | `own_ship_field` |
| C7 `shaping_inputs` | 本机 `truth.z/speed` | `own_ship_field` |
| C8 `objectives` | 本机 `truth.z/health/heading/x/y/missiles_remaining`；目标 `truth.contacts`；`sim.is_unit_active`/`get_unit_health` | `own_ship_field`；`contacts`；`unit_active`/`unit_health` |
| C17 `universal observations` | `truth.x/y`；`truth.contacts`；`truth.rwr_warnings` | `own_ship_attr`；`contacts`；`rwr_warnings` |
| C18 `waypoint_rewards` | 本机 `truth.x/y` | `own_ship_field` |

### 6.3 推迟项（本切片保持原样，附理由）

- **编译整体透传。** C17 的编译路径将整个 `truth` 对象传入 `ef_py.compute_execution_observation_runtime_numpy(inst, truth, …)`。这是向编译内核的整体对象透传，非叶字段读取，故不在本读取收敛切片范围内，保持不变（见 TL18 备注）。
- **推迟消费者（待裁定）。** `step_evaluation.py`（C11/TL14）、`execution_runtime/mainline.py`（C12）、leader 路径（`leader_env_parts/decision_runtime/observations.py` C13/TL15、`python/rl/tasking/leader_tasking.py` C14/TL16），以及共享航路引导辅助（`navigation_runtime/guidance.py` C19/TL20）不迁移：其认知层仍待裁定，故按宁缺毋滥保持不动。
- **报告链 / 诊断读取。** TL3/TL9（报告链）与 TL6（`debug_*`）本已豁免/诊断，非泄漏；为一致性经视图的 Shared Tactical Picture 与诊断面路由，但保持裁定。

### 6.4 验证（零行为变更）

- `tests/architecture/information_state` —— 26 passed（原 14；+12 为新禁令门：8 个各消费者无裸读用例 + 视图 owner 声明 + 可承载负证 + 诊断标注白名单 + owner 排除）。
- 目标消费者集成测试前后一致：60 passed、15 subtests passed、4 failed —— 4 个失败为 `python/rl/runtime/cooperative_world_batch_vec_env.py` 中既有的 NumPy `asarray(copy=)` 本机红（不在范围内），分布于 `tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py`、`tests/runtime/air_combat/test_air_combat_reward_surface.py`、`tests/runtime/naval/test_naval_station_policy_surface.py`、`tests/runtime/execution/test_scenario_loader_execution_step_runtime.py`。
- `tests/runtime/mission` + `tests/world_batch` + `tests/runtime/engagement` 前后一致：255 passed、8 subtests passed、4 个 `stable_baselines3` 收集错误（本机基线）。

这些集成测试经真实内核断言精确的观测向量字段与奖励总额，故其不变的通过集合即本迁移的数值 parity 证据。

### 6.5 独立评审修复（2026-07-21）

本切片的独立评审给出 needs-repair，两项发现均于当日就地修复（§6.4 全部门重跑，结果一致）：

- **P1 —— C5 守卫漂移（行为）。** 首版让 C5（`naval.py`）复用共享 `target_track` 面，其守卫为 mission-observation 变体（`int(target_id) <= 0`）；而 naval 原实现的守卫是 `target_id <= 0`（无强制转换）。两个变体在非整数输入上分歧——转换次数、异常传播、边界结果（例如 `target_id=0.5` 且存在 `id=0` 航迹时，naval 守卫返回该航迹而强转守卫返回 `None`；字符串 id 在 naval 守卫下抛 `TypeError` 而在强转守卫下可匹配）。视图现单列 `naval_target_track` 面，逐 token 复刻 naval 原实现（与基线 `1d25c4d1` AST 函数体全等，两个评审场景探针实证），C5 委派给它。C1 变体已对照其自身原实现审计，逐 token 一致；其余读取面复查无"顺手规范化"（无发现——强制转换均留在调用点）。
- **P2 —— G2 横向导入（分层）。** 视图 owner 首版位于 `gym_envs/scenario_loader/observation_view.py`，使 C17 迁移新增了 `universal_env_parts -> scenario_loader` 的同级横向导入（基线为零）。owner 现下沉到父包层 `gym_envs/observation_view.py`——两个消费者子包的公共下层（G2：共享需求下沉、绝不横向）——八个消费者导入、注册表 owner 路径、禁令门报错文案与本登记册随动更新；旧路径不留任何文件或 shim。

## 7. 第三切片：推迟消费者的裁定与声明（I56，2026-07-21）

第三个 T8 切片为前两切片留作待裁定的五个消费者（C11–C14、C19；TL14–TL16、TL20）关闭 §5 的"裁定并声明推迟路径"事项。每个获得认知层裁定与 G4 声明（三个模块级常量）。声明为纯元数据（零行为变更；五消费者行为测试集前后 bit 一致）。独立评审修复轮（§7.5）中，C13——唯一读取与既有视图面逐 token 同构的消费者——另被迁移到视图并配以新的钉住式 parity 测试，将 TL15 翻转为*收敛*；其余四个按 §7.3 保留读取（宁缺毋滥：仅当读取零风险且携带对基线函数的逐元素数值 parity 证据时才搬迁）。

### 7.1 各消费者裁定

| 消费者（TL） | CONSUMED | PRODUCED | SEMANTIC_STAGE | 裁定 | 是否迁移 | 理由 |
|--------------|----------|----------|----------------|------|----------|------|
| C11 `step_evaluation`（TL14） | World Truth | () | P10 ObservationExport | 已声明但未收敛 | 否（仅声明） | 跨阶段捆绑聚合器：其本机读取喂给奖励/观测输入 DTO 组装，非叶观测面。编排器只声明不迁移。阶段按 I32 闭合（§7.5 P2 修复：移除 P9——它读取伤害事实，不产出效果）。 |
| C12 `execution_runtime/mainline` | World Truth | () | P10 ObservationExport | 已声明但未收敛 | 否（仅声明） | 执行步控制器（奖励/终止/状态 + 战斗终局 / 伤害后果覆盖）。编排器；声明，不迁移。阶段按 I32 闭合（§7.5 P2 修复：移除 P9——覆盖逻辑读取的是已产出的伤害/存活事实）。 |
| C13 `leader .../observations::build_observation`（TL15） | World Truth | Agent Observation | P10 ObservationExport | 收敛 | **是（§7.5 修复轮）** | 干净的 Agent-Observation 产出者，其本机 x/y 读取与 `observation_view.own_ship_field` 逐 token 同构（即已迁移的 C17/C18 形态）。已按机械 `own_ship_field` 搬迁迁移；与 fae17eb8 基线的逐元素 parity 由 `tests/leader/test_leader_observation_view_parity.py` 钉住；已进禁令门扫描集。 |
| C14 `python/rl/tasking/leader_tasking`（TL16） | World Truth | () | P2 TaskingIntent、P3 CommandDelivery | 已声明但未收敛 | 否（禁止迁移） | 裁定为**维护式条令**（脚本化 C2/leader 指挥合法消费本机 truth 以编写任务意图与指令），非仅诊断。声明中立（`python.architecture`），但迁移会将 `python.rl` 读取经 `gym_envs.observation_view` 路由，引入 `python.rl`→`gym_envs` 反向依赖——禁止。 |
| C19 `navigation_runtime/guidance`（TL20） | World Truth | () | P3 CommandDelivery、P4 PlatformControl、P10 ObservationExport | 已声明但未收敛 | 否（需指令 owner） | 混合指令/奖励辅助：其本机读取同时喂给自动驾驶指令目标（指令下发）与航点奖励支撑。观察视图不是指令下发读取的正确 owner，故迁移待一个独立的指令/引导读取 owner。 |

备注：
- **阶段。** 语义阶段遵循代码库权威用法（`python/rl/runtime/world_batch/core.py` 中的 I32 阶段契约）：奖励与观测构建均闭合在 P10 ObservationExport（`observation_build` 与 `reward_episode` 均声明 P10；`reward_episode` 额外的 P1 WorldSetup 仅覆盖回合自动重置子阶段，其位于 vec env 而非 C11/C12）；任务意图/行为在 P2、指令下发在 P3、平台控制在 P4。I32 批步没有任何阶段或子阶段声明 P9 EffectsDamage——P9 是内核效果/伤害系统的*产出*阶段，而 C11/C12 只读取已产出的伤害事实——故聚合器仅声明 P10（§7.5 P2 修复；首版多声明了 P9，已纠正）。
- **PRODUCED。** 奖励输入、任务/指令产物与引导/指令目标都不是信息层，故这些消费者声明 `PRODUCED = ()`；仅 C13（观测产出者）声明 `Agent Observation`。

### 7.2 注册表与门变更

- `python/architecture/information_layer.py`：维护注册表拆分为 `VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS`（受禁令门；八个 §6 消费者，另加 §7.5 修复轮起的 C13——共九个）与新的 `DECLARED_DEFERRED_INFORMATION_LAYER_CONSUMERS`（仅受声明门；C11、C12、C14、C19——共四个）。`MAINTAINED_INFORMATION_LAYER_CONSUMERS` 现为二者并集（13 个消费者）。
- 声明门（`test_g4_layer_declarations.py`）：现对全部 13 个维护消费者参数化（含五个新声明），并新增分区测试（收敛 ∩ 推迟 = ∅；并集 = 维护集）。
- 禁令门（`test_g4_truth_read_ban.py`）：扫描集扩展到九个收敛消费者（§7.5 加入 C13），并新增可承载测试：每个已声明但未收敛消费者被排除出扫描*且仍执行裸 truth 读取*——故推迟为真，将来收敛某一个（移除其裸读）会强制将其移入收敛的、受禁令门的集合。
- 新 parity harness：`tests/leader/test_leader_observation_view_parity.py`（§7.5）在合成场景上将 C13 的输出与 fae17eb8 基线函数逐元素钉住，并经视图缝损坏红证证明读取确经视图流动。

### 7.3 迁移结果

C13 已迁移（§7.5）：其本机 x/y 读取与 `own_ship_field` 逐 token 同构（正是 C17/C18 形态），模块无需 `stable_baselines3` 即可导入，且缺失的数值 harness 被直接补建而非等待——新聚焦测试在合成输入（含无 x/y 默认值触发场景）上将 `build_observation` 输出与经 `git show` 提取的 fae17eb8 基线函数逐元素钉住，另有一次性双跑对照在相同场景上确认基线与迁移版逐元素全等。其余四个保留读取：C11/C12 为编排器（设计上仅声明——其读取喂给输入 DTO 组装，非叶观测面），C14 的迁移被 `python.rl`→`gym_envs` 反向依赖规则阻断，C19 需先有指令/引导读取 owner（观察视图不是指令下发读取的正确 owner）。

### 7.4 验证（零行为变更）

- `tests/architecture/information_state` —— 37 passed（原 26；为新消费者 +5 声明参数化、+1 注册表分区测试、+4 已声明但未收敛禁令排除参数化、+1 已迁移 C13 的禁令扫描参数化）。
- 新 parity harness `tests/leader/test_leader_observation_view_parity.py` —— 3 passed（两个基线钉住场景 + 视图缝红证）；损坏视图面会使钉住变红（可承载证据，§7.5）。
- 五消费者行为集（`tests/leader`、`tests/runtime/execution`、`tests/runtime/mission`、`tests/runtime/navigation`，比对时排除新 parity 文件以保持集合同一）前后一致：179 passed、234 subtests passed、1 收集错误（`tests/leader/test_leader_runtime_control_contracts.py`；`stable_baselines3` 缺失——本机基线）。
- 声明不新增导入、不新增逻辑；C13 迁移仅搬迁本机叶读（parity 如上钉住）。

### 7.5 独立评审修复（2026-07-21）

本切片的独立评审给出 needs-repair，两项发现均于当日就地修复（§7.4 全部门重跑）：

- **P1 —— C13 推迟依据不实（裁定）。** 首版以"leader 环境数值 parity 测试受 `stable_baselines3` 阻断"为由推迟 C13 迁移。评审证伪：仓库没有任何数值测试覆盖 `build_observation`（唯一 SB3 收集错误来自从不调用该函数的 runtime-control 测试），且该模块无 SB3 也可干净导入。修复：C13 已迁移到声明式视图（即裁定本已称"迁移就绪"的机械 `own_ship_field` 搬迁），并且*缺失的 harness 被直接补建*——`tests/leader/test_leader_observation_view_parity.py` 在对 x/y 敏感的合成场景（含无 x/y 默认值触发场景）上将输出与 fae17eb8 基线函数逐元素钉住，并经视图缝损坏红证证明钉住可承载。一次性双跑（基线模块经 `git show` exec、迁移版直接 import）确认输出逐元素全等，且损坏 `own_ship_field` 会使二者分歧。TL15 翻转为*收敛*；注册表将 C13 移入受禁令门的收敛集（9/4 拆分）。
- **P2 —— C11/C12 多声明了 P9 EffectsDamage（阶段闭合）。** 首版将聚合器声明为 P9+P10。`python/rl/runtime/world_batch/core.py` 的 I32 阶段契约把奖励与观测组装闭合在 P10（`observation_build` P10；`reward_episode` P10 + 仅限自动重置的 P1；连事件驱动的 `post_launch_assessment` 子阶段也只声明 P4/P5/P10），且全文没有任何阶段声明 P9——P9 是内核效果/伤害系统的产出阶段，而 C11/C12 只*读取*已产出的伤害事实。修复：两者 `SEMANTIC_STAGE` 现均为 `("P10 ObservationExport",)`；§7.1 矩阵、§2 普查行与 TL14 备注随动更正。

## 8. 第四切片：观察视图结构性事实导出（I60，2026-07-21）

第四个 T8 切片把"维护面观察视图声明了什么"变为运行期可查询的事实：将视图的*结构性声明*从 C++ 运行期 facade 镜像出来，但不迁移任何观测数据流。它关闭 §5 类型化导出事项中"声明只活在 Python"的那一半：结构性声明现已导出并受一致性门钉住；类型化*数据流*迁移仍开放（§5）。这导出的是声明、非数据——它不是收敛，不改变任何裁定（TL13 保持 *exempt-as-seam*）。

### 8.1 导出

- `RuntimeFacade::describe_maintained_observation_view()` 是一个只读 `const` 方法，返回一个 `ObservationViewSpec` DTO，承载维护视图的结构性事实，镜像自 Python 单一真源（`gym_envs/observation_view.py` 的 G4 声明）：`view_id = "gym_envs.observation_view"`、`information_layer_produced = ("Agent Observation",)`、`information_layer_consumed = ("World Truth", "Track State", "Shared Tactical Picture")`、`semantic_stage = ("P10 ObservationExport",)`。
- **单一真源策略。** 只有*结构性事实*被镜像进 C++。详细观测字段目录保持 Python 自持——导出的 `required_fields` / `optional_fields` 刻意留空——故不存在会漂移的双源字段清单。
- **写集（I60）。** 声明 `src/runtime/facade/runtime_facade.h`；实现 `src/runtime/facade/runtime_facade_query.cpp`；绑定 `src/interfaces/python/bindings_runtime.cpp`；DTO 模式 `src/runtime/contracts/detail/observation_view_spec.inc`（及其生成的 builder/schema）；以及 `python/architecture/information_layer.py` 中的可选一致性辅助（`read_maintained_observation_view_export`、`observation_view_export_parity_violations`、`OBSERVATION_VIEW_EXPORT_LAYER_ATTRS`；既有元组 `MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS`——由 §6 视图切片（I50）新增——为 I60 所复用、非新增）。这些辅助把 `ef_py` import 保持在函数内，故 `information_layer.py` 在导入期仍仅依赖标准库，AST G4 门无需构建即可运行。

### 8.2 一致性 + 受限接线门

`tests/architecture/information_state/test_g4_observation_view_export.py`：

- **导出一致性（单一真源）。** C++ 导出与 Python 注册表声明逐项相等（含顺序），且仅用权威六层 / P0–P10 词汇。纯一致性校验器（`observation_view_export_parity_violations`）可承载：在每个被镜像维度注入漂移都会变红。
- **确定性。** 导出是纯常量产出者——跨重复调用、跨不同 world 数的 facade 均一致——故不读任何 facade 实例状态，不会与运行行为耦合（或扰动）。
- **受限接线。** 没有维护 C++ 路径或 `gym_envs`/TL13 consumer 调用导出；I87 已接受切片仅在 `RuntimeFacadeAdapter` 构造期增加一个 Python call site。默认关闭时 describe 为零次，opt-in 从同一 facade 只读一次并缓存结构性准入结果。
- 依赖 `ef_py` 的一致性/取值测试在无本地构建时跳过（沿用仓库约定）；可承载与接线边界测试为纯文本/AST，始终运行。

### 8.3 范围边界（导出不等于迁移）

导出是结构性声明、非字段目录。TL13 保持 **豁免（维护 seam）**：seam 仍返回原始 `truth`/`sim`。I87 已接受切片为 C3/C20 准入该声明并注入既有 §6 reader；更广泛类型化字段流仍在 §5 开放清单。

## 9. 第五切片：登记册收账与门网加固（I63，2026-07-26）

第五个 T8 切片仅文档 + 测试——零行为变更，不动 `gym_envs/**` 生产代码、不动 C++。它 (a) 将本登记册对 I60 导出收账，并 (b) 加固三个 G4 门（声明、真值直读禁令、导出一致性）*之间*的缝隙，新增三项，均为纯测试。

### 9.1 登记册收账

TL13 行、§4 收尾备注与 §5 此前带 I56 时代措辞，将"把 seam 返回变为声明式 `ObservationViewSpec` 导出"列为待办。它们现记录 I60 为已落地（结构性声明已导出并受一致性门钉住），并把剩余工作重新界定为类型化*数据流*迁移（§5）加上观测面逃逸口残留（§5）。无泄漏裁定变化：I60 导出的是声明，故普查（§4）不变。

### 9.2 门网加固（三个门之间的缝隙）

声明门证明每个维护消费者*声明*了合法层；禁令门证明每个收敛消费者*无裸读*；导出门把 *C++ 镜像*钉到 Python 声明。三处缝隙位于它们之间，现各自关闭（或明确登记为开放）：

| 既有门之间的缝隙 | 处置 | 位置 |
|------------------|------|------|
| 消费者*已声明*且*无裸读*，但无任何东西证明它确实经视图读取（它可能经后门读取、或根本不读，仍能空洞地通过禁令门） | **已关闭**——正向视图使用门：每个 `VIEW_CONVERGED` 消费者必须导入视图 owner 且引用至少一个面 | `test_g4_truth_read_ban.py::test_view_converged_consumer_reads_through_the_declared_view`（参数化 ×9）+ `test_view_usage_gate_is_load_bearing` |
| 维护登记册（§2 消费者普查、§6 面清单）可能与代码注册表及视图公共面漂移 | **已关闭（仅代码→文档方向）**——清单↔代码门：每个已注册消费者 + owner 都在双语登记册中被记录（以其 `a/b/c.py` 路径）；`observation_view.__all__` 等于其公共面加三个声明常量；每个公共面在双语登记册中均须由其自身的**词边界**提及被记录（更长的别名不算：`naval_target_track` 不能充当 `target_track` 的记录，`support_unit_messages_optional` 亦不能充当 `support_unit_messages` 的记录）。文档→代码方向未强制：陈旧的登记行（其消费者已从代码注册表移除、其面已从视图删除）——或凭空捏造、指向从未存在代码的登记行——不会使该门变红 | `test_g4_inventory_consistency.py`（5 个测试，含两次可承载排演） |
| 禁令门只扫*已注册*消费者；新增未注册的奖励消费者若落到 `reward_runtime/` 且带裸读会溜过它 | **对 `reward_runtime/**` 已关闭**——目录逃逸口扫描：其中任何带裸 truth 读取的文件必须是已注册维护消费者（或视图 owner） | `test_g4_truth_read_ban.py::test_no_unregistered_reward_consumer_performs_raw_truth_reads` + `test_reward_consumer_escape_hatch_scan_is_load_bearing` |
| *观测*面（`mission_observation`、`universal_env_parts`、`leader_env_parts`、`navigation_runtime` 等）上的同类逃逸 | **已关闭（§10，I76 + 后续）**——本切片当时为*开放（登记于 §5）*：那些目录混入合法的非消费者 World-Truth 读取者（指令 / 动作 / 装载 / 行为路径），故目录级扫描会误报。I76 逐文件分类器将其关闭：整个 `gym_envs/**` + `python/rl/**` 面上的每个裸 truth 读取者都带一条经评审的逐文件分类行，双向强制（未注册读取者变红；陈旧行变红），且凡存在 G4 声明处，分类由该声明者的 `SEMANTIC_STAGE` 结构性钉住 | `test_g4_consumer_classification.py`（见 §10） |

每个新门都带一次内存内可承载排演（对某真实模块的副本做变异并断言检查翻红），故非空洞变绿；工作树从不被修改。

### 9.3 验证（零行为变更）

- `tests/architecture/information_state` —— 有本地构建时 61 passed（I60 后原为 44；本切片 +17：+9 参数化正向视图使用 + 1 可承载、+2 奖励逃逸口扫描、+5 清单↔代码一致性）。无构建时四个 `ef_py` 导出一致性测试跳过，故计数为 57 passed + 4 skipped（原为 40 + 4）。既有声明 / 禁令 / 导出一致性断言不变、仍绿。
- 不触碰任何 `gym_envs/**` 或 C++ 文件；所有新增均为纯 AST/文本门加上本登记册刷新。双语哈希治理门会因本登记册被编辑而变红，直到重新生成簇哈希；该刷新属于本切片（`translate_docs_batch.py clusters --write --pair plan/unified_architecture_program/t8_g4_truth_leak_inventory`），故 `tests/architecture/governance` 落地为绿。

## 10. 第六切片：逐文件分类器（I76）与声明待办收账（本迭代，2026-07-27）

第六个 T8 切片分两步落地，并关闭 §9.2 曾登记为*开放*的那一行。

### 10.1 逐文件维护真值读取者分类（I76）

I76 落地了 §5 所要求的分类器：`python/architecture/consumer_classification.py`
对 `gym_envs/**` + `python/rl/**` 面上每个执行裸 World-Truth 读取
（`truth.<attr>` / `getattr(truth, ...)`，扣除带内联
`g4-diagnostic-truth-read` 标记的读取）的维护模块逐文件分类为五种角色之一：
`observation-consumer`、`reward-consumer`、`command-action-loading-reader`、
`diagnostics` 或 `declared-view-owner`。配套门
（`tests/architecture/information_state/test_g4_consumer_classification.py`）
AST 扫描该面并双向强制注册表↔代码一致——注入的未注册真值读取者变红（无分类行），
陈旧行变红（其文件不再读 truth）——且凡存在 G4 声明处，分类谎言被结构性捕获
（声明 `P10 ObservationExport` 者不得标注为指令/装载/诊断读取者，反之亦然）。
扩展即注册（G5）。I76 同时把尚未携带 G4 声明的两个已分类观测消费者精确钉在
`G4_DECLARATION_PENDING_CONSUMERS` 中：
`python/rl/runtime/world_batch/_vec_env_support.py` 与
`python/rl/runtime/world_batch/observation_batching.py`。

### 10.2 声明待办收账（I76 后续，历史记录）

I76 后续先以声明方式收账；下方的 I87 已接受切片才是这两个模块的受限读取迁移：

- 两个 world-batch 模块现均声明 `INFORMATION_LAYER_CONSUMED = ("World
  Truth",)`、`INFORMATION_LAYER_PRODUCED = ("Agent Observation",)`、
  `SEMANTIC_STAGE = ("P10 ObservationExport",)` —— 镜像它们本已在其下执行的
  I32 批步阶段契约（`python/rl/runtime/world_batch/core.py` 中的
  `state_read` / `observation_build`），并与 §2 记录的 C3 普查裁定一致。
- 在 I76 历史快照中，两者均注册进 `DECLARED_DEFERRED_INFORMATION_LAYER_CONSUMERS`
  （受声明门、不受禁令门）；I87 已接受切片随后将它们移入收敛集合。该切片通过
  注入 reader 消费逐 state 缓存 truth（`state.last_truth`），而非新增逐 loader
  观察视图或 lower-layer owner import。
- `G4_DECLARATION_PENDING_CONSUMERS` 清空。钉机制保留：分类器门的篡改排演现
  针对内存内篡改注册表运行（把已分类消费者移出注册且无钉则变红；陈旧钉变红），
  并新增一个测试钉住收账后的状态本身
  （`test_pending_pin_is_settled_and_world_batch_consumers_are_registered`）。

普查更新：C3 的"经声明视图？"单元格记录该声明（§2），新增 C20 行覆盖
`_vec_env_support.py`（I76 前的普查未将其单列为消费者）。I87 已接受切片在保留 I32
阶段契约的前提下移动 x/y 叶读到高层注入 reader；其状态为已接受/落地。

### 10.3 I76 收账验证（零行为变更）

- `tests/architecture/information_state` —— 全套门在翻转后的钉下通过：有本地
  构建时 79 passed（I63 后为 61，I76 的 +13 分类器测试后为 74；本后续新增 +2
  声明门与 +2 推迟裸读参数化及 +1 收账钉测试，除旧待办钉排演对非空真实钉的依
  赖外无移除）。无构建时四个
  `ef_py` 导出一致性测试跳过（75 passed + 4 skipped）。声明门现枚举 15 个维护
  消费者（原 13）；推迟消费者裸读预期（`test_g4_truth_read_ban.py`，按推迟注
  册表参数化）覆盖两个新增项并证明其推迟为真。
- 不触碰任何生产读取：两个消费者文件只增加三个声明常量与注释；
  `python/architecture/*` 与分类器门的排演是仅有的其他代码编辑。
- 双语哈希治理门会因本登记册被编辑而变红，直到重新生成簇哈希；该刷新在落地侧
  （`translate_docs_batch.py clusters --write --pair
  plan/unified_architecture_program/t8_g4_truth_leak_inventory`）。

### 10.4 I87 受限类型化观测切片（2026-07-27；已接受/落地）

已接受实现严格限制在 C3/C20：

- `RuntimeFacadeAdapter(use_typed_observation_view=True)` 从自身 facade 在构造期读取 `describe_maintained_observation_view()` 一次，并只准入 view id `gym_envs.observation_view`、schema major `1`、声明的产出/消费层与 `P10 ObservationExport`。任一非空 `required_fields` 或 `optional_fields` 都 fail-closed；空清单仅为结构性声明，不是 wildcard 或零字段。默认路径 describe 为零次。
- 高层 `WorldBatchVecEnv` 与 cooperative caller 将 `gym_envs.observation_view.own_ship_attr` 注入 C3/C20。下层 `python.rl.runtime.world_batch` 不新增 owner import，也不再裸读 `truth.x/y`；opaque truth 对象仍传入编译内核。`_ScenarioLoaderRuntimeProxy` 与 TL13 seam 不变。
- 聚焦测试钉住构造次数、全部结构失配、空/非空字段语义、opaque-truth 转发、off/on parity、注入 reader 与零裸叶读门。本段记录已落地切片的证据；更广泛类型化数据流仍保持延期。

## 相关

- [统一架构计划](README.zh.md)
- [SCAL 一致性普查（2026-07-20）](scal_conformance_census_20260720.zh.md)（V3–V7 登记；首批消费者优先级；结构先例）
- [T6 残留台账（2026-07-20）](t6_residual_ledger.zh.md)（同类 `reference` 登记）
- [仿真系统架构设计](../architecture/simulation_system_architecture_design.md)（§3 信息状态层；§6 P0–P10 阶段；§15 G4；§16 表示策略）
- 设施：`python/architecture/information_layer.py`
- 视图 owner：`gym_envs/observation_view.py`
- 结构性事实导出：`RuntimeFacade::describe_maintained_observation_view`（`src/runtime/facade/runtime_facade.h` / `runtime_facade_query.cpp`）
- 门：`tests/architecture/information_state/test_g4_layer_declarations.py`、`tests/architecture/information_state/test_g4_truth_read_ban.py`、`tests/architecture/information_state/test_g4_observation_view_export.py`、`tests/architecture/information_state/test_g4_inventory_consistency.py`
