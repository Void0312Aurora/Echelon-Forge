# 陆军 / 地面当前进展追踪

状态：`2026-05-24` 工作区采样复核。

这是 `docs/task/ground/` 在 `2026-05-21` 开启 G0-G5 地面启动线之后的当前活跃追踪入口。它按基础设施、域语义和 RL/tasking 对接跟踪陆军/地面线。

当前定位：

- `services/army` 是军种画像边界。
- `ground` 是维护中的执行特化名称；`army` 和 `land` 是可接受别名，都会规范化为 `ground`。
- G0-G4 已封存为 accepted tasking baseline。
- G5 已有规范 MVP 场景壳，只证明 loader 加 tasking 状态链参与。
- G6 新增两个 G1 realism-gradient fixture，用于 static occupy 与 support
  relationship 语义。
- 真实地面机动、地形交互、感知、火力、毁伤和 observation export 仍然延后。

术语说明：项目阶段 `G6 Realism Gradient MVP Scenarios` 不等于域真实性梯度
`G6 effects/damage/termination`；当前阶段只发布 `G1` 真实性 fixture。

## 当前结论

陆军/地面线当前已经形成可维护的 tasking 与规划基线，但还不是可维护的地面战斗 runtime。

已经落地的内容：

- `joint/common core`、`services/army` 和 `ground` 的标准分层；
- Python tasking dispatch 中的 ground 别名和 Army service-profile 推断；
- `TASK_MOVE`、`TASK_OCCUPY`、`TASK_SUPPORT` 三个 starter ground task 语义；
- 一个以排为中心的非 runtime 内容种子；
- 可运行的 ground common-core task 合同；
- G4 runtime bridge，证明 normalized ground `TaskOrder -> LeaderIntent -> PilotReport`；
- `scenarios/ground/` 下的 G5 场景 smoke 壳；
- 两个 G6 G1 场景，证明 static occupy/support relationship 语义；
- RL/runtime 入口现在通过共享 tasking bridge 构造 mission command，而不是 air-only 路径。

当前主要风险不是“链路是否存在”，而是边界纪律：很容易把 G5 smoke 场景误读为真实 ground unit 或 movement 证明。现有证据只支持 Army/ground tasking-chain participation。

## 域真实性梯度临界点

Ground 域真实性应随场景实际使用的复杂度提升而提升。项目不应把“地面真实性”当成一个整体标签一次性打勾；每个场景都应声明自己进入了哪个真实性梯度，并为该梯度的最低临界点提供测试或合同。

原则：

- tasking-only smoke 场景只需要任务语义、军种画像对齐和状态链真实性。
- 简单 movement 或 cruise-style 场景必须额外加入机动、速度、队形、路线和地形可通行性真实性，但不需要火控或毁伤真实性。
- contact/report 场景必须额外加入感知、视线、航迹记忆、报告延迟和 information-state 边界。
- firefight 场景必须先加入 ROE、目标识别、武器包线、压制/效果、毁伤和终止条件 gate。
- 未被当前场景使用的域能力可以保持 MVP，但不能被拿来支撑更高复杂度场景的真实性声明。

建议梯度：

| 梯度 | 场景复杂度入口 | 最低真实性要求 | 当前状态 |
|------|----------------|----------------|----------|
| `G0` tasking/status | `TaskOrder -> LeaderIntent -> PilotReport` 是场景目标 | `Army` service profile、normalized `ground` tasking profile、command/support IDs、active status shell | 已实现并验证 |
| `G1` static occupy/support | 单位被分配 occupy、support 或 hold，但不模拟移动 | objective/area reference、support relationship、tactical cadence、status/report semantics | 已为 static occupy 与 support relationship compatibility-shell fixture 实现 |
| `G2` movement/cruise | 地面单位沿路线或向目标机动 | 速度限制、加减速、队形间距、航路点/路线跟随、可通行地表、stuck/off-route 检查 | 未实现 |
| `G3` terrain-aware movement | 地形影响机动或路线选择 | terrain class、坡度/障碍/通行性、cover/concealment 占位、路线成本、机动退化 | 未实现 |
| `G4` contact/report | 发现或报告地面接触成为场景关键 | terrain/LOS gating、visual/acoustic sensor 参数、track memory/confidence、report latency、不泄漏 world truth observation | 未实现 |
| `G5` ROE/fires | 直接或间接火力影响决策 | 目标识别、ROE/authorization、武器包线、射程/射界/冷却/弹药、fire event/rejection evidence | 未实现 |
| `G6` effects/damage/termination | 战斗结果依赖毁伤或压制 | hit/effect model、suppression、mobility/sensor/mission kill、能力退化、reward 与 termination 绑定 | 未实现 |
| `G7` sustainment/logistics | 补给、伤亡后送或续航成为核心 | 弹药/燃料/物资状态、support windows、transfer constraints、readiness 随时间退化 | 未实现 |

当前 ground 位置：

- `ground_platoon_tasking_smoke_v1` 是 `G0` 场景。
- 该场景中的 `TASK_OCCUPY` 还不是 `G1` occupy realism；它只是用于验证状态链的 tasking intent。
- `ground_platoon_static_occupy_v1` 与
  `ground_platoon_support_relationship_v1` 是 `G1` 场景。它们只证明
  static occupy/support status 语义，不证明 movement、terrain、sensing、
  fires、damage 或 native ground platform 行为。
- `G6-C` 新增 route-move boundary guardrails，但不释放 `G2` movement。
  `ground_platoon_flat_route_move_v1` 仍保持 held。
- 后续每个新场景都必须声明自己是继续停留在 `G0`，推进到 `G1`，还是进入 `G2+`，并在宣称该层真实性前补齐相应 gate。

## 基础设施

标准与规划：

- [陆军画像](../../standards/services/army.zh.md)
- [Ground 标准总览](../../standards/ground/README.zh.md)
- [Ground 最小任务结构](../../standards/ground/minimal_task_structure.zh.md)
- [Ground bootstrap plan](./ground_domain_bootstrap_plan_20260521.md)
- [Ground defect inventory](../review/ground_domain_defect_inventory_20260522.md)

已验收阶段：

- `G0 Boundary Freeze`：命名、分层模型、starter scope。
- `G1 Contract Skeleton`：Python-profile-only ground dispatch。
- `G2 Content And Test Seed`：fixture root 与 unit contracts。
- `G3 Execution Surface Design`：选择安全的 tasking-only G4 切片。
- `G4 Runtime Slice`：验收 normalized `TaskOrder -> LeaderIntent -> PilotReport` 生命周期证明。
- `G5 MVP Scenario`：第一版规范 `scenarios/ground/` tasking smoke 壳。
- `G6 Realism Gradient MVP Scenarios`：前两个 G1 static occupy/support
  relationship fixture 与聚焦验证。
- `G6-C Route-Move Boundary`：fail-closed profile hints 与 architecture
  guardrails；route movement 仍保持 held。

内容与场景：

- [ground_platoon_starter.seed](../../../examples/config/database/ground/units/ground_platoon_starter.seed)
  仅是规划/内容种子。它有意不被 runtime database loader 自动加载。
- [ground_platoon_tasking_smoke_v1.json](../../../scenarios/ground/ground_platoon_tasking_smoke_v1.json)
  是第一版规范 ground 场景壳。它使用 `Aircraft` 兼容 spawn 类型，并明确声明这不是维护中的 ground platform schema。
- [ground_platoon_static_occupy_v1.json](../../../scenarios/ground/ground_platoon_static_occupy_v1.json)
  是第一版 G1 static occupy/status fixture。
- [ground_platoon_support_relationship_v1.json](../../../scenarios/ground/ground_platoon_support_relationship_v1.json)
  是第一版 G1 support relationship fixture。

合同与测试：

- [task_order_ground_profile_defaults.json](../../../tests/contracts/unit/ground/task_order_ground_profile_defaults.json)
- [task_order_ground_minimal_structures.json](../../../tests/contracts/unit/ground/task_order_ground_minimal_structures.json)
- [task_order_ground_support_relationships.json](../../../tests/contracts/unit/ground/task_order_ground_support_relationships.json)
- [test_ground_profile_semantics.py](../../../tests/leader/test_ground_profile_semantics.py)
- [test_ground_runtime_lifecycle_bridge.py](../../../tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py)
- [test_ground_mvp_scenario.py](../../../tests/runtime/ground/test_ground_mvp_scenario.py)
- [test_ground_realism_gradient_mvp_scenarios.py](../../../tests/runtime/ground/test_ground_realism_gradient_mvp_scenarios.py)
- [test_ground_realism_gradient_guardrails.py](../../../tests/architecture/test_ground_realism_gradient_guardrails.py)

基础设施缺口：

- 尚无 `src/components/tasking/ground/` DTO 目录；
- 尚无 `src/components/command/ground/` command 目录；
- 尚无 ground-specific C++ enums 或绑定面；
- 尚无 formal P2 stage-node manifest 用于 tasking 可见性；
- 尚无 runtime-loadable ground unit schema 或 capability-bundle lowering 路径。

## 域状态

已经实现的 ground 语义：

- 维护中的特化名：`ground`；
- 别名：`army`、`ground`、`land`；
- 军种画像：`Army`；
- 第一 tight-loop owner：以排为中心的 tactical unit；
- starter tasks：
  - `TASK_MOVE` 映射到共享 movement/transit intent；
  - `TASK_OCCUPY` 映射到共享 defend/hold intent；
  - `TASK_SUPPORT` 映射到共享 support relationship semantics；
- command/support anchor 会保留 `parent_node_id`、`supported_node_id`、
  `supporting_node_id`、`task_group_id` 和 `officer_in_tactical_command`。

已声明但尚未实现的 runtime 特性：

- 地形遮蔽和视线约束的感知；
- 无线电距离约束的 shared tactical picture；
- 未来的 `ground_visual`、`ground_acoustic`、`ground_mobility`、
  `direct_fire_platform`、`indirect_fire_battery` 和 `land_tactics`
  capability families；
- tasking 的 `1 Hz` 战术评估基线，movement 和 sensing cadence 仍 deferred。

边界：

- `services/army` 解释共享 contract 的 Army 含义；它不是 runtime stack。
- `ground` 负责未来执行语义；当前实现停在 tasking-chain status。
- G5 场景不能作为 ground movement、route traversal、terrain masking、cover、sensing、track fusion、fires、effects、suppression、damage 或 combat 的证据。

## RL 对接

已有 RL/tasking 对接：

- [ground_profile.py](../../../python/rl/profile/ground_profile.py) 负责 ground task defaults、observation task codes、tactical-unit inference，以及最小兼容 mission-command builder。
- [ground_adapter.py](../../../python/rl/tasking/ground_adapter.py) 通过 tasking bridge 暴露 ground profile。
- [bridge.py](../../../python/rl/tasking/bridge.py) 将 `army`、`ground`、`land` 和 `ServiceProfile.Army` 解析到 ground adapter。
- 未知的显式 loader `tasking_profile` 或 `service_profile` hint 现在会以
  `ValueError` fail closed；只有完全没有 profile hint 时，才保留 legacy
  air default。
- [common_core_profile.py](../../../python/rl/tasking/common_core_profile.py) 在保留 Army/ground ID 和 support relationship 的同时，应用共享 `TaskOrder`、`LeaderIntent`、`PilotReport` 默认值。
- [world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py) 与
  [cooperative_world_batch_vec_env.py](../../../python/rl/runtime/cooperative_world_batch_vec_env.py)
  从共享 tasking bridge 导入 `build_kernel_mission_command`，并通过 maintained task/intent/report batch assignments 推送 command-chain state。
- Scenario-loader runtime state 和 behavior command-chain 路径消费同一个 tasking bridge，而不是直接绑定 air-only tasking helper。

当前限制：ground RL 已有 profile 选择、task defaults、observation codes 和 command-chain plumbing。它还没有专用 learned ground policy、ground action space、reward model、curriculum、evaluation suite，也没有维护中的 ground-specific observation/export surface。

## 验证

采样时间：`2026-05-24 21:35 CST`。

已通过：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/leader/test_ground_profile_semantics.py tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py tests/runtime/ground/test_ground_mvp_scenario.py
# 15 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/ground/task_order_ground_profile_defaults.json tests/contracts/unit/ground/task_order_ground_minimal_structures.json tests/contracts/unit/ground/task_order_ground_support_relationships.json
# PASS x3

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/ground/test_ground_realism_gradient_mvp_scenarios.py
# 2 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/leader/test_ground_profile_semantics.py tests/architecture/test_ground_realism_gradient_guardrails.py
# 14 passed
```

## 后续重点

建议下一步：

1. 先决定 G2 route-move implementation path：要么先有 runtime-loadable
   ground platform schema，要么写清楚 explicit movement compatibility
   boundary。
2. 保持已接受的 G6-C guardrails 生效：无 private ground runtime path、G1
   fixture 不声明 G2+ realism、未知显式 profile hint fail closed。
3. 在 G2 movement boundary 被接受前，不添加
   `ground_platoon_flat_route_move_v1`。
4. 在 ground command vocabulary 被验收前，继续把 `build_kernel_mission_command()` 视为 compatibility shell。
5. 只有在 observation、action、reward、termination 和 eval surface 定界后，再定义第一个真实 ground RL task。可信的第一步应是静态 `ground_occupy_status` 或 `ground_support_relationship`，先于任何 maneuver、terrain 或 fires policy。
