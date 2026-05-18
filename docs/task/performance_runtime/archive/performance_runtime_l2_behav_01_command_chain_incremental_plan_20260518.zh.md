# L2-BEHAV-01：command-chain 等价增量重算计划

状态：`2026-05-18` 活跃执行条目。  
范围：只覆盖 `L2-BEHAV-01`，不横向扩展到其它二级候选。

关联文档：

- [二级等价算法优化候选集](performance_runtime_level2_equivalent_algorithm_candidates_20260518.zh.md)
- [一级 runtime 优化任务板](performance_runtime_level1_taskboard_20260518.zh.md)
- [runtime 性能优化分层与升级规则](performance_runtime_optimization_ladder_20260518.zh.md)

---

## 1. 本条目的边界声明

本轮只改变 exact command-chain 的计算组织方式。

不允许：

1. 改变 phase transition cadence；
2. 改变 `task_order` / `leader_intent` / `pilot_report` 的任务契约；
3. 改变 mission command 对 kernel 的 freshness；
4. 引入任何近似更新、降频或保真折衷；
5. 横向扩展到 waypoint guidance、reward/info tail 或 scripted-opponent owner 规则。

## 2. 当前目标

目标很窄：

- 确认 current command-chain 更新是否仍然包含“每步完整重建 exact 对象”的结构性成本；
- 若成立，则把它改成“带显式失效规则的 exact 增量重算”。

不在本轮回答的问题：

- waypoint guidance 是否也应 batch 化；
- scripted-opponent 是否应收口为 once-per-world；
- reward/info tail 是否要转入二级。

## 3. 本轮主指标与辅助指标

主指标：

- `behavior_update_ms`

辅助指标：

- `command_sync_ms`
- `total_ms`

规则：

- 本轮验收只以 `behavior_update_ms` 为主；
- `total_ms` 只能作为辅助确认，不允许反过来替代主指标。

## 4. 本轮最大迭代轮数

本候选最多允许 `2` 轮实现迭代。

当前这份条目对应：

- 第 `1` 轮：准入测量 + 首次实现
- 第 `2` 轮：只有在第 `1` 轮已证明有效时，才允许进入补完或收紧

如果第 `1` 轮结果中性，默认不进入第 `2` 轮。

## 5. 准入门槛

进入实现前，至少要满足以下条件之一：

1. command-chain 子项预计占 cooperative `behavior_update_ms` 的 `>= 15%`；
2. command-chain 结构性重复已在 cooperative 与至少一个 batch/single-world
   surface 上被验证；
3. 当前 cooperative 行为链路里，command-chain 已经是最后一个未验证的主结构性瓶颈。

若不满足以上任一条件，则本条目停止在测量与分析阶段，不进入实现。

## 6. 当前已知测量与判断

截至 `2026-05-18` 当前已知信息：

1. 一级第一轮已显著改善 cooperative `command_sync_ms`；
2. 一级第二轮对 director 的收紧在 long-running probe 上总体偏中性；
3. cooperative `behavior_update_ms` 的剩余成本更像还在：
   - command-chain
   - waypoint guidance
4. scripted-opponent duplicated update 已被确认，但由于存在 `target_id`
   owner 语义分歧，不属于本条目的允许范围。

当前默认判断：

```text
L2-BEHAV-01 允许进入准入测量；
只有在测量继续支持 command-chain 是主结构性子项时，才进入实现。
```

### 6.1 `2026-05-18` 准入测量结果

已完成两类 surface 的同口径补测：

1. cooperative long-running cruise probe
2. single-world batch execution runtime（inline scenario）

结果：

- cooperative：
  - `behavior_update_ms ~= 0.442`
  - command-chain 子项约 `0.203 ms/step`
  - waypoint 子项约 `0.130 ms/step`
  - command-chain 约占 `behavior_update_ms` 的 `45.9%`
- single-world：
  - `behavior_update_ms ~= 0.158`
  - command-chain 子项约 `0.136 ms/step`
  - waypoint 子项约 `0.0056 ms/step`
  - command-chain 约占 `behavior_update_ms` 的 `86.0%`

结论：

1. command-chain 子项已明显超过 `>= 15%` 的准入门槛；
2. 该结构并非 cooperative-only 偶发现象；
3. `L2-BEHAV-01` 允许从“准入测量”正式进入“失效条件梳理与首次实现”阶段。

### 6.2 `2026-05-18` 第 1 轮实现结果

第 `1` 轮实现采用了允许范围内最小的切口：

- 只在 `RuleBasedLeaderPhaseManager.update(...)` 内收紧；
- 尝试在稳定步复用 `leader_intent`，而不是每步重建；
- 不改变 cadence、kernel freshness、waypoint guidance、director 逻辑或
  scripted-opponent owner 语义。

验证状态：

- 定向 leader/runtime 语义回归测试保持绿色；
- benchmark family 保持可比，仍使用同口径 cooperative long-running
  cruise probe，并补了一个 single-world 辅助参考面。

测量结果：

- cooperative long-running cruise probe，样本 A：
  - `behavior_update_ms ~= 0.479`
  - `command_sync_ms ~= 0.083`
  - `total_ms ~= 1.559`
- cooperative long-running cruise probe，样本 B：
  - `behavior_update_ms ~= 0.487`
  - `command_sync_ms ~= 0.084`
  - `total_ms ~= 1.579`
- single-world 辅助参考面：
  - `behavior_update_ms ~= 0.080`
  - `command_sync_ms ~= 0.111`
  - `total_ms ~= 0.569`

与当前 cooperative 准入基线对比：

- 上文记录的准入基线为：`behavior_update_ms ~= 0.442`，
  `command_sync_ms ~= 0.079`，`total_ms ~= 1.466`
- 第 `1` 轮两次 cooperative 样本都没有把 `behavior_update_ms` 和
  `total_ms` 往更好方向推，反而出现了同方向退化。

结论：

1. 这条 Python 侧 stable-key / exact-object reuse 切口引入的判定成本，
   大于它减少的重建成本；
2. 两次同口径 cooperative 样本方向一致地为负，因此不满足第 `1` 轮验收规则；
3. 该实现已撤回，本候选在第 `1` 轮冻结；除非后续出现更窄、更便宜的 exact
   invalidation 证据，否则不再进入第 `2` 轮。

## 7. 第 1 轮执行顺序

第 `1` 轮固定顺序如下：

1. 在 cooperative long-running cruise probe 上补 command-chain 子项拆分；
2. 在至少一个非 cooperative 参考面上确认该结构不是 cooperative-only 偶发现象；
3. 明确写出 command-chain 的 exact invalidation 条件集合；
4. 只有在满足准入门槛后，才允许进入代码实现；
5. 改完后回跑：
   - 语义回归测试
   - cooperative long-running cruise probe
   - 至少一个辅助 surface

## 8. 允许的实现方向

只允许以下方向：

1. 为 exact command-chain 引入显式 dirty / invalidation 规则；
2. 把“每步重建 exact 对象”收紧成“只在失效时重建”；
3. 复用稳定的 exact runtime 对象，并用 field-diff 或 stable export 驱动更新；
4. 在不改变语义的前提下，收紧 exact kernel export 的组织方式。

## 8.1 当前显式失效条件集合

根据当前 command-chain / leader-tasking 代码，第一轮实现默认只能围绕以下失效条件组织：

1. `c2_task_name` 变化；
2. `mission_phase_name` 变化；
3. `waypoint_idx` 变化；
4. `post_waypoint_transition` 从有到无、从无到有或内容变化；
5. `task_order` 尚未构建；
6. `leader_intent` 尚未构建；
7. `pilot_report` 尚未构建；
8. 报告类型变化（例如 `REP_WILCO -> REP_RTB`）；
9. `task_order_overrides` 或场景 task 配置变化；
10. 影响 task retask 的 gate 结果变化：
    - scramble complete
    - on-station complete
    - RTB / recover-land gate open
11. hierarchical command-chain 从 inactive 变 active，或反向变化。

第一轮实现的默认目标，不是“把全部 command-chain 逻辑都变成增量”。

第一轮更小的目标是：

```text
先避免在上述失效条件都未触发时，
仍然每步完整重建 leader/task/report exact 对象。
```

这意味着：

- phase / task 不变时，应优先复用已有 exact 对象；
- 只有在失效条件命中时，才允许进入完整 retask / rebuild 路径。

## 9. 当前禁止的实现方向

本轮明确禁止：

1. 通过减少 update 次数换性能；
2. 把 fresh 结果改成 delayed 结果；
3. 通过默认值、短路或 best-effort 行为绕过 exact phase logic；
4. 顺手把 waypoint guidance、director、reward/info tail 混进同一轮；
5. 引入 scripted-opponent owner 语义决策。

## 10. 第 1 轮验收规则

第 `1` 轮要被视为“有效”，至少要满足以下之一：

1. `behavior_update_ms` 改善 `>= 5%`；
2. `behavior_update_ms` 改善虽较小，但两次同口径样本方向一致；
3. `behavior_update_ms` 改善并带动 `total_ms` 同方向变化。

同时必须满足：

1. 行为语义回归测试保持绿色；
2. 没有跨出本条目的边界声明；
3. benchmark 口径保持一致。

## 11. 中性与冻结规则

以下情况视为中性：

1. `behavior_update_ms` 变化很小且方向不稳定；
2. `behavior_update_ms` 改善但 `total_ms` 完全无感，且无法给出结构性解释；
3. 改动复杂度明显上升，但收益不足以支撑第二轮。

若第 `1` 轮中性：

- 记录结果；
- 不进入第 `2` 轮；
- 本候选冻结，除非出现新的更细测量证据。

若第 `2` 轮仍无可重复收益：

- 本候选正式冻结；
- 不再继续推进。
