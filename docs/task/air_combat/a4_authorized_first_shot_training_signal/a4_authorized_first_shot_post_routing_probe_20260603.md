# A4 Authorized First-Shot Post-Routing Probe - 2026-06-03

Status: `2026-06-03`, learned-policy evidence after the retained
`combat_weapons` HMoE route. A4 remains held; M2 remains held.

Language:

- English canonical: `a4_authorized_first_shot_post_routing_probe_20260603.md`
- Chinese companion:
  [a4_authorized_first_shot_post_routing_probe_20260603.zh.md](a4_authorized_first_shot_post_routing_probe_20260603.zh.md)

## Scope

This probe checks whether the retained `combat_weapons` HMoE family makes the
maintained S1 C2/ROE temporal probe learn a deterministic authorized first
shot. It also records a rejected A4-only pulse-prior relaxation trial so that
the two outcomes are not confused.

The retained implementation is the `combat_weapons` routing surface and C2
config family-count update. No pulse-prior relaxation is retained.

## Training Command

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a4_authorized_first_shot_routed_retained_temporal_32k_20260603 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260624
```

Result:

- Completed `32768` timesteps.
- Final model saved under
  `experiments_tmp/a4_authorized_first_shot_routed_retained_temporal_32k_20260603/final_model.zip`.
- Final rollout reward stayed around `-2.77e3`.
- HMoE diagnostics confirmed the route fix:
  - `hmoe/fam/combat = 1`;
  - early diagnostics showed `sub/combat/first_shot = 1`;
  - later diagnostics split `sub/combat/first_shot = 0.5` and
    `sub/combat/assess = 0.5`.
- Runtime warnings were sparse compared with the rejected pulse-prior trial.

## Probe Commands

Deterministic:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a4_authorized_first_shot_routed_retained_temporal_32k_20260603/final_model.zip \
  --episodes 1 \
  --seed 20260625 \
  --max_steps 2400
```

Stochastic:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a4_authorized_first_shot_routed_retained_temporal_32k_20260603/final_model.zip \
  --episodes 3 \
  --seed 20260625 \
  --max_steps 2400 \
  --stochastic
```

## Results

| Probe | Episodes | Termination | Fire attempts | Releases | Authorized releases | Violation releases | Invalid attempts | Damage reports |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 1 | `combat_timeout=1` | 0 | 0 | 0 | 0 | 0 | 0 |
| stochastic | 3 | `combat_timeout=3` | 15 | 9 | 3 | 6 | 6 | 2 |

Per-episode stochastic summary:

| Episode | Attempts | Releases | Authorized | Violations | Invalid attempts | Final missiles | Damage reports |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 5 | 4 | 1 | 3 | 1 | 0 | 1 |
| 1 | 7 | 4 | 1 | 3 | 3 | 0 | 1 |
| 2 | 3 | 1 | 1 | 0 | 2 | 3 | 0 |

## Interpretation

The retained route change is useful and verified: C2/ROE mission semantics now
reach `combat_weapons` instead of generic `nav/vector`. Compared with the
reward-only probe, stochastic behavior improves modestly: attempts drop from
`20` to `15`, releases from `11` to `9`, violation releases from `8` to `6`,
invalid attempts from `9` to `6`, and damage reports increase from `1` to `2`.

This is still not A4 acceptance:

- deterministic policy still does not fire;
- stochastic policy can discover an authorized first release, but still repeats
  after launch in two of three episodes;
- the remaining issue is narrower than before: deterministic `fire_weapon`
  binary logit still does not cross threshold, while stochastic pulse sampling
  can discover releases but not disciplined post-launch suppression.

## Rejected Pulse-Prior Relaxation

An A4-only safe-action bias relaxation was also tested in
`experiments_tmp/a4_authorized_first_shot_routed_temporal_32k_20260603`.
It made `tms_up` / `fire_weapon` exploration less sparse, but was rejected and
removed from retained code.

| Probe | Episodes | Fire attempts | Releases | Authorized releases | Violation releases | Invalid attempts | Damage reports |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| stochastic | 3 | 125 | 12 | 3 | 9 | 113 | 0 |

The rejected trial drove final rollout reward to about `-2.28e4` and emptied
all four missiles every stochastic episode. It confirms that simply increasing
pulse exploration is not the right repair.

## Next Work

- Binary logits/probabilities are now recorded in
  [a4_authorized_first_shot_binary_diagnostics_20260603.md](a4_authorized_first_shot_binary_diagnostics_20260603.md).
- Next, consider a supervised or curriculum-style pulse-action target before
  PPO, or route-specific initialization that raises only the
  `authorized_first_shot` subexpert while suppressing `post_launch_assess`.
- Keep M2 held until deterministic authorized first release is demonstrated
  under the retained route and reward surface.
