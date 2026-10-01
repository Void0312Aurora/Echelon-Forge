#include "state_transfer_component_reflection.h"

#include "components/basic/common.h"
#include "components/basic/stable_identity.h"
#include "components/combat/common/weapon_common.h"
#include "components/combat/health.h"
#include "components/combat/scoring.h"
#include "components/combat/structural_failure.h"
#include "components/command/pilot_action.h"
#include "components/command/command_link.h"
#include "components/command/command_link_qos.h"
#include "components/command/common/mission_command_control_state.h"
#include "components/command/legacy_command.h"
#include "components/domains/air/combat/damage_air.h"
#include "components/domains/air/combat/weapon_air.h"
#include "components/domains/ground/combat/damage_ground.h"
#include "components/domains/ground/ground_capabilities.h"
#include "components/domains/ground/combat/weapon_ground.h"
#include "components/domains/air/platform/flight_dynamics_tuning.h"
#include "components/domains/naval/combat/weapon_naval.h"
#include "components/domains/naval/platform/embarked_air_ops.h"
#include "components/domains/naval/platform/ship_platform.h"
#include "components/domains/naval/platform/submarine_platform.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/physics/instruments.h"
#include "components/physics/performance.h"
#include "components/physics/control_law.h"
#include "components/physics/control_surface.h"
#include "components/systems/data_link.h"
#include "components/systems/comm.h"
#include "components/systems/ew.h"
#include "components/systems/logistics.h"
#include "components/systems/navigation.h"
#include "components/systems/sensor.h"
#include "components/systems/sonar.h"
#include "components/systems/track_management.h"
#include "components/tasking/leader_intent.h"
#include "components/tasking/pilot_report.h"
#include "components/tasking/task_order.h"

#include <flecs.h>

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace {

flecs::opaque<std::string> string_support(flecs::world &) {
    flecs::opaque<std::string> type;
    type.as_type(flecs::String);
    type.serialize([](const flecs::serializer *serializer, const std::string *value) {
        const char *text = value->c_str();
        return serializer->value(flecs::String, &text);
    });
    type.assign_string([](std::string *value, const char *text) { *value = text; });
    return type;
}

template <typename T> flecs::opaque<std::vector<T>, T> vector_support(flecs::world &ecs) {
    flecs::opaque<std::vector<T>, T> type;
    type.as_type(ecs.vector<T>());
    type.serialize([](const flecs::serializer *serializer, const std::vector<T> *values) {
        for (const auto &value : *values) {
            serializer->value(value);
        }
        return 0;
    });
    type.count([](const std::vector<T> *values) { return values->size(); });
    type.ensure_element([](std::vector<T> *values, std::size_t index) {
        if (values->size() <= index) {
            values->resize(index + 1);
        }
        return &(*values)[index];
    });
    type.resize([](std::vector<T> *values, std::size_t size) { values->resize(size); });
    return type;
}

template <typename Derived, typename Base> std::size_t base_offset() {
    Derived value{};
    const auto *derived = reinterpret_cast<const std::byte *>(&value);
    const auto *base = reinterpret_cast<const std::byte *>(static_cast<const Base *>(&value));
    return static_cast<std::size_t>(base - derived);
}

void register_standard_container_reflection(flecs::world &ecs) {
    ecs.component<std::string>().opaque(string_support);
    ecs.component<std::vector<double>>().opaque(vector_support<double>);
    ecs.component<std::vector<std::uint64_t>>().opaque(vector_support<std::uint64_t>);
}

void register_nested_value_reflection(flecs::world &ecs) {
    ecs.component<CommPacket>()
        .member<std::uint64_t>("sender_id")
        .member<std::uint64_t>("target_receiver_id")
        .member<std::int32_t>("type", 1, offsetof(CommPacket, type))
        .member<std::uint64_t>("entity_ref")
        .member<std::uint64_t>("track_ref")
        .member<double>("location_x")
        .member<double>("location_y")
        .member<double>("location_z")
        .member<double>("velocity_x")
        .member<double>("velocity_y")
        .member<double>("velocity_z")
        .member<double>("value")
        .member<double>("quality")
        .member<int>("status_code")
        .member<double>("timestamp");
    ecs.component<Detection>()
        .member<std::uint64_t>("target_id")
        .member<double>("range")
        .member<double>("bearing")
        .member<double>("elevation")
        .member<double>("closing_speed")
        .member<double>("signal_strength")
        .member<double>("snr_db")
        .member<double>("detection_prob_used")
        .member<double>("measured_vr")
        .member<int>("sensor_type")
        .member<bool>("local_sensor_hit")
        .member<double>("timestamp");
    ecs.component<EmitterDetection>()
        .member<std::uint64_t>("source_id")
        .member<double>("bearing_deg")
        .member<double>("signal_strength")
        .member<bool>("is_radar_lock")
        .member<bool>("is_missile_guidance");
    ecs.component<WeaponStation>()
        .member<int>("station_id")
        .member<bool>("is_occupied")
        .member<std::uint8_t>("weapon_type", 1, offsetof(WeaponStation, weapon_type))
        .member<double>("drag_index")
        .member<double>("weight_kg");
    ecs.component<SystemTrack>()
        .member<std::uint64_t>("track_id")
        .member<std::uint64_t>("entity_id")
        .member<double>("x")
        .member<double>("y")
        .member<double>("z")
        .member<double>("vx")
        .member<double>("vy")
        .member<double>("vz")
        .member<double>("range")
        .member<double>("azimuth")
        .member<double>("elevation")
        .member<std::int32_t>("main_source", 1, offsetof(SystemTrack, main_source))
        .member<std::int32_t>("local_source", 1, offsetof(SystemTrack, local_source))
        .member<std::int32_t>("classification", 1, offsetof(SystemTrack, classification))
        .member<std::int32_t>("status", 1, offsetof(SystemTrack, status))
        .member<double>("confidence")
        .member<double>("time_since_update")
        .member<double>("quality")
        .member<int>("confirm_hit_count")
        .member<int>("confirm_miss_count")
        .member<int>("confirm_window_progress")
        .member<double>("last_local_update_time")
        .member<double>("last_datalink_update_time")
        .member<double>("alpha_beta_alpha")
        .member<double>("alpha_beta_beta")
        .member<bool>("iff_known")
        .member<double>("classification_confidence");

    ecs.component<std::vector<CommPacket>>().opaque(vector_support<CommPacket>);

    ecs.component<std::vector<Detection>>().opaque(vector_support<Detection>);
    ecs.component<std::vector<EmitterDetection>>().opaque(vector_support<EmitterDetection>);
    ecs.component<std::vector<WeaponStation>>().opaque(vector_support<WeaponStation>);
    ecs.component<std::vector<SystemTrack>>().opaque(vector_support<SystemTrack>);
}

void register_ground_combat_reflection(flecs::world &ecs) {
    ecs.component<GroundInfantryPostureGeometry>()
        .member<double>("eye_height_m")
        .member<double>("center_of_mass_height_m");
    ecs.component<GroundInfantryCapability>()
        .member<GroundInfantryPostureGeometry>("stand")
        .member<GroundInfantryPostureGeometry>("crouch")
        .member<GroundInfantryPostureGeometry>("prone");
    ecs.component<GroundWeapon>()
        .member<std::int32_t>("weapon_type", 1, offsetof(GroundWeapon, weapon_type))
        .member<int>("ammunition")
        .member<int>("maximum_ammunition")
        .member<double>("damage_per_hit")
        .member<double>("engagement_range_m")
        .member<double>("hit_probability")
        .member<double>("cooldown_s")
        .member<double>("last_fire_time_s");
    ecs.component<std::vector<GroundWeapon>>().opaque(vector_support<GroundWeapon>);
    ecs.component<GroundWeaponState>()
        .member<std::vector<GroundWeapon>>("weapons")
        .member<std::int32_t>("selected_weapon_index");
    ecs.component<GroundPlatformDamageState>()
        .member<double>("mobility_integrity")
        .member<double>("track_integrity")
        .member<double>("fire_severity")
        .member<double>("ignition_source_severity")
        .member<double>("fire_suppression_integrity")
        .member<double>("structural_integrity")
        .member<double>("ongoing_structural_damage")
        .member<double>("casualty_fraction")
        .member<double>("command_integrity")
        .member<bool>("mobility_kill")
        .member<bool>("mission_kill")
        .member<bool>("element_destroyed");
}

void register_platform_state_reflection(flecs::world &ecs) {
    ecs.component<ShipPlatform>()
        .member<double>("displacement_light_kg")
        .member<double>("displacement_full_load_kg")
        .member<double>("length_m")
        .member<double>("beam_m")
        .member<double>("draft_m")
        .member<double>("height_above_waterline_m")
        .member<double>("max_speed_mps")
        .member<double>("economical_speed_mps")
        .member<double>("range_nm")
        .member<double>("range_speed_mps")
        .member<double>("max_accel_mps2")
        .member<double>("max_decel_mps2")
        .member<double>("max_turn_rate_deg_s")
        .member<double>("low_speed_turn_factor")
        .member<double>("steerageway_speed_mps")
        .member<double>("sea_state")
        .member<double>("wave_heading_deg")
        .member<double>("wave_period_s")
        .member<double>("max_roll_deg_sea_state_6")
        .member<double>("max_pitch_deg_sea_state_6")
        .member<double>("added_resistance_fraction_sea_state_6")
        .member<int>("crew");
    ecs.component<SubmarinePlatform>()
        .member<double>("submerged_displacement_kg")
        .member<double>("length_m")
        .member<double>("beam_m")
        .member<double>("draft_m")
        .member<double>("max_speed_submerged_mps")
        .member<double>("quiet_speed_mps")
        .member<double>("max_accel_mps2")
        .member<double>("max_decel_mps2")
        .member<double>("max_turn_rate_deg_s")
        .member<double>("max_depth_rate_mps")
        .member<double>("nominal_patrol_depth_m")
        .member<double>("max_operating_depth_m")
        .member<double>("acoustic_stealth_bias_db")
        .member<double>("self_noise_per_speed_db")
        .member<int>("crew");
    ecs.component<EmbarkedAirOps>()
        .member<std::string>("helo_unit_name")
        .member<std::uint64_t>("active_helo_entity_id")
        .member<double>("launch_altitude_m")
        .member<double>("launch_offset_forward_m")
        .member<double>("launch_offset_starboard_m")
        .member<double>("recover_range_m")
        .member<double>("relay_refresh_s")
        .member<bool>("enabled")
        .member<bool>("relay_oth_targeting")
        .member<bool>("helo_airborne");
    ecs.component<PlatformDamageState>()
        .member<double>("mission_capability")
        .member<double>("mobility_capability")
        .member<double>("sensor_capability")
        .member<double>("survivability_margin")
        .member<double>("flooding_severity")
        .member<double>("fire_severity")
        .member<double>("ongoing_hull_breach")
        .member<bool>("mission_kill")
        .member<bool>("mobility_kill")
        .member<bool>("sensor_kill")
        .member<std::int32_t>("loss_state", 1, offsetof(PlatformDamageState, loss_state));
    ecs.component<AircraftDamageState>()
        .member<double>("structural_integrity")
        .member<double>("flight_control_integrity")
        .member<double>("hydraulic_integrity")
        .member<double>("hydraulic_pressure_availability")
        .member<double>("roll_control_integrity")
        .member<double>("pitch_control_integrity")
        .member<double>("yaw_control_integrity")
        .member<double>("control_asymmetry")
        .member<double>("propulsion_integrity")
        .member<double>("fuel_system_integrity")
        .member<double>("avionics_integrity")
        .member<double>("crew_effectiveness")
        .member<double>("pilot_effectiveness")
        .member<double>("mission_crew_effectiveness")
        .member<double>("command_navigation_integrity")
        .member<double>("fire_severity")
        .member<double>("fuel_leak_severity")
        .member<double>("fuel_imbalance_severity")
        .member<double>("flammable_fluid_exposure")
        .member<double>("ignition_source_severity")
        .member<double>("fire_suppression_integrity")
        .member<double>("smoke_heat_exposure")
        .member<double>("engine_fire_zone_severity")
        .member<double>("wing_fire_zone_severity")
        .member<double>("fuselage_fire_zone_severity")
        .member<double>("mission_fire_zone_severity")
        .member<double>("structural_overstress")
        .member<double>("flutter_exposure")
        .member<bool>("forced_landing_required")
        .member<bool>("flight_control_kill")
        .member<bool>("propulsion_kill")
        .member<bool>("crew_kill");
}

void register_remaining_scalar_reflection(flecs::world &ecs) {
    ecs.component<PilotAction>()
        .member<double>("stick_pitch")
        .member<double>("stick_roll")
        .member<double>("rudder")
        .member<double>("throttle")
        .member<float>("gear_handle")
        .member<float>("flaps")
        .member<float>("speedbrake")
        .member<double>("brake")
        .member<bool>("brake_left")
        .member<bool>("brake_right")
        .member<bool>("radar_active")
        .member<double>("radar_scan_az")
        .member<double>("radar_scan_el")
        .member<bool>("tms_up")
        .member<bool>("master_arm")
        .member<bool>("fire_weapon")
        .member<bool>("fire_gun")
        .member<int>("weapon_select_id")
        .member<bool>("jettison_emergency")
        .member<bool>("program_chaff")
        .member<bool>("program_flare")
        .member<bool>("active");
    ecs.component<EngineTuning>()
        .member<bool>("enabled")
        .member<double>("mil_thrust_n")
        .member<double>("ab_thrust_n")
        .member<double>("throttle_ab_threshold")
        .member<double>("throttle_idle_bias")
        .member<double>("tau_spool_up_s")
        .member<double>("tau_spool_down_s")
        .member<double>("tau_ab_light_s")
        .member<double>("tau_ab_extinguish_s")
        .member<double>("ram_rise_gain")
        .member<double>("ram_rise_mach_cap")
        .member<double>("ram_decay_start_mach")
        .member<double>("ram_decay_gain")
        .member<double>("thrust_sigma_exponent")
        .member<double>("thrust_theta_exponent")
        .member<double>("tsfc_mil_kg_per_nh")
        .member<double>("tsfc_ab_kg_per_nh");
    ecs.component<ControlLawState>()
        .member<double>("stick_roll_filt")
        .member<double>("stick_pitch_filt")
        .member<double>("stick_yaw_filt")
        .member<double>("stick_yaw_cmd")
        .member<double>("dbg_g_cmd")
        .member<double>("dbg_measured_nz")
        .member<double>("dbg_q_cmd")
        .member<double>("dbg_q_cmd_final")
        .member<double>("dbg_elevator_cmd")
        .member<double>("dbg_g_branch_active");
    ecs.component<ControlSurfaceState>()
        .member<double>("elevator_cmd")
        .member<double>("aileron_cmd")
        .member<double>("rudder_cmd")
        .member<double>("elevator_pos")
        .member<double>("aileron_pos")
        .member<double>("rudder_pos");
    ecs.component<Munition>().member<int>("station_id").member<bool>("is_fired");
    ecs.component<PilotWeaponReleaseState>()
        .member<bool>("fire_weapon_was_down")
        .member<bool>("release_consumed");
    ecs.component<Lifetime>().member<double>("max_age").member<double>("current_age");
    ecs.component<NavalStores>()
        .member<double>("fuel_units_current")
        .member<double>("fuel_units_max")
        .member<double>("missile_units_current")
        .member<double>("missile_units_max")
        .member<double>("dry_cargo_units_current")
        .member<double>("dry_cargo_units_max")
        .member<bool>("can_receive_underway")
        .member<bool>("can_provide_underway");
    ecs.component<ResupplyState>()
        .member<double>("time_remaining_s")
        .member<bool>("is_refueling")
        .member<bool>("is_rearming")
        .member<std::int32_t>("kind", 1, offsetof(ResupplyState, kind))
        .member<std::uint64_t>("partner_entity_id")
        .member<std::int32_t>("naval_stage", 1, offsetof(ResupplyState, naval_stage));
    ecs.component<StructuralBreakupState>()
        .member<std::uint8_t>("breakup_state", 1, offsetof(StructuralBreakupState, breakup_state))
        .member<std::uint32_t>("active_break_modes")
        .member<std::uint32_t>("active_structural_groups")
        .member<std::uint32_t>("detached_part_count")
        .member<bool>("airframe_breakup")
        .member<std::uint64_t>("last_breakup_event_id");
    ecs.component<NavalWeaponMountDefinition>()
        .member<std::string>("mount_id")
        .member<std::int32_t>("weapon_type", 1, offsetof(NavalWeaponMountDefinition, weapon_type))
        .member<int>("ready_count")
        .member<int>("max_ready_count")
        .member<int>("ammo_per_shot")
        .member<double>("cooldown_s")
        .member<double>("last_fire_time")
        .member<double>("engagement_range_m")
        .member<double>("projectile_speed_mps")
        .member<double>("hit_probability")
        .member<double>("damage_per_hit")
        .member<bool>("consumes_ready_count")
        .member<bool>("can_intercept_missiles")
        .member<std::string>("fire_control_channel")
        .member<std::string>("target_domain")
        .member<std::string>("provenance_note");
    ecs.component<std::vector<NavalWeaponMountDefinition>>().opaque(
        vector_support<NavalWeaponMountDefinition>);
    ecs.component<NavalWeaponSystem>().member<std::vector<NavalWeaponMountDefinition>>("mounts");
}

void register_tasking_reflection(flecs::world &ecs) {
    ecs.component<TaskOrderCore>()
        .member<std::uint64_t>("task_id")
        .member<int>("service_profile", 1, offsetof(TaskOrderCore, service_profile))
        .member<int>("task_family", 1, offsetof(TaskOrderCore, task_family))
        .member<int>("tactical_unit_type", 1, offsetof(TaskOrderCore, tactical_unit_type))
        .member<int>("priority")
        .member<std::uint64_t>("issuer_id")
        .member<std::uint64_t>("assignee_id")
        .member<int>("command_relationship", 1, offsetof(TaskOrderCore, command_relationship))
        .member<int>("authority_scope", 1, offsetof(TaskOrderCore, authority_scope))
        .member<std::uint64_t>("parent_node_id")
        .member<std::uint64_t>("task_group_id")
        .member<std::uint64_t>("supported_node_id")
        .member<std::uint64_t>("supporting_node_id")
        .member<int>("role_code")
        .member<int>("coordination_mode", 1, offsetof(TaskOrderCore, coordination_mode))
        .member<int>("relative_slot_code")
        .member<int>("assignee_kind", 1, offsetof(TaskOrderCore, assignee_kind))
        .member<std::uint64_t>("recovery_site_id")
        .member<bool>("active")
        .member<double>("issue_time_s");
    ecs.component<TaskOrderAir>()
        .member<int>("task_type", 1, offsetof(TaskOrderAir, task_type))
        .member<std::uint64_t>("element_id")
        .member<std::uint64_t>("package_id")
        .member<std::uint64_t>("lead_aircraft_id")
        .member<double>("anchor_x_m")
        .member<double>("anchor_y_m")
        .member<double>("anchor_z_m")
        .member<int>("station_type", 1, offsetof(TaskOrderAir, station_type))
        .member<double>("station_radius_m")
        .member<double>("station_leg_length_m")
        .member<double>("station_heading_deg")
        .member<double>("altitude_block_min_m")
        .member<double>("altitude_block_max_m")
        .member<double>("target_altitude_m")
        .member<double>("speed_min_mps")
        .member<double>("speed_max_mps")
        .member<double>("target_speed_mps")
        .member<int>("entry_condition_code")
        .member<int>("exit_condition_code")
        .member<double>("on_station_time_s")
        .member<double>("fuel_bingo_override_kg")
        .member<std::uint64_t>("recovery_base_id")
        .member<std::uint64_t>("recovery_runway_id")
        .member<int>("recovery_approach_type", 1, offsetof(TaskOrderAir, recovery_approach_type))
        .member<int>("takeoff_procedure_id", 1, offsetof(TaskOrderAir, takeoff_procedure_id))
        .member<int>("takeoff_clearance_id", 1, offsetof(TaskOrderAir, takeoff_clearance_id))
        .member<double>("takeoff_interval_s")
        .member<int>("runway_slot_id", 1, offsetof(TaskOrderAir, runway_slot_id))
        .member<std::uint64_t>("formation_template_id")
        .member<std::uint64_t>("formation_contract_id")
        .member<int>("formation_role_id", 1, offsetof(TaskOrderAir, formation_role_id))
        .member<int>("wingman_slot_id", 1, offsetof(TaskOrderAir, wingman_slot_id))
        .member<int>("join_policy_id")
        .member<int>("rejoin_policy_id")
        .member<int>("mutual_support_mode")
        .member<std::uint64_t>("support_sector_id");
    ecs.component<TaskOrderNaval>()
        .member<int>("warfare_role_code")
        .member<std::uint64_t>("officer_in_tactical_command")
        .member<int>("naval_station_type", 1, offsetof(TaskOrderNaval, naval_station_type));
    ecs.component<TaskOrderGround>()
        .member<int>("ground_task_mode", 1, offsetof(TaskOrderGround, ground_task_mode))
        .member<std::uint64_t>("objective_area_id")
        .member<std::uint64_t>("objective_node_id")
        .member<std::uint64_t>("ground_commander_id")
        .member<double>("tactical_cadence_hz");
    ecs.component<TaskOrder>()
        .member<TaskOrderCore>("core", 1, base_offset<TaskOrder, TaskOrderCore>())
        .member<TaskOrderAir>("air", 1, base_offset<TaskOrder, TaskOrderAir>())
        .member<TaskOrderNaval>("naval", 1, base_offset<TaskOrder, TaskOrderNaval>())
        .member<TaskOrderGround>("ground", 1, base_offset<TaskOrder, TaskOrderGround>());

    ecs.component<LeaderIntentCore>()
        .member<int>("service_profile", 1, offsetof(LeaderIntentCore, service_profile))
        .member<int>("task_family", 1, offsetof(LeaderIntentCore, task_family))
        .member<int>("tactical_unit_type", 1, offsetof(LeaderIntentCore, tactical_unit_type))
        .member<std::uint64_t>("tactical_unit_id")
        .member<std::uint64_t>("task_group_id")
        .member<int>("role_code")
        .member<int>("coordination_mode", 1, offsetof(LeaderIntentCore, coordination_mode))
        .member<int>("relative_slot_code")
        .member<std::uint64_t>("recovery_site_id")
        .member<int>("command_code")
        .member<double>("cmd_heading_deg")
        .member<double>("cmd_altitude_m")
        .member<double>("cmd_speed_mps")
        .member<int>("roe_state")
        .member<std::uint64_t>("engagement_authority_holder_id")
        .member<std::uint64_t>("engagement_authority_grantor_id")
        .member<std::uint64_t>("assigned_target_id")
        .member<int>("threat_state")
        .member<std::uint64_t>("assigned_target_track_id")
        .member<std::uint64_t>("assigned_target_source_id")
        .member<double>("assigned_target_snapshot_time_s")
        .member<bool>("authorization_to_fire")
        .member<bool>("active");
    ecs.component<LeaderIntentAir>()
        .member<int>("phase_id", 1, offsetof(LeaderIntentAir, phase_id))
        .member<int>("element_phase_id")
        .member<std::uint64_t>("route_ref_id")
        .member<std::uint64_t>("recovery_base_id")
        .member<std::uint64_t>("recovery_runway_id")
        .member<int>("recovery_approach_type", 1, offsetof(LeaderIntentAir, recovery_approach_type))
        .member<int>("takeoff_procedure_id", 1, offsetof(LeaderIntentAir, takeoff_procedure_id))
        .member<int>("takeoff_clearance_id", 1, offsetof(LeaderIntentAir, takeoff_clearance_id))
        .member<double>("takeoff_interval_s")
        .member<int>("runway_slot_id", 1, offsetof(LeaderIntentAir, runway_slot_id))
        .member<int>("formation_id")
        .member<double>("form_offset_x")
        .member<double>("form_offset_y")
        .member<double>("form_offset_z")
        .member<int>("formation_mode_id", 1, offsetof(LeaderIntentAir, formation_mode_id))
        .member<bool>("join_required_flag")
        .member<bool>("rejoin_required_flag")
        .member<bool>("split_flag")
        .member<double>("support_anchor_x_m")
        .member<double>("support_anchor_y_m")
        .member<double>("support_slot_offset_x_m")
        .member<double>("support_slot_offset_y_m")
        .member<int>("wingman_command_mode", 1, offsetof(LeaderIntentAir, wingman_command_mode))
        .member<bool>("approach_armed")
        .member<bool>("commit_to_land")
        .member<bool>("abort_flag");
    ecs.component<LeaderIntentNaval>()
        .member<int>("warfare_role_code")
        .member<std::uint64_t>("officer_in_tactical_command");
    ecs.component<LeaderIntentGround>()
        .member<int>("ground_status_phase", 1, offsetof(LeaderIntentGround, ground_status_phase))
        .member<int>("ground_task_mode", 1, offsetof(LeaderIntentGround, ground_task_mode))
        .member<std::uint64_t>("objective_area_id")
        .member<std::uint64_t>("objective_node_id")
        .member<std::uint64_t>("ground_commander_id")
        .member<double>("tactical_cadence_hz");
    ecs.component<LeaderIntent>()
        .member<LeaderIntentCore>("core", 1, base_offset<LeaderIntent, LeaderIntentCore>())
        .member<LeaderIntentAir>("air", 1, base_offset<LeaderIntent, LeaderIntentAir>())
        .member<LeaderIntentNaval>("naval", 1, base_offset<LeaderIntent, LeaderIntentNaval>())
        .member<LeaderIntentGround>("ground", 1, base_offset<LeaderIntent, LeaderIntentGround>());

    ecs.component<PilotReportCore>()
        .member<int>("report_type", 1, offsetof(PilotReportCore, report_type))
        .member<std::uint64_t>("sender_id")
        .member<std::uint64_t>("task_id")
        .member<int>("service_profile", 1, offsetof(PilotReportCore, service_profile))
        .member<int>("task_family", 1, offsetof(PilotReportCore, task_family))
        .member<int>("tactical_unit_type", 1, offsetof(PilotReportCore, tactical_unit_type))
        .member<std::uint64_t>("tactical_unit_id")
        .member<std::uint64_t>("task_group_id")
        .member<int>("role_code")
        .member<int>("coordination_mode", 1, offsetof(PilotReportCore, coordination_mode))
        .member<double>("timestamp_s")
        .member<double>("status_value")
        .member<std::uint64_t>("entity_ref")
        .member<double>("location_x_m")
        .member<double>("location_y_m")
        .member<double>("location_z_m")
        .member<bool>("active");
    ecs.component<PilotReportAir>()
        .member<std::uint64_t>("element_id")
        .member<int>("phase_id")
        .member<int>("formation_role_id")
        .member<double>("formation_error_m")
        .member<double>("bearing_error_deg")
        .member<double>("closure_mps")
        .member<double>("separation_m");
    ecs.component<PilotReportNaval>()
        .member<int>("warfare_role_code")
        .member<std::uint64_t>("officer_in_tactical_command");
    ecs.component<PilotReportGround>()
        .member<int>("ground_status_phase", 1, offsetof(PilotReportGround, ground_status_phase))
        .member<int>("ground_task_mode", 1, offsetof(PilotReportGround, ground_task_mode))
        .member<std::uint64_t>("objective_area_id")
        .member<std::uint64_t>("objective_node_id")
        .member<std::uint64_t>("ground_commander_id")
        .member<double>("tactical_cadence_hz")
        .member<double>("readiness_ratio");
    ecs.component<PilotReport>()
        .member<PilotReportCore>("core", 1, base_offset<PilotReport, PilotReportCore>())
        .member<PilotReportAir>("air", 1, base_offset<PilotReport, PilotReportAir>())
        .member<PilotReportNaval>("naval", 1, base_offset<PilotReport, PilotReportNaval>())
        .member<PilotReportGround>("ground", 1, base_offset<PilotReport, PilotReportGround>());
}

void register_basic_reflection(flecs::world &ecs) {
    ecs.component<Transform>()
        .member<double>("x")
        .member<double>("y")
        .member<double>("z")
        .member<double>("heading")
        .member<double>("pitch")
        .member<double>("roll");
    ecs.component<Velocity>().member<double>("vx").member<double>("vy").member<double>("vz");
    static_assert(sizeof(Side) == sizeof(std::uint8_t));
    ecs.component<Alliance>().member<std::uint8_t>("side", 1, offsetof(Alliance, side));
    static_assert(sizeof(UnitType) == sizeof(std::uint8_t));
    ecs.component<KeyEntity>().member<std::uint8_t>("type", 1, offsetof(KeyEntity, type));
    ecs.component<StableEntitySerial>().member<std::uint64_t>("value");
    ecs.component<StableIdentityState>()
        .member<std::uint64_t>("next_serial")
        .member<std::uint64_t>("episode_seed");
}

void register_command_scalar_reflection(flecs::world &ecs) {
    ecs.component<ActionCommand>()
        .member<double>("turn_rate_cmd")
        .member<double>("accel_cmd")
        .member<double>("climb_rate_cmd")
        .member<double>("fire_cmd")
        .member<bool>("release_chaff")
        .member<bool>("release_flare")
        .member<bool>("jettison_tanks")
        .member<bool>("send_msg")
        .member<int>("msg_type")
        .member<std::uint64_t>("msg_recipient")
        .member<std::uint64_t>("msg_arg")
        .member<bool>("active");
    ecs.component<ActionSpaceConfig>()
        .member<double>("max_turn_rate_deg_s")
        .member<double>("max_accel_mps2")
        .member<double>("max_climb_rate_mps")
        .member<double>("min_speed_mps")
        .member<double>("max_speed_mps")
        .member<double>("min_alt_m")
        .member<double>("max_alt_m");
    ecs.component<MovementCommand>()
        .member<double>("target_heading")
        .member<double>("target_speed")
        .member<double>("target_altitude")
        .member<bool>("use_stick_control")
        .member<double>("stick_roll")
        .member<double>("stick_pitch")
        .member<double>("throttle_cmd")
        .member<bool>("gear_handle")
        .member<bool>("active");
    ecs.component<CommandLag>()
        .member<double>("heading_tau_s")
        .member<double>("speed_tau_s")
        .member<double>("altitude_tau_s");
    ecs.component<LaggedCommand>()
        .member<double>("target_heading")
        .member<double>("target_speed")
        .member<double>("target_altitude")
        .member<bool>("active");
    ecs.component<CommandLink>().member<double>("latency_s").member<double>("drop_prob");

    ecs.component<MissionCommandTypedAirControlState>()
        .member<double>("throttle_command")
        .member<double>("brake_amount")
        .member<double>("nose_wheel_yaw_command")
        .member<float>("flaps_pos")
        .member<float>("speedbrake_pos")
        .member<bool>("throttle_active")
        .member<bool>("throttle_idle")
        .member<bool>("ground_active")
        .member<bool>("instrument_active")
        .member<bool>("nose_wheel_steering_active")
        .member<bool>("manual_input_active")
        .member<bool>("action_semantics_active")
        .member<bool>("master_arm")
        .member<int>("weapon_selected");
    ecs.component<MissionCommandControlState>()
        .member<double>("target_heading_deg")
        .member<double>("target_altitude_m")
        .member<double>("target_speed_mps")
        .member<double>("lagged_heading_deg")
        .member<double>("lagged_altitude_m")
        .member<double>("lagged_speed_mps")
        .member<bool>("active")
        .member<bool>("lagged_active")
        .member<MissionCommandTypedAirControlState>("typed_air_control");

    ecs.component<MissionCommandCore>()
        .member<double>("cmd_heading_deg")
        .member<double>("cmd_altitude_m")
        .member<double>("cmd_speed_mps")
        .member<int>("command_code")
        .member<std::uint64_t>("route_ref_id")
        .member<int>("roe_state")
        .member<std::uint64_t>("engagement_authority_holder_id")
        .member<std::uint64_t>("engagement_authority_grantor_id")
        .member<std::uint64_t>("assigned_target_id")
        .member<int>("threat_state")
        .member<std::uint64_t>("assigned_target_track_id")
        .member<std::uint64_t>("assigned_target_source_id")
        .member<double>("assigned_target_snapshot_time_s")
        .member<bool>("authorization_to_fire")
        .member<bool>("active");
    ecs.component<MissionCommandAir>()
        .member<std::uint64_t>("recovery_base_id")
        .member<std::uint64_t>("recovery_runway_id")
        .member<std::int32_t>("recovery_approach_type", 1,
                              offsetof(MissionCommandAir, recovery_approach_type))
        .member<std::int32_t>("takeoff_procedure_id", 1,
                              offsetof(MissionCommandAir, takeoff_procedure_id))
        .member<std::int32_t>("takeoff_clearance_id", 1,
                              offsetof(MissionCommandAir, takeoff_clearance_id))
        .member<double>("takeoff_interval_s")
        .member<std::int32_t>("runway_slot_id", 1, offsetof(MissionCommandAir, runway_slot_id))
        .member<int>("formation_id")
        .member<double>("form_offset_x")
        .member<double>("form_offset_y")
        .member<double>("form_offset_z");
    ecs.component<MissionCommandNaval>()
        .member<std::uint64_t>("reference_entity_id")
        .member<double>("station_radius_m")
        .member<double>("station_bearing_deg")
        .member<std::uint64_t>("embarked_helo_entity_id")
        .member<bool>("launch_helo")
        .member<bool>("recover_helo")
        .member<bool>("relay_oth_targeting");
    ecs.component<MissionCommandGround>()
        .member<std::int32_t>("ground_task_mode", 1,
                              offsetof(MissionCommandGround, ground_task_mode))
        .member<std::uint64_t>("objective_area_id")
        .member<std::uint64_t>("objective_node_id")
        .member<std::uint64_t>("ground_commander_id")
        .member<double>("tactical_cadence_hz");
    ecs.component<MissionCommand>()
        .member<MissionCommandCore>("core", 1, base_offset<MissionCommand, MissionCommandCore>())
        .member<MissionCommandAir>("air", 1, base_offset<MissionCommand, MissionCommandAir>())
        .member<MissionCommandNaval>("naval", 1, base_offset<MissionCommand, MissionCommandNaval>())
        .member<MissionCommandGround>("ground", 1,
                                      base_offset<MissionCommand, MissionCommandGround>());

    ecs.component<PendingMissionControlCommand>().member<MissionCommandControlState>(
        "control_state");
    ecs.component<PendingMovementCommand>()
        .member<PendingMissionControlCommand>("typed_command")
        .member<MovementCommand>("command")
        .member<double>("deliver_time")
        .member<bool>("active");
    ecs.component<PendingActionCommand>()
        .member<MissionCommandTypedAirControlState>("typed_air_control_bridge")
        .member<ActionCommand>("command")
        .member<double>("deliver_time")
        .member<bool>("active");
    ecs.component<PendingMissionCommand>()
        .member<MissionCommand>("command")
        .member<double>("deliver_time")
        .member<bool>("active");
    ecs.component<MissionCommandQueueEntry>().member<MissionCommand>("command").member<double>(
        "deliver_time");
    ecs.component<MissionCommandPendingQueue>()
        .member<MissionCommandQueueEntry>("entries", kMissionCommandPendingQueueCapacity,
                                          offsetof(MissionCommandPendingQueue, entries))
        .member<std::uint64_t>("size", 1, offsetof(MissionCommandPendingQueue, size));
}

void register_physics_scalar_reflection(flecs::world &ecs) {
    ecs.component<ForceAccumulator>()
        .member<double>("fx")
        .member<double>("fy")
        .member<double>("fz")
        .member<double>("torque_roll")
        .member<double>("torque_pitch")
        .member<double>("torque_yaw");
    ecs.component<Inertia>().member<double>("ixx").member<double>("iyy").member<double>("izz");
    ecs.component<AngularVelocity>().member<double>("p").member<double>("q").member<double>("r");
    ecs.component<AeroState>()
        .member<double>("dynamic_pressure")
        .member<double>("angle_of_attack")
        .member<double>("angle_of_attack_rate_dps")
        .member<double>("previous_angle_of_attack")
        .member<double>("sideslip_angle")
        .member<double>("mach_number")
        .member<double>("lift_coefficient")
        .member<double>("drag_coefficient")
        .member<double>("stall_progress");
    ecs.component<Mass>()
        .member<double>("empty_mass_kg")
        .member<double>("fuel_mass_kg")
        .member<double>("stores_mass_kg")
        .member<double>("fuel_leak_rate_kg_s");
    ecs.component<Propulsion>()
        .member<double>("mil_thrust_n")
        .member<double>("ab_thrust_n")
        .member<double>("current_thrust_n")
        .member<bool>("afterburner_active")
        .member<double>("throttle_command")
        .member<double>("throttle_state")
        .member<double>("dry_thrust_command_n")
        .member<double>("dry_thrust_state_n")
        .member<double>("ab_command")
        .member<double>("ab_state")
        .member<double>("current_tsfc");
    ecs.component<GearState>()
        .member<bool>("gear_down")
        .member<double>("stress")
        .member<bool>("collapsed")
        .member<double>("stress_rate")
        .member<bool>("on_runway");
    ecs.component<FlightModel>()
        .member<double>("max_speed")
        .member<double>("min_speed")
        .member<double>("max_turn_rate")
        .member<double>("max_accel")
        .member<double>("max_climb_rate")
        .member<double>("max_g")
        .member<double>("min_g")
        .member<double>("takeoff_speed")
        .member<double>("landing_speed")
        .member<double>("taxi_turn_rate");
    ecs.component<LandingGear>()
        .member<bool>("can_use_unpaved")
        .member<double>("rolling_friction_coeff")
        .member<double>("max_load_factor")
        .member<double>("contact_height_m")
        .member<double>("extension_state")
        .member<bool>("is_jammed")
        .member<double>("transit_time_s");
    ecs.component<StallState>()
        .member<double>("stall_progress")
        .member<double>("time_in_stall_s")
        .member<bool>("is_stalled")
        .member<bool>("pitch_break_active");
}

void register_resource_scalar_reflection(flecs::world &ecs) {
    ecs.component<Health>()
        .member<double>("current_hp")
        .member<double>("max_hp")
        .member<bool>("mission_kill")
        .member<bool>("mobility_kill")
        .member<bool>("sensor_kill");
    ecs.component<Score>()
        .member<double>("total_reward")
        .member<int>("missiles_fired")
        .member<int>("hits_landed")
        .member<int>("kills_confirmed");
    ecs.component<Ammo>().member<int>("missiles_remaining").member<int>("max_missiles");
    ecs.component<WeaponCooldown>().member<double>("cooldown_s").member<double>("last_fire_time");
    ecs.component<Jammer>()
        .member<bool>("is_active")
        .member<double>("power_watts")
        .member<double>("bandwidth_mhz")
        .member<std::int32_t>("type", 1, offsetof(Jammer, type))
        .member<double>("effective_angle");
    ecs.component<Countermeasures>()
        .member<int>("chaff_count")
        .member<int>("flare_count")
        .member<double>("release_interval")
        .member<double>("last_release_time")
        .member<bool>("auto_mode");
    ecs.component<RCSProfile>()
        .member<double>("frontal_rcs")
        .member<double>("side_rcs")
        .member<double>("rear_rcs");
    ecs.component<FuelSystem>()
        .member<double>("internal_fuel_kg")
        .member<double>("max_internal_fuel_kg")
        .member<double>("external_fuel_kg")
        .member<double>("max_external_fuel_kg")
        .member<double>("current_flow_rate")
        .member<bool>("afterburner_active")
        .member<double>("mil_power_flow_rate")
        .member<double>("ab_flow_rate_multiplier");
    ecs.component<MassProperties>()
        .member<double>("empty_mass_kg")
        .member<double>("current_total_mass_kg")
        .member<double>("base_drag_index")
        .member<double>("current_drag_index")
        .member<double>("reference_area_m2")
        .member<double>("wing_span_m")
        .member<double>("chord_m");
    ecs.component<GroundState>()
        .member<bool>("on_ground")
        .member<double>("terrain_elevation")
        .member<double>("surface_friction")
        .member<std::int32_t>("lifecycle", 1, offsetof(GroundState, lifecycle))
        .member<double>("impact_horizontal_speed_mps")
        .member<double>("impact_sink_rate_mps")
        .member<double>("impact_severity");
    ecs.component<DataLink>()
        .member<bool>("active")
        .member<int>("network_id")
        .member<std::int32_t>("type", 1, offsetof(DataLink, type))
        .member<double>("max_range_km")
        .member<int>("max_reports_per_update")
        .member<int>("max_messages_per_update")
        .member<int>("reports_sent_last_update")
        .member<int>("messages_sent_last_update")
        .member<int>("reports_dropped_last_update")
        .member<int>("messages_dropped_last_update")
        .member<std::uint64_t>("reports_sent_total")
        .member<std::uint64_t>("messages_sent_total")
        .member<std::uint64_t>("reports_dropped_total")
        .member<std::uint64_t>("messages_dropped_total");
}

void register_sensor_and_queue_reflection(flecs::world &ecs) {
    ecs.component<LogisticsNode>()
        .member<double>("supply_radius_m")
        .member<bool>("infinite_supply")
        .member<bool>("underway_replenishment_enabled")
        .member<double>("underway_min_separation_m")
        .member<double>("underway_max_separation_m")
        .member<double>("underway_max_relative_speed_mps")
        .member<double>("transfer_rate_fuel_units_per_s")
        .member<double>("transfer_rate_missile_units_per_s")
        .member<double>("transfer_rate_dry_cargo_units_per_s");
    ecs.component<Sonar>()
        .member<double>("max_range_m")
        .member<double>("scan_period_s")
        .member<double>("last_scan_time_s")
        .member<double>("detection_threshold_db")
        .member<double>("track_memory_s")
        .member<double>("bearing_noise_std_deg")
        .member<double>("range_noise_std_m")
        .member<double>("directivity_gain_db")
        .member<double>("self_noise_per_speed_db")
        .member<double>("ambient_noise_db")
        .member<double>("source_level_reference_db")
        .member<double>("source_level_speed_factor_db")
        .member<double>("transmission_loss_alpha_db_per_km")
        .member<double>("layer_break_penalty_db")
        .member<double>("convergence_zone_bonus_m")
        .member<double>("baffle_exclusion_deg")
        .member<double>("ownship_quieting_speed_mps")
        .member<double>("active_ping_source_level_db")
        .member<int>("confirm_hits_m")
        .member<int>("confirm_window_n")
        .member<int>("mode")
        .member<bool>("passive_only")
        .member<bool>("bearing_only");
    ecs.component<SonarMount>().member<Sonar>("sonar").member<std::string>("label");
    ecs.component<std::vector<SonarMount>>().opaque(vector_support<SonarMount>);
    ecs.component<MountedSonars>().member<std::vector<SonarMount>>("mounts");
    ecs.component<CommQueue>().member<std::vector<CommPacket>>("inbox");
    ecs.component<ContactList>().member<std::vector<Detection>>("contacts");
    ecs.component<RWR>()
        .member<double>("sensitivity_dbm")
        .member<std::vector<std::uint64_t>>("detected_radar_ids")
        .member<std::vector<std::uint64_t>>("locking_radar_ids")
        .member<bool>("is_missile_launch");
    ecs.component<ESMReceiver>()
        .member<double>("sensitivity_dbm")
        .member<double>("max_detection_range_m")
        .member<bool>("classify_emitters")
        .member<std::vector<EmitterDetection>>("detections");
    ecs.component<Loadout>().member<std::vector<WeaponStation>>("stations");
    ecs.component<TrackDatabase>()
        .member<std::vector<SystemTrack>>("tracks")
        .member<std::vector<SystemTrack>>("tentative_tracks")
        .member<double>("fusion_radius_m")
        .member<int>("max_tracks");

    ecs.component<Sensor>()
        .member<double>("max_range")
        .member<double>("fov_deg")
        .member<double>("scan_period")
        .member<double>("last_scan_time")
        .member<double>("detection_prob")
        .member<double>("range_power")
        .member<double>("bearing_noise_std")
        .member<double>("range_noise_std")
        .member<double>("track_memory_s")
        .member<double>("aspect_influence")
        .member<double>("doppler_notch_width")
        .member<double>("reference_snr_db")
        .member<double>("reference_range_m")
        .member<double>("reference_rcs_m2")
        .member<double>("pfa")
        .member<int>("confirm_hits_m")
        .member<int>("confirm_window_n")
        .member<double>("velocity_noise_std")
        .member<double>("alpha_beta_alpha")
        .member<double>("alpha_beta_beta")
        .member<double>("antenna_height_m")
        .member<double>("target_height_bias_m")
        .member<double>("sea_clutter_sensitivity")
        .member<double>("sea_state_loss_per_level")
        .member<double>("ducting_gain_factor")
        .member<double>("ducting_max_bonus_m")
        .member<double>("bearing_only_min_range_m")
        .member<int>("environment_domain")
        .member<bool>("enforce_radar_horizon")
        .member<bool>("enable_ducting")
        .member<bool>("sea_clutter_enabled")
        .member<bool>("bearing_only")
        .member<int>("type");
    ecs.component<SensorMount>().member<Sensor>("sensor").member<std::string>("label");
    ecs.component<std::vector<SensorMount>>().opaque(vector_support<SensorMount>);
    ecs.component<MountedSensors>().member<std::vector<SensorMount>>("mounts");

    ecs.component<EGI>()
        .member<double>("lat_deg")
        .member<double>("lon_deg")
        .member<double>("alt_baro_m")
        .member<double>("alt_radar_m")
        .member<double>("vn_mps")
        .member<double>("ve_mps")
        .member<double>("vd_mps")
        .member<double>("heading_deg")
        .member<double>("pitch_deg")
        .member<double>("roll_deg")
        .member<double>("wind_speed_mps")
        .member<double>("wind_dir_deg")
        .member<double>("drift_lat_m")
        .member<double>("drift_lon_m")
        .member<double>("drift_alt_m")
        .member<double>("position_uncertainty_m")
        .member<double>("time_since_last_gps_fix")
        .member<double>("ins_drift_rate_mps")
        .member<bool>("gps_available");
}

void register_instrument_reflection(flecs::world &ecs) {
    ecs.component<InstrumentState>()
        .member<double>("alt_baro_m")
        .member<double>("alt_radar_m")
        .member<double>("ias_mps")
        .member<double>("mach")
        .member<double>("vvi_mps")
        .member<double>("pitch_deg")
        .member<double>("roll_deg")
        .member<double>("heading_deg")
        .member<double>("aoa_deg")
        .member<double>("beta_deg")
        .member<double>("g_load_normal")
        .member<double>("g_load_axial")
        .member<double>("p_deg_s")
        .member<double>("q_deg_s")
        .member<double>("r_deg_s")
        .member<double>("engine_rpm_pct")
        .member<double>("engine_temp_c")
        .member<double>("fuel_flow_kg_h")
        .member<double>("throttle_pos")
        .member<double>("fuel_internal_kg")
        .member<double>("fuel_external_kg")
        .member<float>("gear_pos")
        .member<float>("flaps_pos")
        .member<float>("speedbrake_pos")
        .member<bool>("master_arm")
        .member<double>("oat_c")
        .member<double>("cmd_heading_deg")
        .member<double>("cmd_alt_m")
        .member<double>("cmd_speed_mps")
        .member<bool>("rwr_active")
        .member<int>("weapon_selected")
        .member<int>("missiles_remaining")
        .member<double>("lat_deg")
        .member<double>("lon_deg")
        .member<double>("vn_mps")
        .member<double>("ve_mps")
        .member<double>("vd_mps")
        .member<double>("ground_speed_mps")
        .member<double>("ground_track_deg")
        .member<double>("wind_speed_mps")
        .member<double>("wind_dir_deg")
        .member<bool>("gps_available")
        .member<double>("position_uncertainty_m")
        .member<double>("gear_stress")
        .member<bool>("gear_collapsed")
        .member<bool>("on_runway");
}

void register_air_tuning_reflection(flecs::world &ecs) {
    ecs.component<AeroTuning>()
        .member<bool>("enabled")
        .member<double>("cl_alpha_per_deg")
        .member<double>("cl0")
        .member<double>("cd0_clean")
        .member<double>("induced_drag_k")
        .member<double>("cm_alpha_per_rad")
        .member<double>("cm_q")
        .member<double>("alpha_stall_clean_deg")
        .member<double>("alpha_stall_flaps_full_deg")
        .member<double>("alpha_peak_offset_deg")
        .member<double>("alpha_deep_offset_deg")
        .member<double>("cl_peak_clean")
        .member<double>("cl_peak_flaps_full")
        .member<double>("cl_deep_clean")
        .member<double>("cl_deep_flaps_full")
        .member<double>("pitch_break_onset_deg")
        .member<double>("pitch_break_full_deg")
        .member<double>("pitch_break_cm_nose_down")
        .member<double>("post_stall_damp_floor")
        .member<double>("aoa_rate_pitch_break_gain")
        .member<double>("elevator_max_deflection_deg")
        .member<double>("aileron_max_deflection_deg")
        .member<double>("rudder_max_deflection_deg")
        .member<double>("cm_delta_e_per_rad")
        .member<double>("cl_delta_a_per_rad")
        .member<double>("cn_delta_r_per_rad")
        .member<double>("fbw_elevator_cmd_per_rate_err")
        .member<double>("fbw_aileron_cmd_per_rate_err")
        .member<double>("fbw_rudder_cmd_per_rate_err")
        .member<double>("ari_rudder_cmd_per_aileron_cmd")
        .member<bool>("fbw_g_command_enabled")
        .member<double>("fbw_g_command_neutral")
        .member<double>("fbw_g_command_max")
        .member<double>("fbw_g_command_min")
        .member<double>("fbw_pitch_rate_per_g_err")
        .member<std::vector<double>>("control_effectiveness_scale_vs_mach")
        .member<double>("actuator_tau_elevator_s")
        .member<double>("actuator_tau_aileron_s")
        .member<double>("actuator_tau_rudder_s")
        .member<std::vector<double>>("mach_breakpoints")
        .member<std::vector<double>>("cl_alpha_scale_vs_mach")
        .member<std::vector<double>>("cd0_add_vs_mach")
        .member<std::vector<double>>("induced_drag_scale_vs_mach")
        .member<std::vector<double>>("cm_alpha_scale_vs_mach")
        .member<std::vector<double>>("stall_alpha_delta_deg_vs_mach");
}

void register_aircraft_baseline_reflection(flecs::world &ecs) {
    ecs.component<AircraftDamageBaseline>()
        .member<double>("max_speed")
        .member<double>("min_speed")
        .member<double>("max_turn_rate")
        .member<double>("max_accel")
        .member<double>("max_climb_rate")
        .member<double>("max_g")
        .member<double>("min_g")
        .member<double>("takeoff_speed")
        .member<double>("landing_speed")
        .member<double>("taxi_turn_rate")
        .member<double>("mil_thrust_n")
        .member<double>("ab_thrust_n")
        .member<double>("fuel_leak_rate_kg_s")
        .member<double>("flutter_dynamic_pressure_pa")
        .member<double>("flutter_mach")
        .member<double>("sensor_max_range")
        .member<double>("sensor_detection_prob")
        .member<double>("sensor_bearing_noise_std")
        .member<double>("sensor_range_noise_std")
        .member<double>("sensor_track_memory_s");
}

} // namespace

void register_state_transfer_component_reflection(flecs::world &ecs) {
    register_standard_container_reflection(ecs);
    register_nested_value_reflection(ecs);
    register_ground_combat_reflection(ecs);
    register_platform_state_reflection(ecs);
    register_remaining_scalar_reflection(ecs);
    register_basic_reflection(ecs);
    register_command_scalar_reflection(ecs);
    register_tasking_reflection(ecs);
    register_physics_scalar_reflection(ecs);
    register_resource_scalar_reflection(ecs);
    register_sensor_and_queue_reflection(ecs);
    register_instrument_reflection(ecs);
    register_air_tuning_reflection(ecs);
    register_aircraft_baseline_reflection(ecs);
}
