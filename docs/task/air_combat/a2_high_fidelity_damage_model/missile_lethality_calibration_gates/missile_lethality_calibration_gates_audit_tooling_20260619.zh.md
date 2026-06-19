# MLF-10 准入审计工具

状态：`2026-06-19` P3 complete。

英文主文：
[missile_lethality_calibration_gates_audit_tooling_20260619.md](missile_lethality_calibration_gates_audit_tooling_20260619.md)。

## 实现

- 工具：
  [mlf10_calibration_admission.py](../../../../../tools/diagnostics/mlf10_calibration_admission.py)
- 聚焦测试：
  [test_mlf10_calibration_admission.py](../../../../../tests/tools/test_mlf10_calibration_admission.py)
- 契约：
  [missile_lethality_calibration_admission_contract_20260619.zh.md](missile_lethality_calibration_admission_contract_20260619.zh.md)

工具读取 `mlf10.calibration_evidence_manifest.v1`，重新计算每条 evidence decision，
并输出 `mlf10.calibration_admission_report.v1`。它不信任输入中的 `admitted`，
也不修改 runtime state。

## 已覆盖判定

聚焦 fixtures 覆盖：

- 全部 v1 gate 通过后的 `effect_scale_authority` admitted 正向路径；
- retained engineering proxies；
- retained MLF-9-style synthetic reports；
- fail-closed rights 和 source gates；
- v1 禁止的 Pk request；
- rejected sources；
- manifest-level non-claim failure；
- CLI retained-report 输出；
- 当前仓库 manifest 的零 admitted 结论。

## 验证

```text
python -m py_compile \
  tools/diagnostics/mlf10_calibration_admission.py \
  tests/tools/test_mlf10_calibration_admission.py

python -m pytest -q -p no:cacheprovider \
  --basetemp Temp/mlf10-pytest-current \
  tests/tools/test_mlf10_calibration_admission.py
```

结果：`7 passed`。

## 边界

正向 admitted fixture 只证明 contract 的正向分支可达，不接纳仓库证据。当前仓库
manifest 继续 fail-closed。
