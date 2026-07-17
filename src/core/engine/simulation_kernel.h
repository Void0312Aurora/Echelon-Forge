#pragma once

#include <flecs.h>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <random>
#include <string>
#include <map>
#include <vector>
#include "components/basic/common.h"
#include "components/combat/common/weapon_common.h"
#include "components/command/command_link.h"
#include "components/command/common/mission_command_control_state.h"
#include "components/command/mission_command.h"
#include "components/command/pilot_action.h"
#include "components/physics/instruments.h"
#include "components/tasking/leader_intent.h"
#include "components/tasking/pilot_report.h"
#include "components/tasking/task_order.h"
#include "components/systems/navigation.h"
#include "components/systems/sensor.h"
#include "components/systems/comm.h"
#include "components/basic/tags.h"
#include "core/engine/engagement_event_types.h"
#include "core/engine/simulation_kernel_missile_tuning.h"
#include "core/interfaces/unit_data.h"
#include "core/interfaces/observation.h"
#include "core/interfaces/environment_model.h"
#include "core/interfaces/weapon_release_service.h"

class IUnitFactory;
class IEffectsModel;
class ISensorModel;
class IAcousticModel;
class IControlModel;
class IGuidanceModel;
class IWeaponReleaseDamageBridge;
struct UnitDefinition;
class SimulationKernelEngagementEventStore;

struct ExactStepStageDescriptor {
    int order = 0;
    std::string name;
    std::string flecs_kind;
    std::string domain;
    std::string notes;
    bool gpu_migration_scope = false;
    bool manual_trace_supported = false;
};

struct ExactStepStageContractDescriptor {
    int order = 0;
    std::string name;
    std::string flecs_kind;
    std::string domain;
    bool gpu_migration_scope = false;
    bool manual_trace_supported = false;
    std::vector<std::string> reads;
    std::vector<std::string> writes;
    std::vector<std::string> trace_surfaces;
    std::vector<std::string> depends_on_stages;
    std::string contract_summary;
    std::string exact_dependency_notes;
};

class SimulationKernel {
  public:
    SimulationKernel();
    ~SimulationKernel();
    SimulationKernel(const SimulationKernel &) = delete;
    SimulationKernel &operator=(const SimulationKernel &) = delete;
    SimulationKernel(SimulationKernel &&) = delete;
    SimulationKernel &operator=(SimulationKernel &&) = delete;

    // Reset the simulation to initial state with a specific random seed
    void reset(unsigned int seed);

    // Advance the simulation by one fixed time step
    void step();
    std::vector<ExactStepStageDescriptor> exact_gpu_migration_stage_inventory() const;
    std::vector<ExactStepStageContractDescriptor>
    exact_gpu_migration_stage_contract_inventory() const;
    void begin_exact_stage_trace_frame();
    void end_exact_stage_trace_frame();
    bool run_exact_stage_trace_stage(const std::string &stage_name);
    bool run_exact_stage_direct(const std::string &stage_name);
    void step_exact_stage_traceable_pipeline();
    void restore_exact_replay_world_time(double world_time_s);

    // Spawn a basic unit (for testing/gym API)
    flecs::entity spawn_unit(Side side, const std::string &unit_name, double x, double y, double z,
                             double heading, double pitch, double roll, double vx, double vy,
                             double vz);

    // Get the Flecs world (for systems/bindings)
    flecs::world &get_world() { return ecs; }
    const flecs::world &get_world() const { return ecs; }

    double get_time_step() const { return time_step; }
    void set_time_step(double dt);

    // Configuration
    bool load_database(const std::string &path);
    void clear_zones();
    void add_zone(const std::string &name, double x, double y, double width, double height,
                  double heading, int surface_type);
    void set_wind(double speed_mps, double dir_from_deg, double shear_mps_per_km = 0.0);
    void set_terrain_type(const std::string &terrain_type);
    void set_maritime_state(double sea_state, double wave_heading_deg = 0.0,
                            double wave_period_s = 8.0);
    void clear_maritime_state();
    IEnvironmentModel::MaritimeState get_maritime_state() const;

    // Compatibility-only legacy command API retained while typed setup stays blocked.
    void set_unit_command(uint64_t entity_id, double heading_deg, double speed_mps,
                          double altitude_m);
    void set_unit_stick_command(uint64_t entity_id, double stick_roll, double stick_pitch,
                                double throttle, bool gear_down);
    void set_unit_action(uint64_t entity_id, double turn_rate_cmd, double accel_cmd,
                         double climb_rate_cmd, double fire_cmd, bool release_chaff = false,
                         bool release_flare = false, bool jettison_tanks = false);
    void set_command_link(uint64_t entity_id, double latency_s, double drop_prob);
    void set_action_space_config(uint64_t entity_id, double max_turn_rate_deg_s,
                                 double max_accel_mps2, double max_climb_rate_mps,
                                 double min_speed_mps, double max_speed_mps, double min_alt_m,
                                 double max_alt_m);
    void set_command_lag(uint64_t entity_id, double heading_tau_s, double speed_tau_s,
                         double altitude_tau_s);

    // [NEW] Digital Pilot Interface
    void set_pilot_action(uint64_t entity_id, const PilotAction &action);
    void set_mission_command(uint64_t entity_id, const MissionCommand &cmd);
    void set_task_order(uint64_t entity_id, const TaskOrder &order);
    void set_leader_intent(uint64_t entity_id, const LeaderIntent &intent);
    void set_pilot_report(uint64_t entity_id, const PilotReport &report);
    TaskOrder get_task_order(uint64_t entity_id) const;
    LeaderIntent get_leader_intent(uint64_t entity_id) const;
    MissionCommand get_mission_command(uint64_t entity_id) const;
    PilotReport get_pilot_report(uint64_t entity_id) const;

    // Observation Interface
    std::vector<double> get_unit_position(uint64_t entity_id);        // Returns [x, y, z]
    std::vector<UnitData> get_all_units();                            // Bulk observation
    AgentObservation get_agent_observation(uint64_t entity_id) const; // RL Observation
    std::vector<float> get_visual_observation(uint64_t entity_id);    // ARB Visual Observation
    std::vector<float> get_visual_observation_downsampled(uint64_t entity_id,
                                                          int factor); // ARB downsampled visual
    std::vector<Detection> get_detections(uint64_t entity_id);         // Sensor Output
    void set_contact_list(uint64_t entity_id, const std::vector<Detection> &detections);
    InstrumentState get_instrument_state(uint64_t entity_id); // Returns instrument state or default
    EGI get_egi_state(uint64_t entity_id);                    // Returns EGI state or default
    std::vector<double> get_unit_velocity(uint64_t entity_id); // Returns [vx, vy, vz]
    double get_unit_heading(uint64_t entity_id);               // Returns heading
    int get_unit_type(uint64_t entity_id);                     // Returns UnitType enum value or 0
    bool is_unit_active(uint64_t entity_id);                   // Returns whether entity exists
    std::vector<double> get_unit_health(uint64_t entity_id);   // Returns [current, max]
    std::vector<double>
    get_unit_damage_state(uint64_t entity_id); // [mission, mobility, sensor, survivability]
    std::vector<double> debug_get_aircraft_damage_state(
        uint64_t
            entity_id); // [structure, flight_control, hydraulic, hydraulic_pressure, roll_control,
                        // pitch_control, yaw_control, control_asymmetry, propulsion, fuel,
                        // avionics, crew, pilot, mission_crew, command_navigation, fire, fuel_leak,
                        // fuel_imbalance, flammable_fluid, ignition_source, fire_suppression,
                        // smoke_heat, engine_fire_zone, wing_fire_zone, fuselage_fire_zone,
                        // mission_fire_zone, structural_overstress, flutter_exposure,
                        // forced_landing, flight_control_kill, propulsion_kill, crew_kill]
    std::vector<double> debug_get_aircraft_vulnerability_evidence_state(
        uint64_t entity_id); // [present, synthetic, calibrated_evidence, pk_authority,
                             // deterministic_fuze_authority, evidence_dataset_valid]
    std::vector<double> debug_get_aircraft_vulnerability_authority_state(
        uint64_t entity_id); // [present, synthetic, calibrated_evidence, effect_scale_authority,
                             // component_failure_probability_authority, pk_authority,
                             // deterministic_fuze_authority, evidence_dataset_valid]
    std::vector<double> debug_get_naval_weapon_counts(
        uint64_t entity_id); // [mounts, total_ready_vls, total_ready_gun, total_ready_ciws]
    std::vector<double>
    get_unit_fuel(uint64_t entity_id); // Returns [internal, max_internal, external, max_external]
    std::vector<double> debug_get_naval_stores(
        uint64_t entity_id); // [fuel_cur, fuel_max, missile_cur, missile_max, dry_cur, dry_max]
    std::vector<double> debug_get_logistics_node(
        uint64_t entity_id); // [supply_radius, infinite, underway_enabled, min_sep, max_sep,
                             // max_rel_speed, fuel_rate, missile_rate, dry_rate]
    std::vector<double>
    debug_get_resupply_state(uint64_t entity_id); // [active, kind, partner_id, stage,
                                                  // time_remaining, is_refueling, is_rearming]
    std::vector<double> debug_get_data_link_state(
        uint64_t
            entity_id); // [report_budget, message_budget, reports_sent_last, messages_sent_last,
                        // reports_dropped_last, messages_dropped_last, reports_sent_total,
                        // messages_sent_total, reports_dropped_total, messages_dropped_total]
    std::vector<double> debug_get_ground_contact_state(
        uint64_t entity_id); // [on_ground, terrain_z, lifecycle, impact_h_speed, impact_sink_rate,
                             // impact_severity, gear_stress, gear_collapsed, on_runway]
    std::vector<CommPacket> get_unit_messages(uint64_t entity_id);
    void send_message_command(uint64_t entity_id, uint64_t recipient_id, int msg_type,
                              uint64_t msg_arg);
    void set_unit_ammo(uint64_t entity_id, int missiles_remaining, int max_missiles);
    void set_weapon_cooldown(uint64_t entity_id, double cooldown_s, double last_fire_time);
    std::uint64_t debug_get_embarked_helo(uint64_t entity_id) const;

    double debug_get_last_scan_time(uint64_t entity_id);
    int debug_get_contact_count(uint64_t entity_id);
    std::vector<double>
    debug_get_mass_state(uint64_t entity_id); // [mass_empty, mass_fuel, mass_stores, mass_total,
                                              // props_empty, props_total]

    // Weapon Interface: Fire missile
    flecs::entity fire_missile(uint64_t attacker_id, uint64_t target_id);
    bool fire_naval_weapon(uint64_t attacker_id, uint64_t target_id, int weapon_type_code);
    bool debug_apply_proximity_hit(uint64_t attacker_id, uint64_t target_id, double damage,
                                   double fuse_distance);
    bool debug_apply_local_proximity_hit(uint64_t attacker_id, uint64_t target_id,
                                         double local_forward_m, double local_right_m,
                                         double local_up_m, double damage, double fuse_distance);
    bool debug_apply_profiled_local_proximity_hit(uint64_t attacker_id, uint64_t target_id,
                                                  double local_forward_m, double local_right_m,
                                                  double local_up_m,
                                                  const WarheadProfile &warhead_profile);
    bool debug_apply_profiled_local_proximity_hit_with_velocity(
        uint64_t attacker_id, uint64_t target_id, double local_forward_m, double local_right_m,
        double local_up_m, const WarheadProfile &warhead_profile, double missile_vx_mps,
        double missile_vy_mps, double missile_vz_mps);
    bool debug_apply_profiled_local_proximity_hit_with_velocity_and_attitude(
        uint64_t attacker_id, uint64_t target_id, double local_forward_m, double local_right_m,
        double local_up_m, const WarheadProfile &warhead_profile, double missile_vx_mps,
        double missile_vy_mps, double missile_vz_mps, double detonation_heading_deg,
        double detonation_pitch_deg, double detonation_roll_deg);
    RecentEngagementEvents export_recent_engagement_events() const;

    // Unit factory override (for modular swaps)
    void set_unit_factory(std::unique_ptr<IUnitFactory> factory);
    void set_effects_model(std::unique_ptr<IEffectsModel> model);
    void set_sensor_model(std::unique_ptr<ISensorModel> model);
    void set_acoustic_model(std::unique_ptr<IAcousticModel> model);
    void set_control_model(std::unique_ptr<IControlModel> model);
    void set_guidance_model(std::unique_ptr<IGuidanceModel> model);
    void set_environment_model(std::unique_ptr<IEnvironmentModel> model);
    bool load_unit_definitions(const std::string &path, std::string *error = nullptr);
    void set_missile_tuning(const MissileTuning &tuning);
    const MissileTuning &get_missile_tuning() const { return missile_tuning_; }
    void shutdown();

  private:
    void ensure_active(const char *operation) const;
    void register_components_and_systems();

    flecs::world ecs;
    double time_step = 1.0 / 60.0; // 60 Hz by default

    // Deterministic RNG (using std::mt19937 for MVP as planned, better than rand())
    // In production we might use Xoshiro/PCG
    std::mt19937 rng;

    std::unique_ptr<IEnvironmentModel> environment_model_;
    std::unique_ptr<IUnitFactory> unit_factory_;
    std::unique_ptr<IEffectsModel> effects_model_;
    std::unique_ptr<ISensorModel> sensor_model_;
    std::unique_ptr<IAcousticModel> acoustic_model_;
    std::unique_ptr<IControlModel> control_model_;
    std::unique_ptr<IGuidanceModel> guidance_model_;
    MissileTuning missile_tuning_;
    std::unique_ptr<SimulationKernelEngagementEventStore> engagement_event_store_;
    std::unique_ptr<IWeaponReleaseDamageBridge> weapon_release_damage_bridge_;
    std::unique_ptr<IWeaponReleaseService> weapon_release_service_;
    bool exact_stage_trace_frame_active_ = false;
    bool shutdown_complete_ = false;
};
