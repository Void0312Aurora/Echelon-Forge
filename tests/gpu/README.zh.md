# GPU 测试 README

`tests/gpu/` 包含 GPU 运行时绑定和 CUDA 集成回归测试。

## 范围

- GPU 运行时绑定 (`ef_py` capability probing、DLPack 张量导出、设备属性)
- CUDA 导入顺序和运行时环境设置
- 与 `src/gpu/` 和 Python GPU bindings 对齐

## 与架构测试的区别

- `tests/gpu/`：运行时行为测试（导入、绑定、capability、DLPack 往返）
- `tests/architecture/runtime_profiles/test_runtime_profile_contracts.py`：架构合同守卫（GPU truth boundary、parity budget 声明）

## 约束

- GPU 测试默认通过 `EF_ENABLE_CUDA_EXPERIMENTS` 门控，与 `src/gpu/README.md` 中定义的 CPU-truth-first 策略一致。
- 当 CUDA 不可用时，测试应优雅跳过（`pytest.skip` 或等价机制），而不是 fail。
- 不应在此目录中添加纯诊断/探索性脚本——它们属于 `tools/diagnostics/`。
