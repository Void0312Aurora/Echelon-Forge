# Native Runtime Blockers

Document kind: `work-package evidence`
Lifecycle: `active`
Owner: `domains/ground`
Last verified: `2026-09-24`

## What was blocked and is now admitted

The repository can load a native `UnitType::Ground` infantry definition, and
the 2026-09-24 batch admitted a bounded native movement consumer. A direct
probe now spawns `Ground_Infantry_Soldier_MVP`, sends a maintained
`MissionCommandGround::MoveStatic` command, and observes non-zero velocity plus
horizontal position drift. Surface and slope costs are read from the shared
`IEnvironmentModel`; the focused test removes command-link latency only to
isolate that stage.

The source boundary explains the result:

- `src/systems/domains/ground/movement_system.h` now owns the admitted bounded
  Ground movement slice;
- `src/systems/domains/air/control_system.h` is gated by `FlightModel` and is an
  air control system, not a Ground controller;
- `src/components/domains/ground/command/mission_command_ground.h` still owns
  static task/objective/cadence fields; `MoveStatic` is intentionally the only
  movement directive consumed in this slice;
- the Ground standard explicitly holds route movement, terrain traversal,
  passability, observation export, and learned policy claims.

## Non-blocking substitute

`python/rl/ground/infantry_proxy.py` provides a deterministic, read-only
`ground_infantry_proxy.v1` scaffold.  It consumes the verified Arnis raster and
metadata overlay, normalizes a four-field infantry action, emits a
transport-neutral command shell, and supports reset/step/replay. Its route
transition and semantic bridge-intent rules remain deliberately labelled
`engineering_proxy_only`; the native provider now owns only bounded point
surface classification. The proxy remains useful for contract, trace, and
curriculum development but is not runtime authority and must not be wired into
the production WorldBatch path.

`python/rl/ground/proxy_env.py` wraps the same scaffold in a Gymnasium
`GroundInfantryProxyEnv`, so the RL-side reset/step/observation/reward/
termination/trace boundary can be tested without pretending that a learned
policy is already connected to native Ground truth.

The default environment provider now admits an explicit Arnis continuous
bundle load. It validates the bundle contract, shape, signed metric steps,
exact raster byte lengths, and finite elevation values before replacing the
provider raster. Landcover plus the declared hydrology/bridge road vectors now
supply bounded river and bridge surface classes; tree-line, settlement, route,
and general passability semantics remain unconsumed.

The native release service now admits one bounded Ground direct-fire path. A
Ground attacker must carry the default rifle state, an explicit hostile Ground
contact, and a valid range/ammunition/cooldown state. A successful shot records
the legacy launch seam and enters the shared effects/damage bridge at the
current body-center hitbox bootstrap. This is a deterministic close-range
training proxy: it does not provide line of sight, cover, suppression,
ballistics, indirect fire, or target-selection automation.
The explicit `fire_ground_weapon_from_mission_command` entrypoint additionally
requires an active assigned target and matching fire authority; it is a single
command-triggered release, not an automatic per-tick weapon system.
The bounded `SimulationKernel.get_ground_weapon_state` observation returns the
selected weapon type, ammunition, damage/range tuning, hit probability, and
remaining cooldown for diagnostics and future training observations. It does
not promote the training contract: the RL harness remains proxy-only and no
learned target-selection or fire policy is released.

The existing C++ maintained command contract already carries
`ground_static_task`; the Python binding now exposes that slice as well.  This
removes a transport omission. The new movement system now consumes the admitted
`MoveStatic` subset. The native command now carries `GroundStance` and the
movement system applies bounded stand/crouch/prone speed costs; this does not
release cover, concealment, exposure, or the broader fire-control surface beyond
the separate bounded rifle path.

`python/rl/ground/command.py` therefore projects representable heading/speed,
stance, and static-task fields. It still rejects non-direct route intents because
the current native command shape has no route field; silently dropping it would
make the training trace dishonest.

The proxy observation additionally exposes tree-line/settlement distance and
bearing plus river/bridge flags.  These fields are deliberately labelled
engineering products; they do not satisfy the held native observation/track
export gate.

The proxy fails closed on unknown raster cells, out-of-bounds transitions, and
river crossings without the explicit bridge intent.  The bridge rule is a
temporary test policy, not a released crossing model.

## Remaining unblock package

Before promoting this scaffold beyond the bounded movement and direct-fire
slices, a separate
reviewed Ground owner package must:

1. define the native action/command component and its relationship to the
   maintained command-chain batch bindings;
2. extend the bounded vector sampling into route/passability and observation
   provenance as runtime contracts rather than fixture-local assumptions;
3. add native reset/step/replay acceptance tests over the Arnis-derived map,
   then connect the RL adapter;
4. retain the proxy tests as diagnostics until native behavior supersedes them;
5. replace the rifle's synthetic body-center hit with authored infantry
   hitboxes and a reviewed line-of-sight/cover owner before widening weapon
   employment.

The training contract remains `contract_only`; the current proxy is
intentionally not a `train.py` entry point. The admitted native surfaces are
not a passability, line-of-sight, or map-provider integration.

## Verification residual outside this slice

The composition-evidence C++ gate is green for this batch. The broad `ef_test`
gate still has two pre-existing CUDA resident fixture identity failures: the
fixture contract expects entity base `581`, while the current registry (after
the already-landed Ground damage component admission) produces `583` in this
worktree. The composition migration-closure/P7 fixtures also require a separate
Cordis package-producer refresh; the local checkout has no
`packages/cordis-runtime/node_modules/cordis`, so that refresh was not safely
performed here. These are recorded integration residuals, not evidence of
native infantry movement failure.
