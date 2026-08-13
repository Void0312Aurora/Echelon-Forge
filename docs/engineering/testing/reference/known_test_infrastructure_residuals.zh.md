# 已知测试基础设施残差

语言：
- 英文规范版：[known_test_infrastructure_residuals.md](known_test_infrastructure_residuals.md)
- 中文伴随版：`known_test_infrastructure_residuals.zh.md`

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/engineering/testing/reference/known_test_infrastructure_residuals.md`
Owner: `engineering/testing`
Last verified: `2026-08-08`
Content status: 从已完成 T6 账本抽取的当前所有者本地索引；条目描述验证限制，
不代表产品接受状态。

## 验证边界

本文只保留归档账本中的测试工具、依赖快照和合约运行器限制。产品校准归
`systems/effects`，C++ 依赖决策归 `architecture`。

## 当前残差

- 当本地构建只有依赖构建目录而没有对应源码树时，五个 compatibility/runtime-spine
  collection 检查可条件跳过（账本记录的例子是 `flecs`）。在把跳过视为证据前，必须提供
  带依赖源码的匹配构建快照。
- platform-spawn 合约对 `spdlog` 有同类构建快照限制；跳过不构成产品失败，也不构成合约通过。
- 当 `build-gpu/` 及其 `ef_py` 工件不存在时，CUDA import-order 测试条件跳过。CPU-only
  工作树不提供 CUDA 证据。
- diagnostics 顶层入口治理检查在批准的整合边界真正落地前保持严格 xfail。
- leader-phase-manager 场景合约存在 harness fixture 与当前 arming gate 的 lineage 不一致；
  JSON 合约和 runner 需要所有者裁定后才能重新分类该红项。

## 安全使用

条件跳过和严格 xfail 必须在报告中保持可见；它们不能等同于验证通过，不能仅为提高 smoke
计数而删除。只有命名的环境、运行器或治理改动存在且聚焦检查重新执行后，残差才能关闭。

## 来源与保留

日期化复现和已修复项仍保留在
已完成的 T6 账本 (`git show 77610218:docs/plan/archive/unified_architecture_program_completed_20260727/t6_residual_ledger.zh.md`)。
本文是测试维护者的当前入口，不复制账本中的历史迭代叙事。
