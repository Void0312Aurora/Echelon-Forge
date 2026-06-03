# A4 Authorized First-Shot Binary Diagnostics - 2026-06-03

Status: `2026-06-03` retained diagnostics and rejected opportunity-penalty
trial. A4 remains held; M2 remains held.

Language:

- English canonical: `a4_authorized_first_shot_binary_diagnostics_20260603.md`
- Chinese companion:
  [a4_authorized_first_shot_binary_diagnostics_20260603.zh.md](a4_authorized_first_shot_binary_diagnostics_20260603.zh.md)

## Scope

This packet checks whether the retained routed A4 policy is close to a
deterministic `tms_up` / `fire_weapon` threshold crossing. It also records one
bounded reward-mechanism trial: a pre-release authorized fire-opportunity
penalty.

Retained code from this slice:

- hybrid action distribution now returns finite entropy for PPO instead of
  `None`;
- training diagnostics log compact binary action logits/probabilities, e.g.
  `diag/pi_bin_fire_p_mean`;
- the process probe exports per-step and authorized-window binary
  logits/probabilities;
- reward runtime exposes
  `air_combat_roe_authorized_fire_opportunity_penalty`, but the maintained S1
  C2/ROE active scenario leaves it at `0.0`.

## Retained-Routed Baseline Diagnostics

Command:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a4_authorized_first_shot_routed_retained_temporal_32k_20260603/final_model.zip \
  --episodes 1 \
  --seed 20260625 \
  --max_steps 2400 \
  --json_out experiments_tmp/a4_authorized_first_shot_routed_retained_temporal_32k_20260603/binary_diagnostics_det_20260603.json
```

Result:

| Probe | Fire attempts | Releases | Authorized-window steps | `tms_up` prob mean/max | `fire_weapon` prob mean/max | `fire_weapon` logit max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic retained routed | 0 | 0 | 2400 | `0.01877 / 0.01880` | `0.002222 / 0.002224` | `-6.106` |

Interpretation: the deterministic policy is not near threshold. The
`fire_weapon` logit remains essentially pinned to the safe-action prior.

## Opportunity-Penalty Trial

Trial command:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a4_authorized_first_shot_entropy_opportunity_temporal_32k_v2_20260603 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260634
```

The run used a temporary
`air_combat_roe_authorized_fire_opportunity_penalty=-0.1` setting. After the
probe below, the active scenario was returned to `0.0`.

Training completed `32768` timesteps. Final diagnostics still showed:

- `diag/pi_bin_fire_logit_mean ~= -6.12`;
- `diag/pi_bin_fire_p_mean ~= 0.0022`;
- final rollout reward about `-3.36e3`;
- stochastic training warnings still included "no missiles remaining".

Deterministic probe:

| Probe | Fire attempts | Releases | Authorized-window steps | `fire_weapon` prob mean/max | `fire_weapon` logit max | Reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| opportunity trial deterministic | 0 | 0 | 2400 | `0.002210 / 0.002215` | `-6.110` | `-164.59` |

Stochastic probe:

| Episodes | Fire attempts | Releases | Authorized releases | Violation releases | Invalid attempts | Damage reports |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 22 | 11 | 3 | 8 | 11 | 0 |

Per-episode stochastic release summary:

| Episode | Attempts | Releases | Authorized | Violations | Invalid attempts | Final missiles |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 9 | 4 | 1 | 3 | 5 | 0 |
| 1 | 9 | 4 | 1 | 3 | 5 | 0 |
| 2 | 4 | 3 | 1 | 2 | 1 | 1 |

## Decision

The opportunity penalty is rejected as an active default:

- it did not move deterministic `fire_weapon` logits away from the safe prior;
- it made deterministic returns more negative without producing a release;
- stochastic behavior regressed relative to the retained routed run.

The runtime key remains available for future controlled sweeps, but the
maintained S1 C2/ROE active scenario keeps it disabled.

## Next Work

The residual is now narrower than reward magnitude tuning:

- add a supervised or curriculum-style binary pulse target for the
  authorized-first-shot route; or
- add route-specific initialization / curriculum that raises only the
  `authorized_first_shot` subexpert pulse logits while suppressing
  `post_launch_assess`.

Do not release M2 until deterministic authorized first release is demonstrated
under the maintained S1 C2/ROE probe.
