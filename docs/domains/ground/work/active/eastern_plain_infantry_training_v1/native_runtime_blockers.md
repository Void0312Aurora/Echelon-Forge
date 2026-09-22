# Native Runtime Blockers

Document kind: `work-package evidence`
Lifecycle: `active`
Owner: `domains/ground`
Last verified: `2026-09-23`

## What is blocked

The repository can now load a native `UnitType::Ground` infantry definition,
but the maintained C++ composition still has no Ground movement/terrain
consumer.  A direct probe in this worktree spawned
`Ground_Infantry_Soldier_MVP`, called the existing `SimulationKernel.set_command`
surface with a heading and speed, stepped three times, and observed the same
position and zero velocity on every step.  The command transport therefore
does not yet constitute infantry movement.

The source boundary explains the result:

- `src/systems/physics/movement_system.h` only integrates an already-populated
  `Velocity` into `Transform`;
- `src/systems/domains/air/control_system.h` is gated by `FlightModel` and is an
  air control system, not a Ground controller;
- `src/components/domains/ground/command/mission_command_ground.h` currently
  owns static task/objective/cadence fields, not a movement/action state;
- the Ground standard explicitly holds route movement, terrain traversal,
  passability, observation export, and learned policy claims.

## Non-blocking substitute

`python/rl/ground/infantry_proxy.py` provides a deterministic, read-only
`ground_infantry_proxy.v1` scaffold.  It consumes the verified Arnis raster and
metadata overlay, normalizes a four-field infantry action, emits a
transport-neutral command shell, and supports reset/step/replay.  Its speed
and river/bridge rules are deliberately labelled `engineering_proxy_only`.
They are useful for contract, trace, and curriculum development but are not
runtime authority and must not be wired into the production WorldBatch path.

The proxy fails closed on unknown raster cells, out-of-bounds transitions, and
river crossings without the explicit bridge intent.  The bridge rule is a
temporary test policy, not a released crossing model.

## Required unblock package

Before promoting this scaffold, a separate reviewed Ground owner package must:

1. define the native action/command component and its relationship to the
   maintained command-chain batch bindings;
2. register a shared-stage Ground movement system that writes velocity from
   admitted commands and preserves deterministic ordering;
3. define terrain sampling, passability, bridge admission, and observation
   provenance as runtime contracts rather than fixture-local assumptions;
4. add native reset/step/replay acceptance tests, then connect the RL adapter;
5. retain the proxy tests as diagnostics until native behavior supersedes them.

Until those gates pass, the training contract remains `contract_only`; the
current proxy is intentionally not a `train.py` entry point.
