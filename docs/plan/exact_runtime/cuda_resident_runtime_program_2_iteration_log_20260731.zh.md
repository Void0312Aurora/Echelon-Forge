# CUDA 驻留运行时第二期迭代账本

语言版本：

- 英文规范版：[cuda_resident_runtime_program_2_iteration_log_20260731.md](cuda_resident_runtime_program_2_iteration_log_20260731.md)
- 中文伴随版：`cuda_resident_runtime_program_2_iteration_log_20260731.zh.md`
- 计划权威：[cuda_resident_runtime_program_2_20260731.zh.md](cuda_resident_runtime_program_2_20260731.zh.md)
- 规模策略：[cuda_resident_runtime_program_2_size_policy_20260731.json](cuda_resident_runtime_program_2_size_policy_20260731.json)

- 分支：`codex/cuda-resident-runtime-program-2`
- 父级：`935926e83b18187c79a6e0be2ca010276c1a6fc4`
- maintained baseline：`395e02b7dfeaa87baedb2611ec503d14ab137ce3`

状态：**CR2-2a 已以 bf695071 提交，CR2-2p 已以 dee02146 提交。
CR2-2b 是当前 active、可独立复核的 full-window candidate。**
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

## CR2-2p candidate —— 真实 Flecs CPU lane 可移植性前置

### 范围与精确 write set

只要 maintained `FlecsCpuBackend` 图无法在选定 VS2022 工具链编译，CR2-2b 就
不能声称 CPU/CUDA 共同 surface。本前置迭代与 full-window 语义隔离，仅包含：

- 用 C++20 等价的 `std::countr_zero` 替换 GCC-only `__builtin_ctz`；
- 把 `environment_model.h` 从 `IControlModel` class body 移到外部，并把两处陈旧的
  nested type 拼写改回预期的全局 interface；
- 只为 MSVC 下的 `ef_core` 启用既有 `M_PI` 公式，不改变常量值；
- 增加聚焦 architecture guard，并更新本中英文账本。

本 commit 不包含 CUDA source、resident contract、support flag、facade selection、
性能结果或 CR2-2b runner/probe 文件。

### 验证与规模证据

VS2022 Release 已成功构建 `ef_core`、`ef_facade` 与 candidate 真实 Flecs
full-window CPU probe。该 probe 在 runner 外加载 `examples/config/database`，完成
两个窗口并以 0 退出。更宽的 `ef_test` 构建已越过本次修正的 core/control-model
单元，但仍被 test-owned header 中另一些既有 MSVC 问题阻塞，例如
`kalman_seeker.h` 在 `ef_core` 之外使用 `M_PI`；本前置迭代不扩张处理这些问题。

`control_model.h` 为 28 行，`default_control_model.cpp` 为 542 行。
`world_batch_runtime.cpp` 在本 candidate 前已是 1207 行，增加 `<bit>` 后为 1208
行；这是既有的、非 CR2-owned hard-limit debt，不是新模块，也没有被 CR2 policy
的 exception 隐藏。本迭代不拆分该 owner，因为这会把结构重构混入窄范围
portability unblock；该债务继续明确保留。

### 独立复核门

独立 reviewer 已核对精确 staged subset、API/type 意图、bit-scan 等价性、MSVC
definition 范围、聚焦构建证据，以及 CR2-2b 语义文件未进入提交，并返回
**`APPROVE`**。CR2-2p 已以 `dee02146` 提交；该提交不授权 merge、push、promotion
或 CR2-2b 本身。

## CR2-2b candidate —— 两个真实 lane 共用一套 full-window SPI

### 范围与精确 write set

CR2-2b 在现有 `IWorldBatchBackend` 之上增加 backend-neutral、同步 runner，
不增加第二套 facade，也不增加 support/admission surface。唯一声明的序列是：

```text
setup → input_injection → evaluation(empty) → advance(WorldBatch) → export
```

CUDA backend 的 `advance` 调用 `CudaWorldStore::advance_window()`，由 store 自动
完成 injected stage 的 publish 与 window commit。store 的显式状态机为
`awaiting_input → input_injected → stage_published → awaiting_input`；publish 失败
停在 `input_injected`，commit 失败停在 `stage_published`，因此 retry 不会重复
publish；直到 commit/reset/setup 前禁止再次 inject。runner 在任何失败后 poison
session，并记录稳定 operation/failure code 与最后完成的 surface barrier。

write set 仅包含 full-window contract/runner、CUDA backend/store 状态迁移、conformance
测试、使用同一 probe source 的两个 lane target、纯 JSON CPU/CUDA comparator、聚焦
architecture guard 与本计划/账本更新。CPU database load 保留在 runner 外部。历史
RB9 probe/session 和 `cuda_resident_rb9_evidence_20260730` 不修改；不引入 learner
lease 或性能结论。

### 规模与验证证据

所有新增 CR2-2b implementation/test/probe module 均低于 700 行 soft target：contract
105，runner 242/30，probe 179，comparator 76，conformance test 365，architecture
guard 87 行。已有 919 行 replay test 没有增长。修改后的 resident host module 为
665 行（`cuda_world_store.cpp`）和 586 行（`cuda_resident_backend.cpp`），均低于
soft target。

CUDA Release（VS2022、CUDA 13.0、SM86）已构建并运行 full-window probe，完成两个
window 与九个 surface operation。CPU Release 在 CR2-2p 之后成功构建 `ef_core`、
`ef_facade` 与真实 `FlecsCpuBackend` probe；它在 runner 外加载 database，并消费同一
trace。自动 comparator 将两侧 stdout 解析为纯 JSON，确认 surface id、trace signature
以及全部九条 operation/request/window/success/barrier record 完全一致；lane/backend
标识按设计不同。CUDA full-window doctest 为 5/5 case、122/122 assertions，CUDA-off
stub 为 5/5 case、105/105 assertions；更严格的 injection guard 下 lifecycle suite
为 11/11、528/528，replay 为 3/3、47/47。

### 独立复核门

必须由新的独立 agent 审阅完整 staged/unstaged/untracked CR2-2b write set，核对共同
序列、状态机 retry 语义、纯 JSON 比较证据、精确 CMake lane 拓扑、support flag 不变、
历史 evidence 保留与全部规模限制。只有 `APPROVE` 才允许形成一个 CR2-2b commit。
