#include "simulation_kernel.h"

#include "components/combat/scoring.h"
#include "components/combat/damage.h"
#include "components/combat/health.h"
#include "components/combat/weapon.h"
#include "components/command/command_link_qos.h"
#include "components/command/common/mission_command_control_state.h"
#include "components/physics/control_law.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/physics/flight_dynamics_tuning.h"
#include "components/physics/instruments.h"
#include "components/physics/performance.h"
#include "components/systems/comm.h"
#include "components/systems/data_link.h"
#include "components/systems/ew.h"
#include "components/systems/logistics.h"
#include "components/systems/navigation.h"
#include "components/systems/sonar.h"
#include "components/systems/track_management.h"
#include "components/naval/embarked_air_ops.h"
#include "components/naval/submarine_platform.h"
#include "core/interfaces/environment_model.h"
#include "core/interfaces/acoustic_model.h"
#include "core/interfaces/control_model.h"
#include "core/interfaces/effects_model.h"
#include "core/interfaces/guidance_model.h"
#include "core/interfaces/sensor_model.h"
#include "systems/combat/damage_system.h"
#include "systems/combat/guidance_system.h"
#include "systems/combat/pilot_weapon_release_system.h"
#include "systems/core/operation_system.h"
#include "systems/naval/naval_mission_weapon_release_system.h"
#include "systems/physics/aero_state_system.h"
#include "systems/physics/aerodynamics_system.h"
#include "systems/physics/control_system.h"
#include "systems/physics/force_clear_system.h"
#include "systems/physics/force_system.h"
#include "systems/physics/ground_contact_system.h"
#include "systems/physics/instrument_system.h"
#include "systems/physics/leapfrog_system.h"
#include "systems/physics/propulsion_system.h"
#include "systems/physics/rotational_system.h"
#include "systems/naval/ship_motion_system.h"
#include "systems/naval/submarine_motion_system.h"
#include "systems/naval/embarked_air_ops_system.h"
#include "systems/systems/command_link_system.h"
#include "systems/systems/data_link_system.h"
#include "systems/systems/ew_system.h"
#include "systems/systems/logistics_system.h"
#include "systems/systems/navigation_system.h"
#include "systems/systems/sensor_system.h"
#include "systems/systems/sonar_system.h"
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

    ecs.system<ESMReceiver>("ESM_Reset")
       .kind(flecs::PreUpdate)
       .each([](flecs::entity e, ESMReceiver& esm) {
           esm.detections.clear();
       });

    // Initialize common components
    ecs.component<Transform>();
    ecs.component<Velocity>();
    ecs.component<Alliance>();
    ecs.component<KeyEntity>();
    ecs.component<MovementCommand>();
    ecs.component<MissionCommandControlState>();
    ecs.component<PilotAction>(); // New
    ecs.component<MissionCommand>(); // New
    ecs.component<TaskOrder>();
    ecs.component<LeaderIntent>();
    ecs.component<PendingMissionCommand>();
    ecs.component<MissionCommandPendingQueue>();
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
    ecs.component<ShipPlatform>();
    ecs.component<SubmarinePlatform>();
    ecs.component<Propulsion>();
    ecs.component<AeroTuning>();
    ecs.component<EngineTuning>();
    ecs.component<StallState>();
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
    ecs.component<PilotWeaponReleaseState>();
    ecs.component<NavalWeaponSystem>();
    
    // EW Components
    ecs.component<Jammer>();
    ecs.component<Countermeasures>();
    ecs.component<RWR>();
    ecs.component<ESMReceiver>();
    ecs.component<RCSProfile>();
    ecs.component<Lifetime>();
    ecs.component<FuelSystem>();
    ecs.component<Loadout>();
    ecs.component<LogisticsNode>();
    ecs.component<NavalStores>();
    ecs.component<ResupplyState>();

    ecs.component<Sensor>();
    ecs.component<MountedSensors>();
    ecs.component<Sonar>();
    ecs.component<MountedSonars>();
    ecs.component<ContactList>();
    ecs.component<FlightModel>(); 
    ecs.component<Score>();
    ecs.component<DataLink>(); // New Component
    ecs.component<CommQueue>();
    ecs.component<PilotReport>();
    ecs.component<InstrumentState>(); // New Component for Digital Pilot
    ecs.component<EGI>(); // GPS/INS
    ecs.component<TrackDatabase>();
    ecs.component<EmbarkedAirOps>();
    ecs.component<HitboxConfig>();
    ecs.component<SystemHealth>();
    ecs.component<ComponentDamageState>();
    ecs.component<PlatformDamageState>();
    ecs.component<AircraftDamageState>();
    ecs.component<AircraftDamageBaseline>();

    // Systems are registered sequentially below to ensure correct execution order.
    // See "Register Systems IN ORDER" block.

    ecs.component<EffectsModelRef>();
    ecs.component<EngagementEventRecorderRef>();
    ecs.component<SensorModelRef>();
    ecs.component<AcousticModelRef>();
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
    flight_dynamics::register_propulsion_system(ecs); // Phase 3.3: Propulsion runtime state (throttle/spool/thrust/fuel basis)
    register_force_system(ecs);          // Phase 3.4: Forces (gravity + propulsion thrust projection)
    register_aerodynamics_system(ecs);   // Phase 3.5: Aerodynamics (lift/drag + aero torques)
    register_ground_contact_system(ecs, environment_model_.get()); // Phase 3.6: Ground contact/friction/pitch damping
    register_rotational_integration_system(ecs); // Phase 3.7: Rotational Dynamics (ALL torques -> attitude)
    register_guidance_system(ecs);       // Phase 4: Guidance
    register_leapfrog_integration_system(ecs); // Phase 5: Leapfrog Integration (translation)
    register_ship_motion_system(ecs);      // Phase 5.2: simple surface-ship kinematics
    register_submarine_motion_system(ecs); // Phase 5.25: simple submarine kinematics
    // register_movement_system(ecs);       // Phase 5.5: Movement (disabled - replaced by Leapfrog)
    register_navigation_system(ecs);     // Phase 5.8: Navigation/EGI (after integration, before instruments)
    register_sensor_system(ecs);         // Phase 6: Sensor
    register_sonar_system(ecs);          // Phase 6.1: Sonar / acoustic contacts
    register_track_manager_system(ecs);  // Phase 6.5: Build local/fused track picture from sensor + prior inbox
    register_data_link_system(ecs);      // Phase 6.55: Share current track picture to peers
    register_embarked_air_ops_system(ecs); // Phase 6.57: Embarked helo token launch/recover/relay
    IWeaponReleaseService& weapon_release_service = *this;
    register_pilot_weapon_release_system(ecs, weapon_release_service); // Phase 6.58: Pilot weapon release bridge
    register_naval_mission_weapon_release_system(ecs, weapon_release_service); // Phase 6.59: Naval mission weapon release bridge
    register_instrument_system(ecs);     // Phase 6.6: Instruments (Read Physics & Sensor State)
    register_damage_system(ecs);         // Phase 7: Damage/Effects
    register_ew_system(ecs);             // Phase 8: EW Actions
    register_logistics_system(ecs);      // Phase 9: Logistics

    ecs.set<EffectsModelRef>({effects_model_.get()});
    ecs.set<EngagementEventRecorderRef>({this});
    ecs.set<SensorModelRef>({sensor_model_.get()});
    ecs.set<AcousticModelRef>({acoustic_model_.get()});
    ecs.set<ControlModelRef>({control_model_.get()});
    ecs.set<GuidanceModelRef>({guidance_model_.get()});
    ecs.set<EnvironmentModelRef>({environment_model_.get()});
}
