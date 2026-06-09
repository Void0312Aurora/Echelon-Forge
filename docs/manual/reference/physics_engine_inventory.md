# Physics Engine Inventory (Implemented)

> Goal: Organize the **already existing and actually effective** "physics/flight dynamics" foundations in the repository by module, provide corresponding code entry points, and facilitate future integration with RL training, gradually replacing reward-hacking learning.

---

## 1) Simulation Loop & Pipeline (ECS)

### 1.1 SimulationKernel: Register Components, Systems, and Update Order

- `SimulationKernel::step()` executes `ecs.progress(dt)` with a fixed timestep `dt`.
- The actively registered flight-dynamics pipeline now follows the current
  runtime order:
  `CommandLink -> ActionMapping -> CommandLag -> Control -> ForceClear -> AeroState -> Propulsion -> Force -> Aerodynamics -> GroundContact -> RotationalIntegration -> Guidance -> LeapfrogIntegration -> Navigation -> Sensor -> Track/DataLink -> Instruments -> Damage -> EW -> Logistics`
- `MovementSystem` still exists in the repository as a simple legacy
  `Velocity -> Transform` integrator, but it is not registered in the current
  kernel and has been replaced on the active path by the Leapfrog translation
  integrator.

Entry:
- `src/core/engine/simulation_kernel.cpp`

### 1.2 Motion Integration: Leapfrog Mainline + Legacy MovementSystem

- The current mainline translational integrator is
  `LeapfrogIntegrationSystem`, which advances `Transform` and `Velocity` from
  accumulated forces and mass using a kick-drift-kick style update.
- This active path reduces drift relative to the old direct `Velocity * dt`
  translation and is the integration stage actually registered by
  `SimulationKernel`.
- `MovementSystem` remains available as a legacy/simple integrator that applies
  `Transform += Velocity * dt` and derives heading from horizontal velocity,
  but it is disabled in the active kernel path.

Entry:
- `src/systems/physics/leapfrog_system.h`
- `src/systems/physics/movement_system.h` (legacy, not currently registered)

---

## 2) Physics/Control-Related Components

### 2.1 Basic State

- `Transform {x,y,z, heading,pitch,roll}`: local ENU coordinates + Euler angles
- `Velocity {vx,vy,vz}`: linear velocity (m/s)

Entry:
- `src/components/basic/common.h`

### 2.2 Command Chain (for mapping RL/upper-level commands to control model)

- `ActionCommand`: RL normalized actions (`turn_rate_cmd/accel_cmd/climb_rate_cmd`) + weapon/EW/communication trigger fields
- `ActionSpaceConfig`: maps normalized actions to physical scales and bounds (`max_turn_rate/max_accel/max_climb_rate`, speed/altitude limits)
- `MovementCommand`:
  - Autopilot targets: `target_heading/target_speed/target_altitude`
  - Direct stick override: `use_stick_control + stick_roll/stick_pitch/throttle_cmd/gear_handle`
  - `active`: whether it is effective
- `CommandLag / LaggedCommand`: first-order lag (avoids "instantaneous target changes")
- `CommandLink / Pending*`: command chain delay and packet loss (for "leader/wingman/datalink" scenarios)

Entry:
- `src/components/physics/action.h`
- `src/systems/core/operation_system.h`
- `src/systems/systems/command_link_system.h`

### 2.3 Platform Performance/Envelope

- `FlightModel`: speed envelope and maneuver capability (`max_speed/min_speed/max_turn_rate/max_accel/max_climb_rate/max_g/min_g`)  
  + ground operation parameters: `takeoff_speed/landing_speed/taxi_turn_rate`
- `LandingGear`: runway/off-road capability, rolling resistance, structural limits, retraction status

Entry:
- `src/components/physics/performance.h`

### 2.4 Propulsion/Mass/Logistics (strongly related to energy model)

- `Mass`: `empty/fuel/stores` and `get_total_kg()` (control model can read total weight)
- `Propulsion`: `mil/AB thrust` + state
- `FuelSystem`: fuel quantity, flow rate, AB status (updated by LogisticsSystem)
- `MassProperties`: empty weight, current total weight, `drag_index` (currently used to store "drag index", but reference area etc. still hardcoded)

Entry:
- `src/components/physics/dynamics.h`
- `src/components/systems/logistics.h`
- `src/systems/systems/logistics_system.h`

---

## 3) Environment Model (Atmosphere/Terrain/Surface)

### 3.1 Atmosphere (Density/Wind)

- `IEnvironmentModel::get_atmosphere_at(x,y,z)` returns `AtmosphericData`: `air_density/pressure/temperature/wind_velocity/...`

Entry:
- `src/core/interfaces/environment_model.h`
- `src/components/basic/environment_data.h`
- `src/models/environment/default_environment_model.cpp`

### 3.2 Terrain and Surface Types (Runway/Taxiway/Soft Ground/Water)

- `IEnvironmentModel::get_terrain_at(x,y)` returns `TerrainCell`: `SurfaceType + friction_mult + roughness + runway_heading ...`
- Default implementation includes:
  - Regular runway/apron "overlay"
  - Low-resolution grid base map (HardPacked/SoftDirt)

Entry:
- `src/core/interfaces/environment_model.h`
- `src/models/environment/default_environment_model.cpp`

---

## 4) Control Model (ControlModel) and "Physics" Fallback

### 4.1 ControlSystem: Feeds Commands to ControlModel

- Priority: `MovementCommand(use_stick_control=true)` (direct stick) takes precedence over `LaggedCommand` (autopilot targets).

Entry:
- `src/systems/air/control_system.h`

### 4.2 DefaultControlModel: Two Dynamics Paths

> This is the core of whether "physics actually takes effect": which control path an aircraft follows determines whether unrealistic trajectories appear (e.g., nearly vertical climb with almost no forward speed).

1) **Stick Control Path (closer to "dynamics")**  
   - Reads `Mass/Propulsion/LandingGear`, computes thrust, drag, simple gravity terms, updates velocity vector  
   - Both ground and airborne branches exist (takeoff environment `F16TakeoffEnv` uses this path)

2) **Autopilot Target Path (RTS/point-mass/kinematics oriented)**  
   - Targets come from `ActionMapping -> MovementCommand -> CommandLag`  
   - Historically had the vulnerability of "allocating almost all velocity to vz, vx≈0" (already fixed via climb angle/vertical speed command generation)
   - Currently includes drag and simplified energy terms, but still needs to further use "energy conservation/thrust-to-weight ratio/drag" to genuinely limit climb and acceleration (this is also the focus for subsequent training integration)

Entry:
- `src/models/air/default_control_model.cpp`

---

## 5) Data Sources (Database)

### 5.1 Aircraft/Engine/Aerodynamic Parameters

- Aircraft units (mass, reference area/drag coefficient, FlightModel envelope, landing gear, etc.):  
  `examples/config/database/aircraft/units/*.json`
- Engine modules (thrust, SFC, etc.):  
  `examples/config/database/aircraft/modules/engines/*.json`

### 5.2 Factory Assembly (JSON to ECS Components)

- `load_unit_definitions_json()` parses JSON into `UnitDefinition`
- `DefaultUnitFactory::spawn()` assembles a `UnitDefinition` into an entity (writes `FlightModel/Mass/Propulsion/FuelSystem/MassProperties/...`)

Entry:
- `src/content/unit_definition_loader.cpp`
- `src/models/core/default_unit_factory.h`

---

## 6) Python / RL Interface Entry Points (APIs Actually Used in Current Training)

### 6.1 ef_py Interface (Gym Environment Invocation)

- `set_action(entity_id, turn, accel, climb, fire, ...)`: goes through autopilot target chain
- `set_stick_command(entity_id, roll, pitch, throttle, gear_down)`: goes through stick path
- `set_command(entity_id, heading, speed, alt)`: directly sets MovementCommand target

Entry:
- `src/interfaces/python/python_module.cpp`

### 6.2 Training Environments (Current Usage)

The current maintained entry points have converged to a universal env and batch runtime, rather than an early per-task
`f16_*_env.py` file:

- `gym_envs/universal_env.py`: execution-layer single-aircraft environment entry; can cover takeoff / cruise / landing / air-combat etc. task lines via scenario and action mode.
- `gym_envs/leader_env.py`: leader/high-level decision environment entry, drives lower-level flight through an execution backend.
- `python/rl/runtime/world_batch_vec_env.py`: maintained execution-layer batch rollout entry.
- `python/rl/runtime/cooperative_world_batch_vec_env.py`: multi-aircraft cooperative execution rollout entry.

Historical note: Early documentation and experiments used dedicated filenames such as `gym_envs/f16_takeoff_env.py`,
`gym_envs/f16_cruise_waypoint_env.py`, `gym_envs/f16_departure_waypoint_env.py`
and `gym_envs/f16_landing_waypoint_env.py`. These are no longer maintained entry
points in the current repository; if old reports mention them, interpret them as legacy references.

Entry:
- `gym_envs/universal_env.py`
- `gym_envs/leader_env.py`
- `python/rl/runtime/world_batch_vec_env.py`
- `python/rl/runtime/cooperative_world_batch_vec_env.py`

---

## 7) Current Gaps (Most Critical for Training)

1) **Autopilot branch still leans toward "kinematics writing velocity"**: Drag/energy terms exist, but need to be tied to "climb/acceleration allocation" to avoid reward-driven unrealistic maneuvers.
2) **Stick branch dynamics are highly simplified**: Currently no explicit lift/angle-of-attack model; velocity vector roughly follows aircraft heading, leading to the simplification that "pitch = directly changes flight path".
3) **Inconsistency between logistics/fuel and thrust/throttle**: Current fuel consumption approximates "throttle" using `ActionCommand.accel_cmd`, which is inconsistent with the autopilot's `target_speed` logic.

These gaps determine that "rewards/penalties" can easily be exploited; therefore it is more recommended to embed physical constraints (energy conservation, envelope, ground contact rules) into the control model, so that learning can only explore within reasonable trajectory space.
