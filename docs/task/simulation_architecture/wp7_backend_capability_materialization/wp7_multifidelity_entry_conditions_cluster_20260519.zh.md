# WP7-D 分发单：Multi-Fidelity Entry Conditions

状态：`2026-05-19` WP7 架构/设计计划分发单。

语言版本：

- 英文主文：[wp7_multifidelity_entry_conditions_cluster_20260519.md](wp7_multifidelity_entry_conditions_cluster_20260519.md)
- 中文辅文：`wp7_multifidelity_entry_conditions_cluster_20260519.zh.md`
- 可实施细化说明：
  [wp7_multifidelity_entry_conditions_notes_20260519.zh.md](wp7_multifidelity_entry_conditions_notes_20260519.zh.md)

输入：

- [WP7 后端能力物化](backend_capability_materialization_wp7_20260519.zh.md)
- [Temp-02 SCAL 架构愿景审查](../review/temp-02_review_20260519.zh.md)
- [Temp-02 原始笔记](../review/temp/temp-02.md)
- [架构与性能路线进一步调研](../../plan/architecture/architecture_and_performance_research_followup.zh.md)
- [WP6 后端配置文件策略](backend_profile_policy_wp6_20260519.zh.md)
- [WP6-A 后端配置文件注册表](wp6_backend_profile_registry_20260519.zh.md)
- [WP6-B parity budget 注册表](wp6_parity_budget_registry_20260519.zh.md)
- [WP5 验证套件](validation_harness_wp5_20260519.zh.md)

命名边界：

- 旧评审中曾把 `WP7` 作为 backend profile policy 的历史别名；该工作线已经作为
  `WP6` 关闭。
- 本 WP7-D 属于新的 post-WP6 物化工作线。它不得复活旧别名，也不得声称 backend
  profile policy 仍然是 WP7。

## 1. 目的

WP7-D 把此前推迟的 multi-fidelity 想法转化为可实施的 entry conditions。它不启用
adaptive fidelity scheduling、reduced-fidelity execution、learned model
substitution，也不新增维护中 backend support。

本任务定义未来 fidelity profile request 如何引用：

1. 共享的 `P0-P10` semantic lifecycle；
2. 已验收的 backend profile metadata；
3. parity 或 tolerance budget 记录；
4. model family 与暂缓的 `ModelProvider` 边界；
5. WP5 validation gate 证据；
6. facade-visible evidence，用来证明请求了什么以及什么能力确实处于维护态。

## 2. 必需工作项

| 流 | 必需产出 | 写入范围 | 预算 |
|----|----------|----------|------|
| `WP7-D1 Fidelity Profile Vocabulary` | 把 `exact_evaluation`、`fast_training`、`sensor_heavy`、`weapon_effects_heavy`、`large_scale_swarm`、`single_platform_physics` 等 label 定义为 request，而不是维护中 support claim。 | 文档。 | 高。 |
| `WP7-D2 Backend Profile Binding Rule` | 说明每个 fidelity profile request 必须如何绑定 backend profile id、parity/tolerance budget、model family scope、validation gate 与 facade evidence。 | 文档。 | 高。 |
| `WP7-D3 ModelProvider Deferral Boundary` | 文档化哪些 ModelProvider 术语目前只能作为 vocabulary，哪些必须等 model interface、training provenance 与 promotion evidence 后才能使用。 | 文档。 | 中高。 |
| `WP7-D4 Adaptive Scheduling Entry Gate` | 定义 adaptive fidelity scheduling 进入活跃实现前的前置条件。 | 文档与未来测试计划。 | 高。 |

## 3. Fidelity Profile 词汇规则

fidelity profile 不是 backend profile。fidelity profile 是 compilation 或
configuration request，用于为某个 scenario 或 experiment 选择已验收的 model family、
backend profile、comparison budget 与 validation gate。

label 本身永远不是 support claim：

| Fidelity profile request | 请求含义 | 禁止推论 |
|--------------------------|----------|----------|
| `exact_evaluation` | 使用维护中的 exact truth 做评估和比较。 | 不意味着 exact GPU 或 resident-state support。 |
| `fast_training` | 为训练实验优先请求吞吐路径。 | 不会把 approximate 或 diagnostics output 变成 exact truth。 |
| `sensor_heavy` | 强调 sensor、track、data-link、observation 与 information-state 工作负载。 | 不绕过 observation envelope、visibility 或 belief boundary。 |
| `weapon_effects_heavy` | 强调 launch、munition、effect、damage、reward 与 termination evidence。 | 不削弱 event ancestry 或 damage/effect trace 要求。 |
| `large_scale_swarm` | 为大量平台或智能体请求规模导向执行。 | 不削弱 event order、snapshot provenance 或 facade evidence。 |
| `single_platform_physics` | 为单平台或窄平台族请求聚焦的 physics/control 评估。 | 不在命名 model family 与 budget 之外认证 high-fidelity physics。 |

## 4. 绑定契约

每个 fidelity profile request 在进入实现计划前必须绑定以下全部字段：

1. `backend_profile_id`：来自已验收的 WP6/WP7 registry 线；WP7-D 不发明 id。
2. `parity_budget_ref` 或显式 tolerance budget：来自 WP6 parity budget registry 或未来已验收的 registry revision。
3. `model_family_scope`：请求覆盖的 lifecycle stage 与 domain model family。
4. `validation_gate`：必须通过的 WP5 evidence tier 或未来 promotion gate。
5. `facade_evidence`：request id、backend profile id、budget id/version、comparison reference、snapshot 或 barrier provenance、mismatch policy 与 diagnostics label。

第一个已验收 exact baseline 仍是 `cpu_exact.reference`。GPU helper、exact GPU candidate、
resident-state candidate 与 shadow-compare candidate 在各自 profile metadata、budget、
ownership/sync policy 与 WP5 evidence 被验收前，仍保持 diagnostics-only 或 unmaintained。

## 5. ModelProvider 暂缓边界

`ModelProvider` 在 WP7-D 中仅是 vocabulary。以下术语可以用于描述未来架构意图：
analytical provider、table provider、surrogate provider、learned provider、hybrid
provider 与 diagnostics provider。

它们不得成为 runtime interface 或 maintained claim，直到后续工作包定义：

1. provider interface 与 lifecycle ownership；
2. model artifact identity 与 versioning；
3. training 或 calibration provenance；
4. input/output contract 与 information-state boundary；
5. parity 或 tolerance budget；
6. WP5-compatible validation 与 replay evidence；
7. facade-visible evidence，用于区分 maintained truth 与 diagnostics。

## 6. Adaptive Scheduling 进入门槛

adaptive fidelity scheduling 仍不在 WP7-D 活跃实现范围内。只有以下前置条件全部存在后，
它才能进入未来任务：

1. state shard versioning，能够识别 fidelity switch 影响的每个 shard；
2. replay evidence，证明 switch boundary 上可以做确定性比较；
3. mismatch policy，覆盖 exact、tolerated、candidate 与 diagnostics result；
4. scheduling contract，命名允许的 switch point、barrier 与 rollback behavior；
5. rollback 或 quarantine procedure，用于处理 mismatch 或不可信输出；
6. facade evidence，记录 requested fidelity、selected backend profile、selected model family、budget version 与 switch ancestry。

## 7. 非目标

- 不实现 adaptive fidelity scheduling。
- 不引入 learned model provider。
- 不把 approximate output 晋级为 exact truth。
- 不创建单独的 reduced-fidelity semantic lifecycle。
- 不绕过 backend profile 或 parity budget registry。
- 不新增维护中 exact GPU、resident-state、shadow 或 multi-fidelity capability claim。

## 8. 验收门槛

本任务簇在以下条件满足时验收：

1. fidelity profile label 被定义为 request，而不是 support claim。
2. 每个示例 fidelity profile 都说明使用前需要哪个 backend profile、parity 或 tolerance
   budget、model family、validation gate 与 facade evidence。
3. `ModelProvider` 工作被明确推迟并划清范围。
4. adaptive scheduling prerequisites 已命名，并在 gate 存在前保持在当前 WP7 实现范围之外。
5. 任务簇引用 WP6 policy/registry 与 WP5 evidence requirement。
6. 中英文文档互链，并保持相同的章节形状。

## 9. 验证命令

```bash
git diff --check
rg -n "fidelity profile|exact_evaluation|fast_training|sensor_heavy|weapon_effects_heavy|large_scale_swarm|ModelProvider|adaptive|validation gate" docs/task/simulation_architecture/wp7_multifidelity*20260519*.md
```
