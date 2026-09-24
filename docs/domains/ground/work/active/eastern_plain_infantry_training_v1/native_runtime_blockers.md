# Native Runtime Blockers

Document kind: `work-package evidence`
Lifecycle: `active`
Owner: `domains/ground`
Last verified: `2026-09-25`

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
The native probe can now optionally spawn one fixed hostile fixture contact and
call that command entrypoint through `fire_from_mission_command()`. The result
records the target damage-state delta, ammunition/cooldown change, and the
second immediate rejection. This is a replayable command/weapon acceptance
surface only; it still does not provide target selection, line of sight, cover,
suppression, ballistics, or a learned fire policy.
The bounded `SimulationKernel.get_ground_weapon_state` observation returns the
selected weapon type, ammunition, damage/range tuning, hit probability, and
remaining cooldown for diagnostics and future training observations. It does
not promote the training contract: the production RL harness remains held,
while the native probe/Gym adapter is explicitly `native_probe_only`; no
learned target-selection or fire policy is released.

The existing C++ maintained command contract already carries
`ground_static_task`; the Python binding now exposes that slice as well.  This
removes a transport omission. The movement system consumes the admitted
`MoveStatic` subset and now explicitly accepts `OccupyStatic` and
`SupportStatic` as zero-velocity position-hold commands. The native command now
carries `GroundStance` and the movement system applies bounded
stand/crouch/prone speed costs; these task modes do not release cover,
concealment, exposure, or the broader fire-control surface beyond the separate
bounded rifle path.

`python/rl/ground/command.py` therefore projects representable heading/speed,
stance, and static-task fields. It still rejects non-direct route intents because
the current native command shape has no route field; silently dropping it would
make the training trace dishonest.

The proxy observation additionally exposes tree-line/settlement distance and
bearing plus river/bridge flags. The native provider now admits a bounded
metadata-only field observation with the same distance/bearing and in-feature
flags after an explicit overlay load. These fields do not satisfy a cover,
concealment, route, or track-observation gate.

The native movement slice now applies a bounded vegetation-density speed cost
to Arnis landcover classes while retaining the existing surface and slope
costs. It also checks the one-tick destination cell and blocks transitions into
water or unknown/obstacle terrain without advancing the transform. These are
movement effects only; they are not a tree-line cover, concealment, collision,
route graph, or line-of-sight model. The shared native transition query samples
the one-tick segment at 5 m intervals, reports water/obstacle blockers, and
marks a declared bridge segment as admitted. It remains a local passability
probe, not route planning; the native training probe may only advance through a
preconfigured direct waypoint sequence after a point is reached.
The companion `get_ground_transition_movement_observation` owner uses the same
sample points to report minimum/average combined movement multipliers and sample
count for a selected stance. Ground movement consumes the segment average after
the transition is admitted, so a step crossing a surface boundary no longer
uses only the start-cell multiplier. This remains local segment movement cost,
not a route-level cost grid or general passability product.
The native acceptance suite also drives a soldier from one side of the fixture
river to the other along the declared bridge segment in one bounded step. The
position crosses the river and the sampled transition retains
`bridge_admitted=1`; this is evidence for the admitted local bridge transition,
not automatic bridge finding or route-level river-crossing planning.
The same local terrain owner now exposes `SimulationKernel.get_ground_slope_deg`
to the native probe, so the training trace can attribute movement cost to a
replayable slope observation rather than recomputing it in Python. This remains
a slope observation only; climbability, fatigue, and full terrain physics stay
held. The shared `movement_effects.h` owner now also exposes the surface,
vegetation, stance, and combined speed multipliers through
`SimulationKernel.get_ground_movement_effect_observation`; the movement system
and native probe consume the same calculation rather than maintaining two
independent Python formulas.

`python/rl/ground/native_probe.py` now supplies a deterministic native
reset/step/trace/replay adapter over these admitted surfaces. Its blocked-step
reason now comes from the native sampled transition evidence when available
(water versus obstacle), rather than silently inferring a cause from the
current terrain cell. It is explicitly `native_probe_only` and remains outside
production WorldBatch; route intent, learned policy training, and automatic
weapon employment remain held.
The probe also exposes `validate_waypoint_sequence()`, a read-only preflight of
the configured direct polyline. It returns each native seven-field transition
observation and the first blocked segment/reason, allowing a training reset to
fail closed on an impossible fixture route without pretending to plan around
it. This is sequence validation only; it does not create a route graph or a
path-planning authority.
`python/rl/ground/native_env.py` wraps that probe in a Gymnasium-compatible
reset/step surface for training tooling. The wrapper does not add authority or
alter the native trace; it remains outside production `WorldBatch`. Its
waypoint index/count observation and sequence advancement are bounded tooling
bookkeeping, not a route graph, path planner, or production training release.
The wrapper also exposes explicit `max_steps` and `blocked_step_limit`
truncation reasons instead of requiring a caller to infer them from the trace.

The Gymnasium checker is green and now reports two non-blocking space-design
warnings: the native action's route-intent dimension is a fixed direct-only Box
dimension, and the action vector is not normalized. Observation spaces now use
finite bounds derived from the verified bundle manifest plus the probe's finite
episode horizon; when a custom bundle manifest cannot be read, the adapter uses
an explicitly finite probe-horizon fallback. These bounds do not promote the
adapter to production RL authority; a later owner may replace the fixed action
dimension and normalize the action contract.

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
3. extend the existing native reset/step/replay acceptance tests over more of
   the Arnis-derived map before considering any production RL adapter;
4. retain the proxy tests as diagnostics until native behavior supersedes them;
5. replace the rifle's synthetic body-center hit with authored infantry
   hitboxes and a reviewed line-of-sight/cover owner before widening weapon
   employment.

The training contract remains `contract_only`; the current proxy and native Gym
adapter are intentionally not `train.py` or production `WorldBatch` entries.
The admitted native surfaces provide only local sampled passability and terrain
effects; they are not a general route/passability mask, line-of-sight model, or
automatic map-provider integration.

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
