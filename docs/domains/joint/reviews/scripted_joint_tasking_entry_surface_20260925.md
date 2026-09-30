# Scripted Joint Tasking Entry Surface Review — 2026-09-25

- Document kind: review
- Lifecycle: maintained
- Owner: joint/scripted-agent
- Scope: cross-domain tasking entry surface for the independent scripted-agent line
- Verdict: `projection_ready_runtime_missing`

## Verified current surfaces

| Surface | Current evidence | Consequence |
| --- | --- | --- |
| Joint boundary | `docs/domains/joint/standards/command_and_modeling_baseline.md` keeps authority, task organization, intent/order/report vocabulary in the common core and leaves execution geometry to Air, Naval, and Ground owners. | A joint scripted role may coordinate domain nodes, but it must not own runway, station, maneuver, sensor, or weapon semantics. |
| Closed-loop vocabulary | `docs/domains/joint/standards/command_link_and_reporting_baseline.md` defines `TaskOrder -> LeaderIntent -> MissionCommand -> CommandLink -> Execution -> Report -> DataLink`. | The existing loop is the right envelope for a joint adapter; it is not evidence that a cross-domain scheduler or playable scenario already exists. |
| Compiled role and intent contracts | `src/runtime/contracts/policy_contracts.h` and `src/interfaces/python/bindings_runtime_policy.cpp` expose `AgentRole`, `ActionIntentPacket`, `CoordinationIntentPacket`, and `DecisionBelief`, including authority and action-interface compatibility checks. | A joint producer can use the compiled coordination packet and common authority checks instead of inventing a Python-only authority model. |
| Domain field transport | The Air/Navy/Army tasking and command projection tests exercise `service_profile`, `task_group_id`, `supported_node_id`, `supporting_node_id`, `coordination_mode`, role, and relative-slot fields through common DTOs. | Common metadata can cross the contract boundary, while service-owned payloads remain separate. |
| Cooperative routing | `python/rl/runtime/world_batch/cooperative_director.py` and the cooperative world-batch runtime route active roster members, role metadata, formation data, command objects, intents, and reports. | This is reusable substrate for joint roster routing, but it remains an RL-adjacent runtime adapter and does not instantiate a complete independent joint scripted loop. |
| Scenario and operator entry | A dependency-terminal `joint.coordination.task_graph_scripted` adapter and versioned task-graph contract now exist, but repository search still finds no maintained scenario with Air plus Naval/Ground active nodes and no joint scripted CLI or visualization route. | Joint tasking has a bounded producer/projection slice; no playable or large-scale cross-domain claim is admitted. |

## Focused verification

With the local compiled binding selected through `CMO_BUILD_DIR=build-scripted-agent`,
the maintained contract set passed:

```text
tests/leader/test_tasking_profile_contracts.py
tests/leader/test_command_field_projection_contracts.py
tests/world_batch/test_world_batch_runtime_surface.py
48 passed
```

These tests prove contract and projection behavior. They do not prove a
cross-domain episode, service-owned execution, command-link loss handling, or
operator-level replay.

The joint producer and roster contract tests add `20 passed` under
`tests/runtime/tasking/`. A direct compiled projection probe using the local
`ef_py` build produced `CoordinationIntentPacket` with source `joint:director`,
graph roster `joint.air_naval_screen_demo_v1`, Air/Naval task references, and
`authorize_maintained_coordination_intent(...).authorized == true`. The current
DTO has no fields for task group, coordination mode, clock, observation
version, communication state, or authority scope; the projection returns these
as explicit residuals rather than hiding them in unrelated fields.

## Joint closure slices

1. **Task graph declaration:** the dependency-terminal graph contract now
   names cross-domain nodes, `service_profile`, `task_group_id`, authority
   edges, support relationships, coordination mode, and the domain-owned
   payload reference for each node. A maintained scenario manifest consumer is
   still open.
2. **Independent coordination producer:** a bounded scripted role now emits
   graph-scoped common intent data and an optional compiled DTO projection,
   with runtime clock/hold/provenance supplied by the neutral scheduler. Full
   command-link ownership and DTO field closure remain open.
3. **Roster routing:** route at least one Air node and one admitted Naval or
   Ground node through the existing active-roster path. Preserve each domain's
   action/observation owner and record communication state and delivery order.
4. **Execution/report closure:** prove `TaskOrder -> LeaderIntent ->
   MissionCommand -> CommandLink -> Execution -> Report -> DataLink` for the
   joint scenario, including delayed or unavailable delivery and a terminal
   report owned by the correct domain runtime.
5. **Replay and negative controls:** repeat the scenario under reset/replay,
   verify deterministic task graph and report identity, and show that a joint
   producer cannot read privileged domain geometry or write domain components
   directly.
6. **Operator and scale gates:** add a standalone scripted CLI and a bounded
   batch demonstration only after the smallest Air plus one other-domain loop
   closes. A cross-domain task graph alone cannot promote Naval or Ground.

## Explicit non-goals

- No generic cross-domain `JointAction`, `JointObservation`, or
  `ElectronicWarfare` mega-schema.
- No direct Python writes to Air, Naval, or Ground components.
- No promotion based only on DTO serialization, role registration, or a
  cooperative trace that ends before task completion.
- No RL checkpoint or training configuration as the required source of the
  independent scripted loop.
