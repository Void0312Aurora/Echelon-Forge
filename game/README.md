# CMO Game Branch

`game/` is the isolated game-line workspace for the playable Godot client and
its backend bridge.

This subtree is intentionally separated from the research/training path:

- game-only plans, contracts, and design notes live under `game/docs/`
- the Godot client lives under `game/client/`
- the game-backend bridge lives under `game/backend/`
- protocol-facing notes live under `game/protocol/`

Do not place game-line planning notes in the repo-root `docs/` tree unless they
also affect the maintained research/runtime mainline.

## Current Layout

```text
game/
  backend/
  client/
    godot_project/
  docs/
  protocol/
```

## Local Usage

Open the Godot client:

```bash
game/scripts/run_godot_client.sh
```

Run the local backend bridge:

```bash
game/scripts/run_local_backend.sh
```

Run the automated game smoke/debug flow:

```bash
game/scripts/run_game_smoke.sh
```

This smoke runner will:

- launch a temporary local backend on a separate port
- start the Godot client in automation mode under `xvfb`
- auto-enter a local session as `Lead` by default
- capture a machine-readable render/debug report
- exit non-zero if the player unit is missing, not visible, or the imported F-16 model is not in use

Current implementation status:

- [docs/current_progress.md](/home/void0312/Workshop/CMO/game/docs/current_progress.md)

## Near-Term Goal

The first maintained game milestone is:

- a Godot client that owns presentation, input, UI, camera, and game session UX
- a local Python backend that remains authoritative for simulation state
- a stable protocol boundary between the two

See:

- [docs/README.md](/home/void0312/Workshop/CMO/game/docs/README.md)
- [docs/godot_game_branch_plan.md](/home/void0312/Workshop/CMO/game/docs/godot_game_branch_plan.md)
- [docs/backend_integration_contract.md](/home/void0312/Workshop/CMO/game/docs/backend_integration_contract.md)
