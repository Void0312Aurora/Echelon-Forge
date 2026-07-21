# T8 G4 真值泄漏清单（2026-07-21）

语言：
- 英文正本：[t8_g4_truth_leak_inventory.md](t8_g4_truth_leak_inventory.md)
- 中文对照：`t8_g4_truth_leak_inventory.zh.md`

文档类型：`reference`
生命周期：`maintained`
正本：`docs/plan/unified_architecture_program/t8_g4_truth_leak_inventory.md`
归属：`unified architecture program workline`
最近核验：`2026-07-21`
基线提交：`8bd21d86`

状态：[统一架构计划](README.zh.md)的 T8（信息状态架构）登记册。它记录：(a) 维护面观测/奖励消费者普查；(b) G4 层声明机制的落地范围；(c) 策略路径上的 World Truth 直读，逐条裁定。参照
[SCAL 一致性普查](scal_conformance_census_20260720.zh.md)先例，本文为描述性登记册（`reference`）：不改变任何运行期行为。第一切片落地了 G4 声明机制（纯元数据加一个架构测试）并清点了真值泄漏，未关闭任何一条。**第二切片（§6，2026-07-21）** 在 TL13 读取 seam 上物化一个声明式观察视图，并将八个已声明消费者迁移到经其读取，从结构上收敛 11 条已声明泄漏；该迁移是把裸读纯机械地搬入一个带层标注的 owner，数值结果 bit-for-bit 不变。收敛一条泄漏意味着消费者不再读原始 World Truth：其读取经声明式视图 owner，并在此翻转其裁定。

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
| C3 | `python/rl/runtime/world_batch/observation_batching.py` + `_observation_mixin.py` | `state.last_truth`/`state.last_inst`（truth/仪表缓存）、`truth.x/y`、`inst.alt_baro` → 编译批 | 消费 World Truth（缓存）→ 产出 Agent Observation | **是** —— I32 阶段契约（`state_read`/`observation_build`），已合规 |
| C4 | `gym_envs/scenario_loader/reward_runtime/air_combat.py` | `truth.missiles_remaining`；`sim.export_recent_engagement_events`；`sim.debug_get_aircraft_damage_state`/`debug_get_ground_contact_state`；`sim.is_unit_active` | 消费 World Truth；产出奖励 | **本切片已收敛**（§6；经声明视图；原 V5 泄漏） |
| C5 | `gym_envs/scenario_loader/reward_runtime/naval.py` | `truth.x/y`、`truth.contacts`；`sim.get_unit_position`/`get_agent_observation`（他体单位）；`sim.get_unit_messages` | 消费 World Truth + Shared Tactical Picture；产出奖励 | **本切片已收敛**（§6；经声明视图；原 V6 泄漏） |
| C6 | `gym_envs/scenario_loader/reward_runtime/safety.py` | 本机 `truth.health/z/pitch/speed` | 消费 World Truth；产出奖励输入 | **本切片已收敛**（§6；本机经声明视图读） |
| C7 | `gym_envs/scenario_loader/reward_runtime/shaping_inputs.py` | 本机 `truth.z/speed` + 仪表向量 | 消费 World Truth；产出奖励输入 | **本切片已收敛**（§6；本机经声明视图读） |
| C8 | `gym_envs/scenario_loader/reward_runtime/objectives.py` | 本机 `truth.z/health/heading/x/y/missiles_remaining`；目标 `truth.contacts`、`sim.is_unit_active`/`get_unit_health` | 消费 World Truth；产出奖励/目标输入 | **本切片已收敛**（§6；本机 + 目标经声明视图读） |
| C9 | `gym_envs/scenario_loader/reward_runtime/compiled_runtime.py` | 组装预构建输入 DTO；无直接信息层读取 | —（组装器，非直接消费者） | 不适用 —— 排除出注册表 |
| C10 | `gym_envs/scenario_loader/core.py::get_policy_agent_observation` / `get_policy_instrument_state` | `sim.get_agent_observation`/`get_instrument_state`（批路径上为 facade 背书代理） | World Truth 读取 seam 本身（V3） | 维护 seam；声明式观察视图（§6）现从该 seam 的 `truth`/`sim` 输出读取；完整类型化 `ObservationViewSpec` facade 导出仍为后续步骤 |
| C11 | `gym_envs/scenario_loader/step_evaluation.py` | 本机 `truth.x/y/z/vx/vy/vz/speed/pitch/roll/heading/health`；编排奖励面 | 跨阶段捆绑聚合器（V7） | 推迟 —— 待裁定（P9+P10 捆绑） |
| C12 | `gym_envs/scenario_loader/execution_runtime/mainline.py` | 编排执行步；奖励/观测经 loader | 编排器 | 推迟 —— 待裁定 |
| C13 | `gym_envs/leader_env_parts/decision_runtime/observations.py::build_observation` | 主要为 `inst.*`；`truth.x/y` 用于 ILS/跑道/锚点几何；nav 委派给 `get_mission_observation` | 产出 Agent Observation；消费 World Truth（位置） | 推迟 —— 待裁定（leader 路径） |
| C14 | `python/rl/tasking/leader_tasking.py` | 多处 `get_policy_agent_observation`/`get_policy_instrument_state` | 脚本化指挥；消费 World Truth | 推迟 —— 待裁定（脚本指挥的认知层） |
| C15 | `tools/eval/waypoint_eval_utils.py`、`tools/eval/task_eval_driver.py` | `get_agent_observation`/`get_instrument_state` | eval 工具读取 | eval/诊断面 —— 维护策略路径之外 |
| C16 | `gym_envs/universal_env.py::UniversalEnv` 类构造函数 | — | 已降级的 fail-fast 壳（`__init__` 抛 `RuntimeError`） | 死路径 —— 无需声明。此处仅指被移除的原始内核环境，与其再导出的、仍活跃的 `build_universal_observation` 不同（见 C17）。 |
| C17 | `gym_envs/universal_env_parts/observations.py::build_universal_observation` —— 活跃的通用策略观测组装，由 `CooperativeWorldBatchVecEnv` 与 `MultiAgentWorldRuntimeView` 调用 | `truth.x/y`（ILS 查询）、`truth.contacts`、`truth.rwr_warnings`（Python 回退路径）；编译路径将 `truth` 传入 `ef_py.compute_execution_observation_runtime_numpy`；mission 向量委派给 `get_mission_observation` | 消费 World Truth；产出 Agent Observation | **本切片已收敛**（§6；经声明视图；修复轮加入） |
| C18 | `gym_envs/scenario_loader/navigation_runtime/waypoint_rewards.py::build_waypoint_step_state` —— 直接的航点奖励输入消费者，由 `step_evaluation.py`/`execution_runtime/mainline.py` 经 `loader._build_waypoint_step_state` 调用 | 本机 `truth.x/y`（到点距离与航路参考点）；构造 `ef_py.WaypointRewardInputs` | 消费 World Truth；产出奖励输入 | **本切片已收敛**（§6；本机经声明视图读；修复轮加入） |
| C19 | `gym_envs/scenario_loader/navigation_runtime/guidance.py` —— 共享航路引导几何辅助（`query_route_guidance_result`、`compute_waypoint_guidance_state`、`apply_waypoint_guidance_update` 等） | 本机 `truth.x/y/speed`（航路引导几何；`get_policy_agent_observation` 回退） | 跨越指令下发（P3/P4 自动驾驶目标）+ 奖励支撑（P10）；非单一面向 Agent Observation 的消费者 | 推迟 —— 待裁定（引导/指令混合辅助，不强行归类；修复轮） |

第一切片已声明、第二切片（§6）已收敛到声明式观察视图：C1、C4、C5、C6、C7、C8、C17、C18（即 `MAINTAINED_INFORMATION_LAYER_CONSUMERS` / `VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS` 中的八个模块；C17/C18 于第一切片修复轮加入）。已合规：C3。作为非消费者排除：C9。死路径：C16。带理由推迟（宁缺毋滥，不强行归类）：C11、C12、C13、C14、C19。维护策略路径之外：C15。

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
| TL13 | `scenario_loader/core.py::get_policy_agent_observation` / `get_policy_instrument_state` | `sim.get_agent_observation`/`get_instrument_state`（批路径上为 facade 背书代理） | **豁免**（维护 seam） | V3。唯一的维护读取瓶颈；批路径上 `sim` 为 `_ScenarioLoaderRuntimeProxy`（facade 背书）。声明式观察视图（§6）现从该 seam 的 `truth`/`sim` 输出读取；把 seam 返回变为完整类型化 `ObservationViewSpec` facade 导出仍为后续步骤。 |
| TL14 | `scenario_loader/step_evaluation.py`（`build_execution_runtime_state`、奖励输入组装） | 本机 `truth.x/y/z/vx/vy/vz/speed/pitch/roll/heading/health` | **泄漏**（本机，聚合器；推迟） | V7。跨阶段捆绑编排器；声明推迟（待裁定），不强行归类。 |
| TL15 | `leader_env_parts/decision_runtime/observations.py::build_observation` | 本机 `truth.x/y`（ILS/跑道/锚点几何） | **泄漏**（本机位置；推迟） | Leader 观测路径；声明推迟（待裁定）。 |
| TL16 | `python/rl/tasking/leader_tasking.py`（多处） | `get_policy_agent_observation`/`get_policy_instrument_state` | **泄漏**（脚本指挥；推迟） | 脚本化指挥消费 World Truth；认知层（维护式条令 vs 仅诊断）推迟（待裁定）。 |
| TL17 | `tools/eval/waypoint_eval_utils.py`、`tools/eval/task_eval_driver.py` | `get_agent_observation`/`get_instrument_state` | **豁免**（eval 面） | eval/诊断工具，维护策略路径之外；非维护面泄漏。 |
| TL18 | `universal_env_parts/observations.py::build_universal_observation` | `truth.x/y`（ILS 查询）、`truth.contacts`、`truth.rwr_warnings`（Python 回退）；编译路径将 `truth` 传入 `ef_py.compute_execution_observation_runtime_numpy` | **收敛**（声明视图） | C17。叶读经 `observation_view.own_ship_attr` / `contacts` / `rwr_warnings`。编译路径仍将整个 `truth` 对象传入内核 —— 整体透传，非叶读；本切片不在范围内。 |
| TL19 | `navigation_runtime/waypoint_rewards.py::build_waypoint_step_state` | 本机 `truth.x/y`（到点距离、航路参考） → `ef_py.WaypointRewardInputs` | **收敛**（声明视图） | C18。本机 `truth.x/y` 经 `observation_view.own_ship_field`；引导辅助（C19/TL20）委派不变（推迟）。 |
| TL20 | `navigation_runtime/guidance.py`（`query_route_guidance_result`、`compute_waypoint_guidance_state`、`apply_waypoint_guidance_update` 等） | 本机 `truth.x/y/speed`（航路引导几何） | **泄漏**（本机；推迟） | 共享航路引导辅助，跨越指令下发（自动驾驶目标）与奖励支撑；声明推迟（待裁定），不强行归类（C19）。 |

## 4. 裁定分布

| 裁定 | 数量 | 条目 |
|------|------|------|
| 收敛 —— 经声明式观察视图读取（§6） | 11 | TL1、TL2、TL4、TL5、TL7、TL8、TL10、TL11、TL12、TL18、TL19 |
| 泄漏 —— 仍需 T8 视图收敛（推迟） | 4 | TL14、TL15、TL16、TL20 |
| 豁免 —— 由声明/seam 合法化 | 4 | TL3、TL9、TL13、TL17 |
| 诊断 —— 合法诊断用途 | 1 | TL6 |

11 条收敛条目即八个已声明消费者的叶读（TL1、TL2、TL4、TL5、TL7、TL8、TL10、TL11、TL12 位于 C1/C4/C5/C6/C7/C8，另加 TL18 位于 C17、TL19 位于 C18），现经声明式观察视图 owner（`gym_envs/observation_view.py`，§6）读取，而非原始 World Truth。其余 4 条泄漏为推迟的聚合器/leader/引导路径（TL14、TL15、TL16、TL20），仍待裁定。豁免/诊断读取（TL3、TL6、TL9、TL13、TL17）保持裁定；凡位于已迁移消费者上者，为一致性经视图的 Shared Tactical Picture / 诊断面路由。在 TL13 seam 处把 seam 返回本身变为类型化 `ObservationViewSpec` facade 导出仍为后续步骤。

## 5. 后续切片（本切片未做）

- 把 TL13 seam 的返回变为完整类型化 `ObservationViewSpec` facade 导出。第二切片（§6）已在 seam 的 `truth`/`sim` 输出上物化声明式读取视图并将八个消费者迁移到经其读取；类型化 spec 导出（令 seam 本身返回类型化视图对象）仍待完成。
- 裁定并声明推迟的聚合器/leader/引导路径（C11–C14、C19；TL14–TL16、TL20），随后将其收敛到声明式视图。
- 随着这些推迟消费者的收敛，扩展 G4 AST 真值直读禁令门。该门已覆盖八个已迁移消费者（§6；`tests/architecture/information_state/test_g4_truth_read_ban.py`）。

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

## 相关

- [统一架构计划](README.zh.md)
- [SCAL 一致性普查（2026-07-20）](scal_conformance_census_20260720.zh.md)（V3–V7 登记；首批消费者优先级；结构先例）
- [T6 残留台账（2026-07-20）](t6_residual_ledger.zh.md)（同类 `reference` 登记）
- [仿真系统架构设计](../architecture/simulation_system_architecture_design.md)（§3 信息状态层；§6 P0–P10 阶段；§15 G4；§16 表示策略）
- 设施：`python/architecture/information_layer.py`
- 视图 owner：`gym_envs/observation_view.py`
- 门：`tests/architecture/information_state/test_g4_layer_declarations.py`、`tests/architecture/information_state/test_g4_truth_read_ban.py`
