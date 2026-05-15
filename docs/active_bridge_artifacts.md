# Active Bridge Artifacts

Use these as the default takeoff-to-cruise bridge references.

- Experiment:
  `/home/void0312/CMO/experiments_tmp/20260316_p3_takeoff_to_cruise_mixedmode_worldyawroutefix_retrain_v1`
- Maintained training config:
  `/home/void0312/CMO/examples/config/training/frozen/execution/p3_takeoff_to_cruise_retrain_v1.json`
- Historical artifact-provenance config:
  `/home/void0312/CMO/examples/config/Archive/training/pre_freeze_experiments/p3_takeoff_to_cruise_full_visual_navv2_multileg_smoke_v1.json`
- Training scenario:
  `/home/void0312/CMO/scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_train_v2.json`
- Eval scenario:
  `/home/void0312/CMO/scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json`
- Archived bridge experiment results:
  `/home/void0312/CMO/experiments_tmp/archive_takeoff_to_cruise_bridge_20260316`

Latest validated eval snapshot:

- Seed set `123-126`: `100%` success, `100%` survival, mean reward `14356.41`
- Seed set `1001-1004`: `100%` success, `100%` survival, mean reward `13987.14`

Notes:

- Older takeoff-to-cruise experiment outputs were archived to keep the active path clean.
- Older bridge configs are intentionally retained under `examples/config/Archive/training/pre_freeze_experiments/` for regression comparison and artifact provenance, but they are not the maintained entry points.
