# Maintenance README

`tools/maintenance/` holds workspace cleanup, audit, and local maintenance
helpers that are not part of the model/runtime product surface.

Current maintained helpers:

- [cmo_env.sh](cmo_env.sh)
  - Linux/macOS repository-local environment bootstrap and validation for
    `.venv`, `CMO_BUILD_DIR`, and `PYTHONPATH`.
- [cmo_env.ps1](cmo_env.ps1)
  - Windows/PowerShell repository-local environment bootstrap and validation
    for `.venv`, `CMO_BUILD_DIR`, `PYTHONPATH`, and `ef_py*.pyd` artifacts.
- [redundancy_audit.py](redundancy_audit.py)
  - Audits duplicate/temp-like workspace content.
- [cleanup_redundancy.py](cleanup_redundancy.py)
  - Dry-run or apply cleanup for cache/temp artifacts.
- [isolate_repro_workspace.sh](isolate_repro_workspace.sh)
  - Moves selected experiment/dataset directories aside to create a smaller repro workspace.

Maintenance guidance:

- Scripts here may be shell or Python, but they should be workspace-oriented and
  non-destructive by default.
- Maintained Linux/macOS shell workflows should prefer sourcing `cmo_env.sh`
  instead of duplicating `.venv` and build-dir detection logic.
- Maintained Windows workflows should prefer `cmo_env.ps1` instead of assuming
  WSL, `.venv/bin/python`, or Linux `.so` extension artifacts.
- Historical maintenance helpers should move to `tools/archive/legacy_scripts/`
  instead of accumulating here.

Recommended Linux/macOS usage:

```bash
python -m pip install pytest numpy
cmake -S . -B build-workshop -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build-workshop --target ef_core ef_py -j2
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python -m pytest -q tests/runtime/test_env_config.py
```

This mirrors the CI smoke boundary: install the small smoke dependency set,
build `ef_core` / `ef_py` with CMake, then use `cmo_env.sh` to expose the local
extension. Do not replace this fast loop with `pip install -e .` unless the goal
is specifically to test scikit-build editable installation behavior.

Direct script-mode entrypoints are also supported:

```bash
bash tools/maintenance/cmo_env.sh summary
bash tools/maintenance/cmo_env.sh validate
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/test_env_config.py
```

Recommended Windows/PowerShell usage:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install pytest numpy

cmake -S . -B build-local-win -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build-local-win --target ef_core ef_py -j2

.\tools\maintenance\cmo_env.ps1 validate
.\tools\maintenance\cmo_env.ps1 summary
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\test_env_config.py
```

Windows scope:

- The PowerShell helper is intended for local development smoke tests,
  structural tests, and focused runtime regressions.
- It does not define the local workstation's RL training capability. The
  current documented workflow simply does not cover training setup or run
  management yet.
- It intentionally runs beside `cmo_env.sh`; it should not replace the Linux
  CI workflow.
