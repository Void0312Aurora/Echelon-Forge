# M3-S1 Censored Optimal-Stopping Timing Contract

状态：`2026-06-05` nonfinite-probe training-path 修复后，P5 short-training
evidence 已通过；不声明 learned-policy acceptance。

语言：

- 英文主文：[README.md](README.md)
- 中文配套：`README.zh.md`

输入：

- 父级模型任务索引：[模型任务](../README.zh.md)
- M3 模型选择综合：
  [m3_model_selection_synthesis_20260605.md](../m3_optimal_stopping_model_selection/m3_model_selection_synthesis_20260605.md)
- 当前架构边界图：
  [m3_s1_model_architecture_boundary_map_20260605.zh.md](m3_s1_model_architecture_boundary_map_20260605.zh.md)
- A7 当前经验堵塞：
  [A7 当前状态](../../air_combat/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_current_status_20260604.zh.md)
- 子项目标准：
  [子项目创建标准](../../../agent/rules/subproject_creation_standard.zh.md)

## 目的

M3-S1 将 M3 的模型选择结论转成可实现合同。目标不是再做 A7 系数修补，而是给
一次性时机决策建立清晰模型边界：agent 观察序列，在 legal mask 下最多停止一次，
早期事件质量必须受预算约束，并且在数据支持时把事件质量放入 desirable window。

本子项目也先整理当前模型主干与分支，再打开代码修改。reward、合法性 gate、policy
heads、rollout labels 与 auxiliary losses 必须有独立归属，避免后续继续把 reward
shaping、PPO loss 与 first-event supervision 混在同一个补丁面里。

## 当前状态

| Area | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| M1 action surface | accepted input | `air_combat_hybrid_v1` 是 12D flat transport，policy 侧解释 hybrid 语义。 | 不证明 learned fire discipline。 |
| A6/A7 first-event branch | held input | A7 已有 event heads、credit heads、label plumbing 与 diagnostics，但 learned behavior 仍堵塞。 | A7 是证据来源，不是主合同。 |
| M3 model selection | pass input | M3 推荐 censored optimal stopping，配合 wait-preserving data 与 survival/event-time calibration。 | M3 尚未实现。 |
| Architecture separation | pass contract | 本 README 与边界图命名 model trunk、branches、rewards 与 auxiliary losses。 | 尚未验收 runtime refactor。 |
| Implementation | pass | P4 增加 independent stopping-head、grouped evidence/loss helper 与 PPO-side grouped auxiliary pass。 | 不声明 learned-policy success。 |
| Validation dispatch | evidence pass | P5 diagnostics、有边界 8k training 与训练后 deterministic/stochastic probes 均已记录。 | learned executable fire timing 仍 held。 |

## 范围

范围内：

- 在训练修改前写清模型主干/分支归属合同。
- 定义 wait-preserving timing evidence 的 data/censoring route。
- 必要时把 flattened per-row first-event objective 替换成 grouped
  episode/window stopping objective。
- 定义 deterministic stop-vs-continue boundary 与 survival/event-time diagnostics。
- 将环境 reward、auxiliary training losses、C2/ROE 合法性 gate 分开。

范围外：

- 第一动作就释放 M2 或重写 sequence-native PPO。
- 用 reward-only fix 解决 first-event timing。
- 为了方便训练而削弱 C2/ROE、action masks、导弹合法性或 one-shot gates。
- 在验收探针通过前宣称 A7、M3-S1 或任意 learned policy accepted。

## 阶段计划

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary Map` | 固定 model spine、branch、reward 与 loss ownership。 | M3 synthesis 已存在。 | 边界图命名每个 owner、write surface 与 forbidden coupling。 | pass |
| `P1 Data/Censoring Contract` | 定义 wait-preserving timing evidence 与 rollout metadata。 | P0 boundary map 已审阅。 | 合同解释 early event 如何删失 suffix，以及后续 desirable window 如何保持可观测。 | pass |
| `P2 Grouped Objective` | 指定按 episode/window ID 分组的 survival/stopping loss。 | P1 data route 存在。 | Loss 设计保留窗口结构，而不是退化为 shuffled per-row BCE。 | pass |
| `P3 Policy Head Contract` | 决定复用 event-logit delta 还是新增 survival/event-time head。 | P2 objective 存在。 | 定义 deterministic stop boundary 与 calibrated event-time diagnostics。 | pass |
| `P4 Integration Slice` | 只实现 P1-P3 选中的最小 data/loss/head 改动。 | P1-P3 accepted。 | focused tests 通过，且无 reward 或 legality 回归。 | pass |
| `P5 Validation` | 运行 diagnostic 与短训验收门。 | P4 focused tests 通过。 | boundary crossing、early mass、one-shot legality 与 grouped labels 均有记录。 | pass |
| `P6 Closure` | 同步 status、residuals 与父级索引。 | validation evidence 存在。 | 文档区分 accepted code paths 与 held learned behavior。 | held |

## 任务簇

- Task cluster plan：
  [m3_s1_censored_optimal_stopping_timing_contract_task_clusters_20260605.zh.md](m3_s1_censored_optimal_stopping_timing_contract_task_clusters_20260605.zh.md)
- Dispatch queue：
  [m3_s1_censored_optimal_stopping_timing_contract_dispatch_queue_20260605.zh.md](m3_s1_censored_optimal_stopping_timing_contract_dispatch_queue_20260605.zh.md)

## 输出与证据

- 架构边界图：
  [m3_s1_model_architecture_boundary_map_20260605.zh.md](m3_s1_model_architecture_boundary_map_20260605.zh.md)
- Data/censoring contract：
  [m3_s1_data_censoring_contract_20260605.zh.md](m3_s1_data_censoring_contract_20260605.zh.md)
- Grouped objective contract：
  [m3_s1_grouped_stopping_objective_contract_20260605.zh.md](m3_s1_grouped_stopping_objective_contract_20260605.zh.md)
- Policy head boundary contract：
  [m3_s1_policy_head_boundary_contract_20260605.zh.md](m3_s1_policy_head_boundary_contract_20260605.zh.md)
- P4 dispatch review：
  [m3_s1_p4_dispatch_review_20260605.zh.md](m3_s1_p4_dispatch_review_20260605.zh.md)
- P5 dispatch plan 与 short-training evidence：
  [m3_s1_p5_dispatch_plan_20260605.zh.md](m3_s1_p5_dispatch_plan_20260605.zh.md)
- Learned-policy acceptance evidence：P5 后仍 held，因为 deterministic executable
  release 仍然 flat。

## 验收门

本子项目只有在以下条件满足后才能 accepted：

- model trunk/branch 边界已成文，并反映到代码布局或 adapter functions；
- first-event timing 训练基于 grouped episode/window objective，或有明确论证的
  fallback，而不是 accidental per-row classification；
- reward shaping 保持为环境 scalar signal，不替代 legality、censoring 或
  event-time supervision；
- deterministic probes 在 held-out wait-preserving trajectories 的 desirable
  windows 内越过 stop boundary；
- cumulative prewindow event mass 低于配置预算；
- stochastic rollout 保持 one-shot legal，且不削弱 C2/ROE masks；
- validation gates 通过前不声明 learned-policy success。

## 残余与下一步

- P3 选择独立 survival/stopping head 作为长期模型对象；executable fire logits 只是
  adapter/action branch。
- `P4 Minimal Integration` 已作为有边界 implementation slice 通过。它增加 independent
  stopping head、grouped evidence/loss helper 与 PPO-side grouped auxiliary pass，且不修改
  reward 或 legality gates。
- `P5 Validation` 证据已完成。它修复了 `--nonfinite_probe` 的 diagnostic-path drift，
  证明 independent M3 stopping head 可以接收 grouped stopping updates，并记录了
  deterministic/stochastic probes。
- P5 没有验收 learned executable fire timing：deterministic release 仍然 flat，
  stochastic release 仍主要由 sampling 产生，且 executable hybrid action branch 仍与 M3
  stopping head 分离。
- 后续根因审计已移至
  [M3-S2 开火时机可学习性审计](../m3_s2_fire_timing_learnability_audit/README.zh.md)，
  现已归档为有边界 firing-gate evidence：active scenario/config pair 下 release
  execution 已接受，但 legal timing quality 与 effects quality 仍 held。
- 如果 grouped stopping objective 仍无法表达 timing evidence，再把 M2 sequence memory
  当作后续候选。
- 当 M3-S1 取代 actor teaching path 后，将 A7 local repairs 作为证据归档。

## Archive

暂无 archive records。
