# CUDA 驻留运行时第二期迭代账本

语言版本：

- 英文规范版：[cuda_resident_runtime_program_2_iteration_log_20260731.md](cuda_resident_runtime_program_2_iteration_log_20260731.md)
- 中文伴随版：`cuda_resident_runtime_program_2_iteration_log_20260731.zh.md`
- 计划权威：[cuda_resident_runtime_program_2_20260731.zh.md](cuda_resident_runtime_program_2_20260731.zh.md)
- 规模策略：[cuda_resident_runtime_program_2_size_policy_20260731.json](cuda_resident_runtime_program_2_size_policy_20260731.json)

- 分支：`codex/cuda-resident-runtime-program-2`
- 父级：`935926e83b18187c79a6e0be2ca010276c1a6fc4`
- maintained baseline：`395e02b7dfeaa87baedb2611ec503d14ab137ce3`

状态：**CR2-0 candidate freeze；独立复核与提交尚未完成。** RB0-RB11 计划仍是
无晋级关闭。本账本只记录新分支内计划，不改变 maintained support flags。

## CR2-0 candidate —— 计划与规模治理冻结

### 只读 baseline 盘点

以下 CUDA-resident inventory 以 tracked file bytes 和物理 `splitlines()` 计数：

| 路径 | 行数 | 分类 | 动作 |
| --- | ---: | --- | --- |
| `src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda.cu` | 2528 | 超过硬上限 | CR2-1 首先拆分；不得增加语义 |
| `src/tests/test_cuda_resident_replay.cpp` | 919 | review band | 冻结增长；修改前先拆分 |
| `src/tools/experimental/cuda_resident/cuda_resident_rb9_probe.cpp` | 804 | review band | 冻结增长；扩展前先拆分或重新分类 |
| `src/runtime/facade/internal/cuda_resident/cuda_world_store.cpp` | 629 | 低于 soft target | 只能在一个语义 slice 内修改 |
| `src/runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.cpp` | 587 | 低于 soft target | 只能在一个语义 slice 内修改 |
| `src/runtime/facade/internal/cuda_resident/cuda_resident_backend.cpp` | 582 | 低于 soft target | 只能在一个语义 slice 内修改 |

更大仓库中还有与本计划无关的 1000 行以上文件。CR2 不会默默把这些文件纳入
治理或改写；策略只作用于机器记录列出的 CUDA-resident scope。

### 冻结 write set

CR2-0 只允许文档与 guard：

- 中英文 program 与 iteration log；
- 机器可读 size policy；
- exact-runtime 与 parent plan index；
- policy JSON 的 `.gitattributes` 字节稳定规则；
- 守卫 baseline exception/watch item 的 architecture test。

CR2-0 不修改 runtime、CUDA kernel、CMake target、support flag、ABI 或性能数据。
size guard 会在 staging 前扫描声明的 CR2 artifact 前缀下的 tracked 文件与
worktree candidate 文件；独立 reviewer 还会核对完整的 staged/untracked write set。

### 复核门

独立 reviewer 必须核对 branch base、精确 write set、行数/字节阈值、baseline
exception expiry，以及没有 runtime 变更。只有 `APPROVE` 才允许形成一个 CR2-0
commit。CR2-1 是唯一下一授权，且必须先消除 2528 行例外，再进行语义工作。
