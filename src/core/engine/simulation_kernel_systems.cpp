#include "simulation_kernel.h"

#include "components/combat/scoring.h"
#include "components/combat/damage.h"
#include "components/combat/health.h"
#include "components/combat/weapon.h"
#include "components/physics/control_law.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/physics/instruments.h"
#include "components/physics/performance.h"
#include "components/systems/comm.h"
#include "components/systems/data_link.h"
#include "components/systems/ew.h"
#include "components/systems/logistics.h"
#include "components/systems/navigation.h"
#include "components/systems/track_management.h"
#include "core/interfaces/environment_model.h"
#include "core/interfaces/control_model.h"
#include "core/interfaces/effects_model.h"
#include "core/interfaces/guidance_model.h"
#include "core/interfaces/sensor_model.h"
#include "systems/combat/damage_system.h"
#include "systems/combat/guidance_system.h"
#include "systems/core/operation_system.h"
#include "systems/physics/aero_state_system.h"
#include "systems/physics/aerodynamics_system.h"
#include "systems/physics/control_system.h"
#include "systems/physics/force_clear_system.h"
#include "systems/physics/force_system.h"
#include "systems/physics/ground_contact_system.h"
#include "systems/physics/instrument_system.h"
#include "systems/physics/leapfrog_system.h"
#include "systems/physics/rotational_system.h"
#include "systems/systems/command_link_system.h"
#include "systems/systems/data_link_system.h"
#include "systems/systems/ew_system.h"
#include "systems/systems/logistics_system.h"
#include "systems/systems/navigation_system.h"
#include "systems/systems/sensor_system.h"
#include "systems/systems/track_manager_system.h"

void SimulationKernel::register_components_and_systems() {

    // EW System: Reset RWR state each frame before sensors run
    ecs.system<RWR>("RWR_Reset")
       .kind(flecs::PreUpdate)
       .each([](flecs::entity e, RWR& rwr) {
           rwr.detected_radar_ids.clear();
           rwr.locking_radar_ids.clear();
           // rwr.is_locked = false; // Removed
           rwr.is_missile_launch = false;
       });

    // Initialize common components
    ecs.component<Transform>();
    ecs.component<Velocity>();
    ecs.component<Alliance>();
    ecs.component<KeyEntity>();
    ecs.component<MovementCommand>();
    ecs.component<PilotAction>(); // New
    ecs.component<MissionCommand>(); // New
    ecs.component<TaskOrder>();
    ecs.component<LeaderIntent>();
    ecs.component<PendingMissionCommand>();
    ecs.component<ActionCommand>();
    ecs.component<ActionSpaceConfig>();
    ecs.component<CommandLag>();
    ecs.component<LaggedCommand>();
    ecs.component<CommandLink>();
    ecs.component<PendingMovementCommand>();
    ecs.component<PendingActionCommand>();
    
    // Physics
    ecs.component<LandingGear>();
    ecs.component<Health>();
    ecs.component<Mass>();
    ecs.component<MassProperties>();
    ecs.component<Propulsion>();
    ecs.component<ForceAccumulator>();
    ecs.component<AeroState>();
    ecs.component<ControlLawState>();
    ecs.component<Inertia>();
    ecs.component<AngularVelocity>();
    ecs.component<GroundState>();
    ecs.component<GearState>();
    ecs.component<Missile>();
    ecs.component<Munition>();
    ecs.component<Ammo>();
    ecs.component<WeaponCooldown>();
    
    // EW Components
    ecs.component<Jammer>();
    ecs.component<Countermeasures>();
    ecs.component<RWR>();
    ecs.component<RCSProfile>();
    ecs.component<Lifetime>();
    ecs.component<FuelSystem>();
    ecs.component<Loadout>();
    ecs.component<LogisticsNode>();
    ecs.component<ResupplyState>();

    ecs.component<Sensor>();
    ecs.component<ContactList>();
    ecs.component<FlightModel>(); 
    ecs.component<Score>();
    ecs.component<DataLink>(); // New Component
    ecs.component<CommQueue>();
    ecs.component<PilotReport>();
    ecs.component<InstrumentState>(); // New Component for Digital Pilot
    ecs.component<EGI>(); // GPS/INS
    ecs.component<TrackDatabase>();
    ecs.component<HitboxConfig>();
    ecs.component<SystemHealth>();

    // Systems are registered sequentially below to ensure correct execution order.
    // See "Register Systems IN ORDER" block.

    ecs.component<EffectsModelRef>();
    ecs.component<SensorModelRef>();
    ecs.component<ControlModelRef>();
    ecs.component<GuidanceModelRef>();
    ecs.component<EnvironmentModelRef>();

    // Define Pipeline Phases (explicit ordering)
    // Phase 1: Control - writes platform Velocity based on commands
    // Phase 2: Guidance - writes weapon Velocity (missiles)
    // Phase 3: Movement - integrates Velocity → Transform
    // Phase 4: Sensor - scans for contacts
    // Phase 5: Damage - proximity fuse, hit effects
    
    // Note: With flecs, systems registered on OnUpdate run in registration order.
    // For guaranteed ordering, we use .kind() with custom phases or depends_on.
    // For MVP, registration order is sufficient as long as it's explicit.
    
    // Register Systems IN ORDER (dependency chain)
    register_command_link_system(ecs);   // Phase 0: Command Link
    register_action_mapping_system(ecs); // Phase 1: Action Mapping
    register_command_lag_system(ecs);    // Phase 2: Command Lag
    register_control_system(ecs);        // Phase 3: Control (adds control torques)
    register_force_clear_system(ecs);    // Phase 3.1: Clear Forces (per-frame)
    register_aero_state_system(ecs);     // Phase 3.2: Aero State (AoA/beta/q)
    register_force_system(ecs);          // Phase 3.3: Forces (gravity/thrust)
    register_aerodynamics_system(ecs);   // Phase 3.4: Aerodynamics (lift/drag + aero torques)
    register_ground_contact_system(ecs, environment_model_.get()); // Phase 3.5: Ground contact/friction/pitch damping
    register_rotational_integration_system(ecs); // Phase 3.6: Rotational Dynamics (ALL torques -> attitude)
    register_guidance_system(ecs);       // Phase 4: Guidance
    register_leapfrog_integration_system(ecs); // Phase 5: Leapfrog Integration (translation)
    // register_movement_system(ecs);       // Phase 5.5: Movement (disabled - replaced by Leapfrog)
    register_navigation_system(ecs);     // Phase 5.8: Navigation/EGI (after integration, before instruments)
    register_sensor_system(ecs);         // Phase 6: Sensor
    register_data_link_system(ecs);      // Phase 6.5: Data Link Fusion (Post-Sensor)
    register_track_manager_system(ecs);  // Phase 6.55: Build fused track picture from local sensor + data link
    register_instrument_system(ecs);     // Phase 6.6: Instruments (Read Physics & Sensor State)
    register_damage_system(ecs);         // Phase 7: Damage/Effects
    register_ew_system(ecs);             // Phase 8: EW Actions
    register_logistics_system(ecs);      // Phase 9: Logistics

    ecs.set<EffectsModelRef>({effects_model_.get()});
    ecs.set<SensorModelRef>({sensor_model_.get()});
    ecs.set<ControlModelRef>({control_model_.get()});
    ecs.set<GuidanceModelRef>({guidance_model_.get()});
    ecs.set<EnvironmentModelRef>({environment_model_.get()});
}
