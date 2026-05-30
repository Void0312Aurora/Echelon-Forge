# Game Backend Integration Contract

Status: `2026-05-15` bootstrap contract for the isolated Godot game branch.

## 1. Authority Model

The Godot client is not the simulation authority.

The authoritative state remains in a local Python backend process that bridges
into the repository runtime/simulation stack.

The client sends:

- player control input
- session commands
- content selection commands

The backend sends:

- state snapshots
- event messages
- session lifecycle acknowledgements

## 2. First Transport Choice

The first maintained transport should be a local WebSocket connection:

- default URL: `ws://127.0.0.1:8765/game`
- one Godot client connects to one local backend session

This keeps the client and backend physically separated while remaining easy to
debug.

## 3. Message Families

### `hello`

Backend capability advertisement after socket open.

Example:

```json
{
  "type": "hello",
  "backend": "cmo_game_bridge",
  "protocol_version": 1,
  "features": ["local_session", "state_snapshot", "state_event"]
}
```

### `game_command`

Used for coarse game/session actions.

Example:

```json
{
  "type": "game_command",
  "command": "start_local_session",
  "payload": {
    "mode": "prototype_takeoff_patrol_rtb",
    "scenario": "scenarios/combined/cooperative_takeoff_to_cruise_paramroute_navv2_train_v1.json"
  }
}
```

### `client_input`

Used for player flight/control input.

Example:

```json
{
  "type": "client_input",
  "player_slot": "player_1",
  "tick": 1024,
  "axes": {
    "pitch": 0.10,
    "roll": -0.05,
    "yaw": 0.00,
    "throttle": 0.92
  },
  "toggles": {
    "gear": false,
    "brake": false,
    "fire_weapon": false
  }
}
```

### `state_snapshot`

Authoritative state bundle for HUD/view updates.

Example:

```json
{
  "type": "state_snapshot",
  "session_id": "local-0001",
  "mission_label": "Prototype Takeoff Patrol RTB",
  "player_slot": "player_1",
  "sim_time_s": 18.40,
  "paused": false,
  "ownship": {
    "name": "Lead",
    "alt_m": 142.2,
    "ias_mps": 79.3,
    "heading_deg": 88.6
  },
  "objective": {
    "phase": "departure",
    "task": "join_route",
    "success": false
  }
}
```

### `state_event`

Discrete event message for timeline/UI notifications.

Example:

```json
{
  "type": "state_event",
  "event": "mission_phase_changed",
  "session_id": "local-0001",
  "payload": {
    "from": "takeoff_roll",
    "to": "departure"
  }
}
```

## 4. Snapshot Design Rules

1. Do not stream raw training observations as the public game contract.
2. Prefer semantically named DTO fields.
3. Keep the first snapshot compact and HUD-oriented.
4. Expand with explicit versioning when gameplay needs grow.

## 5. Backend Bridge Scope

The backend bridge should eventually own:

- local session lifecycle
- scenario selection
- player-slot binding
- translation from game input into backend control surfaces
- serialization from runtime truth into client DTOs

The backend bridge should not:

- clone simulation rules into `game/backend/`
- create an alternate truth model that diverges from maintained runtime behavior

## 6. Immediate Implementation Target

The first backend target is intentionally small:

- start one local session
- accept one player slot
- emit one periodic `state_snapshot`
- support `start_local_session` and `disconnect`

That is enough to let the Godot client become a real game-facing shell without
yet committing to a large multiplayer or content pipeline design.
