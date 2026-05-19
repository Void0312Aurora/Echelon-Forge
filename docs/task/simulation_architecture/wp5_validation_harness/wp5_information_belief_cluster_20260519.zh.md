# WP5-D 分发单：Information 与 Belief Gate

状态：`2026-05-19` 第二波分发单。

语言版本：

- 英文主文：[wp5_information_belief_cluster_20260519.md](wp5_information_belief_cluster_20260519.md)
- 中文辅文：`wp5_information_belief_cluster_20260519.zh.md`

输入：

- [WP5 验证套件](validation_harness_wp5_20260519.zh.md)
- [WP5 第一波验收审查](../review/wp5_first_wave_acceptance_review_20260519.zh.md)
- [WP5-A harness inventory 笔记](wp5_harness_inventory_notes_20260519.zh.md)
- [WP4-H agent shim 实现笔记](wp4_agent_shim_implementation_notes_20260519.md)
- 当前 `python/rl/runtime/agent_shim.py`
- 当前 `tests/runtime/test_agent_shim.py`
- `python/rl/runtime/`、`python/rl/control/` 与 `gym_envs/` 下的当前 policy/runtime adapter path

## 1. 目的

WP5-D 验证 information-state 与 belief 边界，但不禁止 legacy compatibility 或
diagnostics path。它应证明维护中的 decision path 可以被标记为
`ObservationPacket` 或已声明的 `DecisionBelief` consumer，同时 truth/oracle path
保持 diagnostics-only。

这是一条高推理流，因为过宽 guard 会挡住合法 diagnostics 与 legacy migration path。

## 2. 必做工作

| 流 | 必要产出 | 写入范围 | 预算 |
|----|----------|----------|------|
| `WP5-D1 Shim Vocabulary Gate` | 加强或记录 `ObservationProvenance`、`AgentRole`、action intent 与 coordination intent label 的测试。 | `tests/runtime/test_agent_shim.py`、docs。 | 高。 |
| `WP5-D2 Maintained-Path Allowlist Sketch` | 识别未来 direct `sim.*` 限制可安全作用的 maintained adapter module，并列出必须允许的 compatibility/diagnostics module。 | `docs/task/simulation_architecture`，如低风险可加 architecture test。 | 高。 |
| `WP5-D3 Truth/Oracle Leakage Review` | 添加 docs-backed checks 或 notes，区分 `raw_world_truth` / `diagnostics_oracle` label 与 maintained policy input。 | docs，可选窄测试。 | 高。 |
| `WP5-D4 DecisionBelief Deferral Boundary` | 记录 typed `DecisionBelief` DTO 存在前可测试内容，以及必须 metadata-dependent 的内容。 | docs。 | 高。 |
| `WP5-D5 Smoke Candidate Advice` | 为 WP5-E smoke promotion 推荐 information/belief 测试。 | docs。 | 中等。 |

## 3. 非目标

- 不添加仓库级宽泛 direct `sim.*` ban。
- DTO 支持存在前，不要求 runtime `ObservationViewSpec`、packet snapshot/barrier/source
  metadata 或 typed `DecisionBelief`。
- 不改变 policy inference 行为。
- 不移除 diagnostics/oracle helper。
- 不直接编辑 smoke-suite membership。

## 4. 验收门槛

本任务簇满足以下条件时验收：

1. Shim label 测试或笔记能区分 maintained、compatibility 与 diagnostics-only information source。
2. 未来 direct `sim.*` enforcement 有具体 maintained-path allowlist sketch 与
   compatibility/diagnostics exception list。
3. `DecisionBelief` 可以通过现有 label 测试，或被明确推迟到 typed metadata 后。
4. 聚焦测试本地通过。
