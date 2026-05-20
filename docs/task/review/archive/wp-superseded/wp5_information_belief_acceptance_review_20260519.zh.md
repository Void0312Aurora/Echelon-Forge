# WP5-D Information 与 Belief 验收审查

状态：`2026-05-19` WP5-D 验收已完成。

范围：information-state label、agent role metadata、action/coordination intent
compatibility metadata、truth/oracle leakage boundary 与 DecisionBelief deferral。

相关文档：

- [WP5-D information/belief 笔记](../simulation_architecture/wp5_information_belief_notes_20260519.zh.md)
- [WP5-D 分发表](../simulation_architecture/wp5_information_belief_cluster_20260519.zh.md)
- [WP5 第一波验收审查](wp5_first_wave_acceptance_review_20260519.zh.md)

## 1. 验收决定

WP5-D 予以验收。

已验收 gate 采用 label-first 策略。它通过被动 Python shim 验证当前 information 与
belief 边界，不改变 policy inference、runtime behavior、diagnostics/oracle helper
或 smoke-suite membership。

## 2. 已验收证据

| 领域 | 已验收证据 | 决定 |
|------|------------|------|
| Shim vocabulary | `tests/runtime/test_agent_shim.py` | 作为 maintained information/belief label gate 验收。 |
| Truth/oracle boundary | `wp5_information_belief_notes_20260519.md` | `raw_world_truth` 与 `diagnostics_oracle` 保持 diagnostics-only，不是 maintained policy input。 |
| Maintained-path allowlist sketch | `wp5_information_belief_notes_20260519.md` | 未来 direct `sim.*` restriction 必须基于 allowlist，当前不能全局禁止。 |
| DecisionBelief boundary | `wp5_information_belief_notes_20260519.md` | Belief-layer label 今天可测试；typed DTO enforcement 继续 deferred。 |

## 3. 验证

```bash
python -m pytest -q tests/runtime/test_agent_shim.py
```

结果：`11 passed`。

```bash
python -m py_compile python/rl/runtime/agent_shim.py tests/runtime/test_agent_shim.py
```

结果：通过。

主线程审阅的 WP5-D 笔记与测试通过 `git diff --check`。

## 4. 交接

WP5-E 可将 `tests/runtime/test_agent_shim.py` 提升为 maintained information/belief
smoke gate。Typed `DecisionBelief`、packet provenance、typed reward attribution
与 termination reason-source 的 metadata-dependent checks 继续 deferred。
