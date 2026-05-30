# Echelon Proxy Backend Sync v1

This document describes the first-pass local protocol for:

- Arma SQF <-> `echelon_bridge.dll`
- `echelon_bridge.dll` <-> local authoritative backend

The design goal is to keep the first version simple enough to debug from logs
and robust enough to evolve later into a stricter schema.

## Layers

### SQF <-> DLL

SQF talks to the extension via:

- `callExtension [function, args]`
- `parseSimpleArray` for cached proxy-state payloads

The DLL returns:

- short status strings for control commands
- simple-array payloads for proxy aircraft state

### DLL <-> Backend

The DLL talks to the backend over a local TCP socket using one-line messages.

Default endpoint:

- host: `127.0.0.1`
- port: `8765`

Each request is one UTF-8 line terminated by `\n`.
Fields are tab-separated.

## Control Commands

The SQF layer uses these extension functions:

- `version`
- `ping`
- `configure_backend`
- `begin_session`
- `submit_host_frame`
- `fetch_proxy_state`
- `inject_proxy_state`
- `shutdown`

## SQF Host Frame Payload

`submit_host_frame` sends one argument: a simple array literal with this shape:

```text
[
  protocolVersion,
  worldName,
  missionTimeS,
  deltaTimeS,
  terrainHeightAsl,
  [posX, posY, posZ],
  [velX, velY, velZ],
  [dirX, dirY, dirZ],
  [upX, upY, upZ]
]
```

This is intentionally small. It is enough for:

- map-local timing
- terrain sampling
- proxy feedback
- local debug replay

## Backend Line Protocol

### Begin session

```text
begin_session<TAB>sessionId<TAB>worldName<TAB>proxyClass
```

Expected success reply:

```text
ack<TAB>begin_session
```

### Host frame

```text
host_frame<TAB>sessionId<TAB>context<TAB><sqf-simple-array-literal>
```

Expected reply:

```text
proxy_state<TAB><sqf-simple-array-literal>
```

If the backend has no fresh state, it may return:

```text
ack<TAB>host_frame
```

### Shutdown

```text
shutdown<TAB>sessionId
```

Expected reply:

```text
ack<TAB>shutdown
```

## Proxy State Payload

`fetch_proxy_state` returns a cached simple-array literal with this shape:

```text
[
  frameId,
  [posX, posY, posZ],
  [velX, velY, velZ],
  [dirX, dirY, dirZ],
  [upX, upY, upZ],
  throttle01,
  gearDown01,
  afterburner01,
  stateFlags
]
```

`stateFlags` is a bitfield placeholder for later use, for example:

- bit 0: engine on
- bit 1: destroyed
- bit 2: landed

## First-Pass Constraints

- The protocol is local-only.
- The DLL keeps one active backend endpoint and one active session.
- The DLL caches the last good proxy-state payload.
- Failure to reach the backend must not crash Arma.
- The initial transport is line-based for ease of debugging.

## Known Future Upgrades

- strict JSON or binary schema
- explicit terrain/runway query requests
- richer aircraft systems state
- multi-entity proxy sync
- callback-driven event export from DLL into SQF
