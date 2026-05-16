# 空战 1v1 F-16C 基线切换与最小对战合同进展

状态：`2026-05-16` 当前轮已落地。

关联文档：

- [空战 1v1 冻结计划](/home/void0312/Workshop/CMO/docs/task/air_combat/air_combat_1v1_freeze_plan_20260516.zh.md)
- [空战场景级 Ammo 设计与落地](/home/void0312/Workshop/CMO/docs/task/air_combat/air_combat_scenario_level_ammo_design_20260516.zh.md)
- [空战 1v1 武器链进展](/home/void0312/Workshop/CMO/docs/task/air_combat/air_combat_1v1_weapon_chain_progress_20260516.zh.md)

## 一、这轮完成了什么

这轮把 `1v1` 的 canonical 基线从通用 `Aircraft` 正式切到了对称 `F-16C_Block50 vs F-16C_Block50`。

当前维护场景：

- [air_combat_1v1_headon_sensor_smoke_v1.json](/home/void0312/Workshop/CMO/scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json)

切换方式不是去改平台数据库默认 `has_ammo`，而是继续沿用前一轮已经打通的场景级覆盖语义：

1. 平台仍保留真实机型 `F-16C_Block50`；
2. 场景层显式声明双方 `ammo` 与 `weapon_cooldown`；
3. 因此基线训练机体终于可以回到真实平台，而不是退回通用壳体。

## 二、这轮顺手补上的最小对战合同

这轮没有把完整 `1v1` 训练体系一次性做完，但补上了两个真正推进主线的连接点：

1. `mission_command.assigned_target_name / assigned_target_id` 会在 `ScenarioLoader` 装载时解析为主目标；
2. `execution` 主线的 objective 输入面现在可以识别：
   - `target_active`
   - `target_health`
   - `self_active`
   - `self_health`
   - `missiles_remaining`
   - `target_range_m`

因此，当前 `1v1` 场景已经可以用维护型 `conditional objective` 直接表达：

1. “主目标已被击毁”；
2. 并把它映射为最小胜利终止。

本轮同时补了最小 execution 终止覆盖：

1. `combat_win`
2. `combat_loss`
3. `combat_draw`
4. `combat_timeout`

这里仍然是第一阶段语义，不代表完整对抗评分体系已经完成。

## 三、这轮新接通的发射桥

仅切场景还不够，因为现有 `UniversalEnv` 的 `fire_weapon` 之前并不会走到维护型 `fire_missile()`。

这轮补的最小桥接是：

1. `PilotAction.master_arm && fire_weapon`
2. 优先读取 `MissionCommand.assigned_target_id`
3. 若当前有有效敌方 track，则调用 `SimulationKernel.fire_missile(attacker_id, target_id)`

这意味着：

1. `1v1` 基线场景不再只能靠测试里手工调用 `fire_missile()`；
2. `UniversalEnv` 的 full action surface 终于具备最小可用的导弹释放入口；
3. 但当前仍然不是完整的武器管理系统，`weapon_select_id`、弹种选择、挂点语义仍未接通。

## 四、当前明确仍未完成的部分

这轮之后，`1v1` 比之前前进了一步，但还没有到“可以开始正式大规模训练”的完成态。

仍未完成的关键项：

1. 红方虽然已经可以接入脚本对手，但当前仍只是最小基线，不是强战术体；
2. `fire_weapon` 桥接目前只是一层最小维护型 glue，不是完整武器系统；
3. `1v1` reward 仍缺少更细的交战 shaping，比如距离、占位、能量、资源消耗；
4. `1v1` 评估 JSON 和专门 eval 入口还没冻结；
5. `2v2` 仍然不应在本轮直接进入。

## 五、脚本对手接入状态

当前 canonical `1v1` 场景已经支持在实体级声明红方脚本对手：

1. `entities[].scripted_agent`
2. 目前维护实现绑定到 [examples/agents/red_agent.py](/home/void0312/Workshop/CMO/examples/agents/red_agent.py)
3. 运行时由 `ScenarioLoader.update_behaviors()` 驱动，因此：
   - `UniversalEnv`
   - 默认 `WorldBatchVecEnv`
   - loader/runtime 聚焦测试
   这几条维护路径都会自动执行红方脚本逻辑。

当前脚本体能力边界：

1. 会根据敌方几何做最小截击/偏置/防御转向；
2. 在存在 hostile track 且进入发射距离后，会尝试发射导弹；
3. 目的是提供稳定、可复现的第一版红方 baseline，而不是模拟完整 BVR/ACM 战术。

当前已知限制：

1. 该脚本对手依赖 Python 行为更新链；
2. 因此默认不覆盖 `WorldBatchVecEnv(execution_episode_controller_mainline=True)` 这条刻意跳过 Python behavior updates 的特化路径；
3. 若后续要让 self-play / full compiled mainline 也使用对手脚本，需要把对手控制进一步下沉到 runtime/controller 层。

## 六、这轮之后最自然的下一步

这轮之后，下一步已经很明确：

1. 先冻结 `1v1` 的终止与奖励合同；
2. 明确蓝胜 / 蓝败 / 双亡 / 超时 / 弹尽未决的奖励口径；
3. 再补一个最小红方脚本或冻结对手；
4. 最后才进入真正的 `1v1` rollout 训练与 eval 入口。

建议仍保持：

1. 训练基线先用 `F-16C_Block50 vs F-16C_Block50`；
2. `F-16C vs Su-35` 保留给后续评测或 stress，不作为第一训练基线。
