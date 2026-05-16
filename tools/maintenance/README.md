# Maintenance README

`tools/maintenance/` holds workspace cleanup, audit, and local maintenance
helpers that are not part of the model/runtime product surface.

Current maintained helpers:

- [cmo_env.sh](/home/void0312/Workshop/CMO/tools/maintenance/cmo_env.sh)
  - Repository-local environment bootstrap and validation for `.venv`, `CMO_BUILD_DIR`, and `PYTHONPATH`.
- [redundancy_audit.py](/home/void0312/Workshop/CMO/tools/maintenance/redundancy_audit.py)
  - Audits duplicate/temp-like workspace content.
- [cleanup_redundancy.py](/home/void0312/Workshop/CMO/tools/maintenance/cleanup_redundancy.py)
  - Dry-run or apply cleanup for cache/temp artifacts.
- [isolate_repro_workspace.sh](/home/void0312/Workshop/CMO/tools/maintenance/isolate_repro_workspace.sh)
  - Moves selected experiment/dataset directories aside to create a smaller repro workspace.

Maintenance guidance:

- Scripts here may be shell or Python, but they should be workspace-oriented and
  non-destructive by default.
- Maintained shell workflows should prefer sourcing `cmo_env.sh` instead of
  duplicating `.venv` and build-dir detection logic.
- Historical maintenance helpers should move to `tools/archive/legacy_scripts/`
  instead of accumulating here.

Recommended usage:

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python -m pytest -q tests/runtime/test_env_config.py
```

Direct script-mode entrypoints are also supported:

```bash
bash tools/maintenance/cmo_env.sh summary
bash tools/maintenance/cmo_env.sh validate
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/test_env_config.py
```
