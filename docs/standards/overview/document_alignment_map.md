# Document Alignment Map

Language:
- English canonical: `overview/document_alignment_map.md`
- Chinese companion: [document_alignment_map.zh.md](document_alignment_map.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/standards/overview/document_alignment_map.md`
Owner: `engineering/documentation-governance`
Last verified: `2026-08-08`

Status: `2026-08-08` migration-time authority map for document ownership and
layering.

This document clarifies which standards documents are primary, which are
specialized supplements, and how active task/workflow documents map back to
distributed owner standards and the remaining legacy standards tree.

## Active Primary References

### Joint / Common Core

The current joint-layer primary references are:

- [Joint Standards Overview](../../domains/joint/README.md)
- [Joint Command and Modeling Baseline](../../domains/joint/standards/command_and_modeling_baseline.md)
- [Joint Command-Link and Reporting Baseline](../../domains/joint/standards/command_link_and_reporting_baseline.md)
- [Simulation Conventions](../foundation/conventions.md)
- [Gradient Realism Principles](../foundation/gradient_realism_principles.md)
- [Runtime Workflow and Contract Baseline](../bridge/runtime_workflow_and_contract_baseline.md)

They define:

- command relationships and authority boundaries
- shared tasking, command, and reporting workflow seams
- runtime stage ownership between scenario-loader orchestration and pure C++
  mission/runtime kernels
- engine-neutral coordinate, angle, time, and observation conventions
- gradient realism gates that keep scenario claims aligned with implemented
  domain mechanisms

### Service Profiles

Current service-profile primary references:

- [Service Profile Overview](../../domains/joint/service_profiles/README.md)
- [USAF Profile](../../domains/joint/service_profiles/standards/air_force_profile.md)
- [US Army Profile](../../domains/joint/service_profiles/standards/army_profile.md)
- [US Navy Profile](../../domains/joint/service_profiles/standards/navy_profile.md)
- [US Marine Corps Profile](../../domains/joint/service_profiles/standards/marine_corps_profile.md)

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

### Model Architecture

The current maintained model-architecture references are:

- [Model Architecture Standards Overview](../model/README.md)
- [Policy Execution Architecture Baseline](../model/policy_execution_architecture.md)

They define:

- model/policy component ownership across executable policy branches, auxiliary
  heads, runtime action adapters, losses, rewards, rollout labels, and probes
- the difference between runtime support constraints and learned stopping or
  timing mechanisms
- how active `docs/task/model/` work maps back to stable architecture
  vocabulary without turning task status into a standard

## Valid Specialized Supplements

### Air Specialization

These remain valid, but they are not project-wide common-core standards:

- [Air Standards Overview](../../domains/air/README.md)
- [Pilot Observation Space Standard](../../domains/air/standards/pilot_observation_contract.md)
- [Pilot Action Space Standard](../../domains/air/standards/pilot_action_contract.md)
- [Air Mission Command Standard](../../domains/air/standards/mission_command_and_tasking_contract.md)
- [Pilot Report Standard](../../domains/air/standards/pilot_reporting_contract.md)
- [Air-To-Air Kill-Chain Expectation Envelope](../../domains/air/work/issues/kill_chain_expectation_envelope.md)
  - active planning supplement, not a current runtime contract

They own:

- runway, approach, ILS, takeoff, recovery, sortie-phase semantics
- air mission observation and execution-command specialization
- air formation roles such as `wingman`, `element`, and `flight`
- air-to-air kill-chain expectation-envelope labels used to review diagnostic
  distributions before calibration work

### Naval Specialization

The maintained naval specialization entrypoints are:

- [Naval Standards Overview](../naval/README.md)
- [Naval Minimal Task Structure](../naval/minimal_task_structure.md)
- [Ship Unit References](../naval/ship_unit_references.md)
- [Naval Observation Contract](../naval/obs.md)

They own:

- maritime task/station/screen/support/recovery semantics
- ship- and task-group-level naval role interpretation
- first-batch naval data/reference boundaries, with
  [Ship Unit References](../naval/ship_unit_references.md) acting as the current
  reference-baseline supplement
- `naval_screen_station_v1` mission-observation ownership and field order

They do not own cross-service authority or generic tasking DTO boundaries.

### Ground Specialization

The maintained ground specialization entrypoints are:

- [Ground Standards Overview](../../domains/ground/README.md)
- [Ground Specialization Baseline](../../domains/ground/standards/specialization_baseline.md)
- [Ground Minimal Task Structure](../../domains/ground/standards/minimal_task_structure.md)

They own:

- platoon-centered starter tasking defaults
- `TASK_MOVE`, `TASK_OCCUPY`, and `TASK_SUPPORT` ground semantics
- ground agency role defaults
- terrain-masked sensing and radio-range-constrained shared-picture assumptions
- capability-composition expectations for first-wave ground platforms

They do not own cross-service authority definitions, Army service-profile
interpretation, or full terrain/mobility/fires/runtime behavior.

Routing rule: `docs/domains/joint/service_profiles/standards/army_profile.md`
owns Army profile interpretation; `docs/domains/ground/` owns maintained ground
specialization. The accepted aliases `army` and `land` normalize to `ground`
and must not be documented as a separate `army` runtime stack.

## Active Planning Supplements

The following document is maintained as an active planning supplement, not as a
current runtime contract:

- [Modularization Plan](../planning/modularization_plan.md)

It exists to describe target codebase structure and future split direction after
the standards-tree rebuild. It now also records the current
`src/components/domains`, `src/systems/domains`, and `src/models/domains` roots
so readers can distinguish realized owner roots from still-planned interfaces.
It should not be cited as proof that every planned module boundary or every
domain runtime owner is already implemented.

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

## Mapping Historical Flight-Dynamics Work Back To Standards

The `docs/task/flight_dynamics/` tree is now a historical/reference realism
analysis entry, not the active project-planning root. Its subprojects should be
read as execution-analysis records that map back to standards ownership, not as
the standards ownership map itself.

Map those workstreams back as follows:

- `c2_command_chain/`
  - primarily aligns to `docs/domains/joint/`
  - secondarily to the Navy service profile and the legacy `naval/` subtree
    where ship authority/report semantics appear
- `naval/`
  - aligns to the Navy service profile and the legacy `naval/` subtree
- `ground/` or future land-domain task work
  - aligns to the Army service profile for service-profile interpretation and
    `docs/domains/ground/` for specialization
  - must not introduce a separate `army` runtime stack
- `sensor_situation/`
  - currently aligns to the workflow bridge and future shared standards that
    govern `track`, `IFF`, and `report` contracts
- `weapon_guidance/`
  - currently aligns to the workflow bridge and future weapon specialization
- `flight/`
  - aligns to air specialization plus runtime workflow constraints

This means archived or reference task folders may contain valid analysis, but
they should not decide where stable shared contracts live.

## Recommended Maintenance Rule

When adding a new maintained standards document:

1. Put cross-service relationships in `docs/domains/joint/standards/`.
2. Put service organization/control interpretation in
   `docs/domains/joint/service_profiles/standards/`.
3. Put Air or Ground specialization in the matching owner-local `standards/`
   surface. Route Naval changes through its current legacy owner until its
   separate migration lands.
4. Put new cross-domain runtime/workflow contracts under `docs/architecture/`;
   do not expand the legacy `bridge/` subtree.
5. Put new model/policy architecture vocabulary under `docs/learning/` while
   the current legacy model standard awaits migration.
6. Retire superseded work through the document lifecycle policy; do not rewrite
   existing archives as part of a standards migration.
