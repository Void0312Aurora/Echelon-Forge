# Joint Command and Modeling Baseline

Language:
- English canonical: `command_and_modeling_baseline.md`
- Chinese companion: [command_and_modeling_baseline.zh.md](command_and_modeling_baseline.zh.md)

Status: `2026-06-10` authoritative for maintained joint command and modeling
boundaries.

This document defines the joint/common core boundary for command relationship, authority scope, intent/order/report, and the minimum data model that can be shared across air, naval, and the early ground profile.

## 1. What the Joint Layer Means Here

The joint layer is not a full tactical tree for every service. In this codebase, it is the shared contract that answers four questions:

- Who may command whom
- Who may delegate or inherit authority
- What is being ordered, reported, or relayed
- Which parts of a mission belong in common core and which parts belong in a service profile

That means the joint layer should stay small and stable. It should not be written in air-only terms such as `runway`, `wingman`, or `CAP`, and it should not be written in ship-only or ground-only terms either.

## 2. Shared Command Relationship Vocabulary

The following relationships are joint/common core concepts in this project:

- `COCOM`
- `OPCON`
- `TACON`
- `ADCON`
- `support`
- `coordinating authority`
- `DIRLAUTH`

These are not service-specific words. The service profile decides which relationship is active, who holds it, and how it changes during a task.

The current runtime and tests already treat authority-bearing fields as first-class contract data, including:

- `roe_state`
- `engagement_authority_holder_id`
- `engagement_authority_grantor_id`
- `assigned_target_id`
- `authorization_to_fire`

## 3. Authority Scope

Authority scope is the answer to "who can affect what, and up to which boundary".

In the common core, authority scope should be represented as a small set of explicit fields and relationships rather than as service-specific behavior. The runtime contract uses this idea in several places:

- `TaskOrder` and `LeaderIntent` carry the shared command intent
- `MissionCommand` carries the executable command and its authority-bearing state
- `CommandLink` carries delivery timing and ordering
- `DataLink` carries shared track/report exchange

The authority model should remain explicit. Do not hide it inside platform motion parameters.

## 4. Intent, Order, and Report

The minimum common flow is:

`Intent -> Order -> Execution Command -> Report`

The practical split in this repository is:

- `TaskOrder` expresses mission-level tasking
- `LeaderIntent` expresses the leader's current tactical decision
- `MissionCommand` expresses the executable command that the runtime can consume
- `PilotReport` and related report structures express status back to the tasking side

This flow is already reflected in the tasking and mission runtime tests. The common layer should preserve the shape of the flow, but it should not force a single execution style on every service.

## 5. Command Relationship vs Task Organization

The joint layer should carry the organizational skeleton, not the service doctrine detail.

Keep in common core:

- `task_family`
- `service_profile`
- `tactical_unit_type`
- `command_relationship`
- `authority_scope`
- `assignee_kind`
- `coordination_mode`
- `parent_node_id`
- `supported_node_id`
- `supporting_node_id`
- `task_group_id`
- `role_code`
- `relative_slot_code`
- `recovery_site_id`

Leave to service profiles:

- Air-specific `runway`, `takeoff`, `landing`, `CAP`, and formation semantics
- Naval-specific `station`, `screen`, `formation`, `reference entity`, and embarked helicopter semantics
- Later ground-specific maneuver and support semantics

The common layer may describe that a unit is supported or supporting, but it should not hardcode how that support is executed in the air, sea, or land domain.

## 6. What Common Core Must Not Prioritize

When designing shared structures, do not let the common core be shaped by one service's execution language.

Avoid making these the primary abstraction:

- `wingman_slot_id`
- `recovery_runway_id`
- `task_cap`
- `takeoff_clearance`
- `station_radius_m` as the only stationing model

Prefer abstractions that can still be interpreted by every service profile:

- `task_family`
- `service_profile`
- `tactical_unit_type`
- `relative_slot_code`
- `coordination_mode`
- `authority_scope`
- `recovery_site_id`

## 7. Boundary Between Common Core and Service Profile

The boundary is simple:

- Common core defines the nouns and authority relationships that survive across services
- Service profiles define how those nouns are interpreted in a specific mission domain
- Platform/task specialization defines the actual geometry, timing, and control details

This is the reason `docs/standards/joint/*` should describe naming boundaries and prohibitions, while service- and platform-specific documents should define the detailed execution vocabulary.

## 8. Implementation Implication

The current code and tests already point in this direction:

- `MissionCommand` is the runtime command carrier
- `CommandLink` is the delivery and ordering layer
- `DataLink` is the shared track/report layer
- `ROE` and engagement authority are part of the executable command contract, not an afterthought

The baseline for future module splits should therefore be:

1. `joint/common core`
2. `service profile`
3. `platform/task specialization`
