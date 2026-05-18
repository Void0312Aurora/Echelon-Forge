# Python-Layer README vs Code Review

## python/README.md

### Verified
- Root-level files (`artifact_paths.py`, `env_config.py`, `mission_obs_taxonomy.py`, `training_callbacks.py`) — all exist.
- Compatibility shims: `scenario_compiler.py` and `scenario_runtime.py` — confirmed as re-export shims.
- All 8 `rl/` subdirectories exist with described files.
- `testing/`, `training/`, `world_model/`, `models/` — all files match description.

No mismatches found.

---

## python/training/README.md

### Verified
- `cli.py` and `bootstrap.py` — exist and match descriptions.

No mismatches found.

---

## gym_envs/README.md

### Verified
- `universal_env.py`, `leader_env.py` — exist.
- `universal_env_parts/` files, `scenario_loader/` structure, `leader_env_parts/` structure — all match.

### Mismatches
- **Missing `common.py`** in `universal_env_parts/` file listing. Actual directory has `common.py` (1888 bytes). Severity: P2.
- **Missing `runtime_facade.py`** in `leader_env_parts/` file listing. Actual file is 19359 bytes — substantial module. Severity: P2.

---

## tests/README.md

### Verified
- All 12 listed directories in "Current Structure" exist.
- Contract types map to existing modules.
- Compatibility shim claims are accurate.

### Mismatches
- **`tests/architecture/` not listed** in "Current Structure". Directory exists with 2 test files. Severity: P2.
- **`tests/contracts/env/` not documented**. Directory exists with 6 subdirectories, 29 JSON contracts. Severity: P2.
- **`tests/contracts/unit/env/` not documented**. Directory exists with 6 JSON files. Severity: P2.
- Naming conventions section missing entries for `controllers/`, `config/`, `naval/` directories. Severity: P3.
- `tests/contracts/bridges/*.json` listed twice — copy-paste error. Severity: P3.
- `tests/diagnostics/` described as containing scripts but contains only READMEs. Severity: P3.

---

## tools/README.md

### Verified
- All 5 subdirectories exist. All listed files in `eval/`, `runners/`, `diagnostics/`, `maintenance/`, `archive/` exist.

### Mismatches
- `tools/archive/check_binding.py` exists but not listed in main README (covered by archive README). Severity: P3.

---

## tools/diagnostics/README.md

### Verified
- All listed diagnostics files, benchmark families, GPU phase-0 probe files — exist.

### Mismatches
- **Unlisted files**: `analyze_cooperative_observation_scales.py` and `trace_training_nonfinite_source.py` exist but not mentioned. Severity: P2.

---

## tools/maintenance/README.md

### Verified
- All files exist and match descriptions.

No mismatches found.

---

## examples/README.md

### Verified
- All config directories exist. `scenarios/`, `viz/` subdirectories match.

### Mismatches
- **`examples/agents/` not documented**. Directory exists with `red_agent.py` (7384 bytes). Severity: P2.
- `examples/config/training/curriculum/` not mentioned. Severity: P3.

---

## Root README.md

### Verified
- `train.py`, `evaluate.py`, `world_model_train.py` — all exist.
- All 9 `scenarios/` subdirectories exist.
- Maintained smoke test paths — all verified.

No mismatches found.

---

## docs/README.md

### Verified
- All referenced paths exist.

No mismatches found.

---

## Summary

| Severity | Count | Details |
|----------|-------|---------|
| P2 | 7 | Documentation omissions (missing files in listings) |
| P3 | 6 | Editorial/minor (duplicated entries, stale descriptions) |
| P0/P1 | 0 | No critical path/claim mismatches |

The Python-layer READMEs are the most accurate documentation domain — no fabricated paths or feature claims.
