# WP10-B Window Loop And Injection

状态：`2026-05-20` planned WP10 dispatch sheet。

语言版本：

- 英文主文：[wp10_window_loop_injection_cluster_20260520.md](wp10_window_loop_injection_cluster_20260520.md)
- 中文辅文：`wp10_window_loop_injection_cluster_20260520.zh.md`

输入：

- [WP10 causal runtime foundation](causal_runtime_foundation_wp10_20260520.zh.md)
- [WP10-A manifest registry](wp10_manifest_registry_cluster_20260520.zh.md)
- [WP2.5 state/barrier cluster](../wp25_scheduler_semantics/wp25_state_barrier_cluster_20260519.zh.md)
- [Post-WP9 gap analysis](../../review/post_wp9_gap_analysis_20260520.zh.md)

## 1. 目的

`WP10-B` 为所选 slice 添加最小 scheduling-window loop skeleton 与第一组
cross-layer request injection 语义。

该 loop 证明架构中的 `collect -> inject -> DAG -> commit -> export` 形态，
但不替换全局 scheduler。

## 2. 范围

范围内：

- 为所选 slice 定义 small scheduling-window context；
- 把 facade-compatible graph inputs 收集到 ingress queue；
- 将 arrived requests 分类为 accepted、future-window、rejected 或 expired；
- 让 accepted requests 只在 `input_injection` 后可见；
- 运行 selected manifest-derived node sequence；
- 跨过带稳定 id 的 `window_commit` 与 `export` barriers；
- 添加 barrier sequence 与 request visibility 的 focused tests。

范围外：

- full multi-rate scheduler；
- strict clock-domain skip/merge enforcement；
- `ActionHoldPolicy` runtime cadence；
- global ECS scheduler replacement；
- broad policy/control/physics cadence proof。

## 3. Minimal Window Contract

第一组 loop skeleton 应暴露或内部记录：

| Field | 含义 |
|-------|------|
| `window_id` | 测试中 scheduling window 的稳定 id 或 sequence。 |
| `world_id` | event/snapshot evidence 使用的 world identity。 |
| `source_time_s` | 当前 window 的 simulated source time。 |
| `barrier_sequence` | 区分重复 barriers 的 monotonic sequence。 |
| `current_barrier_id` | `input_injection`、`stage_publish`、`window_commit`、`export` 之一。 |
| `accepted_inputs` | admitted to current-window maintained logic 的 requests。 |
| `deferred_inputs` | `effective_time` 超出 current window 的 requests。 |
| `rejected_inputs` | metadata 不合法或 merge policy 不兼容的 requests。 |
| `expired_inputs` | `valid_until` 早于 current window 的 requests。 |

## 4. Request Injection Rules

每个 injected request 必须携带：

- `source_layer`；
- `source_id`；
- `input_snapshot_version`；
- `effective_time`；
- `valid_until`；
- `merge_policy`；
- request family 或 packet type。

可见性规则：

1. `input_injection` 前，arrived requests 可位于 ingress buffers，但 maintained stage
   nodes 不能消费它们。
2. `input_injection` 后，只有 accepted current-window requests 对声明 matching input
   packets 与 `read_snapshot_policy: post_injection` 的 nodes 可见。
3. Future-window requests 保持 deferred，对 current window 不可见。
4. Expired 或 invalid requests 被 rejected 或记录为 diagnostics-only；它们不改变
   maintained state。

## 5. 验收测试

最低测试：

- barrier sequence 记录为 `input_injection -> execution/stage_publish where
  applicable -> window_commit -> export`；
- accepted requests 只在 `input_injection` 后可见；
- future-window requests 被 deferred；
- expired requests 不被 current window 消费；
- invalid metadata fail closed；
- loop 消费来自 `WP10-A` 的 manifest registry node ids。

## 6. Handoff Contract

返回：

- loop 与 injection file paths；
- 已实现的 accepted/deferred/rejected/expired 语义；
- added/updated tests；
- commands run and outcomes；
- touched shared facade 或 binding files；
- 给 `WP10-C/D/E` 的 integration notes。
