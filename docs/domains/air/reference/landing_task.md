# Landing Task Notes

Language: English canonical; [Chinese companion](landing_task.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/domains/air/reference/landing_task.md`
Owner: `domains/air/landing-task`
Last verified: `2026-08-08`

This document defines the initial landing-task scaffold for the next training
stage after takeoff and cruise.

## Verification Boundary

This page records the repository landing-task interface and maintained scenario
and configuration routes. Code, scenarios, configuration schemas, and focused
tests remain authoritative when they disagree with this narrative.

## Mission Semantics

- `command_code = 4`
- Meaning: runway-aligned landing / final approach task
- `target_heading`: runway final course
- `target_altitude`: runway elevation / landing reference altitude
- `target_speed`: approach reference speed (`Vref`-like target)
- `threshold_crossing_height_m`: target height above the runway threshold for a
  stabilized final; the ILS glideslope reference is aligned to this point
- Vertical path guidance is provided through the existing instrument-style
  `ILS` channels already appended to the observation:
  `ils_valid`, `loc_dev`, `gs_dev`, `dme_m`

The key design choice is to keep landing realism-first:

- lateral and vertical path cues come from localizer / glideslope-like
  observables
- the policy is not given direct runway heading or privileged touchdown-point
  geometry
- runway geometry is used only for reward shaping and success evaluation

For human-facing visualization and scenario semantics, the landing path is now
treated as a sequence rather than a single ground point:

- intercept and stabilize on the ILS final
- cross the runway threshold overhead, not at touchdown
- touchdown inside a runway touchdown zone farther down the runway
- remain controlled through rollout and decelerate to a low-speed stop-like state

## New Task Files

Paths below are repository-relative:

- Training scenario:
  `scenarios/landing/landing_ils_final_train_v1.json`
- Eval scenario:
  `scenarios/landing/landing_ils_final_eval_v1.json`
- Maintained training config:
  `examples/config/training/frozen/execution/p4_landing_retrain_v1.json`
- Historical artifact-provenance config:
  `examples/config/Archive/training/pre_freeze_experiments/p4_landing_full_visual_ils_smoke_v1.json`

## Added Landing Hooks

Environment / objective properties:

- `on_runway_geom`
- `on_runway`
- `on_ground`
- `ground_speed`
- `sink_rate_abs_mps`
- `vertical_speed_abs_mps`
- `ils_localizer_abs`
- `ils_glideslope_abs`
- `dme_m`

Reward hooks:

- `approach_localizer_weight`
- `approach_localizer_improve_weight`
- `approach_glideslope_weight`
- `approach_glideslope_improve_weight`
- `approach_dme_progress_weight`
- `approach_capture_bonus`
- `landing_sink_rate_penalty_weight`

Optional DME-quality gating:

- `approach_dme_progress_localizer_band`
- `approach_dme_progress_glideslope_band`
- `approach_dme_progress_quality_power`

The landing reward design now uses a mixed strategy:

- modest absolute-deviation penalties keep the approach stabilized
- improvement rewards pay for reducing localizer / glideslope error
- DME progress can be gated by ILS quality, so a misaligned dive toward the
  threshold is not rewarded like a stabilized approach
- capture rewards make "continue the approach correctly" better than
  intentionally terminating early

Runway-touchdown success is evaluated with the same practical ground-contact
envelope used by the task logic: in particular, the final `altitude_agl`
success threshold is aligned with the landing `on_ground` threshold rather than
an unrealistically tighter value that rejects stable settled rollouts.

Rollout-stop success should use `ground_speed`, not `speed`/IAS:

- IAS remains air-relative and can stay non-zero in wind even after the aircraft
  is physically stopped on the runway
- rollout completion is therefore judged on low ground speed plus on-runway
  ground-contact conditions
- the ground-contact model now also applies a low-speed brake-hold / static
  stiction behavior so touchdown does not leave a long unrealistic creep tail

Current training defaults also include:

- runway-relative airborne spawn randomization for the landing agent
- training spawn ranges that stay inside a realistic capture envelope so the
  policy first learns runway-course alignment and stabilized final, rather than
  being thrown into unrecoverable offset cases immediately
- a scripted `landing_ils` baseline option for residual PPO training in the
  full 17D action space

These hooks are generic and can support later landing curricula such as:

- stabilized straight-in ILS
- offset-localizer recovery
- crosswind landing
- flare / rollout refinement
- go-around decision tasks

## Limitations

- This is an implemented-interface reference, not evidence that a learned
  landing policy has met an acceptance gate.
- The listed reward hooks describe repository behavior, not a claim of
  aircraft-specific flight-test fidelity.
- Crosswind, flare refinement, go-around decisions, and broader curricula
  remain follow-on work unless separately accepted.
