<!-- Machine-translated draft generated on 2026-05-18 from tools/archive/README.md. Review before treating this file as authoritative. -->

# 归档工具

`tools/archive/` 存放着此前留在仓库根目录的临时探测脚本，仅保留用作手动参考。

该目录的状态为 `Archived`。这些文件不是文档、测试或活跃工作流的维护入口。

当前包含的已归档辅助脚本：

- [check_binding.py](check_binding.py)
  - 手动 ef_py 绑定成员探测脚本，仅保留用于直接人工审查。
- [batch_api_probe.py](batch_api_probe.py)
  - 针对 C++ 批处理准备 API 的手动探测脚本。
- [world_batch_vec_env_benchmark.py](world_batch_vec_env_benchmark.py)
  - 更早的 vec-env 吞吐量基准测试，早于当前维护的诊断布局。
- [diagnose_training_matrix.py](diagnose_training_matrix.py)
  - 遗留评估矩阵辅助脚本，用于解析旧版 `evaluate.py` 文本摘要格式。
- `legacy_test_diagnostics/`
  - 历史性的单次诊断脚本，从 `tests/diagnostics/` 迁移而来，因为已不再是维护的测试入口。
- `legacy_scripts/`
  - 历史性的 shell/Python 工作流包装器，已被维护的 `tools/` 入口所取代。
