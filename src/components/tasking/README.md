# `src/components/tasking` Boundary

`components/tasking` is the home directory for formations, task assignment, leader intent, pilot report, and C2 status DTOs. It describes “intent and task status”, not how underlying actions are executed by physical systems.

The current directory boundary already separates tasking and command. The
maintained shape is a common C2/tasking foundation plus domain extensions:
`common` carries shared semantics, while
`components/domains/<domain>/tasking` carries each domain slice. Ground runtime
movement, sensing, fires, terrain, and damage remain held.

## Allowed

- Cross-domain shared tasking/C2 base enums and DTOs, for example semantics such as authority, relationship, service, task family, coordination.
- Task status objects such as `TaskOrder`, `LeaderIntent`, `PilotReport`, and their shared common plus domain-owned layered versions.
- Lightweight task states readable and writable by mission runtime, facade, and Python binding.

## Forbidden

- `PilotAction`, `MissionCommand`, `CommandLink` and legacy movement/action commands; these belong to `components/command`.
- Waypoint transition, landing transition, or task JSON interpretation logic; these belong to `core/mission`.
- Physical control, sensor, weapon, data link tick logic.
- Python binding code.

## Split Direction

- `common tasking` holds cross-domain shared semantics: for example C2/authority/relationship, task family, generic assignee or coordination metadata.
- `components/domains/air/tasking` holds semantics that are currently clearly aviation-oriented: for example CAP, takeoff/landing, runway, formation, wingman, approach/recovery.
- `components/domains/naval/tasking` holds the current vessel/maritime tasking slice: naval station type, warfare role, and officer-in-tactical-command owner fields. It should not directly reuse air's runway/formation/recovery naming.
- `components/domains/ground/tasking` holds the current static G0/G1 slice: objective/area references, static occupy/support task mode, tactical commander ID, tactical cadence, and status/readiness metadata. Do not represent land movement, sensing, fires, damage, or terrain-control semantics as generic `common` fields just to avoid a later dedicated ground schema.
- `TaskOrder`, `LeaderIntent`, `PilotReport` are more suitable than `MissionCommand` for a first documentation and type layer split, because they are currently more on the DTO/API surface, not on a highly coupled flight control execution surface.

## Dependency Direction

Tasking DTOs reside at the data layer. `core/mission` can interpret them, `systems/` can consume them, `runtime/facade` can batch-set and export them, but tasking must not depend on these upper layers.

## Migration Notes

Already landed:

- `components/domains/air/tasking/air_tasking_enums.h`
- `components/domains/naval/tasking/naval_tasking_enums.h`
- `components/domains/ground/tasking/ground_tasking_enums.h`
- `tasking_enums.h`
- `task_order.h`
- `leader_intent.h`
- `pilot_report.h`
- `common/*` plus `components/domains/<domain>/tasking/*` owner slices for task order, leader intent, and pilot report.

WP0 document stance:

- First identify which fields/enums should sink to `common`.
- Then separate air-specific semantics from shared DTOs.
- Naval side models independently and has a limited maintained tasking slice; it does not follow the “ship = air but on water” split approach.
- Ground-aware setup now has a maintained static task/status owner slice here, while ground movement/runtime behavior remains held beyond bootstrap evidence.
- `tasking_enums.h` is retained as a compatibility umbrella; new code should preferentially explicitly depend on `common/core_tasking_enums.h` or the relevant `components/domains/<domain>/tasking/*_tasking_enums.h`.

Although `MissionCommand` is strongly related to tasking, it belongs to the command side and is a high-risk subsequent split item: it is already connected to execution episodes, mission runtime, control laws, and observation chains. WP0 clarifies the direction; do not describe it in the tasking document as an object that can be safely extracted immediately.

The old `components/physics/action.h` has been demoted to a compatibility umbrella include. New code should include the specific header files.
