# CUDA 驻留运行时第二期计划

语言版本：

- 英文规范版：[cuda_resident_runtime_program_2_20260731.md](cuda_resident_runtime_program_2_20260731.md)
- 中文伴随版：`cuda_resident_runtime_program_2_20260731.zh.md`
- 规模策略：[cuda_resident_runtime_program_2_size_policy_20260731.json](cuda_resident_runtime_program_2_size_policy_20260731.json)
- 迭代账本：[cuda_resident_runtime_program_2_iteration_log_20260731.zh.md](cuda_resident_runtime_program_2_iteration_log_20260731.zh.md)

- 文档类型：RB11 closure 之后的新显式 continuation program
- 分支：`codex/cuda-resident-runtime-program-2`
- 父级 closure：`935926e83b18187c79a6e0be2ca010276c1a6fc4`
- maintained baseline：`395e02b7dfeaa87baedb2611ec503d14ab137ce3`
- 日期：`2026-07-31`

状态：**CR2-4a 已获独立批准并以 d778c67c 提交；CR2-4b 是当前 active 的
selected-payload parity candidate。前一套
RB0-RB11 计划仍保持无晋级关闭。本计划可能产出可晋级证据，也可能再次 closure；
它不会自行重新开放 maintained support。**

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
| CR2-2p | 只用 portable bit scan、预期的全局 environment-model type 与 MSVC core 数学常量 opt-in，解除真实 Flecs CPU lane 在 VS2022 的阻塞。 | 真实 `FlecsCpuBackend` 图可编译；聚焦 guard 通过；独立复核与单独 commit 必须先于 CR2-2b。 |
| CR2-2b | 定义一套 full-window trace 与等价 CPU/CUDA invocation surface，覆盖 setup、input、evaluation、advance、export、error/barrier。 | 已独立批准并以 `607c1f33` 提交；两个真实 lane 通过声明的共同 surface 消费同一 trace。 |
| CR2-3 | 增加真实 device consumer/learner-facing lease，移除 measured consumer path 的 hidden host validation。 | 已独立批准并以 `7da41a2a` 提交；显式 consumer smoke、ownership/lifetime/failure、延迟 diagnostic readback 与 CUDA-on/off 验证通过，public support 保持关闭。 |
| CR2-4a | 将 919 行 RB8 replay test 拆为受限 support/projection/test owner，不改变 oracle、quarantine、93-field budget 或历史 evidence。 | 已获独立批准并以 `d778c67c` 提交；CUDA-on/off replay 与 architecture guard 通过，当前无 watch item。 |
| CR2-4b | 基于真实 payload evidence 与显式 identity policy，将 selected-slice parity 与 deterministic reset identity 从 quarantine 中 release。 | 每个 released field 都是真实数据或显式 normalized/excluded；每个声明 barrier 的 frozen-budget replay 通过；public support 保持关闭。 |
| CR2-5 | 为 full window 采集 ptxas/Nsight resource evidence：register、spill、local/shared/global traffic、occupancy、divergence、launch topology。 | counters 完整或记录外部 blocker 并停止 gate；不以不完整 counters 声称 tuning 成功。 |
| CR2-6 | 运行 production-shaped world-count/mode matrix，包含 rollout 与 small-batch。 | cold、warm、rollout、export、device-consumer、small-batch 均支持端到端决策。 |
| CR2-7 | 独立作 promotion 或 closure 决策。 | promotion 需要新授权与 integration plan；否则记录第二次 closure，维护行为不变。 |

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

## 5. 晋级与恢复边界

只要 invocation surface 不等价、真实 learner update loop 缺失、parity 仍是
diagnostic、required counters 缺失、world-1 或声明的 small-batch 回归没有明确
策略，或需要第二套 public facade/重复 DTO，promotion 就保持关闭。

整个 CR2 期间保留 branch 与 worktree，不 merge、push 或删除。未来 cleanup 必须
重新审计 refs/worktree，并取得用户明确授权。
