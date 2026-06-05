# M3-S1 Policy Head Boundary Contract

状态：`2026-06-05` pass；P3 合同选择方案 B，即独立 survival/stopping head 作为长期模型对象。
implementation 现在由 P4 dispatch queue 承接。

父项目：[M3-S1 Censored Optimal-Stopping Timing Contract](README.zh.md)。

输入：

- [P1 Data/Censoring Contract](m3_s1_data_censoring_contract_20260605.zh.md)
- [P2 Grouped Stopping Objective Contract](m3_s1_grouped_stopping_objective_contract_20260605.zh.md)
- [Architecture Boundary Map](m3_s1_model_architecture_boundary_map_20260605.zh.md)

## 决策

M3-S1 选择方案 B：

```text
policy trunk
  -> ordinary hybrid action branch
  -> independent survival/stopping-time branch
  -> value branch
  -> optional A7 credit/diagnostic branch
```

stopping branch 是一次性时机决策的规范模型本体。现有 executable fire logits 不是停时模型。
它们属于动作执行分支，只能在 stopping branch 做出合法 stop decision 后，通过显式 adapter
接收信号。

作为长期主线拒绝：

- 使用 `fire_logit - hold_logit` 作为 primary stop score；
- 让 A7 `Q_fire_once - Q_hold` 成为 event logits 的唯一教师；
- 让 executable action logits 同时承担 action distribution 与 event-time density；
- 在没有本 stopping-head 合同的情况下添加 generic sequence model。

## Head 定义

对每个 row `t`，policy 暴露一个 stopping score：

```text
z_t = h_stop(H_t)
```

其中 `H_t` 是当前 observation 的 policy representation，或未来 M2 选择的 sequence
representation。第一版 M3-S1 implementation slice 可以使用当前 HMoE actor latent。长期合同
不要求 M2，但也不能阻止后续用 M2 替换 representation。

合法性 mask 在 raw head 外部应用：

```text
lambda_t = M_t * sigmoid(z_t)
```

其中 `M_t` 来自 observation 与 C2/ROE state 的 executable legal stop/fire mask。head
可以学习状态好坏，但只有 mask 决定 stop 是否可执行。

## Deterministic Boundary

部署规则：

```text
stop iff M_t = 1 and z_t >= theta_stop
```

`theta_stop` 是配置或校准阈值。Grouped objective 负责校准 event-time mass；
deterministic probes 判断 boundary 是否在 desirable windows 内越过。

action branch 通过显式 adapter 接收 stop decision：

```text
if stop:
  request fire_once through the existing hybrid action transport
else:
  keep fire_once off
```

adapter 不允许绕过 C2/ROE。被拒绝或 closed-mask 的 stop 仍然不可执行，并应进入 diagnostics。

## 与现有 Event Logits 的关系

当前 hybrid event logits 保持为 action-distribution parameters。

允许：

- 将 `event_logit_delta` 暴露为 diagnostic；
- 在 grouped loss 建立后，可选地把 stopping-head decision 蒸馏到 legal-open rows 的
  executable fire logits；
- event logits 仅在 hybrid action branch 内用于 policy log-prob。

不允许：

- 使用 `event_logit_delta` 作为 M3-S1 primary stop score；
- 直接从 executable action logits 计算 survival/event-time likelihood；
- 从 closed-mask 或 unobserved censored suffix rows 训练 executable fire logits；
- 从 stochastic fire samples 宣称 deterministic stopping success。

## 与 A7 Credit 的关系

A7 credit 可以保留为支撑：

```text
A7 credit head: Q_hold, Q_fire_once
M3-S1 stopping head: z_t, lambda_t, p(tau=t)
```

A7 credit 可以诊断 stop/fire 局部上是否优于 hold，但 M3-S1 的验收基于 grouped
survival/stopping behavior。A7 credit 不是权威 event-time model。

## P4 实现边界

最小实现应增加独立 stopping-head path，而不是复用 hybrid event head 作为 head body。

可能写入面：

- `python/rl/policy_algo/policies.py`
  - 增加可选 `hybrid_stopping_head` 或 `m3_stopping_head`；
  - 通过 policy 或 distribution helper methods 暴露 `stopping_logit` /
    `stopping_hazard_logit`；
  - 在 stats 中分离 event logits 与 stopping logits。
- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - 从 P2 选定的 grouped auxiliary pass 调用 stopping-head getter；
  - 不让 grouped loss 走 ordinary shuffled PPO minibatches。
- `python/rl/policy_algo/first_event_*`
  - 承载 grouped evidence，并计算 survival/stopping terms。
- `tests/hmoe/**` 与 `tests/training/**` 下 focused tests
  - 证明新 head 与 event logits 分离；
  - 证明 masks 继续权威；
  - 证明 closed-mask rows 不更新 executable fire logits。

P4 implementation 不得修改 reward magnitude、削弱 C2/ROE gates，或把 M2 变成依赖。

## 必需诊断

P4/P5 必须记录独立 stopping-head metrics：

- `m3s1/stop_logit_mean`；
- `m3s1/stop_logit_desirable_mean`；
- `m3s1/stop_logit_prewindow_mean`；
- `m3s1/hazard_desirable_mass`；
- `m3s1/hazard_early_mass`；
- `m3s1/no_event_mass`；
- `m3s1/boundary_cross_count`；
- `m3s1/boundary_cross_in_window_count`；
- `m3s1/closed_mask_stop_attempt_count`；
- `m3s1/event_logit_delta_diagnostic_mean`。

实现时 metric 名称可以调整，但类别必须保持分离。

## P3 验收门

P3 accepted，因为它：

- 选择独立 stopping/survival head 作为长期模型对象；
- 拒绝 action-logit reuse 作为 primary stopping score；
- 用 legal masked stop boundary 定义 deterministic deployment；
- 保留 action branch 为 execution adapter；
- 将 A7 credit 保持为 diagnostic/support；
- 命名 P4 写入面与 forbidden couplings，但不打开代码。

## 下一步

`M3S1-P4 Minimal Integration` 已通过。下一阶段是 P5 diagnostics 与 short training；在提出
learned-policy success claim 前，必须报告 boundary crossing、early mass、no-event mass、
closed-mask stop attempts 与 one-shot legality。
