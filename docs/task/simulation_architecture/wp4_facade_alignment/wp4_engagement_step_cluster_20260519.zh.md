# WP4-B + WP4-C 分发表：Engagement、Step 与 Lifecycle 对齐

状态：`2026-05-19` 分发表；在 WP4-A 发布初始 surface 词汇后启动。

语言版本：

- 英文主文：[wp4_engagement_step_cluster_20260519.md](wp4_engagement_step_cluster_20260519.md)
- 中文辅文：`wp4_engagement_step_cluster_20260519.zh.md`

输入：

- [WP4 facade 对齐](facade_alignment_wp4_20260519.zh.md)
- [WP4-A surface inventory 任务簇](wp4_surface_inventory_cluster_20260519.zh.md)
- [WP3 交战试点验收审查](../review/wp3_engagement_pilot_acceptance_review_20260519.zh.md)
- [WP2.5 调度语义冻结](scheduler_semantics_wp25_20260519.zh.md)
- 当前 `src/runtime/facade/*`、`tests/runtime/facade/` 与
  `tests/runtime/engagement/`

## 一、目的

本表把最贴近已验收 WP3 试点的 WP4 facade 实现工作归为一组：

- `WP4-B Engagement Alignment`
- `WP4-C Step And Lifecycle Alignment`

该任务簇应稳定维护中的 facade output，但不发明新的 engagement、guidance、effects、damage、reward 或 termination 语义。

## 二、分发交付物

| 流 | 必需输出 | 主要写入范围 | 思考预算 |
|----|----------|--------------|----------|
| `WP4-B1 Engagement Producer Coverage` | 记录并在必要时测试哪些 event family 填充 engagement export slot。 | `docs/task/simulation_architecture`、`tests/runtime/engagement/`。 | 中。 |
| `WP4-B2 World-Safe Engagement Export` | 验证 multi-world export 一致保留或重标 `world_index`，且不把 raw runtime 作为维护路径。 | `src/runtime/facade/runtime_facade.cpp`、engagement tests。 | 中。 |
| `WP4-B3 Diagnostics Piggyback Boundary` | 在 dedicated diagnostics surface 出现前，显式说明 diagnostics piggyback engagement export 的边界。 | facade docs/tests；避免宽泛 runtime 变更。 | 中高。 |
| `WP4-C1 Step Result Ownership` | 对齐 execution-step result 形态与 reward、termination、observation snapshot、episode phase ownership。 | `src/runtime/facade/*`、`tests/runtime/facade/`。 | 若 DTO 形态变化则高。 |
| `WP4-C2 Reward Fact/Shaping Attribution` | 在维护中 step result 上记录或测试 fact vs shaping attribution。 | facade docs/tests；必要时读取 Python adapter 证据。 | 高。 |
| `WP4-C3 Termination/Truncation Attribution` | 记录或测试 reason-source separation 与 mirrored phase 行为。 | facade docs/tests；必要时 adapter tests。 | 中高。 |

## 三、写入范围规则

1. 本任务簇可以编辑 `src/runtime/facade/runtime_facade.cpp` 与 facade tests。
2. 除非 WP4-E 已确认签名稳定，本任务簇应避免编辑 `src/interfaces/python/bindings_runtime.cpp`。
3. 除了不与 WP4-D 冲突的窄证据备注或测试，本任务簇不得编辑 policy/orchestration adapter。
4. 除非 compatibility adapter 无法用其他方式表达，本任务簇不得编辑 `simulation_kernel_weapon_api.cpp`；如必须触碰，应交由 integration owner 串行处理。
5. 如果 WP4-A 尚未冻结某个 surface 名称，本任务簇应写文档备注或 skipped/pending test，而不是发明新名称。

## 四、Engagement 对齐规则

WP4-B 必须保持这些已验收 WP3 属性：

1. Engagement export 是 facade-first。
2. Multi-world export 保持 world-safe。
3. Recent-event retagging 不得制造含混的 `world_index` ancestry。
4. Track、launch、effects、damage 与 diagnostics slot 的 event-family coverage 必须显式。
5. 空 slot 或 placeholder 只有在记录为 compatibility placeholder 或 deferred producer 时才允许存在。
6. 放在 engagement export 内的 diagnostics data 必须标记为 engagement evidence 或 diagnostics piggyback，而不是完整 diagnostics logging framework。

## 五、Step 与 Lifecycle 对齐规则

WP4-C 必须保持这些架构边界：

1. `ExecutionBatchStepResult` 通过 facade-shaped data 报告 step result state，而不是隐藏 mirror。
2. Reward output 在当前数据允许的范围内区分 simulation fact 与 shaping/composition。
3. `terminated` 与 `truncated` 保持分离，并在可用时带 reason-source attribution。
4. Episode phase authority 仍由 compiled/facade 拥有；Gymnasium 或 Python adapter 只 mirror 并请求 transition。
5. Step result 返回的 observation snapshot 在当前 DTO 能承载时必须说明 source time 或 snapshot provenance。

## 六、验证目标

推荐聚焦命令：

```powershell
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\engagement\test_facade_engagement_export.py tests\runtime\facade\test_runtime_facade.py
```

如果本地 artifact 过旧，先重建 `ef_core` 与 `ef_py` 再运行聚焦测试。

## 七、退出标准

本任务簇退出条件：

1. Engagement facade export 对当前 slot 有明确 producer coverage。
2. Multi-world engagement export 仍保持 world-safe。
3. Step result 记录 reward、termination、truncation、observation 与 episode lifecycle ownership。
4. Diagnostics piggybacking 已显式化，可交给 WP5 evidence validation。
5. 未实现 surface 被标记为 deferred 或 pending WP4-A/WP4-E，而不是静默藏在 raw runtime access 后面。
