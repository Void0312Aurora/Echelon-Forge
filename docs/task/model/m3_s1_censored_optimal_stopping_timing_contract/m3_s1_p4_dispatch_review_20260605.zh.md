# M3-S1 P4 Dispatch Review

状态：`2026-06-05` pass。P4-A、P4-B 与 P4-C 作为有边界 implementation slices
验收；P5 diagnostics and short training 已由
[P5 dispatch plan](m3_s1_p5_dispatch_plan_20260605.zh.md) 打开。

父项目：[M3-S1 Censored Optimal-Stopping Timing Contract](README.zh.md)。

## 验收范围

| Slice | Status | Touched surface | Evidence | 不证明 |
| --- | --- | --- | --- | --- |
| `M3S1-P4A Policy Head Skeleton` | pass | `python/rl/policy_algo/policies.py`；focused `tests/policy/test_execution_policy_surface.py` entries | optional independent `m3_stopping_head`、getter helpers、独立 `m3s1/*` stats、focused policy tests | PPO integration、threshold calibration 或 grouped mass learning |
| `M3S1-P4B Grouped Evidence/Loss Skeleton` | pass | `python/rl/policy_algo/m3s1_grouped_stopping.py`；`tests/policy/test_grouped_stopping_loss_contracts.py` | grouped evidence carrier 加 pure survival/event-mass loss helper 和 tests | rollout-buffer sidecar、PPO auxiliary pass 或 training config |
| `M3S1-P4C PPO Auxiliary Integration` | pass | `python/rl/policy_algo/ppo_adaptive_kl.py`；`tests/policy/test_auxiliary_training_updates.py` | M3-S1 sidecar 在 buffer flattening 前构建；grouped auxiliary update 在 base PPO loop 后调用 independent stopping head；focused integration tests | P5 short training、threshold calibration 或 learned-policy success |

## 本地验证

```bash
python -m py_compile python/rl/policy_algo/policies.py \
  python/rl/policy_algo/m3s1_grouped_stopping.py \
  tests/policy/test_grouped_stopping_loss_contracts.py
python -m pytest tests/policy/test_execution_policy_surface.py \
  tests/policy/test_grouped_stopping_loss_contracts.py -q
python -m pytest tests/policy/test_grouped_stopping_loss_contracts.py \
  tests/policy/test_execution_policy_surface.py \
  tests/policy/test_auxiliary_training_updates.py -q
python -m pytest tests/policy/test_event_head_update_contracts.py \
  tests/training/test_event_timing_training_config_contracts.py -q
git diff --check -- python/rl/policy_algo/policies.py \
  tests/policy/test_execution_policy_surface.py \
  python/rl/policy_algo/m3s1_grouped_stopping.py \
  tests/policy/test_grouped_stopping_loss_contracts.py \
  docs/task/model/m3_s1_censored_optimal_stopping_timing_contract
```

结果：

- `py_compile`：pass。
- focused pytest：`44 passed`。
- M3-S1/HMoE integration pytest：`64 passed`。
- A6/A7 adjacent regression pytest：`14 passed`。
- `git diff --check`：pass。

## 验收注记

- P4-A 让新 stopping score 与 executable hybrid event logits 保持独立。action branch
  与既有 fire mask 继续权威。
- P4-A 默认通过 `m3_stopping_head_lr_scale = 0.0` 关闭，因此只有显式启用该 head
  时才改变策略表面。
- P4-B 按 complete ordered groups 计算 `lambda_t = M_t * sigmoid(z_t)`、survival、
  event mass、desirable-window mass、early mass、no-event mass 与 early-prefix survival。
- P4-B 保留 group structure，且明确不是 row-wise BCE helper。
- P4-B 当前将 `support_horizon` 解释为 `row_indices` 坐标，将 `censor_step`
  解释为 `step_indices` 坐标。P4-C 必须有意保留或显式转换这一约定。
- P4-C 在 M3-S1 sidecar 中保留 full episode chunks，包括 closed-mask rows，并用
  `legal_mask` 保持 hazard 只在 executable rows 上生效。
- P4-C 保持 base PPO minibatch flow 不变，并在 ordinary PPO loop 后以独立 auxiliary
  optimizer step 运行 grouped stopping objective。
- P4-C 默认通过 `m3s1_grouped_stopping_coef = 0.0` 关闭；同时要求 policy 暴露
  `get_m3_stopping_logits()`。

## 残余

- P5 已在 [P5 dispatch plan](m3_s1_p5_dispatch_plan_20260605.zh.md) 下 active，
  且必须运行 diagnostic probes 与 short training，之后才能提出 behavior claim。
- P5 必须报告 deterministic boundary crossing、cumulative early mass、no-event mass、
  one-shot legality 与 closed-mask stop attempts。
- Threshold calibration 与 active training config promotion 不属于 P4。
- P4 未修改 reward magnitude、C2/ROE gate、action mask 或 one-shot legality behavior。
