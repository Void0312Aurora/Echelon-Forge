# `src/components/domains/air/tasking` Boundary

`components/domains/air/tasking` stores tasking extensions for the current air mission-organization surface. It carries fields that clearly belong to the air tasking surface, such as formation, takeoff/landing, recovery, and CAP/route semantics, rather than semantics shared across services.

## Allowed

- Air extension fields such as `TaskOrderAir`, `LeaderIntentAir`, and `PilotReportAir`.
- Air-specific tasking enums.
- Pure DTO fields related to formations, stationing, runways, recovery, and approach.

## Forbidden

- Shared joint-layer enums and core fields; those go into `common/`.
- Command-side objects such as `MissionCommand`, `PilotAction`, and `CommandLink`.
- Episode transitions, mission runtime logic, environment glue, or control-law logic.
- Python bindings and facade adaptation.

## Current Files

- [air_tasking_enums.h](air_tasking_enums.h)
- [task_order_air.h](task_order_air.h)
- [leader_intent_air.h](leader_intent_air.h)
- [pilot_report_air.h](pilot_report_air.h)

## Dependency Direction

This directory may depend on `components/tasking/common`. It must not depend on `core/mission`, `systems/`, or `interfaces/python`.
