# Standards Documentation Overview

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Status: `2026-06-10` authoritative for the maintained standards tree.

This directory defines the standardized modeling baseline the project intends to
use going forward. Its job is not to restate every active implementation task.
Its job is to tell contributors which concepts belong to the joint/common core,
which belong to service profiles, which belong to domain specializations, which
cross-domain runtime/bridge/foundation constraints every layer must honor, and
how the current code/runtime should align with that split.

## Purpose

The maintained standards tree exists to keep three things from drifting apart:

- real-world public doctrine and reference material
- the repository's current runtime and test contracts
- active task planning under `docs/task/`

The standards tree is therefore the ownership map. Task plans may describe
current implementation waves, but they should not redefine which layer owns
`authority_scope`, `task_group_id`, `runway_slot_code`, or `warfare_role_code`.
Implementation maturity in a task area is useful status context, but it is not
the standard ownership hierarchy.

## Tree Structure

Since `2026-03-23`, the standards documentation is no longer organized around
an "air first, generalize later" line. Its maintained ownership spine now
follows:

1. `joint/`
2. `services/`
3. `air/`
4. `naval/`
5. `ground/`
6. `model/`

This spine is read together with the cross-domain standards under `foundation/`
and `bridge/`, including runtime workflow and contract baselines. Those
documents constrain every domain; they do not form a separate service or
platform stack.

The `model/` layer is cross-domain. It owns model/policy architecture vocabulary
for reinforcement-learning components, auxiliary heads, loss ownership, runtime
action adapters, and diagnostics. It does not own service or domain semantics.

The maintained tree therefore reflects a deliberate modeling split:

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
- `model/` defines policy/model architecture boundaries that can be reused by
  air, naval, ground, cooperative, and world-model work without promoting any
  single domain's task status into a model standard.

Third-domain navigation must route through both layers: `services/army.md`
owns Army service-profile interpretation, while `ground/` owns maintained
ground specialization semantics. The aliases `army` and `land` normalize to
the maintained `ground` specialization and do not create a separate `army`
runtime stack.

## Ownership Hierarchy

Use this hierarchy when deciding where a stable concept belongs:

1. `foundation/` and runtime/bridge constraints define cross-domain rules:
   coordinate and time conventions, realism gates, public-source admission,
   scenario/runtime workflow boundaries, DTO alignment, and current testable
   contracts. They constrain every service and specialization.
2. `joint/` owns shared semantic objects such as command relationships,
   authority scopes, task/report identifiers, support relationships, and other
   names that must mean the same thing across services.
3. `services/` owns service-profile interpretation: how the Air Force, Army,
   Navy, and Marine Corps read the shared objects, which echelons or unit
   forms are admissible, and where service-specific terminology stops before
   becoming domain mechanics.
4. `air/`, `naval/`, and `ground/` own domain specialization. They can define
   platform, mission, environment, and execution semantics that should not be
   promoted into the common core just because one domain implemented them first.
5. `model/` owns cross-domain model/policy architecture vocabulary: executable
   branches, auxiliary heads, action adapters, loss ownership, rollout labels,
   and diagnostic surfaces.

This is an ownership hierarchy, not a maturity ladder. A mature air-combat or
flight-dynamics implementation does not make air concepts project-wide common
core. An early naval or ground bootstrap can still establish the authoritative
owner for its service/profile and specialization concepts. Missing or partial
runtime support should be tracked as implementation work, not as a lower
standard layer.

## Recommended Reading Order

For new work, read in this order:

1. [Joint Standards Overview](joint/README.md)
2. [Joint Command and Modeling Baseline](joint/command_and_modeling_baseline.md)
3. [Joint Command-Link and Reporting Baseline](joint/command_link_and_reporting_baseline.md)
4. [Runtime Workflow and Contract Baseline](bridge/runtime_workflow_and_contract_baseline.md)
5. [Gradient Realism Principles](foundation/gradient_realism_principles.md)
6. [Public Data Source Admission Standard](foundation/public_data_source_admission.md)
7. [Service Profile Overview](services/README.md)
8. [USAF Profile](services/air_force.md)
9. [US Army Profile](services/army.md)
10. [US Navy Profile](services/navy.md)
11. [Document Alignment Map](overview/document_alignment_map.md)
12. [Scenario Configuration Guide](bridge/scenario_guide.md)
13. [Air Platform Specialization Overview](air/README.md)
14. [Naval Standards Overview](naval/README.md)
15. [Ground Standards Overview](ground/README.md)
16. [Model Architecture Standards Overview](model/README.md)

## Relationship to Active Task Plans

The current task tree under `docs/task/` contains active or recently active
execution workstreams for flight dynamics, air combat, common air/naval splits,
naval realism, ground bootstrap, simulation architecture, runtime/performance,
model work, and cross-cutting issue tracking.

That task-tree layout is useful for execution, backlog ownership, and maturity
tracking, but it is not the ownership map for the standardized model. A task
area may be more implemented, less implemented, archived, or newly bootstrapped
without changing the standards layer that owns its stable concepts. In
particular:

- `flight_dynamics/flight`, `sensor_situation`, `weapon_guidance`, and
  `air_combat` mostly exercise implementation realism and air specialization;
  they do not make air the default common core.
- `flight_dynamics/c2_command_chain`, `simulation_architecture`, and
  cross-cutting runtime/performance work often produce contracts that belong in
  `joint/`, `foundation/`, or `bridge/`.
- `common_air_naval` and naval task plans contain concepts split across shared
  semantics, `services/navy.md`, and `naval/`.
- `ground` task plans contain concepts split across shared semantics,
  `services/army.md`, and `ground/`; the `army` and `land` aliases route
  through that split rather than through a new runtime stack.
- model, training, evaluation, and issue-board tasks may depend on standards
  contracts, but they should cite or pressure the relevant standard owner
  instead of defining a parallel hierarchy. Model-architecture vocabulary belongs
  in `model/`.
- the standards tree should absorb stable shared contracts from task documents
  instead of mirroring the task folder layout or the current rollout maturity of
  each domain.

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

- [docs/task/README.md](../task/README.md)
- [docs/task/flight_dynamics/README.md](../task/flight_dynamics/README.md)
- [docs/task/air_combat/README.md](../task/air_combat/README.md)
- [docs/task/naval/README.md](../task/naval/README.md)
- [docs/task/ground/README.md](../task/ground/README.md)
- [docs/task/simulation_architecture/README.md](../task/simulation_architecture/README.md)
- [docs/standards/model/README.md](model/README.md)
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

These categories describe documentation authority and specialization ownership.
They do not claim that every owned concept is equally implemented in runtime,
tests, scenarios, models, or UI surfaces.

Current status mapping:

- `foundation/*.md`: `Authoritative foundation`
- `joint/*.md`: `Authoritative`
- `services/*.md`: `Authoritative`
- `runtime_workflow_and_contract_baseline.md`: `Authoritative`
- `scenario_guide.md`: `Authoritative bridge`
- `air/*.md`: `Specialization`
- `naval/*.md`: `Specialization`
- `ground/*.md`: `Specialization`
- `model/*.md`: `Authoritative model architecture`
- `docs/Archive/**`: `Archived`
- `docs/task/flight_dynamics/archive/**`: task-history archive, not an active standard source

Additional maintained supplements:

- [air/kill_chain_expectation_envelope.md](air/kill_chain_expectation_envelope.md)
  - active planning supplement for air-to-air kill-chain expectation-envelope
    review labels; not a current runtime contract or calibration authority
- [naval/ship_unit_references.md](naval/ship_unit_references.md)
  - reference-baseline supplement for first-batch naval units and public-source
    traceability
- [naval/obs.md](naval/obs.md)
  - mission-observation contract for the maintained naval screen/station mode
- [ground/minimal_task_structure.md](ground/minimal_task_structure.md)
  - G0 baseline for the first ground tasking vocabulary and architecture
    constraints
- [model/policy_execution_architecture.md](model/policy_execution_architecture.md)
  - cross-domain policy execution, auxiliary-head, loss, reward, adapter, and
    probe ownership baseline
- [modularization_plan.md](planning/modularization_plan.md)
  - active planning supplement for future codebase structure, with current
    `src/*/domains` layout notes; not a current runtime contract

## Maintained Rules

- English `.md` files are canonical. Chinese `.zh.md` files are companions.
- Maintained canonical docs should not keep machine-translation draft markers.
- New shared contracts should land in `joint/` or the `bridge/` workflow
  documents before
  they are repeated in task plans.
- Service-specific or platform-specific terms must not be promoted into the
  common core just because the current implementation started in one domain.
- Standards changes that register, refresh, hold, or retire implementation
  contracts must follow
  [Standards Maintenance Policy](governance/standards_maintenance_policy.md).
- Project-internal work codes and implementation-stage aliases must follow the
  [Internal Code Naming Policy](governance/internal_code_policy.md); stable
  interfaces and runtime diagnostics lead with semantic capability names.
- Documentation kinds, lifecycle states, README boundaries, evidence packs,
  generated output, config indexes, links, and archive transitions must follow
  the [Document Lifecycle Policy](governance/document_lifecycle_policy.md).
- Repository-wide code and documentation consolidation is sequenced through the
  [Repository Consolidation Plan](../plan/repository_consolidation/README.md).
- When work is split across subagents or workers, follow
  [Subagent Usage Policy](governance/subagent_usage_policy.md).
- When a simulation-architecture WP is implementation-complete but still needs
  publication cleanup, use
  [WP Closure Lane Policy](governance/wp_closure_lane_policy.md).

## Related Documents

- [Bilingual Documentation Policy](governance/bilingual_documentation_policy.md)
- [Bilingual Document Clusters](governance/bilingual_document_clusters.md)
- [Document Lifecycle Policy](governance/document_lifecycle_policy.md)
- [Standards Maintenance Policy](governance/standards_maintenance_policy.md)
- [Internal Code Naming Policy](governance/internal_code_policy.md)
- [Release And Dependency Policy](governance/release_and_dependency_policy.md)
- [Subagent Usage Policy](governance/subagent_usage_policy.md)
- [WP Closure Lane Policy](governance/wp_closure_lane_policy.md)
- [Document Alignment Map](overview/document_alignment_map.md)
- [Simulation Conventions](foundation/conventions.md)
- [Gradient Realism Principles](foundation/gradient_realism_principles.md)
- [Public Data Source Admission Standard](foundation/public_data_source_admission.md)
- [Scenario Configuration Guide](bridge/scenario_guide.md)
- [Runtime Workflow and Contract Baseline](bridge/runtime_workflow_and_contract_baseline.md)
- [Modularization Plan](planning/modularization_plan.md)
- [Repository Consolidation Plan](../plan/repository_consolidation/README.md)
