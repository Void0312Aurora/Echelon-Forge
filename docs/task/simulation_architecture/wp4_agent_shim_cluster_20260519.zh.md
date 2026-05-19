# WP4-H 分发表：Information And Agent Shim

状态：`2026-05-19` 第二波分发表。

语言版本：

- 英文主文：[wp4_agent_shim_cluster_20260519.md](wp4_agent_shim_cluster_20260519.md)
- 中文辅文：`wp4_agent_shim_cluster_20260519.zh.md`

输入：

- [WP4 第一波验收审查](../review/wp4_first_wave_acceptance_review_20260519.zh.md)
- [WP4-D/E policy-binding 对齐笔记](wp4_policy_binding_alignment_notes_20260519.zh.md)
- [WP4-A surface inventory 初稿](wp4_surface_inventory_wp4a_20260519.zh.md)
- 当前 `python/rl/runtime/*`、`python/rl/control/*` 与 `gym_envs/*`

## 一、目的

WP4-H 创建通向 `AgentRole`、`ActionIntentPacket` 与 `CoordinationIntentPacket` 的最小 Python-side bridge，同时避免过早提升新的 C++ facade DTO。

本任务簇应产出 shim、notes 或窄测试，让当前 compatibility path 显式化。

## 二、必需工作项

| 流 | 必需输出 | 写入范围 | 预算 |
|----|----------|----------|------|
| `WP4-H1 AgentRole Dataclass Or Note` | Python-side `AgentRole` sketch 或文档映射 single-agent、batch、multi-agent、leader/C2 与 scripted director role。 | `python/rl/runtime/*` 或 docs。 | 高。 |
| `WP4-H2 ActionIntent Compat Wrapper` | 为当前 `PilotAction` 与 `WorldPilotActionAssignment` 提供 wrapper/note，在可能时携带 source id、timing、merge policy 与 role metadata。 | `python/rl/runtime/*`、`python/rl/control/*`、docs。 | 高。 |
| `WP4-H3 CoordinationIntent Compat Wrapper` | 为 task/order/leader/report assignment chain 提供 wrapper/note，在可能时携带 source、roster、update clock、merge policy 与 role metadata。 | `python/rl/runtime/*`、`gym_envs/*`、docs。 | 中高。 |
| `WP4-H4 Observation Provenance Labels` | 识别名为 `truth` 但实际是 facade observation 的变量，并把 raw/oracle path 标为 diagnostics-only。 | docs，可选窄 Python comment/test。 | 高。 |
| `WP4-H5 Binding Deferral Note` | 确认 `AgentRole`、`DecisionBelief` 与 intent packet 等待稳定 WP4-A 名称后再做 C++ binding。 | docs/task/simulation_architecture。 | 中。 |

## 三、非目标

- 本任务簇不为 `AgentRole`、`DecisionBelief`、`ActionIntentPacket` 或 `CoordinationIntentPacket` 添加 public C++ binding。
- 不大范围重构 Gymnasium environment。
- 不改变 policy inference 行为。
- 不移除 compatibility adapter。

## 四、验收门槛

本任务簇验收条件：

1. 当前 policy/coordination path 有明确 role/action/coordination metadata 映射，或有文档化缺口。
2. Maintained、compatibility 与 diagnostics-only observation path 可区分。
3. 若新增 Python-side shim，它们是 passive wrapper，不改变 runtime 行为。
4. Binding 扩展保持 deferred，直到 surface name 与 DTO field 稳定。
