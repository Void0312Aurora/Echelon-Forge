# CUDA 驻留运行时第二期计划

语言版本：

- 英文规范版：[cuda_resident_runtime_program_2_20260731.md](cuda_resident_runtime_program_2_20260731.md)
- 中文伴随版：`cuda_resident_runtime_program_2_20260731.zh.md`
- 规模策略：[cuda_resident_runtime_program_2_size_policy_20260731.json](cuda_resident_runtime_program_2_size_policy_20260731.json)
- 迭代账本：[cuda_resident_runtime_program_2_iteration_log_20260731.zh.md](cuda_resident_runtime_program_2_iteration_log_20260731.zh.md)
- CR2-6b 证据：[cuda_resident_cr2_matrix_evidence_20260804.zh.md](cuda_resident_cr2_matrix_evidence_20260804.zh.md)
- CR2-7 closure：[cuda_resident_cr2_closure_20260805.zh.md](cuda_resident_cr2_closure_20260805.zh.md)

- 文档类型：RB11 closure 之后的新显式 continuation program
- 分支：`codex/cuda-resident-runtime-program-2`
- 父级 closure：`935926e83b18187c79a6e0be2ca010276c1a6fc4`
- maintained baseline：`395e02b7dfeaa87baedb2611ec503d14ab137ce3`
- 日期：`2026-07-31`
- closure 日期：`2026-08-05`

状态：**CR2-0 至 CR2-6b 均已独立批准并提交。CR2-7 在包含 closure record 的
commit 中将 Runtime Program 2 无晋级关闭。CUDA-resident 第二后端及证据作为未维护的
研究 candidate 保留；maintained support 继续关闭。**

## 1. 目标与边界

目标是在保持“第二后端、设备原生状态与独立调度”架构的前提下，把分支内
CUDA 驻留实验推进到可度量的 facade-equivalent candidate。它不是把 Flecs
system 逐一改写成 CUDA helper。

计划必须依次证明：

1. resident 实现可以拆成可审阅模块；
2. CPU 与 CUDA 通过等价 invocation surface 执行同一套 full-window contract；
3. learner/device consumer 可以消费结果，measured path 没有 hidden host validation readback；
4. selected-slice parity 与 reset identity 可以 release，而不只是 diagnostic quarantine；
5. 对真实端到端 window 有 registers、spill、occupancy、memory、divergence 证据；
6. 性能决策包含 small batch 与 rollout cost，而不是只看孤立 kernel 或 private phase sequence。

在所有 gate 通过前，maintained CPU 继续是 default，resident support flags 继续为
false，RuntimeFacade 不选择本分支。即使 gate 通过，也只能授权另一个独立的
promotion proposal，不能静默 merge 或 publish。

## 2. 规模治理（强制）

物理行数以 checkout 后的 tracked bytes 为准，用 `splitlines()` 计数；不得通过
压缩代码或把多条语句挤在一行来规避。策略由机器记录保存，并由
`test_cuda_resident_program_2_size_policy.py` 守卫。

| 范围 | soft target | review band | hard limit |
| --- | ---: | ---: | ---: |
| `.cpp`、`.cc`、`.cu`、`.cxx` implementation module | 700 行 | 800 行 | 1000 行 |
| `.h`、`.hpp`、`.cuh` contract/header module | 600 行 | 800 行 | 1000 行 |
| CUDA-resident test/probe module | 700 行 | 800 行 | 1000 行 |

1000 行是 CR2-owned module 的硬上限，不是目标。超过 soft target 必须在账本中
记录拆分决定；进入 review band 后禁止继续添加无关语义。已经超过硬上限的模块
只能以带期限的显式 migration exception 存在，并必须成为第一项结构性工作。

CR2-0 记录过一个 2528 行单体 `cuda_world_store_cuda.cu` 的硬上限迁移例外。
CR2-1 已从当前树移除该文件，不再延续例外。当前 CUDA implementation inventory
如下：

| 模块 | 作用 | 行数 |
| --- | --- | ---: |
| `cuda_world_store_cuda_internal.cuh` | shared layout、allocation 与 wrapper contract | 291 |
| `cuda_world_store_cuda_math.cuh` | shared device math helpers | 139 |
| `cuda_world_store_cuda_storage.cu` | allocation/layout、metadata 与 fixture storage | 547 |
| `cuda_world_store_cuda_barrier.cu` | barrier kernel 与 resource query | 264 |
| `cuda_world_store_cuda_phase_a.cu` | Phase A kernel 与 publication | 204 |
| `cuda_world_store_cuda_phase_b.cu` | Phase B kernels 与 launch wrappers | 497 |
| `cuda_world_store_cuda_phase_d.cu` | Phase D kernels 与 launch wrappers | 231 |
| `cuda_world_store_cuda_observation.cu` | diagnostic 与 CR2-3 lease pack/consumer | 441 |
| `cuda_world_store_cuda_state_readback.cu` | host state readback | 271 |
| `cuda_world_store_cuda_window.cu` | private full-window orchestration | 69 |

当前 CR2-owned CUDA 模块全部低于 700 行 soft target。旧单体只作为历史 baseline
保留，不是当前 source，也不是活动中的 exception。

CR2-3 将 host/device lease 边界拆在小型 owner 中：
`cuda_resident_device_consumer.cpp/.h` 为 246/49 行，
`cuda_world_store_device_lease.cpp` 为 66 行，
`cuda_world_store_host_internal.h` 为 33 行。已有 host owner 仍低于 soft target：
`cuda_world_store.cpp` 661 行，`cuda_resident_backend.cpp` 636 行；没有新增规模例外。

CR2-4a 将 replay test 做零语义拆分，移除原 watch item：
`test_cuda_resident_replay_projection.cpp` 611 行、
`test_cuda_resident_replay_support.cpp` 175 行、
`test_cuda_resident_replay_support.h` 58 行，断言/test owner
`test_cuda_resident_replay.cpp` 139 行。当前不再有 CR2 watch item。

CR2-4b 的语义 owner 也都低于 soft target：parity release contract 244 行、
full-window contract/runner 118/257 行、opt-in probe 337 行、C++ conformance
test 417 行、comparator 494 行、architecture guard 239 行。comparator 已纳入
机器规模扫描；没有新增 exception 或 watch item。

generated/vendor 文件与历史文档只有在 manifest 明确记录 provenance 时才可排除模块
行数限制。新 tracked evidence/report/generated artifact 的 soft limit 为 512 KiB，
hard limit 为 1 MiB；重复的 raw trace 不得进入 tracked write set。例外不能用来
隐藏 implementation 语义增长。CR2 evidence/report/generated 文件必须使用声明的
`cuda_resident_runtime_program_2_` 或 `cuda_resident_cr2_` 前缀；guard 会在 staging
前同时扫描 tracked 文件与 worktree 中的 candidate 文件。

## 3. 工程不变量

- admitted window 内由 backend 持有 resident state；不逐阶段写回 Flecs，不在 CUDA window 内 CPU fallback；
- 边界复用 public DTO 与 RuntimeFacade contract；private SoA 可以在显式 export/consumer lease 后保持 device-owned；
- 每个迭代只有一个 bounded semantic scope、精确 write set、聚焦验证、独立 reviewer 与一个 commit；
- final decision gate 之前 runtime/support/ABI 变化继续 fail-closed；
- `--maxrregcount` 不是 layout 或 scheduling 修复的替代品；tuning 必须基于资源证据并保持 frozen trace；
- RB9 证据只是 provenance，不是 promotion result；CR2 必须补齐缺失 gate，不能给旧 private threshold 改名。

## 4. 迭代队列

| ID | 范围 | 退出门 |
| --- | --- | --- |
| CR2-0 | 冻结本计划、size policy、exception manifest 与 architecture guard。 | 已在 `2f34fac6` 完成；policy 可解析且复核过的 write set 已提交。 |
| CR2-1 | 在不改变语义下按 layout/allocation、Phase A、Phase B、Phase D、barrier、device API orchestration 拆分 `cuda_world_store_cuda.cu`。 | 已由 `/root/cr2_split_review` 独立批准并以 `db7e6ad4` 提交；CR2-owned module 不超过 1000 行；聚焦 C++/CUDA lifecycle、replay、parity 与 architecture 测试通过。 |
| CR2-2a | 在不改变 invocation surface、JSON schema、错误文本和 phase 顺序的前提下，将 RB9 probe 的 lane-specific session 移到独立实现模块。 | 独立批准后已以 `bf695071` 完成；probe/session 均低于 soft limit，历史 evidence 未改。 |
| CR2-2p | 只用 portable bit scan、预期的全局 environment-model type 与 MSVC core 数学常量 opt-in，解除真实 Flecs CPU lane 在 VS2022 的阻塞。 | 已独立批准并以 `dee02146` 提交；真实 `FlecsCpuBackend` 图可在 VS2022 编译。 |
| CR2-2b | 定义一套 full-window trace 与等价 CPU/CUDA invocation surface，覆盖 setup、input、evaluation、advance、export、error/barrier。 | 已独立批准并以 `607c1f33` 提交；两个真实 lane 通过声明的共同 surface 消费同一 trace。 |
| CR2-3 | 增加真实 device consumer/learner-facing lease，移除 measured consumer path 的 hidden host validation。 | 已独立批准并以 `7da41a2a` 提交；显式 consumer smoke、ownership/lifetime/failure、延迟 diagnostic readback 与 CUDA-on/off 验证通过，public support 保持关闭。 |
| CR2-4a | 将 919 行 RB8 replay test 拆为受限 support/projection/test owner，不改变 oracle、quarantine、93-field budget 或历史 evidence。 | 已获独立批准并以 `d778c67c` 提交；CUDA-on/off replay 与 architecture guard 通过，当前无 watch item。 |
| CR2-4b | 基于真实 payload evidence 与显式 identity policy，将 selected-slice parity 与 deterministic reset identity 从 quarantine 中 release。 | 已独立批准并以 `08b48f29` 提交；真实 12 字段投影与同 backend exact reset 通过，public support 仍关闭。 |
| CR2-5 | 为 full window 采集 ptxas/Nsight resource evidence：register、spill、local/shared/global traffic、occupancy、divergence、launch topology。 | CR2-5a/5b 已独立批准并以 `6d7ec7dd`、`05b05c5a` 提交；静态/拓扑证据完整，achieved counter 以已记录的 `ERR_NVGPUCTRPERM` 收口，不产生 tuning 结论。 |
| CR2-6 | 运行 production-shaped world-count/mode matrix，包含 rollout 与 small-batch。 | CR2-6a/6b 已独立批准并以 `0c24a075`、`356bcd56` 提交；保留两轮 order-balanced campaign、fresh parity 与 host-specific fail-closed advisory。 |
| CR2-7 | 独立作 promotion 或 closure 决策。 | 在包含 `cuda_resident_cr2_closure_20260805.json` 的 commit 中无晋级关闭；maintained 行为不变，未来工作需要新显式计划。 |

CR2-1 至 CR2-6 可以拆成窄范围 sub-iteration，但单个 commit 不得把结构拆分、
语义扩展与性能 tuning 合并。

### CR2-2a 边界

CR2-2a 只做结构迁移。可执行文件仍是历史 RB9 probe；CPU/CUDA lane 选择、
mode matrix、private phase sequence、JSON key、trace signature、unavailable reason
与 hold reason 全部冻结。只将 lane-specific ProbeSession 的状态与操作实现移至
cuda_resident_rb9_probe_session.cpp，通过小型 header 暴露；两个 CMake target
都编译该模块。本 sub-iteration 不引入 full-window SPI、public facade、support flag、
learner contract 或新的性能结论。

### CR2-2p 边界

CR2-2p 只做前置 portability repair：替换一个 GCC-only bit intrinsic，恢复预期的
全局 `IEnvironmentModel` type boundary，并让 `ef_core` 在 MSVC 下启用既有 `M_PI`
定义。它有自己的 architecture guard 和 `dee02146` commit，不包含 full-window
runner 或 resident 语义变化。

### CR2-2b 边界

CR2-2b 是第一个 full-window 语义 slice。唯一统一 surface 仍是现有
`IWorldBatchBackend`；同步 runner 固定执行
`setup → inject → evaluate(empty) → advance(WorldBatch) → export`。CPU database
load 在 runner 外部完成。CUDA `advance` 在显式三态 window machine 后方完成 stage
publish 与 commit，runner 只报告共同的 input/window/export barrier。失败会 poison
runner，不增加 retry、fallback、device pointer、learner lease、support flag 或
facade selection。两个真实 lane 编译同一 trace source，独立 comparator 检查纯 JSON
的 surface/trace/operation 相等性。

### CR2-3 边界

CR2-3 增加 private `cuda_resident.device_observation_lease.v1` 输入和真实
`cuda_resident.device_consumer_smoke.v1` kernel submit。lease 自有 D2D-packed
values、ids、ready event、device/default-stream identity、以 element 为单位的 tensor
shape/stride，以及 allocation/reset/committed-window/source epoch。receipt 持有输入
lease，直到自身 event 与 output buffer 被释放。允许重复 submit/await；保留的 lease
在 reset 乃至 backend 销毁后仍可读取。backend/store 仍是 single-owner runtime
对象，lease/receipt 的 shared ownership 则显式声明。

计时中的 consumer path 是 acquire → submit → event await。它不做 consumer-validation
D2H，也不调用 `state_snapshot()` 或读取 device global version。diagnostic
materialization 恰好执行两次 D2H，而且只在对应 cold、warm 或 rollout timer 记录后
发生。rollout 会把本 sample 的全部 receipt diagnostic 延迟到 timer 关闭之后，因此
reported peak requested bytes 按 `rollout_windows` 个 lease/output owner 计。一般 window
仍包含既有的五次 barrier-status D2H；选择 host export 时为七次。因此“0”字段只描述
device-consumer 增量路径，不代表整个 window 没有 D2H。`cudaMalloc` 可能隐式同步，
in-flight RAII release 也可能等待 event；allocation risk 与
`device_consumer_release_outside_measured_path = true` 都显式报告。该问题留给
CR2-5 证据与 tuning，不伪装成 zero-sync。

稳定 failure 覆盖 invalid request/lease/receipt、缺少 committed window、epoch/device/
stream/layout mismatch、lease allocation/pack/event record、consumer allocation/launch/
event record、wait 与 diagnostic materialize。该 seam 仍是 backend-private：CR2-3
不改 `IWorldBatchBackend`、RuntimeCapabilities、admission、support flag 或
RuntimeFacade selection。历史 RB9 evidence 目录不重写，也不声称 learner update、
performance promotion 或 tuning 已完成。

### CR2-4b 边界

CR2-4b 只 release `cr2.full_window.fixed_air.v1` 的冻结 12 字段公共 DTO
投影：11 个 `AgentObservation` 标量和 `InstrumentState.throttle_pos`。它不把旧
RB8 手工 93 字段 oracle 或 RB9 evidence 改称为通过。其余 53 个 raw 标量/计数
字段逐一声明排除原因；`AgentObservation.id` 保留为 lane-local allocator 诊断。
跨 lane 身份键是
`(session_index, window_index, world_slot, field_path)`；raw allocator id 会与各
lane 的 setup ref 做本地一致性检查，但不进入 parity/reset digest。

每个真实 lane 在同一个未替换 backend 上，顺序构造两个新的 full-window
`Runner` 并运行同一冻结 trace。跨 lane 比较采用逐字段 absolute/relative
tolerance，要求有限数并规范化 signed zero；同 backend reset 对 12 个 released
value 要求 exact。payload 只在 `window_commit` 后通过 host diagnostic export
捕获；`input_injection` 只由 trace 证明，`window_commit` 只提供 metadata。该捕获
既不修改也不计入 CR2-3 measured device-consumer path。

此 release 仍只是 candidate evidence：`candidate_promotion_blocked=true`，
`maintained_claim_allowed=false`，`public_support_enabled=false`。本迭代不改
RuntimeFacade selection、admission、public ABI、旧 93 字段 budget、历史 evidence、
性能阈值或 kernel 调度。

### CR2-5a 边界

CR2-5a 增加 CUDA-only `cudaProfilerApi` probe，只捕获一次 256-world、单 window、
Release/SM86 body。setup、运行时资源查询与 owner 析构都在 capture range 外；range
内只有 `inject → evaluate(empty) → advance(WorldBatch) → public export → device
lease acquire → consumer submit → event await`，不调用 diagnostic materialization。
因此 Nsight Systems SQLite 必须恰好包含按声明顺序排列的 12 个 launch instance、
10 个 unique kernel symbol；每个实例的 grid 为 `2×1×1`、block 为 `128×1×1`；
并实测 5 次 `cudaDeviceSynchronize`、1 次 event synchronize、1 次 stream event
wait，以及 3 H2D / 7 D2H / 3 D2D copy。
同时冻结两组 event create/record、四次 range 内 allocation 与零次 range 内 free；
owner release 仍位于 capture body 外。

compact resource artifact 会交叉校验显式 ptxas record、运行时
`cudaFuncGetAttributes`/occupancy query、cubin resource usage 与 SASS。40-byte stack
frame 及其 `LDL`/`STL` 指令与 compiler-reported spill 是不同事实。Nsight Systems
launch metadata 会保留为仪器输出，但其中为零的 local-memory 字段既不是 achieved
local traffic，也不能抹除 40-byte 静态结果。同理，`-maxrregcount=0` 明确解释为
no cap，而不是 zero-register cap。raw `.nsys-rep` 不跟踪，也不是 compact collector
input。SQLite/build-log raw bytes 与派生的 cuobjdump resource/SASS output 以 SHA-256
标识；仓库保留 collector 与 compact facts，不保留 raw input。

CR2-5a 不采集 achieved occupancy、divergence 或 kernel global/local/shared traffic；
这些字段以 `pending_cr2_5b` 状态保持 null，tuning、promotion、public support 与
maintained claim 全部为 false。CR2-5b 必须单独真实运行 Nsight Compute：要么提供
完整 counters，要么记录外部 blocker，不能用 theoretical value 替代。

### CR2-5b 边界

CR2-5b 通过 fail-closed collector，对未修改的 CR2-5a Release/SM86 binary 与 profile
运行这次独立尝试。实际 Nsight Compute 2025.3.1.0 运行完成了应用 body，但以退出码 1
结束，唯一 error 是 `ERR_NVGPUCTRPERM`，并且没有生成 counter report。因此 achieved
occupancy、divergence 与 global/local/shared traffic family 继续保持 null；零代表
取得的 counter record 数量，而不是伪造的零值 measurement。

真实尝试 sub-gate 以 documented external blocker 完成，但 achieved-counter gate 仍未
完成。CR2-5 的 disposition 是 `documented_external_blocker`，不是 tuning result。
compact artifact 对实际 invocation、profiler、binary、log、probe output、父证据、
collector 与 contract 做 hash；raw profiler file 不跟踪。本迭代不修改 kernel、runtime
selection、tuning、support、maintained 或 promotion 状态。

### CR2-6a 边界

CR2-6a 新建 production-matrix probe，不修改或重新标记历史 RB9 probe/evidence。同一组
source 分别编译为 Flecs CPU reference 与 CUDA-resident lane；两者都执行当前 backend
SPI sequence：`inject → evaluate(empty) → advance(WorldBatch) → optional public
export`。optional device lease/consumer suffix 明确是 CUDA-only，对应 CPU row 保持 N/A。

冻结矩阵为 world count `1/4/16/64/256`，覆盖 no-export/export 与
no-device/device-consumer mode。production protocol 包含 10 个 reset-cold sample、32 个
warmup window、100 个 measured window，以及 10 组各 64 window 的 rollout。consumer
await 位于 measured suffix 内，diagnostic materialization 与 receipt release 位于 timer
外。same-lane reset correctness 对 CR2-4b release 的 12 个 numeric field 做 hash，排除
allocator identity；trace payload 在写入 JSON 前压缩为 FNV-1a-64 digest。schema、
policy 与 source-profile ref 直接绑定 CR2-4b 权威契约，同时用显式 field-projection-only
disposition 保持 matrix profile 未 release。
report 还冻结 CPU `worker_threads=0` 为按 world count 截断的自动 hardware
concurrency，并逐 row 记录 effective count；它与 CUDA lane 的单 host orchestrator 加
CR2-5a 权威 128-thread device block 明确区分。

CR2-6a 只负责 probe、schema validator、真实 CPU/CUDA smoke 与 fail-closed gate，不提交
production timing、不选择 threshold，也不声称性能结论。CR2-6b 必须以完整 protocol
运行两个 Release binary，对 raw report 做内容寻址，只比较共同 available mode，将
CUDA-only consumer row 分开处理，并形成显式 small-batch selection policy。counter、
support、maintained、tuning 与 promotion gate 继续为 false。

### CR2-6b 边界

CR2-6b 跟踪两轮顺序平衡且不重叠 campaign 的四份未修改 production report，并重算
统计与 policy。world 1 采用 CPU reference；world 4 无 export 采用 CUDA；world 4 有
host export 时因 rollout p95 在两轮间反转而保守默认 CPU；world 16/64/256 的共同 mode
采用 CUDA。device-consumer mode 仅 CUDA 可用，不作 CPU 比较。advisory 只适用于五个
已测 world count，并保持 host-specific，不成为 runtime selector。fresh 12-field parity
通过，但 achieved counter、tuning、support、maintained 与 promotion gate 继续为 false。

### CR2-7 终态边界

CR2-7 是 evidence-only closure。achieved-counter gate 仍被 `ERR_NVGPUCTRPERM` 阻断，
且不存在显式 promotion 授权或 integration plan。因此机器记录为
`closed_without_promotion`；不修改 runtime、contract、probe、CMake、kernel、launch、
C++ test、support flag 或 public ABI。branch、worktree、12-commit CR2 chain 与全部证据
继续可恢复。重新开启工作必须建立新的显式计划并取得用户授权。

## 5. 晋级与恢复边界

只要 invocation surface 不等价、真实 learner update loop 缺失、parity 仍是
diagnostic、required counters 缺失、world-1 或声明的 small-batch 回归没有明确
策略，或需要第二套 public facade/重复 DTO，promotion 就保持关闭。

整个 CR2 期间保留 branch 与 worktree，不 merge、push 或删除。未来 cleanup 必须
重新审计 refs/worktree，并取得用户明确授权。
