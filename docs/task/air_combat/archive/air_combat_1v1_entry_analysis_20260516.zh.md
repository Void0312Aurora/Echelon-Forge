# 空战 1v1 切入分析

状态：`2026-05-16` 任务分析版。

关联文档：

- [P8 协同执行管线发现与计划](../../../plan/cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md)
- [多 Agent 协同训练底座与性能计划](../../../plan/cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md)
- [HMoE Strict Terminal Eval (2026-05-15)](../../../plan/results/hmoe_strict_terminal_eval_20260515.md)
- [强化学习与自博弈前瞻](../../../forward/rl_selfplay.md)

文档定位：

- 本文档用于确认当前仓库进入 `1v1` 空战工作的实际切入点。
- 目标不是直接授权实现，而是先把“应该站在哪条已稳定主线上进入对战”说明白。
- 本文档聚焦当前维护中的训练入口、运行时环境、观测/动作合同与评估能力，不复述协同执行全量设计。

## 一、当前可信前提

截至 `2026-05-16`，可以作为 `1v1` 起点的可信前提有：

1. `execution` 单机执行训练主线仍然是最成熟、最稳定、覆盖面最完整的执行入口。
2. `cooperative_execution` 已在最近一轮 HMoE 与严格 terminal eval 中证明“同一 world 多可控实体共享 world-step / reset”的训练链可用，但它当前服务的是同队协同，不是敌对对抗。
3. 现有评估入口 [tools/eval/eval_sb3.py](../../../../tools/eval/eval_sb3.py) 只维护了 `single` 与 `cooperative` 两种口径，还没有 `versus` / `combat_1v1` 模式。
4. 旧的 [强化学习与自博弈前瞻](../../../forward/rl_selfplay.md) 仍停留在前瞻口径；文中提到的 `examples/training/train_self_play.py` 与 `examples/training/selfplay_config.json` 在当前仓库中并不存在，不能当作现成主线入口。
5. 当前 `ScenarioCompiler` / `ScenarioLoader` 维护主线只会把 `objectives` 中的 `type = "conditional"` 编译进运行时；不要把旧文档中的 `capture_zone` 说明直接当成 `1v1` 可用主线能力。

## 二、与 1v1 直接相关的现状

### 2.1 训练入口现状

[train.py](../../../../train.py) 当前只接受三类 `agent_layer`：

- `execution`
- `leader`
- `cooperative_execution`

其中：

- `execution` 走 [UniversalEnv](../../../../gym_envs/universal_env.py) 或 [WorldBatchVecEnv](../../../../python/rl/runtime/world_batch_vec_env.py)，本质是“每个 world 一个 active `agent_id`”。
- `cooperative_execution` 走 [CooperativeWorldBatchVecEnv](../../../../python/rl/runtime/cooperative_world_batch_vec_env.py)，本质是“同一 world 多个同队 controllable roster 成员展开为 flat slots，共享同一次 world step / reset”。

当前没有：

- `combat_execution`
- `versus_execution`
- `selfplay_execution`

这样的维护型训练入口。

### 2.2 运行时环境现状

[WorldBatchVecEnv](../../../../python/rl/runtime/world_batch_vec_env.py) 仍是单 active agent 语义：

- 每个 world 只维护一个 `handle.agent_id`
- 观测回读、动作下发、mission/tasking 同步都按这一个实体组织

[CooperativeWorldBatchVecEnv](../../../../python/rl/runtime/cooperative_world_batch_vec_env.py) 则已经具备：

- active controllable roster
- `world_index + entity_id` 粒度的 slot 展开
- `policy_route` / role / formation metadata
- 同 world 多实体共享 step/reset

但它的 world-level director、success 语义、slot flatten 方式目前都围绕“同队协同完成共同 objective”构建，不是敌我对抗。

### 2.3 场景 / roster 现状

[python/scenario_runtime.py](../../../../python/scenario_runtime.py) 已支持：

- 在同一 world 中声明多实体
- 解析 `active_controllable_roster` / `cooperative_roster`
- 为 roster 成员保留 `team_id`、`element_id`、`role_code`、`policy_route`、`reference_entity_id` 等元数据

这意味着：

- 当前底座已经能表达“同一 world 里存在两架或更多可控飞机”。
- 但当前维护中的 roster 语义更接近“同队协同控制面”，而不是“蓝红双方对抗控制面”。

### 2.4 观测与动作现状

[UniversalEnv](../../../../gym_envs/universal_env.py) 的 `full` 动作模式已经包含对空战有价值的基础控制语义：

- 飞行操纵
- 雷达开关与扫描
- `master_arm`
- `fire_weapon`
- `fire_gun`
- `weapon_select_id`

当前观测也已经包含：

- `instruments`
- `contacts`
- `rwr`
- `mission`

其中 `instruments` 内已有 `missiles_remaining`，`contacts` / `rwr` 已具备基础对抗感知语义。

但还需要明确一个当前约束：

- `PilotAction.master_arm / fire_weapon / fire_gun / weapon_select_id` 已经在动作接口中暴露；
- 当前武器主线并不会直接从这些 `PilotAction` 字段触发导弹发射；
- 仓库里真实可用的发射入口仍是底层 [SimulationKernel.fire_missile(...)](../../../../src/interfaces/python/bindings_core.cpp) API。
- 数据库中的不同平台对 runtime ammo 的支持也还不一致；例如当前 `F-16C_Block50` 仍是 `has_ammo: false`，而 `Su-35S_Flanker-E` 才已经带有可观测的 ammo/runtime fire state。

这说明：

- `1v1` 的动作/感知底座并不是从零开始。
- 真正的缺口不在“有没有武器字段”，而在“如何把对抗 objective、发射主链、终止条件、奖励、场景约束、评估口径组织成维护中的训练主线”。

### 2.5 任务 / mission 语义现状

当前维护中的 mission observation taxonomy 仍以：

- `basic`
- `nav_v1`
- `nav_v2`
- `nav_v2_formation_v1`
- `nav_v2_formation_role_v1`
- `nav_v2_cooperative_takeoff_v1`

为主。

这说明当前 mission block 仍然偏：

- 航路跟踪
- 编队
- 协同起飞 / 巡航

而不是：

- 空战交战阶段
- 攻防态势
- 对抗交战规则

因此 `1v1` 如果要走维护主线，至少需要新增一条对抗任务语义，而不能直接把 `nav_v2_*` 观测模式硬塞到 dogfight 里冒充完成。

### 2.6 评估现状

[tools/eval/eval_sb3.py](../../../../tools/eval/eval_sb3.py) 当前只支持：

- `single`
- `cooperative`

还没有：

- 双方胜负统计
- 蓝方 / 红方存活
- 交战时长
- 脱战
- 命中 / kill chain 结果

这些 `1v1` 最基本的评估口径。

因此 `1v1` 不能只补训练入口，不补评估口径。

## 三、为什么不应直接从 cooperative_execution 进入 1v1

`cooperative_execution` 最近的确是最活跃的新线，但它不适合作为 `1v1` 第一刀的直接承载体，原因如下：

1. 它当前的成功语义是“同 world 多友机完成共同任务”，而不是“敌我对抗下某一方获胜”。
2. 它当前的 director / roster 设计默认需要维护一组协同 intent，而 `1v1` 第一阶段更需要先把“单作战机对单敌机的执行闭环”做稳。
3. 一上来走 `cooperative_execution` 会把问题同时放大到：
   - 多 controllable roster
   - 敌我双方对抗建模
   - 多 policy 或 self-play routing
   - 新评估口径
   - 新奖励/终止合同
4. 当前 `cooperative_execution` 的价值更适合在 `2v2` 时复用，因为 `2v2` 天然需要“同队协同 + 敌方对抗”双层语义。

结论：

- `cooperative_execution` 不是不相关，而是更适合作为 `2v2` 阶段的直接底座。
- `1v1` 第一阶段更应该复用稳定的 `execution` 主线，把对抗任务闭环单独建立起来。

## 四、推荐切入点

### 4.1 首选：基于 `execution` 主线扩展 `1v1` 对抗任务

推荐第一阶段站在 `execution` 主线上推进，原因：

1. 训练入口最稳。
2. 单 active agent 的 reward / done / info / eval 契约已经成熟。
3. 当前动作/观测已经具备基础空战控制语义。
4. 可以把变量控制在“单学习机 + 单敌方脚本/冻结对手”的最小集合。

对应含义是：

- 第一阶段不急着做真正双边同时学习。
- 先把 `1v1` 场景、奖励、终止、评估、日志和配置入口做成维护主线。
- 对手优先使用脚本体或冻结策略体，而不是一开始就上 self-play。

### 4.2 第二阶段：在 `1v1` 主线上引入 frozen opponent / policy pool

当第一阶段的 `1v1` 任务闭环稳定后，再往上加：

- 冻结 checkpoint 作为对手
- 简单 opponent pool
- 对抗评估脚本

这一阶段仍然可以保持：

- 学习侧只有一条 `execution` policy
- 对手侧不进入同一个 PPO 更新闭环

### 4.3 第三阶段：再考虑 self-play 或双边对抗训练

只有当下列能力已经稳定，才适合进入 self-play：

1. `1v1` 对抗 reward / termination / eval 口径稳定
2. 脚本 / 冻结对手基线已经可复现
3. 训练与评估入口已经能稳定记录胜率、时长、终局原因

否则直接进入 self-play 很容易把“任务合同不稳”和“策略学习不稳”混在一起。

## 五、对后续 2v2 的含义

如果 `1v1` 按上面的路径推进，那么后续 `2v2` 的承接关系会更清楚：

1. `1v1` 阶段沉淀：
   - 对抗场景 contract
   - 奖励 / 终止 contract
   - 对抗 eval 口径
   - 脚本 / 冻结对手机制
2. `2v2` 阶段复用：
   - cooperative roster / slot 展开
   - `policy_route`
   - 同 world 多实体 step/reset
   - world-level coordination director

换言之：

- `1v1` 先解决“对抗任务是什么”。
- `2v2` 再解决“在对抗任务下如何做同队协同”。

## 六、建议的任务边界

当前最合理的任务边界应冻结为：

1. 先做 `1v1`，不直接并入 `2v2`。
2. 先做“单学习机 vs 脚本/冻结对手”，不直接进入双边 self-play。
3. 先基于 `execution` 主线扩展对抗任务，不直接把 `cooperative_execution` 改造成对抗主入口。
4. 先补训练、场景、奖励/终止、评估四件套，再谈 HMoE、双 policy routing 或历史策略池。

## 七、结论

当前仓库已经具备进入 `1v1` 的不少基础设施，但真正可靠的切入点不是“直接上自博弈”，也不是“把 cooperative 反过来当敌对环境用”。

更稳妥、也更符合当前项目演进状态的路径是：

1. 以 `execution` 作为第一阶段训练主线；
2. 新建空战 `1v1` 的场景 / reward / termination / eval 合同；
3. 先用脚本或冻结对手把最小对抗闭环做稳；
4. 再在第二阶段进入更强的 frozen-opponent / policy-pool；
5. 最后才把真正的 self-play 与 `2v2` 协同对抗接进来。
