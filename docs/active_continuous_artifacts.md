# Active Continuous Artifacts

Use these as the default references for the current takeoff-cruise-landing continuous task.

- Active experiment:
  `/home/void0312/CMO/experiments_tmp/20260318_p5_takeoff_to_landing_continuous_v3_retrain_v1`
- Active model:
  `/home/void0312/CMO/experiments_tmp/20260318_p5_takeoff_to_landing_continuous_v3_retrain_v1/final_model.zip`
- Maintained training config:
  `/home/void0312/CMO/examples/config/training/frozen/execution/p5_continuous_retrain_v1.json`
- Historical artifact-provenance config:
  `/home/void0312/CMO/examples/config/Archive/training/pre_freeze_experiments/p5_takeoff_to_landing_full_visual_navv2_residual_smoke_v3.json`
- Training scenario:
  `/home/void0312/CMO/scenarios/combined/takeoff_to_landing_continuous_train_v1.json`
- Eval scenario:
  `/home/void0312/CMO/scenarios/combined/takeoff_to_landing_continuous_eval_v1.json`

Runtime note:

- The active artifact provenance predates the 2026-04-16 retirement of the exact-step GPU default from the maintained mainline.
- The maintained training config now keeps exact world stepping on CPU and uses
  the compiled world-batch observation and visual helpers by default:
  `batch_observation_backend=compiled` and `batch_visual_backend=compiled`.
- The older mixed `gpu_host` visual line is still reproducible for diagnostics,
  but it is frozen as experimental and is no longer the maintained default.
- `runtime.exact_world_step_backend` remains available only for archived exact-step GPU experiments and is no longer part of the maintained continuous baseline.

Latest validation snapshot:

- Gate-fix only, before landing-controller repair:
  `success rate = 25.0%`
- Post gate-fix retrain:
  `success rate = 50.0%`
- Current active marker after landing-controller + arrival-bridge repair:
  `success rate = 100.0%`
- Current dominant failure mode:
  `none observed in the 4-episode active eval marker`

Useful diagnostics:

- Successful recovered seed:
  `/home/void0312/CMO/artifacts/takeoff_to_landing_continuous/model_gatefix_retrain_seed124.png`
- Failure seed after retrain:
  `/home/void0312/CMO/artifacts/takeoff_to_landing_continuous/model_gatefix_retrain_seed125.png`
- Reference gate-fix success before retrain:
  `/home/void0312/CMO/artifacts/takeoff_to_landing_continuous/model_seed123_gatefix_v2.png`
- Remaining-failure repair marker before final retrain:
  `/home/void0312/CMO/artifacts/takeoff_to_landing_continuous/model_gatefix_retrain_seed126_v3.png`
- Active final-retrain success marker:
  `/home/void0312/CMO/artifacts/takeoff_to_landing_continuous/model_v3_retrain_seed126.png`
