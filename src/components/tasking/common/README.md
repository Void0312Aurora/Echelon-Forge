# `src/components/tasking/common` Boundary

`components/tasking/common` stores the shared tasking/C2 foundation used across services. It defines joint-layer or generic mission-organization semantics without directly carrying platform-specific air or naval fields.

## Allowed

- Shared enums such as `ServiceProfile`, `TaskFamily`, and `CoordinationMode`.
- Shared field shells such as `TaskOrderCore`, `LeaderIntentCore`, and `PilotReportCore`.
- Generic task/intent/report fields that `air/` and `naval/` can extend further.

## Forbidden

- Air-specific fields such as runway, approach, wingman, element, and station-pattern semantics.
- Future naval-specific fields such as naval stations or warfare-command roles.
- Command-layer objects such as `MissionCommand`, `PilotAction`, and `CommandLink`.
- Mission transitions, JSON codecs, or reward/termination logic.

## Current Files

- [core_tasking_enums.h](core_tasking_enums.h)
- [task_order_core.h](task_order_core.h)
- [leader_intent_core.h](leader_intent_core.h)
- [pilot_report_core.h](pilot_report_core.h)

## Dependency Direction

This directory should remain a data layer. `air/` and `naval/` may only reuse the core definitions here downstream; this directory must not depend back on concrete service subdomains.
