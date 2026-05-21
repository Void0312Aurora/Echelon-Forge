# WP15-A Replay Envelope And Branch Point Contract

状态：`2026-05-21` mergeable / first slice complete。

语言版本：

- 英文主文：[wp15_replay_envelope_branch_point_cluster_20260521.md](wp15_replay_envelope_branch_point_cluster_20260521.md)
- 中文辅文：`wp15_replay_envelope_branch_point_cluster_20260521.zh.md`

输入：

- [WP15 counterfactual experiment generation](counterfactual_experiment_generation_wp15_20260521.zh.md)
- [WP2.5 scheduler semantics freeze](../wp25_scheduler_semantics/scheduler_semantics_wp25_20260519.zh.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.zh.md)
- [WP11 facade vertical slice and provenance](../wp11_facade_vertical_slice_provenance/facade_vertical_slice_provenance_wp11_20260520.zh.md)
- 当前 `src/runtime/contracts/*`
- 当前 `python/world_model/replay.py`

## 1. 目的

`WP15-A` 创建 deterministic replay envelope 与 branch point vocabulary，供后续
counterfactual streams 共用。该 contract 必须命名 baseline seed、
snapshot/barrier/event-order evidence、facade provenance 与 branch point identity，
但不得声明 restore execution。

## 2. 范围

范围内：

- typed `ReplayEnvelope` 与 `BranchPoint`，或等价 code-owned contracts；
- seed、episode、snapshot version、barrier id、event-order、source-time 与 facade
  provenance references；
- 拒绝缺失 ancestry 的 validation helpers；
- 证明 deterministic shape 与 fail-closed 行为的 focused architecture tests。

范围外：

- full snapshot/restore implementation；
- `WP15-B` 负责的 worldline parent/child metadata；
- `WP15-C` 负责的 counterfactual request admission；
- `WP15-D` 负责的 scenario/adversary generation。

## 3. 候选实现接缝

编辑前检查：

- `src/runtime/contracts/stage_node_manifest_registry.h`
- `src/runtime/facade/runtime_window_coordinator.h`
- `src/runtime/contracts/runtime_dto_contracts.h`
- `python/world_model/replay.py`
- `tests/architecture/test_wp10_*.py`

首选方式：

- 新增 counterfactual/replay-focused contract surface，不复用 backend 或 platform
  capability contracts；
- required fields 保持可字符串测试、确定性；
- 在 restore proof 存在前显式包含 `snapshot_restore_supported = false` 或等价 support
  boundary；
- 为缺失 envelope id、seed、snapshot、barrier、event-order 与 provenance refs 提供稳定
  rejection reason。

## 4. Gate 规则

| Boundary | Required behavior |
|----------|-------------------|
| Deterministic envelope | Replay envelope 命名 seed、episode/run、snapshot、barrier、event-order 与 provenance evidence。 |
| Branch point identity | Branch point ids 稳定，并绑定 replay envelope 与 snapshot/barrier boundary。 |
| Restore boundary | 第一切片可命名 restore prerequisites，但不得声明 restore support。 |
| Fail-closed validation | 缺少 id、seed、snapshot、barrier、event-order 或 provenance refs 时拒绝 fixture。 |

## 5. 验收测试

最低测试：

- architecture test 构建有效 replay envelope 与 branch point fixture；
- validation 拒绝缺失 envelope id、deterministic seed、snapshot version、barrier id、
  event-order ref 与 facade provenance ref；
- 测试证明 envelope 存在不意味着 restore support；
- 测试证明 evidence refs ordering 是确定性的。

建议命令：

```bash
git diff --check
python -m pytest -q tests/architecture/test_wp15_replay_envelope_contracts.py
```

## 6. Handoff Contract

返回：

- touched contract files；
- replay envelope 与 branch point field names；
- validation helper names 与 rejection reasons；
- tests added or updated；
- exact commands run and outcomes；
- `WP15-B`、`WP15-C` 或 `WP15-E` 的 blockers。
