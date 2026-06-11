# A7 Short Opportunity Learned Evidence

Status: `2026-06-04` `A7-EVC-R Short Opportunity Learned Evidence` pass as
valid evidence, but held as a learned-policy outcome. Direct legal-open
opportunity credit is no longer candidate-starved in the learned train path,
but the final policy still does not meet first-shot timing acceptance.

Parent: [README.md](README.md). Prototype:
[a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.md](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.md).

## Scope

This slice runs the maintained A7 active config after `A7-EVC-Q` and probes the
final policy in deterministic and stochastic modes. It asks whether direct
legal-open quality opportunity credit changes learned behavior relative to
`A7-EVC-N Short Projection Learned Evidence`.

It does not release M2, HMoE redesign, missile physics, Pk/fuze/damage
authority, `2v2`, self-play, or real-world doctrine claims. `experiments_tmp`
artifacts remain unstaged.

## Valid Training Run

Run:
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

Final model:
`experiments_tmp/a7_legal_open_opportunity_32k_20260604_r1/final_model.zip`

TensorBoard scalar check from
`experiments_tmp/a7_legal_open_opportunity_32k_20260604_r1/logs/PPO_1/`:

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

Interpretation: Q fixed the source-starvation problem for direct legal-open
opportunity credit. Legal-open quality positives are present in the real train
loss, including the final update. However, the event-credit advantage remains
negative on those positive rows and deterministic event mode never flips to
`fire_once`.

## Probe Commands

Deterministic:

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

Stochastic:

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

Source:
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

Deterministic behavior remains held. The policy does not request `fire_once`,
even though the open-window probability is higher than N's deterministic probe.
The quality-window event-credit advantage is still negative.

## Stochastic Probe

Source:
`experiments_tmp/a7_legal_open_opportunity_32k_20260604_r1/a7_opportunity_stochastic_probe.json`

| Episode | First release step | Releases | Authorized | Violations | Repeat releases | Budget violations | Final missiles | Open steps before release | Quality steps before release | Prewindow advantage mean |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0` | `3` | `1` | `1` | `0` | `0` | `0` | `3` | `1` | `0` | `-0.802803` |
| `1` | `44` | `1` | `1` | `0` | `0` | `0` | `3` | `2` | `0` | `-0.797275` |
| `2` | `10` | `1` | `1` | `0` | `0` | `0` | `3` | `8` | `0` | `-0.803578` |

Stochastic one-shot discipline remains intact: all sampled releases are
authorized, with no repeat release, no shot-budget violation, and no legacy or
unauthorized fallback. Timing remains held because the releases still occur in
the prewindow before quality-window behavior can be accepted.

## Comparison With N Projection Evidence

| Evidence slice | Legal-open source | Deterministic release | Deterministic open-window fire probability | Quality-window advantage | Stochastic release steps | One-shot legality | Interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `A7-EVC-N projection r3` | missing / not implemented | `0` releases | mean/max `0.251826` / `0.261581` | `-0.866` | `2`, `47`, `5` | pass | Projection path was enabled but candidate-starved. |
| `A7-EVC-R opportunity r1` | final count `332`, positive count `332` | `0` releases | mean/max `0.281221` / `0.293340` | `-0.793` | `3`, `44`, `10` | pass | Direct legal-open credit is live and raises probability modestly, but does not flip deterministic mode or advantage sign. |

R improves the evidence plumbing and slightly improves event-fire probability.
It does not improve the learned behavior enough for acceptance.

## Interpretation And Next Direction

Accepted:

- Direct legal-open opportunity credit is present in the learned training path.
- The new source metrics distinguish `LEGAL_OPEN_QUALITY` positives from
  deadline, shadow, and projection rows.
- A3/A5 one-shot legality remains intact in stochastic probing.
- The run is valid learned evidence because ordinary A7 event-credit loss and
  legal-open source counts are live.

Held:

- deterministic policy still makes `0` `fire_once` requests;
- stochastic policy still samples early releases;
- quality-window A7 advantage remains negative;
- event mode remains `hold` even though `fire_once` probability increases;
- projection remains mostly inactive and is no longer the primary expected
  improvement path for this slice.

Next bounded direction:

- audit the value/advantage-to-policy coupling now that source starvation is no
  longer the active explanation. The next work should not be another blind
  coefficient run; it should inspect why positive legal-open labels drive
  nonzero loss and probability movement while the learned advantage remains
  negative and deterministic mode remains `hold`.

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
