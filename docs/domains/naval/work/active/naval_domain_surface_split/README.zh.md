# 海军领域执行面拆分

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/work/active/naval_domain_surface_split/README.md`
Owner: `domains/naval`
Last verified: `2026-09-23`

状态：`2026-09-23`，活跃；有边界的 N4 闭合已 **accepted**。`P2-B` command projection
已落地为 `NavalCommandIntent` 加唯一维护写入 seam，新分支已有原生 projection 回归测试。
N5/N6 仍是独立的 blocked 工作。

语言：

- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

输入：

- [海军 owner README](../../../README.zh.md)
- [海军进展快照](../../../reviews/naval_progress_snapshot_20260527.zh.md)
- [N4 威胁 / ROE bridge](../../../reviews/n4_threat_roe_bridge_20260525/README.zh.md)
- [N5 RL 动作面拆分](../../../reviews/n5_rl_action_surface_split_20260527/README.zh.md)
- [领域 owner 索引](../../../../README.zh.md)
- [Command 边界 README](../../../../../../src/components/command/README.zh.md)
- [海军标准](../../../README.zh.md)
- [子项目创建标准](../../../../../engineering/automation/rules/subproject_creation_standard.zh.md)

## Purpose

本子项目承接第一段 N4 训练入口修复之后的海军领域拆分。上一段已经移除了 active
入口对 `takeoff4` 和空军 formation-role mission observation 的直接复用，但还没有把
所有空军优先兼容载体从维护中的海军 runtime 路径中拆掉。

本项目的目标是在打开任何 N5 武器交战或 N6 毁伤声明之前，把剩余兼容层明确收束为
adapter surface，并建立海军拥有的 command、action、observation 与配置表面。

## Current State

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| Active N4 动作面 | 第一切片已接受；`2026-06-12` 收紧 command surface | `gym_envs/universal_env_parts/naval_actions.py` 中的 `naval_station3` | `_naval_station3_command_surface` 是站位指令真值；中性 `PilotAction` 仅保留为 legacy transport |
| Active N4 任务观测 | maintained adapter 已接受 | `python/mission_obs_taxonomy.py` 与 `gym_envs/scenario_loader/mission_observation.py` 中的 `naval_screen_station_v1` | policy vector 由 `naval_screen_station_v1_maintained_adapter` 生成；compiled batch 输入仍退回 `basic` |
| Command shell | 兼容层仍活跃 | `src/components/command/mission_command.h` 中的 `MissionCommand = core + air + naval` | flat shell 仍携带 air owner slice 和 target-altitude 命名 |
| Naval command projection | 已落地（`P2-B`，有边界） | `src/components/domains/naval/command/mission_command_naval.h` 中的 `NavalCommandIntent`；投影 `mission_command_naval_intent(owner_slice, core)`；唯一写入 seam `set_mission_command_naval_projection` | station/motion 与 embarked-air 系统消费投影组件；weapon-release 兼容读取器仍消费 flat shell，不构成 N5 闭合 |
| World-batch policy action | 兼容层仍活跃 | `src/runtime/contracts/world_batch_contracts.h` 中的 `WorldPilotActionAssignment` | 尚无 naval-owned action assignment packet |
| N5/N6 声明 | held | N4 合同禁止 weapon inventory、health 和 damage delta | 本项目不释放武器或毁伤 authority |
| Naval tasking token 映射 | 英中聚焦 guard 已刷新 | `tests/architecture/command_tasking/test_naval_tasking_standard_guard.py` 交叉核对英中标准 token、C++ enum 与 Python profile | 仅为合同证据；它是术语守卫，并不约束海军 observation——后者由 `tests/runtime/naval/test_naval_station_policy_surface.py` 约束 |
| Naval reward surface | 声明项在零值时也会上报 | `gym_envs/scenario_loader/reward_runtime/naval.py` 的 `DECLARED_NAVAL_TERMS`；`tools/eval/naval_station_policy_eval.py` 要求这些名字存在 | `2026-09-22` 修复：该表面以 key 集合被观测，而值为零的声明项此前被丢弃，导致 `main` 上有一个海军表面测试为红 |

## Scope

范围内：

- 盘点 active naval 路径上仍存在的 air-first compatibility；
- 定义海军拥有的 action 或 intent transport，替代 maintained naval 入口对 `PilotAction`
  语义的 policy-visible 依赖；
- 收窄 `MissionCommand` 用法，让 naval station、ROE、目标分配以及后续 fire-control
  intent 经由明确的 maintained owner slice；
- 将 `naval_screen_station_v1` 从 Python-owned replacement 推向 maintained naval
  observation packet；
- 当 `flight_shaping_backend` 这类空军标签阻塞海军 runtime owner 时，增加中性别名或
  wrapper；
- 增加测试和文档，保持 N4 pre-fire gate 为绿，同时拒绝 N5/N6 过度声明。

范围外：

- weapon release success、hit/intercept、damage、kill 或 engagement reward；
- 完整海军 helm doctrine、舰艇 autopilot 或 fleet C2；
- 正式 learned-policy 验收；
- 一次性移除所有历史 compatibility shell；
- 大范围重写成熟空军 takeoff、cruise、landing 或 cooperative execution 行为。

## Phase Plan

| 阶段 | 目标 | 进入条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 固定范围、输入、写集和禁止声明。 | 用户请求加当前 N4/N5 证据 | 子项目文件和父 README 链接存在 | active |
| `P1 Inventory` | 映射 active naval 的所有 air-first 依赖。 | P0 scaffold | current-status inventory 命名代码 owner 和风险等级 | accepted |
| `P2 Command/Action Split` | 引入 naval-owned command 和 action transport seam。 | P1 inventory accepted | active naval policy 路径不再依赖 `PilotAction` 语义 | accepted：action command surface 已收束，`P2-B` command projection 已落地为 `NavalCommandIntent` |
| `P3 Observation/Config Split` | 提升 naval observation 并中和阻塞性 env 命名。 | P2 packet boundary accepted | `naval_screen_station_v1` 有 maintained packet gate 和配置别名 | accepted |
| `P4 Integration Gates` | 将训练、评估、合同接到新 surface。 | P2/P3 implementation slices | 聚焦测试和场景合同通过且不声明 N5/N6 | accepted |
| `P5 Closure` | 同步验收、当前进展和 archive 边界。 | P4 validation | acceptance record 标记 split accepted 或 held | 有边界 N4 surface 已 accepted；N5/N6 和 carrier cleanup 延后 |

## Task Clusters

- 任务簇计划：
  [naval_domain_surface_split_task_clusters_20260601.md](naval_domain_surface_split_task_clusters_20260601.md)
- 当前状态：
  [naval_domain_surface_split_current_status_20260601.md](naval_domain_surface_split_current_status_20260601.md)
- 分发队列：
  [naval_domain_surface_split_dispatch_queue_20260601.md](naval_domain_surface_split_dispatch_queue_20260601.md)
- `P2-B` 闭合记录：
  [naval_domain_surface_split_p2b_command_projection_20260921.md](naval_domain_surface_split_p2b_command_projection_20260921.md)
- `P5-A` 闭合裁决：
  [naval_domain_surface_split_p5_closure_20260922.md](naval_domain_surface_split_p5_closure_20260922.md)
- 验收门：
  [naval_domain_surface_split_acceptance_20260601.md](naval_domain_surface_split_acceptance_20260601.md)

## Outputs And Evidence

预期输出：

- naval action/intent packet 或等价 maintained adapter 边界；
- command-chain 测试，证明 naval 字段存活不依赖 air owner slice 语义；
- observation 测试，证明 naval policy 输入不是改名后的 air formation/takeoff vector；
- active naval training-entry 检查，拒绝 air action 和 air observation fallback；
- eval JSON surface gate，证明 active 入口运行在 maintained action command surface 与
  naval observation adapter 上；
- 更新文档，保持 `naval_limited_engagement_v1` 在独立 N5 launch/reject package 之前继续阻塞。

## Acceptance Gate

只有满足以下条件，本子项目才能标记为 accepted：

- active maintained naval 入口拥有 naval-owned action/intent transport，或剩余
  `PilotAction` 使用被明确限定为 compatibility-only，且已有 maintained command surface
  承担 policy truth；
- `MissionCommand` compatibility shell 使用被 shared core 与 naval owner slice 的
  maintained projection 测试约束；
- naval policy observation 不把 air takeoff、air formation、runway、gear 或 ILS 字段作为
  policy-visible 语义；
- 配置和 CLI 命名不再迫使 naval 路径宣称 air `flight_shaping` owner；
- N4 pre-fire 场景合同和 active training-entry 测试仍通过；
- N5 武器释放和 N6 毁伤 authority 除非有独立 accepted package，否则继续拒绝。

## Residuals And Next Steps

- 第一轮实现应先做 inventory 和 guard，不应直接大范围重构。
- command/action packet 工作若和 observation packet 写集重叠，应先拆 command/action。
- `naval_limited_engagement_v1` 仍是独立的未来 N5 package。
- 正式海军 policy 训练必须等 transport、observation、reward 和 eval gate 接受之后再做。
- command projection 已由原生 C++ 回归测试执行；`NavalCommandIntent` 仍有意不暴露给
  Python。剩余后续是 transport/carrier cleanup，而不是缺少 projection 执行门。

## 证据生命周期

已接受或被取代的记录迁入 owner-local `docs/domains/naval/reviews/`，不再留在
已退役 task 根下。
