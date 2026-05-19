# WP6-C + WP6-D 规范分发单：Resident-State 边界规则与集成交接

状态：`2026-05-19` resident-state 边界规则、backend capability projection
策略与 WP6 index sync 的实现对齐分发单和已完成发布交接。

语言版本：

- 英文主文：[wp6_integration_and_index_sync_20260519.md](wp6_integration_and_index_sync_20260519.md)
- 中文辅文：`wp6_integration_and_index_sync_20260519.zh.md`

输入：

- [WP6 后端配置文件策略](backend_profile_policy_wp6_20260519.zh.md)
- [WP6-A 后端配置文件分类分发单](wp6_backend_profile_taxonomy_cluster_20260519.zh.md)
- [WP6-A 后端配置文件注册表](wp6_backend_profile_registry_20260519.zh.md)
- [WP6-B parity budget 分发单](wp6_parity_budget_cluster_20260519.zh.md)
- [WP6-B parity budget 注册表](wp6_parity_budget_registry_20260519.zh.md)
- [WP6-C1 resident-state 边界规则](wp6_resident_state_boundary_rules_20260519.zh.md)
- [仿真系统架构设计](../../plan/architecture/simulation_system_architecture_design.zh.md)
- [架构与性能路线进一步调研](../../plan/architecture/architecture_and_performance_research_followup.zh.md)
- [架构计划审查](../review/architecture_plan_review_20260519.zh.md)
- [Temp-02 SCAL 架构愿景审查](../review/temp-02_review_20260519.zh.md)
- [WP4 facade 对齐](facade_alignment_wp4_20260519.zh.md)
- [WP5 验证套件](validation_harness_wp5_20260519.zh.md)

规范术语：

- `MUST` 表示 WP6 维护文档与后续发布所要求的行为。
- `MUST NOT` 表示不能定义维护中的 backend 真值的行为。
- `SHOULD` 表示默认规则，偏离需要显式补充任务或审查说明。
- `MAY` 表示允许的兼容或文档路径。

## 1. 目的

本分发单把剩余的 WP6 议题收敛成串行集成包。它不再重新定义 taxonomy 或 parity，而是处理 resident-state profile、backend capability projection 与发布交接如何拼接。

这里的文案刻意写成面向实现且可直接进入发布说明的形式：它应当指导第一轮 capability projection 工作，但不能在维护中的 profile 声明前宣称 exact GPU execution、resident-state truth 或 shadow execution 支持。

这里也记录 WP6 命名规范化：旧笔记里把 backend profiles 写成 `WP7`，在这条工作线里视为历史命名；当前有效任务标识统一使用 `WP6`。

## 2. 分发产物

| 流 | 必需产出 | 负责人画像 | 思考预算 |
|----|---------|-----------|---------|
| `WP6-C1 Resident-State Boundary Rules` | host-owned、backend-owned、partial-sync、observation-only 与 export-only 规则。 | integration worker。 | 高。 |
| `WP6-C2 Backend Capability Projection Policy` | `RuntimeCapabilities`、`BackendCapabilityFacade` 与任何 backend capability query 的策略。 | integration worker。 | 高。 |
| `WP6-D1 Naming And Cross-Reference Sync` | WP6 引用与旧 WP7 文案的跨文档对齐。 | integration worker。 | 中。 |
| `WP6-D2 Publication Handoff` | 在 WP6 文档稳定后，用于更新 README / review 索引的交接文本。 | integration worker。 | 中。 |

## 2.1 已完成 WP6-C/WP6-D 产物

已完成的发布线引用以下 implementation-ready 产物：

1. [WP6-A 后端配置文件注册表](wp6_backend_profile_registry_20260519.zh.md)
   作为 profile metadata 来源。
2. [WP6-B parity budget 注册表](wp6_parity_budget_registry_20260519.zh.md)
   作为 profile-owned comparison budget 来源。
3. [WP6-C1 resident-state 边界规则](wp6_resident_state_boundary_rules_20260519.zh.md)
   作为 resident-state ownership 与 sync gate。
4. [runtime facade layering 测试](../../../tests/architecture/test_runtime_facade_layering.py)、
   [runtime facade 测试](../../../tests/runtime/facade/test_runtime_facade.py) 与
   [GPU runtime binding 测试](../../../tests/test_gpu_runtime_bindings.py) 中的
   capability-projection guard。
5. [WP6 验收审查](../review/wp6_backend_profile_policy_acceptance_review_20260519.zh.md)
   作为最终 WP6 发布记录。

## 3. Resident-state 边界规则

WP6-C MUST 说明：

1. device-resident state 只有在声明 host/backend ownership 与 sync policy 后，才可作为维护中的实现。
2. resident-state profile MUST 写清哪些 shard 由 host 拥有，哪些由 backend 拥有。
3. resident-state profile MUST 写清维护中的输出是 observation-only、export-only 还是 committed state。
4. resident-state profile MUST 写清哪些 backend-local state 不在维护中的 parity 范围内，因此只能 diagnostics-only。
5. backend thread completion order MUST NOT 变成维护中的真值。

## 4. Backend capability 暴露策略

WP6-C 还 MUST 说明：

1. `RuntimeCapabilities` 是 capability projection，不是 backend profile 类别、
   planner 或权威来源。
2. `RuntimeCapabilities` 可以镜像已声明的 profile 元数据和可探测部署事实，
   但不能发明 profile 没声明的能力语义。
3. `BackendCapabilityFacade` 是策略面，不是隐藏实现真值。
4. 任何无法从 profile 元数据解释的 capability query，都应放入后续实现包。
5. exact GPU world-step 在维护中的 profile 声明 parity、ownership、sync 规则与 validation gate 前保持 false。
6. resident-state capability 在维护中的 profile 声明 backend-owned state scope、
   host-visible reconstruction 或 export 规则、sync barrier 与 parity budget 前保持 false。
7. shadow 风格 capability 保持 false，除非维护中的 profile 显式声明 shadow 的对象、是否影响 committed state，以及 diagnostics 如何与维护真值隔离。
8. 可探测部署事实可以包括已编译 backend 是否存在、运行时是否可用、device 枚举或配置的 feature gate；这些事实可以解释为什么已声明 profile 不可用，但不能把 helper 提升成维护中的 exact/resident/shadow 支持。

## 5. 集成与发布规则

WP6-D MUST 把以下内容当作发布约束：

1. WP6-A taxonomy 输出与 WP6-B parity 输出，是 WP6-C 与 WP6-D 能使用的唯一后端 profile 词汇来源。
2. 主 WP6 文档保持为 backend profile policy 的顶层入口。
3. README 与 review 索引更新引用 registry、boundary、capability guard 与
   acceptance-review 产物，而不是草稿碎片。
4. 旧 `WP7` 表述在 active WP6 线中必须先被规范化，然后才能发布；规范化后也只能保留为历史命名。
5. 任何以后依赖这些文档的 runtime 变更，都应引用最终发布的 WP6 线，而不是草稿碎片。

## 6. 非目标

- 在 WP6-A/B/C 产物稳定前修改 `docs/task/simulation_architecture/README.md`
  或 review 索引。
- 实现 resident-state runtime 代码。
- 实现 backend capability query。
- 在维护中 profile 元数据声明前，宣称 exact GPU、resident-state 或 shadow 支持。
- 重开调度语义或 facade 语义。
- 把集成单当成 runtime parity 的替代物。

## 7. 退出标准

当以下条件满足时，本分发单退出：

1. resident-state 边界规则已经明确，且不与 taxonomy 单冲突。
2. capability 暴露被描述为策略面，而不是隐藏 runtime 假设。
3. `RuntimeCapabilities` 被对齐为已声明 profile 元数据与可探测部署事实的投影；
   exact GPU、resident-state 与 shadow 风格支持默认 false，除非维护中的 profile 显式声明。
4. WP6/WP7 的命名规范化说清楚了。
5. 发布交接更新 README 和 review 索引，而不必重写 WP6 主体，也不会把
   `WP7` 重新变成活线。
6. 中文辅文已足够对齐，可用于后续发布。

## 8. 发布交接结果

WP6-D 发布以下稳定结论：

1. `cpu_exact.reference` 是初始 profile registry 中唯一维护中的 exact baseline。
2. GPU helper、exact GPU candidate、resident-state candidate 与 shadow-compare
   candidate 在维护中的 profile revision 声明 ownership、sync、parity budget 与
   validation gate 前，仍保持 diagnostics-only 或 unmaintained。
3. `RuntimeCapabilities` 当前只投影维护中的 facade/core 能力：batch runtime、
   compiled episode controller 与 compiled execution step。Exact GPU、device
   observation、resident-state 与 shadow support 保持 false。
4. Backend helper/probe availability 可以解释 diagnostics 或 deployment fact，但不能把
   profile 提升成维护中真值。
5. 活跃文档使用 `WP6` 作为规范 backend profile 线；历史 `WP7` 表述只保留为历史命名。

## 9. 验证命令

```bash
git diff --check
rg -n "WP6|WP7|resident-state|BackendCapability|RuntimeCapabilities|shadow|index sync" docs/task/simulation_architecture docs/plan/architecture docs/task/review
```
