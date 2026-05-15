# Active Landing Artifacts

Use these as the default landing-task references.

- Experiment:
  `/home/void0312/CMO/experiments_tmp/20260317_p4_landing_ils_smoke_v4`
- Maintained training config:
  `/home/void0312/CMO/examples/config/training/frozen/execution/p4_landing_retrain_v1.json`
- Historical artifact-provenance config:
  `/home/void0312/CMO/examples/config/Archive/training/pre_freeze_experiments/p4_landing_full_visual_ils_smoke_v1.json`
- Training scenario:
  `/home/void0312/CMO/scenarios/landing/landing_ils_final_train_v1.json`
- Eval scenario:
  `/home/void0312/CMO/scenarios/landing/landing_ils_final_eval_v1.json`
- Archived landing smoke runs:
  `/home/void0312/CMO/archive/20260317_landing_cleanup/experiments_tmp`

Latest landing-phase validation marker:

- Ground-stop success now uses `ground_speed <= 1.0` instead of IAS.
- Active smoke marker remains `20260317_p4_landing_ils_smoke_v4`.
