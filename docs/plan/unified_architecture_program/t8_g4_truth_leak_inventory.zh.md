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

状态：[统一架构计划](README.zh.md)的 T8（信息状态架构）第一切片登记册。它记录：(a) 维护面观测/奖励消费者普查；(b) 本切片 G4 层声明机制的落地范围；(c) 策略路径上的 World Truth 直读，逐条裁定。参照
[SCAL 一致性普查](scal_conformance_census_20260720.zh.md)先例，本文为描述性登记册（`reference`）：不改变任何运行期行为。G4 声明机制为纯元数据加一个架构测试；本切片仅清点并登记真值泄漏，不关闭任何一条。关闭一条泄漏意味着后续某个 T8 切片把该消费者迁移到声明式 `ObservationViewSpec` 导出，并在此翻转其裁定。

全文使用的 G4 词汇即
[仿真系统架构设计](../architecture/simulation_system_architecture_design.md)§3 的权威六层信息状态集合，逐字沿用 `python/rl/runtime/world_batch/core.py` 中 I32 阶段契约白名单（由 `tests/world_batch/test_world_batch_core.py` 钉住）：World Truth、Sensed State、Track State、Shared Tactical Picture、Agent Observation、Decision Belief。

## 1. G4 声明机制（Python 侧）

核心不变量 G4（"每个观测/奖励消费者都声明其信息状态层"）在 Python 维护面上以轻量、零运行时开销的设施实现，沿用 T0 普查提出的机制（普查 §3）：

- **设施**：`python/architecture/information_layer.py` —— 一个中立、仅依赖标准库的模块（依赖方向 `gym_envs -> python.architecture <- python.rl`，与 `python.tasking_contracts` 对齐）。它发布权威层词汇（`AUTHORITATIVE_INFORMATION_LAYERS`）、规范 P0–P10 阶段词汇（`CANONICAL_SEMANTIC_STAGES`）、已声明消费者的 G5 注册表（`MAINTAINED_INFORMATION_LAYER_CONSUMERS`），以及可供未来 AST 门复用的共享校验器 `validate_information_layer_declaration`。
- **声明**：每个维护面消费者声明三个模块级常量 —— `INFORMATION_LAYER_CONSUMED`、`INFORMATION_LAYER_PRODUCED`、`SEMANTIC_STAGE` —— 均为权威字符串元组。它们是纯赋值（无每步或导入期开销），风格取自 I32 阶段契约声明与 `mission_obs_taxonomy` 的 OWNER 映射先例。
- **门**：`tests/architecture/information_state/test_g4_layer_declarations.py` 断言每个已注册消费者携带合法声明，双向交叉核对设施词汇与 I32 阶段契约白名单，并确认其覆盖 `core.py` 实际声明的每个层/阶段。白名单测试与 `core.py` 均通过静态 AST 解析读取、从不 import，故此门不依赖 `ef_py`/运行期，无需构建即可运行。声明提取器仅接受元组（列表字面量视为缺失声明）；门证明其可承载：摘掉、篡改或写成列表形式的声明均会变红。

本切片交付声明 + 存在性门；G4 预期的"禁止非诊断 World Truth 直读的 AST 门"（"执行从文档迁移到 AST 门"，设计文档 §15）留待后续切片，由 §3 清单播种。

## 2. 维护面观测/奖励消费者普查

`gym_envs/**` 与 `python/rl/**` 面（以及 `tools/eval/**` 直读）上的每条维护面观测/奖励消费路径。"经声明视图？"记录该读取是否已经过声明视图/seam。

| # | 消费者 | 读取的数据面 | G4 层 | 经声明视图？ |
|---|--------|--------------|-------|--------------|
| C1 | `gym_envs/scenario_loader/mission_observation.py` —— Python 自持模式（`naval_screen_station_v1`、`air_combat_c2_roe_v1/v2`） | `truth.contacts`、`truth.missiles_remaining`、`truth.x/y`；support `get_agent_observation`/`get_unit_position`；support `get_unit_messages` | 消费 World Truth + Shared Tactical Picture；产出 Agent Observation | **本切片已声明**（原 V4 泄漏） |
| C2 | `gym_envs/scenario_loader/mission_observation.py` —— 编译模式（`basic`/`nav_v1`/`nav_v2`/…） | 由 `mission_command_view` + 航路引导编译 `ef_py.compute_mission_observation`（truth 传入） | 产出 Agent Observation（编译） | 编译 facade 路径；由 C1 模块声明覆盖 |
| C3 | `python/rl/runtime/world_batch/observation_batching.py` + `_observation_mixin.py` | `state.last_truth`/`state.last_inst`（truth/仪表缓存）、`truth.x/y`、`inst.alt_baro` → 编译批 | 消费 World Truth（缓存）→ 产出 Agent Observation | **是** —— I32 阶段契约（`state_read`/`observation_build`），已合规 |
| C4 | `gym_envs/scenario_loader/reward_runtime/air_combat.py` | `truth.missiles_remaining`；`sim.export_recent_engagement_events`；`sim.debug_get_aircraft_damage_state`/`debug_get_ground_contact_state`；`sim.is_unit_active` | 消费 World Truth；产出奖励 | **本切片已声明**（原 V5 泄漏） |
| C5 | `gym_envs/scenario_loader/reward_runtime/naval.py` | `truth.x/y`、`truth.contacts`；`sim.get_unit_position`/`get_agent_observation`（他体单位）；`sim.get_unit_messages` | 消费 World Truth + Shared Tactical Picture；产出奖励 | **本切片已声明**（原 V6 泄漏） |
| C6 | `gym_envs/scenario_loader/reward_runtime/safety.py` | 本机 `truth.health/z/pitch/speed` | 消费 World Truth；产出奖励输入 | **本切片已声明**（本机自读） |
| C7 | `gym_envs/scenario_loader/reward_runtime/shaping_inputs.py` | 本机 `truth.z/speed` + 仪表向量 | 消费 World Truth；产出奖励输入 | **本切片已声明**（本机自读） |
| C8 | `gym_envs/scenario_loader/reward_runtime/objectives.py` | 本机 `truth.z/health/heading/x/y/missiles_remaining`；目标 `truth.contacts`、`sim.is_unit_active`/`get_unit_health` | 消费 World Truth；产出奖励/目标输入 | **本切片已声明**（本机 + 目标读） |
| C9 | `gym_envs/scenario_loader/reward_runtime/compiled_runtime.py` | 组装预构建输入 DTO；无直接信息层读取 | —（组装器，非直接消费者） | 不适用 —— 排除出注册表 |
| C10 | `gym_envs/scenario_loader/core.py::get_policy_agent_observation` / `get_policy_instrument_state` | `sim.get_agent_observation`/`get_instrument_state`（批路径上为 facade 背书代理） | World Truth 读取 seam 本身（V3） | 维护 seam；T8 目标为 `ObservationViewSpec` 导出点 |
| C11 | `gym_envs/scenario_loader/step_evaluation.py` | 本机 `truth.x/y/z/vx/vy/vz/speed/pitch/roll/heading/health`；编排奖励面 | 跨阶段捆绑聚合器（V7） | 推迟 —— 待裁定（P9+P10 捆绑） |
| C12 | `gym_envs/scenario_loader/execution_runtime/mainline.py` | 编排执行步；奖励/观测经 loader | 编排器 | 推迟 —— 待裁定 |
| C13 | `gym_envs/leader_env_parts/decision_runtime/observations.py::build_observation` | 主要为 `inst.*`；`truth.x/y` 用于 ILS/跑道/锚点几何；nav 委派给 `get_mission_observation` | 产出 Agent Observation；消费 World Truth（位置） | 推迟 —— 待裁定（leader 路径） |
| C14 | `python/rl/tasking/leader_tasking.py` | 多处 `get_policy_agent_observation`/`get_policy_instrument_state` | 脚本化指挥；消费 World Truth | 推迟 —— 待裁定（脚本指挥的认知层） |
| C15 | `tools/eval/waypoint_eval_utils.py`、`tools/eval/task_eval_driver.py` | `get_agent_observation`/`get_instrument_state` | eval 工具读取 | eval/诊断面 —— 维护策略路径之外 |
| C16 | `gym_envs/universal_env.py::UniversalEnv` 类构造函数 | — | 已降级的 fail-fast 壳（`__init__` 抛 `RuntimeError`） | 死路径 —— 无需声明。此处仅指被移除的原始内核环境，与其再导出的、仍活跃的 `build_universal_observation` 不同（见 C17）。 |
| C17 | `gym_envs/universal_env_parts/observations.py::build_universal_observation` —— 活跃的通用策略观测组装，由 `CooperativeWorldBatchVecEnv` 与 `MultiAgentWorldRuntimeView` 调用 | `truth.x/y`（ILS 查询）、`truth.contacts`、`truth.rwr_warnings`（Python 回退路径）；编译路径将 `truth` 传入 `ef_py.compute_execution_observation_runtime_numpy`；mission 向量委派给 `get_mission_observation` | 消费 World Truth；产出 Agent Observation | **本切片已声明**（修复轮：从第一切片 C16 拆分，C16 曾将此活跃路径误判为死路径） |
| C18 | `gym_envs/scenario_loader/navigation_runtime/waypoint_rewards.py::build_waypoint_step_state` —— 直接的航点奖励输入消费者，由 `step_evaluation.py`/`execution_runtime/mainline.py` 经 `loader._build_waypoint_step_state` 调用 | 本机 `truth.x/y`（到点距离与航路参考点）；构造 `ef_py.WaypointRewardInputs` | 消费 World Truth；产出奖励输入 | **本切片已声明**（修复轮：第一切片普查遗漏） |
| C19 | `gym_envs/scenario_loader/navigation_runtime/guidance.py` —— 共享航路引导几何辅助（`query_route_guidance_result`、`compute_waypoint_guidance_state`、`apply_waypoint_guidance_update` 等） | 本机 `truth.x/y/speed`（航路引导几何；`get_policy_agent_observation` 回退） | 跨越指令下发（P3/P4 自动驾驶目标）+ 奖励支撑（P10）；非单一面向 Agent Observation 的消费者 | 推迟 —— 待裁定（引导/指令混合辅助，不强行归类；修复轮） |

本切片已注册（声明）：C1、C4、C5、C6、C7、C8、C17、C18（即 `MAINTAINED_INFORMATION_LAYER_CONSUMERS` 中的八个模块；C17/C18 于本修复轮加入）。已合规：C3。作为非消费者排除：C9。死路径：C16。带理由推迟（宁缺毋滥，不强行归类）：C11、C12、C13、C14、C19。维护策略路径之外：C15。

## 3. 真值泄漏清单

策略路径上的 World Truth 直读（策略/观测构建，或代表面向 Agent Observation 的消费者却读取 truth 的奖励）。裁定：**诊断** = 合法诊断用途；**泄漏** = 需 T8 视图收敛；**豁免** = 由声明/seam 合法化。

| ID | 位置 | 读取 | 裁定 | 备注 |
|----|------|------|------|------|
| TL1 | `mission_observation.py::_air_combat_c2_roe_vector`（`_target_track`、`_truth_missiles_remaining`） | `truth.contacts`（目标距离/航迹龄/分类）、`truth.missiles_remaining` | **泄漏**（他体 + 本机弹量） | V4。现已 G4 声明（C1 CONSUMED World Truth）。T8：改读声明式航迹/观测导出，而非原始 `truth.contacts`。 |
| TL2 | `mission_observation.py::_naval_screen_station_vector` | `truth.x/y`（本机）、`truth.contacts`（目标在场）；`runtime_view.get_agent_observation`/`get_unit_position`（support 单位） | **泄漏**（本机 + 他体） | V4。现已 G4 声明（C1）。support 的 truth-obs 与目标 contacts 属上帝视角读取，待收敛。 |
| TL3 | `mission_observation.py::_naval_screen_station_vector` | `runtime_view.call_optional("get_unit_messages", support)`（报告链） | **豁免** | Shared Tactical Picture：链路分发报告是合法的声明层（C1 CONSUMED Shared Tactical Picture），非原始 truth。 |
| TL4 | `reward_runtime/air_combat.py::_truth_missiles_remaining`（`_air_combat_observed_release_count`、`_apply_release_shaping`） | `truth.missiles_remaining` | **泄漏**（经 truth 的本机弹药状态） | V5。现已 G4 声明（C4）。本机弹量，低风险，但读自原始 truth。 |
| TL5 | `reward_runtime/air_combat.py::_recent_engagement_events` / `_standard_damage_fact_projections` | `sim.export_recent_engagement_events()`（damage/lifecycle/consequence 事件） | **泄漏**（交战证据） | V5。部分自门控：`consumer_visibility == "diagnostics_only"` 的事件被过滤。T8：改经声明式交战证据视图。 |
| TL6 | `reward_runtime/air_combat.py::_damage_consequence_snapshot`、`_ground_contact_terminal_state` | `sim.debug_get_aircraft_damage_state`、`sim.debug_get_ground_contact_state` | **诊断** | 显式 `debug_*` API，用于伤害后果奖励塑形；可接受的诊断用途。 |
| TL7 | `reward_runtime/air_combat.py::combat_entity_terminal_state` | `sim.is_unit_active(target)` | **泄漏**（他体存活状态） | V5。目标存活为权威 truth；T8：从声明式交战/观测视图派生。 |
| TL8 | `reward_runtime/naval.py::_station_reward_terms` / `apply_naval_reward_surface` | `truth.x/y`（本机）、`truth.contacts`（目标）、`sim.get_unit_position(support)`、`sim.get_agent_observation(support)` | **泄漏**（本机 + 他体） | V6。现已 G4 声明（C5）。他体单位位置/观测属上帝视角读取，待收敛。 |
| TL9 | `reward_runtime/naval.py::_support_received_target_report` | `sim.get_unit_messages(support)`（报告链） | **豁免** | Shared Tactical Picture（C5 CONSUMED Shared Tactical Picture）：合法链路分发报告。 |
| TL10 | `reward_runtime/safety.py::build_safety_runtime_inputs` | 本机 `truth.health/z/pitch/speed` | **泄漏**（本机自读，低风险） | 现已 G4 声明（C6）。本机状态可观测；收敛到声明式本机观测视图。 |
| TL11 | `reward_runtime/shaping_inputs.py::build_flight_shaping_runtime_inputs` | 本机 `truth.z/speed` | **泄漏**（本机自读，低风险） | 现已 G4 声明（C7）。 |
| TL12 | `reward_runtime/objectives.py::build_conditional_objective_inputs`、`_combat_target_snapshot` | 本机 `truth.z/health/heading/x/y/missiles_remaining`；目标 `truth.contacts` 距离、`sim.is_unit_active`/`get_unit_health(target)` | **泄漏**（本机 + 他体） | 现已 G4 声明（C8）。目标血量/存活属上帝视角读取，待收敛。 |
| TL13 | `scenario_loader/core.py::get_policy_agent_observation` / `get_policy_instrument_state` | `sim.get_agent_observation`/`get_instrument_state`（批路径上为 facade 背书代理） | **豁免**（维护 seam） | V3。唯一的维护读取瓶颈；批路径上 `sim` 为 `_ScenarioLoaderRuntimeProxy`（facade 背书）。T8 目标：把该 seam 的返回变为声明式 `ObservationViewSpec` 导出，令 C1/C4/C5/C6/C7/C8 不再读原始 truth。 |
| TL14 | `scenario_loader/step_evaluation.py`（`build_execution_runtime_state`、奖励输入组装） | 本机 `truth.x/y/z/vx/vy/vz/speed/pitch/roll/heading/health` | **泄漏**（本机，聚合器；推迟） | V7。跨阶段捆绑编排器；声明推迟（待裁定），不强行归类。 |
| TL15 | `leader_env_parts/decision_runtime/observations.py::build_observation` | 本机 `truth.x/y`（ILS/跑道/锚点几何） | **泄漏**（本机位置；推迟） | Leader 观测路径；声明推迟（待裁定）。 |
| TL16 | `python/rl/tasking/leader_tasking.py`（多处） | `get_policy_agent_observation`/`get_policy_instrument_state` | **泄漏**（脚本指挥；推迟） | 脚本化指挥消费 World Truth；认知层（维护式条令 vs 仅诊断）推迟（待裁定）。 |
| TL17 | `tools/eval/waypoint_eval_utils.py`、`tools/eval/task_eval_driver.py` | `get_agent_observation`/`get_instrument_state` | **豁免**（eval 面） | eval/诊断工具，维护策略路径之外；非维护面泄漏。 |
| TL18 | `universal_env_parts/observations.py::build_universal_observation` | `truth.x/y`（ILS 查询）、`truth.contacts`、`truth.rwr_warnings`（Python 回退）；编译路径将 `truth` 传入 `ef_py.compute_execution_observation_runtime_numpy` | **泄漏**（本机 + 他体航迹/告警） | 现已 G4 声明（C17）。第一切片普查误判为死路径的活跃策略观测路径（`CooperativeWorldBatchVecEnv`/`MultiAgentWorldRuntimeView`）；T8：改读声明式观测导出，而非原始 truth。 |
| TL19 | `navigation_runtime/waypoint_rewards.py::build_waypoint_step_state` | 本机 `truth.x/y`（到点距离、航路参考） → `ef_py.WaypointRewardInputs` | **泄漏**（经原始 truth 的本机位置） | 现已 G4 声明（C18）。本机位置馈入航点奖励输入；收敛到声明式本机观测视图。 |
| TL20 | `navigation_runtime/guidance.py`（`query_route_guidance_result`、`compute_waypoint_guidance_state`、`apply_waypoint_guidance_update` 等） | 本机 `truth.x/y/speed`（航路引导几何） | **泄漏**（本机；推迟） | 共享航路引导辅助，跨越指令下发（自动驾驶目标）与奖励支撑；声明推迟（待裁定），不强行归类（C19）。 |

## 4. 裁定分布

| 裁定 | 数量 | 条目 |
|------|------|------|
| 泄漏 —— 需 T8 视图收敛 | 15 | TL1、TL2、TL4、TL5、TL7、TL8、TL10、TL11、TL12、TL14、TL15、TL16、TL18、TL19、TL20 |
| 豁免 —— 由声明/seam 合法化 | 4 | TL3、TL9、TL13、TL17 |
| 诊断 —— 合法诊断用途 | 1 | TL6 |

15 条泄漏中，本轮已 G4 声明 11 条（TL1、TL2、TL4、TL5、TL7、TL8、TL10、TL11、TL12 位于 C1/C4/C5/C6/C7/C8，另加本修复轮的 TL18 位于 C17、TL19 位于 C18 —— 共八个已声明消费者），4 条为推迟的聚合器/leader/引导路径（TL14、TL15、TL16、TL20）。声明一条泄漏并不关闭它：声明使当前 truth 读取可见、可测；T8 的收敛目标是 TL13 处唯一的 `ObservationViewSpec` 导出，令下游消费者改读 Agent Observation 而非原始 World Truth。

## 5. 后续切片（本切片未做）

- 在 TL13 seam 处将 `ObservationViewSpec` 物化为运行期 facade 导出，并将已声明消费者（C1/C4/C5/C6/C7/C8/C17/C18）迁移到经其读取（关闭 TL1/TL2/TL4/TL5/TL7/TL8/TL10/TL11/TL12/TL18/TL19）。
- 裁定并声明推迟的聚合器/leader/引导路径（C11–C14、C19；TL14–TL16、TL20）。
- 在视图导出就绪后，加上禁止已声明消费者非诊断 World Truth 直读的 G4 AST 门（设计文档 §15；普查 §3 第三部分）。

## 相关

- [统一架构计划](README.zh.md)
- [SCAL 一致性普查（2026-07-20）](scal_conformance_census_20260720.zh.md)（V3–V7 登记；首批消费者优先级；结构先例）
- [T6 残留台账（2026-07-20）](t6_residual_ledger.zh.md)（同类 `reference` 登记）
- [仿真系统架构设计](../architecture/simulation_system_architecture_design.md)（§3 信息状态层；§6 P0–P10 阶段；§15 G4；§16 表示策略）
- 设施：`python/architecture/information_layer.py`
- 门：`tests/architecture/information_state/test_g4_layer_declarations.py`
