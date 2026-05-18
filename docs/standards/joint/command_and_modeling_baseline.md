<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/joint/command_and_modeling_baseline.zh.md. Review before treating this file as authoritative. -->

<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/joint/command_and_modeling_baseline.md. Review before treating this file as authoritative. -->

# Joint Command Relationship and Modeling Baseline

This document defines the minimal joint-layer template shared by all services in the project.

## 1. Official Reality Basis

According to official Joint Chiefs material, the common basis of the US joint layer lies not in "all services using the same tactical command tree", but rather in:

- Common command relationships
- Common authority delegation
- Common reporting / status framework

The project must first isolate this layer when modeling.

Primary official references:

- [Joint Chiefs Service Publications](https://www.jcs.mil/Doctrine/Service-Publications/)
- [CJCSM 3150.13C, Joint Reporting Structure](https://www.jcs.mil/Portals/36/Documents/Library/Manuals/m315013.pdf)

## 2. Objects That Must Be Unified at the Joint Layer

### 2.1 Command Relationship

The project should treat the following relationships as joint-layer common fields, not service-specific fields:

- `COCOM`
- `OPCON`
- `TACON`
- `support`
- `ADCON`
- `coordinating authority`
- `DIRLAUTH`

Note:

- This is a unified authorization language.
- Differences between Air Force, Army, and Navy lie primarily in "who holds which relationships under what circumstances", not in the vocabulary itself.

### 2.2 Task Organization

The joint layer defines only:

- `command_node`
- `tactical_unit`
- `platform_unit`

And:

- `parent_node_id`
- `supported_node_id`
- `supporting_node_id`
- `authority_scope_code`
- `task_group_id`

It does **not** directly define:

- `element`
- `brigade`
- `task force`

These should be left to service profiles for interpretation.

### 2.3 Intent / Order / Report

The recommended common data flow across all domains is:

`Commander Intent / Task Order -> Tactical Intent -> Execution Command -> Status / Report`

The joint layer defines only the common interfaces, not domain-specific execution parameters.

## 3. Separation of Concerns Principle

### 3.1 What the Joint Layer Is Responsible For

- Relationships and authorities
- Who tasks whom
- Who reports to whom
- Which level is the tight-loop tactical unit

### 3.2 What the Joint Layer Is Not Responsible For

- Runway approach
- Carrier formation station geometry
- Ground combat fire support wedge deployment
- Specific platform execution actions

These all belong to the service profile or platform/task layer.

## 4. Data Model Constraints for the Project

If the project is to support air, naval, and ground in the future, the core structures should **not** prioritize writing:

- `wingman_slot_id`
- `recovery_runway_id`
- `task_cap`

Instead, they should prioritize:

- `task_family`
- `service_profile`
- `tactical_unit_type`
- `role_code`
- `relative_slot_code`
- `coordination_mode`
- `recovery_site_id`

Note:

- `runway` is a `recovery_site` in the air profile
- `CAP` is a type of `patrol` family under the air profile
- `wingman` is a type of `subordinate role` under the air profile

## 5. Direct Constraints for Upcoming Module Splitting

If the subsequent `tasking / command` module is further split, the documentation should directly fall into the following three categories:

### 5.1 `common`

Contains fields, enums, and DTO skeletons that remain valid across all services:

- `service_profile`
- `task_family`
- `tactical_unit_type`
- `command_relationship`
- `authority_scope`
- `assignee_kind`
- `coordination_mode`
- `parent_node_id / supported_node_id / supporting_node_id`
- `task_group_id`
- `role_code`
- `relative_slot_code`
- `recovery_site_id`

These objects at the `common` layer only express "who commands whom, who coordinates with whom, and which site recovers to", not domain-specific details such as runways, CAP routes, or naval warfare stations.

### 5.2 `air`

Contains domain-specific semantics that the current air combat runtime must retain:

- `CAP`
- `route_cap`
- phases in `LeaderPhase` such as takeoff / departure / on-station / landing
- `recovery_runway_id`
- `recovery_approach_type`
- `takeoff_procedure`
- `takeoff_clearance`
- `runway_slot`
- `wingman / element`
- air-specific interpretation of `MissionCommand.command_code`

### 5.3 `naval`

Contains domain-specific semantics for future naval tight-loop runtime:

- Naval profile interpretation of `task force / task group / task unit`
- `warfare_role_code`
- `officer_in_tactical_command`
- fleet-level semantics of `screen / support / station / formation`
- Ship/formation recovery, replenishment, routing, and fleet station semantics

`naval` should **not** reuse air vocabulary such as `lead / wingman / runway / approach` as core templates.

## 6. Direct Conclusions for Project Architecture

Future project standardization documentation and code design should be organized in three layers:

1. `joint/common core`
2. `service profile`
3. `platform/task specialization`

This is more aligned with real-world practices and better for engineering separation of concerns than "writing air first, then hoping sea/land can also reuse".

In upcoming module work, the following documentation-to-module mapping can be directly adopted:

1. `docs/standards/joint/*` defines the naming boundaries and prohibitions for `common`.
2. `docs/standards/services/*.md` defines how each service profile interprets `common` fields.
3. `docs/standards/air/*` and future `docs/standards/naval/*` define platform/task-specific extensions, and should not drive `common` naming in reverse.
