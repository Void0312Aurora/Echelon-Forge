# A7 Short Learned Evidence

Status: `2026-06-04` `A7-EVC-G Short Learned Evidence` pass as valid evidence,
but held as a learned-policy outcome. The A7 training path is now active; the
learned policy still fails the launch-window timing acceptance gate.

Parent: [README.md](README.md). Focused validation:
[a7_event_value_advantage_credit_head_focused_validation_sweep_20260604.md](a7_event_value_advantage_credit_head_focused_validation_sweep_20260604.md).

## Scope

This slice ran the maintained A7 active config after focused validation and
probed the final policy in deterministic and stochastic modes. It compares the
result with `A6-EVT-M Launch-Window Short Learned Evidence`.

It does not release M2, HMoE redesign, missile physics, Pk/fuze/damage
authority, `2v2`, self-play, or real-world doctrine claims. `experiments_tmp`
artifacts remain unstaged.

## Pre-Run Blockers Fixed

Two training-path issues were found before accepting the A7 learned evidence:

- SB3 stdout key truncation collided on long A7 callback diagnostic names. The
  callback A7 keys were shortened in `python/training/diagnostics.py`, with
  regression coverage in `tests/training/test_diagnostics_callback_contracts.py`.
- The A7 active config enables `diagnostics.nonfinite_probe=true`, but
  `NonFiniteTrainingProbe` still used the A6-only first-event gate and did not
  add `_first_event_credit_loss()` in its patched `train()` path. That meant A7
  coefficients could load while the credit head stayed untrained. The probe now
  uses `_first_event_label_collection_enabled()` when available and records A7
  credit-loss metrics, with regression coverage in
  `tests/policy/test_auxiliary_training_updates.py`.

The pre-fix run
`experiments_tmp/a7_event_credit_launch_window_32k_20260604_r2` is therefore
invalid as A7 learned evidence. It is retained only as root-cause evidence for
the bypassed credit path.

## Valid Training Run

Run:
`experiments_tmp/a7_event_credit_launch_window_32k_20260604_r3`

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a7_event_credit_launch_window_32k_20260604_r3 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260671
```

Final model:
`experiments_tmp/a7_event_credit_launch_window_32k_20260604_r3/final_model.zip`

TensorBoard scalar check from
`experiments_tmp/a7_event_credit_launch_window_32k_20260604_r3/logs/PPO_1/`:

| Scalar | Final step | Final value |
| --- | ---: | ---: |
| `a7/event_credit_loss` | `32768` | `0.323648` |
| `a7/event_credit_value_loss` | `32768` | `0.323296` |
| `a7/event_credit_delta_align_loss` | `32768` | `0.000352` |
| `a7/event_credit_active_count_mean` | `32768` | `450.0` |
| `a7/event_credit_advantage_mean` | `32768` | `-0.978105` |
| `a7/event_credit_target_positive_frac` | `32768` | `0.599889` |

Callback snapshots also show a live but negative event-credit advantage:
`a7/evc_adv_mean` moved from `-0.2495` at step `10240` to `-0.9233` at step
`30720`, with positive fraction `0.0` and negative fraction `1.0`.

Interpretation: the A7 credit head is no longer bypassed. The remaining failure
is learned signal direction/timing, not a dead training path.

## Probe Commands

Deterministic:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a7_event_credit_launch_window_32k_20260604_r3/final_model.zip \
  --episodes 1 \
  --seed 20260672 \
  --max_steps 2400 \
  --json_out experiments_tmp/a7_event_credit_launch_window_32k_20260604_r3/a7_event_credit_deterministic_probe.json \
  --csv_out experiments_tmp/a7_event_credit_launch_window_32k_20260604_r3/a7_event_credit_deterministic_probe.csv
```

Stochastic:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a7_event_credit_launch_window_32k_20260604_r3/final_model.zip \
  --episodes 3 \
  --seed 20260672 \
  --max_steps 2400 \
  --stochastic \
  --json_out experiments_tmp/a7_event_credit_launch_window_32k_20260604_r3/a7_event_credit_stochastic_probe.json \
  --csv_out experiments_tmp/a7_event_credit_launch_window_32k_20260604_r3/a7_event_credit_stochastic_probe.csv
```

## Deterministic Probe

Source:
`experiments_tmp/a7_event_credit_launch_window_32k_20260604_r3/a7_event_credit_deterministic_probe.json`

| Metric | Observed |
| --- | ---: |
| Episodes | `1` |
| Fire requests | `0` |
| Releases | `0` |
| Final missiles | `4` |
| Open-window steps | `1880` |
| Open-window fire probability mean / max | `0.230779` / `0.232900` |
| Policy event fire probability mean / max | `0.180777` / `0.232900` |
| A7 prewindow / quality steps | `800` / `1080` |
| A7 prewindow cumulative fire probability | `1.0` |
| A7 prewindow advantage mean | `-0.881011` |
| A7 quality-window advantage mean | `-0.881781` |
| Advantage positive frac, prewindow / quality | `0.0` / `0.0` |
| Advantage negative frac, prewindow / quality | `1.0` / `1.0` |

Deterministic policy still chooses `hold`, with no release. The A7 advantage is
negative in both the pre-window and quality window, so it does not provide the
required `fire_once` preference inside the quality window.

## Stochastic Probe

Source:
`experiments_tmp/a7_event_credit_launch_window_32k_20260604_r3/a7_event_credit_stochastic_probe.json`

| Episode | First release step | Releases | Authorized | Violations | Repeat releases | Budget violations | Final missiles | Prewindow `P_early` | Prewindow advantage mean |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0` | `14` | `1` | `1` | `0` | `0` | `0` | `3` | `0.935183` | `-0.868688` |
| `1` | `47` | `1` | `1` | `0` | `0` | `0` | `3` | `0.724034` | `-0.878345` |
| `2` | `2` | `1` | `1` | `0` | `0` | `0` | `3` | `0.0` | `0.0` |

Stochastic one-shot discipline remains intact: every sampled release is
authorized, there are no repeat releases before assessment, and there are no
shot-budget violations. The timing remains held: all stochastic releases occur
very early, before quality-window behavior can be accepted.

## A6-EVT-M Comparison

| Evidence slice | Deterministic release | Deterministic open-window fire probability | Stochastic release steps | Discipline | Interpretation |
| --- | --- | --- | --- | --- | --- |
| `A6-EVT-M Launch-Window` | `0` releases | mean/max `34.6%` / `35.0%` | `7`, `43`, `4` | authorized one-shot | Higher per-step fire probability, still no deterministic argmax crossing; stochastic fires too early. |
| `A7-EVC-G r3` | `0` releases | mean/max `23.1%` / `23.3%` | `14`, `47`, `2` | authorized one-shot | Credit-head training is active, but advantage is negative in quality windows and stochastic timing is still early. |

A7 did not improve the accepted timing behavior relative to A6-M. It restored a
real credit-training path and preserved A5 one-shot legality, but it did not
produce the expected event-advantage sign or deterministic quality-window
release.

## Interpretation And Next Direction

Accepted:

- A7 active config can train the event-credit head through the nonfinite-probe
  training path.
- A7 diagnostics now expose credit-loss activity, advantage signs, and
  cumulative pre-window stochastic fire probability.
- A3/A5 legality and one-shot discipline remain intact in the valid probe.

Held:

- deterministic policy still makes `0` `fire_once` requests;
- stochastic policy still samples early releases;
- cumulative pre-window fire probability is still high when the mask remains
  open;
- A7 advantage remains negative in quality-window rows.

Likely follow-on diagnosis should inspect target construction and credit
assignment before more tuning:

- whether quality-window positive labels are outweighed by hold/deadline or
  censored early-sample targets;
- whether value targets are centered/scaled so that `Q_fire_once - Q_hold`
  can become positive in quality windows;
- whether delta alignment is reinforcing the negative advantage faster than
  quality positives can correct it;
- whether HMoE routing is only a secondary issue, since the current failure is
  already visible in the event-credit sign itself.

## Worker Packet

```md
status: pass; held outcome
touched files:
- docs/task/air_combat/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_short_learned_evidence_20260604.md
commands/outcomes:
- A7 r3 32768-step train -> completed
- TensorBoard scalar check -> a7/event_credit_loss present at step 32768
- deterministic probe -> 0 requests, 0 releases, no violations
- stochastic probe -> 3/3 authorized one-shot releases at steps 14, 47, 2
remaining paths:
- A7-EVC-I Target Construction And Credit Sign Audit has since closed as
  evidence that spawned the J repair
- A7-EVC-J Shadow Quality Target Repair has since closed as repair-pass but
  behavior-held evidence
- A7-EVC-K Legal-State Projection And Coupling Audit before another training wave
behavior risks:
- stochastic one-shot behavior is preserved but still fires too early
- quality-window advantage remains negative, so A7 is not accepted
integration notes:
- experiments_tmp remains unstaged
- A3/A5 legality remains authoritative
- M2, HMoE redesign, missile authority, 2v2, self-play, and doctrine remain held
```
