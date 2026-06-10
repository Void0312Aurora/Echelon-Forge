# WP15-D Scenario And Adversary Generation Request Surface

状态：`2026-05-21` mergeable / first slice complete。

语言版本：

- 英文主文：[wp15_scenario_adversary_generation_surface_cluster_20260521.md](wp15_scenario_adversary_generation_surface_cluster_20260521.md)
- 中文辅文：`wp15_scenario_adversary_generation_surface_cluster_20260521.zh.md`

输入：

- [WP15 counterfactual experiment generation](counterfactual_experiment_generation_wp15_20260521.zh.md)
- [WP8 learning face](../wp8_learning_face/learning_face_wp8_20260520.zh.md)
- [WP14 capability composition](../wp14_capability_composition/capability_composition_wp14_20260521.zh.md)
- 当前 `python/scenario/compiler/*`
- 当前 `python/scenario/runtime/*`
- 当前 `tests/scenario/test_scenario_compiler.py`

## 1. 目的

`WP15-D` 创建 generated scenarios 与 adversaries 的 request surface。输出应是确定性、
source-attributed、遵守 seed/version discipline，并且可以作为 experiment input evidence
处理。它不能变成修改 authoritative simulation state 的 runtime 后门。

## 2. 范围

范围内：

- scenario/adversary generation request 与 validation vocabulary；
- deterministic seed、generator version、source、baseline scenario、branch point 或
  replay refs，以及 capability/evidence refs；
- 以 metadata 表达 scenario variation、adversary placement、route/mission perturbation
  与 stressor injection 等 request kind；
- 证明 generated inputs 仍是显式 requests 或 scenario artifacts 的 compiler/runtime guard tests；
- 可供后续 experiment evidence 使用的 deterministic fixtures。

范围外：

- broad generator algorithm implementation；
- direct runtime state mutation；
- 改变现有 scenario JSON compatibility；
- 声明 generated scenarios 是 maintained truth 或 capability support。

## 3. 候选实现接缝

编辑前检查：

- `python/scenario/compiler/service.py`
- `python/scenario/compiler/clone.py`
- `python/scenario/runtime/models.py`
- `tests/scenario/test_scenario_compiler.py`
- `docs/task/simulation_architecture/wp8_learning_face/*scenario*`

首选方式：

- 添加小型 Python request/validation module，而不是编辑整个 scenario compiler；
- generated output 保持为 data 加 evidence metadata；
- 包含 deterministic seed/version checks；
- unsupported request kinds 以稳定 reasons fail closed。

## 4. Gate 规则

| Boundary | Required behavior |
|----------|-------------------|
| Seed discipline | Request 必须命名 deterministic seed 与 generator version。 |
| Source attribution | Request 必须命名 source、baseline scenario 与 evidence refs。 |
| Non-mutation | Generated request artifacts 不直接修改 runtime state。 |
| Compatibility | 现有 scenario compiler/runtime behavior 保持兼容。 |

## 5. 验收测试

最低测试：

- 有效 scenario/adversary request fixture 能确定性通过 validation；
- 缺失 seed、generator version、source、baseline scenario 或 evidence refs 时以稳定
  reasons 拒绝；
- unsupported generation kind fail closed；
- 现有 scenario compiler branch/runtime isolation tests 仍通过。

建议命令：

```bash
git diff --check
python -m pytest -q tests/scenario/test_scenario_generation_contracts.py
python -m pytest -q tests/scenario/test_scenario_compiler.py -k "branch or runtime"
```

## 6. Handoff Contract

返回：

- touched Python files；
- request field names 与 validation helpers；
- rejection reason vocabulary；
- tests added or updated；
- exact commands run and outcomes；
- `WP15-E` 的 blockers。
