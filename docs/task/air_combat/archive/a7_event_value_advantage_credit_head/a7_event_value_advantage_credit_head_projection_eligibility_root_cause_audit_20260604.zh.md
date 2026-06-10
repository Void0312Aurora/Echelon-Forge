# A7 Projection Eligibility Root-Cause Audit

状态：`2026-06-04`，`A7-EVC-O Projection Eligibility Root-Cause Audit` pass。
Projected legal-open path 已实现，且在 `shadow_quality` rows 存在时可以 activate；
但 N learned run 让该 branch 饥饿，因为训练 rollout 没有 accepted early releases，
因此没有产生 `shadow_quality` projection candidates。

父级：[README.zh.md](README.zh.md)。前序证据：
[short projection learned evidence](a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.zh.md)。

## 问题

`A7-EVC-N` 显示：

- projection 已启用：`a7/evc_proj_enabled=1.0`；
- ordinary A7 event-credit 是 live 的：
  step `32768` 的 `a7/event_credit_active_count_mean=450.0`；
- projected active rows 保持 `0.0`；
- projected unsupported rows 也保持 `0.0`。

因此审计问题比“projection 失败”更窄：是没有 shadow candidate，是 candidate 被
projection eligibility 拒绝，还是 train/probe handoff 丢了字段？

## 代码路径发现

当前 `AdaptiveKLPPO._first_event_credit_loss()` 只对 active 且 first-event source
为 `A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY` 的 rows 启用 projection。这些 rows 只有在
early accepted first release 关闭 ordinary fire mask，且后续出现 launch-window
quality evidence 后，才由 `build_first_event_hazard_labels()` 生成。

因此 M projection 是 post-early-release repair path，不是通用 quality-window
opportunity-credit path。

## 新增诊断

本切片只增加 source/candidate diagnostics，不改变训练目标：

- `FirstEventCreditLoss.projection_candidate_count`
- `FirstEventCreditLoss.source_shadow_count`
- `FirstEventCreditLoss.source_deadline_count`
- `FirstEventCreditLoss.source_early_accepted_count`
- `FirstEventCreditLoss.source_prewindow_count`

Logger tags：

- `a7/evc_proj_candidate_count_mean`
- `a7/evc_src_shadow_count_mean`
- `a7/evc_src_deadline_count_mean`
- `a7/evc_src_early_count_mean`
- `a7/evc_src_pre_count_mean`

这些 tags 同时记录在 normal PPO train path 和 active A7 config 使用的
`NonFiniteTrainingProbe` patched train path 中。

## N 证据复核

TensorBoard from
`experiments_tmp/a7_projection_credit_32k_20260604_r3/logs/PPO_1`：

| Scalar | Observation |
| --- | --- |
| `diag/a5_release_executed_count` | 3 个 diagnostic snapshots 中始终为 `0.0` |
| `diag/a5_fire_once_accepted_count` | 3 个 diagnostic snapshots 中始终为 `0.0` |
| `diag/a5_fire_once_requested_count` | 只有 step `30720` 非零，value `1.0` |
| `diag/a5_fire_once_rejected_count` | 只有 step `30720` 非零，value `1.0` |
| `a7/evc_proj_active_count_mean` | 31 条 train records 中始终为 `0.0` |
| `a7/evc_proj_unsupported_count_mean` | 31 条 train records 中始终为 `0.0` |
| `a7/event_credit_active_count_mean` | live；final value `450.0` |
| `a7/event_credit_target_positive_frac` | live；final value `0.599887` |

解释：learned run 有 ordinary event-credit labels，但已记录的训练 rollout 没有 accepted
releases。没有 accepted early release，当前 `shadow_quality` projection source 就不会生成。

## Probe 重构

使用同一个 label builder 重构 N probe CSVs，输入为：

- `engagement_state`、`fire_mask`、`fire_once_accepted` 与 `episode`；
- launch window 用 `target_range_track_m` in `[8000, 30000]` 且
  `target_track_age_s <= 5` 近似；
- A7 active config weights：
  prewindow `0.4`、early accepted `1.0`、deadline `1.0`、
  shadow-quality `1.0`。

| Probe | Active labels | Positive labels | Source counts |
| --- | ---: | ---: | --- |
| deterministic N | `1880` | `1080` | `deadline=1080`, `prewindow=800` |
| stochastic N | `3291` | `3280` | `shadow_quality=3280`, `prewindow=8`, `early_accepted=3` |

解释：early stochastic release 真正发生时，label builder 可以产生数千个
`shadow_quality` rows。N training run 没有激活 projection，不是因为 projection helper
拒绝 supported rows，而是因为训练 rollout 没有产生这些 candidates。

## 根因

M projection path 依赖其试图修复的失败模式。它只有在 policy 已采样 early accepted
release 后，才提供 legal-open projected positives。若 rollout 没有 accepted release，
A7 会退回 ordinary deadline/prewindow labels，projection branch 就是 no-op。

这解释了 N 的分裂：

- deterministic/probe no-release trajectories 暴露 deadline positives，但没有 projection
  candidates；
- stochastic/probe early-release trajectories 暴露大量 shadow candidates；
- N training diagnostics 没有 accepted release，因此 projected active rows 保持 zero。

## 已排除

- Unsupported observation layout：不是 primary。N 中
  `a7/evc_proj_unsupported_count_mean=0.0`。
- Projection implementation path：不是 primary。M focused tests 可以 activate projected
  rows 并更新 event logits。
- Launch-window gate disabled：不是 primary。active config 中
  `a6_first_event_launch_window_enabled=true`，probe reconstruction 也能用同一
  launch-window settings 生成 deadline/shadow labels。
- Ordinary A7 labels 缺失：不是 primary。ordinary event-credit active counts 与
  positive fractions 是 live 的。

## 下一方向

`A7-EVC-P Legal-Open Opportunity Credit Contract` 应定义不依赖 early accepted release
的 credit source。可能合同是：

- 保留 `shadow_quality` projection 作为 early-release trajectories 的 repair path；
- 为 no-release quality-window rows 增加 legal-open opportunity source，使
  projection/value-to-policy coupling 在 policy 已经采样 failure mode 前也能收到 positive
  legal-open evidence；
- 保持 A3/A5 masks 权威，不把 raw closed-mask rows 直接对齐到 event logits。

## 验证

已运行命令：

```bash
python -m compileall -q python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py python/rl/support/nonfinite_probe.py tests/policy/test_auxiliary_training_updates.py
pytest tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_nonfinite_probe_records_a7_projection_credit_stats tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_a7_shadow_quality_projection_aligns_projected_legal_open_event_logits -q
rg -n '<stale O-next current-status patterns>' docs/task/air_combat
git diff --check -- docs/task/air_combat python/rl tests/policy tests/training
pytest tests/policy/test_first_event_timing_contracts.py tests/policy/test_event_head_update_contracts.py tests/policy/test_auxiliary_training_updates.py tests/training/test_event_timing_training_config_contracts.py tests/training/test_air_combat_training_entry_contracts.py -q
```

观察结果：compileall 通过；focused projection/nonfinite tests 通过，`2 passed`；
stale-current-status scan 没有发现 O 仍为 planned 的当前状态残留；diff check 通过；
combined A6/A7/HMoE/active-config pytest 通过，`52 passed`。

## Worker Packet

```md
status: pass; spawned P contract
touched files:
- python/rl/policy_algo/first_event_hazard.py
- python/rl/policy_algo/ppo_adaptive_kl.py
- python/rl/support/nonfinite_probe.py
- tests/policy/test_auxiliary_training_updates.py
- docs/task/air_combat/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_projection_eligibility_root_cause_audit_20260604.zh.md
commands/outcomes:
- TensorBoard N scalar review -> logged train diagnostics 中无 accepted release；projection active/unsupported 均为 zero
- Probe CSV reconstruction -> deterministic source 是 deadline/prewindow；stochastic source 包含 3280 个 shadow_quality positives
- compileall -> pass
- focused projection/nonfinite pytest -> 2 passed
- post-sync combined pytest -> 52 passed
- docs/code diff check -> pass
remaining paths:
- A7-EVC-P Legal-Open Opportunity Credit Contract
behavior risks:
- projection-only repair 在 policy 未采样 early accepted release 时 candidate-starved
- ordinary deadline positives 仍不足以产出 deterministic quality-window release
integration notes:
- experiments_tmp remains unstaged
- A3/A5 legality remains authoritative
- M2, HMoE redesign, missile authority, 2v2, self-play, and doctrine remain held
```
