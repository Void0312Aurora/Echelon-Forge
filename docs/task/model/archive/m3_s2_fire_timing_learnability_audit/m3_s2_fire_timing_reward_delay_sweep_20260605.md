# M3-S2 Fire-Timing Reward Delay Sweep

Parent: [README.md](README.md).

Status: `2026-06-05` evidence update; records reward-ordering defect and
reopens the learned-policy reachability question.

## Command

The sweep evaluates every legal-open delay from `0` through `1778` for one
Stage-1 episode under the maintained M3-S1 probe scenario/config. Each case
uses the oracle `legal_mask_fire` transport, so this is an environment/reward
surface audit, not a learned-policy success claim.

Artifacts:

```text
experiments_tmp/air_combat_fire_timing_full_delay_sweep_seed7_ep1_0_1778_20260605.jsonl
experiments_tmp/air_combat_fire_timing_full_delay_sweep_seed7_ep1_0_1778_20260605_summary.json
experiments_tmp/air_combat_fire_timing_full_delay_sweep_seed7_ep1_0_1778_20260605_compact.csv
experiments_tmp/air_combat_fire_timing_full_delay_sweep_seed7_ep1_0_1778_20260605.png
```

## Result

| Metric | Value |
| --- | ---: |
| Candidate delays | `1779` |
| Probe errors | `0` |
| Successful releases | `1759` |
| Effects/damage reports | `270` |
| Combat wins | `27` |
| Best delay by episode return | `1664` |
| Best release step | `1666` |
| Best effects/damage step | `1693` |
| Best terminal reason | `combat_win` |
| Best loss state | `mission_kill` |
| Best return | `2009.267824398761` |

The best delay is a very late close-range shot. The hold-trace geometry at the
release step is approximately:

```text
track_range_m: 1341.264
geom_range_m: 823.605
track_age_s: 1.25
closing_mps: 408.303
```

This means the current reward surface has a mathematical optimum, but that
optimum is not the maintained `8 km` to `30 km` quality-window proxy and should
not be interpreted as tactical best fire timing.

## Reward Ordering Defect

The sweep shows why late wins outrank earlier wins. For successful terminal
shots:

```text
return ~= release_bonus + objective_bonus + accumulated per-step shaping
release_bonus ~= 300 + 50 + 100 = 450
objective_bonus = 1500
```

Example comparison:

| Delay | Combat-win step | Return |
| ---: | ---: | ---: |
| `939` | `1233` | `1990.8678243987608` |
| `1664` | `1693` | `2009.267824398761` |

The return gap is:

```text
2009.267824398761 - 1990.8678243987608 = 18.4
1693 - 1233 = 460 steps
18.4 / 460 = 0.04 per step
```

So mission success still dominates no-win outcomes, but among outcomes that
already win, the positive per-step shaping rewards later termination. The
reward contract therefore lacks an explicit time-to-success cost or an
absorbing success-normalized objective.

## Consequence For Reachability

This finding does not explain the learned policy's no-fire behavior. The oracle
surface proves that:

- no fire is not optimal under the current return;
- legal release is reachable and strongly rewarded;
- terminal wins are reachable from some delayed oracle shots.

Therefore the remaining learned-policy blocker should be investigated as an
action/event reachability and credit-assignment problem:

```text
continuous model output -> masked edge-triggered pulse -> executable fire_once
```

The next audit should separate whether the learned policy:

- assigns low probability to `fire_once`;
- chooses `fire_once` before the executable mask is open and consumes the edge;
- has a stopping/event head boundary crossing that is not transported to the
  action;
- receives action-mask support but remains deterministic-hold due to logits or
  PPO credit.
