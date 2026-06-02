# Ground / Army Current Progress Tracking

Status: `2026-05-26` workspace sampling review.

This is the active tracking entry for `docs/task/ground/` after the G0-G5
ground bootstrap line opened on `2026-05-21`. It tracks the Army/ground line
across infrastructure, domain semantics, and RL/tasking integration.

Current positioning:

- `services/army` is the service-profile boundary.
- `ground` is the maintained execution-specialization name; `army` and `land`
  are accepted aliases that normalize to `ground`.
- G0-G4 are sealed as the accepted tasking baseline.
- G5 has a canonical MVP scenario shell that proves loader plus tasking
  status-chain participation only.
- G6 adds the first two G1 realism-gradient fixtures for static occupy and
  support relationship semantics.
- G6-D selects the schema-first route-move release posture. D1/D2 preflight
  confirmed the first G2 route-move scenario must wait for a runtime-loadable
  native ground platform schema.
- G6-E0 opens the native ground platform schema planning package and defines
  the minimum load/spawn/identity evidence needed before route movement can be
  reconsidered.
- G6-E1 accepts the source-inventory/design preflight: the first native schema
  implementation should use `UnitType::Ground`, `type = "Ground"`,
  `Ground_Platoon_MVP`, and existing type-name/default factory materialization.
- G6-E2/E3 accept the first native ground platform schema evidence:
  `Ground_Platoon_MVP` loads, spawns, reports `UnitType::Ground`, and exposes
  static runtime inspection state through shared surfaces.
- Real ground movement, terrain interaction, sensing, fires, damage, and
  observation export are still deferred.

Terminology note: the project phase `G6 Realism Gradient MVP Scenarios` is not
the same as the domain-realism grade `G6 effects/damage/termination`; this
phase ships only `G1` realism fixtures.

## Current Conclusion

The Army/ground line is currently a maintained tasking and planning baseline,
not yet a maintained ground-combat runtime.

What is already real:

- a standards split between `joint/common core`, `services/army`, and `ground`;
- ground aliases and Army service-profile inference in Python tasking dispatch;
- starter ground task semantics for `TASK_MOVE`, `TASK_OCCUPY`, and
  `TASK_SUPPORT`;
- a non-runtime content seed for a platoon-centered ground unit;
- runnable common-core ground task contracts;
- a G4 runtime bridge proving normalized ground `TaskOrder -> LeaderIntent ->
  PilotReport`;
- a G5 scenario smoke shell under `scenarios/ground/`;
- two G6 G1 scenarios for static occupy/support relationship semantics;
- a G6-E0 native schema planning package that names the minimum implementation
  surface for loadable/spawnable native ground identity;
- a G6-E1 design decision that avoids a new typed-platform/facade path for the
  first schema slice;
- a G6-E2/E3 native schema slice that makes `Ground_Platoon_MVP` loadable,
  spawnable, and inspectable as native `Ground` without releasing movement;
- RL/runtime entry points now route mission-command construction through the
  shared tasking bridge rather than an air-only path.

The remaining risk is mostly boundary discipline: it is easy to over-read the
G5 smoke scenario as a real ground unit or movement proof. The current evidence
only supports Army/ground tasking-chain participation.

## Domain Realism Gradient Critical Points

Ground-domain realism should rise with the complexity actually used by a
scenario. The project should not claim "ground realism" as one flat label.
Instead, each scenario should declare the realism grade it enters and provide
tests or contracts for that grade's minimum critical points.

Principles:

- A tasking-only smoke scenario only needs task semantics, service-profile
  alignment, and status-chain realism.
- A simple movement or cruise-style scenario must add mobility, speed,
  formation, route, and terrain-passability realism, but it does not need fire
  control or damage realism.
- A contact/report scenario must add sensing, line-of-sight, track memory,
  report latency, and information-state boundaries.
- A firefight scenario must first add ROE, target identification, weapon
  envelopes, suppression/effects, damage, and termination gates.
- Unused domain capabilities may remain MVP, but they must not support realism
  claims for a more complex scenario.

Recommended gradient:

| Grade | Scenario entry | Minimum realism requirement | Current state |
|-------|----------------|-----------------------------|---------------|
| `G0` tasking/status | `TaskOrder -> LeaderIntent -> PilotReport` is the scenario goal | `Army` service profile, normalized `ground` tasking profile, command/support IDs, active status shell | Implemented and validated |
| `G1` static occupy/support | Unit is assigned to occupy, support, or hold an area without movement simulation | objective/area references, support relationship, tactical cadence, status/report semantics | Implemented for static occupy and support relationship compatibility-shell fixtures |
| `G2` movement/cruise | ground unit moves along route or toward objective | speed limits, acceleration/deceleration, formation spacing, waypoint/route following, passable surface, stuck/off-route checks | Not implemented |
| `G3` terrain-aware movement | terrain affects movement or path choice | terrain class, slope/obstacle/passability, cover/concealment placeholders, route cost, movement degradation | Not implemented |
| `G4` contact/report | detecting or reporting ground contacts matters | terrain/LOS gating, visual/acoustic sensor parameters, track memory/confidence, report latency, no world-truth observation leak | Not implemented |
| `G5` ROE/fires | direct or indirect fire affects decisions | target ID, ROE/authorization, weapon envelope, range/arcs/cooldown/ammo, fire event/rejection evidence | Not implemented |
| `G6` effects/damage/termination | combat outcome depends on damage or suppression | hit/effect model, suppression, mobility/sensor/mission kill, capability degradation, reward and termination binding | Not implemented |
| `G7` sustainment/logistics | resupply, casualty recovery, or endurance is core | ammunition/fuel/store state, support windows, transfer constraints, degraded readiness over time | Not implemented |

Current ground placement:

- `ground_platoon_tasking_smoke_v1` is a `G0` scenario.
- `TASK_OCCUPY` in that scenario is not yet `G1` occupy realism; it is only a
  tasking intent used to validate the status chain.
- `ground_platoon_static_occupy_v1` and
  `ground_platoon_support_relationship_v1` are `G1` scenarios. They prove
  static occupy/support status semantics only, not movement, terrain, sensing,
  fires, damage, or native ground platform behavior.
- `G6-C` adds route-move boundary guardrails but does not release `G2`
  movement. `ground_platoon_flat_route_move_v1` remains held.
- `G6-D` chooses the schema-first route-move release path. The current
  `Aircraft` compatibility spawn shell is not accepted as evidence for G2
  movement realism.
- `G6-D1/D2` preflight found that the runtime lacked an accepted `Ground` unit
  type/schema at that time. That historical blocker is the one `G6-E2/E3` now
  closes for schema identity.
- `G6-E0` defines the native schema package boundary and records the files,
  tests, and evidence needed for the first native ground platform
  implementation.
- `G6-E1` selects the E2 route: add public `UnitType::Ground`, parse
  `type = "Ground"`, add `Ground_Platoon_MVP`, reuse default-factory spawn, and
  assert identity through existing `get_unit_type()`.
- `G6-E2/E3` accept the native schema evidence: the database loads
  `Ground_Platoon_MVP`, spawn returns a non-null entity, Python identity is
  `ef_py.UnitType.Ground`, the entity is not an air/naval/facility substitute,
  and malformed ground schemas fail closed.
- This closes schema identity only; it does not release `G2` movement.
- Any next scenario must declare whether it remains `G0`, moves to `G1`, or
  enters `G2+`, and it must add the corresponding gates before claiming
  realism at that level.

## Infrastructure

Standards and planning:

- [US Army profile](../../standards/services/army.md)
- [Ground standards overview](../../standards/ground/README.md)
- [Ground minimal task structure](../../standards/ground/minimal_task_structure.md)
- [Ground bootstrap plan](./ground_domain_bootstrap_plan_20260521.md)
- [Ground defect inventory](../review/ground_domain_defect_inventory_20260522.md)
- [G6-E native ground platform schema](archive/g6_native_ground_platform_schema/README.md)

Accepted task phases:

- `G0 Boundary Freeze`: naming, layer model, starter scope.
- `G1 Contract Skeleton`: Python-profile-only ground dispatch.
- `G2 Content And Test Seed`: fixture root and unit contracts.
- `G3 Execution Surface Design`: selected the safe tasking-only G4 slice.
- `G4 Runtime Slice`: accepted normalized `TaskOrder -> LeaderIntent ->
  PilotReport` lifecycle proof.
- `G5 MVP Scenario`: first canonical `scenarios/ground/` tasking smoke shell.
- `G6 Realism Gradient MVP Scenarios`: first two G1 static occupy/support
  relationship fixtures and focused validation.
- `G6-C Route-Move Boundary`: fail-closed profile hints and architecture
  guardrails; route movement remains held.
- `G6-D Route-Move Release Decision`: schema-first decision plus D1/D2
  preflight packets for native ground platform schema and movement evidence
  gates; D1/D2 returned `preflight-only`, and route movement remains held for a
  later release vote.
- `G6-E Native Ground Platform Schema`: G6-E0 planning package for the minimum
  native ground platform schema; G6-E1 design preflight, G6-E2 implementation,
  and G6-E3 integration/release vote are accepted for native schema evidence.

Content and scenarios:

- [ground_platoon_starter.seed](../../../examples/config/database/ground/units/ground_platoon_starter.seed)
  is a planning/content seed only. It is intentionally not auto-loaded by the
  runtime database loader.
- [ground_platoon_mvp.json](../../../examples/config/database/ground/units/ground_platoon_mvp.json)
  is the first auto-loaded native ground unit definition. It is accepted as a
  static or caller-initial-velocity schema token only, with route movement,
  terrain, sensing, fires, damage, and combat deferred.
- [ground_platoon_tasking_smoke_v1.json](../../../scenarios/ground/ground_platoon_tasking_smoke_v1.json)
  is the first canonical ground scenario shell. It uses an `Aircraft`
  compatibility spawn type and documents that it is not a maintained ground
  platform schema.
- [ground_platoon_static_occupy_v1.json](../../../scenarios/ground/ground_platoon_static_occupy_v1.json)
  is the first G1 static occupy/status fixture.
- [ground_platoon_support_relationship_v1.json](../../../scenarios/ground/ground_platoon_support_relationship_v1.json)
  is the first G1 support relationship fixture.

Contracts and tests:

- [task_order_ground_profile_defaults.json](../../../tests/contracts/unit/ground/task_order_ground_profile_defaults.json)
- [task_order_ground_minimal_structures.json](../../../tests/contracts/unit/ground/task_order_ground_minimal_structures.json)
- [task_order_ground_support_relationships.json](../../../tests/contracts/unit/ground/task_order_ground_support_relationships.json)
- [test_ground_profile_semantics.py](../../../tests/leader/test_ground_profile_semantics.py)
- [test_ground_runtime_lifecycle_bridge.py](../../../tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py)
- [test_ground_mvp_scenario.py](../../../tests/runtime/ground/test_ground_mvp_scenario.py)
- [test_ground_realism_gradient_mvp_scenarios.py](../../../tests/runtime/ground/test_ground_realism_gradient_mvp_scenarios.py)
- [test_ground_realism_gradient_guardrails.py](../../../tests/architecture/test_ground_realism_gradient_guardrails.py)
- [test_ground_native_platform_schema.py](../../../tests/runtime/ground/test_ground_native_platform_schema.py)

Infrastructure gaps:

- no `src/components/tasking/ground/` DTO directory yet;
- no `src/components/command/ground/` command directory yet;
- no formal P2 stage-node manifest for tasking visibility;
- movement-state evidence gates are now defined for future G2, but no native
  route-move scenario is accepted yet.
- G6-E2 now provides the minimum native loader path:
  `UnitType::Ground`, `type = "Ground"`, `Ground_Platoon_MVP`,
  `DefaultUnitFactory::spawn()`, existing `SimulationKernel.get_unit_type()`
  Python evidence, and focused load/spawn/negative tests.

## Domain State

Implemented ground semantics:

- maintained specialization name: `ground`;
- aliases: `army`, `ground`, and `land`;
- service profile: `Army`;
- first tight-loop owner: platoon-centered tactical unit;
- starter tasks:
  - `TASK_MOVE` maps to shared movement/transit intent;
  - `TASK_OCCUPY` maps to shared defend/hold intent;
  - `TASK_SUPPORT` maps to shared support relationship semantics;
- command and support anchors preserve `parent_node_id`,
  `supported_node_id`, `supporting_node_id`, `task_group_id`, and
  `officer_in_tactical_command`.

Declared but not implemented runtime characteristics:

- terrain-masked and line-of-sight-constrained sensing;
- radio-range-constrained shared tactical picture;
- future `ground_visual`, `ground_acoustic`, `ground_mobility`,
  `direct_fire_platform`, `indirect_fire_battery`, and `land_tactics`
  capability families;
- tactical cadence baseline of `1 Hz` for tasking, with movement and sensing
  cadences still deferred.

Boundaries:

- `services/army` explains Army interpretation of shared contracts; it is not a
  runtime stack.
- `ground` owns future execution semantics; current implementation stops at
  tasking-chain status.
- The G5 scenario cannot be used as evidence for ground movement, route
  traversal, terrain masking, cover, sensing, track fusion, fires, effects,
  suppression, damage, or combat.

## RL Integration

Existing RL/tasking integration:

- [ground_profile.py](../../../python/rl/profile/ground_profile.py) owns ground
  task defaults, observation task codes, tactical-unit inference, and the
  minimal compatibility mission-command builder.
- [ground_adapter.py](../../../python/rl/tasking/ground_adapter.py) exposes the
  ground profile through the tasking bridge.
- [bridge.py](../../../python/rl/tasking/bridge.py) resolves `army`, `ground`,
  `land`, and `ServiceProfile.Army` to the ground adapter.
- Unknown explicit loader `tasking_profile` or `service_profile` hints now
  fail closed with `ValueError`; the legacy air default remains only when no
  profile hint exists.
- [common_core_profile.py](../../../python/rl/tasking/common_core_profile.py)
  applies shared `TaskOrder`, `LeaderIntent`, and `PilotReport` defaults while
  preserving Army/ground IDs and support relationships.
- [world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py)
  and
  [cooperative_world_batch_vec_env.py](../../../python/rl/runtime/cooperative_world_batch_vec_env.py)
  import `build_kernel_mission_command` from the shared tasking bridge and push
  command-chain state through maintained task/intent/report batch assignments.
- Scenario-loader runtime state and behavior command-chain paths consume the
  same tasking bridge instead of binding directly to air-only tasking helpers.

Current limitation: ground RL has profile selection, task defaults, observation
codes, and command-chain plumbing. It does not yet have a dedicated learned
ground policy, ground action space, reward model, curriculum, evaluation suite,
or maintained observation/export surface for ground-specific state.

## Validation

Sampling time: `2026-05-25`.

Passed:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/leader/test_ground_profile_semantics.py tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py tests/runtime/ground/test_ground_mvp_scenario.py
# 15 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/ground/task_order_ground_profile_defaults.json tests/contracts/unit/ground/task_order_ground_minimal_structures.json tests/contracts/unit/ground/task_order_ground_support_relationships.json
# PASS x3

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/ground/test_ground_realism_gradient_mvp_scenarios.py
# 2 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/leader/test_ground_profile_semantics.py tests/architecture/test_ground_realism_gradient_guardrails.py
# 14 passed
```

Additional G6-E2/E3 validation sampled on `2026-05-26`:

```bash
cmake --build build-workshop --target ef_py -j2
# [100%] Built target ef_py

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/ground/test_ground_native_platform_schema.py
# 5 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/ground/test_ground_native_platform_schema.py tests/contracts/unit/ground tests/architecture/test_ground_realism_gradient_guardrails.py tests/runtime/ground/test_ground_mvp_scenario.py tests/runtime/ground/test_ground_realism_gradient_mvp_scenarios.py tests/leader/test_ground_profile_semantics.py
# 24 passed
```

## Next Focus

Recommended next steps:

1. Open a later G6-D3/G6-F route-move release vote only if it consumes the
   accepted G6-E2/E3 native schema evidence and names the new movement evidence
   gates.
2. Keep the accepted G6-C/G6-D/G6-E guardrails active: no private ground runtime
   path, no G1 fixture claims of G2+ realism, fail-closed explicit profile
   hints, and no compatibility-shell G2 movement release.
3. Do not add `ground_platoon_flat_route_move_v1` until that later release vote
   accepts a bounded route-move implementation cluster.
4. Keep `build_kernel_mission_command()` as a compatibility shell until a
   ground command vocabulary is accepted.
5. Define a first real ground RL task only after observation, action, reward,
   termination, and eval surfaces are scoped. A credible first task would be a
   static `ground_occupy_status` or `ground_support_relationship` task before
   any maneuver, terrain, or fires policy.
