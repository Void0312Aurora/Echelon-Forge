# WP12-A Law 14 Read-Side Enforcement

状态：`2026-05-20` accepted / implementation mergeable。

语言版本：

- 英文主文：[wp12_law14_read_side_enforcement_cluster_20260520.md](wp12_law14_read_side_enforcement_cluster_20260520.md)
- 中文辅文：`wp12_law14_read_side_enforcement_cluster_20260520.zh.md`

输入：

- [WP12 information and agency enforcement](information_agency_enforcement_wp12_20260520.zh.md)
- [WP11-D consumer boundary pre-gates](../wp11_facade_vertical_slice_provenance/wp11_consumer_boundary_pregates_cluster_20260520.zh.md)
- [WP11 acceptance review](../../review/wp11_facade_vertical_slice_provenance_acceptance_review_20260520.zh.md)
- [Post-WP9 gap analysis](../../review/post_wp9_gap_analysis_20260520.zh.md)

## 1. 目的

`WP12-A` 把 WP11 maintained-vs-diagnostics consumer pre-gates 推进为 focused
Architecture Law 14 read-side enforcement slice。

Architecture Law 14 要求 maintained decision paths 消费 `ObservationPacket`，
必要时消费 `DecisionBelief`；除非路径被标记为 diagnostics-only，否则不得消费
`World Truth`。

## 2. 范围

范围内：

- 强制 focused maintained consumer path 使用 provenance-labeled packet 或 belief
  inputs；
- 当 maintained fixture 消费 unlabeled truth、raw ECS 或 privileged traces 时
  fail closed；
- 通过显式 labels 或 allowlists 保留 diagnostics-only 与 compatibility-only
  truth/raw-runtime fixtures；
- 增加测试同时证明 rejected 和 allowed paths；
- 记录 repository-wide Law 14 coverage 的残留。

范围外：

- 全局禁止所有 raw ECS reads；
- 覆盖所有 Python 和 C++ policy paths 的完整静态分析；
- Agency Graph authority validation；
- decision-model dispatch；
- backend/fidelity 或 learning-face changes。

## 3. 候选实现接缝

编辑前检查：

- `python/rl/runtime/agent_shim.py`
- `tests/runtime/test_agent_shim.py`
- `tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py`
- `src/runtime/contracts/policy_contracts.h`
- `src/runtime/facade/runtime_facade_types.h`
- `src/interfaces/python/bindings_runtime.cpp`

优先方式：

- 扩展既有 WP11 pre-gate helpers，而不是创建第二套 guard framework；
- 让 raw-truth diagnostics 保持显式标签；
- 使用窄 failing fixture 证明 maintained paths 不能静默绕过
  `ObservationPacket` / `DecisionBelief`。

## 4. Gate 规则

| Boundary | 必需行为 |
|----------|----------|
| Maintained consumer | focused slice 中必须消费 provenance-labeled packet 或 belief input。 |
| Diagnostics-only consumer | 只有显式 labeled 或 allowlisted 时才可消费 truth/raw ECS。 |
| Compatibility adapter | 只有标记为 compatibility-only 且不作为 maintained decision evidence 时可保留。 |
| Unknown source | 在 focused guard tests 中 fail closed。 |

## 5. 验收测试

最低测试：

- maintained consumer fixture 使用 labeled `ObservationPacket` 或 `DecisionBelief`
  时通过；
- maintained consumer fixture 使用 `WorldTruth`、raw ECS、privileged trace 或
  unlabeled input 时失败；
- 使用 truth/raw ECS 的 diagnostics-only fixture 保持显式且允许；
- architecture test 记录精确 allowlist，且不声明 global repository-wide
  enforcement；
- 不引入新的 raw runtime escape hatch。

## 6. 交付契约

返回：

- touched guard files 与 allowlists；
- maintained 与 diagnostics-only fixture paths；
- 新增或更新的 tests；
- 精确 commands run 与 outcomes；
- 更广 Law 14 coverage 的 blockers 和 residuals；
- 给 `WP12-D` 与 `WP12-E` 的 integration notes。
