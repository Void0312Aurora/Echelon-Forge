# Native Runtime Blockers

Document kind: `work-package evidence`
Lifecycle: `active`
Owner: `domains/ground`
Last verified: `2026-10-01`

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
current body-center hitbox bootstrap. Since `2026-10-01` release also requires
terrain line of sight (item 5 below). This is a deterministic close-range
training proxy: it does not provide cover, concealment, suppression,
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
not a route-level cost grid or general passability product. Since 2026-09-28 the
stance-dependent reduction lives with the Ground owner
(`evaluate_transition_movement_effects` in `movement_effects.h`); the shared
`IEnvironmentModel` keeps only domain-neutral terrain, slope, and transition
queries and no longer carries Ground stance or cost semantics.
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
Each validated segment now also carries the native ten-field sampled movement
observation for the selected stance, so reset-time diagnostics retain terrain
cost evidence instead of only passability flags. This remains fixed-sequence
bookkeeping, not a route-level cost grid or planner.
`python/rl/ground/native_env.py` wraps that probe in a Gymnasium-compatible
reset/step surface for training tooling. The wrapper does not add authority or
alter the native trace; it remains outside production `WorldBatch`. Its
waypoint index/count observation and sequence advancement are bounded tooling
bookkeeping, not a route graph, path planner, or production training release.
The wrapper also exposes explicit `max_steps` and `blocked_step_limit`
truncation reasons instead of requiring a caller to infer them from the trace.
The probe now exposes `replay(actions, seed=...)`, which resets the same native
fixture and returns the reset plus bounded step traces until termination or
truncation. This is an offline deterministic replay helper, not a live-provider
or production WorldBatch entrypoint.

The Gymnasium checker is green without space-design warnings. The native Gym
adapter now declares a normalized three-field heading/speed/stance Box and
keeps `route_intent=direct` as fixed metadata; the probe still accepts the
legacy four-field raw vector for diagnostics. Observation spaces use finite
bounds derived from the verified bundle manifest plus the probe's finite
episode horizon; when a custom bundle manifest cannot be read, the adapter uses
an explicitly finite probe-horizon fallback. These bounds and the normalized
adapter do not promote it to production RL authority.

The proxy fails closed on unknown raster cells, out-of-bounds transitions, and
river crossings without the explicit bridge intent.  The bridge rule is a
temporary test policy, not a released crossing model. It now also exposes
`GroundFieldProxy.plan_bridge_route()`, which enumerates only declared bridge
overlay geometry and returns a deterministic proxy waypoint polyline. It is
useful for curriculum/route-contract development, but remains
`engineering_proxy_only`; it is not a native route graph, general passability
mask, or production planner.

## Remaining unblock package

Before promoting this scaffold beyond the bounded movement and direct-fire
slices, a separate
reviewed Ground owner package must:

1. define the native action/command component and its relationship to the
   maintained command-chain batch bindings;
2. extend the bounded vector sampling into route/passability and observation
   provenance as runtime contracts rather than fixture-local assumptions
   (items 1 and 2 are planned in
   [Ground Command And Route Owner Plan](../../issues/ground_command_and_route_owner_plan.md),
   packets GC-0 to GC-6);
3. extend the existing native reset/step/replay acceptance tests over more of
   the Arnis-derived map before considering any production RL adapter
   (**evidence landed 2026-10-01 at `native_probe_only` scope**, see
   [Item 3 acceptance matrix](#item-3-acceptance-matrix); this alone does not
   admit a production RL adapter, which still needs items 1, 2, and 5);
4. retain the proxy tests as diagnostics until native behavior supersedes them;
5. replace the rifle's synthetic body-center hit with authored infantry
   hitboxes and a reviewed line-of-sight/cover owner before widening weapon
   employment. **Partly unblocked `2026-10-01`:** the line-of-sight owner is the
   environment's domain-neutral
   [terrain line-of-sight query](../../../../../systems/environment/work/active/terrain_line_of_sight_v1/README.md),
   and the rifle gate consumes it before the hit roll: the sight line runs from
   the shooter's eye height to the target's centre-of-mass height for each held
   stance, and blocked or unknown terrain rejects the shot without consuming a
   round. The posture heights are authored `engineering_proxy` content
   (follow-up `TLOS-F1`). Still held: authored infantry hitboxes (the hit point
   is still the synthetic body centre), cover and concealment from vegetation
   and buildings, suppression, and ballistics.

The training contract remains `contract_only`; the current proxy and native Gym
adapter are intentionally not `train.py` or production `WorldBatch` entries.
The admitted native surfaces provide only local sampled passability and terrain
effects; they are not a general route/passability mask, line-of-sight model, or
automatic map-provider integration.

## Item 3 acceptance matrix

Evidence path:

- case derivation: `python/rl/ground/fixture_cases.py`
  (`derive_acceptance_cases`), tested offline by
  `tests/training/test_ground_infantry_fixture_cases.py`;
- native matrix: `python/rl/ground/acceptance_matrix.py`
  (`build_acceptance_matrix`), tested by
  `tests/training/test_ground_infantry_native_acceptance_matrix.py`;
- replay determinism:
  `tests/training/test_ground_infantry_native_replay_determinism.py`;
- S1/S2 stages: `python/rl/ground/curriculum.py` with
  `examples/config/training/active/ground/eastern_plain_infantry_curriculum_stages_v1.json`,
  tested by `tests/training/test_ground_infantry_curriculum_stages.py`.

Cases are derived from the bundle, overlay, and field-acceptance data rather
than typed coordinates. On the checked-in fixture at seed 42 the matrix has 26
cases. All of them match their fixture-derived expectation under the native
probe (measured on the Linux army build, 2026-10-01):

| Category | Cases | Expected | Native outcome |
|---|---|---|---|
| landcover (tree, grass, crop, built-up, bare) | 5 | reach | reach |
| slope band (<p50, p50-p95, p95-p99, >p99) | 4 | reach | reach |
| water (landcover water, river line, floodplain polygon) | 3 | block | `water_transition_blocked`, then `blocked_step_limit` |
| raster edge (outbound x4 / parallel x4) | 8 | block / reach | `obstacle_transition_blocked` / reach |
| bridge (crossing / off-bridge control) | 2 | reach / block | reach with `bridge_admitted` on every step / water block |
| held building footprint | 4 | held | reach (recorded only) |

The native preflight rejects every block case with the same reason the rollout
reports, and every rollout ends with exactly one termination or truncation
reason.

Determinism:

- a same-seed rollout is byte-identical;
- probe `replay` reproduces the env trace;
- seed 42 and seed 43 differ only in the recorded `trace.seed` field, because
  the single-soldier slice draws no seeded randomness.

The scripted heading-to-goal baseline passes both stages:

- S1: 7 admitted flat, open-landcover reach cases;
- S2: 22 admitted cases, 14 reach and 8 fail-closed blocks.

The SB3 PPO smoke completes one short rollout and update on an S1 case. This is
pipeline evidence, not a learning result.

Open decisions, recorded in the stage config and not resolved by this tooling:

- S2 block cases place the waypoint in water or outside the raster. The native
  reward (distance delta minus blocked-attempt penalty) is reused unchanged. A
  stop-at-bank or reroute objective would be a contract change, not a
  coefficient this runner may add.
- Farm-track cost cannot be exercised, because native movement consumes only
  bridge-flagged road vectors.
- Building footprints are traversable natively: all four held cases reach the
  footprint centroid. A collision/cover owner must decide their passability;
  until then they are excluded from S1 and S2.
- The native slope query uses a +/-5 m central difference, while slope bands
  use the field-acceptance estimator. Band membership is therefore a
  fixture-level label, not a native slope classification.
- Near the raster boundary the native slope saturates, because the central
  difference samples out-of-raster elevation. The edge-parallel cases
  therefore run at the 0.20 slope-multiplier floor.

Still held: route planning, line of sight and cover, sensing, and multi-agent
behaviour.

## Verification residual outside this slice

The two integration residuals this section recorded on `2026-09-25` are closed on
`work/army-mechanisms` as of `2026-09-28`:

- the CUDA resident fixture identity failures (contract base `581`, registry `583`)
  are gone because the CPU reference tests no longer pin raw Flecs ids; they assert
  census-independent identity invariants instead (`dbc616fe`, `e674672d`);
- the Cordis package, provenance, parity, and closure evidence were regenerated in the
  documented causal order (`b0a17ab1`); the local `packages/cordis-runtime/node_modules`
  is installed with `npm ci`.

One residual remains and is not owned here. Two Air realism nodes flip on this branch
because stochastic draws are seeded from raw Flecs entity ids, which move with every
composition change. The root fix and its acceptance gate are in
[Stable Entity Identity For Stochastic Draws](../../../../../architecture/work/issues/stable_entity_identity_for_stochastic_draws.md);
neither flip is evidence of a native infantry movement failure.
