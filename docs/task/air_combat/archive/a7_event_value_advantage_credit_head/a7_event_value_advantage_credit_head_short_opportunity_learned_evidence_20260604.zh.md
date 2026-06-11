# A7 Short Opportunity Learned Evidence

状态：`2026-06-04`，`A7-EVC-R Short Opportunity Learned Evidence` 作为有效证据
pass，但 learned-policy outcome 继续 held。Direct legal-open opportunity credit 在
learned train path 中不再 candidate-starved，但最终 policy 仍没有达到首发时机验收门。

父级：[README.zh.md](README.zh.md)。Prototype：
[a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.zh.md](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.zh.md)。

## 范围

本切片在 `A7-EVC-Q` 后运行维护中的 A7 active config，并用 deterministic 与
stochastic 模式 probe final policy。问题是：direct legal-open quality opportunity
credit 是否相对 `A7-EVC-N Short Projection Learned Evidence` 改变 learned behavior。

本切片不释放 M2、HMoE redesign、missile physics、Pk/fuze/damage authority、`2v2`、
self-play 或真实 doctrine claims。`experiments_tmp` artifacts 不 stage。

## 有效训练运行

Run：
`experiments_tmp/a7_legal_open_opportunity_32k_20260604_r1`

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a7_legal_open_opportunity_32k_20260604_r1 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260701
```

Final model：
`experiments_tmp/a7_legal_open_opportunity_32k_20260604_r1/final_model.zip`

TensorBoard scalar check 来自
`experiments_tmp/a7_legal_open_opportunity_32k_20260604_r1/logs/PPO_1/`：

| Scalar | Final step | Final value | Max / nonzero records |
| --- | ---: | ---: | ---: |
| `a7/event_credit_loss` | `32768` | `0.312856` | max `2.089820`; `23/31` |
| `a7/event_credit_active_count_mean` | `32768` | `512.0` | max `512.0`; `23/31` |
| `a7/event_credit_target_positive_frac` | `32768` | `0.648438` | max `0.909919`; `14/31` |
| `a7/event_credit_advantage_mean` | `32768` | `-0.850262` | max `-0.050440`; `31/31` |
| `a7/evc_src_legal_open_quality_count_mean` | `32768` | `332.0` | max `450.0`; `13/31` |
| `a7/evc_src_legal_open_quality_positive_count_mean` | `32768` | `332.0` | max `450.0`; `13/31` |
| `a7/evc_src_legal_open_quality_advantage_mean` | `32768` | `-0.850221` | max `0.0`; `13/31` |
| `a7/evc_src_deadline_positive_count_mean` | `32768` | `0.0` | max `0.0`; `0/31` |
| `a7/evc_src_shadow_positive_count_mean` | `32768` | `0.0` | max `112.5`; `1/31` |
| `a7/evc_proj_candidate_count_mean` | `32768` | `0.0` | max `112.5`; `1/31` |
| `a7/evc_proj_active_count_mean` | `32768` | `0.0` | max `112.5`; `1/31` |
| `a6/event_fire_prob_mean_open` | `30720` | `0.344788` | max `0.344788`; `3/3` |
| `a6/event_fire_prob_max_open` | `30720` | `0.346663` | max `0.346663`; `3/3` |
| `diag/pi_event_mode_fire_frac` | `30720` | `0.0` | max `0.0`; `0/3` |
| `rollout/ep_rew_mean` | `32768` | `228.113190` | max `527.523560`; `23/23` |

解释：Q 修复了 direct legal-open opportunity credit 的 source-starvation 问题。
legal-open quality positives 已进入真实 train loss，包括最终 update。但这些 positive rows
上的 event-credit advantage 仍为负，deterministic event mode 也没有翻到 `fire_once`。

## Probe 命令

Deterministic：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a7_legal_open_opportunity_32k_20260604_r1/final_model.zip \
  --episodes 1 \
  --seed 20260702 \
  --max_steps 2400 \
  --json_out experiments_tmp/a7_legal_open_opportunity_32k_20260604_r1/a7_opportunity_deterministic_probe.json \
  --csv_out experiments_tmp/a7_legal_open_opportunity_32k_20260604_r1/a7_opportunity_deterministic_probe.csv
```

Stochastic：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a7_legal_open_opportunity_32k_20260604_r1/final_model.zip \
  --episodes 3 \
  --seed 20260702 \
  --max_steps 2400 \
  --stochastic \
  --json_out experiments_tmp/a7_legal_open_opportunity_32k_20260604_r1/a7_opportunity_stochastic_probe.json \
  --csv_out experiments_tmp/a7_legal_open_opportunity_32k_20260604_r1/a7_opportunity_stochastic_probe.csv
```

## Deterministic Probe

Source：
`experiments_tmp/a7_legal_open_opportunity_32k_20260604_r1/a7_opportunity_deterministic_probe.json`

| Metric | Observed |
| --- | ---: |
| Episodes | `1` |
| Fire requests | `0` |
| Releases | `0` |
| Final missiles | `4` |
| Open-window steps | `1840` |
| Quality-window steps | `1080` |
| Open-window fire probability mean / max | `0.281221` / `0.293340` |
| Policy event fire probability mean / max | `0.215603` / `0.293340` |
| A7 prewindow / quality steps | `760` / `1080` |
| A7 prewindow cumulative fire probability | `1.0` |
| A7 prewindow advantage mean | `-0.793259` |
| A7 quality-window advantage mean | `-0.792674` |
| Advantage positive frac, prewindow / quality | `0.0` / `0.0` |
| Advantage negative frac, prewindow / quality | `1.0` / `1.0` |

Deterministic behavior 继续 held。policy 不请求 `fire_once`，尽管 open-window
probability 已高于 N 的 deterministic probe。quality-window event-credit advantage
仍然为负。

## Stochastic Probe

Source：
`experiments_tmp/a7_legal_open_opportunity_32k_20260604_r1/a7_opportunity_stochastic_probe.json`

| Episode | First release step | Releases | Authorized | Violations | Repeat releases | Budget violations | Final missiles | Open steps before release | Quality steps before release | Prewindow advantage mean |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0` | `3` | `1` | `1` | `0` | `0` | `0` | `3` | `1` | `0` | `-0.802803` |
| `1` | `44` | `1` | `1` | `0` | `0` | `0` | `3` | `2` | `0` | `-0.797275` |
| `2` | `10` | `1` | `1` | `0` | `0` | `0` | `3` | `8` | `0` | `-0.803578` |

Stochastic one-shot discipline 继续保持：所有采样 release 均为 authorized，无 repeat
release、shot-budget violation、legacy 或 unauthorized fallback。Timing 仍 held，因为
release 仍发生在 prewindow，尚未进入可 accepted 的 quality-window 行为。

## 与 N Projection Evidence 对照

| Evidence slice | Legal-open source | Deterministic release | Deterministic open-window fire probability | Quality-window advantage | Stochastic release steps | One-shot legality | Interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `A7-EVC-N projection r3` | missing / not implemented | `0` releases | mean/max `0.251826` / `0.261581` | `-0.866` | `2`、`47`、`5` | pass | Projection path 已启用但 candidate-starved。 |
| `A7-EVC-R opportunity r1` | final count `332`，positive count `332` | `0` releases | mean/max `0.281221` / `0.293340` | `-0.793` | `3`、`44`、`10` | pass | Direct legal-open credit 是 live 的，并轻微抬高 probability，但没有翻转 deterministic mode 或 advantage sign。 |

R 改善了 evidence plumbing，并轻微改善 event-fire probability；但 learned behavior
没有改善到 acceptance。

## 解释与下一方向

Accepted：

- Direct legal-open opportunity credit 已进入 learned training path。
- 新 source metrics 能区分 `LEGAL_OPEN_QUALITY` positives、deadline、shadow 与
  projection rows。
- stochastic probe 中 A3/A5 one-shot legality 保持 intact。
- 该 run 是有效 learned evidence，因为 ordinary A7 event-credit loss 与 legal-open
  source counts 是 live 的。

Held：

- deterministic policy 仍为 `0` 次 `fire_once` request；
- stochastic policy 仍采样 early releases；
- quality-window A7 advantage 仍为负；
- `fire_once` probability 上升，但 event mode 仍保持 `hold`；
- projection 仍大多 inactive，且本切片已不把 projection 当作主要改善路径。

下一有界方向：

- 在 source starvation 不再是 active explanation 后，审计
  value/advantage-to-policy coupling。下一步不应继续 blind coefficient run，而应检查
  positive legal-open labels 为什么能带来 nonzero loss 与 probability movement，却仍让
  learned advantage 为负、deterministic mode 保持 `hold`。

## Worker Packet

```md
status: pass; held outcome
touched files:
- docs/task/air_combat/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_short_opportunity_learned_evidence_20260604.md
- docs/task/air_combat/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_short_opportunity_learned_evidence_20260604.zh.md
commands/outcomes:
- A7 legal-open opportunity r1 32768-step train -> completed
- TensorBoard scalar check -> legal-open quality source active; final count 332, positive count 332
- deterministic probe -> 0 requests, 0 releases, open-window fire probability mean/max 0.281/0.293, negative quality-window advantage
- stochastic probe -> 3/3 authorized one-shot releases at steps 3, 44, 10 with zero violations
remaining paths:
- value/advantage-to-policy coupling audit after non-starved source evidence
behavior risks:
- source labels are live, but the credit head still learns negative advantage on quality-window positives
- probability improves modestly without deterministic mode flip
- timing remains early or absent, so A7 is not accepted
integration notes:
- experiments_tmp remains unstaged
- A3/A5 legality remains authoritative
- M2, HMoE redesign, missile authority, 2v2, self-play, and doctrine remain held
```
