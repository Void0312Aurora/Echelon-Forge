# Archive Tools

`tools/archive/` stores ad hoc probes that were previously left at repo root
and are kept only for manual reference.

Status for this directory is `Archived`. These files are not maintained entry
points for docs, tests, or active workflows.

Archived helpers currently include:

- [check_binding.py](check_binding.py)
  - Manual ef_py binding member probe retained only for direct human inspection.
- [batch_api_probe.py](batch_api_probe.py)
  - Manual probe for the C++ batch preparation API.
- [world_batch_vec_env_benchmark.py](world_batch_vec_env_benchmark.py)
  - Older vec-env throughput benchmark predating the maintained diagnostics layout.
- [diagnose_training_matrix.py](diagnose_training_matrix.py)
  - Legacy evaluation-matrix helper that parses the old `evaluate.py` text summary format.
- [arma_proxy_backend_echelon_env.py](arma_proxy_backend_echelon_env.py)
  - Archived raw `UniversalEnv` Arma proxy backend. The maintained Arma bridge diagnostics surface keeps only the local stub entrypoint.
- [analyze_cooperative_observation_scales.py](analyze_cooperative_observation_scales.py)
  - Archived raw single-env observation scale sampler; the name suggested cooperative coverage but the implementation directly constructed `UniversalEnv`.
- [visual_resolution.py](visual_resolution.py)
  - Archived visual downsample benchmark backed by raw `UniversalEnv`; active benchmarks now expose maintained runtime families only.
- [coarse_route_segments.py](coarse_route_segments.py)
  - Archived coarse route-segment rollout benchmark backed by raw `UniversalEnv` and direct policy loading.
- `legacy_test_diagnostics/`
  - Historical one-off diagnostics migrated out of `tests/diagnostics/` because they are no longer maintained test entrypoints.
- `legacy_scripts/`
  - Historical shell/python workflow wrappers that were superseded by maintained `tools/` entrypoints.
