# Scenario Configuration Guide

Language:
- English canonical: `scenario_configuration_guide.md`
- Chinese companion: [scenario_configuration_guide.zh.md](scenario_configuration_guide.zh.md)

Document kind: `howto`
Lifecycle: `maintained`
Canonical: `docs/operations/howto/scenario_configuration_guide.md`
Owner: `operations/scenario-configuration`
Last verified: `2026-08-08`

Status: maintained scenario JSON authoring and loader-mapping guide.

This document describes the current repository JSON scenario implementation
surface. It is not itself the doctrine baseline or a DTO authority. Its job is
to explain how maintained scenario JSONs map onto owner standards and the
current runtime workflow.

Read this after:

- [Operations Documentation Overview](../README.md)
- [Document Alignment Map](../../engineering/documentation/reference/document_alignment_map.md)
- [Runtime Workflow and Contract Baseline](../../architecture/standards/runtime_workflow_and_contract_baseline.md)

## Scope

This guide answers three questions:

1. Which fields can current loaders and compilers consume directly?
2. Which fields are still implementation-era JSON seams rather than stable
   common-core ontology?
3. How should scenario authors map tasking concepts to the current runtime
   without confusing common core, service profile, and specialization ownership?

It does not define:

- joint command relationships
- service doctrine
- the full runtime DTO contract

## Current Runtime Relationship

The current scenario path is roughly:

`scenario JSON -> loader/compiler -> normalized mission/task state -> runtime step evaluation -> mission observation/reward/termination products`

Repository entrypoints involved in that path include:

- [gym_envs/scenario_loader/loading.py](../../../gym_envs/scenario_loader/loading.py)
- [gym_envs/scenario_loader/core.py](../../../gym_envs/scenario_loader/core.py)
- [gym_envs/scenario_loader/behavior_runtime/](../../../gym_envs/scenario_loader/behavior_runtime)
- [src/core/mission/runtime/](../../../src/core/mission/runtime)

Scenario JSON is therefore a configuration input surface, not the final runtime
contract by itself.

## Mapping To The Standards Tree

Under the maintained split:

- `docs/domains/joint/` owns shared tasking/task-organization vocabulary
- `docs/domains/joint/service_profiles/` owns service-specific interpretation
- `docs/domains/air/` and `docs/domains/naval/` own execution-level
  specialization

Scenario files may temporarily carry a mix of these concepts because the current
runtime is still a bridge. When that happens, use these rules:

- keep shared ownership terms generic
- keep service-specific interpretation under the relevant service profile
- keep air/naval execution details in specialization-owned fields

Examples:

- `service_profile`, `task_family`, and `tactical_unit_type` are common/service
  alignment fields
- `takeoff_procedure_code` and `runway_slot_code` are air specialization fields
- `task_group_id` is a shared anchor whose naval meaning is interpreted by the
  Navy profile

## Top-Level Structure

A maintained scenario file typically contains:

```json
{
  "scenario_name": "Example Scenario",
  "environment": { ... },
  "entities": [ ... ],
  "task_order": { ... },
  "mission_command": { ... },
  "objectives": [ ... ],
  "rewards": { ... },
  "meta": { ... }
}
```

Not every scenario uses every section today, but this is the current effective
bridge shape.

## `environment`

`environment` defines world-level runtime settings such as:

- `time_step`
- `max_steps`
- `terrain_type`

These are engine/runtime configuration values, not doctrine or service-profile
 values.

## `entities`

`entities` defines the instantiated participants in the scenario.

Common fields include:

- `name`
- `type`
- `side`
- `pos`
- `vel`
- `heading`
- `is_agent`

These fields define world state and scenario roster membership. They do not, by
themselves, define command relationship, authority, or task organization.

If task organization matters, prefer expressing it through task/tasking metadata
and roster/task-order bridges rather than overloading entity names.

## `task_order`

`task_order` is the scenario-side mission tasking object.

It is the closest maintained bridge to the common-core side of the command
workflow. In current practice it may carry:

- task family or tasking intent
- target altitude/speed/heading hints
- route or waypoint-oriented intent
- role/slot-oriented metadata used by the runtime bridge

`task_order` should be read as upstream tasking intent, not as the final
executable command.

## `mission_command`

`mission_command` is the scenario-side representation of the executable command
state that the runtime can consume after normalization.

Current maintained practice includes fields such as:

- `command_code`
- `target_heading`
- `target_altitude`
- `target_speed`
- route/waypoint information
- air-specific takeoff, runway, and formation fields
- naval-specific station/reference fields where currently supported

This object sits at the bridge between scenario JSON and runtime command state.
Its shared semantics are governed by the joint/common-core command baseline;
its service/platform extensions belong to the applicable owner-local domain
standard.

## `objectives`

`objectives` defines success conditions or mission-phase completion conditions.

Common maintained shapes currently include:

- `conditional`
- `capture_zone`

Objective property names may reference runtime-exposed values such as altitude,
speed, runway geometry, localizer/glideslope error, and similar terms.

These property names are current runtime-contract inputs. They are not all
common-core ontology terms.

## `rewards`

`rewards` defines shaping and penalty configuration.

Examples include:

- `survival`
- `crash_penalty`
- task-specific shaping config

Reward config belongs to the runtime workflow bridge. It should not be used to
smuggle service doctrine into scenario JSON naming.

## `meta`

`meta` is the bucket for scenario-level metadata that the loader/compiler may
consume without treating it as executable command state.

Use `meta` for annotations, experiment knobs, or compile/runtime toggles that
do not belong in mission tasking semantics.

## Authoring Rules

When authoring or revising maintained scenarios:

1. Use common/service terms when the concept truly crosses domains.
2. Use air/naval specialization fields only for execution semantics that belong
   to those layers.
3. Keep `task_order` and `mission_command` distinct in intent.
4. Do not encode authority/organization solely through entity naming patterns.
5. Prefer adding explicit metadata fields over overloading an unrelated command
   field.

## Related Documents

- [Runtime Workflow and Contract Baseline](../../architecture/standards/runtime_workflow_and_contract_baseline.md)
- [Joint Command and Modeling Baseline](../../domains/joint/standards/command_and_modeling_baseline.md)
- [Joint Command-Link and Reporting Baseline](../../domains/joint/standards/command_link_and_reporting_baseline.md)
- [US Navy Profile](../../domains/joint/service_profiles/standards/navy_profile.md)
- [Air Standards Overview](../../domains/air/README.md)
- [Naval Standards Overview](../../domains/naval/README.md)
