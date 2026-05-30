# Current Progress

Status: `2026-05-15`

## Delivered

The isolated `game/` subtree now contains a working Godot-first playable branch
shell rather than only planning notes.

Implemented pieces:

- a Godot 4.6 project under `game/client/godot_project/`
- a local authoritative backend under `game/backend/app.py`
- a live WebSocket protocol bridge on `ws://127.0.0.1:8765/game`
- automatic local-session startup from the Godot client
- keyboard-to-backend control input routing
- a `WorldView3D` scene that consumes backend packets directly
- a HUD layer for mission status, task sequence, terminal state, and rewards
- an in-client mission restart flow through `restart_local_session`
- explicit player-aircraft binding for `Lead` and `Wing`
- restart flow that preserves the currently selected player aircraft role

## Reused Repository Results

The current game line already reuses maintained repo outputs instead of creating
a parallel content model:

- scenario JSON world content from `scenarios/*.json`
- environment zones via `map_setup`
- waypoint/route markers via `nav_setup`
- F-16 asset from `examples/viz/web_viz/static/assets/f16.glb`
- authoritative runtime truth from `UniversalEnv` and `SimulationKernel`
- mission naming and task-flow semantics from `python/rl/control/mission_defs.py`
- mission-status shaping logic adapted from `examples/viz/viz_runner.py`

## Current Visual Chain

The Godot client now renders:

- scenario zones as 3D runway / apron planes
- route markers and a waypoint polyline
- ownship as an F-16 model when the imported asset is available
- fallback primitive aircraft visuals when import is unavailable
- non-aircraft scene units such as the control tower with separate visuals
- cooperative scenario units carried through the backend `units` snapshot

The Godot HUD now shows:

- C2 task, phase, command, and waypoint progress
- task-sequence chips derived from maintained mission semantics
- mission transition history
- current player aircraft identity and role semantics
- whether the current slot carries lead authority
- terminal success/failure reason
- reward total and summarized reward terms
- restart affordance after terminal state

Coordinate mapping follows the existing visualization semantics:

- sim `x` -> world `x`
- sim `y` -> world `-z`
- sim `z` -> world `y`
- heading -> yaw `-heading`

## Verified Checks

Completed local checks:

- `./.venv/bin/python -m py_compile game/backend/app.py`
- `/home/void0312/.local/bin/godot --path game/client/godot_project --headless --import`
- `/home/void0312/.local/bin/godot --path game/client/godot_project --headless --quit`
- WebSocket smoke test covering `mission_status` and `restart_local_session`
- `game/scripts/run_game_smoke.sh` automated backend + Godot smoke flow

Additional backend probe confirmed that the cooperative scenario snapshot now
contains multiple units:

- `Lead` as player aircraft
- `Wing` as additional aircraft
- `Control_Tower` as facility

Additional role-binding checks now pass:

- start session as `Lead` -> ownship binds to `Lead`
- start session as `Wing` -> ownship binds to `Wing`
- restart a `Wing` session -> ownship remains `Wing`

Implementation detail:

- the backend now creates a per-session scenario variant under `game/.session_cache/`
- the selected aircraft is moved to the first `is_agent` position before `UniversalEnv` startup
- this reuses the maintained cooperative runtime instead of forking the research-line env API

## Immediate Next Steps

Highest-value next tasks are:

1. expose camera modes such as chase / orbit / tactical overview
2. add limited lead-only high-level command inputs while keeping the player inside a single aircraft slot
3. enrich backend unit serialization with richer non-player flight state
4. add HUD focus switching so the player can inspect other cooperative units
5. add dedicated success/failure presentation and post-mission summary layout

## Automation Notes

The game branch now has a dedicated automation smoke path:

- `game/scripts/run_game_smoke.sh`

It starts a temporary backend on a separate port, launches the Godot client
headlessly under `xvfb`, auto-starts a local playable session, and writes a
JSON debug report that includes:

- whether the player unit was found
- whether the player is in front of the camera
- whether the imported F-16 model is being used
- current camera position and look target
- current player role and entity identity

Default report/log outputs:

- `/tmp/cmo_game_smoke_report.json`
- `/tmp/cmo_game_smoke_backend.log`
- `/tmp/cmo_game_smoke_godot.log`
