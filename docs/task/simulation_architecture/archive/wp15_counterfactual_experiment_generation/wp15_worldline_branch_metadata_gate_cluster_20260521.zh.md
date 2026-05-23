# WP15-B Worldline Branch Metadata Gate

状态：`2026-05-21` mergeable / first slice complete。

语言版本：

- 英文主文：[wp15_worldline_branch_metadata_gate_cluster_20260521.md](wp15_worldline_branch_metadata_gate_cluster_20260521.md)
- 中文辅文：`wp15_worldline_branch_metadata_gate_cluster_20260521.zh.md`

输入：

- [WP15 counterfactual experiment generation](counterfactual_experiment_generation_wp15_20260521.zh.md)
- [WP15-A replay envelope and branch point](wp15_replay_envelope_branch_point_cluster_20260521.zh.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.zh.md)
- [WP11 facade vertical slice and provenance](../wp11_facade_vertical_slice_provenance/facade_vertical_slice_provenance_wp11_20260520.zh.md)
- `tests/scenario/test_scenario_compiler.py` 中现有 scenario compiler branch isolation tests

## 1. 目的

`WP15-B` 定义潜在 branchable worldline 如何命名、追踪，以及在缺失前置条件时如何拒绝。
它应让后续代码可以推理 parent/child worldline metadata，但不得假装 snapshot restore 或
counterfactual rollout execution 已经处于维护态。

## 2. 范围

范围内：

- baseline、parent 与 child worldline identifiers；
- branch point reference 与 replay envelope reference；
- branch reason、mutation/intervention intent、source 与 evidence refs；
- metadata-only、admitted、rejected 与 unsupported restore cases 的显式 support state；
- 拒绝 raw state mutation 或缺失 ancestry 的测试。

范围外：

- 执行 restored branch；
- `WP15-C` 负责的 counterfactual request admission；
- `WP15-D` 负责的 scenario/adversary generation；
- `WP15-E` 负责的 capability 或 experiment scoring。

## 3. 候选实现接缝

编辑前检查：

- `WP15-A` 的输出；
- `tests/scenario/test_scenario_compiler.py` branch isolation fixtures；
- `python/scenario/compiler/clone.py`；
- `src/runtime/contracts/runtime_dto_contracts.h`；
- `src/runtime/contracts/world_batch_contracts.h`。

首选方式：

- A 命名共享 vocabulary 后，在 replay/counterfactual contract surface 附近添加
  worldline metadata；
- 把 scenario compiler branch isolation 作为辅助 evidence，而不是 runtime worldline guarantee；
- 为缺失 parent id、child id、branch point、replay envelope、mutation intent 与
  evidence refs 提供稳定 rejection reasons。

## 4. Gate 规则

| Boundary | Required behavior |
|----------|-------------------|
| Parent/child identity | Branch metadata 命名 baseline 或 parent worldline 与 child worldline，且不冲突。 |
| Ancestry | 每条 branch 引用 replay envelope 与 branch point。 |
| Mutation intent | Intervention 或 mutation intent 显式，并带 source attribution。 |
| Unsupported restore | Metadata 可有效，但 executable restore 仍 unsupported 且可见。 |

## 5. 验收测试

最低测试：

- 有效 branch metadata fixture 引用 A 的 replay envelope 与 branch point；
- validation 拒绝缺失 parent/child ids、branch point、envelope、mutation intent 或
  evidence refs；
- validation 拒绝 request contracts 外的 raw state mutation claims；
- 测试确认 metadata-only branches 不暗示 snapshot/restore support。

建议命令：

```bash
git diff --check
python -m pytest -q tests/architecture/test_wp15_worldline_branch_metadata.py
python -m pytest -q tests/scenario/test_scenario_compiler.py -k "branch or runtime"
```

## 6. Handoff Contract

返回：

- touched metadata files；
- worldline status 与 rejection vocabulary；
- tests added or updated；
- exact commands run and outcomes；
- `WP15-C` 或 `WP15-E` 的 blockers。
