# 三级近似优化候选集

状态：`2026-05-18` 谨慎规划草案。  
范围：在当前 Level 1 与 Level 2 精确优化线走到活跃候选池尾部之后，定义当前
Level 3 近似优化候选集、漂移预算与更严格的停止规则。

关联文档：

- [runtime 性能优化分层与升级规则](performance_runtime_optimization_ladder_20260518.zh.md)
- [二级等价算法候选集](performance_runtime_level2_equivalent_algorithm_candidates_20260518.zh.md)
- [一级 runtime 优化任务板](performance_runtime_level1_taskboard_20260518.zh.md)

---

## 1. 目的

本文档不是为了默认重开精确优化线。

它回答三个更窄的问题：

1. 当前 runtime 性能线是否已经允许讨论近似优化；
2. 哪些近似候选有资格进入工作；
3. 必须遵守哪些漂移边界与停止规则，才能让这条线保持可控、可回滚。

这里的“Level 3”指的是：

- runtime 收益允许来自显式接受的任务可见漂移；
- 每个候选都必须明确说明到底哪些输出允许漂移；
- 每个候选都必须保留干净的 exact 回退路径；
- 任何近似都不允许在未声明、未批准的情况下，悄悄改变 reward、
  termination、安全逻辑或 kernel 可见控制语义。

## 2. 为什么现在允许进入 Level 3

当前这条线已经满足“谨慎讨论 Level 3”的条件：

1. Level 1 已经取得首轮确认收益，并进入明显的边际递减区；
2. 当前已定义的 Level 2 候选池已经消耗完：
   `L2-BEHAV-01` 已冻结，`L2-BEHAV-02` 已冻结，
   `L2-EVAL-01` 已完成，而 `L2-NAV-01` 作为更早的 exact 胜出基线存在；
3. 仍然有剩余热点，但如果不先新立 exact 候选，继续做精确优化已不再是默认最优投入；
4. 这个项目已经在 exact 线上花费了足够多时间，因此后续 runtime 工作必须更加有选择性。

因此默认结论是：

```text
当前允许讨论 Level-3 approximate optimization，
但只能以 opt-in、benchmark 驱动、可回滚、单候选实验的形式进入。
```

## 3. 当前 Level 3 候选池

下面这些候选按照“语义风险最低”到“虽然可讨论但语义风险更高”的顺序排列。

### L3-VIS-01：视觉观测刷新频率 / 分辨率降低

优先级：`P0`

目标：

- 通过降低视觉观测刷新频率、在刷新间隔内复用上一帧 exact 画面，和/或
  在已批准 surface 上提高策略侧 downsample 因子，来降低 visual 路径成本。

为什么放这里：

- visual observation 天然与 reward、termination 和 command-chain 语义隔离；
- 这是最干净的近似方向，因为它只改变 `include_visual=True` surface 上的
  policy 输入张量；
- 仓库里已经存在 visual cache / update 机制，因此这一近似可以保持局部、可回滚。

允许的近似变化：

- 把 `visual_update_interval > 1` 作为性能优先选择；
- 在刷新步之间复用上一帧 exact visual；
- 在已批准的 policy surface 上提高 visual downsample 因子。

不允许：

- 不允许更改非视觉 observation 通道；
- 不允许更改 reward、termination、mission status 或 kernel 状态；
- 不允许在 `include_visual=False` 时引入隐藏 cadence 变化。

默认漂移预算：

- 只允许 `visual` 张量漂移；
- staleness budget 与 downsample factor 必须在实验前写明；
- 所有非视觉输出必须保持 exact。

### L3-OBS-01：contact / RWR 观测宽度缩减

优先级：`P1`

目标：

- 通过导出更少的 contact 和/或 RWR 条目，配合确定性排序规则与零填充尾部，
  来降低 policy observation 尺寸与组装成本。

为什么放这里：

- 即使做完 exact 清理，`obs_build` 仍然是可见 runtime 切片；
- 观测宽度缩减是一个直接但边界清晰的近似杠杆，不需要碰 kernel 状态或 reward 逻辑；
- 它可以被限制在 policy-facing observation 边界上。

允许的近似变化：

- 在已批准 surface 上使用更小的固定 `max_contacts` 和/或 `max_rwr`；
- 按显式排序规则（如威胁、距离、置信度、优先级分数）做确定性 top-`K` 保留；
- 对被省略的尾部做零填充，以便在需要时保持张量形状契约。

不允许：

- 不允许近似 truth state、instrument state、reward 或 termination；
- 不允许使用不确定性的 eviction 规则；
- 不允许在没有文档说明的情况下悄悄改 ranking 逻辑。

默认漂移预算：

- 只允许 `contacts` 与 `rwr` 通道省略低优先级条目；
- mission、reward、termination 与 command 输出必须保持 exact；
- 实现前必须明确保留的 `K` 与排序规则。

### L3-PREC-01：policy-facing 低精度导出路径

优先级：`P1`

目标：

- 在 exact runtime product 已经算完之后，把选定的 policy-facing 张量以更低精度
  （如 `bf16` 或 `fp16`）导出，以降低带宽、bridge 和策略输入成本。

为什么放这里：

- 剩余 runtime 线的成本不只来自 kernel compute，也来自 observation / export；
- 低精度在 GPU-facing policy 路径上可能有帮助，而不必把近似推进 exact runtime core；
- 相比 cadence 变化，这个候选更容易被限制住。

允许的近似变化：

- 对 `visual`、`mission`、`contacts`、`rwr` 或完整 flattened policy batch
  做低精度导出；
- 在支持的 GPU-oriented surface 上使用低精度 bridge 路径。

不允许：

- 不允许把低精度推进 kernel 状态演化；
- 不允许把低精度推进 reward、安全、termination 或 command-sync 逻辑；
- 不允许在 exact 参考路径上引入隐藏 dtype 漂移。

默认漂移预算：

- 只允许 policy-facing 导出张量发生量化；
- exact runtime state 与任务结果必须保持 exact；
- 实现前必须明确 dtype 变化和受影响张量。

### L3-MISS-01：mission / auxiliary observation 刷新频率降低

优先级：`P2`

目标：

- 通过降低部分 policy-facing mission observation 与 auxiliary info 字段的刷新频率，
  或仅在发生变化时刷新，来降低相关成本。

为什么放这里：

- 在尾部收紧之后，某些 surface 上 mission 与 auxiliary observation 物化仍可能重要；
- 但相比 purely visual 或 breadth-only 近似，这条线语义风险更高，因为这些通道会影响导航与策略控制。

允许的近似变化：

- 对 policy-facing mission 或 step-info 字段使用显式刷新 cadence；
- 对选定 observation 子通道使用显式的“仅变化时更新”规则。

不允许：

- 不允许降低 kernel 可见 mission command 状态的新鲜度；
- 不允许降低 reward、termination 或 safety 逻辑的刷新频率；
- 不允许在 exact 参考 surface 上悄悄复用陈旧 mission product。

默认漂移预算：

- 只允许具名的 policy-facing mission / auxiliary 字段变得陈旧；
- 最大 staleness 必须以 step 数写明；
- reward、termination 与 command 语义必须保持 exact。

当前限制：

- 这不是默认第一近似候选；
- 只有在更安全的近似候选无法满足时间预算需求时，才允许启动。

### 保留但不活跃：behavior / command cadence reduction

状态：不进入活跃 Level 3 候选集。

原因：

- 降低 behavior update cadence 或 command-sync cadence 会直接改变
  kernel 可见控制产品的新鲜度；
- 这会非常快地从“受控近似”滑向“难以审计的任务语义漂移”。

结论：

- 在没有明确任务级漂移预算批准之前，这个方向不进入活跃 Level 3 池。

## 4. 最大迭代次数

Level 3 的轮次上限必须比 Level 2 更严格。

全局规则：

1. 每个候选默认最多 `1` 轮探索性实现；
2. 第 `2` 轮只允许在 runtime 收益与行为漂移经过显式复审后进入；
3. 一轮内不得混合多个近似候选；
4. 每个候选都必须保持 runtime-toggleable，且可以轻易回滚；
5. 只要候选突破漂移预算，或缺乏清晰质量读数，就立即冻结。

解释：

- 第一轮的目的只是验证这条近似是否值得存在；
- 若批准进入第二轮，也只能用于收紧或校准一个已经被接受的近似；
- Level 3 应该比 Level 2 更早停，而不是更晚停。

## 5. 任一轮次的进入规则

在开始实现前，每个 Level 3 候选都必须满足以下条件：

1. 已经存在 benchmark / control surface；
2. 已选择一个主 runtime 指标；
3. 已选择一个质量或行为指标；
4. 已用用户可理解的方式明确写出漂移预算；
5. 已识别出干净的 exact toggle / rollback 路径。

### 5.1 Benchmark / 控制面限制

默认允许的 surface 要刻意保持狭窄：

1. `world_batch_vec_env` 或 cooperative runtime benchmark，用来衡量 runtime 收益；
2. 一个 policy 或 rollout sanity surface，用来暴露明显行为漂移；
3. 一个保持不变的 exact baseline run，用来比较。

### 5.2 候选特定准入门槛

`L3-VIS-01` 只有在以下条件同时满足时才允许启动：

- 目标 surface 实际使用 `include_visual=True`；
- visual refresh 或 visual transport 是可见的 runtime 切片。

`L3-OBS-01` 只有在以下条件同时满足时才允许启动：

- `obs_build` 仍然是显著瓶颈；
- 目标 policy surface 能承受对 contact / RWR 截断的显式审查。

`L3-PREC-01` 只有在以下条件同时满足时才允许启动：

- policy-facing export 或 bridge 成本在所选 surface 上足够显著；
- 目标硬件 / runtime 路径实际支持该低精度模式。

`L3-MISS-01` 只有在以下条件同时满足时才允许启动：

- 更安全的近似候选无法满足时间预算需求；
- mission / auxiliary observation tail 在所选 surface 上仍是主要瓶颈。

## 6. 默认顺序

当前谨慎顺序是：

1. `L3-VIS-01`
2. `L3-OBS-01`
3. `L3-PREC-01`
4. `L3-MISS-01`

原因：

- 从隔离度高的 policy 输入漂移逐步走向更接近控制侧的漂移；
- 先花掉语义风险最低的近似；
- 把 mission / auxiliary cadence 近似保留为更晚、且必须额外审查的选项。

## 7. 强制停止 / 回滚规则

任何 Level 3 轮次，只要出现以下任一情况，就必须停止或回滚：

1. runtime 收益太小，不足以支撑已声明漂移；
2. 漂移超出预先声明的预算；
3. reward、termination 或 command 语义在没有显式批准的情况下发生变化；
4. 实现无法保持在清晰的 runtime toggle 之后；
5. 行为比较 surface 无法提供清晰的 pass / fail 读数。

因此，这个仓库对 Level 3 的默认态度应当是：

```text
只有当近似是显式的、局部的、benchmark 可证明的、
质量有边界的、且容易关闭时，才允许进入工作。
```
