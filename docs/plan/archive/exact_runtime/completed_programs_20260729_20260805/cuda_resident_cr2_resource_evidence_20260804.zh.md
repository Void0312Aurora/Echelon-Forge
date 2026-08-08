# CUDA-resident CR2-5a 资源证据（2026-08-04）

## 范围

本记录只覆盖一次 production-shaped full-window body 的静态 kernel 资源与实测
launch/API 拓扑，不包含 Nsight Compute hardware counter，也不授权 tuning、support、
promotion 或 maintained-backend claim。机器可读 artifact 是
`cuda_resident_cr2_resource_evidence_20260804.json`。

CUDA-only Release/SM86 probe 在 `cudaProfilerStart` 前配置并 setup 256 个 fixed-air
world。唯一 capture range 内执行：

`inject → evaluate(empty) → advance(WorldBatch) → public export → acquire
device lease → consumer submit → event await`。

资源查询与对象析构位于 range 外；consumer diagnostic materialization 从未调用。

## 实测拓扑

Nsight Systems 2025.3.2 恰好捕获 12 个 launch instance 与 10 个 unique kernel
symbol。每个 launch 的 grid 都是 `2×1×1`，block 都是 `128×1×1`。顺序为围绕
Phase A/B/D 的三次 barrier、七个 phase kernel（Phase A 一次、Phase B 三次、
Phase D 三次）、observation pack 与 device consumer。

CUDA API/memory table 的实测结果是：

| 事实 | 实测值 |
| --- | ---: |
| kernel launch | 12 |
| `cudaDeviceSynchronize` | 5 |
| capture 内 `cudaMalloc` / `cudaFree` | 4 / 0 |
| event create / record | 2 / 2 |
| `cudaEventSynchronize` | 1 |
| `cudaStreamWaitEvent` | 1 |
| `cudaMemset` / `cudaMemcpy` | 5 / 13 |
| H2D copy / bytes | 3 / 14,080 |
| D2H copy / bytes | 7 / 229,908 |
| D2D copy / bytes | 3 / 677,376 |

七次 D2H 是五次既有 barrier-status transfer 与两次 public export transfer；两次
consumer diagnostic readback 不在 capture 中。CUDA memcpy bytes 是 API transfer
证据，不是 kernel global-memory achieved traffic。

## 静态资源

collector 对每个 kernel 交叉核验 ptxas、runtime attribute 与 cuobjdump。十个 ptxas
entry 都显式报告 zero spill store 和 zero spill load。构建参数
`-maxrregcount=0` 表示不设置 register cap。

| Kernel | Registers | 每线程 stack bytes | 理论 occupancy | SASS LDL / STL |
| --- | ---: | ---: | ---: | ---: |
| apply barrier | 30 | 0 | 100% | 0 / 0 |
| Phase A controls | 34 | 0 | 100% | 0 / 0 |
| Phase B forces | 66 | 40 | 58.33% | 3 / 2 |
| Phase B aerodynamics | 66 | 40 | 58.33% | 3 / 2 |
| Phase B integrate | 64 | 40 | 66.67% | 3 / 2 |
| Phase D instruments | 64 | 40 | 66.67% | 3 / 2 |
| Phase D configuration | 34 | 0 | 100% | 0 / 0 |
| Phase D projection | 40 | 0 | 100% | 0 / 0 |
| Phase D pack | 16 | 0 | 100% | 0 / 0 |
| Phase D consumer | 14 | 0 | 100% | 0 / 0 |

四个 40-byte stack kernel 各自含三条 `LDL.64` 与两条 `STL.64`。这些是 stack/local
operation，不能改称 compiler spill。Nsight Systems 对所有 launch 的
`localMemoryPerThread` metadata 都报告零；该字段会原样保留，但既不覆盖静态 stack
size，也不作为 achieved traffic counter。它还对 consumer launch 报告 16 registers，
而 ptxas、runtime attribute 与 cuobjdump 一致报告 14；launch metadata 被保留，但不
覆盖三源一致的静态结果。

## Fail-closed 状态

achieved occupancy、divergence 与 kernel global/local/shared traffic 全部保持 null，
状态为 `pending_cr2_5b`。collector 会拒绝 kernel 或 ptxas 字段缺失、资源源不一致、
launch 顺序/数量/shape 错误、distinct-symbol drift、冲突 register cap、无效 runtime
occupancy metadata、第二个 window、额外 diagnostic D2H、support flag 变为 true，
或把 theoretical value 填入 achieved-counter field。单独的 Nsight Compute 尝试与
外部 blocker 记录属于 CR2-5b。

source-file SHA-256 明确采用 UTF-8/LF canonical form，因此 Windows checkout 的
换行转换不会改变 provenance guard。binary、probe output、SQLite 与 build-log hash
仍按 raw bytes 计算。
