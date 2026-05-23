# WP9-C Infrastructure Closure

状态：`2026-05-20` complete / accepted WP9 并行流，保留一个已跟踪残余项。

语言版本：

- 英文主文：[wp9_infrastructure_closure_cluster_20260520.md](wp9_infrastructure_closure_cluster_20260520.md)
- 中文辅文：`wp9_infrastructure_closure_cluster_20260520.zh.md`

输入：

- [WP9 contract and infrastructure closure](contract_infrastructure_closure_wp9_20260520.zh.md)
- [WP2.5 调度语义冻结](../wp25_scheduler_semantics/scheduler_semantics_wp25_20260519.zh.md)
- [WP3 交战试点](../wp3_engagement_pilot/engagement_pilot_wp3_20260519.zh.md)
- [WP4 facade 对齐验收](../../review/archive/wp-acceptance/wp4_facade_alignment_acceptance_review_20260519.zh.md)
- [WP6 后端配置文件策略验收](../../review/archive/wp-acceptance/wp6_backend_profile_policy_acceptance_review_20260519.zh.md)
- [WP7 后端能力物化](../wp7_backend_capability_materialization/backend_capability_materialization_wp7_20260519.zh.md)

## 1. 目的

WP9-C 关闭早期工作包验收中作为 deferred follow-up 接受的小型基础设施残项。核心意图是让架构跟踪保持诚实：每个 residual 要么有证据关闭，要么带新 owner 继续可见。

本流覆盖 INF-1 至 INF-7。

## 2. 必需闭合项

| ID | 项目 | 必需产出 |
|----|------|----------|
| `INF-1` | `merge_policy` 命名碰撞 | 把 WP2.5 clock-domain wording 重命名为 `clock_merge_policy`；cross-layer `merge_policy` 仍保留给 action/coordination DTO。 |
| `INF-2` | `DiagnosticsTrace` 独立 facade surface | 添加专用 facade query endpoint，或明确命名、不只 piggyback 在 engagement export 上的 facade method。 |
| `INF-3` | `RuntimeCapabilities` population trigger | 文档化 richer capability projection 只有在至少一个 non-reference backend profile 进入 maintained 后才启动。 |
| `INF-4` | StageNodeManifest registry completion | 在已有 P7 示例之外添加 P0-P6 与 P8-P10 示例 manifests。 |
| `INF-5` | Facade split threshold rule | 文档化约 40 个 public methods 时拆成 Session、Setup、Execution、Observation、Diagnostics、Engagement 与 Capability groups。 |
| `INF-6` | WP3 real missile terminal effects capture | 把 maintained capture 推向 guidance/effects events，而不是 debug-only proximity-hit path；或记录精确 blocked handoff。 |
| `INF-7` | WP3 recent-event storage strategy | 用 event-queue-aligned ordering semantics 替代或正式包装 bounded recent-event buffer；或记录精确 blocked handoff。 |

## 3. 实施路线

推荐路线：

1. 先修补 INF-1、INF-3、INF-4 与 INF-5 的文档，因为它们没有 runtime dependency。
2. 为 INF-2 添加 narrow diagnostics facade method 与 focused test。
3. 编辑 INF-6/INF-7 前先检查 WP3 event capture path；不要把可工作的 debug path 换成更不可见的抽象。
4. 如果 INF-6/INF-7 对 WP9 过大，创建显式 owner notes 与 tests，让 residual 保持可见，而不是静默关闭。

推荐写入范围：

- `docs/plan/architecture/*`
- `docs/task/simulation_architecture/wp25_scheduler_semantics/*`
- `docs/task/simulation_architecture/wp3_engagement_pilot/*`
- `docs/task/simulation_architecture/wp6_backend_profile_policy/*`
- `docs/task/simulation_architecture/wp7_backend_capability_materialization/*`
- `src/runtime/facade/*`
- `src/core/engine/*engagement*`、`src/core/engine/*weapon*`、`src/core/engine/*damage*`
- `tests/runtime/engagement/*`
- `tests/runtime/facade/*`
- `tests/architecture/*`

## 4. 工作项

| 流 | 必需产出 | 预算 |
|----|----------|------|
| `WP9-C1 Naming And Capability Docs` | INF-1 与 INF-3 文档 patch；源文档双语时保持双语引用。 | Medium. |
| `WP9-C2 Manifest Registry Completion` | `StageNodeManifest` 的 P0-P6 与 P8-P10 examples 或 registry entries。 | High. |
| `WP9-C3 Diagnostics Facade Surface` | 独立 diagnostics trace facade query 与 focused tests。 | High. |
| `WP9-C4 Facade Split Rule` | 在 architecture/facade docs 中记录 Runtime facade split threshold 与目标分组。 | Medium. |
| `WP9-C5 Engagement Event Closure` | INF-6/INF-7 implementation，或带保留测试的显式 blocked owner note。 | Xhigh. |

## 5. 非目标

- 不实现完整 scheduler runtime。
- 不提升 backend profiles，也不改变 WP6/WP7 capability truth。
- 在 replacement facade tests 通过前，不删除现有 engagement export compatibility。
- 如果代码仍依赖 debug-only path，不用 docs-only 声称 INF-6/INF-7 已关闭。

## 6. 验收 Gate

WP9-C 满足以下条件后可进入 WP9-E：

1. INF-1 至 INF-7 每一项都有命名 evidence row。
2. 文档型 INF 项已经 patch 到权威源文档。
3. Diagnostics trace query 可通过 facade method 使用，或以原因明确 blocked。
4. WP3 event capture/storage residual 已修复，或带具体 follow-up owner 与 failing/blocked evidence 保持可见。
5. Focused tests 或 document checks 覆盖变更 surface。

## 7. 验证命令

```bash
git diff --check
pytest tests/runtime/engagement tests/runtime/facade tests/architecture
rg -n "clock_merge_policy|DiagnosticsTrace|RuntimeCapabilities|StageNodeManifest|facade split|kMaxRecentEngagementEvents|recent engagement" docs src tests
```
