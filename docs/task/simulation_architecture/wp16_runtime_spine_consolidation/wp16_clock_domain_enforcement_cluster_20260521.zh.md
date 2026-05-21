# WP16-B Clock-Domain Enforcement And Merge Trace

状态：`2026-05-21` complete / strict cadence slice accepted。

语言版本：

- 英文主文：[wp16_clock_domain_enforcement_cluster_20260521.md](wp16_clock_domain_enforcement_cluster_20260521.md)
- 中文辅文：`wp16_clock_domain_enforcement_cluster_20260521.zh.md`

输入：

- [WP16 runtime spine consolidation](runtime_spine_consolidation_wp16_20260521.zh.md)
- [WP2.5 scheduler semantics](../wp25_scheduler_semantics/scheduler_semantics_wp25_20260519.zh.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.zh.md)
- [post-WP9 gap analysis](../../review/post_wp9_gap_analysis_20260520.zh.md)

## 1. 目标

`WP16-B` 实现第一条严格 `GAP-9` 切片。选定 runtime spine 中的 clock domain
必须影响执行：当前 window 未触发的 clock domain 对应节点不能静默执行。
scheduler/window coordinator 必须记录节点是 executed、skipped、deferred 还是
rejected，以及原因。

## 2. 范围

范围内：

- 为 selected maintained spine slice 添加有边界的 clock-domain trigger decision helper；
- 支持 base tick、declared multiple、declared slot、event predicate 或 export cadence
  这类 nested trigger evidence；
- 为未触发节点添加 skip/defer/reject reason codes 与 execution evidence；
- independent clock domain 缺少 deterministic `clock_merge_policy`、source time、
  source snapshot、target window 与 barrier-order metadata 时 fail closed；
- 添加 triggered、skipped、deferred/rejected 与 independent merge cases 的 focused tests。

范围外：

- 全局 scheduler rewrite；
- hard-real-time execution；
- 超出 selected slice 的 broad policy/control/physics multi-rate support；
- 除暴露 evidence 所需字段外，不迁移 facade/batch consumers。

## 3. 交付物

- code-owned clock-domain cadence helper 或 coordinator extension。
- `executed`、`skipped`、`deferred`、`rejected` clock-domain decisions 的 execution evidence records。
- independent-domain merge trace vocabulary 或 fail-closed rejection reasons。
- `GAP-9` 行为的 focused architecture/runtime tests。

## 4. Gate 规则

| Gate item | Pass condition |
|-----------|----------------|
| Triggered node | declared clock domain 在 window 内触发的节点执行，并记录 trigger source。 |
| Skipped node | declared clock domain 未触发的节点以可见 evidence 被 skipped/deferred/rejected。 |
| No silent advisory behavior | 测试证明 selected slice 中 clock-domain 字段不再只是 decorative。 |
| Independent merge | 缺少 deterministic merge metadata 时 input 被 rejected 或 diagnostics-gated。 |
| Replay/evidence compatibility | Trigger/skip decisions 携带 window id、barrier id、source time 或 reason、node id。 |

## 5. 建议验证

```bash
git diff --check
python -m pytest -q tests/architecture/test_wp16_clock_domain_enforcement.py
python -m pytest -q tests/runtime/facade/test_runtime_facade_window_loop_injection.py -k "clock or window or barrier or evidence"
```

## 6. 交接契约

返回：

- touched files；
- selected clock-domain slice；
- helper/API names 与 evidence fields；
- 精确验证命令和结果；
- unsupported 或 deferred cadence cases；
- 给 WP16-C 与 WP16-F 的 integration notes。
