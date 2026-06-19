# MLF-10 聚焦验证

状态：`2026-06-19` P5 pass。

英文主文：
[missile_lethality_calibration_gates_validation_20260619.md](missile_lethality_calibration_gates_validation_20260619.md)。

## 验证表面

- P1 类校准证据盘点。
- P2 admission contract 和 report schema。
- P3 确定性 admission-audit tooling。
- P4 当前仓库 evidence manifest 和 retained report。
- 相邻 MLF-9 trend-report 行为。
- 现有 A2 source-admission guardrails。

本验证不测试 real-world Pk、deterministic fuze reliability、weapon-specific
lethality、target-specific lethality、runtime 参数重调、reward authority 或
entity deletion。

## 命令和结果

```text
python -m py_compile \
  tools/diagnostics/mlf10_calibration_admission.py \
  tools/diagnostics/mlf9_statistical_trends.py \
  tests/tools/test_mlf10_calibration_admission.py \
  tests/tools/test_mlf9_statistical_trends.py
```

结果：pass。

```text
python -m pytest -q -p no:cacheprovider \
  --basetemp Temp/mlf10-validation-pytest \
  tests/tools/test_mlf10_calibration_admission.py \
  tests/tools/test_mlf9_statistical_trends.py \
  tests/architecture/damage_model/test_source_admission_audit.py
```

结果：`7 passed`。

Retained report 已重新生成到 `Temp/mlf10-validation-report.json`，并与
[mlf10_calibration_admission_report_20260619.json](mlf10_calibration_admission_report_20260619.json)
逐字节比较。结果：match。

`git diff --check` 通过。本地 Markdown 验证覆盖 18 个 MLF-10 和父级索引 Markdown
文件，`missing_local_links=0`。

## 当前证据判定

| Classification | Count |
| --- | ---: |
| `engineering_proxy` | 1 |
| `retained_non_authoritative` | 1 |
| `calibration_candidate` | 0 |
| `admitted` | 0 |
| `rejected` | 1 |
| `blocked` | 4 |

## P5 决策

Gate infrastructure 已具备收口条件。由于当前 report 没有 admitted evidence，
calibration authority 继续 held。
