# 诊断工具 README

`tests/diagnostics/` 只保留临时探索性或调试导向检查。它不是稳定
pytest 回归的维护目录。

当前状态：此目录下没有活跃 pytest 脚本。原有稳定检查已提升到对应能力域：

- `tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py`
- `tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py`
- `tests/runtime/air_combat/test_diagnostics_process_probe_summary.py`
- `tests/training/test_fire_timing_fault_localization_contracts.py`
- `tests/runtime/link/test_external_proxy_backend_contracts.py`
- `tests/runtime/bindings/test_lazy_binding_resolution.py`

当诊断脚本稳定为确定性回归证据时，应迁移至拥有该能力的测试域，或编码为
JSON contract。新增到此目录的文件应是短期入口，并在落地前说明目标提升路径。
