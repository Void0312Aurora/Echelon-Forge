# A4 Authorized First-Shot Reward Probe - 2026-06-03

Status: `2026-06-03` reward-side evidence. A4 remains active; this record does
not accept the learned policy and does not release M2.

Language:

- English canonical: `a4_authorized_first_shot_reward_probe_20260603.md`
- Chinese companion:
  [a4_authorized_first_shot_reward_probe_20260603.zh.md](a4_authorized_first_shot_reward_probe_20260603.zh.md)

## Scope

This evidence follows the A3 reactive/temporal comparison. It tests whether
additional reward signal can make the S1 C2/ROE authorized first shot trainable
without changing missile physics, ammunition runtime, damage authority, or M2.

Maintained scenario/config pair:

- Scenario:
  `scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json`
- Config:
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json`

## Implementation

The retained implementation adds configurable C2/ROE reward terms for the
authorized pre-release weapon chain:

- `air_combat_roe_authorized_radar_active_bonus`
- `air_combat_roe_authorized_tms_up_bonus`
- `air_combat_roe_authorized_master_arm_bonus`
- `air_combat_roe_authorized_weapon_selected_bonus`
- `air_combat_roe_authorized_fire_attempt_bonus`
- `air_combat_roe_authorized_fire_no_release_penalty`

The positive preparation/attempt terms are awarded once per episode so the
policy cannot farm reward by keeping radar/master-arm/weapon-select on. The
fire-no-release penalty remains per failed fire attempt. The configured S1
C2/ROE probe also strengthens repeat-release and single-shot violation
penalties.

## Commands

Focused tests:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_reward_surface.py \
  tests/training/test_air_combat_active_training_entries.py
```

Retained 32k temporal run:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a4_authorized_first_shot_temporal_once_32k_20260603 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260623
```

Model probes:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a4_authorized_first_shot_temporal_once_32k_20260603/final_model.zip \
  --episodes 1 \
  --seed 20260623 \
  --max_steps 2400
```

The stochastic probe used the same command with `--episodes 3 --stochastic`.

## Results

Focused tests passed:

- `tests/runtime/air_combat/test_air_combat_reward_surface.py`: `10 passed`.
- `tests/training/test_air_combat_active_training_entries.py`: `9 passed, 8 subtests passed`.

Training completed and saved
`experiments_tmp/a4_authorized_first_shot_temporal_once_32k_20260603/final_model.zip`.
No non-finite abort occurred. Final rollout reward was around `-3.87e3`, and
HMoE diagnostics still routed all samples to `nav/vector`.

Final-model probes:

| Probe | Episodes | Termination | Fire attempts | Releases | Authorized releases | Violation releases | Invalid attempts | Damage reports |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 1 | `combat_timeout=1` | 0 | 0 | 0 | 0 | 0 | 0 |
| stochastic | 3 | `combat_timeout=3` | 20 | 11 | 3 | 8 | 9 | 1 |

Per-episode stochastic summary:

| Episode | Attempts | Releases | Authorized | Violations | Invalid attempts | Final missiles | Damage reports |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 5 | 3 | 1 | 2 | 2 | 1 | 0 |
| 1 | 8 | 4 | 1 | 3 | 4 | 0 | 0 |
| 2 | 7 | 4 | 1 | 3 | 3 | 0 | 1 |

## Discarded Per-Step Shaping Attempt

Before the retained once-per-episode implementation, a per-step preparation
reward was tested with the same 32k temporal surface. It made deterministic
radar/master-arm/weapon-select stable and produced one stochastic `combat_win`,
but deterministic still did not fire and stochastic probing produced
`11` releases with `8` violation releases. That attempt was discarded because
it created a no-fire preparation-reward local optimum.

## Interpretation

Reward shaping alone is not sufficient. The retained once-per-episode shaping
removes the obvious reward-farming failure mode and makes violation releases
costly, but it does not teach the deterministic policy to cross the TMS/fire
pulse thresholds. Stochastic behavior still samples repeated fire after the
authorized first release.

The next A4 cut should move to policy mechanics:

- add or test an HMoE air-combat weapons-employment route instead of routing the
  C2/ROE engagement to generic `nav/vector`;
- inspect binary pulse logits for `tms_up` and `fire_weapon`;
- consider a bounded action-head prior or curriculum for pulse actions rather
  than increasing reward magnitudes again.

Follow-up implementation evidence is recorded in
[a4_authorized_first_shot_routing_probe_20260603.md](a4_authorized_first_shot_routing_probe_20260603.md).

M2 remains held.
