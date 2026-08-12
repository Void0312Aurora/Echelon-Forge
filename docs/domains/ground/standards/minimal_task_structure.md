# Ground Minimal Task Structure

Language: English canonical; [Chinese companion](minimal_task_structure.zh.md).

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/domains/ground/standards/minimal_task_structure.md`
Owner: `domains/ground`
Last verified: `2026-08-08`

## Scope

This standard defines the implemented G0/G1 static Ground task/status contract.
It covers profile routing, three admitted starter task names, their common-core
defaults, Ground-owned static fields, and the projection into
`MissionCommandGround`.

It does not release movement, terrain, sensing, fires, damage, logistics, or a
Ground execution system.

## Profile And Common Defaults

When an explicit tasking profile is `army`, `ground`, or `land`, or when the
service profile is `ServiceProfile.Army` without a conflicting explicit tasking
profile, the maintained tasking route is `ground`.

Every admitted starter task defaults to:

- `service_profile = Army`
- `tactical_unit_type = TacticalUnit`
- `authority_scope = Tactical`
- a platoon-centered first-wave interpretation; higher echelons remain scenario
  or tasking metadata rather than separate tight-loop runtime owners

An explicit tasking profile takes precedence over an inferred service profile.
Unknown explicit profile names MUST fail closed.

## Admitted Starter Tasks

The maintained static contract admits exactly these starter task names:

| Task name | `TaskFamily` | `GroundTaskMode` | Default relationship | Default coordination | Derived status phase |
| --- | --- | --- | --- | --- | --- |
| `TASK_MOVE` | `Transit` | `MoveStatic` | `TACON` | `Independent` | `HoldingStatic` |
| `TASK_OCCUPY` | `Defend` | `OccupyStatic` | `TACON` | `Independent` | `OccupyingStatic` |
| `TASK_SUPPORT` | `Defend` | `SupportStatic` | `Support` | `Support` | `SupportingStatic` |

These mappings describe the current code. In particular, the current common
`TaskFamily` enum has no `Maneuver` or Ground-specific `Support` family:
`TASK_MOVE` maps to `Transit`, while `TASK_OCCUPY` and `TASK_SUPPORT` map to
`Defend`. The support distinction is retained through
`CommandRelationship.Support`, `CoordinationMode.Support`, support IDs, and
`GroundTaskMode.SupportStatic`.

`MoveStatic` is a static task/status code. It MUST NOT be cited as route
traversal or movement-dynamics evidence.

Other candidate names, including `TASK_SCREEN`, `TASK_SECURE`, `TASK_PATROL`,
`TASK_DIRECT_FIRE`, `TASK_INDIRECT_FIRE`, and `TASK_SUSTAIN`, are not admitted
by this standard. They require separate semantics and an accepted standards
update before becoming Ground defaults or required profile outputs.

## Ground-Owned Static Fields

The Ground owner slices carry the following accepted fields:

- `ground_task_mode`
- `ground_status_phase` on status-bearing DTOs
- `objective_area_id`
- `objective_node_id`
- `ground_commander_id`
- `tactical_cadence_hz`
- `readiness_ratio` on `PilotReportGround`

The maintained tasking cadence default is `1 Hz`.

`TaskOrderGround`, `LeaderIntentGround`, and `PilotReportGround` own the static
task/status fields. `MissionCommandGround` is the accepted command-side carrier
for the static task metadata. Flat `TaskOrder`, `LeaderIntent`, `PilotReport`,
and `MissionCommand` structures remain compatibility shells that project those
owner slices.

## Identifier And Relationship Rules

- `parent_node_id` is the command-hierarchy fallback.
- `supported_node_id` and `supporting_node_id` express support relationships.
- `task_group_id` is an optional shared organization hook, not the primary land
  task owner.
- For `TASK_SUPPORT`, the supported node is the preferred objective-area and
  objective-node fallback, while the command hierarchy supplies the Ground
  commander fallback.
- Explicit valid fields MUST win over inferred defaults.

## Scenario Evidence Boundary

The current scenario set proves two bounded surfaces:

- compatibility-shell fixtures validate normalized Ground tasking and static
  status propagation while retaining their declared non-native spawn boundary;
- `ground_platoon_native_static_occupy_v1` validates native
  `Ground_Platoon_MVP` loading plus the Army/Ground `TASK_OCCUPY` static chain.

These fixtures may prove `TaskOrder -> LeaderIntent -> PilotReport` propagation
and `MissionCommandGround` static projection. They MUST NOT be used as evidence
for occupy geometry, route movement, terrain effects, sensing, fires, damage,
or combat behavior.

## Held Boundaries

The following remain outside this task contract:

- route following and movement dynamics;
- terrain traversal, masking, cover, concealment, obstacles, and breach logic;
- Ground sensing, track fusion, shared-picture transport, and observation
  export;
- direct fire, indirect fire, effects, damage, suppression, and attrition;
- logistics, sustainment, and recovery behavior;
- formal Ground `CommandPacket`, `ObservationPacket`, or `TrackPacket`
  specializations.

## Verification

- [Ground profile implementation](../../../../python/rl/profile/ground_profile.py)
- [Tasking profile bridge](../../../../python/rl/tasking/bridge.py)
- [Ground task/status enums](../../../../src/components/domains/ground/tasking/ground_tasking_enums.h)
- [Ground command owner slice](../../../../src/components/domains/ground/command/mission_command_ground.h)
- [Tasking profile contract tests](../../../../tests/leader/test_tasking_profile_contracts.py)
- [Ground tasking component boundary tests](../../../../tests/architecture/ground/test_tasking_component_boundary.py)
- [Ground runtime lifecycle bridge tests](../../../../tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py)

## Related Documents

- [Ground owner overview](../README.md)
- [Ground specialization baseline](specialization_baseline.md)
- [Joint command and modeling baseline](../../joint/standards/command_and_modeling_baseline.md)
