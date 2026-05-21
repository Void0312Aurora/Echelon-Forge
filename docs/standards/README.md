# Standards Documentation Overview

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Status: `2026-05-21` authoritative for the maintained standards tree.

This directory defines the standardized modeling baseline the project intends to
use going forward. Its job is not to restate every active implementation task.
Its job is to tell contributors which concepts belong to the joint/common core,
which belong to service profiles, which belong to platform or mission
specializations, and how the current code/runtime should align with that split.

## Purpose

The maintained standards tree exists to keep three things from drifting apart:

- real-world public doctrine and reference material
- the repository's current runtime and test contracts
- active task planning under `docs/task/`

The standards tree is therefore the ownership map. Task plans may describe
current implementation waves, but they should not redefine which layer owns
`authority_scope`, `task_group_id`, `runway_slot_code`, or `warfare_role_code`.

## Tree Structure

Since `2026-03-23`, the standards documentation is no longer organized around
an "air first, generalize later" line. It now follows:

1. `joint/`
2. `services/`
3. `air/`
4. `naval/`
5. `ground/`

This reflects a deliberate modeling split:

- `joint/` defines common relationships, authority, tasking, reporting, and
  workflow seams that remain valid across services.
- `services/` explains how those common objects map onto the Air Force, Army,
  Navy, and Marine Corps.
- `air/` defines air-platform specialization such as sortie phases, runway
  recovery, takeoff procedures, and air-specific mission observation semantics.
- `naval/` defines naval specialization such as task-group semantics, station,
  screen, support, recovery, and maritime command-role extensions.
- `ground/` defines ground specialization such as platoon-centered tasking,
  move/occupy/support semantics, terrain-masked information assumptions, and
  land command/support extensions.

Third-domain navigation must route through both layers: `services/army.md`
owns Army service-profile interpretation, while `ground/` owns maintained
ground specialization semantics. The aliases `army` and `land` normalize to
the maintained `ground` specialization and do not create a separate `army`
runtime stack.

## Recommended Reading Order

For new work, read in this order:

1. [Joint Standards Overview](joint/README.md)
2. [Joint Command and Modeling Baseline](joint/command_and_modeling_baseline.md)
3. [Joint Command-Link and Reporting Baseline](joint/command_link_and_reporting_baseline.md)
4. [Runtime Workflow and Contract Baseline](bridge/runtime_workflow_and_contract_baseline.md)
5. [Service Profile Overview](services/README.md)
6. [USAF Profile](services/air_force.md)
7. [US Army Profile](services/army.md)
8. [US Navy Profile](services/navy.md)
9. [Document Alignment Map](overview/document_alignment_map.md)
10. [Scenario Configuration Guide](bridge/scenario_guide.md)
11. [Air Platform Specialization Overview](air/README.md)
12. [Naval Standards Overview](naval/README.md)
13. [Ground Standards Overview](ground/README.md)

## Relationship to Active Task Plans

The current task tree under `docs/task/` includes implementation workstreams
such as `flight_dynamics/flight`, `flight_dynamics/sensor_situation`,
`flight_dynamics/weapon_guidance`, `flight_dynamics/naval`, and
`flight_dynamics/c2_command_chain`, plus the newer `ground/` third-domain
bootstrap.

That task-tree layout is useful for execution, but it is not the ownership map
for the standardized model. In particular:

- `flight`, `sensor`, and `weapon` are mostly implementation realism domains.
- `c2_command_chain` contains many concepts that belong in `joint/`.
- `naval` contains concepts split across `services/navy.md` and `naval/`.
- `ground` contains concepts split across `services/army.md` and `ground/`;
  the `army` and `land` aliases route through that split rather than through a
  new runtime stack.
- the standards tree should absorb the stable shared contracts from those task
  documents instead of mirroring their folder layout.

If a task document and a standards document appear to disagree on ownership, the
standards tree wins for naming and layering.

## Research Baseline

This standards slice uses only official or officially hosted public material as
its real-world baseline, plus repository-internal code/tests for current
contract alignment.

Current key external references include:

- [Joint Chiefs doctrine publications](https://www.jcs.mil/Doctrine/Service-Publications/)
- [CJCSM 3150.13C, Joint Reporting Structure](https://www.jcs.mil/Portals/36/Documents/Library/Manuals/m315013.pdf)
- [AFDP 3-0.1, Command and Control](https://www.doctrine.af.mil/Portals/61/documents/AFDP_3-0_1/AFDP3-0.1CommandandControl.pdf)
- [U.S. 7th Fleet, CTF 71 establishment](https://www.c7f.navy.mil/Media/News/Display/Article/2641477/ctf-71-establishment-enhances-readiness-in-7th-fleet/)
- [TTGP Warfare Commanders Conference I](https://www.ttgp.navy.mil/OFRP-Syllabus/Warfare-Commanders-Conference-I/)
- [NAVIFOR, IW Has a Seat at the Table](https://www.navifor.usff.navy.mil/Press-Room/News-Stories/Article/2395110/iw-has-a-seat-at-the-table/)
- [MCDP 1-0](https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1323621/mcdp-1-0-w-ch-1-3/)

Current key repository references include:

- [docs/task/flight_dynamics/README.md](../task/flight_dynamics/README.md)
- [docs/task/flight_dynamics/archive/program/realism_program_convergence_plan_20260517.md](../task/flight_dynamics/archive/program/realism_program_convergence_plan_20260517.md)
- [gym_envs/scenario_loader/core.py](../../gym_envs/scenario_loader/core.py)
- [src/core/mission/README.md](../../src/core/mission/README.md)
- [tests/runtime/README.md](../../tests/runtime/README.md)

## Status Categories

The maintained standards tree uses three status categories:

- `Authoritative`
  - current primary standard for maintained work
- `Specialization`
  - platform- or domain-specific supplement
- `Archived`
  - historical path retained for reference only

Current status mapping:

- `joint/*.md`: `Authoritative`
- `services/*.md`: `Authoritative`
- `runtime_workflow_and_contract_baseline.md`: `Authoritative`
- `scenario_guide.md`: `Authoritative bridge`
- `air/*.md`: `Specialization`
- `naval/*.md`: `Specialization`
- `ground/*.md`: `Specialization`
- `docs/Archive/**`: `Archived`
- `docs/task/flight_dynamics/archive/**`: task-history archive, not an active standard source

Additional maintained supplements:

- [naval/ship_unit_references.md](naval/ship_unit_references.md)
  - reference-baseline supplement for first-batch naval units and public-source
    traceability
- [ground/minimal_task_structure.md](ground/minimal_task_structure.md)
  - G0 baseline for the first ground tasking vocabulary and architecture
    constraints
- [modularization_plan.md](planning/modularization_plan.md)
  - active planning supplement for future codebase structure, not a current
    runtime contract

## Maintained Rules

- English `.md` files are canonical. Chinese `.zh.md` files are companions.
- Maintained canonical docs should not keep machine-translation draft markers.
- New shared contracts should land in `joint/` or the `bridge/` workflow
  documents before
  they are repeated in task plans.
- Service-specific or platform-specific terms must not be promoted into the
  common core just because the current implementation started in one domain.
- When work is split across subagents or workers, follow
  [Subagent Usage Policy](governance/subagent_usage_policy.md).
- When a simulation-architecture WP is implementation-complete but still needs
  publication cleanup, use
  [WP Closure Lane Policy](governance/wp_closure_lane_policy.md).

## Related Documents

- [Bilingual Documentation Policy](governance/bilingual_documentation_policy.md)
- [Bilingual Document Clusters](governance/bilingual_document_clusters.md)
- [Subagent Usage Policy](governance/subagent_usage_policy.md)
- [WP Closure Lane Policy](governance/wp_closure_lane_policy.md)
- [Document Alignment Map](overview/document_alignment_map.md)
- [Simulation Conventions](foundation/conventions.md)
- [Scenario Configuration Guide](bridge/scenario_guide.md)
- [Runtime Workflow and Contract Baseline](bridge/runtime_workflow_and_contract_baseline.md)
- [Modularization Plan](planning/modularization_plan.md)
