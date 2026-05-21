# Document Alignment Map

Language:
- English canonical: `overview/document_alignment_map.md`
- Chinese companion: [document_alignment_map.zh.md](document_alignment_map.zh.md)

Status: `2026-05-21` authoritative for document ownership and layering.

This document clarifies which standards documents are primary, which are
specialized supplements, and how active task/workflow documents map back to the
maintained standards tree.

## Active Primary References

### Joint / Common Core

The current joint-layer primary references are:

- [Joint Standards Overview](../joint/README.md)
- [Joint Command and Modeling Baseline](../joint/command_and_modeling_baseline.md)
- [Joint Command-Link and Reporting Baseline](../joint/command_link_and_reporting_baseline.md)
- [Simulation Conventions](../foundation/conventions.md)
- [Runtime Workflow and Contract Baseline](../bridge/runtime_workflow_and_contract_baseline.md)

They define:

- command relationships and authority boundaries
- shared tasking, command, and reporting workflow seams
- runtime stage ownership between scenario-loader orchestration and pure C++
  mission/runtime kernels
- engine-neutral coordinate, angle, time, and observation conventions

### Service Profiles

Current service-profile primary references:

- [Service Profile Overview](../services/README.md)
- [USAF Profile](../services/air_force.md)
- [US Army Profile](../services/army.md)
- [US Navy Profile](../services/navy.md)
- [US Marine Corps Profile](../services/marine_corps.md)

They define:

- which echelons are valid tight-loop runtime units
- which concepts remain service-specific before specialization
- how the common core should be interpreted per service

### Bridge Documents

The current maintained bridge documents are:

- [Scenario Configuration Guide](../bridge/scenario_guide.md)
- [Runtime Workflow and Contract Baseline](../bridge/runtime_workflow_and_contract_baseline.md)

They do not redefine doctrine. They explain how current repository inputs,
workflow stages, and DTOs line up with the maintained standards tree.

## Valid Specialized Supplements

### Air Specialization

These remain valid, but they are not project-wide common-core standards:

- [Air Standards Overview](../air/README.md)
- [Pilot Observation Space Standard](../air/obs.md)
- [Pilot Action Space Standard](../air/act.md)
- [Air Mission Command Standard](../air/aim.md)
- [Pilot Report Standard](../air/rep.md)

They own:

- runway, approach, ILS, takeoff, recovery, sortie-phase semantics
- air mission observation and execution-command specialization
- air formation roles such as `wingman`, `element`, and `flight`

### Naval Specialization

The maintained naval specialization entrypoints are:

- [Naval Standards Overview](../naval/README.md)
- [Naval Minimal Task Structure](../naval/minimal_task_structure.md)
- [Ship Unit References](../naval/ship_unit_references.md)

They own:

- maritime task/station/screen/support/recovery semantics
- ship- and task-group-level naval role interpretation
- first-batch naval data/reference boundaries, with
  [Ship Unit References](../naval/ship_unit_references.md) acting as the current
  reference-baseline supplement

They do not own cross-service authority or generic tasking DTO boundaries.

### Ground Specialization

The maintained ground specialization entrypoints are:

- [Ground Standards Overview](../ground/README.md)
- [Ground Minimal Task Structure](../ground/minimal_task_structure.md)

They own:

- platoon-centered starter tasking defaults
- `TASK_MOVE`, `TASK_OCCUPY`, and `TASK_SUPPORT` ground semantics
- ground agency role defaults
- terrain-masked sensing and radio-range-constrained shared-picture assumptions
- capability-composition expectations for first-wave ground platforms

They do not own cross-service authority definitions, Army service-profile
interpretation, or full terrain/mobility/fires/runtime behavior.

Routing rule: `services/army.md` owns Army profile interpretation; `ground/`
owns maintained ground specialization. The accepted aliases `army` and `land`
normalize to `ground` and must not be documented as a separate `army` runtime
stack.

## Active Planning Supplements

The following document is maintained as an active planning supplement, not as a
current runtime contract:

- [Modularization Plan](../planning/modularization_plan.md)

It exists to describe target codebase structure and future split direction after
the standards-tree rebuild. It should not be cited as proof that a planned
module boundary is already implemented.

## Archived Documents

The following are retained for historical reference only:

- `docs/Archive/air_first_standards/com/*.md`
- `docs/Archive/air_first_standards/com/two_ship/*.md`
- `docs/Archive/architecture/*.md`
- `docs/Archive/architecture/layers/*.md`
- `docs/task/flight_dynamics/archive/**`

These are archived because they describe superseded execution paths, older
air-first generalization attempts, or task-history snapshots that no longer act
as current standards.

## Ownership Rules For Common Concepts

The following concepts should be lifted to common core whenever possible:

- `command_relationship`
- `authority_scope`
- `service_profile`
- `task_family`
- `tactical_unit_type`
- `coordination_mode`
- `role_code`
- `task_group_id`
- `supported_node_id`
- `supporting_node_id`
- `recovery_site_id`

Ownership rule:

- `joint/` defines names, minimal semantics, and forbidden conflations.
- service profiles explain service-specific interpretation.
- bridge documents explain how the current runtime expresses them.
- specialization docs must not redefine them as air-only or naval-only core.

## Ownership Rules For Air-Specific Concepts

The following concepts should remain in air specialization unless and until a
different cross-service abstraction exists:

- `CAP`
- `route CAP`
- `runway`
- `approach_type`
- `takeoff_procedure`
- `takeoff_clearance`
- `LeaderPhase`
- `wingman`
- `element`
- `flight`

These may continue to exist in code, tests, and scenarios, but they must not be
described as project-wide common-core defaults.

## Ownership Rules For Naval-Specific Concepts

The following concepts belong to the Navy profile or naval specialization, not
the common core:

- `warfare_role_code`
- `officer_in_tactical_command`
- `task force / task group / task unit` as naval organization semantics
- `screen`
- `support`
- `station`
- `replenishment`
- ship/section recovery semantics

`joint/common core` may carry hooks such as `task_group_id` or
`coordination_mode`, but the Navy profile and naval specialization own the
meaning of those hooks in maritime scenarios.

## Ownership Rules For Ground-Specific Concepts

The following concepts belong to the Army profile or ground specialization, not
the common core:

- `platoon` as the first tight-loop ground tasking boundary
- `move`, `occupy`, and land `support` task semantics
- `ground_squad_leader`
- `ground_platoon_commander`
- `ground_company_commander`
- terrain-masked sensing
- radio-range-constrained shared tactical picture
- ground mobility, direct-fire, indirect-fire, sustainment, and land reporting
  extensions

`joint/common core` may carry hooks such as `tactical_unit_type`,
`parent_node_id`, `supported_node_id`, `supporting_node_id`, and
`coordination_mode`, but the Army profile and ground specialization own the
land-specific meaning of those hooks.

## Mapping Active Flight-Dynamics Work Back To Standards

The active task tree under `docs/task/flight_dynamics/` should be read as an
execution view, not as the standards ownership map.

Map those workstreams back as follows:

- `c2_command_chain/`
  - primarily aligns to `joint/`
  - secondarily to `services/navy.md` and `naval/` where ship authority/report
    semantics appear
- `naval/`
  - aligns to `services/navy.md` and `naval/`
- `ground/` or future land-domain task work
  - aligns to `services/army.md` for service-profile interpretation and
    `ground/` for specialization
  - must not introduce a separate `army` runtime stack
- `sensor_situation/`
  - currently aligns to the workflow bridge and future shared standards that
    govern `track`, `IFF`, and `report` contracts
- `weapon_guidance/`
  - currently aligns to the workflow bridge and future weapon specialization
- `flight/`
  - aligns to air specialization plus runtime workflow constraints

This means task folders may contain valid analysis, but they should not decide
where stable shared contracts live.

## Recommended Maintenance Rule

When adding a new maintained standards document:

1. Put cross-service relationships in `joint/`.
2. Put service organization/control interpretation in `services/`.
3. Put platform or mission specialization in `air/`, `naval/`, or `ground/`.
4. Put scenario/runtime bridge documentation in `bridge/`.
5. Put superseded work in `docs/Archive/` or the relevant task archive tree.
