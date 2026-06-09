# Current Engine Capabilities

Status: `2026-06-01` multi-domain maintenance note.

Echelon Forge has a simulation kernel based on **ECS (flecs)**. The air/execution
path remains the most mature runtime and training surface, while naval has
maintained pre-fire tasking/contact evidence plus bounded weapon-release and
engagement-event hooks. Ground has early tasking/schema evidence at the project
level, but the maintained C++ `src` surface is limited to setup/type/capability
evidence and aircraft/terrain ground-contact primitives. The description below
is based on the current repository implementation; it is not a release claim
for complete naval or ground combat runtime.

## 1) Core Capabilities (What It Can Do Now)

### A. Fixed-Step Simulation Loop + Reproducibility
- Advances the world with a fixed `dt` (default 60Hz), supports reset seed for reproducible experiments.
- The system pipeline has a clear order: command chain / action mapping / lag / control / motion integration / sensors / damage / EW / logistics, etc.

### B. Unit Assembly (Database -> Components)
- Supports assembling platform/content definitions from JSON in
  `examples/config/database`, including aircraft, ships, weapons, damage
  inputs, facilities, modules, and early ground unit schema fixtures.
- Key components include: `Transform/Velocity/FlightModel/LandingGear/Mass/Propulsion/FuelSystem/...`

### C. Motion and Control (Key)
- **LeapfrogIntegrationSystem**: This is the active translational integrator in
  the current kernel. It advances position and velocity from force accumulation
  and mass, and is the mainline motion integration path used by
  `SimulationKernel`.
- **MovementSystem**: Still present as a simpler legacy `Velocity ->
  Transform` integrator, but currently disabled in the active kernel path.
- **ControlModel (DefaultControlModel)**:
  - Supports two types of control inputs:  
    1) **Autopilot target control**: target heading / speed / altitude (used for RL cruise / waypoint missions)  
    2) **Stick direct control**: roll/pitch/throttle/gear (used for RL takeoff missions)
  - Includes aircraft runway/taxiway ground-contact logic: speed limits,
    unpaved / water detection, rolling resistance / braking, etc. This supports
    air/execution runway phases and crash detection; it is not ground-domain
    movement/sensing/fires runtime support.

### D. Environment (Basic Version)
- Atmosphere: temperature / pressure / density / wind (simplified ISA)
- Terrain / surface: SurfaceType such as runway / taxiway / soft earth / water, providing friction and runway heading information

### E. Perception / Engagement (Basic Version)
- Sensor system: scanning and track memory, accesses `SensorModel`
- Weapons / guidance / damage / EW / data link: basic systems, components, and
  engagement evidence exports exist, suitable for bounded expansion of tactical
  layer training.
- Naval support is currently pre-fire/tasking/contact oriented with bounded
  weapon-release and engagement-event evidence hooks; do not infer complete
  naval weapon-outcome authority from these entries.
- Ground support is currently schema/setup/bootstrap oriented in C++ `src`;
  there is no maintained C++ ground command/tasking owner, and movement,
  sensing, terrain, fires, damage, and full ground runtime behavior remain held.

## 2) Key Limitations (The Most Sensitive Part for "Training Going Astray")

- **Flight dynamics are still a simplified point-mass/envelope model**: no full 6DoF, lift/angle of attack/stability derivatives, etc.; some paths are "kinematically written as speed," requiring constraints like energy conservation / thrust-drag ratio to reduce the exploration space.
- **Logistics and throttle consistency still need to be strengthened**: fuel consumption currently approximates "throttle" via actions, and is not fully consistent with the autopilot's target speed control.
- **Environment/terrain is still procedurally simplified**: suitable for early RL training, but still far from real airports/terrain.

## 3) Interface with RL (Ready-Made)

- `ef_py.SimulationKernel.set_action(...)`: normalized autopilot actions (turn/accel/climb)
- `ef_py.SimulationKernel.set_stick_command(...)`: direct stick commands (roll/pitch/throttle/gear)

For a more detailed "physics engine inventory", see: `docs/manual/physics_engine_inventory.md`.
