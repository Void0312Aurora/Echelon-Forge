# Improvement Backlog (Air Combat Focus)

This document lists candidate improvements and why they matter. It is a living
backlog to guide future iterations.

## P0 - Correctness and Consistency
- Flight dynamics: add thrust/drag or specific excess power (SEP) model to make
  speed/altitude/turn tradeoffs consistent.
- Sensor output: unify detection timestamps, fields, and filtering rules to
  avoid inconsistent contact lists.
- Guidance/control coupling: ensure action limits (G, stall) are respected
  consistently across control and movement systems.
- Scenario validation: validate JSON configs against schemas before execution.

## P1 - Realism and Behavior
- Atmosphere model: air density vs altitude to affect drag and climb.
- Missile energy: burnout, drag, and seeker limits (FOV, lock range).
- Radar model: detection probability, SNR thresholds, and track memory.
- Damage model: component-level damage (engine, radar, control surfaces).

## P2 - Training and Analysis
- Action/observation normalization with explicit bounds per unit type.
- Reward templates and event hooks for training.
- Deterministic replay with event logs and metadata snapshots.
- Scenario batch runner for metrics and regression tests.

## P2 - Engineering Hardening
- Keep `pyproject.toml` dependency groups aligned with the maintained smoke,
  RL, training, and world-model entrypoints; add a lockfile or environment file
  before claiming reproducible training runs.
- Shrink root-level training scripts into CLI/orchestration glue. `train.py`
  already uses `python/training/`; `world_model_train.py` should get an
  equivalent staged split before more world-model features are added.
- Promote physics sanity checks into contract tests: takeoff distance bounds,
  climb-rate and speed-envelope limits, fuel monotonicity, weight changes, wind
  influence, and no free energy gain in autopilot paths.
- Prepare a `v0.1.0-alpha` release checklist once build, smoke tests, minimal
  training smoke, known limitations, and artifact-output policy are all
  documented from a fresh environment.

## P3 - Extensibility
- Multi-fidelity models (low/medium/high) selectable per scenario.
- Asset library for unit and weapon definitions with versioned schemas.
- Plug-in style model registry for sensors/guidance/effects.
