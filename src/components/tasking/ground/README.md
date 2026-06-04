# `src/components/tasking/ground` Boundaries

`components/tasking/ground` stores the first maintained ground tasking owner
slice. It formalizes G0/G1 Army/ground tasking status and native static schema
evidence without claiming a land combat runtime.

## Allowed

- G0/G1 tasking status fields for `TaskOrderGround`, `LeaderIntentGround`, and
  `PilotReportGround`.
- Static occupy/support relationship metadata and native schema boundary
  identity for `Ground_Platoon_MVP`.
- Explicit booleans that keep movement, observation export, and fires held
  until separate release votes accept those surfaces.

## Prohibited

- `MissionCommand`, `PilotAction`, action-space, or command-transport objects.
- Ground movement, route following, terrain passability, sensing, fires,
  effects, damage, suppression, sustainment, or combat runtime behavior.
- `CommandPacket`, `ObservationPacket`, or `TrackPacket` claims.
- Scenario loading, reward, termination, facade, binding, or policy code.

## Current State

This directory is the formal C++ component boundary for the current ground
bootstrap line. It is intentionally narrower than the naval tasking slice:
ground has a maintained tasking/status owner slice, but no maintained movement
or observation/action packet boundary yet.

The accepted runtime evidence remains:

- normalized Army/ground `TaskOrder -> LeaderIntent -> PilotReport` status;
- native `Ground_Platoon_MVP` schema load/spawn/identity;
- a native static scenario-loader fixture that consumes that schema.

That evidence is still below a G2 movement release.

## Dependency Direction

This directory may depend on `components/tasking/common`. It must not depend on
`core/mission`, `systems/`, `runtime/facade`, `interfaces/python`, or scenario
loader code.
