# A3 C2/ROE Reactive vs Temporal Comparison - 2026-06-03

Status: `2026-06-03` post-launch-observation comparison evidence. This record
does not accept the learned policy and does not release M2.

Language:

- English canonical: `a3_c2_roe_reactive_temporal_comparison_20260603.md`
- Chinese companion: [a3_c2_roe_reactive_temporal_comparison_20260603.zh.md](a3_c2_roe_reactive_temporal_comparison_20260603.zh.md)

## Scope

This run compares A3 C2/ROE reactive and temporal HMoE policies after
`air_combat_c2_roe_v1` mission observation began dynamically exposing
post-launch state.

Both runs use:

- scenario: `scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json`;
- seed: `20260613`;
- 32,768 training steps;
- 4 world-batch envs;
- `action_mode=air_combat_hybrid_v1`;
- `mission_obs_mode=air_combat_c2_roe_v1`.

Configs:

- reactive: `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json`;
- temporal: `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json`.

## Training Results

Both runs completed without a non-finite report. Both remained
`combat_timeout` dominated and ended near `ep_rew_mean=-753`. Training
diagnostics stayed routed through `nav/vector`, and deterministic diagnostic
windows showed `action_fire_weapon_frac=0`.

The training logs still produced no-missiles-remaining warnings in sampled
rollouts. Dynamic post-launch observation alone therefore did not remove
missile-spending behavior during stochastic exploration.

## Final-Model Probes

| Probe | Episodes | Termination | Fire attempts | Releases | Authorized releases | Violation releases | Invalid attempts | Damage reports |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| reactive deterministic | 1 | `combat_timeout=1` | 0 | 0 | 0 | 0 | 0 | 0 |
| reactive stochastic | 3 | `combat_timeout=3` | 14 | 11 | 3 | 8 | 3 | 3 |
| temporal deterministic | 1 | `combat_timeout=1` | 0 | 0 | 0 | 0 | 0 | 0 |
| temporal stochastic | 3 | `combat_timeout=3` | 7 | 2 | 2 | 0 | 5 | 0 |

Per-episode stochastic release buckets:

| Policy | Episode | Fire attempts | Releases | Authorized releases | Violation releases | Invalid attempts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| reactive | 0 | 5 | 4 | 1 | 3 | 1 |
| reactive | 1 | 4 | 4 | 1 | 3 | 0 |
| reactive | 2 | 5 | 3 | 1 | 2 | 2 |
| temporal | 0 | 1 | 0 | 0 | 0 | 1 |
| temporal | 1 | 3 | 1 | 1 | 0 | 2 |
| temporal | 2 | 3 | 1 | 1 | 0 | 2 |

## Interpretation

Temporal history is now the better stochastic release-discipline surface: in
this fixed-seed 32k comparison, it reduced violation releases from 8 to 0.
However, it did so by becoming conservative. Deterministic policy still never
fires, temporal stochastic probing produced only two authorized releases, and
it produced no damage reports.

The remaining issue should not be treated as solved memory. The next work item
is training-signal and policy-routing repair: the policy must learn a
deterministic authorized first shot, and then learn to hold or request
reattack after launch.
