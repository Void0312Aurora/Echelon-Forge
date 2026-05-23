# WP10-A Manifest Registry Seed

状态：`2026-05-20` planned WP10 dispatch sheet。

语言版本：

- 英文主文：[wp10_manifest_registry_cluster_20260520.md](wp10_manifest_registry_cluster_20260520.md)
- 中文辅文：`wp10_manifest_registry_cluster_20260520.zh.md`

输入：

- [WP10 causal runtime foundation](causal_runtime_foundation_wp10_20260520.zh.md)
- [WP2.5 manifest/event cluster](../wp25_scheduler_semantics/wp25_manifest_event_cluster_20260519.zh.md)
- [WP2.5 state/barrier cluster](../wp25_scheduler_semantics/wp25_state_barrier_cluster_20260519.zh.md)
- [Post-WP9 route plan](../post_wp9_architecture_route_plan_20260520.zh.md)

## 1. 目的

`WP10-A` 为所选 engagement/observation slice 创建第一组 code-owned
`StageNodeManifest` registry。后续 WP10 streams 消费该 registry；不得在本地重新定义
manifest fields。

## 2. 范围

范围内：

- 选择 registry location 与 public query API；
- 为所选 `P7`、`P9` 与 `P10` nodes 编码稳定 `node_id`；
- 为这些 nodes 编码 WP2.5 required manifest fields；
- 添加可被 architecture tests 枚举的 fixtures 或 builders；
- 在 WP10 中把 clock domains 标为 advisory，而不是 strict enforcement。

范围外：

- 盘点每个 runtime system；
- 生成完整 schema compiler；
- 除 compile-facing type exposure 外改变 facade export behavior；
- 执行 clock-domain cadence。

## 3. 必需 Manifest Fields

WP10 selected slice 中每个 maintained node 必须声明：

| 字段组 | 必需字段 |
|--------|----------|
| Identity | `node_id`, `semantic_stage`, `owner_module` |
| Contracts | `input_packets`, `output_packets`, `event_families_emitted` |
| State | `read_state_shards`, `write_state_shards`, `read_snapshot_policy`, `write_commit_policy` |
| Time and visibility | `clock_domain`, `latency_policy`, `sync_policy`, `required_barriers`, `facade_visibility` |
| Same-window | 当 `write_commit_policy = stage_publish` 或声明 same-window visibility 时需要 `allowed_same_window_edges` |
| Diagnostics | `diagnostic_trace_obligations`、source snapshot 或 shard ancestry requirements |
| Compatibility | legacy/raw access 仍可达时需要 `compatibility_adapter_allowed` |

## 4. 候选 Slice Nodes

| Node candidate | Semantic stage | 初始角色 | 预期可见性 |
|----------------|----------------|----------|------------|
| `p7.fire_control_launch.v1` | `P7 FireControlLaunch` | Launch request admission、fire-control gating、launch event publication。 | 带 facade request ancestry 的 maintained stage node。 |
| `p9.effects_damage.v1` | `P9 EffectsDamage` | Effects/damage event 与 damage-state commit evidence。 | maintained stage node；若当前代码还不能 commit shard，则为 diagnostic bridge。 |
| `p10.observation_export.v1` | `P10 ObservationExport` | Recent engagement events、diagnostics trace 与 observation/facade export。 | maintained facade export。 |

worker 只有在名称保持稳定、确定且 handoff 记录清楚时，才可以重命名 node ids。

## 5. 验收测试

最低测试：

- architecture test 枚举所有 WP10 maintained manifest records；
- 缺少 required fields 时 fail closed；
- same-window publish claims 需要非空 `allowed_same_window_edges`；
- compatibility nodes 不能被报告为 maintained scheduler truth；
- event-emitting nodes 声明 event family 与 diagnostics obligations。

## 6. Handoff Contract

返回：

- registry file paths 与 public query functions；
- node ids 以及对候选列表的任何有意偏离；
- added/updated tests；
- commands run and outcomes；
- 仍为 advisory 而非 enforced 的字段；
- 给 `WP10-B/C/D` 的 integration notes。
