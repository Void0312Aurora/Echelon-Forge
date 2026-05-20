# WP10-C Same-Window Edge Validation

状态：`2026-05-20` planned WP10 dispatch sheet。

语言版本：

- 英文主文：[wp10_same_window_validation_cluster_20260520.md](wp10_same_window_validation_cluster_20260520.md)
- 中文辅文：`wp10_same_window_validation_cluster_20260520.zh.md`

输入：

- [WP10 causal runtime foundation](causal_runtime_foundation_wp10_20260520.zh.md)
- [WP10-A manifest registry](wp10_manifest_registry_cluster_20260520.zh.md)
- [WP2.5 state/barrier cluster](../wp25_scheduler_semantics/wp25_state_barrier_cluster_20260519.zh.md)
- [Post-WP9 route plan](../post_wp9_architecture_route_plan_20260520.zh.md)

## 1. 目的

`WP10-C` 在 schedule-construction 阶段判定 same-window dataflow 合法或非法。
这防止第一组 window loop 退化为 hidden linear pipeline 或 wildcard read-after-write channel。

## 2. 范围

范围内：

- 消费 `WP10-A` manifest registry；
- 验证 producer publish intent；
- 验证 consumer read declarations；
- 验证 read/write 或 packet intersections；
- 拒绝 wildcard 或 undeclared same-window edges；
- 拒绝 selected manifest-derived window 中的 cycles；
- 添加 passing 与 failing fixtures。

范围外：

- per-tick dynamic edge discovery；
- global graph compiler；
- strict clock-domain enforcement；
- runtime mutation of manifest definitions。

## 3. Validation Rules

same-window edge 只有全部条件为真时合法：

1. Producer 声明 output packet 或 state-derived output。
2. Producer 对该 output 声明 `write_commit_policy: stage_publish`。
3. Producer 的 `allowed_same_window_edges` 命名 consumer node id 或 allowed downstream
   stage family。
4. Consumer 声明 `read_snapshot_policy: same_window`。
5. Consumer read set 或 input packets 与 producer write set 或 output packets 相交。
6. Consumer 在 `required_barriers` 中声明 `stage_publish`。
7. 结果 window graph 是 acyclic。

失败必须显式：invalid edges 应产生稳定 validation error，而不是静默 fallback 到 hidden order。

## 4. Fixtures

必需 fixture 类型：

| Fixture | 预期结果 |
|---------|----------|
| Producer 与 consumer 均声明，且 read/write sets 匹配。 | Pass。 |
| Producer 未命名 consumer。 | Fail。 |
| Producer 命名 consumer，但 read/write sets 不相交。 | Fail。 |
| Consumer 请求 `same_window` 但省略 `stage_publish`。 | Fail。 |
| Edge 引入 cycle。 | Fail。 |
| `window_commit`-only producer 被 same-window 消费。 | Fail。 |

## 5. 验收测试

最低测试：

- passing fixture 验证 selected WP10 slice；
- 每个 invalid fixture 以命名原因 fail；
- validator 使用 registry API，而不是重解析重复 doc tables；
- validation 在 loop 执行 selected schedule 前运行。

## 6. Handoff Contract

返回：

- validation helper file paths；
- fixture file paths；
- exact failure messages 或 error codes；
- added/updated tests；
- commands run and outcomes；
- 给 `WP10-B/D/E` 的 integration notes。
