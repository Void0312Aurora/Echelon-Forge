# Pilot Reporting Contract

Language:
- English canonical: `rep.md`
- Chinese companion: [rep.zh.md](rep.zh.md)

Status: `2026-05-18` specialization baseline for maintained air reporting semantics.

This document defines the maintained air reporting contract for the current
repository. It does not serve as a full brevity-code handbook.

## Scope

The maintained reporting surface is split into:

- `PilotReportCore`
- `PilotReportAir`
- the subset of report types that current leader/runtime logic actually treats
  as stable

Primary references:

- [src/components/tasking/common/pilot_report_core.h](../../../src/components/tasking/common/pilot_report_core.h)
- [src/components/tasking/air/pilot_report_air.h](../../../src/components/tasking/air/pilot_report_air.h)
- [python/rl/tasking/leader_tasking.py](../../../python/rl/tasking/leader_tasking.py)
- [src/runtime/contracts/world_batch_contracts.h](../../../src/runtime/contracts/world_batch_contracts.h)

## Core Report Fields

`PilotReportCore` provides the cross-domain report skeleton:

- `report_type`
- `sender_id`
- `task_id`
- `service_profile`
- `task_family`
- `tactical_unit_type`
- `tactical_unit_id`
- `task_group_id`
- `role_code`
- `coordination_mode`
- `timestamp_s`
- `status_value`
- `entity_ref`
- `location_x_m`
- `location_y_m`
- `location_z_m`
- `active`

These fields belong to common tasking/report ownership, not air ownership.

## Air Report Extension Fields

`PilotReportAir` currently adds:

- `element_id`
- `phase_id`
- `formation_role_id`
- `formation_error_m`
- `bearing_error_deg`
- `closure_mps`
- `separation_m`

These are air-specific reporting fields for formation and air-task execution
context.

## Maintained Stable Report Types

The current leader/runtime loop treats the following report types as stable and
meaningful:

- `REP_ON_STATION`
- `REP_RTB`
- `WARN_BINGO`
- `REP_UNABLE`
- `REP_WILCO`

These are the report types that current runtime logic actually interprets for
task progression or leader assessment.

## Extended Report Surface

The wider DTO and enum surface can carry more report codes, and tests may store
or roundtrip additional air report types such as formation-related status.

However, those broader codes should be documented as extension surface unless
current runtime logic gives them stable closed-loop semantics.

That means this document should not present a large tactical brevity catalog as
if the repository already consumes all of it.

## Report Generation Rules

The maintained pilot-report contract should preserve:

- a valid `report_type`
- sender/task identity
- timestamp
- location
- active state

When formation context matters, air extension fields may also be populated with:

- formation role
- formation error
- bearing error
- closure
- separation

## Ownership Boundary

Keep in common core:

- generic report identity and metadata
- cross-domain tasking/report skeleton

Keep in air specialization:

- formation-specific error and closure data
- phase and element context tied to air-task execution
- air-specific meanings layered on top of shared report types

## Non-Goals

This document does not standardize a complete brevity-code manual, every
possible air-combat callout, or every future leader-agent reporting heuristic.
It documents the maintained reporting contract that current code and tests can
actually roundtrip or interpret.
