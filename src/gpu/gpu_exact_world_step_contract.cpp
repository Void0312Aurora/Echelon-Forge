#include "gpu/gpu_exact_world_step_contract.h"

#include <cstring>
#include <stdexcept>
#include <type_traits>

namespace gpu {

namespace {

constexpr std::uint64_t kFnv1aOffsetBasis = 1469598103934665603ull;
constexpr std::uint64_t kFnv1aPrime = 1099511628211ull;

void fnv1a_64_append(std::uint64_t& hash, const void* data, std::size_t size) noexcept {
    const auto* bytes = static_cast<const unsigned char*>(data);
    for (std::size_t i = 0; i < size; ++i) {
        hash ^= static_cast<std::uint64_t>(bytes[i]);
        hash *= kFnv1aPrime;
    }
}

static_assert(std::is_trivially_copyable_v<ExactWorldStepStateV1>);

template <typename T>
std::enable_if_t<std::is_same_v<T, bool>, void> hash_append(std::uint64_t& hash, T value) noexcept {
    const std::uint8_t raw = value ? 1u : 0u;
    fnv1a_64_append(hash, &raw, sizeof(raw));
}

template <typename T>
std::enable_if_t<std::is_enum_v<T>, void> hash_append(std::uint64_t& hash, T value) noexcept {
    const auto raw = static_cast<std::underlying_type_t<T>>(value);
    fnv1a_64_append(hash, &raw, sizeof(raw));
}

template <typename T>
std::enable_if_t<std::is_arithmetic_v<T> && !std::is_same_v<T, bool>, void> hash_append(
    std::uint64_t& hash,
    T value
) noexcept {
    fnv1a_64_append(hash, &value, sizeof(value));
}

void hash_append(std::uint64_t& hash, const Transform& value) noexcept {
    hash_append(hash, value.x);
    hash_append(hash, value.y);
    hash_append(hash, value.z);
    hash_append(hash, value.heading);
    hash_append(hash, value.pitch);
    hash_append(hash, value.roll);
}

void hash_append(std::uint64_t& hash, const Velocity& value) noexcept {
    hash_append(hash, value.vx);
    hash_append(hash, value.vy);
    hash_append(hash, value.vz);
}

void hash_append(std::uint64_t& hash, const AngularVelocity& value) noexcept {
    hash_append(hash, value.p);
    hash_append(hash, value.q);
    hash_append(hash, value.r);
}

void hash_append(std::uint64_t& hash, const ForceAccumulator& value) noexcept {
    hash_append(hash, value.fx);
    hash_append(hash, value.fy);
    hash_append(hash, value.fz);
    hash_append(hash, value.torque_roll);
    hash_append(hash, value.torque_pitch);
    hash_append(hash, value.torque_yaw);
}

void hash_append(std::uint64_t& hash, const AeroState& value) noexcept {
    hash_append(hash, value.dynamic_pressure);
    hash_append(hash, value.angle_of_attack);
    hash_append(hash, value.sideslip_angle);
    hash_append(hash, value.mach_number);
    hash_append(hash, value.lift_coefficient);
    hash_append(hash, value.drag_coefficient);
}

void hash_append(std::uint64_t& hash, const ControlLawState& value) noexcept {
    hash_append(hash, value.stick_roll_filt);
    hash_append(hash, value.stick_pitch_filt);
    hash_append(hash, value.stick_yaw_filt);
    hash_append(hash, value.stick_yaw_cmd);
}

void hash_append(std::uint64_t& hash, const PilotAction& value) noexcept {
    hash_append(hash, value.stick_pitch);
    hash_append(hash, value.stick_roll);
    hash_append(hash, value.rudder);
    hash_append(hash, value.throttle);
    hash_append(hash, value.gear_handle);
    hash_append(hash, value.flaps);
    hash_append(hash, value.speedbrake);
    hash_append(hash, value.brake);
    hash_append(hash, value.brake_left);
    hash_append(hash, value.brake_right);
    hash_append(hash, value.radar_active);
    hash_append(hash, value.radar_scan_az);
    hash_append(hash, value.radar_scan_el);
    hash_append(hash, value.tms_up);
    hash_append(hash, value.master_arm);
    hash_append(hash, value.fire_weapon);
    hash_append(hash, value.fire_gun);
    hash_append(hash, value.weapon_select_id);
    hash_append(hash, value.jettison_emergency);
    hash_append(hash, value.program_chaff);
    hash_append(hash, value.program_flare);
    hash_append(hash, value.active);
}

void hash_append(std::uint64_t& hash, const MissionCommand& value) noexcept {
    hash_append(hash, value.cmd_heading_deg);
    hash_append(hash, value.cmd_altitude_m);
    hash_append(hash, value.cmd_speed_mps);
    hash_append(hash, value.command_code);
    hash_append(hash, value.route_ref_id);
    hash_append(hash, value.recovery_base_id);
    hash_append(hash, value.recovery_runway_id);
    hash_append(hash, value.recovery_approach_type);
    hash_append(hash, value.formation_id);
    hash_append(hash, value.form_offset_x);
    hash_append(hash, value.form_offset_y);
    hash_append(hash, value.form_offset_z);
    hash_append(hash, value.assigned_target_id);
    hash_append(hash, value.authorization_to_fire);
    hash_append(hash, value.active);
}

void hash_append(std::uint64_t& hash, const MovementCommand& value) noexcept {
    hash_append(hash, value.target_heading);
    hash_append(hash, value.target_speed);
    hash_append(hash, value.target_altitude);
    hash_append(hash, value.use_stick_control);
    hash_append(hash, value.stick_roll);
    hash_append(hash, value.stick_pitch);
    hash_append(hash, value.throttle_cmd);
    hash_append(hash, value.gear_handle);
    hash_append(hash, value.active);
}

void hash_append(std::uint64_t& hash, const ActionCommand& value) noexcept {
    hash_append(hash, value.turn_rate_cmd);
    hash_append(hash, value.accel_cmd);
    hash_append(hash, value.climb_rate_cmd);
    hash_append(hash, value.fire_cmd);
    hash_append(hash, value.release_chaff);
    hash_append(hash, value.release_flare);
    hash_append(hash, value.jettison_tanks);
    hash_append(hash, value.send_msg);
    hash_append(hash, value.msg_type);
    hash_append(hash, value.msg_recipient);
    hash_append(hash, value.msg_arg);
    hash_append(hash, value.active);
}

void hash_append(std::uint64_t& hash, const ActionSpaceConfig& value) noexcept {
    hash_append(hash, value.max_turn_rate_deg_s);
    hash_append(hash, value.max_accel_mps2);
    hash_append(hash, value.max_climb_rate_mps);
    hash_append(hash, value.min_speed_mps);
    hash_append(hash, value.max_speed_mps);
    hash_append(hash, value.min_alt_m);
    hash_append(hash, value.max_alt_m);
}

void hash_append(std::uint64_t& hash, const CommandLag& value) noexcept {
    hash_append(hash, value.heading_tau_s);
    hash_append(hash, value.speed_tau_s);
    hash_append(hash, value.altitude_tau_s);
}

void hash_append(std::uint64_t& hash, const LaggedCommand& value) noexcept {
    hash_append(hash, value.target_heading);
    hash_append(hash, value.target_speed);
    hash_append(hash, value.target_altitude);
    hash_append(hash, value.active);
}

void hash_append(std::uint64_t& hash, const CommandLink& value) noexcept {
    hash_append(hash, value.latency_s);
    hash_append(hash, value.drop_prob);
}

void hash_append(std::uint64_t& hash, const PendingMovementCommand& value) noexcept {
    hash_append(hash, value.command);
    hash_append(hash, value.deliver_time);
    hash_append(hash, value.active);
}

void hash_append(std::uint64_t& hash, const PendingActionCommand& value) noexcept {
    hash_append(hash, value.command);
    hash_append(hash, value.deliver_time);
    hash_append(hash, value.active);
}

void hash_append(std::uint64_t& hash, const PendingMissionCommand& value) noexcept {
    hash_append(hash, value.command);
    hash_append(hash, value.deliver_time);
    hash_append(hash, value.active);
}

void hash_append(std::uint64_t& hash, const FlightModel& value) noexcept {
    hash_append(hash, value.max_speed);
    hash_append(hash, value.min_speed);
    hash_append(hash, value.max_turn_rate);
    hash_append(hash, value.max_accel);
    hash_append(hash, value.max_climb_rate);
    hash_append(hash, value.max_g);
    hash_append(hash, value.min_g);
    hash_append(hash, value.takeoff_speed);
    hash_append(hash, value.landing_speed);
    hash_append(hash, value.taxi_turn_rate);
}

void hash_append(std::uint64_t& hash, const Inertia& value) noexcept {
    hash_append(hash, value.ixx);
    hash_append(hash, value.iyy);
    hash_append(hash, value.izz);
}

void hash_append(std::uint64_t& hash, const LandingGear& value) noexcept {
    hash_append(hash, value.can_use_unpaved);
    hash_append(hash, value.rolling_friction_coeff);
    hash_append(hash, value.max_load_factor);
    hash_append(hash, value.contact_height_m);
    hash_append(hash, value.extension_state);
    hash_append(hash, value.is_jammed);
    hash_append(hash, value.transit_time_s);
}

void hash_append(std::uint64_t& hash, const GearState& value) noexcept {
    hash_append(hash, value.gear_down);
    hash_append(hash, value.stress);
    hash_append(hash, value.collapsed);
    hash_append(hash, value.stress_rate);
    hash_append(hash, value.on_runway);
}

void hash_append(std::uint64_t& hash, const FuelSystem& value) noexcept {
    hash_append(hash, value.internal_fuel_kg);
    hash_append(hash, value.max_internal_fuel_kg);
    hash_append(hash, value.external_fuel_kg);
    hash_append(hash, value.max_external_fuel_kg);
    hash_append(hash, value.current_flow_rate);
    hash_append(hash, value.afterburner_active);
    hash_append(hash, value.mil_power_flow_rate);
    hash_append(hash, value.ab_flow_rate_multiplier);
}

void hash_append(std::uint64_t& hash, const Mass& value) noexcept {
    hash_append(hash, value.empty_mass_kg);
    hash_append(hash, value.fuel_mass_kg);
    hash_append(hash, value.stores_mass_kg);
    hash_append(hash, value.fuel_leak_rate_kg_s);
}

void hash_append(std::uint64_t& hash, const Propulsion& value) noexcept {
    hash_append(hash, value.mil_thrust_n);
    hash_append(hash, value.ab_thrust_n);
    hash_append(hash, value.current_thrust_n);
    hash_append(hash, value.afterburner_active);
}

void hash_append(std::uint64_t& hash, const MassProperties& value) noexcept {
    hash_append(hash, value.empty_mass_kg);
    hash_append(hash, value.current_total_mass_kg);
    hash_append(hash, value.base_drag_index);
    hash_append(hash, value.current_drag_index);
    hash_append(hash, value.reference_area_m2);
    hash_append(hash, value.wing_span_m);
    hash_append(hash, value.chord_m);
}

void hash_append(std::uint64_t& hash, const GroundState& value) noexcept {
    hash_append(hash, value.on_ground);
    hash_append(hash, value.terrain_elevation);
    hash_append(hash, value.surface_friction);
}

void hash_append(std::uint64_t& hash, const Health& value) noexcept {
    hash_append(hash, value.current_hp);
    hash_append(hash, value.max_hp);
}

void hash_append(std::uint64_t& hash, const Ammo& value) noexcept {
    hash_append(hash, value.missiles_remaining);
    hash_append(hash, value.max_missiles);
}

void hash_append(std::uint64_t& hash, const Missile& value) noexcept {
    hash_append(hash, value.attacker_id);
    hash_append(hash, value.target_id);
    hash_append(hash, value.max_speed);
    hash_append(hash, value.turn_rate);
    hash_append(hash, value.fuse_distance);
    hash_append(hash, value.damage);
    hash_append(hash, value.seeker_fov_deg);
    hash_append(hash, value.seeker_lock_range);
    hash_append(hash, value.guidance_delay_s);
    hash_append(hash, value.guidance_update_period_s);
    hash_append(hash, value.last_guidance_time);
    hash_append(hash, value.launch_time);
    hash_append(hash, value.max_flight_time_s);
    hash_append(hash, value.nav_gain);
    hash_append(hash, value.active);
    hash_append(hash, value.rng_state);
    hash_append(hash, value.proximity_min_dist_m);
    hash_append(hash, value.proximity_last_dist_m);
    hash_append(hash, value.proximity_engaged);
}

void hash_append(std::uint64_t& hash, const ExactWorldStepRwrSummaryV1& value) noexcept {
    hash_append(hash, value.detected_count);
    hash_append(hash, value.locking_count);
    hash_append(hash, value.is_missile_launch);
}

void hash_append(std::uint64_t& hash, const Detection& value) noexcept {
    hash_append(hash, value.target_id);
    hash_append(hash, value.range);
    hash_append(hash, value.bearing);
    hash_append(hash, value.elevation);
    hash_append(hash, value.closing_speed);
    hash_append(hash, value.signal_strength);
    hash_append(hash, value.timestamp);
}

void hash_append(std::uint64_t& hash, const ExactWorldStepContactListSummaryV1& value) noexcept {
    hash_append(hash, value.count);
    hash_append(hash, value.truncated);
    for (std::size_t i = 0; i < kExactWorldStepContactSummaryCapacity; ++i) {
        hash_append(hash, value.contacts[i]);
    }
}

void hash_append(std::uint64_t& hash, const InstrumentState& value) noexcept {
    hash_append(hash, value.alt_baro_m);
    hash_append(hash, value.alt_radar_m);
    hash_append(hash, value.ias_mps);
    hash_append(hash, value.mach);
    hash_append(hash, value.vvi_mps);
    hash_append(hash, value.pitch_deg);
    hash_append(hash, value.roll_deg);
    hash_append(hash, value.heading_deg);
    hash_append(hash, value.aoa_deg);
    hash_append(hash, value.beta_deg);
    hash_append(hash, value.g_load_normal);
    hash_append(hash, value.g_load_axial);
    hash_append(hash, value.p_deg_s);
    hash_append(hash, value.q_deg_s);
    hash_append(hash, value.r_deg_s);
    hash_append(hash, value.engine_rpm_pct);
    hash_append(hash, value.engine_temp_c);
    hash_append(hash, value.fuel_flow_kg_h);
    hash_append(hash, value.throttle_pos);
    hash_append(hash, value.fuel_internal_kg);
    hash_append(hash, value.fuel_external_kg);
    hash_append(hash, value.gear_pos);
    hash_append(hash, value.flaps_pos);
    hash_append(hash, value.speedbrake_pos);
    hash_append(hash, value.master_arm);
    hash_append(hash, value.oat_c);
    hash_append(hash, value.cmd_heading_deg);
    hash_append(hash, value.cmd_alt_m);
    hash_append(hash, value.cmd_speed_mps);
    hash_append(hash, value.rwr_active);
    hash_append(hash, value.weapon_selected);
    hash_append(hash, value.missiles_remaining);
    hash_append(hash, value.lat_deg);
    hash_append(hash, value.lon_deg);
    hash_append(hash, value.vn_mps);
    hash_append(hash, value.ve_mps);
    hash_append(hash, value.vd_mps);
    hash_append(hash, value.ground_speed_mps);
    hash_append(hash, value.ground_track_deg);
    hash_append(hash, value.wind_speed_mps);
    hash_append(hash, value.wind_dir_deg);
    hash_append(hash, value.gps_available);
    hash_append(hash, value.position_uncertainty_m);
    hash_append(hash, value.gear_stress);
    hash_append(hash, value.gear_collapsed);
    hash_append(hash, value.on_runway);
}

void hash_append(std::uint64_t& hash, const EGI& value) noexcept {
    hash_append(hash, value.lat_deg);
    hash_append(hash, value.lon_deg);
    hash_append(hash, value.alt_baro_m);
    hash_append(hash, value.alt_radar_m);
    hash_append(hash, value.vn_mps);
    hash_append(hash, value.ve_mps);
    hash_append(hash, value.vd_mps);
    hash_append(hash, value.heading_deg);
    hash_append(hash, value.pitch_deg);
    hash_append(hash, value.roll_deg);
    hash_append(hash, value.wind_speed_mps);
    hash_append(hash, value.wind_dir_deg);
    hash_append(hash, value.drift_lat_m);
    hash_append(hash, value.drift_lon_m);
    hash_append(hash, value.drift_alt_m);
    hash_append(hash, value.position_uncertainty_m);
    hash_append(hash, value.time_since_last_gps_fix);
    hash_append(hash, value.ins_drift_rate_mps);
    hash_append(hash, value.gps_available);
}

void hash_append(std::uint64_t& hash, const ExactWorldStepEnvironmentSampleV1& value) noexcept {
    hash_append(hash, value.terrain_elevation_m);
    hash_append(hash, value.wind_vx_mps);
    hash_append(hash, value.wind_vy_mps);
    hash_append(hash, value.terrain_surface_code);
    hash_append(hash, value.runway_heading_deg);
}

void hash_optional_component(
    std::uint64_t& hash,
    bool present,
    const auto& value
) noexcept {
    hash_append(hash, present);
    if (present) {
        hash_append(hash, value);
    }
}

}  // namespace

std::size_t exact_world_step_state_v1_size_bytes() noexcept {
    return sizeof(ExactWorldStepStateV1);
}

std::string pack_exact_world_step_states_v1(const std::vector<ExactWorldStepStateV1>& states) {
    const auto packed_size = states.size() * sizeof(ExactWorldStepStateV1);
    std::string packed;
    packed.resize(packed_size);
    if (packed_size > 0) {
        std::memcpy(packed.data(), states.data(), packed_size);
    }
    return packed;
}

std::vector<ExactWorldStepStateV1> unpack_exact_world_step_states_v1(std::string_view packed) {
    if (packed.size() % sizeof(ExactWorldStepStateV1) != 0) {
        throw std::invalid_argument("packed exact world step state blob has an invalid byte size");
    }
    std::vector<ExactWorldStepStateV1> out(packed.size() / sizeof(ExactWorldStepStateV1));
    if (!out.empty()) {
        std::memcpy(out.data(), packed.data(), packed.size());
    }
    return out;
}

std::uint64_t exact_world_step_state_v1_apply_signature(const ExactWorldStepStateV1& state) noexcept {
    std::uint64_t hash = kFnv1aOffsetBasis;
    hash_append(hash, 0ull);
    hash_append(hash, state.time_step_s);
    hash_append(hash, 0.0);
    hash_append(hash, state.transform);
    hash_append(hash, state.velocity);
    hash_optional_component(hash, state.has_angular_velocity, state.angular_velocity);
    hash_optional_component(hash, state.has_force_accumulator, state.force_accumulator);
    hash_optional_component(hash, state.has_aero_state, state.aero_state);
    hash_optional_component(hash, state.has_control_law_state, state.control_law_state);
    hash_optional_component(hash, state.has_pilot_action, state.pilot_action);
    hash_optional_component(hash, state.has_mission_command, state.mission_command);
    hash_optional_component(hash, state.has_movement_command, state.movement_command);
    hash_optional_component(hash, state.has_action_command, state.action_command);
    hash_optional_component(hash, state.has_action_space_config, state.action_space_config);
    hash_optional_component(hash, state.has_command_lag, state.command_lag);
    hash_optional_component(hash, state.has_lagged_command, state.lagged_command);
    hash_optional_component(hash, state.has_command_link, state.command_link);
    hash_optional_component(hash, state.has_pending_movement_command, state.pending_movement_command);
    hash_optional_component(hash, state.has_pending_action_command, state.pending_action_command);
    hash_optional_component(hash, state.has_pending_mission_command, state.pending_mission_command);
    hash_optional_component(hash, state.has_flight_model, state.flight_model);
    hash_optional_component(hash, state.has_inertia, state.inertia);
    hash_optional_component(hash, state.has_landing_gear, state.landing_gear);
    hash_optional_component(hash, state.has_gear_state, state.gear_state);
    hash_optional_component(hash, state.has_fuel_system, state.fuel_system);
    hash_optional_component(hash, state.has_mass, state.mass);
    hash_optional_component(hash, state.has_propulsion, state.propulsion);
    hash_optional_component(hash, state.has_mass_properties, state.mass_properties);
    hash_optional_component(hash, state.has_ground_state, state.ground_state);
    hash_optional_component(hash, state.has_health, state.health);
    hash_optional_component(hash, state.has_ammo, state.ammo);
    hash_optional_component(hash, state.has_missile, state.missile);
    hash_optional_component(hash, state.has_rwr_summary, state.rwr_summary);
    hash_optional_component(hash, state.has_contact_list_summary, state.contact_list_summary);
    hash_optional_component(hash, state.has_instrument_state, state.instrument_state);
    hash_optional_component(hash, state.has_egi, state.egi);
    return hash;
}

std::vector<std::uint64_t> exact_world_step_state_v1_apply_signatures(
    const std::vector<ExactWorldStepStateV1>& states
) {
    std::vector<std::uint64_t> out(states.size(), 0ull);
    for (std::size_t i = 0; i < states.size(); ++i) {
        out[i] = exact_world_step_state_v1_apply_signature(states[i]);
    }
    return out;
}

std::vector<std::pair<std::string, std::uint64_t>> exact_world_step_state_v1_component_digests(
    const ExactWorldStepStateV1& state
) {
    auto digest_of = [](const auto& value) {
        std::uint64_t hash = kFnv1aOffsetBasis;
        hash_append(hash, value);
        return hash;
    };

    std::vector<std::pair<std::string, std::uint64_t>> out;
    out.reserve(24);
    out.emplace_back("entity_id", digest_of(state.entity_id));
    out.emplace_back("time_step_s", digest_of(state.time_step_s));
    out.emplace_back("transform", digest_of(state.transform));
    out.emplace_back("velocity", digest_of(state.velocity));
    out.emplace_back("environment_sample.present", digest_of(state.has_environment_sample));
    if (state.has_environment_sample) {
        out.emplace_back("environment_sample", digest_of(state.environment_sample));
    }
    out.emplace_back("angular_velocity.present", digest_of(state.has_angular_velocity));
    if (state.has_angular_velocity) {
        out.emplace_back("angular_velocity", digest_of(state.angular_velocity));
    }
    out.emplace_back("force_accumulator.present", digest_of(state.has_force_accumulator));
    if (state.has_force_accumulator) {
        out.emplace_back("force_accumulator", digest_of(state.force_accumulator));
    }
    out.emplace_back("aero_state.present", digest_of(state.has_aero_state));
    if (state.has_aero_state) {
        out.emplace_back("aero_state", digest_of(state.aero_state));
    }
    out.emplace_back("control_law_state.present", digest_of(state.has_control_law_state));
    if (state.has_control_law_state) {
        out.emplace_back("control_law_state", digest_of(state.control_law_state));
    }
    out.emplace_back("pilot_action.present", digest_of(state.has_pilot_action));
    if (state.has_pilot_action) {
        out.emplace_back("pilot_action", digest_of(state.pilot_action));
    }
    out.emplace_back("mission_command.present", digest_of(state.has_mission_command));
    if (state.has_mission_command) {
        out.emplace_back("mission_command", digest_of(state.mission_command));
    }
    out.emplace_back("movement_command.present", digest_of(state.has_movement_command));
    if (state.has_movement_command) {
        out.emplace_back("movement_command", digest_of(state.movement_command));
    }
    out.emplace_back("action_command.present", digest_of(state.has_action_command));
    if (state.has_action_command) {
        out.emplace_back("action_command", digest_of(state.action_command));
    }
    out.emplace_back("action_space_config.present", digest_of(state.has_action_space_config));
    if (state.has_action_space_config) {
        out.emplace_back("action_space_config", digest_of(state.action_space_config));
    }
    out.emplace_back("command_lag.present", digest_of(state.has_command_lag));
    if (state.has_command_lag) {
        out.emplace_back("command_lag", digest_of(state.command_lag));
    }
    out.emplace_back("lagged_command.present", digest_of(state.has_lagged_command));
    if (state.has_lagged_command) {
        out.emplace_back("lagged_command", digest_of(state.lagged_command));
    }
    out.emplace_back("command_link.present", digest_of(state.has_command_link));
    if (state.has_command_link) {
        out.emplace_back("command_link", digest_of(state.command_link));
    }
    out.emplace_back("pending_movement_command.present", digest_of(state.has_pending_movement_command));
    if (state.has_pending_movement_command) {
        out.emplace_back("pending_movement_command", digest_of(state.pending_movement_command));
    }
    out.emplace_back("pending_action_command.present", digest_of(state.has_pending_action_command));
    if (state.has_pending_action_command) {
        out.emplace_back("pending_action_command", digest_of(state.pending_action_command));
    }
    out.emplace_back("pending_mission_command.present", digest_of(state.has_pending_mission_command));
    if (state.has_pending_mission_command) {
        out.emplace_back("pending_mission_command", digest_of(state.pending_mission_command));
    }
    out.emplace_back("flight_model.present", digest_of(state.has_flight_model));
    if (state.has_flight_model) {
        out.emplace_back("flight_model", digest_of(state.flight_model));
    }
    out.emplace_back("inertia.present", digest_of(state.has_inertia));
    if (state.has_inertia) {
        out.emplace_back("inertia", digest_of(state.inertia));
    }
    out.emplace_back("landing_gear.present", digest_of(state.has_landing_gear));
    if (state.has_landing_gear) {
        out.emplace_back("landing_gear", digest_of(state.landing_gear));
    }
    out.emplace_back("gear_state.present", digest_of(state.has_gear_state));
    if (state.has_gear_state) {
        out.emplace_back("gear_state", digest_of(state.gear_state));
    }
    out.emplace_back("fuel_system.present", digest_of(state.has_fuel_system));
    if (state.has_fuel_system) {
        out.emplace_back("fuel_system", digest_of(state.fuel_system));
    }
    out.emplace_back("mass.present", digest_of(state.has_mass));
    if (state.has_mass) {
        out.emplace_back("mass", digest_of(state.mass));
    }
    out.emplace_back("propulsion.present", digest_of(state.has_propulsion));
    if (state.has_propulsion) {
        out.emplace_back("propulsion", digest_of(state.propulsion));
    }
    out.emplace_back("mass_properties.present", digest_of(state.has_mass_properties));
    if (state.has_mass_properties) {
        out.emplace_back("mass_properties", digest_of(state.mass_properties));
    }
    out.emplace_back("ground_state.present", digest_of(state.has_ground_state));
    if (state.has_ground_state) {
        out.emplace_back("ground_state", digest_of(state.ground_state));
    }
    out.emplace_back("health.present", digest_of(state.has_health));
    if (state.has_health) {
        out.emplace_back("health", digest_of(state.health));
    }
    out.emplace_back("ammo.present", digest_of(state.has_ammo));
    if (state.has_ammo) {
        out.emplace_back("ammo", digest_of(state.ammo));
    }
    out.emplace_back("missile.present", digest_of(state.has_missile));
    if (state.has_missile) {
        out.emplace_back("missile", digest_of(state.missile));
    }
    out.emplace_back("rwr_summary.present", digest_of(state.has_rwr_summary));
    if (state.has_rwr_summary) {
        out.emplace_back("rwr_summary", digest_of(state.rwr_summary));
    }
    out.emplace_back("contact_list_summary.present", digest_of(state.has_contact_list_summary));
    if (state.has_contact_list_summary) {
        out.emplace_back("contact_list_summary", digest_of(state.contact_list_summary));
    }
    out.emplace_back("instrument_state.present", digest_of(state.has_instrument_state));
    if (state.has_instrument_state) {
        out.emplace_back("instrument_state", digest_of(state.instrument_state));
    }
    out.emplace_back("egi.present", digest_of(state.has_egi));
    if (state.has_egi) {
        out.emplace_back("egi", digest_of(state.egi));
    }
    return out;
}

}  // namespace gpu
