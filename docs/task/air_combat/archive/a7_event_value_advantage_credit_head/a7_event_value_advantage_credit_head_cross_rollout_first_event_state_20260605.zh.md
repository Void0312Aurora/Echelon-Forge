# A7 跨 Rollout First-Event Credit State

状态：`2026-06-05` implementation pass；learned-policy behavior 仍 held，等待新的
观察训练。

父级：[README.zh.md](README.zh.md)。英文权威页：
[a7_event_value_advantage_credit_head_cross_rollout_first_event_state_20260605.md](a7_event_value_advantage_credit_head_cross_rollout_first_event_state_20260605.md)。

## 目的

`A7-EVC-W` 已证明 first-event credit target 是 episode-level function，但实现却在
PPO rollout-local chunks 上求值。当 stochastic exploration 在 quality window 前
accepted release，而 quality window 落在后续 rollout 时，完整 episode 上存在的
`shadow_quality` positives 会从训练标签中消失。

`A7-EVC-X` 修复这一 training-loop contract：在 PPO rollouts 之间携带 per-env
episode first-event context，用既有 label builder 在带前缀上下文的序列上求值，再只把当前
rollout slice 写回 buffer。

## 实现

代码变更：

- `python/rl/policy_algo/ppo_adaptive_kl.py` 增加 `_A7FirstEventRolloutRow` 和
  per-env `_a7_first_event_rollout_history`。
- Cross-rollout path 只在 A7 credit labels、A6 hazard targets 未启用、且存在
  `launch_window_open` evidence 时生效。
- Label attach 时同时构造 rollout-local labels 与 same-episode carried-prefix
  labels；写入 rollout buffer 的只有当前 rollout slice。
- 当 `env_episode_id_after_rollout` 显示 env 已进入新 episode 时 reset history，
  包括 episode 在 rollout 最后一步结束的情况。
- 正常 PPO path 与 `NonFiniteTrainingProbe` 同步记录新的 A7 diagnostics：
  - `a7/evc_cross_rollout_context_rows`
  - `a7/evc_carried_shadow_pending_envs`
  - `a7/evc_carried_shadow_positive_count_mean`
  - `a7/evc_cross_rollout_first_event_count_mean`

该修复不改变 A3/A5 runtime legality masks、event action suppression、missile
authority、reward shaping 或 policy action surface。

## 验证

本 slice 已运行 focused gates：

```bash
python -m compileall -q python/rl/policy_algo/ppo_adaptive_kl.py python/rl/support/nonfinite_probe.py tests/hmoe/test_hmoe_ppo_warmup.py
pytest tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_a7_cross_rollout_first_event_state_recovers_shadow_quality_after_boundary -q
pytest tests/hmoe/test_a6_first_event_hazard.py -q
python -m compileall -q python/rl/policy_algo/ppo_adaptive_kl.py python/rl/policy_algo/first_event_hazard.py python/rl/support/nonfinite_probe.py tests/hmoe/test_a6_first_event_hazard.py tests/hmoe/test_hmoe_ppo_warmup.py
pytest tests/hmoe/test_hmoe_ppo_warmup.py -q
```

观察结果：

- compileall：pass。
- 新 cross-rollout regression：`1 passed`。
- A6 first-event hazard tests：`20 passed`。
- HMoE/PPO warmup tests：`16 passed`。

新 regression 构造一条 512-step episode：index `5` accepted release、index `281`
开始 launch-window open，并按 `128` step chunks 切分。完整 episode labels 含
`231` 个 `shadow_quality` positives。无 carried state 的 rollout-local chunk labels
含 `0` 个 shadow positives。带 carried-state 的 attach path 与完整 episode labels
逐字段一致，并在最后一个 chunk 恢复 `128` 个 carried shadow positives。

## 边界

X 是 focused implementation repair。它证明 PPO rollout boundary 不再在覆盖场景中删除
episode-level first-event credit。它尚不验收 A7 learned behavior：deterministic
首发、stochastic early-release probability、one-shot legality 与 event-advantage sign
仍需要在本修复后重新进行 bounded learned-policy observation。

## 下一步

用修复后的 training-loop contract 运行一次短 A7 observation，并与 V/W 对照：

- `a7/event_credit_active_count_mean`
- `a7/evc_src_shadow_positive_count_mean`
- `a7/evc_carried_shadow_positive_count_mean`
- deterministic first-release timing
- stochastic early-release timing 与 one-shot violations
