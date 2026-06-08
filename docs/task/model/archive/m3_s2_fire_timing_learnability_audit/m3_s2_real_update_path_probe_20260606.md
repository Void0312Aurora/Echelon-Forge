# M3-S2 Real Update Path Probe - 2026-06-06

Parent: [README.md](README.md).

Status: `root-cause localization evidence`; real M3-S2 updates reach the
executable event parameters, but they currently suppress both prewindow and
quality-window logits instead of forming a quality-window boundary.

## Question

The structural toy probe showed that the grouped M3-S2 loss can learn an
abstract one-shot window pulse. Why does the real Stage-1 policy still not
fire?

This probe asks whether the current M3-S2 auxiliary update, applied to real
Stage-1 observations and real policy parameters, moves the executable
`fire_once` logit in the right direction.

## Tooling

New diagnostic:

```text
tools/diagnostics/m3s2_real_update_path_probe.py
```

The probe:

- loads the M3-S2 support-preserving checkpoint;
- collects a forced-hold Stage-1 sequence so one-shot support is not consumed;
- reconstructs M3-S2 groups using the same legal-open age and launch-window
  rule as the training sidecar;
- applies offline M3-S2 auxiliary updates to real policy parameters;
- compares `fire_once` logit/probability before and after the update for
  prewindow and quality-window rows.

Test coverage:

```bash
python -m pytest tests/diagnostics/test_m3s2_real_update_path_probe.py -q
```

Outcome: `2 passed`.

## Artifacts

Four-step probe:

```text
experiments_tmp/m3s2_real_update_path_probe_20260606_4step.json
```

Forty-step current-scope probe:

```text
experiments_tmp/m3s2_real_update_path_probe_20260606_40step_current.json
```

The 200-step exploratory run was stopped because two full scopes were too slow
for interactive diagnosis; no evidence was taken from that partial run.

## Collection

The forced-hold collection produced real supported rows:

| Metric | Value |
| --- | ---: |
| `steps` | `2400` |
| `group_count` | `1` |
| `legal_rows` | `1880` |
| `quality_rows` | `1040` |
| `accepted_count` | `0` |
| `launch_min_age` | `32` |

This rules out "there were no quality rows" for this probe.

## Initial Real Logits

Before any offline update:

| Subset | Count | Logit mean | Logit max | Prob mean | Cumulative risk | Boundary count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Prewindow | `840` | `-5.719286` | `-5.707861` | `0.003271` | `0.936229` | `0` |
| Quality | `1040` | `-5.721806` | `-5.719494` | `0.003263` | `0.966600` | `0` |

The policy is almost unable to distinguish prewindow from quality rows:
quality logits are slightly lower than prewindow logits.

## Four-Step Update

This mirrors the active config's `m3s2_event_window_separate_update_steps = 4`.

| Scope | Selected groups | Quality logit max delta | Prewindow logit max delta | Quality boundary after | Loss delta |
| --- | --- | ---: | ---: | ---: | ---: |
| `current` | `action_net`, `actor_mlp`, `event_head` | `-0.265521` | `-0.264529` | `0` | `-2.033200` |
| `current_plus_features` | `action_net`, `actor_mlp`, `event_head`, `features` | `-0.428197` | `-0.431909` | `0` | `-2.979543` |

The update has large gradients and reduces loss, but it does so by lowering
hazard almost everywhere. It does not raise quality-window logits toward the
deterministic boundary.

## Forty-Step Current-Scope Update

The current-scope result after forty offline update steps:

| Subset | Logit mean delta | Logit max delta | Prob mean delta | Cumulative risk delta | Boundary after |
| --- | ---: | ---: | ---: | ---: | ---: |
| Prewindow | `-1.804984` | `-1.794477` | `-0.002732` | `-0.571688` | `0` |
| Quality | `-1.794544` | `-1.789550` | `-0.002719` | `-0.534545` | `0` |

The trend persists: the real update mostly learns "fire less everywhere." It
slightly separates quality from prewindow, but the separation is tiny compared
with the distance to the `fire_once` boundary.

## Decision

The failure is no longer best described as missing gradients or missing
support. This probe shows:

- real M3-S2 has supported quality rows;
- the auxiliary update reaches `action_net`, `actor_mlp`, and `event_head`;
- gradients are large and parameters move;
- loss decreases;
- but quality logits move downward with prewindow logits and never cross
  deterministic mode.

The localized failure is feature-to-logit discrimination under the real policy
update path. The model can reduce cumulative hazard by applying a shared
downward shift, and that is the easier direction than learning the sharp
prewindow/quality separator. The next repair should not be another coefficient
sweep. It should enforce or audit the discriminator explicitly:

1. add a contrastive/margin term on real rows:
   `quality_logit - prewindow_logit > margin`;
2. audit whether the explicit mission-observation quality features survive the
   temporal feature extractor and actor MLP;
3. split the event boundary adapter from the sampled Bernoulli hazard so the
   learner can represent stopping separately from per-step stochastic risk;
4. only then revisit PPO overwrite or M2 memory.
