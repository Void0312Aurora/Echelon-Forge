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

状态：**CR2-1 implementation 已获独立批准；单一 commit 待完成。前一套
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
| `cuda_world_store_cuda_observation.cu` | observation pack 与 consumer | 174 |
| `cuda_world_store_cuda_state_readback.cu` | host state readback | 271 |
| `cuda_world_store_cuda_window.cu` | private full-window orchestration | 69 |

当前 CR2-owned CUDA 模块全部低于 700 行 soft target。旧单体只作为历史 baseline
保留，不是当前 source，也不是活动中的 exception。

以下文件是 watch item；在拆分或显式重新分类前不得继续增长：

- `src/tests/test_cuda_resident_replay.cpp`：919 行；
- `src/tools/experimental/cuda_resident/cuda_resident_rb9_probe.cpp`：804 行。

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
| CR2-1 | 在不改变语义下按 layout/allocation、Phase A、Phase B、Phase D、barrier、device API orchestration 拆分 `cuda_world_store_cuda.cu`。 | 已由 `/root/cr2_split_review` 独立批准；CR2-owned module 不超过 1000 行；聚焦 C++/CUDA lifecycle、replay、parity 与 architecture 测试通过；还需一个 commit。 |
| CR2-2 | 定义一套 full-window trace 与等价 CPU/CUDA invocation surface，覆盖 setup、input、evaluation、advance、export、error/barrier。 | 两侧消费同一 trace；private-only performance invocation 不再是唯一证据路径。 |
| CR2-3 | 增加真实 device consumer/learner-facing lease，移除 measured path 的 hidden host validation。 | consumer smoke 成为显式 contract；ownership/lifetime/failure 有测试；不晋级 public support。 |
| CR2-4 | 将 selected-slice parity 与 deterministic reset identity 从 quarantine 中 release。 | identity policy 稳定或明确排除；每个声明 barrier 上的 frozen budget replay 通过。 |
| CR2-5 | 为 full window 采集 ptxas/Nsight resource evidence：register、spill、local/shared/global traffic、occupancy、divergence、launch topology。 | counters 完整或记录外部 blocker 并停止 gate；不以不完整 counters 声称 tuning 成功。 |
| CR2-6 | 运行 production-shaped world-count/mode matrix，包含 rollout 与 small-batch。 | cold、warm、rollout、export、device-consumer、small-batch 均支持端到端决策。 |
| CR2-7 | 独立作 promotion 或 closure 决策。 | promotion 需要新授权与 integration plan；否则记录第二次 closure，维护行为不变。 |

CR2-1 至 CR2-6 可以拆成窄范围 sub-iteration，但单个 commit 不得把结构拆分、
语义扩展与性能 tuning 合并。

## 5. 晋级与恢复边界

只要 invocation surface 不等价、learner/device consumption 缺失、parity 仍是
diagnostic、required counters 缺失、world-1 或声明的 small-batch 回归没有明确
策略，或需要第二套 public facade/重复 DTO，promotion 就保持关闭。

整个 CR2 期间保留 branch 与 worktree，不 merge、push 或删除。未来 cleanup 必须
重新审计 refs/worktree，并取得用户明确授权。
