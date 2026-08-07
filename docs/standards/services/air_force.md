# US Air Force Profile

Language:
- English canonical: `air_force.md`
- Chinese companion: [air_force.zh.md](air_force.zh.md)

Status: `2026-05-18` authoritative for USAF service-profile placement.

This document defines how the repository interprets U.S. Air Force organizational
concepts before they are mapped into common-core tasking or the maintained
`air/` specialization.

It is not a full doctrine digest. Its job is to answer:

- which USAF layers belong in scenario and mission-packaging metadata
- which tactical layers are meaningful runtime units
- which terms stay at service-profile level and which must be expressed through
  the maintained air command, observation, action, and reporting contracts

## Real-World Basis

Current public USAF doctrine still treats command and control as a mission-command
problem built around authority delegation rather than around a single monolithic
operations center interface.

Official references:

- [AFDP 3-0.1, Command and Control](https://www.doctrine.af.mil/Operational-Level-Doctrine/AFDP-3-01-Command-and-Control/)
- [AFDP 3-0.1 PDF](https://www.doctrine.af.mil/Portals/61/documents/AFDP_3-0_1/AFDP3-0.1CommandandControl.pdf)

The current official AFDP 3-0.1 page shows `Last Published: 22 Jan 2025`. The
publication and synopsis emphasize:

- command and control as a commander-centered function
- explicit delegation of authority
- `Centralized Command - Distributed Control - Decentralized Execution`
- organizations such as AFFOR staff, AOC staff, wings, and TACS as parts of
  the broader C2 system rather than as the only runtime surface

These sources are enough for this repository's standards work: they justify
keeping high-level air-component structures above the tight-loop runtime while
preserving tactical sortie organization below them.

## Layer Boundaries

### `joint/common core`

The common layer should keep only the cross-service skeleton:

- `service_profile`
- `task_family`
- `tactical_unit_type`
- `authority_scope`
- `command_relationship`
- `coordination_mode`
- `task_group_id`
- `role_code`
- `relative_slot_code`
- `recovery_site_id`

These fields stay neutral. They do not become USAF-specific just because the
current repository is air-heavy.

### `services/air_force`

The Air Force service profile owns the USAF reading of that shared skeleton:

- `mission package` or similar task packaging above individual aircraft
- `flight` and `element` as tactical grouping concepts
- role distinctions between package lead, element lead, wingman, and platform
- the point where an organizational layer stops being metadata and starts being
  a runtime tactical unit

This layer defines interpretation and ownership. It does not define runway
geometry, action vectors, or mission-observation array layouts.

### `air`

The dedicated `air/` specialization owns the maintained air execution contract:

- `TaskOrderAir`, `LeaderIntentAir`, and `PilotReportAir`
- `MissionCommand` air extensions and maintained `command_code` behavior
- `route_ref_id`
- `takeoff_*`, `formation_*`, and `recovery_*` fields
- mission-observation modes
- `PilotAction` mapping and report taxonomy

If a term only becomes meaningful once it touches runway, formation, recovery,
or pilot-control surfaces, it belongs in `air/`, not here.

## Runtime Boundary

### Layers that should remain scenario or campaign metadata

The following concepts are real and important, but should stay above the
tight-loop runtime in the current repository:

- COMAFFOR / JFACC-level authority framing
- AOC planning and air-tasking-cycle orchestration
- MAJCOM, NAF, wing, and similar administrative or theater-management layers
- theater-level force presentation and allocation decisions

These layers belong in:

- scenario authoring
- force packaging
- mission authorization
- higher-level operation metadata

### Layers that can meaningfully enter the tactical runtime

The current repository should keep the executable air boundary on real tactical
units, interpreted through the USAF profile:

- mission package
- flight
- element
- aircraft / platform

In code terms, that usually means the common core can carry generalized runtime
anchors such as `MissionPackage`, `TacticalUnit`, and `Platform`, while the
Air Force profile explains how those anchors correspond to sortie-level units.

## Direct Constraints On Standards Design

The Air Force profile imposes several guardrails on the rest of the standards
tree.

### Keep common core free of air-only task language

Do not make these common-core nouns:

- `CAP`
- `BARCAP`
- `TARCAP`
- `runway slot`
- `takeoff clearance`
- `element lead`

Those are Air Force profile or `air/` specialization concepts.

### Use shared fields for the skeleton, not for the full air vocabulary

The shared fields should carry the portable part of the organization:

- who the unit belongs to
- what tactical unit it is
- what support or coordination relation it holds
- which recovery site or task group anchors it references

The air-specific meaning of those fields is layered on top by the USAF profile
and `air/` documents.

### Route, formation, takeoff, and recovery remain below this layer

Even when current runtime objects expose fields such as `route_ref_id`,
`takeoff_procedure_id`, `takeoff_clearance_id`, `formation_id`, or recovery
identifiers, those fields are not service-profile ownership. They are maintained
air-specialization contracts.

## Relationship To Current Repository Contracts

The maintained repository already reflects an air-first tactical bridge:

- common tasking fields flow through `TaskOrder`, `LeaderIntent`, and
  `PilotReport`
- executable commands flow through `MissionCommand`
- sortie-level observation and action contracts are defined in `air/obs.md` and
  `air/act.md`

This document therefore acts as a guardrail:

- keep upper USAF organization as metadata
- keep tactical grouping semantics at service-profile level
- let the maintained `air/` documents own execution details

## Related Documents

- [Service Profile Overview](README.md)
- [Air Platform Specialization](../air/README.md)
- [Joint Command and Modeling Baseline](../../domains/joint/standards/command_and_modeling_baseline.md)
- [Joint Command-Link and Reporting Baseline](../../domains/joint/standards/command_link_and_reporting_baseline.md)
- [Runtime Workflow and Contract Baseline](../bridge/runtime_workflow_and_contract_baseline.md)
