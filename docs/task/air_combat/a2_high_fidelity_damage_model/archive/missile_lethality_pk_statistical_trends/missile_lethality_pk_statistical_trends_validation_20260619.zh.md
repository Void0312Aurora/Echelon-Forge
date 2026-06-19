# MLF-9 聚焦验证

状态：`2026-06-19` P5 pass。

英文主文：
[missile_lethality_pk_statistical_trends_validation_20260619.md](missile_lethality_pk_statistical_trends_validation_20260619.md)。

## 范围

本验证覆盖当前 MLF-9 切片：

- process probe 中的 `structural_breakup` row-surface 暴露。
- 基于显式 rows 的确定性 MLF-9 trend extraction。
- 通过 `mlf9_statistical_trends` 和可选 `--mlf9_report_json_out` 完成的 process-probe
  retained report integration。
- MLF-9 工作面的文档和本地 Markdown 链接。

它不验证现实 Pk、具体弹种杀伤率、具体目标杀伤率、公开结果校准、reward shaping 或实体删除。

## 命令

```bash
python3 -m py_compile \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_chain.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_rows.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_snapshot.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/schema.py \
  tools/diagnostics/lethality_chain_contract.py \
  tools/diagnostics/mlf9_statistical_trends.py \
  tests/tools/test_mlf9_statistical_trends.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py

PYTHONPATH=build-workshop:. pytest -q \
  tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_summary.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py::DiagnosticsProcessProbeSnapshotTests::test_run_probe_payload_and_chain_csv_include_lethality_chain_rows \
  tests/training/test_fire_timing_fault_localization_contracts.py \
  tests/tools/test_mlf9_statistical_trends.py

git diff --check -- \
  docs/task/air_combat/a2_high_fidelity_damage_model \
  tools/diagnostics \
  tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py \
  tests/tools/test_mlf9_statistical_trends.py \
  tests/training/test_fire_timing_fault_localization_contracts.py
```

本地 Markdown 链接检查覆盖父级 A2 README 文件和 MLF-9 目录。

## 结果

- `py_compile`：pass。
- 聚焦 pytest：`50 passed`。
- `git diff --check`：pass。
- 本地 Markdown 链接检查：`20 markdown files; missing local links: 0`。

## 验收准备度

当前切片可以进入 `MLF9-Q6` closeout 讨论。可接受部分应限制为 deterministic
simulation-trend extraction 和 retained diagnostics/report exposure。校准和现实 Pk 继续 held。

## 残余

- MLF-10 必须负责 calibration gates、public outcome admission，以及任何未来具体武器 /
  目标概率讨论。
- 只要 MLF-9 报告被导出或引用，就应继续标注为 synthetic simulation trends。
