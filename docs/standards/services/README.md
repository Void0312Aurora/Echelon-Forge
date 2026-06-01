# Service Profile Overview

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Status: `2026-06-01` authoritative for service-profile placement.

This directory defines service profiles based on publicly available U.S.
military information. A service profile is not a platform guide and not a full
order of battle. It exists to answer which organizational levels, role codes,
and control relationships should be represented in the project runtime versus
retained as higher-level scenario metadata.

## Included Profiles

- [US Air Force](air_force.md)
- [US Army](army.md)
- [US Navy](navy.md)
- [US Marine Corps](marine_corps.md)

Current specialization directories that build on service profiles:

- [Air Platform Specialization](../air/README.md)
- [Naval Specialization](../naval/README.md)
- [Ground Specialization](../ground/README.md)

## What A Service Profile Owns

A service profile explains:

- which tactical echelons are meaningful runtime units
- which roles belong in mission/tasking metadata rather than control surfaces
- how `joint/common core` fields should be interpreted in that service
- which concepts must remain service-specific before they can be specialized at
  the platform or mission layer

Examples:

- `task_package`, `flight`, and `element` are Air Force profile concepts before
  they become air-platform execution semantics.
- `task group`, `task unit`, `warfare_role_code`, and
  `officer_in_tactical_command` are Navy profile concepts before they become
  ship/station-level naval semantics.

## What A Service Profile Does Not Own

Service profiles do not define:

- engine-neutral coordinate or unit conventions
- low-level runtime DTO memory layouts
- platform-specific sensor pages, runway procedures, or ship station geometry
- active task planning details under `docs/task/`

Those belong in:

- [conventions.md](../foundation/conventions.md)
- [Runtime Workflow and Contract Baseline](../bridge/runtime_workflow_and_contract_baseline.md)
- [air/](../air/README.md)
- [naval/](../naval/README.md)
- [ground/](../ground/README.md)

## Unified Conclusion

All four services reject the idea of directly shoving an administrative
organization tree into the tight-loop RL/runtime layer.

The maintained repository baseline is:

- keep joint/service upper layers as tasking, authority, and force-packaging
  metadata
- place tight-loop runtime on real tactical units
- let each service profile define what counts as the tactical unit boundary

## Relationship to Current Runtime Work

The current code base already contains a mixed bridge:

- air-first mission semantics in `mission_command`, route, takeoff, runway, and
  formation contracts
- emerging naval semantics in `task_group_id`, ship mission commands, and
  command-authority tests
- early ground tasking/schema semantics in `tasking_profile: ground`, Army
  aliases, `UnitType::Ground`, and static/support relationship fixtures
- joint/common seams in `MissionCommand`, `CommandLink`, `DataLink`, and report
  flow

Service profiles are the layer that should normalize those seams before a term
is promoted into common core or sunk into specialization.

## Related Documents

- [Joint Standards Overview](../joint/README.md)
- [Document Alignment Map](../overview/document_alignment_map.md)
- [Scenario Configuration Guide](../bridge/scenario_guide.md)
- [Runtime Workflow and Contract Baseline](../bridge/runtime_workflow_and_contract_baseline.md)
