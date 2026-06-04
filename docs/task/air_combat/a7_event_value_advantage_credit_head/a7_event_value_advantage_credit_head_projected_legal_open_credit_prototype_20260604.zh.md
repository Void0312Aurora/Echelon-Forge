# A7 Projected Legal-Open Credit Prototype

状态：`2026-06-04`，`A7-EVC-M` implementation pass；learned-policy behavior
尚未评估。

父级：[README.zh.md](README.zh.md)。英文规范页：
[a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.md](a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.md)。

## 目的

`A7-EVC-L` 选择 legal-state projection，是因为 repaired `shadow_quality` positives
位于 post-release closed-mask observations，而 policy coupling 需要 legal-open
observations 上的 positive `fire_once` credit。M 将该合同实现为 focused prototype。

## 实现

- 新增 `python/rl/policy_algo/first_event_projection.py`。
  - 只投影 `air_combat_c2_roe_v1` observations 的 A3/A5 event-legality surface。
  - 改写 `mission[5]`、`mission[6]`、`mission[14]`、`mission[15]`、
    `mission[16]`、`mission[17]`、`mission[19]`，以及可选
    `event_action_mask` 和 `fire_mask`。
  - 保留 contacts、contact history、geometry、instruments、RWR、proprioception
    与无关 policy inputs。
  - 拒绝 unsupported mission layouts，并报告 unsupported rows，不静默训练
    closed-mask alignment。
- 扩展 `AdaptiveKLPPO._first_event_credit_loss()`。
  - Raw `shadow_quality` rows 继续排除出 ordinary delta alignment。
  - 当 `a7_event_credit_legal_projection_enabled=true` 时，带 contact evidence 的
    shadow rows 进入 projected legal-open observation pass。
  - Projected rows 训练 positive value，并可训练 projected event-logit delta alignment。
- 新增 A7 projection knobs：
  - `a7_event_credit_legal_projection_enabled`
  - `a7_event_credit_projection_value_coef`
  - `a7_event_credit_projection_delta_align_coef`
- 新增 short logger stats：
  - `a7/evc_proj_active_count_mean`
  - `a7/evc_proj_unsupported_count_mean`
  - `a7/evc_proj_advantage_mean`
  - `a7/evc_proj_delta_mean`
- 在 `NonFiniteTrainingProbe` 中同步记录这些 projection stats；active A7 config
  使用的正是它 patch 过的 `train()` path。
- Active A7 config 已启用 projection。

## 验证

已运行命令：

```bash
python -m compileall -q python/rl/policy_algo/first_event_projection.py python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py
pytest tests/hmoe/test_a6_first_event_hazard.py -q
pytest tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_a7_shadow_quality_projection_aligns_projected_legal_open_event_logits -q
pytest tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_hmoe_ppo_warmup.py -q
python -m json.tool examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json
pytest tests/training/test_a6_event_value_active_config.py tests/training/test_air_combat_active_training_entries.py -q
pytest tests/hmoe/test_a6_first_event_hazard.py tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_hmoe_ppo_warmup.py tests/training/test_a6_event_value_active_config.py tests/training/test_air_combat_active_training_entries.py -q
```

观察结果：

- compileall：pass。
- `tests/hmoe/test_a6_first_event_hazard.py`：`17 passed`。
- focused projected-loss PPO test：`1 passed`。
- HMoE/PPO focused group：`15 passed`。
- active config and active-entry group：`19 passed`。
- A7 JSON parse：pass。
- Docs sync 后 combined focused rerun：`51 passed`。

## 边界

M 未运行 learned-policy wave，也不验收 A7 behavior。它证明 projection path 已存在，
遵守 A3/A5 legality，让 raw closed-mask `shadow_quality` 继续不进入直接 delta alignment，
并能在 focused PPO test 中产生 projected legal-open positive event-logit pressure。

## 下一步

下一有界切片是 `A7-EVC-N Short Projection Learned Evidence`：运行短 learned-policy probe，
并比较 deterministic release timing、stochastic first-release timing、one-shot violations、
projected active count、projected advantage sign 与 projected delta sign。
