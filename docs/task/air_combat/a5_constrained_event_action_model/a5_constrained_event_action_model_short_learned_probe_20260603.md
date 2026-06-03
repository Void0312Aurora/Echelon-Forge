# A5 Short Learned-Policy Probe

Status: `2026-06-03` learned-policy evidence after A5 event-action,
reward/config, and diagnostics implementation. A5 remains held: deterministic
policy still does not request `fire_once`, while stochastic probing now shows
structural release discipline.

Parent: [README.md](README.md). Implementation evidence:
[a5_constrained_event_action_model_implementation_evidence_20260603.md](a5_constrained_event_action_model_implementation_evidence_20260603.md).

## Scope

This run checks whether the first A5 event-action implementation is enough for
the maintained S1 C2/ROE temporal probe to learn a deterministic authorized
first shot. It does not accept M2, `2v2`, self-play, missile physics, Pk, fuze,
or real-world doctrine claims.

The evidence is intentionally short: one `32768`-step A5 post-change training
run plus deterministic and stochastic process probes. Artifacts are under
`experiments_tmp/` and must not be staged.

## Training Command

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a5_event_action_temporal_32k_20260603 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260626
```

Result:

- Completed `32768` timesteps.
- Final model saved under
  `experiments_tmp/a5_event_action_temporal_32k_20260603/final_model.zip`.
- No non-finite abort occurred.
- Final rollout mean reward was about `528`.
- Training diagnostics confirmed `hmoe/fam/combat = 1`.
- Late-run diagnostics still showed `pi_event_fire_mask_frac ~= 0.75`,
  `pi_event_fire_p_mean ~= 0.20%`, and `pi_event_mode_fire_frac = 0`.

## Probe Commands

Deterministic:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a5_event_action_temporal_32k_20260603/final_model.zip \
  --episodes 1 \
  --seed 20260627 \
  --max_steps 2400 \
  --json_out experiments_tmp/a5_event_action_temporal_32k_20260603/a5_deterministic_probe.json \
  --csv_out experiments_tmp/a5_event_action_temporal_32k_20260603/a5_deterministic_probe.csv
```

Stochastic:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a5_event_action_temporal_32k_20260603/final_model.zip \
  --episodes 3 \
  --seed 20260627 \
  --max_steps 2400 \
  --stochastic \
  --json_out experiments_tmp/a5_event_action_temporal_32k_20260603/a5_stochastic_probe.json \
  --csv_out experiments_tmp/a5_event_action_temporal_32k_20260603/a5_stochastic_probe.csv
```

## Results

| Probe | Episodes | Termination | Fire mask open steps | Fire requests | Accepted | Rejected | Releases | Authorized releases | Violation releases | Repeat / budget violations |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 1 | `combat_timeout=1` | 1880 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stochastic | 3 | `combat_timeout=3` | 1647 | 4 | 3 | 1 | 3 | 3 | 0 | 0 |

Deterministic summary:

| Episode | Fire mask open | AuthorizedReady steps | Fire event probability mean / max | Fire event mode-fire count | Requests | Releases |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1880 | 1880 | `0.217% / 0.278%` | 0 | 0 | 0 |

Stochastic summary:

| Episode | First release step | Fire mask open | Requests | Accepted | Rejected | Rejection reason | Releases | Authorized | Violations | Final missiles |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 0 | 823 | 792 | 2 | 1 | 1 | `weapon_not_ready=1` | 1 | 1 | 0 | 3 |
| 1 | 346 | 296 | 1 | 1 | 0 | none | 1 | 1 | 0 | 3 |
| 2 | 592 | 559 | 1 | 1 | 0 | none | 1 | 1 | 0 | 3 |

## Interpretation

A5 fixes the structural multi-fire and stochastic release-discipline failure
from A4. In stochastic probing, each episode executes exactly one authorized
release; there are no violation releases, no repeat releases before assessment,
and no shot-budget violations. This is a major improvement over retained A4
stochastic evidence, which still produced repeated and violation releases.

A5 does not yet solve deterministic learned release timing. The deterministic
probe had `1880` valid fire-mask-open steps and `1880` `AuthorizedReady` steps,
but made zero `fire_once` requests. The masked event fire probability stayed
near `0.2%`, so deterministic argmax remains `hold`.

The residual is no longer a reward-only legality problem. It is now a policy
optimization / event-value problem: the event-action surface can legally express
and suppress release, but PPO still keeps deterministic `fire_once` below the
hold action.

## Held Residual

A5 should remain held rather than accepted. The recommended next package is an
event-value or first-event timing mechanism, such as an event Q-head, explicit
first-shot curriculum, or hazard/first-event objective. This follow-on should
not reopen broad invalid-fire penalties as the legality mechanism.
