<!-- Machine-translated draft generated on 2026-05-18 from src/components/tasking/naval/README.md. Review before treating this file as authoritative. -->

# `src/components/tasking/naval` Boundaries

`components/tasking/naval` stores tasking extensions for naval/maritime mission organization. It carries naval-specific semantics such as formation stations, maritime mission roles, fleet coordination, and embarked aviation task organization, rather than shared tasking core or execution layer commands.

## Allowed

- Future extension fields for `TaskOrderNaval`, `LeaderIntentNaval`, `PilotReportNaval`.
- Pure DTO semantics related to ship formations, screen stations, warfare commanders, embarked air operations.
- Naval-side supplements to the shared tasking core in `common/`, without directly translating air terminology to ship terms.

## Prohibited

- Command objects such as `MissionCommand`, `PilotAction`, `CommandLink`; these belong in `components/command`.
- Tick/update logic for ship movement, data links, sensors, or aircraft launch/recovery; these belong in `systems/`.
- Mission transitions, scenario loaders, reward/termination logic, or facade adapters.
- Using this directory as a substitute statement that "the naval runtime already fully exists".

## Current State

The current directory is still in the first-stage landing zone phase:

- Shared/joint layer fields should continue to reside in `common/*`.
- Existing air sortie semantics remain in `air/*`.
- Naval-specific organization, stations, and embarked aviation mission semantics are reserved here as stable landing points.

This means the directory is already the formal boundary entry point for the current mainline, but not yet proof of a complete naval tasking runtime.

## Dependency Direction

This directory may depend on `components/tasking/common`. It should not depend on `core/mission`, `systems/`, `runtime/facade`, or `interfaces/python`.
