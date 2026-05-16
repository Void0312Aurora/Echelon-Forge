# Archive Tools

`tools/archive/` stores ad hoc probes that were previously left at repo root
and are kept only for manual reference.

Archived helpers currently include:

- [check_binding.py](/home/void0312/Workshop/CMO/tools/archive/check_binding.py)
  - Manual ef_py binding member probe retained only for direct human inspection.
- [batch_api_probe.py](/home/void0312/Workshop/CMO/tools/archive/batch_api_probe.py)
  - Manual probe for the C++ batch preparation API.
- [world_batch_vec_env_benchmark.py](/home/void0312/Workshop/CMO/tools/archive/world_batch_vec_env_benchmark.py)
  - Older vec-env throughput benchmark predating the maintained diagnostics layout.
- [diagnose_training_matrix.py](/home/void0312/Workshop/CMO/tools/archive/diagnose_training_matrix.py)
  - Legacy evaluation-matrix helper that parses the old `evaluate.py` text summary format.
- `legacy_test_diagnostics/`
  - Historical one-off diagnostics migrated out of `tests/diagnostics/` because they are no longer maintained test entrypoints.
- `legacy_scripts/`
  - Historical shell/python workflow wrappers that were superseded by maintained `tools/` entrypoints.
