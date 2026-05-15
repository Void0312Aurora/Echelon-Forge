# 多 Agent 协同训练底座与性能计划

状态：`2026-05-11` 调研计划草案。

文档定位：

- 本文档用于规划真正的多 agent 协同训练底座，不是单机编队提示的延伸说明。
- 目标是把“同一 world 内多个可控实体”的 roster、观测、动作、协调与训练入口统一起来。
- 本文档同时把性能优化列为一级约束，因为多 agent 会天然放大观测、推理、同步和内存开销。
- 本文档不授权立即引入 `TwoShipEnv` 式专用孤岛；接口必须面向 `N` 个同 world 可控实体。

## 一、核心判断

当前仓库已经具备协同执行相关的局部材料，但还没有真正的多 agent 底座：

- `ScenarioRuntime` / `ScenarioLoader` 已能在同一 world 中 spawn 多实体，但 `agent_id` 仍只选第一个 `is_agent: true` 实体。
- `UniversalEnv` 仍是单 `agent_id` 的观测、动作、奖励闭环。
- `WorldBatchRuntime` / `RuntimeFacade` 已支持按 `WorldEntityRef(world_index, entity_id)` 批量访问，但 Python 训练/环境层还没有按 entity roster 组织。
- `LeaderTrainingEnv` 已验证“高层协调 + 执行层飞行”的分层思想，但它仍是单执行机窗口，不是多机协同环境。

因此，多 agent 协同训练的第一步不是“再造一个双机环境”，而是补齐：

```text
同一 world 内多个可控实体的 roster / refs / observation / action / coordination 映射层
```

## 二、设计边界

### 2.1 多 agent 不是多 world

`n_envs` 解决的是并行 world 数量，不是单 world 内 agent 数量。

本计划关注的是：

- 一个 world 里有多个可控实体。
- 这些实体可能共享一个 policy，也可能按 role 分配不同 policy。
- 这些实体可以部分脚本化，部分由学习策略驱动。

### 2.2 协同层不是机体本身

长机层 / coordination director 负责生成编队与协同意图，不等于长机飞机本身。

推荐链路：

```text
C2 / TaskOrder
  -> Coordination Director
  -> per-platform MissionCommand / LeaderIntent
  -> per-platform execution policy
  -> PilotAction
  -> WorldBatchRuntime step
```

### 2.3 观测必须服从现实可获得原则

执行层输入只能来自现实可获得的信息产品：

- 自身座舱/仪表
- 任务系统/无线电/数据链
- 目视/雷达/IRST/RWR
- 已建模的友机相对信息

不能因为训练方便而把全局真值、内部 reward 误差或训练器状态塞进 policy。

## 三、已有设施

可直接复用的基础设施：

- `RuntimeFacade` / `WorldBatchRuntime`
  - 批量写入 `PilotAction`、`MissionCommand`、`TaskOrder`、`LeaderIntent`、`PilotReport`
  - 批量读取 `AgentObservation`、`InstrumentState`、command/tasking/report
- `ScenarioRuntime`
  - 已能 spawn 多实体并保留 `entities: name -> entity_id`
- `ScenarioLoader`
  - 已有 `mission_command`、`contacts`、`visual`、`track`、`leader_intent` 等数据链
- `LeaderBatchedVecEnv`
  - 已验证 batch 推理与 shared runtime 调度
- `WorldBatchVecEnv`
  - 已有 world batch 运行、reset、step、回读框架

缺口在于：

- roster 约束缺失
- 单 world 多实体 observation/action 路由缺失
- 多 agent policy routing 缺失
- 性能预算和 benchmark 护栏缺失

## 四、性能风险

多 agent 协同训练会放大以下成本：

1. 观测成本
   - contacts / visual / datalink / radar products 按 agent 复制
   - 大张量重复打包与 Python/C++ 交界开销
2. 推理成本
   - 单 shared policy 需要更大 batch
   - 多 role policy 会增加 forward 次数
3. 步进成本
   - 每个 agent 的动作写入、状态回读、reward 汇总都会放大
4. 同步成本
   - 多 agent 共享 world 时，任何一个成员的等待都会影响整批 step
5. 内存成本
   - rollout buffer、obs cache、visual cache、track cache 都会按 agent 放大
6. 序列化成本
   - Python dict / list / numpy 结构在高频路径里会很贵

## 五、优化原则

1. 先保留单一 world-step 真值源，不拆散仿真 truth。
2. 优先复用 batch runtime 和 facade，不新建专用双机 runtime。
3. roster、role、policy_route 这类元数据与 execution policy 输入分离。
4. 观测尽量采用 packed array / structured batch，而不是深层 Python dict 嵌套。
5. 共享 policy 优先做 batch forward；按 role 多 policy 也要保留批处理入口。
6. 视觉、雷达、contacts 等高成本输入按需启用，默认只给最必要的成员或最低频率。
7. 先做 benchmark，再做优化；不要先写一堆分支再猜性能。

## 六、建议工作包

### WP1：Roster 与实体引用层

- 让 scenario / loader 明确返回 active controllable roster。
- 把 `world_index / entity_id / entity_name / role_code / element_id` 作为统一引用。
- 明确 leader / wingman / passive entity 的归属。

### WP2：多 agent observation / action 契约

- 定义单 world 多实体观测包的最小结构。
- 定义 per-agent action routing 与 policy route。
- 保留现实可获得原则，禁止新建训练专用角色字段直接进 policy。

### WP3：VecEnv 与训练入口改造

- 让训练入口支持单 world 多 agent 的 rollout。
- 支持 shared policy 与 role-split policy 两种路由。
- 保持现有单 agent 入口可兼容。

当前进展：

- 已新增 `agent_layer = "cooperative_execution"` 训练入口。
- 已新增 `python/rl/cooperative_world_batch_vec_env.py`，把同一 world 内的 active roster 成员展开为 flat VecEnv slots，并共享同一次 world step / reset。
- 当前已打通 shared-policy cooperative rollout，且保持原有 `execution` / `leader` 入口不变。
- 现阶段的 role-split policy 仍停留在 roster / `policy_route` 元数据与 VecEnv 辅助查询层，尚未在 `train.py` 中接入多 policy 训练闭环。
- 已补 smoke / SB3 rollout / 训练入口合同测试，验证双机 cooperative execution 路径可跑通。

### WP4：协同层与脚本化 director

- 把长机/协同意图从飞机执行本体中剥离出来。
- 先支持脚本化 coordination director，再逐步支持 RL director。

当前进展：

- 已在 `python/rl/cooperative_world_batch_vec_env.py` 中接入 world-level scripted coordination director。
- director 以 world 为单位更新各 slot 的 `mission_cmd / task_order / leader_intent / pilot_report`，再复用现有 batch command chain 下发。
- 已补定向测试，确认 cooperative execution 中不同成员可以获得不同的 formation offsets，且训练入口保持可用。

### WP5：性能基线与 benchmark

- 建立单 agent / 双 agent / 多 agent 的统一 benchmark。
- 记录 per-agent step time、policy forward time、observation build time、memory footprint。
- 分开测 Python 组装、C++ runtime、GPU helper 和模型推理。

当前进展：

- 已新增 `python/rl/multi_agent_benchmark.py` 与 `scripts/benchmark_multi_agent.py`，形成可重复执行的性能基线入口。
- 当前基线已覆盖：
  - `single_agent`
  - `leader`
  - `cooperative_execution`
  - `all` 聚合模式
- cooperative 路径已在 `CooperativeWorldBatchVecEnv` 中补齐 `collect_step_timing / last_step_timing / last_reset_timing`，从而与现有 single-world / leader / world-batch timing 口径对齐。
- 已新增正式 cooperative 巡航场景：
  - `scenarios/cruise/cooperative_cruise_waypoints_paramroute_navv2_formation_train_v1.json`
- 已补 benchmark smoke test，并验证：
  - `tests/runtime/test_multi_agent_benchmark.py`
  - `tests/runtime/test_cooperative_world_batch_vec_env.py`
- 当前 cooperative smoke 基线已经能输出每步 JSON 指标，包括：
  - `per_agent_step_time_ms`
  - `action_prepare_ms`
  - `batch_step_ms`
  - `state_read_ms`
  - `behavior_update_ms`
  - `command_sync_ms`
  - `obs_build_ms`
  - `reward_info_ms`
  - `rss_bytes`

WP5 当前判断：

- 基线入口已具备，可作为 WP6 的优化前对照。
- 还没有形成更大规模的多 world / 多 slot 数据表，也还没有把 leader 冻结模型推理与 cooperative shared-policy rollout 放到同一批实验记录中；这属于 WP5 的扩展采样，不再阻塞进入 WP6。

### WP6：性能优化

- 对高频 observation packing 做 C++/batch 化。
- 对 contacts / visual / track 生成做缓存与低频更新策略。
- 对共享 policy 做批推理，对多 policy 做 route-aware batching。

建议切口：

- 先盯 `obs_build_ms`、`state_read_ms`、`behavior_update_ms` 这三项，它们已经在 cooperative 基线中可直接观测。
- 第一批优化优先级建议为：
  1. cooperative observation build 的批量化与缓存
  2. cooperative state read / packet export 的批量化收口
  3. shared policy forward 的批推理接入

当前进展：

- 已完成 cooperative runtime 的第一轮热点收口，改动集中在 `python/rl/cooperative_world_batch_vec_env.py` 与训练 / benchmark 入口，不改仿真语义。
- 已接入并验证的优化项：
  - cooperative state read 改为复用 `_RuntimeFacadeAdapter.read_truth_and_instruments(...)`，去掉 per-world packet 到 Python dict 的二次映射。
  - cooperative visual observation 补齐 per-slot cache，并真正服从 `visual_update_interval`。
  - cooperative observation build 已接入现有 batch-capable 设施：
    - `batch_observation_backend`
    - `batch_visual_backend`
  - `train.py` 的 `agent_layer = "cooperative_execution"` 分支已接收并打印 cooperative observation / visual backend。
  - `python/rl/multi_agent_benchmark.py` 已支持从训练配置读取 cooperative runtime backend，并在 benchmark notes 中回显 effective backend。
- 已新增 / 更新验证：
  - `tests/runtime/test_cooperative_world_batch_vec_env.py`
  - `tests/runtime/test_multi_agent_benchmark.py`
  - `tests/runtime/test_train_entry_cooperative.py`
- 已将 `ScenarioLoader.compute_full_step(...)` 的 step-eval 入口改为可选缓存消费，并在 cooperative vec env 里直接复用已准备的 `step_evaluation`，避免 reward 热路径重复重建。
- 已补回归测试，确认缓存命中时不再重新构建 step-eval，且 reward / termination / status 与基线一致。
- 当前 `.venv` benchmark smoke：
  - `n_envs=1`：`step_time_ms ~= 1.28`，`reward_info_ms ~= 0.087`
  - `n_envs=4`：`step_time_ms ~= 4.76`，`reward_info_ms ~= 0.348`

WP6 第一轮 benchmark 结论：

- 在当前 cooperative 巡航 smoke 基线下，默认 `auto -> legacy` 更稳妥；compiled observation 路径已经打通，但在当前 2-slot / 8-slot 规模下尚未稳定跑赢 legacy，因此保留为显式可选能力，而不是默认主路径。
- `n_envs=1`、2 slots、8 steps、默认 backend（legacy）下，cooperative benchmark 当前约为：
  - `step_time_ms ~= 1.22`
  - `per_agent_step_time_ms ~= 0.61`
  - `obs_build_ms ~= 0.49`
  - `state_read_ms ~= 0.015`
- 相比 WP5 进入 WP6 前的 smoke 基线（约 `step_time_ms ~= 1.31`、`obs_build_ms ~= 0.54`、`state_read_ms ~= 0.070`），当前结果说明：
  - state read 路径已经明显收口；
  - observation build 也有下降；
  - cooperative 路径现在已经具备可比较的 observation backend / visual backend 护栏。
- `n_envs=4`、8 slots 的当前默认 smoke 结果约为：
  - `step_time_ms ~= 4.97`
  - `per_agent_step_time_ms ~= 0.62`
  - `obs_build_ms ~= 2.36`
  - `behavior_update_ms ~= 1.02`
  这说明 cooperative 扩展到多 world 后，新的第一热点已经更偏向：
  1. per-slot `update_behaviors(...)`
  2. per-slot reward / info 汇总
  3. world 内 observation build 的进一步 fused/batched 化

WP6 当前判断：

- 第一轮 cooperative runtime 热点治理已完成，且已通过 smoke / benchmark / 训练入口合同测试。
- 现阶段不建议把 compiled cooperative observation backend 设为默认值；应继续以 benchmark 驱动后续切换。
- WP6 后续若继续深挖，优先级建议更新为：
  1. `behavior_update_ms`：评估何时可安全切入更窄的 command-chain-only / mainline runtime path
  2. `reward_info_ms`：减少 per-slot Python info/step-eval 重建
  3. 更大 world/slot 规模下的 observation fused 路径再评估

### WP6 后续拆解

为避免“性能优化”继续发散，WP6 后续只做下面 4 个闭环，每个闭环都必须绑定 benchmark 与回归测试：

#### WP6.1：`behavior_update_ms` 收口

- 目标：减少每个 slot 的行为更新开销。
- 只允许做两类判断：
  - 是否能在协同场景里安全使用更窄的 `update_command_chain_only(...)`
  - 是否能把 world-level scripted director 的更新频率再降一级
- 不允许：
  - 直接把所有 cooperative 场景切成 command-chain-only
  - 因为提速而跳过 waypoint / transition 语义
- 验收：
  - 现有 cooperative smoke 不退化
  - `n_envs=4` 基线下 `behavior_update_ms` 可量化下降，或确认无安全收益并停止

当前结果：

- 已完成第一轮收口，`ScriptedCooperativeCoordinationDirector` 现在会在 world 级 dirty 状态未变化时跳过重复更新。
- 这一步不改变 mission / formation 语义，只避免每步重复重写同一套编队与角色元数据。
- 已重新跑 smoke / benchmark，4 world、8 slot 基线下 `behavior_update_ms` 已从约 `1.02 ms` 降到约 `0.74 ms`，`step_time_ms` 约从 `4.97 ms` 降到 `4.09 ms`。
- 已新增回归测试，锁住“未变化时不重复更新”的行为。

WP6.1 当前判断：

- 已完成并验证。
- 下一步若继续压 `behavior_update_ms`，就要进入更窄的 command-chain-only / mainline runtime 评估，而不是继续在 scripted director 上做微调。

#### WP6.2：`reward_info_ms` 收口

- 目标：减少 per-slot `compute_full_step(...)` 周边的 Python info / step-eval 重建。
- 优先路径：
  - 复用已缓存的 step evaluation
  - 仅在同构 mission 配置下启用 batch prepare
- 不允许：
  - 为了省时把 reward 语义改成简化版
  - 直接绕开现有 safety / approach / landing 评估链
- 验收：
  - `reward_info_ms` 在 cooperative benchmark 中下降
  - 结果与现有 smoke / reward 回归一致

当前状态：

- 已完成。
- 现已由 cooperative vec env 直接传递缓存的 `step_evaluation`，`compute_full_step(...)` 在命中缓存时不再重建 step-eval。
- 回归测试已覆盖缓存命中与基线一致性。

#### WP6.3：`obs_build_ms` 再评估

- 目标：在更大 slot 规模下决定 compiled observation backend 是否值得默认启用。
- 只做 benchmark 驱动，不新增观测字段。
- 重点对比：
  - `legacy` vs `compiled`
  - `n_envs=1 / 4 / 8`
  - `include_visual=false / true`
- 验收：
  - 形成明确的默认策略结论
  - 如果 compiled 不能稳定赢过 legacy，就继续保持显式 opt-in

当前状态：

- 已完成。
- benchmark 显示 compiled observation 在当前 cooperative cruise smoke 上没有稳定赢过 legacy，`include_visual=true` 时优势更不明显。
- 当前 active cooperative 配置保持 `batch_observation_backend=legacy`，`batch_visual_backend=compiled`。

#### WP6.4：基线矩阵收束

- 目标：避免后续所有优化都只看单一 smoke。
- 至少固定三组对照：
  - `1 world / 2 slots`
  - `4 worlds / 8 slots`
  - `visual on/off`
- 记录项固定为：
  - `step_time_ms`
  - `per_agent_step_time_ms`
  - `obs_build_ms`
  - `state_read_ms`
  - `behavior_update_ms`
  - `reward_info_ms`
  - `rss_bytes`
- 这一步结束后，WP6 就进入“是否继续优化”决策，而不是继续扩范围。

当前状态：

- 已完成。
- 固定矩阵结果如下：
  - `1 world / 2 slots / visual off`: `step_time_ms ~= 1.334`, `obs_build_ms ~= 0.594`, `state_read_ms ~= 0.0188`, `behavior_update_ms ~= 0.235`, `reward_info_ms ~= 0.0907`
  - `1 world / 2 slots / visual on`: `step_time_ms ~= 1.801`, `obs_build_ms ~= 1.107`, `state_read_ms ~= 0.0150`, `behavior_update_ms ~= 0.206`, `reward_info_ms ~= 0.0783`
  - `4 worlds / 8 slots / visual off`: `step_time_ms ~= 4.126`, `obs_build_ms ~= 2.058`, `state_read_ms ~= 0.0562`, `behavior_update_ms ~= 0.754`, `reward_info_ms ~= 0.300`
  - `4 worlds / 8 slots / visual on`: `step_time_ms ~= 6.533`, `obs_build_ms ~= 4.340`, `state_read_ms ~= 0.0532`, `behavior_update_ms ~= 0.719`, `reward_info_ms ~= 0.299`
  - `8 worlds / 16 slots / visual off`: `step_time_ms ~= 7.812`, `obs_build_ms ~= 4.015`, `state_read_ms ~= 0.108`, `behavior_update_ms ~= 1.382`, `reward_info_ms ~= 0.595`
  - `8 worlds / 16 slots / visual on`: `step_time_ms ~= 13.264`, `obs_build_ms ~= 8.759`, `state_read_ms ~= 0.101`, `behavior_update_ms ~= 1.364`, `reward_info_ms ~= 0.596`
- 结论：compiled observation 仍未在当前 cooperative 扩展矩阵中形成稳定优势，visual 打开时成本更高，因此继续保持显式 opt-in，不把它升级为默认主路径。

## 七、验收指标

至少需要验证：

- 同一 world 可同时管理多个可控实体。
- 每个 agent 都能获得自己的观测并接收自己的动作。
- shared policy / role policy 都能运行。
- 双机场景能稳定跑完 smoke。
- 多 agent 下单步开销有可量化的基线与优化结果。

## 八、当前主线状态与下一步

当前主线判断：

- cooperative execution 底座、shared-policy cooperative rollout、scripted coordination director、benchmark 护栏与第一轮性能收口已经基本完成。
- 双机 cooperative 巡航线已经具备可训练、可评估、可视化检查的闭环。
- 巡航可视化链路中的关键误差已完成修正：
  - `Lead/Wing` 不再被误判为 `Facility`；
  - F-16 模型已恢复正常显示；
  - 在 `--zero_randomization` 下，机体朝向与真实 eastbound 起始飞行方向一致。

因此，当前不再把“继续修 cooperative 巡航底座”视为主线阻塞项。后续主线应转入：

```text
双机协同起飞训练准备 -> cooperative takeoff/departure 训练线
```

下一步建议按下面顺序推进：

1. 冻结 cooperative cruise 当前基线
   - 保留当前 active cruise config 作为 cooperative execution 的已验证巡航起点。
   - 记录可视化确认结论，避免后续把模型朝向 / world yaw 问题重新引入。

2. 盘点可直接复用的起飞资产
   - 复用现有单机起飞 / departure 场景、reward、课程随机化和 `scripted_takeoff` 控制器。
   - 优先参考已冻结的单机起飞配置与 `takeoff_to_cruise` 桥接线，而不是从零新造 cooperative takeoff 机制。

3. 明确双机协同起飞训练切口
   - 第一阶段优先做“双机同跑道、共享起飞/离场程序、共享 policy”的 cooperative departure 训练。
   - 第一阶段不重写整套地面滑行/塔台系统，而是在现有 `MissionCommand -> TaskOrder -> LeaderIntent -> execution policy` 链路上补齐最小起飞口令语义：
     - `takeoff_procedure_id`：单机 / interval / wing 起飞方式；
     - `takeoff_clearance_id`：hold short / line up and wait / cleared for takeoff / rolling / airborne / abort；
     - `takeoff_interval_s`：interval departure 的放行间隔；
     - `runway_slot_id`：center / left / right 跑道占位。
   - `command_code` 仍保持粗粒度的 `takeoff / departure`，不把具体起飞方式继续塞进宏指令码。
   - 第一阶段观测使用专门的 cooperative takeoff mission obs 变体，只承载飞行员现实可获得的任务/放行语义，不引入训练器私有真值。
   - 保持现实可获得原则，不向 policy 暴露训练器私有真值。
   - 先把成功标准收敛在：
     - 安全离地
     - 跑道/离场轴线保持
     - 基本编队不相互干扰
     - 到达离场后可平滑接入后续巡航 command chain

4. 在起飞线打通前，不扩展到更复杂的双机降落或 full mission
   - 先解决 cooperative takeoff/departure 的动作耦合、跑道占用、间隔与 early climb 稳定性。
   - 等 cooperative takeoff 稳定后，再考虑与现有 cooperative cruise 连接成 bridge 任务。

## 九、非目标

- 不立即引入新的 `TwoShipEnv` 专用孤岛。
- 不把全局真值、reward 内部误差或训练器私有状态喂给 policy。
- 不在没有 benchmark 的前提下先做大规模性能重写。
- 不把 exact GPU world-step 当作多 agent 底座的前置条件。
