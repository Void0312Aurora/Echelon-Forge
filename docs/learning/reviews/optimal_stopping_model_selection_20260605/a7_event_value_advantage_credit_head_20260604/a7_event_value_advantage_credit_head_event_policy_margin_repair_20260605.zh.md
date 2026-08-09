# A7 Event-Policy Margin 修复

状态：`2026-06-05` 已完成为结构修复与短训 learned-policy 证据；结论 held。

父级：[README.zh.md](README.zh.md)。

## 目的

`A7-EVC-Z` 已隔离剩余 execution breakpoint：labels 存在，credit head 能离线拟合符号
切分，并且当 event logits 收到直接有符号监督时，actor 能分离 timing windows。失败链路是
policy contract：

```text
labels -> credit head -> tiny detached advantage -> event-logit delta
```

本 slice 实现该诊断要求的有边界修复：为 ordinary legal-open positive rows 与 prewindow
negative rows 提供直接有符号 event-policy margin，让 actor/event path 获得训练信号；credit
head 保留为 value support，而不再作为 deterministic event-mode crossing 的唯一教师。

## 已实现修复

代码改动：

- `python/rl/policy_algo/first_event_hazard.py`
  - 增加 `FirstEventPolicyMarginLoss`；
  - 增加 `compute_first_event_policy_margin_loss()`；
  - 使用 signed squared hinge 训练 `event_logit_delta`：
    positive target 将 fire-logit delta 推到 margin 之上，negative target 将其推到
    negative margin 以下；
  - 保留 first-event mass caps，并支持 `policy_active` masking，使 raw closed-mask
    `shadow_quality` rows 不会直接写入 event logits。
- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - 增加 `a7_event_policy_margin_coef`、
    `a7_event_policy_margin`、
    `a7_event_policy_projection_margin_coef`、
    `a7_event_policy_separate_update_enabled`、
    `a7_event_policy_separate_update_max_grad_norm` 与
    `a7_event_policy_separate_update_steps`；
  - 接入 `_first_event_policy_margin_loss()`；
  - 增加独立 actor/event update lane，只更新 `action_net`、`hybrid_event_head` 与
    `mlp_extractor.policy_net`；
  - margin lane 不更新 `hybrid_event_credit_head`。
- `train.py`
  - 保持 hybrid `fire_weapon` 初始 bias 为保守的 `-6.0`，包括 A7
    event-policy margin path 启用时。
- A7 active configs：
  - 关闭旧的弱 detached delta-align coefficients；
  - 在 shaped 与 state-completed 两个 A7 active config 中启用 event-policy margin
    coefficients 与独立 actor/event update steps。

Runtime A3/A5 legal masks、fire-state machine、shot budget 与 one-shot discipline
均未改变。

## Focused Validation

Focused checks 已通过：

```bash
python -m compileall -q train.py python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py
python -m json.tool examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json
python -m json.tool examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_state_completed_world_batch_probe_v1.json
pytest tests/training/test_event_timing_training_config_contracts.py -q
pytest tests/policy/test_event_head_update_contracts.py -q
pytest tests/policy/test_auxiliary_training_updates.py -q
pytest tests/policy/test_execution_policy_surface.py -q
git diff --check -- <A7 event-policy margin write set>
```

Observed outcomes：

- active-config tests：`7 passed`；
- event-head update-strength tests：`7 passed`；
- HMoE PPO warmup tests：`18 passed`；
- HMoE policy tests：`32 passed`；
- compile、JSON 与 diff whitespace checks 均通过。

新增测试覆盖 positive/negative margin gradient signs、projection margin routing、
separate-update behavior，以及 A7 margin 不应放宽初始 fire prior 的 safe-bias contract。

safe-bias reversal 的 post-correction checks：

```bash
python -m compileall -q train.py python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py python/rl/policy_algo/policies.py
pytest tests/policy/test_execution_policy_surface.py::ExecutionPolicySurfaceTests::test_safe_action_bias_initializes_air_combat_hybrid_switch_logits tests/policy/test_event_head_update_contracts.py tests/training/test_event_timing_training_config_contracts.py::EventTimingTrainingConfigContractTests::test_a7_event_credit_config_exposes_credit_head_without_reusing_a6_hazard_loss -q
pytest tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_a7_policy_margin_loss_projects_shadow_rows_into_policy_path tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_a7_separate_policy_margin_update_only_writes_event_policy_path tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_a7_shadow_quality_projection_aligns_projected_legal_open_event_logits tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_a7_legal_open_quality_credit_aligns_event_logits_without_projection -q
```

Observed outcomes：compile passed；targeted safe-bias/A7 config/update-strength
checks 为 `9 passed`；A7 policy-margin warmup checks 为 `4 passed`。

## 短训证据

本轮使用两个 8192-step short runs 做有边界前后对照。产物保留在 `experiments_tmp`，不作为
staging 输入。

Run directories：

```text
experiments_tmp/a7_event_policy_margin_8k_20260605_r1
experiments_tmp/a7_event_policy_margin_8k_20260605_r2
```

主 r2 temporary train config：

```text
experiments_tmp/a7_short_configs/a7_event_policy_margin_8k_20260605_r2.json
```

Probe summary：

| Run | Probe | Episodes | Accepted releases | Release steps | Quality-window fire probability mean | Prewindow fire probability mean | Open-window logit delta mean |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| r1 | deterministic | `2` | `0` | `[]`, `[]` | `0.00391` | `0.00391` | `-5.5409` |
| r1 | stochastic | `4` | `4` | `[6]`, `[147]`, `[273]`, `[18]` | `0.0` | `0.00389` | `-5.5445` |
| r2 | deterministic | `2` | `0` | `[]`, `[]` | `0.11261` | `0.11262` | `-2.0643` |
| r2 | stochastic | `4` | `4` | `[6]`, `[51]`, `[11]`, `[18]` | `0.0` | `0.11250` | `-2.0655` |

r2 现在解释为被否定的 diagnostic，而不是 accepted repair：quality/open-window fire
probability 提升约一个数量级，但 prewindow fire probability 也一起提升。startup prior
从旧 safe-bias 区域的约 `-5.5` 推到约 `-2.06` 后，会让 stochastic policy 在
legal-quality window 形成前几乎必然早射。

Behavior 仍未 accepted：

- deterministic probing 仍记录 `0` accepted releases；
- stochastic probing 在观测 probe 中保持 authorized one-shot release discipline；
- stochastic releases 仍是 early/prewindow samples，而不是 learned quality-window timing；
- r2 同时抬高了 prewindow 与 quality fire probability，因此还没有学到所需 timing
  discriminator。

### Conservative-Bias Follow-Up

safe-bias reversal 后，额外运行了一次 8192-step short run，用于验证当前保守 startup
prior：

```text
experiments_tmp/a7_event_policy_margin_safe_bias_8k_20260605_r1
experiments_tmp/a7_short_configs/a7_event_policy_margin_safe_bias_8k_20260605_r1.json
```

Probe summary：

| Run | Probe | Episodes | Accepted releases | Release steps | Quality-window fire probability mean | Prewindow fire probability mean | Open-window logit delta mean |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| safe-bias r1 | deterministic | `2` | `0` | `[]`, `[]` | `0.00310`, `0.00308` | `0.00310`, `0.00308` | `-5.7735`, `-5.7804` |
| safe-bias r1 | stochastic | `4` | `3` | `[84]`, `[407]`, `[]`, `[18]` | `0.0`, `0.00308`, `0.00308`, `0.0` | `0.00310`, `0.00308`, `0.00308`, `0.00310` | `-5.7740`, `-5.7807`, `-5.7807`, `-5.7731` |

TensorBoard review：

- `a7/event_credit_active_count_mean` 在训练中段是 live 的：step `3072` 为
  `718`，step `4096` 为 `762`；但 step `8192` 结束时降为 `0`。
- `a7/evc_src_legal_open_quality_count_mean` 曾短暂恢复：step `3072` 为
  `231`，step `4096` 为 `128`；随后回到 `0`。
- `a7/event_credit_advantage_mean` 最终为约 `0.7148` 的正值，但该最终符号是在
  active event-credit rows 为 `0` 时记录的。
- PPO 末端移动幅度很小：`train/approx_kl=0.0006695`，
  `train/policy_gradient_loss=-0.0002126`。

该 follow-up 在窄意义上确认 safe-bias fix 生效：event fire probability 不再跳回被否定的
`~0.112` 区域，且 stochastic execution 没有破坏 one-shot discipline。但它仍未解决
learned behavior：deterministic probe 继续 `hold`，stochastic releases 来自低单步概率的
累积 hazard，而不是 learned quality-window timing discriminator。所有 probe episode 都没有
effects 或 damage，最终 target health 保持 `40.0`。

## 解释

本 slice 修复了 Z 确认的 implementation-level 问题：actor 现在收到直接有符号
event-policy margin，而不是只依赖 tiny detached credit advantage。短训同时暴露了第二个
structural fault：放宽 startup fire prior 不是探索，而是 label starvation。当
`fire_weapon` bias 为 `-2.0` 且 hold 为 `0.0` 时，单步 stochastic fire probability
约为 `0.119`，因此 32-step window 内至少一次 pre-window release 的概率约为 `0.983`。
这会把 ordinary legal-open positives 转成 early-accepted/shadow-quality rows，迫使
actor 主要通过更弱的 projection path 学习。

它没有解决 A7。剩余 blocker 已转移为：

```text
direct signed margin exists
  -> relaxed startup prior makes stochastic samples fire early
  -> deterministic argmax still stays below the fire threshold
  -> legal-open actor labels are starved online
```

当前证据不再支持“credit 完全无法移动 actor”。更接近的问题是 policy-threshold 与 online
sampling-distribution structure：policy 能被推到 stochastic one-shot firing，但训练分布必须
保持低 prewindow hazard，才能让 legal-open quality labels 持续进入 actor margin。

Conservative-bias follow-up 进一步缩小了问题边界：恢复低 prewindow hazard 能避免明显的
label-starvation failure，但也让 actor 回到极低 event-fire probability 区间。训练中段的
label spike 说明 credit source 并非永久断开；最终 active rows 塌回 `0` 则指向剩余 blocker：
online sampling/update distribution 无法维持 legal-open actor labels 足够久，从而无法跨过
deterministic event-mode selection。

## 状态

`A7-EVC-AA` 作为结构修复与短训观察通过。A7 继续 held。验收仍要求 deterministic 在 quality
window 内 one-shot release、stochastic prewindow hazard 受控，并保持 A3/A5 legality。
