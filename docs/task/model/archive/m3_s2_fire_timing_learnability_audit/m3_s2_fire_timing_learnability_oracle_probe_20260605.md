# M3-S2 Fire-Timing Oracle Probe

Parent: [README.md](README.md).

Status: `2026-06-05` evidence pass for the learnability audit; learned policy
remains held.

## Command

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_fire_timing_learnability_audit.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json \
  --episodes 2 \
  --seed 31 \
  --max_steps 2000 \
  --delays 0,31,63 \
  --json_out experiments_tmp/air_combat_fire_timing_learnability_audit_20260605.json
```

Artifact:

```text
experiments_tmp/air_combat_fire_timing_learnability_audit_20260605.json
```

## Summary

| Case | Mean reward | Mean release count | Release steps | Effects | Damage | Health drop | Rejections |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| `hold_fire` | `71.54782439876094` | `0.0` | `[]` | `0.0` | `0.0` | `0` | `{}` |
| `forced_fire_edge_at_reset` | `71.54782439876094` | `0.0` | `[]` | `0.0` | `0.0` | `0` | `{"no_target": 2}` |
| `legal_mask_fire_delay_0` | `521.547824398761` | `1.0` | `[2, 42]` | `0.0` | `0.0` | `0` | `{}` |
| `legal_mask_fire_delay_31` | `521.547824398761` | `1.0` | `[33, 73]` | `0.0` | `0.0` | `0` | `{}` |
| `legal_mask_fire_delay_63` | `521.5478243987609` | `1.0` | `[65, 105]` | `0.0` | `0.0` | `0` | `{}` |

Verdict:

```json
{
  "primary_breakpoint": "legal_timing_unidentifiable_from_current_return",
  "release_reachable_with_legal_oracle": true,
  "release_vs_hold_reward_distinguishable": true,
  "release_vs_hold_reward_delta": 450.00000000000006,
  "post_release_effect_observable": false,
  "legal_timing_reward_distinguishable": false,
  "legal_timing_reward_spread": 1.1368683772161603e-13,
  "edge_trigger_adapter_hazard": true
}
```

## Interpretation

The current Stage-1 problem is not blocked at the basic release-reachability
layer. A legal oracle pulse fires exactly one authorized missile.

The current Stage-1 problem is blocked at timing identifiability. Legal pulses
at delay `0`, `31`, and `63` receive the same return, while no effects event,
damage report, health drop, or kill appears within `2000` steps. Therefore the
environment currently teaches "make a legal release" but does not teach "choose
this legal time rather than that legal time."

The action adapter adds a separate hazard. `forced_fire` high from reset does
not mean repeated fire attempts. Because `air_combat_hybrid_v1` fire is
edge-triggered, the first high signal is rejected as `no_target`; the signal
then remains high and produces no later pulse.

## Consequence

More PPO steps or a larger stopping head are unlikely to solve this by
themselves. The next slice should choose one of these contract-level repairs:

- connect the stopping/event decision to an executable pulse adapter that can
  intentionally emit low-before-window and one high pulse inside the window;
- expose timing-quality or downstream effects as a distinguishable target;
- only then reconsider M2 memory/sequence state as a representation upgrade.
