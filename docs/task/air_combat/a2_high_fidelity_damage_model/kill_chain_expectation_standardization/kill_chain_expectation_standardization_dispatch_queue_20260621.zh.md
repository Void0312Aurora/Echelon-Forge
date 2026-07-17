# 杀伤链期望标准化派发队列

状态：`2026-06-23`，当前会话内 P0-P5 docs-only 队列已集成 pass。

英文规范页：
[kill_chain_expectation_standardization_dispatch_queue_20260621.md](kill_chain_expectation_standardization_dispatch_queue_20260621.md)

父任务簇：
[kill_chain_expectation_standardization_task_clusters_20260621.zh.md](kill_chain_expectation_standardization_task_clusters_20260621.zh.md)

## 边界

本队列只覆盖期望标准化。不得创建新的 Codex 会话线程，不得修改 runtime 代码，不得重调
descriptor，不得声明真实 AIM-120C、F-16C 或 Pk 权威。

## 当前派发包

| Packet | Cluster | Assignee | Write set | Required output | Status |
| --- | --- | --- | --- | --- | --- |
| `KCES-P0-W1` | `KCES-P0 Project Boundary` | main thread | 子项目文档和父级 A2 README 文件 | 创建子项目骨架并从 A2 链接。 | integrated pass |
| `KCES-P1-W1` | `KCES-P1 Expectation Contract` | main thread | 期望合同文档 | 起草 v0 期望合同，包含归一化距离和 AIM-120C-like 种子画像。 | integrated pass |
| `KCES-P2-W1` | `KCES-P2 Scenario Matrix` | main thread | 场景矩阵文档 | 构建距离 x 偏置角 heatmap，将非机动 full grid 和机动 sparse grid 归类为 nominal、marginal 或 outside-envelope，估算推荐主网格 / seed 预算，并选择第一轮 `R_effect_variant` handoff。 | integrated pass |
| `KCES-P3-W1` | `KCES-P3 Metric Mapping` | main thread | 指标映射文档和状态面 | 把期望分区、采样密度层级、`R_effect_variant` 和 owner guard 映射到 stage-report / derived-report 字段。 | integrated pass |
| `KCES-P4-W1` | `KCES-P4 Calibration Harness Plan` | main thread | harness plan 文档和状态面 | 在不重调参数的情况下，把 P3 report row schema 绑定到单层 delta-guard 检查、artifact family 和 pilot batch 计划。 | integrated pass |
| `KCES-P5-W1` | `KCES-P5 Closure / Promotion Decision` | main thread | P5 决策文档和状态面 | 决定 P1-P4 pass 内容保留为 task-local docs-only standard；本轮不提升到 `docs/standards`。 | integrated pass |

## 可派发后续

无。本 P0-P5 docs-only 队列已收口。未来 harness implementation 或 standards promotion
必须作为新的明确 workstream 进入。

## 集成说明

- P1 已按 `R_effect` 保持独立 review variable 收口。
- P2 不得把当前 runtime 的成功或失败当成 oracle。
- P2 已选择第一轮 `R_effect_variant` rows，并将校准对象扩展为 heatmap；推荐主网格
  为约 `572` signed cases / seed；stage-report metric mapping 进入 P3。
- P3 已将 heatmap、采样层级和 `R_effect_variant` 映射到 report row schema。
- P4 已复用 P6 single-layer guard 形状生成 docs-only harness plan，但未运行批量仿真。
- P5 已决定本子项目保留为 task-local docs-only standard；本轮不写入 `docs/standards`，
  不静默提升 runtime behavior。

## Worker Packet 合同

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```
