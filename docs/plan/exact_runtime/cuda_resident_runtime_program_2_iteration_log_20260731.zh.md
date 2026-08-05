# CUDA 驻留运行时第二期迭代账本

语言版本：

- 英文规范版：[cuda_resident_runtime_program_2_iteration_log_20260731.md](cuda_resident_runtime_program_2_iteration_log_20260731.md)
- 中文伴随版：`cuda_resident_runtime_program_2_iteration_log_20260731.zh.md`
- 计划权威：[cuda_resident_runtime_program_2_20260731.zh.md](cuda_resident_runtime_program_2_20260731.zh.md)
- 规模策略：[cuda_resident_runtime_program_2_size_policy_20260731.json](cuda_resident_runtime_program_2_size_policy_20260731.json)

- 分支：`codex/cuda-resident-runtime-program-2`
- 父级：`935926e83b18187c79a6e0be2ca010276c1a6fc4`
- maintained baseline：`395e02b7dfeaa87baedb2611ec503d14ab137ce3`

状态：**CR2-4a 已以 d778c67c 提交。CR2-4b 是当前 active、可独立复核的
selected-payload parity candidate。**
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

独立 reviewer 对精确的 18-file write set、共同序列、retry 语义、真实 CPU/CUDA
probe、comparator、support 边界与规模证据返回 **`FINAL APPROVE`**。CR2-2b 已以
`607c1f33` 提交；这不授权 merge、push、support promotion 或历史 evidence 修改。

## CR2-3 candidate —— 自有 device lease 与显式 consumer 边界

### 范围与精确 write set

CR2-3 增加 private `cuda_resident.device_observation_lease.v1` contract 与
`cuda_resident.device_consumer_smoke.v1` CUDA kernel path。lease 自有 D2D-packed
observation values、ids、ready event、device/default-stream identity、以 element
为单位的 tensor descriptor，以及 allocation/reset/committed-window/source epoch。
consumer receipt 持有 input lease，并独立拥有 output buffer 与 completion event。
复制 lease/receipt 会共享显式 owner；允许重复 submit/await。测试覆盖 lease 跨 reset、
backend 销毁，以及 receipt 跨 consumer 销毁。

store 只用 host lifecycle/window state 判定 acquisition。setup 不等于 committed
window；只有成功 commit 才递增 host epoch。acquisition 不调用 `state_snapshot()`，
也不读取 device global version。旧 device-view API 保留为 RB7 compatibility 的显式
diagnostic path，但 RB9 measured consumer mode 不再调用它。

write set 仅包含新 contract/consumer/lease owner、窄范围 backend/store host epoch
plumbing、已有 observation CUDA unit、聚焦 C++/architecture 测试、RB9 session/ledger
计时边界、CMake、size-policy inventory 与本中英文计划/acceptance 记录。它不改
`IWorldBatchBackend`、RuntimeCapabilities、admission、support flag、RuntimeFacade
selection 或历史 RB9 evidence 目录。

### 计时与 transfer 边界

device-consumer measurement 是 acquire → submit → 显式 event await。acquisition 与
submit 成功路径没有 D2H，也没有显式 `cudaDeviceSynchronize`；await 只使用
`cudaEventSynchronize`。diagnostic materialization 在 await 前会被拒绝；await 后
恰好执行两次 D2H，而且发生在对应 sample timer 记录之后。cold/warm sample 在记录
时间后 drain 一个 receipt；rollout sample 在 rollout timer 关闭前保留全部 receipt，
随后统一验证与释放，因此 reported peak requested bytes 按 `rollout_windows` 倍的
lease/output bytes 计。

transfer ledger 明确使用 `device_consumer_measured_path_d2h_copy_count = 0`；它表示
consumer 增量，不是说整个 window 没有 D2H。resident window 仍记录五次 barrier-status
D2H，选择 host export 时为七次；diagnostic 两次 D2H 单独报告。`cudaMalloc` 可能
隐式同步，因此 `device_consumer_allocation_may_synchronize = true` 继续作为 CR2-5
risk 显式保留；CR2-3 不声称已完成 allocation pool 或 tuning。

### Failure、规模与验证证据

稳定 failure code 覆盖 request/lease/receipt validity、缺 committed window、epoch/
device/stream/layout mismatch、lease allocation/pack/event、consumer allocation/
launch/event、wait 与 diagnostic materialize。一次性 fault seam 覆盖 allocation、
launch、event record、wait 与 diagnostic failure，并避免 double-free；contract 允许的
场景可用同一 retained lease/receipt retry。CUDA-off 明确 fail-closed。

全部 CR2-3 module 低于 soft limit：contract 209 行，consumer 246/49，host-internal/
lease wrapper 33/66，observation CUDA 441，C++ test 292，architecture guard 197，
RB9 probe/session/header 597/304/46，store 661，backend 636。919 行 replay watch item
没有增长，也没有新增例外。

VS2022 Release、CUDA 13.0/SM86 在 RTX 3090 上通过 14/14 lifecycle case、599/599
assertions；CUDA-off 为 14/14、91/91。真实两世界 RB9 smoke 生成四个 available row。
device-consumer row 报告 consumer measured D2H 0、diagnostic D2H 2、一次 event wait、
allocation sync risk 为 true、deferred receipt 2，并在 peak bytes 中计入两个 owner。
本次 build log 中新 pack/consumer kernel 分别为 16/14 registers、reported spill 0；
这只是 compile sanity fact，不是 CR2-5 full resource gate。聚焦 CR2-3/performance/
size architecture 测试为 25/25，new guard 的 Ruff check/format 通过。

### 独立复核门

新的独立 agent 必须审阅完整 staged/unstaged/untracked write set、RAII/event cleanup、
epoch 与 cross-destruction 语义、deferred timing 与 rollout peak accounting、CUDA-on/off
结果、support/evidence 不变和全部规模限制。只有 `APPROVE` 才允许一个 CR2-3
commit；这不授权 merge、push、RuntimeFacade promotion 或 CR2-4。

## CR2-4a candidate —— 零语义拆分 replay watch item

CR2-4a 只做结构拆分。原 919 行的
`src/tests/test_cuda_resident_replay.cpp` 被拆成断言 owner
（`test_cuda_resident_replay.cpp`，139 行）、projection/frame support
（`test_cuda_resident_replay_projection.cpp`，611 行）、lane runner/trace
support（`test_cuda_resident_replay_support.cpp`，175 行）与声明 header（58
行）。四者都继续进入 size-policy 扫描，并低于 700 行 test 与 600 行 header
soft limit。
旧 RB8 frozen 93-field budget、手工 CPU fixture oracle、显式 CUDA
`publish_stage()` seam、预期 quarantine、failure tests、trace-signature 检查与
历史 RB9 evidence 均不变。

精确 write set 仅包含三个新 support owner、原 test、CMake source list、replay
architecture guard、机器可读 size inventory 与中英文计划/迭代记录。不改 runtime
backend、parity budget、JSON evidence、support flag、admission、RuntimeFacade、
learner lease 或 kernel path。CR2-4b 是后续独立语义迭代；本拆分不声称
selected-slice parity 或 deterministic reset release。

candidate gate：CUDA-on/off focused replay target 重建，保持 CUDA-on 3/3 case、
47/47 assertions 与 CUDA-off 3/3 case、14/14 assertions；replay/size/runtime
architecture guard 与 Ruff 通过；没有模块进入
watch band；并由独立 agent 审阅完整 staged write set 后才允许一个 commit。

staged review 前，VS2022 Release 已重建两个 focused target：CUDA-on 通过 3/3
case、47/47 assertions，CUDA-off 通过 3/3、14/14。完整 runtime-profile
architecture selection 通过 63 项，改动的 Python guard 通过 Ruff check/format。
working write set 不含 runtime 或历史 evidence 文件。

## CR2-4b candidate —— 冻结 selected-payload parity release

### 契约与精确边界

CR2-4b 增加独立 release overlay，不修改 1399 行的历史 parity-budget owner，也
不把 RB8 手工 93 字段 oracle 改称为通过。冻结
`cr2.full_window.fixed_air.v1` profile 只 release 12 个真实公共 DTO value：
`AgentObservation` 的 `sim_time`、`x/y/z`、`vx/vy/vz`、`heading`、`roll`、
`speed`、`gear_state`，以及 `InstrumentState.throttle_pos`。raw inventory 共
66 个标量/计数字段；契约用 static invariant 将其无遗漏、无重叠地分为 12 个
released、1 个 lane-local identity diagnostic 与 53 个带明确原因的 excluded 字段。

`AgentObservation.id` 在 export 时必须等于各 lane 自己的 setup ref；它不要求跨
lane 或 reset 相同，也不进入 digest。canonical identity 是
`(session_index, window_index, world_slot, field_path)`，其中 `world_slot` 在 JSON
中显式保存。每个 lane 在相同 backend/configuration/content 上新建两个 `Runner`
顺序运行，不插入显式 reset shortcut。released projection 不含 excluded DTO
field；comparator 会拒绝额外、缺失、非有限数或标签错误的 payload。

payload 只在 committed window 后的真实公共 export 捕获。`input_injection` 仅由
trace signature 证明；`window_commit` 因没有共同 host-visible payload 而只保留
metadata。CUDA 捕获路径是 host diagnostic export，不属于 CR2-3 measured consumer
path。lane/backend label 与其他 backend provenance 是 outer 或 diagnostic-only
证据，不进入 physical digest。

### 真实 lane 与 reset 证据

重建后的两个 probe 都保留默认 `cuda_resident.full_window_probe.v1` 输出和旧
operation-only comparator；`--parity-release` 才增加 policy-bound 的双 session
投影。冻结 trace signature 的 SHA-256 是
`54c0a905d07bf19212da7fa0dee1baa23599d4f80dc84e38f1f9957c41b28e3c`；
seed/action signature 变化会 hard-fail。

真实两世界、两窗口 CPU/CUDA 比较中，每个 released field 都有四次匹配。最大
absolute difference：`sim_time` 为 `8.94e-10`、`x` 为 `1.689e-4`、`z` 为
`8.12e-6`、`vx` 为 `1.689e-2`、`vz` 为 `8.12e-4`、`speed` 为
`1.689e-2`，均在各字段 absolute/relative budget 内。`y`、`vy`、`heading`、
`roll`、`gear_state`、`throttle_pos` exact。两个 lane 的两次同 backend session
对全部 12 字段都 exact。raw allocator id 在 CPU/CUDA 的四个 reset position 中
均发生变化；该事实只作为 diagnostic 报告，不影响 canonical world-slot identity。

candidate promotion 仍关闭。release JSON 与 comparator 固定
`maintained_claim_allowed=false`、`public_support_enabled=false`、
`measured_consumer_path_unchanged=true`。本迭代不改 RuntimeFacade selection、
admission/support flag、public ABI、历史 RB9 evidence、旧 93 字段 quarantine、
device lease、kernel 或性能阈值。

### 规模与验证证据

CR2-4b owner 全部低于 soft limit：parity release contract 244 行、full-window
contract/runner 118/257 行、probe 337 行、C++ conformance test 417 行、comparator
494 行、architecture guard 239 行。comparator 已纳入机器规模扫描；
`watch_items` 和 hard-limit exception 仍为空。

VS2022 Release 已重建两个真实 probe 和两个 full-window test target。旧 comparator
仍确认九条 operation surface 相等；新 comparator 对 12 个跨 lane field 和两侧
exact reset session 全部通过。CUDA-off full-window doctest 为 6/6 case、136/136
assertions；CUDA-on 为 6/6、153/153。未修改的 replay suite 为 CUDA-off 3/3、
14/14 与 CUDA-on 3/3、47/47；lifecycle 为 CUDA-off 14/14、91/91 与 CUDA-on
14/14、599/599。完整 CUDA-resident runtime-profile architecture selection 为
73 passed、21 deselected；Ruff check/format 与 `git diff --check` 通过。

### 独立复核门

新的独立 agent 必须审阅精确 staged CR2-4b snapshot，包括字段 partition/tolerance、
双 Runner reset 语义、raw-id policy、barrier/provenance 边界、negative test、真实
probe evidence、support/history 不变和全部规模限制。只有 `FINAL APPROVE` 才允许
一个 CR2-4b commit；不授权 merge、push、promotion、CR2-5 tuning 或改写旧 evidence。

## CR2-5a candidate —— 静态资源与实测 launch topology

### 契约与 capture 边界

CR2-5a 增加独立的 `cr2.resource.steady_full_window_body.sm86.v1` profile。CUDA-only
Release probe 在进入唯一 `cudaProfilerApi` range 前 setup 256 个 world，并查询十个
kernel attribute。capture body 恰好是
`inject → evaluate(empty) → advance(WorldBatch) → public export → lease acquire →
consumer submit → event await`。receipt、lease、backend 析构和 resource-query side
effect 都在 range 外；diagnostic materialization 从未调用。

Nsight Systems 2025.3.2 导出的 single-window SQLite trace 恰好包含按 contract 顺序
排列的 12 个 launch instance 和 10 个 unique symbol；每个实例的 grid 为 `2×1×1`，
block 为 `128×1×1`。runtime table 包含 12 次 launch API、5 次 device synchronize、
1 次 event synchronize、1 次 stream wait，以及 3 H2D / 7 D2H / 3 D2D transfer。
七次 D2H 证明 public export 已包含，而 consumer diagnostic 的两次 copy 已排除。
range 内还包含两组 event create/record、四次 allocation 与零次 free；receipt/lease/
backend release 仍在 range 外。

### 静态资源证据与解释

compact JSON 对十个 kernel 的显式 ptxas entry、runtime attribute、cuobjdump resource
与 SASS 做交叉核验。register 依次为 `30/34/66/66/64/64/34/40/16/14`；其中
66/66/64/64-register 的四个 kernel 有 40-byte stack frame，理论 occupancy 为
58.33/58.33/66.67/66.67%，其余六个 zero stack、100% theoretical occupancy。
全部 ptxas entry 显式报告 zero spill store/load。每个 40-byte kernel 含三条
`LDL.64` 与两条 `STL.64`；它们保持 stack/local instruction 语义，不改称 spill。

Nsight Systems 对所有 launch row 报告 zero `localMemoryPerThread` metadata，并在三个
静态源一致报告 consumer 14 registers 时记录 16-register metadata。这些仪器字段会
保留，但不覆盖静态 cross-check，也不是 achieved local traffic。
`-maxrregcount=0` 记录为 no cap。tracked evidence 约 19 KiB。raw `.nsys-rep`
不跟踪，也不是 compact collector input。SQLite/build-log raw bytes 与派生的
cuobjdump resource/SASS output 以 SHA-256 标识；仓库不保留 raw input bytes。

### Gate 状态

static resource 与 launch-topology sub-gate 已完成。achieved occupancy、divergence、
kernel global/local/shared traffic 以 `pending_cr2_5b` 保持 null；整体 CR2-5 counter
gate、tuning、promotion、support 与 maintained claim 均为 false。negative test 会
拒绝 probe payload 额外/缺失、trace drift、ptxas spill field 缺失、launch 顺序或
数量错误、exact-symbol/unique-count drift、冲突 register cap、无效 runtime occupancy
metadata、额外 diagnostic D2H、theoretical-to-achieved substitution 与 support flag 变化。

新 contract/probe/orchestrator/static-parser/architecture-test 模块分别为
93/350/655/116/382 行。没有模块进入 watch band，compact tracked artifact 低于
512 KiB soft cap。

staged review 前，Release resource probe 已在 RTX 3090 上重建并完成；用同一组
untracked 输入重新生成 compact artifact 得到相同 SHA-256。CUDA-on
lifecycle/replay/full-window suite 分别通过 14/14 case、599/599 assertion，3/3、
47/47，以及 6/6、153/153；CUDA-off 对应结果为 14/14、91/91，3/3、14/14，
以及 6/6、136/136。完整 CUDA-resident runtime-profile architecture selection 为
89 passed、21 deselected；focused Ruff check/format 与 `git diff --check` 通过。
构建重复出现 `src/tests/test_main.cpp` 既有的 MSVC C4819 warning；CR2-5a 不修改
该文件。

### 独立复核门

新的独立 agent 必须审阅完整 staged CR2-5a snapshot、profiler range 与 RAII cleanup、
四类 resource source、SQLite topology query、stack/spill 术语、null achieved field、
negative test、历史 evidence 不变及全部规模限制。只有 `FINAL APPROVE` 才允许一个
CR2-5a commit；不授权 merge、push、tuning、promotion，或把 CR2-5b 合入同一 commit。

## CR2-5b candidate —— achieved-counter 权限 blocker

### 真实尝试与 provenance

独立 collector 对未修改的 CR2-5a Release/SM86 resource-probe binary 执行 Nsight
Compute 2025.3.1.0。invocation 使用 application-only target、`cudaProfilerApi` range
control、kernel replay、demangled kernel name、`full` counter set 与 12-launch limit。
collector 对实际 absolute argument vector 记录 SHA-256，对外只保留路径遮蔽的 command
template；同时对 NCU executable、probe binary、attempt log、probe output、CR2-5a 父
evidence、collector 与 contract 做 hash。

NCU 连接一个进程，只报告一个 profiler error，并从同一个进程断开。它以退出码 1
结束，错误为 `ERR_NVGPUCTRPERM`，没有生成 `.ncu-rep`。probe 应用仍完成 256-world、
单-window body，等待 device consumer，并产生与 CR2-5a 冻结值相同的 binary/probe
output hash。因此状态是 `external_blocked`，不是 kernel failure，也不是成功采得零值。

### Counter 与 gate 状态

achieved occupancy、branch divergence 与 kernel global/local/shared-memory traffic 全部
保持 null。required counter-launch count 是 12，取得的 hardware-counter record count
是 0。negative validation 会拒绝 blocked 状态中的零或非空字段、exit-zero/blocker
矛盾、错误或额外 profiler error、虚构 report、部分 launch coverage、缺少 metric name、
theoretical-occupancy provenance、source/hash drift，以及 support、tuning、maintained 或
promotion 状态变化。

外部权限 blocker 已经复现并记录，因此 real-attempt sub-gate 完成；achieved-counter
gate 仍为 false，CR2-5 以 `documented_external_blocker` 收束，不产生 tuning result。
raw log、probe output 与 profiler report 不跟踪。开启 GPU performance counter 是本迭代
范围外的外部 host-policy 操作。

### 规模与验证证据

新增 contract/collector/architecture-test 模块分别为 58/657/255 行，低于对应
600/700/700 软阈值；tracked compact JSON 为 4,555 bytes。聚焦 CR2-5a/5b/size
architecture test 为 34/34；完整 CUDA-resident runtime-profile selection 为 104 passed、
21 deselected；聚焦 Ruff check/format 与 `git diff --check` 通过。既有 CUDA-on
lifecycle/replay/full-window executable 分别通过 14/14 case、599/599 assertion，3/3、
47/47，以及 6/6、153/153；CUDA-off 对应结果为 14/14、91/91，3/3、14/14，以及
6/6、136/136。

### 独立复核门

新的独立 agent 必须审阅精确 staged CR2-5b snapshot，包括真实 invocation/error
provenance、应用完成、NCU report 缺失、CR2-5a binary/probe link、全 null achieved
family、状态矛盾与 available-state negative test、历史 evidence 不变和全部规模限制。
只有 `FINAL APPROVE` 才允许一个 CR2-5b commit；不授权 merge、push、修改 host
permission、tuning、promotion，或在同一 commit 开始 CR2-6。

## CR2-6a candidate —— common-SPI production matrix probe

### Surface 与 matrix contract

CR2-6a 新建 probe，不修改或重新标记历史 RB9 probe/evidence。同一组 probe/session
source 分别编译为 Release CPU 与 CUDA target。两者的 timed common sequence 都通过
`IWorldBatchBackend` 执行
`inject → evaluate(empty) → advance(WorldBatch) → optional public export`。matrix
projection 使用独立 surface ID，并通过 `full_window::kSurfaceId` 权威常量直接引用
完整 full-window surface；不调用 `publish_stage()` 或 private
`export_snapshot()`。optional device lease/consumer suffix
明确是 CUDA-only；CPU device-consumer row 以一个稳定 reason 标记 unavailable，不生成
虚假 timing。

冻结 production matrix 为 `1/4/16/64/256` worlds 乘四种 export/consumer mode；protocol
为 10 个 reset-cold sample、32 个 warmup window、100 个 measured window，以及 10 组
各 64 window 的 rollout。latency family 分开记录 setup、cold total/first window、warmed
end-to-end、common compute、collection 与 rollout total。device-consumer await 位于
suffix timer 内，diagnostic materialization 与 receipt release 位于 sample/rollout timer
之后；schema 会校验 receipt、materialization 与 deferred-rollout count。

same-lane reset correctness 在计时后 export CR2-4b 的 12-field selected payload，检查
lane-local entity identity，从 digest 排除 allocator ID，并要求不同 reset/mode 的 exact
digest 稳定。第一次 CUDA smoke 正确暴露 replay harness 返回的是很长的 canonical trace；
现在 probe 会先把 canonical form 内容寻址为 FNV-1a-64，再输出 row/master signature，
从而限制 report size。report 直接引用 CR2-4b 权威 selected-slice schema、policy 与
source trace profile；这种复用仅限 same-lane reset 的 field projection，并显式保持
matrix profile 未 release。
CPU 显式请求 `worker_threads=0`，表示按各 world count 截断的自动 hardware
concurrency；每个 available row 会记录 effective count。CUDA 记录一个 host
orchestrator，并从 CR2-5a resource-evidence contract 直接别名 128-thread block size，
因此后续比较不能静默改变 host 或 device 并行度。

### 真实构建与 smoke 证据

CUDA-on 与 CUDA-off tree 都已重新配置，并以 Release 构建
`ef_cuda_resident_cr2_matrix_cuda_probe` 和
`ef_cuda_resident_cr2_matrix_cpu_probe`。真实 `--smoke` 覆盖 world 1/4；每个 available
row 使用 1 cold、1 warmup、2 measured 与一组 2-window rollout。两 lane 的 common
master/row trace digest 一致。CUDA 8/8 row available；CPU 有四个 common available row
与四个 device-consumer N/A row。所有 available row 的 same-lane exact reset 通过，两个
raw smoke report 也都通过同一 fail-closed validator。world count 1/4 的 CPU row 分别
记录 1/4 个 effective worker；全部 CUDA row 记录一个 host orchestrator，而 CPU N/A row
的 effective worker count 为 null。未跟踪 CPU/CUDA report 分别为 16,241/26,449 bytes。

CPU probe 在创建任何 session 前把 logging 设为 warning，因此 database/reset info log
不进入 cold/setup measurement。CPU build 重复出现
`src/components/combat/common/missile_seeker_state.h` 既有的 MSVC C4819 warning；
CR2-6a 不修改该文件。

### 规模、negative test 与复核门

新增 contract/session-header/session/probe/validator/architecture-test 模块分别为
107/53/288/475/603/450 行，全部低于 soft target。contract 固化标准 FNV-1a-64
offset/prime 与 empty/`a`/`foobar` known vector；trace 和 selected-payload reset digest
共用这些常量。negative test 会拒绝 private
invocation surface、缺少 empty evaluation、不完整 matrix、CPU consumer availability
或 worker-policy claim、跨 mode effective-worker drift、timing/raw-stat drift、
receipt/deferred-owner drift、trace/reset-digest disagreement、allocator identity
进入 reset scope、重复 JSON key、configuration/mode/row/statistics/
diagnostics/memory/environment/gate 中的 integer/boolean/float JSON 类型别名，以及
warmed/cold timing decomposition drift、master/world-256 trace mismatch、跨 mode
CUDA-memory drift，以及 support/matrix-complete/promotion gate 变化。

聚焦 matrix/size architecture test 为 39/39；完整 CUDA-resident runtime-profile
selection 为 140 passed、21 deselected；Ruff/format 与 `git diff --check` 通过。既有
CUDA-on lifecycle/replay/full-window 仍为 14/14、599/599，3/3、47/47，以及 6/6、
153/153；CUDA-off 仍为 14/14、91/91，3/3、14/14，以及 6/6、136/136。

新的独立 agent 必须审阅精确 staged CR2-6a snapshot、两个真实 smoke report、
common-SPI/timing boundary、compact trace derivation、CPU N/A 语义、receipt ownership、
validator negative coverage、历史 RB9 不变和全部规模限制。只有 `FINAL APPROVE` 才
允许一个 CR2-6a commit；不授权 merge、push、production evidence、selection-policy
claim、tuning、promotion，或在同一 commit 开始 CR2-6b。

## CR2-6b candidate —— order-balanced production evidence 与 selection advisory

### Evidence 边界与 provenance

CR2-6b 不修改 runtime、contract、probe 或 CMake 行为；source commit 是已经独立批准的
CR2-6a commit `0c24a075`。四份未修改 production report 跟踪在
`cuda_resident_cr2_matrix_evidence_20260804/`：campaign 1 为 CPU→CUDA，campaign 2
反向执行，lane 从不重叠。每条 lane 使用冻结的五 world/四 mode production protocol，
并通过 CR2-6a production validator。raw report 分别为 103,773/194,834 与
103,948/194,684 bytes，均低于 1 MiB artifact cap，并由 manifest 内容寻址。

manifest 记录 exact matrix/full-window binary、CR2-6a source owner、validator、
comparator、CR2-5a/5b evidence、host topology、balanced power scheme、report 完成时间、
process duration 与所有 hash。它也记录未固定 affinity、未使用 GPU exclusive mode、
background load 未受控。因此本证据只是 host-specific experimental routing advice，
不是受控 tuning 或 support benchmark。

collector 重新运行真实 CR2-4b full-window comparator；12 个 released field 全部通过
cross-lane budget 与 same-backend exact reset，canonical parity artifact 已跟踪并 hash。
CR2-5a static/topology gate 保持 complete。CR2-5b 仍是已记录的
`ERR_NVGPUCTRPERM` external blocker，collected launch 为 0，achieved counter 为 null，
所以不授权 tuning。

### 派生比较与显式 small-batch policy

共同 mode ratio 定义为 CPU ms/CUDA ms，覆盖两轮 campaign 的 warmed p50/p95 与
rollout-per-window p50/p95。world 1 的两个共同 mode 选择 CPU；world 4 no-export 选择
CUDA。world 4 host-export 为 mixed：CUDA 在两轮都赢得两个 p50，但 rollout p95 随
run order 从 CPU-faster 反转为 CUDA-faster；其保守 default 为 CPU，只为 median
throughput 显式 opt in CUDA。world 16/64/256 的两个共同 mode 选择 CUDA。
device-consumer mode 因 CPU N/A 必须使用 CUDA，不产生比较性能 claim。未测 world count
不外推。

setup/cold family 保留在 raw evidence 中，但不是 routing 输入。10-sample rollout 的
nearest-rank p95 明确视为观测最大值，而不是高样本量 tail estimate。

maintained default 继续为 `flecs_cpu_reference`，不实现 runtime selector。
`cr2_6_matrix_evidence_complete` 与 `cr2_6_selection_advisory_complete` 只在本 evidence
artifact 中为 true。maintained claim、public support、achieved-counter、tuning 与
promotion gate 继续为 false。

### 拆分、验证与复核门

620 行 collector 负责 provenance、fresh parity execution、raw-report validation 与
comparison derivation；450 行 schema 模块负责严格 JSON type、ratio 重算、固定
selection rule、limitation 与 gate；207 行 architecture test 从四份 raw report 重新
派生 tracked comparison，并攻击 policy、ratio、campaign order、blocker 与 gate drift。
三者均低于 700 行 soft target。exact evidence artifact 使用 `-text`，source 与
prior-evidence hash 使用 `utf8_lf` canonicalization；全部 tracked evidence artifact
均低于 1 MiB。

focused matrix-probe/evidence/size test 为 57/57；完整 CUDA-resident runtime-profile
selection 为 158 passed、21 deselected；Ruff check/format 与 `git diff --check` 通过。
既有 CUDA-on lifecycle/replay/full-window 仍为 14/14、599/599，3/3、47/47，以及
6/6、153/153；CUDA-off 仍为 14/14、91/91，3/3、14/14，以及 6/6、136/136。
连续两次 collector run 生成相同 evidence 与 parity hash。

commit 前，新的独立 agent 必须审阅 exact staged snapshot、四份 raw report、manifest、
generated evidence、fresh parity artifact、selection derivation、CR2-5 blocker binding、
documentation 与 size inventory。只有 `FINAL APPROVE` 才允许一个 CR2-6b commit；不授权
merge、push、runtime selection、tuning、promotion，或在同一 commit 开始 CR2-7。

## CR2-7 candidate —— 第二次无晋级 closure

### 机械决策与保留证据

CR2-7 在收口前 HEAD `356bcd56a61e40f1327d16b6a2dda335d7fdd553` 上评估已接受的
CR2-0 至 CR2-6b chain。common-SPI full-window 路径、device-consumer boundary、
12-field parity、static resource/launch topology 与两轮 production matrix 已完成。
achieved-counter gate 未完成：真实 CR2-5b 尝试仍被 `ERR_NVGPUCTRPERM` 外部阻断，
collected launch 为零，全部 achieved family 为 null。不存在显式 promotion 授权或
integration plan。

因此计划内唯一结果是 `closed_without_promotion`。CUDA-resident 实现作为未维护的
研究型第二后端保留。CR2-6b host-specific advisory 原样保留，不转化为 RuntimeFacade
selector、maintained performance contract 或 tuning 权限。不以 theoretical/zero 值
替代 blocked counter，也不外推未测 world count。

### 仓库、写集与恢复边界

最终 pre-commit snapshot 中，原 maintained baseline 与 candidate/main merge base 仍为
`395e02b7dfeaa87baedb2611ec503d14ab137ce3`。maintained `main` 由独立 PR #21 推进至
`a4365cf6`；main 与 candidate 分别有 4 和 24 个独有提交，其中 parent closure
`935926e8` 之后有 12 个线性 CR2 commit。在未 fetch 的本地 remote-tracking ref 范围内，
没有 ref 包含收口前 HEAD。branch、worktree、commit chain、raw report 与 compact
evidence 均保留。可变 ref 与 worktree presence 是有日期的观测，不是永久 architecture pin。

CR2-7 写集仅包括精确 closure JSON、双语 closure pair、双语 plan/log/index 终态、
parent plan index pair、严格 closure validator 与 architecture guard、size inventory
更新，以及 closure JSON 的 `-text` 规则。既有 RB11 closure guard 从可变 live ref
收窄为冻结快照与不可变提交图。runtime、contract、probe、CMake、kernel、launch、
C++ test、support flag 与 public ABI 均不变。不执行 merge、push、删除、清理、权限修改
或 maintained rollback。

### 规模、验证与复核门

新 validator 为 546 行，新 architecture guard 为 232 行，调整后的 RB11 guard 为 143
行；均低于 700 行 soft target 与 1000 行 hard ceiling。CR2-7 不增加大型 raw artifact。
保留的四份 CR2-6b report 合计 597,239 bytes，作为可重新推导证据仍有保留价值；每件
均低于 512 KiB artifact soft cap 与 1 MiB hard cap。

严格 validator 检查 JSON type、exact/canonical descriptor、gate/advisory invariant、
不可变线性提交链、maintained flag 与 evidence-only 写边界。`--check-live-snapshot`
在 acceptance 时单独比对可变本地 ref/worktree；持久 architecture test 不 pin 未来仓库
操作。review 前必须通过 focused closure/size test、完整 CUDA-resident runtime-profile
selection、Ruff/format、diff check，以及已接受的 CUDA-on/off lifecycle/replay/full-window
套件。

focused closure/size test 为 24/24；完整 CUDA-resident runtime-profile selection 为
179 passed、21 deselected；Ruff check/format、严格 JSON 解析、live closure validator
与 `git diff --check` 通过。CUDA-on lifecycle/replay/full-window 保持 14/14、599/599，
3/3、47/47，以及 6/6、153/153；CUDA-off 保持 14/14、91/91，3/3、14/14，以及
6/6、136/136。

新的独立 agent 必须审阅精确 staged CR2-7 snapshot、机器记录、保留证据 hash、blocker
与授权逻辑、selection-advisory 边界、Git topology、maintained flag、双语链接、写集与
全部规模限制。只有 `FINAL APPROVE` 才允许形成一个 CR2-7 closure commit；不授权
merge、push、promotion、tuning、host permission 修改、cleanup，也不允许在本已关闭
program 下继续下一轮 CUDA-resident 迭代。
