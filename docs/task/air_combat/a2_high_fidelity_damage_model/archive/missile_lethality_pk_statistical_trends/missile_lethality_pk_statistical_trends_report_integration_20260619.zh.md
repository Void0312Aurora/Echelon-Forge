# MLF-9 报告集成结果

状态：`2026-06-19` P4 initial pass。

英文主文：
[missile_lethality_pk_statistical_trends_report_integration_20260619.md](missile_lethality_pk_statistical_trends_report_integration_20260619.md)。

## 结果

`tools/diagnostics/air_combat_weapon_employment_process_probe.py` 现在会在 process-probe
结果中嵌入 `mlf9_statistical_trends` payload。该报告基于 probe 保留的
`lethality_chain_rows` 构建，并复用
`tools/diagnostics/mlf9_statistical_trends.py`。

process-probe CLI 也接受：

```bash
--mlf9_report_json_out <path>
--mlf9_group_by miss_distance_bucket,break_mode
--mlf9_confidence_level 0.95
```

如果提供 `--mlf9_report_json_out`，MLF-9 报告会作为独立 JSON artifact 写出；如果省略，
报告只保留在 process-probe JSON payload 内。

## 保留边界

集成报告声明：

- `sample_source`：`process_probe_lethality_chain_rows`
- `report_surface`：`process_probe_retained_diagnostics_artifact`
- `authority_boundary.real_world_pk`：`false`
- `authority_boundary.weapon_specific_lethality`：`false`
- `authority_boundary.target_specific_lethality`：`false`
- `authority_boundary.calibration_authority`：`false`
- `authority_boundary.reward_authority`：`false`
- `authority_boundary.entity_deletion_authority`：`false`

这使 MLF-9 保持为 diagnostics/report artifact。它不进入 reward terms、训练收益声明、
实体删除、runtime damage physics 或校准门。

## 验证

```bash
python3 -m py_compile \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  tools/diagnostics/mlf9_statistical_trends.py
PYTHONPATH=build-workshop:. pytest -q \
  tests/tools/test_mlf9_statistical_trends.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py::DiagnosticsProcessProbeSnapshotTests::test_run_probe_payload_and_chain_csv_include_lethality_chain_rows
```

结果：

- `3 passed`。

## 后续

Focused validation 已记录在
[missile_lethality_pk_statistical_trends_validation_20260619.zh.md](missile_lethality_pk_statistical_trends_validation_20260619.zh.md)。
后续 closeout 仍应保持现实 Pk 和 calibration held。
