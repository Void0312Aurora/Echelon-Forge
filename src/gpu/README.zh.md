# `src/gpu` 边界

`gpu/` 保存 GPU helper、批量 packet runtime 和显式实验探针。当前默认 truth path 仍是 CPU `SimulationKernel::step()`；GPU 代码不能悄悄改变 canonical world-step 语义。

## 允许

- observation、visual、interaction broadphase、flight shaping 等 helper runtime。
- CUDA kernel 和 CPU fallback 包装。
- 与 `WorldBatchRuntime` 边界对接的 packet 提取、计算、回填 helper。
- 明确标注的实验探针。

## 禁止

- 未冻结的 exact world-step 替代主线。
- 拥有 mission/episode state machine。
- Python binding 实现。
- 修改 CPU truth state 语义而不经过 plan freeze 和 parity 验收。

## 子目录约定

- `experimental/`：未进入维护主线的探针和验证代码。

## 迁移备注

若后续重命名为 `accelerators/gpu`，应先冻结迁移计划并保持 include/CMake 兼容。GPU helper 可以加速 runtime packet，但不拥有 simulation truth。
