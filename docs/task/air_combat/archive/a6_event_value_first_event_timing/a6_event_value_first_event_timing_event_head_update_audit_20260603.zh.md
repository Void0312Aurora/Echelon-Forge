# A6 事件头更新强度审计

状态：`2026-06-03` `A6-EVT-J` 作为 update-strength audit 通过。A6 仍保持
held，因为本审计解释了 deterministic blocker，但它本身没有产出 accepted learned
policy。

父级：[README.zh.md](README.zh.md)。任务簇计划：
[a6_event_value_first_event_timing_task_clusters_20260603.zh.md](a6_event_value_first_event_timing_task_clusters_20260603.zh.md)。

## 问题

Deadline-bootstrap run 已经把持续正例标签接到既有 `hold/fire_once` event logit delta，
但 deterministic probe 仍然是 `0` requests。open-window event probability 仅从约
`0.247%` 移动到约 `0.494%`。

本审计要区分：A6 labels 是否没有接上，还是 labels 已接上但在当前 optimizer/head
scaling 下更新强度不足。

## 证据

既有 deadline run scalars：

| 信号 | 观测 | 含义 |
| --- | --- | --- |
| A6 labels | `a6/active_count_mean` 存在，first `237.5`，last `386.0`。 | Deadline labels 到达 PPO minibatches。 |
| 正例来源 | `a6/deadline_weight=1.0`，`a6/target_positive_frac` 到达 `1.0`。 | late open-window labels 是持续正例。 |
| Loss | `a6/hazard_loss` 非零，first `1.4603`，last `1.5972`。 | A6 loss 真实生效，而不是 inactive。 |
| Learning rate | `train/learning_rate=3e-5`，`train/kl_lr_mult=1.0` 全程不变。 | KL control 没有放大学习率。 |
| KL | `train/approx_kl` 很低：min 约 `0.00015`，max 约 `0.00169`。 | 训练很保守；不是因为 high KL early stop 卡死。 |
| Event delta callback | open-window delta 从 `10240` 步的 `-5.9625` 移到 `30720` 步的 `-5.3986`。 | event head 会移动，但离 deterministic argmax 还很远。 |
| Final probe | open-window delta 约 `-5.306`，probability max 约 `0.496%`，deterministic requests 为 `0`。 | learned policy 继续 held。 |

Focused probes：

| Probe | 结果 | 含义 |
| --- | --- | --- |
| Bias-only Adam，`128` steps，`lr=3e-5` | event delta 只移动 `+0.00769`。 | 当前短训尺度下，单独 event bias 不可能跨过 `-5` margin。 |
| Bias-only Adam，`128` steps，`lr=3e-4` | event delta 移动 `+0.07679`。 | 对这个最小情形，控制量是 step size，而不是 active-count 体量。 |
| HMoE policy，first-shot route，first gradient | shared action head gradient 非零；HMoE gradient 非零；optimizer groups 为 `shared=3e-5`、`hmoe=1.05e-5`。 | A6 loss 确实路由到 shared 与 routed heads。 |
| HMoE policy，`32` 个 hazard-only steps，当前 `lr=3e-5` | event delta 移动约 `+0.046` 到 `+0.050`。 | 当前 LR 可以移动高维 head，但速度很慢。 |
| HMoE policy，`128` 个 hazard-only steps，当前 `lr=3e-5` | event delta 移动约 `+0.254`。 | 这仍远低于从 final probe 的 `-5.3` 跨到 argmax 需要的约 `+5.3`。 |
| HMoE policy，`32` 个 hazard-only steps，`lr=3e-4` | event delta 移动约 `+0.61` 到 `+0.67`。 | 一个更强但有边界的 event-head update lane 是可信的下一 slice。 |

新增 regression / diagnostic test：

```bash
.venv/bin/python -m pytest -q tests/policy/test_event_head_update_contracts.py
```

结果：`2 passed`。

## 诊断

blocker 不是 label path 死掉。Deadline labels、A6 hazard loss、event logit delta accessor、
first-shot route、shared action head gradients 和 HMoE residual gradients 都是 live。

blocker 是 update strength 与 optimization ownership。Deterministic `fire_once` 要求 masked
event delta `fire - hold` 变成正值。Deadline run 最终接近 `-5.3`，所以 policy 至少需要约
`+5.3` 的 logit displacement，才能让 deterministic argmax 从 `hold` 切到 `fire_once`。
当前 `32768` 步 probe 只产生了这一幅度中的一小部分。

关键机制：

- A6 hazard loss 对 active labels 做平均。更多 deadline-positive samples 能提升状态覆盖，但当
  minibatch 已有足够 active labels 后，它们不会自动把总 gradient scale 乘上去。
- 在 Adam 下，单纯增大 hazard coefficient 不一定成比例增大 bias 的有效更新；主要控制项是
  optimizer learning rate，以及 competing gradients / clipping。
- HMoE residual path 有梯度，但被 residual scale / warmup 和 `hmoe_head_lr_scale=0.35`
  抑制。启动阶段 route-specific residual 尤其弱；即使 full gate，它也仍然只是 shared
  action head 上的低尺度 residual。
- event logits 仍是 shared action head 内的普通 rows 加低尺度 routed residual；没有专用的
  event-logit optimizer lane，也没有 event-value calibration surface。

## 建议

不要因为本审计 accept A6，也不要释放 M2。正确的下一步是一个有边界的 event-head
optimization lane，然后再考虑 sequence-native release vote。

建议新增任务簇：

`A6-EVT-K Event-Head Optimization Lane`

目标：

- 给 `hold/fire_once` event rows 一个足够强、可观测、受边界约束的更新路径，用于测试
  deterministic crossing，同时不削弱 A3/A5 masks。

候选实现顺序：

1. 为 event-logit parameters / rows 增加专用 optimizer group，覆盖 shared fire binary row
   和独立 hold logit row，并暴露 event-head LR multiplier 与 diagnostics。
2. 为 routed-residual event rows 增加对应通道，或仅在 combat first-shot route 上临时提高
   HMoE event-row LR / scale。
3. 保留 deadline/hazard labels，但增加 event-row gradient norm、event-row LR、train update
   前后 event delta、deterministic crossing margin 等 diagnostics。
4. 如果 event-head optimization 能强力移动 delta，但仍不能学习稳定首发 policy，再升级到
   event-value / advantage head。

下一 slice 的验收边界：

- A3/A5 合法性必须继续由 mask/state-machine 持有。
- 不得恢复 reward-only legality penalty 作为主修复。
- M2、`2v2`、self-play、missile physics、Pk、fuze 与 damage authority 继续 held。
- 短训 probe 必须对比 deterministic event probability、event mode、
  request/accept/release counts、rejected reasons 和 violation counts。

## Worker Packet

```md
status: pass
touched files:
- tests/policy/test_event_head_update_contracts.py
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_event_head_update_audit_20260603.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_event_head_update_audit_20260603.zh.md
- docs/task/air_combat/a6_event_value_first_event_timing/README.md
- docs/task/air_combat/a6_event_value_first_event_timing/README.zh.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_current_status_20260603.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_current_status_20260603.zh.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_task_clusters_20260603.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_task_clusters_20260603.zh.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_dispatch_queue_20260603.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_dispatch_queue_20260603.zh.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_acceptance_20260603.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_acceptance_20260603.zh.md
- docs/task/air_combat/README.md
- docs/task/air_combat/README.zh.md
commands/outcomes:
- .venv/bin/python -m pytest -q tests/policy/test_event_head_update_contracts.py -> 2 passed
- .venv/bin/python -m pytest -q tests/policy/test_event_head_update_contracts.py tests/policy/test_first_event_timing_contracts.py tests/policy/test_execution_policy_surface.py tests/policy/test_auxiliary_training_updates.py tests/training/test_event_timing_training_config_contracts.py tests/training/test_diagnostics_callback_contracts.py tests/runtime/air_combat/test_diagnostics_probe_contracts.py -> 73 passed, 9 subtests passed
- python -m compileall -q tests/policy/test_event_head_update_contracts.py -> passed
- git diff --check -- docs/task/air_combat tests/policy/test_event_head_update_contracts.py -> passed
remaining paths:
- 实现 A6-EVT-K event-head optimization lane。
behavior risks:
- 更高 event-head LR 可能导致 overfire，因此 A3/A5 masks 和 rejected-reason diagnostics 必须保持 active。
integration notes:
- 本审计只是 diagnostic evidence，不是 learned-policy acceptance。
```
