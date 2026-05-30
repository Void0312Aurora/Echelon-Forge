# Godot Game Branch Plan

Status: `2026-05-15` draft bootstrap for the isolated playable branch.

## 1. Branch Intent

This branch is not a thin reskin of `examples/viz/viz_runner.py`.

It is a separate game-line workspace with its own client, backend bridge, and
docs. The repository's research/runtime stack remains the simulation authority,
but the user-facing game shell moves into a dedicated Godot client.

## 2. Why Godot Now

The game line is expected to be long-lived and structurally separate from the
research line.

That means the top-level client choice should be made before deeper UI/input
work:

- camera flow belongs to the game client
- input mapping belongs to the game client
- menus, HUD, audio, scene composition, and session UX belong to the game client
- the simulation authority remains in the Python/C++ backend

Deferring the engine choice would force a later rewrite of the same game-facing
systems, so the game line should start directly on Godot.

## 3. Architectural Direction

The maintained split is:

```text
Godot Client
  -> game protocol
    -> Python game backend bridge
      -> repo simulation/runtime stack
```

### Godot client owns

- rendering and camera
- player input
- game HUD and menus
- session UX
- client-side interpolation / presentation smoothing

### Python backend owns

- authoritative world state
- scenario loading
- mission flow truth
- AI helper control
- simulation stepping
- player command application to backend truth state

## 4. Separation Rules

1. Game-only plans live under `game/docs/`.
2. The Godot client must not import or embed research-line planning concerns.
3. The backend bridge should consume maintained repo APIs instead of copying
   simulation logic into the Godot client.
4. `examples/viz/` remains a prototype/reference path, not the ownership home
   of the playable branch.
5. The first backend milestone should expose typed snapshots/events instead of
   raw training observations.

## 5. Folder Layout

```text
game/
  backend/
    app.py
  client/
    godot_project/
  docs/
  protocol/
```

Recommended future expansion:

```text
game/
  backend/
    app.py
    session_manager.py
    game_runtime.py
    mission_flow.py
    state_serializer.py
  client/
    godot_project/
      scenes/
      scripts/
      assets/
  docs/
  protocol/
    schemas/
```

## 6. First Playable Milestones

### M1: Client bootstrap

- isolated `game/` subtree exists
- Godot project opens successfully
- client can connect to a local backend URL
- UI exposes connection/session placeholders

### M2: Local authoritative session

- Python backend can start a local playable session
- player input is sent from Godot to backend
- backend emits state snapshots and events
- client displays mission/session status and local world telemetry

### M3: Playable loop

- takeoff or air-start mission loads
- player controls ownship
- mission goal state is exposed through HUD
- failure/success/reset loop works

### M4: Project-identity features

- AI wingman or cooperative helper
- simplified command wheel / tactic input
- mission phase transitions surfaced in the HUD

## 7. First Technical Priorities

1. Keep Godot and backend as separate processes.
2. Define a stable message contract before adding rich presentation details.
3. Keep the first playable loop small: one mission, one player slot, one local
   backend.
4. Reuse repo scenarios and runtime semantics rather than inventing a parallel
   game-only simulation model.

## 8. Immediate Next Steps

1. Flesh out the backend bridge under `game/backend/`.
2. Replace placeholder UI labels with live connection/session data.
3. Define the first prototype mission profile under `game/protocol/` or
   `game/content/`.
4. Add an explicit backend launch script for the Godot client.
