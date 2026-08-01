# CUDA 驻留运行时第二期迭代账本

语言版本：

- 英文规范版：[cuda_resident_runtime_program_2_iteration_log_20260731.md](cuda_resident_runtime_program_2_iteration_log_20260731.md)
- 中文伴随版：`cuda_resident_runtime_program_2_iteration_log_20260731.zh.md`
- 计划权威：[cuda_resident_runtime_program_2_20260731.zh.md](cuda_resident_runtime_program_2_20260731.zh.md)
- 规模策略：[cuda_resident_runtime_program_2_size_policy_20260731.json](cuda_resident_runtime_program_2_size_policy_20260731.json)

- 分支：`codex/cuda-resident-runtime-program-2`
- 父级：`935926e83b18187c79a6e0be2ca010276c1a6fc4`
- maintained baseline：`395e02b7dfeaa87baedb2611ec503d14ab137ce3`

状态：**CR2-1 已以 db7e6ad4 提交。CR2-2a 已获独立批准；单一 commit 待完成。**
RB0-RB11 计划仍是无晋级关闭。本账本只记录新分支内计划，
不改变 maintained support flags。

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

## CR2-1 candidate —— CUDA translation unit 物理拆分

CR2-1 保留原有 kernel body、host-visible error 行为和 private window trace，
只把实现移入独立 translation unit。删除的 `cuda_world_store_cuda.cu` 没有被另一个
更大的 coordinator 替代；新的 coordinator 文件只有 69 行 host wrapper。

### 精确 write set

- 在 `CMakeLists.txt` 中把 resident CUDA source 替换为八个 `.cu` 文件；
- 增加一个 shared internal `.cuh` contract 和一个 shared device-math `.cuh`；
- 增加 storage、barrier、Phase A、Phase B、Phase D、observation、state
  readback、window 八个 `.cu` 文件；
- 更新 CUDA architecture guards 与 RB9 ledger source label；
- 更新 performance contract comment，指向拆分后的 source family；
- 删除旧的 2528 行 monolith。

没有修改 public facade、support flag、ABI、DTO、runtime selection 或 CUDA
separable compilation。跨 translation unit 只有 host wrapper；kernel 与 device helper
仍私有于各自 `.cu`。

### 结构不变量

- 保留 10 个 kernel：Phase A 1 个、Phase B 3 个、Phase D 3 个、observation 2 个、
  barrier 1 个；
- private window 仍按相同顺序 launch 六个 B/D kernel，在序列后执行一次
  `cudaDeviceSynchronize()`，并保留 status/error 检查与 barrier publication；
- resource-query helper 保留固定 128-thread occupancy 语义和原错误字符串；
- resident target 不启用 CUDA separable compilation/RDC。

### 规模证据

| 模块 | 行数 |
| --- | ---: |
| `cuda_world_store_cuda_internal.cuh` | 291 |
| `cuda_world_store_cuda_math.cuh` | 139 |
| `cuda_world_store_cuda_storage.cu` | 547 |
| `cuda_world_store_cuda_barrier.cu` | 264 |
| `cuda_world_store_cuda_phase_a.cu` | 204 |
| `cuda_world_store_cuda_phase_b.cu` | 497 |
| `cuda_world_store_cuda_phase_d.cu` | 231 |
| `cuda_world_store_cuda_observation.cu` | 174 |
| `cuda_world_store_cuda_state_readback.cu` | 271 |
| `cuda_world_store_cuda_window.cu` | 69 |

CR2-0 的 2528 行 exception 已在机器策略中清空；919 行 replay test 与 804 行
RB9 probe 仍是冻结的 watch item。

### 验证证据

- Visual Studio/CUDA 13.0、`CMAKE_CUDA_ARCHITECTURES=86`、Release 构建：
  `ef_cuda_resident_lifecycle_test`、`ef_cuda_resident_replay_test`、
  `ef_cuda_resident_rb9_cuda_probe` 均编译并链接成功；
- lifecycle executable：11/11 test cases，527/527 assertions 通过；
- replay executable：3/3 test cases，47/47 assertions 通过；
- RB9 CUDA probe 在 NVIDIA GeForce RTX 3090（SM 8.6）上运行。既有 hold reasons
  仍明确报告：full-facade invocation 不可用、learner/device consumption 不可用、
  GPU counters 为 `ERR_NVGPUCTRPERM`，以及 identity-inclusive reset determinism
  仍是 diagnostic；
- CUDA-off 配置成功；CPU lifecycle/replay target 已构建并通过（11/11，66 个
  assertions；3/3，14 个 assertions）。完整 CUDA-off probe target 未构建，原因是
  未修改的 `ef_core` 图当前在 MSVC 下存在 `__builtin_ctz`、`M_PI` 等既有 portability
  编译错误；
- architecture/size/performance/Phase A/B/D 聚焦测试 31 项通过；Ruff 与
  `git diff --check` 通过。
- 完整 `tests/architecture/runtime_profiles` 运行结果为 52 passed、15 failures；
  15 项全部是 Windows snippet 环境找不到 `g++`（`WinError 2`），不涉及 CR2-1
  修改路径。

### 独立复核门

新的 reviewer `/root/cr2_split_review` 在核对完整 staged/unstaged/untracked
write set、与 RB11 单体的归一化 kernel/function body 比对、CMake device-link
拓扑、size policy 及聚焦构建/测试证据后返回 **`APPROVE`**，没有 CR2-1 blocker。
上述精确 write set 现获授权形成一个 CR2-1 commit；该 commit 不包含 merge、push
或 promotion。

## CR2-2a candidate —— RB9 probe session 拆分

### 范围与冻结行为

本 sub-iteration 只做结构迁移。RB9 executable 保持既有 CPU/CUDA lane 选择、
mode matrix、private phase sequence、JSON schema、trace signature、unavailable
reason 与 hold reason。cuda_resident_rb9_evidence_20260730 下的历史证据不修改。
不增加 full-window SPI、facade、support flag、learner contract 或性能结论。

### 精确 write set

- 增加 cuda_resident_rb9_probe_session.h，提供小型 ProbeSession/Mode/
  WindowTiming interface；
- 增加 cuda_resident_rb9_probe_session.cpp，承载 lane-specific session 的
  storage、setup/reset、window execution、digest 与 diagnostics；
- 从 cuda_resident_rb9_probe.cpp 删除重复 session 实现和 helper；
- 两个 RB9 CMake target 都编译新实现；
- 更新 performance architecture guard，使其检查迁移后的 CUDA sequence；
- 从机器可读 size policy 移除已解决的 probe watch item；
- 更新中英文计划与本账本。

### 规模与验证证据

probe 为 567 个物理行，新 session implementation 为 255 行，interface header
为 45 行；两个实现文件都低于 700 行 soft target，replay test 是唯一 review-band
watch item。聚焦 architecture 测试通过：size/performance/Phase A/B/D 共 27 项，
contract/lifecycle/closure/replay 共 20 项。CUDA Release（VS2022、CUDA 13.0、
SM86）已重新配置并构建 probe、lifecycle、replay target；lifecycle 为 11/11
case、527/527 assertions，replay 为 3/3、47/47；RTX 3090 上 probe smoke 返回
0，原有 private-surface hold reason 未变化。CUDA-off probe target 仍被未修改的
ef_core MSVC portability 错误阻塞（__builtin_ctz、M_PI 及其后续诊断）。在关闭
project references 的独立 MSBuild ClCompile 中，CPU probe、新 session 实现与
replay harness 均已成功编译。

### 独立复核门

新的 reviewer /root/cr2_2a_review 在核对完整 staged/unstaged/untracked write
set、迁移的全部 10 个可观察字符串、CPU/CUDA 操作顺序和计时边界、两个 CMake
lane、行数、聚焦测试/构建证据以及未改动的历史 RB9 evidence 后返回
**APPROVE**，没有 CR2-2a blocker。该结论授权形成一个 CR2-2a commit；不授权
merge、push、promotion、CR2-2b 语义或历史 evidence 改写。
