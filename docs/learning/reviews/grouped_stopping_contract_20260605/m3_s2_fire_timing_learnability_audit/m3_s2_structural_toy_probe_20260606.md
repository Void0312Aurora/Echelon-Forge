# M3-S2 Structural Toy Probe - 2026-06-06

Parent: [README.md](README.md).

Status: `decisive structural evidence`; the grouped M3-S2 objective is
learnable on an abstract one-shot window task, so the remaining failure is not
the loss object alone.

## Question

Can the current grouped stopping/window objective, without the air-combat
environment, learn the abstract object we need?

The object is:

```text
prewindow:      keep cumulative event risk below a small budget
quality window: put at least one event inside the window
boundary:       cross deterministic fire_once mode in the quality window
constraint:     do not cross before the quality window
```

This removes aircraft dynamics, reward shaping, C2/ROE state transitions,
rollout collection, and PPO credit from the test. The only remaining mechanism
is the M3-S2 grouped survival/event-mass loss over ordered logits.

## Tooling

New diagnostic:

```text
tools/diagnostics/fire_timing_fault_localization_probe.py --mode structural_toy
```

The probe runs two toy models:

- `free_logits`: one learnable logit per time step. This tests the loss
  surface directly.
- `mlp`: a small MLP that receives explicit normalized age and quality-window
  features. This tests whether a simple parametric actor can learn the
  discriminator when the required state is visible.

Both variants use the active M3-S2 coefficients:

```text
early_mass_coef = 2.0
early_mass_budget = 0.02
early_survival_coef = 8.0
window_delay_coef = 0.5
window_deadline_coef = 0.5
window_deadline_steps = 64
```

## Validation

```bash
python -m compileall -q \
  tools/diagnostics/fire_timing_fault_localization_probe.py --mode structural_toy \
  tests/training/test_fire_timing_fault_localization_contracts.py
```

Outcome: pass.

```bash
python -m pytest tests/training/test_fire_timing_fault_localization_contracts.py -q
```

Outcome: `2 passed`.

## Long Toy Run

Command:

```bash
./.venv/bin/python tools/diagnostics/fire_timing_fault_localization_probe.py --mode structural_toy \
  --model both \
  --prewindow-steps 800 \
  --quality-steps 1080 \
  --train-steps 3000 \
  --learning-rate 0.01 \
  --json-out experiments_tmp/m3s2_structural_toy_probe_20260606.json
```

Artifact:

```text
experiments_tmp/m3s2_structural_toy_probe_20260606.json
```

Final metrics:

| Model | Pass | Prewindow cumulative risk | Prewindow max logit | Quality max logit | First quality crossing | Quality boundary crosses | Window mass |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `free_logits` | yes | `0.009140485` | `-11.375060` | `2.393876` | `800` | `2` | `0.990859449` |
| `mlp` | yes | `0.000005254` | `-17.986553` | `9.366981` | `800` | `1080` | `0.999994695` |

Initial state for both variants used `initial_logit = -6.0`, which corresponds
to a per-step probability near `0.00247` and an unsafe cumulative prewindow
risk near `0.862` across `800` prewindow steps. The toy optimizer learned to
push prewindow logits below the `1 / horizon` scale while crossing the quality
window boundary.

## Decision

This is a strong negative result for the hypothesis that "the grouped M3-S2
loss cannot represent the desired one-shot window pulse." It can.

Therefore, the active air-combat failure should be localized to integration
rather than the pure loss object:

- rollout/sidecar construction may still present a distribution that does not
  match the toy support contract;
- the actor event update may not be training the representation layers that
  carry quality-window discriminators;
- PPO/shared updates may overwrite or dilute the auxiliary event boundary;
- executable action transport may still need a stopping-to-pulse adapter;
- reward ordering remains a separate timing-quality defect, but it is not
  required to explain this structural toy result.

The next analysis should inspect the real M3-S2 update path at the parameter and
feature level: whether quality-window features actually change the
`fire_once` logit, whether selected update parameters include the layers needed
to use those features, and whether the post-update logits are overwritten by
the following PPO update cycle.
