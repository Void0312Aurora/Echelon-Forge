# Scripts README

`scripts/` now keeps only a small set of operator-facing workflow shells that
still provide value beyond the maintained Python entrypoints in `tools/`.

Current retained scripts:

- [benchmark_multi_agent.py](benchmark_multi_agent.py)
  - Thin compatibility launcher for `python.rl.support.multi_agent_benchmark.main`.
  - Kept because it is referenced by existing performance-plan documentation.
- [eval_hmoe_strict_terminal.sh](eval_hmoe_strict_terminal.sh)
  - Convenience shell for strict-endpoint HMoE vs shared cooperative evaluation runs.
- [run_hmoe_cooperative_takeoff_to_cruise_control.sh](run_hmoe_cooperative_takeoff_to_cruise_control.sh)
  - Combined train/eval control script for the maintained HMoE fairness line.
- [train_cruise_waypoints_pipeline.sh](train_cruise_waypoints_pipeline.sh)
  - Legacy-but-still-usable world-model waypoint training pipeline.

Maintenance guidance:

- New maintained workflows should prefer `tools/` entrypoints plus config files,
  not new shell wrappers in `scripts/`.
- Retained shell workflows should source
  [tools/maintenance/cmo_env.sh](../tools/maintenance/cmo_env.sh)
  so `.venv` and build-dir detection stay unified.
- If a script becomes historical or machine-specific, archive it under
  `tools/archive/legacy_scripts/`.
- Workspace cleanup helpers belong under `tools/maintenance/`, not here.
