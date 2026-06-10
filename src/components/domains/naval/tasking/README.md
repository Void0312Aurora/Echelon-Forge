# `src/components/domains/naval/tasking` Boundaries

`components/domains/naval/tasking` stores tasking extensions for naval/maritime mission organization. It carries naval-specific semantics such as station type, maritime mission roles, command authority, and embarked aviation task organization, rather than shared tasking core or execution layer commands.

## Allowed

- Maintained extension fields for `TaskOrderNaval`, `LeaderIntentNaval`, `PilotReportNaval`.
- Pure DTO semantics related to screen stations, warfare roles, officer-in-tactical-command, and embarked air operations.
- Naval-side supplements to the shared tasking core in `common/`, without directly translating air terminology to ship terms.

## Prohibited

- Command objects such as `MissionCommand`, `PilotAction`, `CommandLink`; these belong in `components/command`.
- Tick/update logic for ship movement, data links, sensors, or aircraft launch/recovery; these belong in `systems/`.
- Mission transitions, scenario loaders, reward/termination logic, or facade adapters.
- Using this directory as a substitute statement that "the naval runtime already fully exists".

## Current State

The current directory is in a first-stage maintained DTO phase:

- Shared/joint layer fields should continue to reside in `common/*`.
- Existing air sortie semantics remain in `air/*`.
- Naval-specific station and command-authority owner slices are present for `TaskOrder`, `LeaderIntent`, and `PilotReport`.
- Facade/runtime contracts can transport the naval tasking slice, but mission execution still stays bounded by the lower runtime owner.

This means the directory is already the formal boundary entry point for the current mainline, but not yet proof of a complete naval tasking runtime.

## Dependency Direction

This directory may depend on `components/tasking/common`. It should not depend on `core/mission`, `systems/`, `runtime/facade`, or `interfaces/python`.
