# 二级等价算法优化候选集

状态：`2026-05-18` 活跃规划草案。  
范围：当 Level 1 实现优化开始出现明显边际递减后，汇总当前 Level 2 候选、迭代边界与停止规则。

关联文档：

- [runtime 性能优化分层与升级规则](performance_runtime_optimization_ladder_20260518.zh.md)
- [一级实现优化分析](performance_runtime_level1_implementation_analysis_20260518.zh.md)
- [一级 runtime 优化任务板](performance_runtime_level1_taskboard_20260518.zh.md)

---

## 1. 目的

本文档不再讨论 Level 1 的实现清理。

它回答三个更窄的问题：

1. 当前这条线是否已经准备进入 Level 2；
2. 当前允许哪些 Level 2 候选；
3. 每个候选必须遵守什么迭代边界，避免再次发散。

这里的“Level 2”指的是：

- 保留任务契约；
- 保留目标语义完全等价；
- 允许计算重组、 batching 变化、增量失效规则，或精确算法结构重排；
- 不跨入近似或保真度权衡。

## 2. 为什么现在允许进入 Level 2

当前这条线已经满足进入 Level 2 的条件：

1. 第一轮 Level 1 取得了确认收益，尤其是在 cooperative 的 `command_sync_ms` 上；
2. 第二轮 Level 1 是安全的，但在长跑 probe 上整体偏中性；
3. 剩余 cooperative 成本更多像是精确 behavior 组织结构中的问题，而不是 Python 表面 churn；
4. 继续无边界挖 Level 1 已经不太符合当前时间收益预期。

因此默认结论是：

```text
当前 runtime 性能线可以从
Level-1 implementation optimization 提升到 Level-2 equivalent algorithm optimization。
```

## 3. 当前 Level 2 候选池

下面这些候选按“当前最优先”到“保留但不要先开”的顺序排列。

### L2-BEHAV-01：command-chain 精确增量重算

优先级：`P0`

目标：

- 把 cooperative / batch command-chain 更新从每步全量重建，改成带显式失效规则的精确增量重算；
- 保留 `task_order`、`leader_intent`、`pilot_report` 和 mission-command 可见性的语义。

为什么放这里：

- 剩余的 `behavior_update_ms` 热点更像精确 command-chain 逻辑问题，而不只是 orchestration 问题；
- 如果验证成立，这条路线对 cooperative 和 batch 两边都能产生收益。

允许的算法变化：

- 对 phase、route、takeoff / recovery gate 和 override 变化建立显式失效规则；
- 只在失效条件触发时重建精确结构；
- 用精确复用或精确增量更新取代每步全量对象重写。

不允许：

- 不允许改 behavior cadence；
- 不允许跳过 phase transition；
- 不允许引入“通常等价”的 shortcut 来做近似。

### L2-NAV-01：waypoint-guidance 精确批处理 / 结构化导出

优先级：`P1`

目标：

- 把逐 slot 的精确 waypoint-guidance 查询收拢成更结构化的 batch 或共享导出路径；
- 保持 route guidance、LNAV 和 waypoint sequencing 输出完全一致。

为什么放这里：

- 子切片 timing 仍显示 waypoint guidance 是 cooperative `behavior_update_ms` 的可见组成部分；
- 工作形态天然适合做多 slot 的精确查询共享。

允许的算法变化：

- 精确 batch query 路径；
- 精确 world-shared route-product 导出与再分发；
- 带显式 key 和失效规则的精确 guidance cache。

不允许：

- 不允许降低 waypoint 产品更新频率；
- 不允许更改 sequence gate、turn lead 或 commanded track 的定义。

### L2-BEHAV-02：leader / task / report 精确对象复用与导出重组

优先级：`P1`

目标：

- 减少每步对 `leader_intent`、`task_order` 和 `pilot_report` 的重建，同时保持语义等价；
- 允许精确对象复用、精确 field-diff 更新或更结构化的 batch 导出。

为什么放这里：

- 这是 `L2-BEHAV-01` 的自然伴随方向；
- 如果 command-chain 重组只吃到一部分收益，这会是下一个精确 behavior 侧扩展。

允许的算法变化：

- 复用稳定 runtime 对象；
- 精确 dirty-bit / version 驱动导出；
- 用精确 diff 驱动更新替代全量精确重建。

不允许：

- 不允许省略 kernel 必须可见的更新；
- 不允许降低 task-contract 字段的新鲜度。

状态更新（`2026-05-18`）：

- 该候选已经完成两轮实现；
- 基于精确 snapshot 的稳定导出跳过，在 single-world 与 cooperative
  两条路径上都已验证语义安全；
- 即使收紧 mission snapshot 切点后，基准收益仍不足以形成可重复改进，
  cooperative execution 面也仍未超过更早的 `L2-NAV-01` 基线；
- 因此按“两轮停止规则”冻结该候选。

### L2-EVAL-01：reward / info 精确尾部批处理

优先级：`P2`

目标：

- 进一步把 `compute_full_step(...)` 和 info 导出结构化为更大的精确 batching；
- 只有在 Level 1 的 `L1-TAIL-01` 明显耗尽后才开始。

为什么放这里：

- Level 1 的尾部收紧已经带来第一轮明确收益；
- 如果剩余尾部成本本质上还是结构化的 exact reward evaluation，而不是 caller 侧物化，它就属于 Level 2。

当前限制：

- 这不是默认第一候选；
- 只有当新测量再次显示 reward/info tail 是主要瓶颈时，才允许启动。

状态更新（`2026-05-18`）：

- 该候选已经完成两轮实现；
- 第一轮去掉了主线 request-build 路径中冗余的 `ExecutionEpisodeState`
  物化，并在已验证的 `execution_episode_controller_mainline=True`
  控制面上取得可重复收益；
- 第二轮收紧了 steady-state loader mirror，使主线的非结构变化步不再重复
  重建 navigation structure 壳，并再次在 `reward_info_ms`、
  `loader_consume_ms` 和 `total_ms` 上取得可重复收益；
- 因此该候选在当前 Level-2 候选池内已视为完成；除非后续重新测得仍在
  本候选边界内的新尾部热点，否则应冻结。

### 保留但不活跃：脚本对手按 world 合并

状态：先保留为已观察到的可能性，但不进入活跃 Level 2 候选集。

原因：

- cooperative world 中按 slot 重复的 `update_scripted_opponents(...)` 已被确认；
- 但不同 slot loader 可能会把同一个 scripted opponent 绑定到不同的 `target_id`；
- 这首先是 owner / target-selection 语义问题，而不是默认的等价算法优化。

结论：

- 在 owner 语义被显式定义之前，这个候选不能提升到活跃工作。

## 4. 最大迭代次数

为了防止再次发散，Level 2 工作必须遵守更严格的轮次上限。

全局规则：

1. 每个候选最多做 `2` 轮实现；
2. 每轮只能处理 `1` 个候选；
3. 一轮内不得横向扩展到第二个候选；
4. 如果一个候选在 `2` 轮内没有产生可重复收益，就必须冻结。

解释：

- 第一轮用来证明这条结构方向到底值不值得做；
- 第二轮只允许作为在首次确认收益上的收紧或收尾；
- 如果第一轮就是中性结果，默认不应进入第二轮，除非更细测量证明切点错了而不是方向错了。

## 5. 任一轮次的进入规则

在开始实现前，每个 Level 2 候选都必须满足以下条件：

1. 已经存在 benchmark / control surface；
2. 已选择一个主目标指标；
3. 已达到进入阈值；
4. 已明确说明语义非目标。

### 5.1 Benchmark / 控制面限制

默认只允许以下 surface 的子集：

1. `world_batch_vec_env`
