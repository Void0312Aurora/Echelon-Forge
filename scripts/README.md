# Scripts README

`scripts/` now keeps only a small set of operator-facing workflow shells that
still provide value beyond the maintained Python entrypoints in `tools/`.
The retained scripts are currently air/execution or cooperative/HMoE workflow
shells, not general multi-domain product entrypoints.

Current retained scripts:

- [benchmark_cuda_resident_rb9.py](benchmark_cuda_resident_rb9.py)
  - Merges the separately built RB9 CPU/CUDA diagnostic evidence reports into a
    provisional comparison that stays outside the maintained-backend claim.
  - Imported directly by `tests/architecture/runtime_profiles/test_cuda_resident_performance.py`,
    so it is a test-covered module, not only an operator shell.
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
- New naval or ground workflows should land as maintained `tools/` entrypoints
  before gaining convenience shells here.
- Retained shell workflows should source
  [tools/maintenance/cmo_env.sh](../tools/maintenance/cmo_env.sh)
  so `.venv` and build-dir detection stay unified.
- If a script becomes historical or machine-specific, delete it and add a
  line to the retirement register in `tools/README.md` (git history is the
  archive).
- Workspace cleanup helpers belong under `tools/maintenance/`, not here.
