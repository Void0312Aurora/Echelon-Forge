# WP21-D Scenario Intervention Generation Runtime

状态：`2026-05-21` planned；可在 WP21-A 后与 B 并行。

Language:

- English canonical:
  [wp21_scenario_intervention_generation_cluster_20260521.md](wp21_scenario_intervention_generation_cluster_20260521.md)
- Chinese companion: `wp21_scenario_intervention_generation_cluster_20260521.zh.md`

## 目的

将 WP15 generation request surface 转为 deterministic runtime-adjacent generator，
为 counterfactual experiments 产生 admitted artifacts，同时不直接修改 authoritative
simulation state。

## 范围

范围内：

- 第一条 maintained generator，覆盖 starting distance、altitude、speed、selected platform setup
  或 intervention metadata 等 parameter variation；
- 带 seed、lineage、evidence refs 与 baseline scenario/setup refs 的 versioned artifact output；
- non-mutation guard，证明 generated artifacts 只通过 setup/admission paths 进入 runtime；
- 如果 generator integration 可能依赖 loader-owned runtime state，则补充 `ScenarioLoader`
  mirror pre-gate 或 adapter boundary。

范围外：

- adversarial search、curriculum optimization 或 learned scenario generation；
- 默认改变 public scenario schemas；
- direct runtime state writes。

## 任务项

| ID | 项目 | 验收 |
|----|------|------|
| `D1` | Deterministic generator | 相同 request、version 与 seed 产生相同 artifact。 |
| `D2` | Artifact lineage | Artifact 记录 baseline scenario/setup、replay envelope、branch point、generator version 与 evidence refs。 |
| `D3` | Runtime admission seam | Generated artifact 可输入 setup/admission，且不绕过 facade authority。 |
| `D4` | Loader boundary guard | Scenario/content adaptation 与 maintained runtime state ownership 保持区分。 |

## 建议验证

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/scenario/test_scenario_generation_contracts.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/scenario -k "generation or scenario_loader"
```

## 交接

返回 generator API、artifact schema、non-mutation evidence、loader boundary notes、
touched files、commands run，以及面向 E 的 experiment input notes。
