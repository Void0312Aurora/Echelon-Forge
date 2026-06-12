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
- [world_batch_runtime.py](world_batch_runtime.py)
  - 已归档的 raw `WorldBatchRuntime` 基准。维护中的 benchmark 入口现在使用 facade/vector-env runtime family。
- [diagnose_training_matrix.py](diagnose_training_matrix.py)
  - 遗留评估矩阵辅助脚本，用于解析旧版 `evaluate.py` 文本摘要格式。
- [arma_proxy_backend_echelon_env.py](arma_proxy_backend_echelon_env.py)
  - 已归档的 raw `UniversalEnv` Arma proxy backend。维护中的 Arma bridge diagnostics 面只保留本地 stub 入口。
- [analyze_cooperative_observation_scales.py](analyze_cooperative_observation_scales.py)
  - 已归档的 raw single-env observation scale sampler；文件名暗示 cooperative 覆盖，但实现直接构造 `UniversalEnv`。
- [visual_resolution.py](visual_resolution.py)
  - 已归档的视觉降采样基准，依赖 raw `UniversalEnv`；活跃 benchmark 现在只暴露维护中的 runtime family。
- [coarse_route_segments.py](coarse_route_segments.py)
  - 已归档的粗略航路段 rollout 基准，依赖 raw `UniversalEnv` 和直接策略加载。
- `legacy_test_diagnostics/`
  - 历史性的单次诊断脚本，从 `tests/diagnostics/` 迁移而来，因为已不再是维护的测试入口。
- `legacy_scripts/`
  - 历史性的 shell/Python 工作流包装器，已被维护的 `tools/` 入口所取代。
