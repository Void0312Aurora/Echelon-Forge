# WP4 第一波验收审查

状态：`2026-05-19` 第一波验收完成。

范围：WP4-A surface inventory、WP4-B/C engagement 与 step/lifecycle 探查、WP4-D/E policy/binding 探查。

相关文档：

- [WP4 facade 对齐](../simulation_architecture/facade_alignment_wp4_20260519.zh.md)
- [WP4-A surface inventory 初稿](../simulation_architecture/wp4_surface_inventory_wp4a_20260519.zh.md)
- [WP4-B/C engagement-step 对齐笔记](../simulation_architecture/wp4_engagement_step_alignment_notes_20260519.md)
- [WP4-D/E policy-binding 对齐笔记](../simulation_architecture/wp4_policy_binding_alignment_notes_20260519.zh.md)
- [WP4 surface inventory 任务簇](../simulation_architecture/wp4_surface_inventory_cluster_20260519.zh.md)
- [WP4 engagement-step 任务簇](../simulation_architecture/wp4_engagement_step_cluster_20260519.zh.md)
- [WP4 policy-binding 任务簇](../simulation_architecture/wp4_policy_binding_cluster_20260519.zh.md)

## 一、验收结论

WP4 第一波工作作为 discovery 与 surface-freeze 输入予以验收。它不是 WP4 实现完成。

第一波已经提供足够证据，可以启动第二波：

1. `WP4-A` 已有 canonical surface inventory 初稿，区分 maintained、compatibility、diagnostics-only 与 deferred。
2. `WP4-B/C` 已给出 engagement export、producer coverage、diagnostics piggyback 与 execution-step/lifecycle 缺口的有界证据。
3. `WP4-D/E` 已给出 `AgentRole`、action intent、coordination intent、observation/belief path 与 compatibility escape hatch 的 policy/binding discovery map。

## 二、接受的发现

| 领域 | 接受结论 | 分流 |
|------|----------|------|
| Surface classification | `ObservationViewSpec`、`ObservationPacket`、`DecisionBelief`、reward/termination/lifecycle surface 是 maintained concept；`RuntimeFacade::runtime()` 与 raw `WorldBatchRuntime` 是 compatibility-only；`DiagnosticsTrace` 在 WP4 保持 diagnostics-only piggyback。 | 作为第二波词汇使用。 |
| Deferred agent/action concepts | `ActionIntentPacket`、`CoordinationIntentPacket` 与 `AgentRole` 暂不提升为 C++ facade surface，直到 WP4-D 建立 adapter shim 与 contract sketch。 | 进入 policy/agent shim 任务簇。 |
| Engagement producer coverage | `track_packets`、recent launch/effects/damage event 与 diagnostics trace 当前有 producer；`launch_requests` 与 `munition_lifecycle_packets` 是显式 deferred placeholder。 | 进入 facade evidence test 与 WP4-F 文档。 |
| Diagnostics boundary | Engagement diagnostics 是 piggyback evidence，不是完整 diagnostics logging surface。 | 保持 WP4 范围收窄；只有 WP5 trace gate 需要时才提升 dedicated diagnostics surface。 |
| Step/lifecycle coverage | `ExecutionBatchStepResult` 暴露 step result、reward、terminated/truncated、status、termination reason、reward JSON、step info、controller state changed flag 与 observation packet。 | 添加 semantic evidence test，并记录 typed DTO 缺口。 |
| Step/lifecycle gaps | 缺 typed reward fact/shaping attribution、termination reason source、observation snapshot/barrier/source-time provenance、top-level episode authoritative-source marker。 | 在第二波测试明确最小 DTO 增量前，不进行 facade signature churn。 |
| Policy/binding map | 当前 policy/batch/multi-agent/leader/director path 大多是 `compatibility_adapter`；Python bindings 镜像稳定 facade DTO，但暂不绑定 `AgentRole`、`DecisionBelief` 或 intent packet。 | 进入 Python shim 与 oracle-audit 任务簇。 |
| World-truth risk | 直接 `sim.*`、`RuntimeFacade.runtime()`、`WorldBatchRuntime.world(...)`、visual/candidate helper 与 teacher/oracle path 不能成为 maintained policy input。 | 进入 compatibility guard test。 |

## 三、第二波必需工作

第二波 WP4 应轻实现、重测试/证据：

| 任务簇 | 目的 |
|--------|------|
| `WP4-G Facade Evidence Gates` | 添加或记录 engagement producer coverage、deferred placeholder、diagnostics piggyback、multi-world retagging 与当前 step-result semantic shape 的聚焦测试。 |
| `WP4-H Information And Agent Shim` | 草拟 Python-side `AgentRole`、`ActionIntent` 与 `CoordinationIntent` shim 或 notes，添加 observation provenance 标记，并把 oracle path 识别为 diagnostics-only。 |
| `WP4-I Compatibility Guard And Integration` | 添加 architecture/doc gate 约束 raw-runtime compatibility boundary，整合第一波发现到 WP4 文档，并准备移交 WP5。 |

## 四、不阻塞的开放问题

这些问题仍开放，但不阻塞第二波分发：

1. `ObservationViewSpec` 是否在 WP4 成为 C++ DTO，还是到 WP5 metadata enforcement 前保持 policy/test-owned concept。
2. `DiagnosticsTrace` 是否在 WP4 获得 dedicated facade query/export，还是到 WP5 前继续作为 engagement-piggyback evidence。
3. `RuntimeCapabilities` 是否继续推迟到 backend profile work。
4. 未来触发 `RuntimeFacade` split 的精确 method-count 口径。
5. `AgentObservation` 中 ownship position 默认是否为 maintained，还是只有 view spec 显式允许 ownship truth-state projection 时才允许。

## 五、验收门槛

第一波予以验收，因为它满足任务簇退出条件：

1. 后续 worker 可使用 surface name 与 classification。
2. Engagement 与 step/lifecycle 缺口已经具体到可测试。
3. Policy 与 binding 缺口已分类，且没有过早扩展 C++ surface。
4. Compatibility-only 与 diagnostics-only path 已与 maintained policy/training truth 清楚分离。
