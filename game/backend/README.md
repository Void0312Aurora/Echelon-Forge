# Game Backend

This folder is the local backend bridge for the isolated Godot game branch.

It is intentionally separate from:

- `train.py`
- `examples/viz/`
- research-only evaluation/diagnostic entrypoints

The backend bridge should expose a game-facing protocol and keep authoritative
simulation state on the Python side.

Current entrypoint:

- [app.py](/home/void0312/Workshop/CMO/game/backend/app.py)
- [../scripts/run_local_backend.sh](/home/void0312/Workshop/CMO/game/scripts/run_local_backend.sh)
