# CR2-3 Device Consumer Lease 验收候选

日期：2026-08-01
分支：`codex/cuda-resident-runtime-program-2`
父提交：`607c1f33`

## 技术结论

有边界的 CR2-3 工程 gate 已通过。CUDA-resident backend 现在提供自有的、
learner-facing device observation lease 与真实 device consumer smoke kernel。
consumer validation D2H 位于全部已记录 sample timer 之外。这不等于 learner update
已实现，也不构成性能晋级或 public support release。

## 验收边界

- Lease：自有 D2D observation values/ids、ready event、device/default-stream identity、
  element-based shape/stride/dtype 与 allocation/reset/window/source epoch。
- Receipt：独立拥有 output/event，并持有 input lease。
- Measured work：acquire、submit 与显式 event await；consumer-validation 增量 D2H 为 0。
- Diagnostic work：sample timer 后恰好两次 D2H；rollout receipt 延迟处理，并计入
  requested-memory peak。
- Release：in-flight RAII 可能等待 event，因此 release 延迟到所有 sample timer 之外。
- Failure：稳定 code；一次性测试覆盖 allocation、launch、event、wait、materialize、
  stale epoch、device、stream 与 layout error。
- Lifetime：lease 跨 reset/backend destruction，receipt 跨 consumer destruction；
  支持重复 submit/await。

## 证据

- CUDA Release：RTX 3090 上 14/14 case、599/599 assertions。
- CUDA-off Release：14/14 case、91/91 assertions。
- 两世界 RB9 smoke：4/4 row available；device row 报告 consumer D2H 0、diagnostic
  D2H 2、event wait 1、allocation-sync risk true、deferred receipt 2，peak bytes
  包含两个 owner。
- 聚焦 architecture：25/25；new guard 已 Ruff format/check。
- 规模：全部 CR2-3 implementation/test module 低于 700 行 soft target（contract
  209、consumer 246/49、host-internal/lease 33/66、observation CUDA 441、C++
  test 292、architecture guard 197、RB9 probe/session/header 597/304/46、store
  661、backend 636；header 低于 600 行）；没有新增 exception。

## 保持关闭的边界

`IWorldBatchBackend`、RuntimeCapabilities、admission、support flag 与 RuntimeFacade
selection 未改；历史 RB9 evidence 未动。`cudaMalloc` 可能隐式同步，作为 CR2-5
risk 明确保留；in-flight release 也可能等待完成，并明确位于 measured path 之外。
完整 learner update、parity release、hardware counter、tuning、merge、
push 与 promotion 均未验收。

candidate 在形成唯一 CR2-3 commit 前，仍需最终独立 staged-write-set 批准。
