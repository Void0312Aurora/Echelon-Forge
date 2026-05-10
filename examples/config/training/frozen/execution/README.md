# Frozen Execution Curriculum

This directory contains the maintained post-freeze execution-layer curriculum.

## Stage Order

1. [p2_takeoff_retrain_v1.json](/home/void0312/CMO/examples/config/training/frozen/execution/p2_takeoff_retrain_v1.json)
2. [p3_takeoff_to_cruise_retrain_v1.json](/home/void0312/CMO/examples/config/training/frozen/execution/p3_takeoff_to_cruise_retrain_v1.json)
3. [p4_landing_retrain_v1.json](/home/void0312/CMO/examples/config/training/frozen/execution/p4_landing_retrain_v1.json)
4. [p4b_cruise_to_landing_retrain_v1.json](/home/void0312/CMO/examples/config/training/frozen/execution/p4b_cruise_to_landing_retrain_v1.json)
5. [p5_continuous_retrain_v1.json](/home/void0312/CMO/examples/config/training/frozen/execution/p5_continuous_retrain_v1.json)
6. [p5_continuous_coldstart_retrain_v2.json](/home/void0312/CMO/examples/config/training/frozen/execution/p5_continuous_coldstart_retrain_v2.json)

## Recommended Scenario Pairing

- `p2`
  - `scenarios/takeoff/takeoff_stage1_runway45_stresswind.json`
- `p3`
  - `scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_train_v2.json`
- `p4`
  - `scenarios/landing/landing_ils_final_train_v1.json`
- `p4b`
  - `scenarios/combined/cruise_to_landing_continuous_train_v1.json`
- `p5`
  - `scenarios/combined/takeoff_to_landing_continuous_train_v1.json`
- `p5 coldstart`
  - `scenarios/combined/takeoff_to_landing_continuous_train_v1.json`

## Notes

- These configs are now aligned to the historically successful `p2/p3/p4/p5` training backups instead of the earlier first-pass rewrite.
- `p2` follows the archived takeoff-departure controller-fix line, because that is the strongest surviving runway-takeoff reference in the repo.
- `p3`, `p4`, and `p5` intentionally mirror the historical successful retrain/smoke configs with minimal drift.
- The dedicated `p4b` bridge is still new, but its budget and curriculum now stay in-family with the historical `p5` continuous line.
- The execution configs now set `env.step_info_mode=terminal` by default. This keeps terminal diagnostics while avoiding per-step step-info packaging on the hot path.
- As of the validated `p5` comparison on 2026-04-18, the maintained `p5`
  configs now default to the CPU-mainline world-batch path:
  `runtime.world_batch_vec_env=true`, `batch_observation_backend=compiled`,
  `batch_visual_backend=compiled`, and
  `env.execution_step_runtime_mode=compiled`.
- Maintained runtime stance:
  exact world stepping stays on the CPU `SimulationKernel::step()` path, and
  the maintained default avoids optional GPU helper selection unless a later
  benchmark re-promotes one explicitly.
- `batch_visual_backend` now stays on `compiled` by default because the latest
  maintained `p5` training and rollout-side comparisons showed the retained
  `gpu_host` helper was functional but slower on the current production path.
- `batch_observation_backend` also stays on `compiled`. The broader
  `gpu_host/fullgpu` observation line remains available only for controlled
  benchmarking and compatibility checks, not as the maintained default.
- Expected build/runtime matrix for the maintained `p5` configs:
  - CPU-only build:
    `world_batch_vec_env` stays available, and the visual/observation helpers
    stay on maintained compiled CPU paths.
  - CUDA build without an available runtime device:
    the same config remains launchable with the same compiled defaults.
  - CUDA build with an available runtime device:
    the maintained config still stays on the same compiled defaults; optional
    `gpu_host` helper experiments remain explicit opt-in overrides only.
- `p5_continuous_retrain_v1.json` is a warm-start/continuation config. It mirrors the historical successful `p5` retrain, but with `32768` total timesteps and `4` envs it only gives each env `8192` steps, about `409.6 s` of simulated time.
- The current full continuous route is about `121-125 km`, which is roughly `755-776 s` at the scenario's waypoint speed profile. Cold-start `p5` training therefore cannot reliably see a full mission completion under `v1`.
- Use `p5_continuous_coldstart_retrain_v2.json` for cold-start/full-route retraining on the new architecture. It reduces `n_envs` and raises total timesteps so each env can experience multiple full episodes.
