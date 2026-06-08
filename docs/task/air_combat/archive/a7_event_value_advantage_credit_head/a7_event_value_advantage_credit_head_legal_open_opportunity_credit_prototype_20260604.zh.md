# A7 Legal-Open Opportunity Credit Prototype

状态：`2026-06-04`，`A7-EVC-Q Legal-Open Opportunity Credit Prototype` 作为
focused implementation slice pass。Learned-policy behavior 继续 held，直到后续有界
probe 运行。

父级：[README.zh.md](README.zh.md)。合同：
[legal-open opportunity credit contract](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.zh.md)。

## 已实现合同

Q 按 P 合同增加 direct legal-open quality-window positives：

```text
A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY
```

新 source 只在 no-release rows 仍是真实 `AuthorizedReady` / fire-open observation，
且满足 configured launch-window quality gate 时输出。它不投影 closed-mask rows，不重新打开
`FiredAssess`，也不依赖先采样 early accepted release。

## 代码更改

- `python/rl/policy_algo/first_event_hazard.py`
  - 增加 `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY`；
  - 为 `build_first_event_hazard_labels()` 增加
    `legal_open_quality_weight` 与
    `legal_open_quality_min_window_age_steps`；
  - 在 deadline fallback 后输出 legal-open quality positives，使 opportunity
    credit 启用时 source identity 不再记为 `DEADLINE`。
- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - 增加 `a7_event_credit_legal_open_quality_weight` 与
    `a7_event_credit_legal_open_quality_min_window_age_steps`；
  - 只在 A7 target path 上传递新 knobs；
  - 记录 legal-open quality source counts、positive counts 与 source advantage
    mean；
  - projection candidates 继续只限于 `SHADOW_QUALITY`。
- `python/rl/support/nonfinite_probe.py`
  - 在 patched train path 中镜像新的 A7 source metrics。
- Active A7 config
  - 在维护型 A7 active config 中启用 legal-open quality opportunity credit。

## Diagnostics

新增或扩展 logger tags：

- `a7/event_credit_legal_open_quality_weight`
- `a7/evc_src_legal_open_quality_count_mean`
- `a7/evc_src_legal_open_quality_positive_count_mean`
- `a7/evc_src_deadline_positive_count_mean`
- `a7/evc_src_shadow_positive_count_mean`
- `a7/evc_src_legal_open_quality_advantage_mean`

既有 projection tags 仍绑定到 shadow rows：

- `a7/evc_proj_candidate_count_mean`
- `a7/evc_proj_active_count_mean`
- `a7/evc_proj_unsupported_count_mean`

## Focused Tests

新增或更新测试证明：

- no-release legal-open quality rows 会成为
  `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY` positives；
- 缺少 `launch_window_open` evidence 时，新 source disabled；
- early accepted release 仍产生 `EARLY_ACCEPTED` negatives 和
  `SHADOW_QUALITY` repair candidates；
- legal-open quality rows 可不经 projection 直接训练 event-logit delta；
- raw shadow rows 仍是唯一 projection candidates；
- normal PPO 与 nonfinite-probe logging 暴露新 source metrics；
- active A7 config 暴露新 opportunity knobs。

## 验证

已运行命令：

```bash
python -m compileall -q python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py python/rl/support/nonfinite_probe.py tests/hmoe/test_a6_first_event_hazard.py tests/hmoe/test_hmoe_ppo_warmup.py tests/training/test_a6_event_value_active_config.py tests/training/test_air_combat_active_training_entries.py
pytest tests/hmoe/test_a6_first_event_hazard.py::A6FirstEventHazardTests::test_legal_open_quality_credit_marks_no_release_quality_rows_before_deadline tests/hmoe/test_a6_first_event_hazard.py::A6FirstEventHazardTests::test_legal_open_quality_credit_requires_launch_window_evidence tests/hmoe/test_a6_first_event_hazard.py::A6FirstEventHazardTests::test_shadow_quality_repair_adds_post_early_positive_credit_without_reopening_fire_mask tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_nonfinite_probe_records_a7_projection_credit_stats tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_a7_legal_open_quality_credit_aligns_event_logits_without_projection -q
pytest tests/hmoe/test_a6_first_event_hazard.py tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_hmoe_ppo_warmup.py tests/training/test_a6_event_value_active_config.py tests/training/test_air_combat_active_training_entries.py -q
```

观察结果：compileall 通过；focused Q tests 通过，`5 passed`；combined
A6/A7/HMoE/active-config pytest 通过，`55 passed`。

## 边界

- Q 不声明 learned-policy acceptance。
- 不 stage `experiments_tmp` artifacts。
- A3/A5 masks 与 post-launch suppression 继续权威。
- Raw `SHADOW_QUALITY` rows 仍不训练 direct event-logit delta。
- M2、HMoE redesign、missile/Pk/fuze/damage authority、`2v2`、self-play 与
  doctrine 继续 held。

## Dispatch Result

`A7-EVC-Q` 已实现 non-starved legal-open opportunity-credit path，并通过 focused
gates。下一有界工作是 `A7-EVC-R Short Opportunity Learned Evidence`。
