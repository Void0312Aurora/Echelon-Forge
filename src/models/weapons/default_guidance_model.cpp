#include "core/interfaces/guidance_model.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <utility>
#include <vector>

#include "components/basic/common.h"
#include "components/physics/dynamics.h"
#include "components/systems/logistics.h"
#include "components/systems/sensor.h"
#include "core/interfaces/environment_model.h"
#include "core/interfaces/engagement_event_recorder.h"
#include "models/physics/aerodynamics_common.h"
#include "models/weapons/missile_guidance_math.h"
#include "models/weapons/missile_guidance_types.h"

namespace {

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using missile_guidance::Vec3;
using missile_guidance::operator+;
using missile_guidance::operator-;
using missile_guidance::operator*;
using missile_guidance::operator/;

constexpr double kGravity = 9.80665;
constexpr double kBoostMinDurationS = 0.5;

struct GuidanceResolvedTuning {
    double bearing_filter_tau_s = MissileGuidanceDefaults::kTrackFilterTauS;
    double elevation_filter_tau_s = MissileGuidanceDefaults::kTrackFilterTauS;
    double range_filter_tau_s = MissileGuidanceDefaults::kTrackFilterTauS;
    double track_memory_timeout_s = MissileGuidanceDefaults::kTrackMemoryTimeoutS;
    double boost_time_s = MissileGuidanceDefaults::kBoostTimeS;
    double sustain_time_s = MissileGuidanceDefaults::kSustainTimeS;
    double boost_thrust_n = 0.0;
    double sustain_thrust_n = 0.0;
    double reference_area_m2 = MissileGuidanceDefaults::kReferenceAreaM2;
    double cd0_subsonic = MissileGuidanceDefaults::kCd0Subsonic;
    double cd0_supersonic = MissileGuidanceDefaults::kCd0Supersonic;
    double induced_drag_k = MissileGuidanceDefaults::kInducedDragScale;
    double propellant_mass_kg = 0.0;
    double max_lateral_g = 0.0;
    double autopilot_tau_s = MissileGuidanceDefaults::kAutopilotTauS;
    double max_accel_response_g_per_s = MissileGuidanceDefaults::kAccelResponseGps;
    double apn_target_accel_gain = MissileGuidanceDefaults::kDefaultApnTargetAccelGain;
    double cd0_power_on_ratio = MissileGuidanceDefaults::kCd0PowerOnRatio;
    double mach_transonic_start = MissileGuidanceDefaults::kMachTransonicStart;
    double mach_transonic_end = MissileGuidanceDefaults::kMachTransonicEnd;
    std::vector<double> cd0_mach_breakpoints;
    std::vector<double> cd0_mach_values;
    std::vector<double> induced_drag_k_mach_breakpoints;
    std::vector<double> induced_drag_k_mach_values;
    double autopilot_damping = 1.0;
    int autopilot_order = 1;
};

double default_propellant_mass_kg(double total_mass_kg) {
    const double scaled = total_mass_kg * MissileGuidanceDefaults::kPropellantMassFraction;
    return std::clamp(
        scaled, MissileGuidanceDefaults::kMinPropellantMassKg,
        std::max(MissileGuidanceDefaults::kMinPropellantMassKg, total_mass_kg * 0.55));
}

double default_boost_thrust_n(double total_mass_kg, double max_speed_mps,
                              double current_speed_mps) {
    const double delta_v = std::max(200.0, max_speed_mps - current_speed_mps);
    const double nominal_accel = delta_v / std::max(0.5, MissileGuidanceDefaults::kBoostTimeS);
    return std::max(15000.0, total_mass_kg * nominal_accel * 1.10);
}

double default_sustain_thrust_n(double boost_thrust_n) {
    return boost_thrust_n * 0.35;
}

double fallback_max_lateral_g(const Missile &missile) {
    return std::clamp(12.0 + 0.4 * std::max(0.0, missile.turn_rate), 12.0, 35.0);
}

double nonnegative_or(double candidate, double fallback) {
    return std::isfinite(candidate) && candidate >= 0.0 ? candidate : fallback;
}

double positive_or_nan_safe(double candidate, double fallback) {
    return std::isfinite(candidate) && candidate > 1.0e-9 ? candidate : fallback;
}

double finite_nonnegative_or(double candidate, double fallback) {
    return std::isfinite(candidate) && candidate >= 0.0 ? candidate : fallback;
}

std::array<double, 3> guidance_world_point_to_local_body(const Transform &target_transform,
                                                         double world_x, double world_y,
                                                         double world_z) {
    const Math::Vector3 local = Math::world_to_body(
        {world_x - target_transform.x, world_y - target_transform.y, world_z - target_transform.z},
        target_transform);
    return {local.x, -local.y, local.z};
}

bool guidance_has_stored_proximity_min_local_point(const Missile &missile) {
    return std::isfinite(missile.proximity_min_dist_m) &&
           std::isfinite(missile.proximity_min_local_forward_m) &&
           std::isfinite(missile.proximity_min_local_right_m) &&
           std::isfinite(missile.proximity_min_local_up_m);
}

std::array<double, 3> guidance_timeout_local_point(const Missile &missile,
                                                   const Transform &target_transform,
                                                   const Transform &missile_transform) {
    if (guidance_has_stored_proximity_min_local_point(missile)) {
        return {
            missile.proximity_min_local_forward_m,
            missile.proximity_min_local_right_m,
            missile.proximity_min_local_up_m,
        };
    }
    return guidance_world_point_to_local_body(target_transform, missile_transform.x,
                                              missile_transform.y, missile_transform.z);
}

double guidance_timeout_miss_distance(const Missile &missile, const Transform &target_transform,
                                      const Transform &missile_transform) {
    if (std::isfinite(missile.proximity_min_dist_m)) {
        return missile.proximity_min_dist_m;
    }
    const double dx = missile_transform.x - target_transform.x;
    const double dy = missile_transform.y - target_transform.y;
    const double dz = missile_transform.z - target_transform.z;
    return std::sqrt(dx * dx + dy * dy + dz * dz);
}

double guidance_closure_mps(const Transform &missile_transform, const Transform &target_transform,
                            const Velocity &missile_velocity, const Velocity *target_velocity) {
    const double target_vx = target_velocity ? target_velocity->vx : 0.0;
    const double target_vy = target_velocity ? target_velocity->vy : 0.0;
    const double target_vz = target_velocity ? target_velocity->vz : 0.0;
    const double rel_vx = target_vx - missile_velocity.vx;
    const double rel_vy = target_vy - missile_velocity.vy;
    const double rel_vz = target_vz - missile_velocity.vz;
    const double dx = target_transform.x - missile_transform.x;
    const double dy = target_transform.y - missile_transform.y;
    const double dz = target_transform.z - missile_transform.z;
    const double range = std::sqrt(dx * dx + dy * dy + dz * dz);
    if (range <= 1.0e-6) {
        return std::sqrt(rel_vx * rel_vx + rel_vy * rel_vy + rel_vz * rel_vz);
    }
    const double ux = dx / range;
    const double uy = dy / range;
    const double uz = dz / range;
    return std::max(0.0, -(rel_vx * ux + rel_vy * uy + rel_vz * uz));
}

std::array<double, 3> guidance_velocity_axis_in_target_body(const Transform &target_transform,
                                                            const Velocity &missile_velocity) {
    const double norm = std::sqrt(missile_velocity.vx * missile_velocity.vx +
                                  missile_velocity.vy * missile_velocity.vy +
                                  missile_velocity.vz * missile_velocity.vz);
    if (norm <= 1.0e-9) {
        return {0.0, 0.0, 0.0};
    }
    const auto local_velocity = guidance_world_point_to_local_body(
        target_transform, target_transform.x + missile_velocity.vx,
        target_transform.y + missile_velocity.vy, target_transform.z + missile_velocity.vz);
    return {
        local_velocity[0] / norm,
        local_velocity[1] / norm,
        local_velocity[2] / norm,
    };
}

std::string guidance_nearest_approach_aspect_bucket(double local_forward_m, double local_right_m) {
    if (!std::isfinite(local_forward_m) || !std::isfinite(local_right_m)) {
        return "unknown";
    }
    if (std::abs(local_forward_m) >= std::abs(local_right_m)) {
        return local_forward_m >= 0.0 ? "nose" : "tail";
    }
    return "beam";
}

void record_missile_timeout_event(flecs::world world, flecs::entity missile_entity,
                                  const Transform &transform, const Velocity &velocity,
                                  const Missile &missile, double current_time) {
    const EngagementEventRecorderRef *recorder_ref = world.get<EngagementEventRecorderRef>();
    if (!recorder_ref || !recorder_ref->recorder || missile.target_id == 0) {
        return;
    }

    flecs::entity target_entity = world.entity(missile.target_id);
    if (!target_entity.is_valid()) {
        return;
    }
    const Transform *target_transform = target_entity.get<Transform>();
    if (!target_transform) {
        return;
    }

    constexpr const char *kReason = "missile_max_flight_time_exceeded";
    constexpr const char *kOutcomeState = "missile_timeout";
    const Velocity *target_velocity = target_entity.get<Velocity>();
    const double nearest_time =
        std::isfinite(missile.proximity_min_time_s) ? missile.proximity_min_time_s : current_time;
    const double miss_distance_m =
        guidance_timeout_miss_distance(missile, *target_transform, transform);
    const auto local_point = guidance_timeout_local_point(missile, *target_transform, transform);
    const double closure_mps =
        std::max(guidance_closure_mps(transform, *target_transform, velocity, target_velocity),
                 std::max(0.0, missile.filtered_closing_speed_mps));
    const auto missile_axis = guidance_velocity_axis_in_target_body(*target_transform, velocity);
    const double trigger_radius_m = std::isfinite(missile.fuze_profile.trigger_radius_m)
                                        ? missile.fuze_profile.trigger_radius_m
                                        : missile.fuse_distance;
    const double fuze_reliability = std::clamp(missile.fuze_profile.reliability, 0.0, 1.0);

    NearestApproachEvent nearest{};
    nearest.header.stage = std::string(kLethalityChainStageNearestApproach);
    nearest.header.status = "observed";
    nearest.header.reason = kReason;
    nearest.header.source_time_s = nearest_time;
    nearest.header.fidelity_mode = "runtime";
    nearest.header.evidence_level = "observed_runtime";
    nearest.header.confidence = 1.0;
    nearest.nearest_approach_time_s = nearest_time;
    nearest.miss_distance_m = miss_distance_m;
    nearest.local_forward_m = local_point[0];
    nearest.local_right_m = local_point[1];
    nearest.local_up_m = local_point[2];
    nearest.closure_mps = closure_mps;
    nearest.aspect_bucket = guidance_nearest_approach_aspect_bucket(local_point[0], local_point[1]);
    EngagementNearestApproachEventRecord nearest_record{};
    nearest_record.munition_entity_id = static_cast<std::uint64_t>(missile_entity.id());
    nearest_record.shooter_id = missile.attacker_id;
    nearest_record.target_id = missile.target_id;
    nearest_record.event = std::move(nearest);
    (void)recorder_ref->recorder->record_nearest_approach_event(std::move(nearest_record));

    FuzeEvaluationEvent fuze{};
    fuze.header.stage = std::string(kLethalityChainStageFuze);
    fuze.header.status = "evaluated";
    fuze.header.reason = kReason;
    fuze.header.source_time_s = current_time;
    fuze.header.fidelity_mode = "runtime";
    fuze.header.evidence_level = "observed_runtime";
    fuze.header.confidence = 1.0;
    fuze.fuze_type = fuze_profile_type(missile.fuze_profile);
    fuze.armed = false;
    fuze.triggered = false;
    fuze.failure_reason = kReason;
    fuze.delay_s = std::max(0.0, missile.fuze_profile.delay_s);
    fuze.reliability = fuze_reliability;
    fuze.sample = 1.0;
    fuze.expected_detonation_probability = 0.0;
    fuze.sampled_outcome = true;
    fuze.trigger_radius_m = trigger_radius_m;
    EngagementFuzeEvaluationEventRecord fuze_record{};
    fuze_record.munition_entity_id = static_cast<std::uint64_t>(missile_entity.id());
    fuze_record.shooter_id = missile.attacker_id;
    fuze_record.target_id = missile.target_id;
    fuze_record.event = std::move(fuze);
    (void)recorder_ref->recorder->record_fuze_evaluation_event(std::move(fuze_record));

    const EngagementDamageStateSnapshot snapshot =
        recorder_ref->recorder->capture_engagement_damage_state(missile.target_id);
    EngagementEffectsDamageEventRecord effects_record{};
    effects_record.munition_entity_id = static_cast<std::uint64_t>(missile_entity.id());
    effects_record.target_id = missile.target_id;
    effects_record.before = snapshot;
    effects_record.after = snapshot;
    EffectsEvent &effects = effects_record.effects;
    effects.trigger_type = std::string(kLethalityReasonMissileTimeout);
    effects.outcome_state = kOutcomeState;
    effects.detonation_time_s = current_time;
    effects.nearest_approach_time_s = nearest_time;
    effects.miss_distance_m = miss_distance_m;
    effects.detonation_local_forward_m = local_point[0];
    effects.detonation_local_right_m = local_point[1];
    effects.detonation_local_up_m = local_point[2];
    effects.detonation_heading_deg = transform.heading;
    effects.detonation_pitch_deg = transform.pitch;
    effects.detonation_roll_deg = transform.roll;
    effects.closure_mps = closure_mps;
    effects.missile_axis_forward = missile_axis[0];
    effects.missile_axis_right = missile_axis[1];
    effects.missile_axis_up = missile_axis[2];
    effects.quality = 0.0;
    effects.confidence = 0.0;
    effects.effect_family = warhead_effect_family(missile.warhead_profile);
    effects.warhead_mass_kg =
        std::isfinite(missile.warhead_profile.mass_kg) ? missile.warhead_profile.mass_kg : 0.0;
    effects.warhead_lethal_radius_m = std::isfinite(missile.warhead_profile.lethal_radius_m)
                                          ? missile.warhead_profile.lethal_radius_m
                                          : missile.fuse_distance;
    effects.warhead_profile_synthetic = missile.warhead_profile.synthetic;
    effects.damage_scalar_synthetic = missile.warhead_profile.damage_scalar_synthetic;
    effects.fuze_type = fuze_profile_type(missile.fuze_profile);
    effects.fuze_trigger_radius_m = trigger_radius_m;
    effects.fuze_delay_s = std::max(0.0, missile.fuze_profile.delay_s);
    effects.fuze_reliability = fuze_reliability;
    effects.fuze_profile_synthetic = missile.fuze_profile.synthetic;
    effects.fuze_signature_source = "timeout";
    effects.fuze_target_signature = 0.0;
    effects.fuze_signature_scale = 1.0;
    effects.fuze_effective_reliability = 0.0;
    (void)recorder_ref->recorder->record_effects_damage_event(std::move(effects_record));
}

void ensure_mass_state_initialized(flecs::entity missile_entity, double reference_area_m2) {
    if (missile_entity.has<MassProperties>()) {
        return;
    }
    const Mass *mass = missile_entity.get<Mass>();
    if (!mass) {
        return;
    }
    missile_entity.set<MassProperties>(make_missile_mass_properties(
        *mass, clamp_missile_reference_area_m2(reference_area_m2,
                                               MissileGuidanceDefaults::kReferenceAreaM2)));
}

GuidanceResolvedTuning resolve_tuning(flecs::entity missile_entity, const Missile &missile,
                                      const Velocity &velocity) {
    GuidanceResolvedTuning out{};

    const Mass *mass = missile_entity.get<Mass>();
    const MassProperties *props = missile_entity.get<MassProperties>();
    const double total_mass_kg = mass ? std::max(1.0, mass->get_total_kg()) : 80.0;
    const double runtime_speed_mps = std::max(
        1.0, std::max(missile.current_speed_mps,
                      missile_guidance::norm(missile_guidance::velocity_to_vec3(velocity))));

    out.track_memory_timeout_s = nonnegative_or(missile.track_memory_timeout_s,
                                                MissileGuidanceDefaults::kTrackMemoryTimeoutS);
    out.boost_time_s =
        finite_nonnegative_or(missile.boost_duration_s, MissileGuidanceDefaults::kBoostTimeS);
    out.sustain_time_s =
        finite_nonnegative_or(missile.sustain_duration_s, MissileGuidanceDefaults::kSustainTimeS);
    if (out.boost_time_s <= 1.0e-9 && out.sustain_time_s <= 1.0e-9) {
        const double total_burn_s = std::max(0.0, missile.burnout_time_s - missile.launch_time);
        if (std::isfinite(total_burn_s) && total_burn_s > 0.0) {
            out.boost_time_s = std::min(total_burn_s, MissileGuidanceDefaults::kBoostTimeS);
            out.sustain_time_s = std::max(0.0, total_burn_s - out.boost_time_s);
        }
    }
    if (out.boost_time_s <= 1.0e-9 && out.sustain_time_s <= 1.0e-9) {
        out.boost_time_s = MissileGuidanceDefaults::kBoostTimeS;
        out.sustain_time_s = MissileGuidanceDefaults::kSustainTimeS;
    }

    out.reference_area_m2 =
        props ? clamp_missile_reference_area_m2(props->reference_area_m2,
                                                MissileGuidanceDefaults::kReferenceAreaM2)
              : MissileGuidanceDefaults::kReferenceAreaM2;
    out.propellant_mass_kg =
        mass ? std::max(0.0, mass->fuel_mass_kg) : default_propellant_mass_kg(total_mass_kg);
    out.max_lateral_g =
        positive_or_nan_safe(missile.guidance_max_lateral_g, fallback_max_lateral_g(missile));
    out.autopilot_tau_s = positive_or_nan_safe(missile.guidance_autopilot_tau_s,
                                               MissileGuidanceDefaults::kAutopilotTauS);
    out.autopilot_damping =
        std::isfinite(missile.autopilot_damping) && missile.autopilot_damping > 0.0
            ? missile.autopilot_damping
            : 1.0;
    out.autopilot_order = missile.autopilot_order >= 1 ? missile.autopilot_order : 1;
    out.mach_transonic_start = finite_nonnegative_or(missile.guidance_mach_transonic_start,
                                                     MissileGuidanceDefaults::kMachTransonicStart);
    out.mach_transonic_end = finite_nonnegative_or(missile.guidance_mach_transonic_end,
                                                   MissileGuidanceDefaults::kMachTransonicEnd);
    out.cd0_power_on_ratio = finite_nonnegative_or(missile.guidance_cd0_power_on_ratio,
                                                   MissileGuidanceDefaults::kCd0PowerOnRatio);
    out.max_accel_response_g_per_s = positive_or_nan_safe(
        missile.guidance_max_accel_response_g_per_s, MissileGuidanceDefaults::kAccelResponseGps);
    out.cd0_subsonic =
        positive_or_nan_safe(missile.guidance_cd0_subsonic, MissileGuidanceDefaults::kCd0Subsonic);
    out.cd0_supersonic = positive_or_nan_safe(missile.guidance_cd0_supersonic,
                                              MissileGuidanceDefaults::kCd0Supersonic);
    out.induced_drag_k = finite_nonnegative_or(missile.guidance_induced_drag_k,
                                               MissileGuidanceDefaults::kInducedDragScale);
    out.cd0_mach_breakpoints = missile.guidance_cd0_mach_breakpoints;
    out.cd0_mach_values = missile.guidance_cd0_mach_values;
    out.induced_drag_k_mach_breakpoints = missile.guidance_induced_drag_k_mach_breakpoints;
    out.induced_drag_k_mach_values = missile.guidance_induced_drag_k_mach_values;
    out.apn_target_accel_gain = finite_nonnegative_or(
        missile.apn_target_accel_gain, MissileGuidanceDefaults::kDefaultApnTargetAccelGain);
    out.bearing_filter_tau_s = finite_nonnegative_or(missile.guidance_bearing_filter_tau_s,
                                                     MissileGuidanceDefaults::kTrackFilterTauS);
    out.elevation_filter_tau_s = finite_nonnegative_or(missile.guidance_elevation_filter_tau_s,
                                                       MissileGuidanceDefaults::kTrackFilterTauS);
    out.range_filter_tau_s = finite_nonnegative_or(missile.guidance_range_filter_tau_s,
                                                   MissileGuidanceDefaults::kTrackFilterTauS);
    const double fallback_boost_thrust_n =
        default_boost_thrust_n(total_mass_kg, missile.max_speed, runtime_speed_mps);
    out.boost_thrust_n =
        finite_nonnegative_or(missile.guidance_boost_thrust_n, fallback_boost_thrust_n);
    out.sustain_thrust_n = finite_nonnegative_or(missile.guidance_sustain_thrust_n,
                                                 default_sustain_thrust_n(out.boost_thrust_n));
    return out;
}

void initialize_runtime_state(flecs::entity missile_entity, Missile &missile,
                              const Velocity &velocity, double current_time) {
    if (missile.shared_launch_initialized && missile.runtime_initialized) {
        ensure_mass_state_initialized(missile_entity, MissileGuidanceDefaults::kReferenceAreaM2);
        return;
    }

    missile.runtime_initialized = true;
    if (!missile.shared_launch_initialized) {
        missile.seeker_mode = static_cast<int>(MissileSeekerMode::Ballistic);
        missile.track_memory_timeout_s = nonnegative_or(
            missile.track_memory_timeout_s, MissileGuidanceDefaults::kTrackMemoryTimeoutS);
        missile.current_speed_mps =
            missile_guidance::norm(missile_guidance::velocity_to_vec3(velocity));
        if (!std::isfinite(missile.burnout_time_s) || missile.burnout_time_s <= current_time) {
            missile.burnout_time_s = current_time + MissileGuidanceDefaults::kBoostTimeS +
                                     MissileGuidanceDefaults::kSustainTimeS;
        }
        if (!std::isfinite(missile.boost_duration_s)) {
            missile.boost_duration_s = MissileGuidanceDefaults::kBoostTimeS;
        }
        if (!std::isfinite(missile.sustain_duration_s)) {
            missile.sustain_duration_s = MissileGuidanceDefaults::kSustainTimeS;
        }
        if (!std::isfinite(missile.guidance_bearing_filter_tau_s)) {
            missile.guidance_bearing_filter_tau_s = MissileGuidanceDefaults::kTrackFilterTauS;
        }
        if (!std::isfinite(missile.guidance_elevation_filter_tau_s)) {
            missile.guidance_elevation_filter_tau_s = MissileGuidanceDefaults::kTrackFilterTauS;
        }
        if (!std::isfinite(missile.guidance_range_filter_tau_s)) {
            missile.guidance_range_filter_tau_s = MissileGuidanceDefaults::kTrackFilterTauS;
        }
        if (!std::isfinite(missile.guidance_max_lateral_g)) {
            missile.guidance_max_lateral_g = fallback_max_lateral_g(missile);
        }
        if (!std::isfinite(missile.guidance_autopilot_tau_s)) {
            missile.guidance_autopilot_tau_s = MissileGuidanceDefaults::kAutopilotTauS;
        }
        if (!std::isfinite(missile.guidance_max_accel_response_g_per_s)) {
            missile.guidance_max_accel_response_g_per_s =
                MissileGuidanceDefaults::kAccelResponseGps;
        }
        if (!std::isfinite(missile.guidance_boost_thrust_n)) {
            missile.guidance_boost_thrust_n = default_boost_thrust_n(
                80.0, missile.max_speed, std::max(1.0, missile.current_speed_mps));
        }
        if (!std::isfinite(missile.guidance_sustain_thrust_n)) {
            missile.guidance_sustain_thrust_n =
                default_sustain_thrust_n(missile.guidance_boost_thrust_n);
        }
        if (!std::isfinite(missile.guidance_cd0_subsonic)) {
            missile.guidance_cd0_subsonic = MissileGuidanceDefaults::kCd0Subsonic;
        }
        if (!std::isfinite(missile.guidance_cd0_supersonic)) {
            missile.guidance_cd0_supersonic = MissileGuidanceDefaults::kCd0Supersonic;
        }
        if (!std::isfinite(missile.guidance_induced_drag_k)) {
            missile.guidance_induced_drag_k = MissileGuidanceDefaults::kInducedDragScale;
        }
    }

    if (Mass *mass = missile_entity.get_mut<Mass>()) {
        if (!missile.shared_launch_initialized) {
            const double total = mass->get_total_kg();
            if (total > 1.0 && mass->fuel_mass_kg <= 1.0e-6) {
                *mass = make_missile_mass_state(total, default_propellant_mass_kg(total));
            }
        }
    }
    ensure_mass_state_initialized(missile_entity, MissileGuidanceDefaults::kReferenceAreaM2);
}

void update_track_from_detection(Missile &missile, const Detection &det, double current_time,
                                 double dt, const GuidanceResolvedTuning &tuning,
                                 const Transform &transform, const Velocity &velocity) {
    // EKF path
    if (missile.use_kalman_seeker) {
        const double missile_world[3] = {transform.x, transform.y, transform.z};
        const double heading_rad = transform.heading * M_PI / 180.0;
        if (!missile.ekf_state.initialized) {
            missile_seeker::ekf_init(missile.ekf_state, missile.ekf_params,
                                     det.bearing * M_PI / 180.0, det.elevation * M_PI / 180.0,
                                     std::max(1.0, det.range), missile_world, heading_rad,
                                     current_time);
        } else {
            missile_seeker::ekf_predict(missile.ekf_state, missile.ekf_params,
                                        current_time - missile.ekf_state.last_predict_time_s);
            missile_seeker::ekf_update(missile.ekf_state, missile.ekf_params,
                                       det.bearing * M_PI / 180.0, det.elevation * M_PI / 180.0,
                                       std::max(1.0, det.range), missile_world, heading_rad);
        }
        // Save previous angles for rate computation
        const double prev_bearing = missile.filtered_bearing_deg;
        const double prev_elevation = missile.filtered_elevation_deg;

        // Extract body-relative spherical state for guidance-law compatibility
        missile.filtered_bearing_deg =
            missile_seeker::ekf_filtered_bearing_deg(missile.ekf_state, missile_world, heading_rad);
        missile.filtered_elevation_deg = missile_seeker::ekf_filtered_elevation_deg(
            missile.ekf_state, missile_world, heading_rad);
        missile.filtered_range_m =
            missile_seeker::ekf_filtered_range_m(missile.ekf_state, missile_world, heading_rad);
        const double mvel[3] = {velocity.vx, velocity.vy, velocity.vz};
        missile.filtered_closing_speed_mps =
            missile_seeker::ekf_closing_speed_mps(missile.ekf_state, missile_world, mvel);

        // Compute body-relative LOS rates from frame-to-frame angle delta
        if (dt > 1.0e-6 && missile.seeker_has_valid_track) {
            missile.bearing_rate_deg_s = missile_guidance::shortest_angle_delta_deg(
                                             prev_bearing, missile.filtered_bearing_deg) /
                                         dt;
            missile.elevation_rate_deg_s = (missile.filtered_elevation_deg - prev_elevation) / dt;
        } else {
            missile.bearing_rate_deg_s = 0.0;
            missile.elevation_rate_deg_s = 0.0;
        }
    } else {
        // Legacy first-order smoothing path
        if (!missile.seeker_has_valid_track) {
            missile.filtered_bearing_deg = det.bearing;
            missile.filtered_elevation_deg = det.elevation;
            missile.filtered_range_m = std::max(0.0, det.range);
            missile.filtered_closing_speed_mps = det.closing_speed;
            missile.bearing_rate_deg_s = 0.0;
            missile.elevation_rate_deg_s = 0.0;
        } else {
            const double prev_bearing = missile.filtered_bearing_deg;
            const double prev_elevation = missile.filtered_elevation_deg;

            missile.filtered_bearing_deg = missile_guidance::exp_smooth_angle_deg(
                missile.filtered_bearing_deg, det.bearing, tuning.bearing_filter_tau_s, dt);
            missile.filtered_elevation_deg = missile_guidance::exp_smooth_angle_deg(
                missile.filtered_elevation_deg, det.elevation, tuning.elevation_filter_tau_s, dt);
            missile.filtered_range_m = missile_guidance::exp_smooth(
                missile.filtered_range_m, std::max(0.0, det.range), tuning.range_filter_tau_s, dt);
            missile.filtered_closing_speed_mps =
                missile_guidance::exp_smooth(missile.filtered_closing_speed_mps, det.closing_speed,
                                             tuning.range_filter_tau_s, dt);

            if (dt > 1.0e-6) {
                missile.bearing_rate_deg_s = missile_guidance::shortest_angle_delta_deg(
                                                 prev_bearing, missile.filtered_bearing_deg) /
                                             dt;
                missile.elevation_rate_deg_s =
                    (missile.filtered_elevation_deg - prev_elevation) / dt;
            }
        }
    }

    missile.seeker_has_valid_track = true;
    missile.seeker_has_range = det.range > 1.0e-3;
    missile.last_track_time_s = current_time;
    missile.seeker_mode = static_cast<int>(MissileSeekerMode::Track);
}

void propagate_track_memory(Missile &missile, double dt, const Transform &transform,
                            const Velocity &velocity) {
    if (missile.use_kalman_seeker && missile.ekf_state.initialized) {
        const double prev_bearing = missile.filtered_bearing_deg;
        const double prev_elevation = missile.filtered_elevation_deg;

        missile_seeker::ekf_predict(missile.ekf_state, missile.ekf_params, dt);
        const double missile_world[3] = {transform.x, transform.y, transform.z};
        const double heading_rad = transform.heading * M_PI / 180.0;
        const double mvel[3] = {velocity.vx, velocity.vy, velocity.vz};
        missile.filtered_bearing_deg =
            missile_seeker::ekf_filtered_bearing_deg(missile.ekf_state, missile_world, heading_rad);
        missile.filtered_elevation_deg = missile_seeker::ekf_filtered_elevation_deg(
            missile.ekf_state, missile_world, heading_rad);
        missile.filtered_range_m =
            missile_seeker::ekf_filtered_range_m(missile.ekf_state, missile_world, heading_rad);
        missile.filtered_closing_speed_mps =
            missile_seeker::ekf_closing_speed_mps(missile.ekf_state, missile_world, mvel);

        if (dt > 1.0e-6) {
            missile.bearing_rate_deg_s = missile_guidance::shortest_angle_delta_deg(
                                             prev_bearing, missile.filtered_bearing_deg) /
                                         dt;
            missile.elevation_rate_deg_s = (missile.filtered_elevation_deg - prev_elevation) / dt;
        }
    } else {
        missile.filtered_bearing_deg = missile_guidance::normalize_angle_deg(
            missile.filtered_bearing_deg + missile.bearing_rate_deg_s * dt);
        missile.filtered_elevation_deg = std::clamp(
            missile.filtered_elevation_deg + missile.elevation_rate_deg_s * dt, -89.0, 89.0);
        missile.filtered_range_m = std::max(
            0.0, missile.filtered_range_m - std::max(0.0, missile.filtered_closing_speed_mps) * dt);
    }
    missile.seeker_mode = static_cast<int>(MissileSeekerMode::Memory);
}

bool terminal_seeker_is_active(const Missile &missile) {
    if (missile.terminal_seeker_active) {
        return true;
    }
    if (!std::isfinite(missile.seeker_activation_range_m) ||
        missile.seeker_activation_range_m <= 0.0) {
        return true;
    }
    return missile.filtered_range_m > 0.0 &&
           missile.filtered_range_m <= missile.seeker_activation_range_m;
}

bool detection_is_usable_for_guidance(const Missile &missile, const Detection &det) {
    if (det.local_sensor_hit) {
        return true;
    }
    return missile.midcourse_datalink_supported;
}

bool detection_matches_assigned_target(const Missile &missile, const Detection &det) {
    return missile.target_id == 0 || det.target_id == missile.target_id;
}

Vec3 guidance_estimated_target_position_world(const Missile &missile, const Transform &transform) {
    const Vec3 los_world =
        missile_guidance::normalize(missile_guidance::world_los_from_relative_angles(
            missile.filtered_bearing_deg, missile.filtered_elevation_deg, transform));
    const double range_m = std::max(0.0, missile.filtered_range_m);
    return {transform.x + los_world.x * range_m, transform.y + los_world.y * range_m,
            transform.z + los_world.z * range_m};
}

bool guidance_target_kinematics_are_finite(const Missile &missile) {
    return std::isfinite(missile.target_track_x_m) && std::isfinite(missile.target_track_y_m) &&
           std::isfinite(missile.target_track_z_m) && std::isfinite(missile.target_track_vx_mps) &&
           std::isfinite(missile.target_track_vy_mps) &&
           std::isfinite(missile.target_track_vz_mps) &&
           std::isfinite(missile.target_track_ax_mps2) &&
           std::isfinite(missile.target_track_ay_mps2) &&
           std::isfinite(missile.target_track_az_mps2);
}

double guidance_fallback_lead_time_s(double range_m, double closing_speed_mps,
                                     double missile_speed_mps) {
    const double closing_for_prediction =
        std::max({closing_speed_mps, missile_speed_mps * 0.25,
                  MissileGuidanceDefaults::kLeadPredictionMinClosingMps});
    return std::clamp(range_m / closing_for_prediction, 0.0,
                      MissileGuidanceDefaults::kLeadPredictionMaxTimeS);
}

double guidance_intercept_lead_time_s(const Vec3 &relative_target_pos, const Vec3 &target_vel,
                                      double missile_speed_mps, double fallback_time_s) {
    const double missile_speed_sq = missile_speed_mps * missile_speed_mps;
    if (!std::isfinite(missile_speed_sq) || missile_speed_sq <= 1.0) {
        return fallback_time_s;
    }

    const double a = missile_guidance::dot(target_vel, target_vel) - missile_speed_sq;
    const double b = 2.0 * missile_guidance::dot(relative_target_pos, target_vel);
    const double c = missile_guidance::dot(relative_target_pos, relative_target_pos);
    double intercept_time_s = fallback_time_s;

    if (std::abs(a) <= 1.0e-6) {
        if (std::abs(b) > 1.0e-6) {
            const double linear_time_s = -c / b;
            if (linear_time_s > 0.0 && std::isfinite(linear_time_s)) {
                intercept_time_s = linear_time_s;
            }
        }
    } else {
        const double discriminant = b * b - 4.0 * a * c;
        if (discriminant >= 0.0 && std::isfinite(discriminant)) {
            const double sqrt_disc = std::sqrt(discriminant);
            const double t1 = (-b - sqrt_disc) / (2.0 * a);
            const double t2 = (-b + sqrt_disc) / (2.0 * a);
            if (t1 > 0.0 && std::isfinite(t1)) {
                intercept_time_s = t1;
            }
            if (t2 > 0.0 && std::isfinite(t2)) {
                intercept_time_s = intercept_time_s > 0.0 ? std::min(intercept_time_s, t2) : t2;
            }
        }
    }

    return std::clamp(intercept_time_s, 0.0, MissileGuidanceDefaults::kLeadPredictionMaxTimeS);
}

void update_target_kinematics_from_track(Missile &missile, const Transform &transform,
                                         double current_time, double dt) {
    if (!std::isfinite(missile.filtered_range_m) || missile.filtered_range_m <= 1.0e-3) {
        missile.target_kinematics_valid = false;
        return;
    }

    const Vec3 target_pos = guidance_estimated_target_position_world(missile, transform);
    const double elapsed_s = missile.target_kinematics_time_s >= 0.0
                                 ? std::max(0.0, current_time - missile.target_kinematics_time_s)
                                 : 0.0;
    const bool can_differentiate = missile.target_kinematics_valid &&
                                   guidance_target_kinematics_are_finite(missile) &&
                                   elapsed_s > 1.0e-6 && elapsed_s < 2.0;

    if (can_differentiate) {
        const Vec3 previous_pos = {missile.target_track_x_m, missile.target_track_y_m,
                                   missile.target_track_z_m};
        const Vec3 previous_vel = {missile.target_track_vx_mps, missile.target_track_vy_mps,
                                   missile.target_track_vz_mps};
        const Vec3 measured_vel = (target_pos - previous_pos) / elapsed_s;
        const double vel_alpha = std::clamp(
            elapsed_s / (MissileGuidanceDefaults::kTargetKinematicsVelocityFilterTauS + elapsed_s),
            0.0, 1.0);
        const Vec3 filtered_vel = previous_vel + (measured_vel - previous_vel) * vel_alpha;
        const Vec3 measured_accel = (filtered_vel - previous_vel) / elapsed_s;
        const Vec3 previous_accel = {missile.target_track_ax_mps2, missile.target_track_ay_mps2,
                                     missile.target_track_az_mps2};
        const double accel_alpha = std::clamp(
            elapsed_s / (MissileGuidanceDefaults::kTargetKinematicsAccelFilterTauS + elapsed_s),
            0.0, 1.0);
        const Vec3 filtered_accel =
            previous_accel + (measured_accel - previous_accel) * accel_alpha;
        missile.target_track_vx_mps = filtered_vel.x;
        missile.target_track_vy_mps = filtered_vel.y;
        missile.target_track_vz_mps = filtered_vel.z;
        missile.target_track_ax_mps2 = filtered_accel.x;
        missile.target_track_ay_mps2 = filtered_accel.y;
        missile.target_track_az_mps2 = filtered_accel.z;
    } else {
        missile.target_track_vx_mps = 0.0;
        missile.target_track_vy_mps = 0.0;
        missile.target_track_vz_mps = 0.0;
        missile.target_track_ax_mps2 = 0.0;
        missile.target_track_ay_mps2 = 0.0;
        missile.target_track_az_mps2 = 0.0;
    }

    missile.target_track_x_m = target_pos.x;
    missile.target_track_y_m = target_pos.y;
    missile.target_track_z_m = target_pos.z;
    missile.target_kinematics_time_s = current_time;
    missile.target_kinematics_valid = true;
    (void)dt;
}

void update_mass_and_drag_state(flecs::world world, flecs::entity missile_entity,
                                const Transform &transform, Missile &missile, double current_time,
                                double dt, double speed_mps, double lateral_accel_mps2,
                                const GuidanceResolvedTuning &tuning, double &thrust_n,
                                double &drag_n) {
    const EnvironmentModelRef *env_ref = world.get<EnvironmentModelRef>();
    const AtmosphericData atmo = aero_physics::sample_atmosphere(transform, env_ref);

    Mass *mass = missile_entity.get_mut<Mass>();
    if (!mass) {
        thrust_n = 0.0;
        drag_n = 0.0;
        return;
    }

    ensure_mass_state_initialized(missile_entity, tuning.reference_area_m2);
    MassProperties *props = missile_entity.get_mut<MassProperties>();

    const double total_mass = std::max(1.0, mass->get_total_kg());
    const double mach = aero_physics::mach_from_speed(speed_mps, atmo.speed_of_sound);
    const double q_bar = aero_physics::dynamic_pressure(atmo.air_density, speed_mps * speed_mps);
    const double boost_end_time = missile.launch_time + tuning.boost_time_s;
    const bool propulsion_active =
        current_time < missile.burnout_time_s && mass->fuel_mass_kg > 1.0e-6;

    const double mach_frac =
        std::clamp((mach - tuning.mach_transonic_start) /
                       std::max(1.0e-6, tuning.mach_transonic_end - tuning.mach_transonic_start),
                   0.0, 1.0);
    double base_cd =
        aero_physics::lookup_1d_optional(tuning.cd0_mach_breakpoints, tuning.cd0_mach_values, mach,
                                         aero_physics::positive_strict_lookup_validation())
            .value_or(
                missile_guidance::lerp(tuning.cd0_subsonic, tuning.cd0_supersonic, mach_frac));
    if (propulsion_active) {
        base_cd *= tuning.cd0_power_on_ratio;
    }
    const double lateral_frac =
        std::clamp(lateral_accel_mps2 / std::max(1.0, tuning.max_lateral_g * kGravity), 0.0, 1.0);
    const double induced_drag_k =
        aero_physics::lookup_1d_optional(tuning.induced_drag_k_mach_breakpoints,
                                         tuning.induced_drag_k_mach_values, mach,
                                         aero_physics::positive_strict_lookup_validation())
            .value_or(tuning.induced_drag_k);
    const double drag_coeff = base_cd + induced_drag_k * lateral_frac * lateral_frac;
    drag_n = q_bar * tuning.reference_area_m2 * drag_coeff;

    if (propulsion_active) {
        const bool in_boost_phase = current_time < boost_end_time;
        thrust_n = in_boost_phase ? tuning.boost_thrust_n : tuning.sustain_thrust_n;
        if (thrust_n <= 1.0e-6) {
            thrust_n = in_boost_phase
                           ? default_boost_thrust_n(total_mass, missile.max_speed,
                                                    missile.current_speed_mps)
                           : default_sustain_thrust_n(default_boost_thrust_n(
                                 total_mass, missile.max_speed, missile.current_speed_mps));
        }
        const double remaining_burn_s =
            std::max(kBoostMinDurationS, missile.burnout_time_s - current_time + dt);
        const double mass_flow = mass->fuel_mass_kg / remaining_burn_s;
        mass->fuel_mass_kg = std::max(0.0, mass->fuel_mass_kg - mass_flow * dt);
    } else {
        thrust_n = 0.0;
    }

    if (props) {
        sync_missile_mass_properties(*mass, *props, tuning.reference_area_m2);
    }
}

class DefaultGuidanceModel : public IGuidanceModel {
  public:
    void update(flecs::world world, flecs::entity missile_entity, Velocity &velocity,
                const Transform &transform, Missile &missile, double dt) override {
        if (!missile.active) return;

        const ecs_world_info_t *info = ecs_get_world_info(world.c_ptr());
        double current_time = info ? (double)info->world_time_total : 0.0;
        if (missile.launch_time <= 0.0) {
            missile.launch_time = current_time;
        }
        if (missile.max_flight_time_s > 0.0 &&
            (current_time - missile.launch_time) > missile.max_flight_time_s) {
            record_missile_timeout_event(world, missile_entity, transform, velocity, missile,
                                         current_time);
            missile.active = false;
            missile_entity.destruct();
            return;
        }
        if (current_time - missile.launch_time < missile.guidance_delay_s) {
            return;
        }
        if (missile.guidance_update_period_s > 0.0) {
            if (current_time - missile.last_guidance_time < missile.guidance_update_period_s) {
                return;
            }
        }
        missile.last_guidance_time = current_time;
        initialize_runtime_state(missile_entity, missile, velocity, current_time);
        const GuidanceResolvedTuning tuning = resolve_tuning(missile_entity, missile, velocity);
        missile.track_memory_timeout_s = tuning.track_memory_timeout_s;
        missile.terminal_seeker_active = terminal_seeker_is_active(missile);

        const ContactList *contacts = missile_entity.get<ContactList>();
        const Detection *best_det = nullptr;
        double max_sig = -1.0;
        const Alliance *missile_alliance = missile_entity.get<Alliance>();

        if (contacts) {
            for (const auto &c : contacts->contacts) {
                if (c.target_id == missile.attacker_id) {
                    continue;
                }

                const Alliance *target_alliance = world.entity(c.target_id).get<Alliance>();
                if (missile_alliance && target_alliance &&
                    missile_alliance->side == target_alliance->side) {
                    continue;
                }

                if (!detection_is_usable_for_guidance(missile, c)) {
                    continue;
                }
                if (missile.seeker_lock_range > 0.0 && c.range > missile.seeker_lock_range) {
                    continue;
                }
                if (missile.seeker_fov_deg > 0.0 &&
                    std::abs(c.bearing) > missile.seeker_fov_deg * 0.5) {
                    continue;
                }
                if (!c.local_sensor_hit && missile.terminal_seeker_active) {
                    continue;
                }

                if (!detection_matches_assigned_target(missile, c)) {
                    continue;
                }

                if (c.signal_strength > max_sig) {
                    max_sig = c.signal_strength;
                    best_det = &c;
                }
            }
        }

        if (best_det) {
            missile.target_id = best_det->target_id;
            update_track_from_detection(missile, *best_det, current_time, dt, tuning, transform,
                                        velocity);
            if (missile.apn_target_accel_gain > 0.0) {
                update_target_kinematics_from_track(missile, transform, current_time, dt);
            } else {
                missile.target_kinematics_valid = false;
            }
            missile.terminal_seeker_active = terminal_seeker_is_active(missile);
        } else if (missile.seeker_has_valid_track && missile.last_track_time_s >= 0.0 &&
                   (current_time - missile.last_track_time_s) <= tuning.track_memory_timeout_s) {
            propagate_track_memory(missile, dt, transform, velocity);
            missile.terminal_seeker_active = terminal_seeker_is_active(missile);
            missile.target_kinematics_valid = false;
            missile.guidance_lead_time_s = 0.0;
            missile.guidance_lead_blend = 0.0;
            missile.guidance_apn_lateral_accel_mps2 = 0.0;
        } else {
            missile.seeker_mode = static_cast<int>(MissileSeekerMode::Ballistic);
            missile.seeker_has_valid_track = false;
            missile.target_kinematics_valid = false;
            missile.commanded_lateral_accel_mps2 = 0.0;
            missile.guidance_lead_time_s = 0.0;
            missile.guidance_lead_blend = 0.0;
            missile.guidance_apn_lateral_accel_mps2 = 0.0;
            missile.terminal_seeker_active = terminal_seeker_is_active(missile);
        }

        Vec3 velocity_vec = missile_guidance::velocity_to_vec3(velocity);
        double speed_mps = missile_guidance::norm(velocity_vec);
        if (speed_mps < 1.0) {
            speed_mps = std::max(1.0, missile.current_speed_mps);
        }
        Vec3 velocity_dir = missile_guidance::normalize(velocity_vec);
        if (missile_guidance::norm(velocity_dir) <= 1.0e-6) {
            velocity_dir = missile_guidance::world_los_from_relative_angles(0.0, 0.0, transform);
        }

        Vec3 commanded_accel = {0.0, 0.0, 0.0};
        if (missile.seeker_has_valid_track &&
            missile.seeker_mode != static_cast<int>(MissileSeekerMode::Ballistic)) {
            const Vec3 los_world =
                missile_guidance::normalize(missile_guidance::world_los_from_relative_angles(
                    missile.filtered_bearing_deg, missile.filtered_elevation_deg, transform));
            const double range_m = std::max(150.0, missile.filtered_range_m);
            const double closing_speed_mps = std::max(0.0, missile.filtered_closing_speed_mps);
            const double nav_gain = missile.nav_gain > 0.0 ? missile.nav_gain : 3.0;
            const double apn_gain = std::clamp(missile.apn_target_accel_gain, 0.0, 2.0);
            const double lead_terminal_fraction =
                apn_gain > 0.0
                    ? std::clamp(MissileGuidanceDefaults::kLeadBlendTerminalRangeM / range_m, 0.20,
                                 1.0)
                    : 0.0;
            missile.guidance_lead_time_s = 0.0;
            missile.guidance_lead_blend = 0.0;
            missile.guidance_apn_lateral_accel_mps2 = 0.0;

            Vec3 guidance_los_world = los_world;
            const bool target_kinematics_available =
                apn_gain > 0.0 &&
                missile.seeker_mode == static_cast<int>(MissileSeekerMode::Track) &&
                missile.target_kinematics_valid && guidance_target_kinematics_are_finite(missile);
            if (target_kinematics_available) {
                const Vec3 missile_pos = {transform.x, transform.y, transform.z};
                const Vec3 target_pos = {missile.target_track_x_m, missile.target_track_y_m,
                                         missile.target_track_z_m};
                const Vec3 target_vel = {missile.target_track_vx_mps, missile.target_track_vy_mps,
                                         missile.target_track_vz_mps};
                const Vec3 target_accel = {missile.target_track_ax_mps2,
                                           missile.target_track_ay_mps2,
                                           missile.target_track_az_mps2};
                const Vec3 relative_target_pos = target_pos - missile_pos;
                const double fallback_lead_time_s =
                    guidance_fallback_lead_time_s(range_m, closing_speed_mps, speed_mps);
                const double lead_time_s = guidance_intercept_lead_time_s(
                    relative_target_pos, target_vel, speed_mps, fallback_lead_time_s);
                const Vec3 predicted_target = target_pos + target_vel * lead_time_s +
                                              target_accel * (0.5 * lead_time_s * lead_time_s);
                const Vec3 lead_los_world =
                    missile_guidance::normalize(predicted_target - missile_pos);
                if (missile_guidance::norm(lead_los_world) > 1.0e-6) {
                    const double lead_blend =
                        MissileGuidanceDefaults::kLeadBlendMax * lead_terminal_fraction;
                    guidance_los_world = missile_guidance::normalize(
                        los_world * (1.0 - lead_blend) + lead_los_world * lead_blend);
                    missile.guidance_lead_time_s = lead_time_s;
                    missile.guidance_lead_blend = lead_blend;
                }
            }

            const Vec3 los_lateral =
                missile_guidance::project_lateral(guidance_los_world, velocity_dir);
            const Vec3 los_lateral_dir = missile_guidance::normalize(los_lateral);
            const double lateral_error = std::clamp(missile_guidance::norm(los_lateral), 0.0, 1.0);
            const double terminal_weight =
                std::clamp(MissileGuidanceDefaults::kTerminalCaptureRangeM / range_m, 0.25, 2.5);

            const double capture_mag = MissileGuidanceDefaults::kCaptureGain * terminal_weight *
                                       (speed_mps * speed_mps / range_m) * lateral_error;

            const Math::Vector3 pn_body_world = Math::body_to_world(
                {
                    0.0,
                    -MissileGuidanceDefaults::kPnGainScale * nav_gain * closing_speed_mps *
                        Math::to_radians(missile.bearing_rate_deg_s),
                    MissileGuidanceDefaults::kPnGainScale * nav_gain * closing_speed_mps *
                        Math::to_radians(missile.elevation_rate_deg_s),
                },
                transform);
            const Vec3 pn_world = {
                pn_body_world.x,
                pn_body_world.y,
                pn_body_world.z,
            };

            commanded_accel = (los_lateral_dir * capture_mag) + pn_world;

            const double apn_limit = tuning.max_lateral_g * kGravity *
                                     MissileGuidanceDefaults::kApnAccelLimitFraction *
                                     std::min(1.0, std::max(0.25, apn_gain));
            if (target_kinematics_available) {
                const Vec3 target_accel = {missile.target_track_ax_mps2,
                                           missile.target_track_ay_mps2,
                                           missile.target_track_az_mps2};
                Vec3 apn_world = missile_guidance::project_lateral(target_accel, velocity_dir) *
                                 (apn_gain * lead_terminal_fraction);
                const double apn_mag = missile_guidance::norm(apn_world);
                if (apn_mag > apn_limit && apn_mag > 1.0e-6) {
                    apn_world = missile_guidance::normalize(apn_world) * apn_limit;
                }
                missile.guidance_apn_lateral_accel_mps2 = missile_guidance::norm(apn_world);
                commanded_accel = commanded_accel + apn_world;
            } else if (apn_gain > 0.0 && missile.apn_rate_history_valid && dt > 1.0e-6) {
                const double raw_bearing_accel_rad_s2 =
                    (missile.bearing_rate_deg_s - missile.prev_bearing_rate_deg_s) / dt * M_PI /
                    180.0;
                const double raw_elevation_accel_rad_s2 =
                    (missile.elevation_rate_deg_s - missile.prev_elevation_rate_deg_s) / dt * M_PI /
                    180.0;
                const double tau_s = MissileGuidanceDefaults::kApnAccelFilterTauS;
                missile.filtered_bearing_accel_rad_s2 = missile_guidance::exp_smooth(
                    missile.filtered_bearing_accel_rad_s2, raw_bearing_accel_rad_s2, tau_s, dt);
                missile.filtered_elevation_accel_rad_s2 = missile_guidance::exp_smooth(
                    missile.filtered_elevation_accel_rad_s2, raw_elevation_accel_rad_s2, tau_s, dt);
                const double apn_scale = MissileGuidanceDefaults::kPnGainScale * nav_gain *
                                         apn_gain * lead_terminal_fraction;
                const Math::Vector3 apn_body_world = Math::body_to_world(
                    {
                        0.0,
                        -apn_scale * range_m * missile.filtered_bearing_accel_rad_s2,
                        apn_scale * range_m * missile.filtered_elevation_accel_rad_s2,
                    },
                    transform);
                Vec3 apn_world = {apn_body_world.x, apn_body_world.y, apn_body_world.z};
                const double apn_mag = missile_guidance::norm(apn_world);
                if (apn_mag > apn_limit && apn_mag > 1.0e-6) {
                    apn_world = missile_guidance::normalize(apn_world) * apn_limit;
                }
                missile.guidance_apn_lateral_accel_mps2 = missile_guidance::norm(apn_world);
                commanded_accel = commanded_accel + apn_world;
            }
            missile.prev_bearing_rate_deg_s = missile.bearing_rate_deg_s;
            missile.prev_elevation_rate_deg_s = missile.elevation_rate_deg_s;
            missile.apn_rate_history_valid = true;

            commanded_accel = missile_guidance::project_lateral(commanded_accel, velocity_dir);
        }

        missile.commanded_lateral_accel_mps2 = missile_guidance::norm(commanded_accel);
        const double max_lateral_accel = tuning.max_lateral_g * kGravity;
        if (missile.commanded_lateral_accel_mps2 > max_lateral_accel) {
            commanded_accel = missile_guidance::normalize(commanded_accel) * max_lateral_accel;
            missile.commanded_lateral_accel_mps2 = max_lateral_accel;
        }

        const double accel_step_limit =
            tuning.max_accel_response_g_per_s * kGravity * std::max(0.0, dt);
        const double desired_delta =
            std::clamp(missile.commanded_lateral_accel_mps2 - missile.achieved_lateral_accel_mps2,
                       -accel_step_limit, accel_step_limit);
        const double accel_target = missile.achieved_lateral_accel_mps2 + desired_delta;

        if (tuning.autopilot_order >= 2) {
            const double omega_n = 1.0 / std::max(0.001, tuning.autopilot_tau_s);
            const double zeta = std::clamp(tuning.autopilot_damping, 0.1, 2.0);
            const double x1 = missile.autopilot_filter_state_mps2;
            const double x2 = missile.autopilot_rate_state_mps3;
            missile.autopilot_rate_state_mps3 =
                x2 + dt * (omega_n * omega_n * (accel_target - x1) - 2.0 * zeta * omega_n * x2);
            missile.autopilot_filter_state_mps2 =
                std::clamp(x1 + dt * missile.autopilot_rate_state_mps3, 0.0, max_lateral_accel);

            if (tuning.autopilot_order >= 3) {
                // First-order actuator lag (~30 Hz bandwidth) after second-order filter.
                const double act_alpha =
                    std::clamp(dt / (MissileGuidanceDefaults::kActuatorTauS + dt), 0.0, 1.0);
                missile.autopilot_actuator_state_mps2 +=
                    act_alpha *
                    (missile.autopilot_filter_state_mps2 - missile.autopilot_actuator_state_mps2);
                missile.achieved_lateral_accel_mps2 = missile.autopilot_actuator_state_mps2;
            } else {
                missile.autopilot_actuator_state_mps2 = missile.autopilot_filter_state_mps2;
                missile.achieved_lateral_accel_mps2 = missile.autopilot_filter_state_mps2;
            }
        } else {
            const double autopilot_alpha = std::clamp(dt / (tuning.autopilot_tau_s + dt), 0.0, 1.0);
            missile.achieved_lateral_accel_mps2 +=
                autopilot_alpha * (accel_target - missile.achieved_lateral_accel_mps2);
            missile.autopilot_filter_state_mps2 = missile.achieved_lateral_accel_mps2;
            missile.autopilot_rate_state_mps3 = 0.0;
            missile.autopilot_actuator_state_mps2 = missile.achieved_lateral_accel_mps2;
        }
        missile.achieved_lateral_accel_mps2 =
            std::clamp(missile.achieved_lateral_accel_mps2, 0.0, max_lateral_accel);
        missile.autopilot_actuator_state_mps2 =
            std::clamp(missile.autopilot_actuator_state_mps2, 0.0, max_lateral_accel);
        if (tuning.autopilot_order < 3) {
            missile.autopilot_filter_state_mps2 = missile.achieved_lateral_accel_mps2;
        }

        Vec3 achieved_lateral_accel = {0.0, 0.0, 0.0};
        const double commanded_mag = missile_guidance::norm(commanded_accel);
        if (commanded_mag > 1.0e-6 && missile.achieved_lateral_accel_mps2 > 1.0e-6) {
            achieved_lateral_accel =
                missile_guidance::normalize(commanded_accel) * missile.achieved_lateral_accel_mps2;
        }

        double thrust_n = 0.0;
        double drag_n = 0.0;
        update_mass_and_drag_state(world, missile_entity, transform, missile, current_time, dt,
                                   speed_mps, missile.achieved_lateral_accel_mps2, tuning, thrust_n,
                                   drag_n);

        velocity_dir = missile_guidance::norm(velocity_vec) > 1.0e-6
                           ? missile_guidance::normalize(velocity_vec)
                           : velocity_dir;
        const double total_mass = [&]() {
            const Mass *mass = missile_entity.get<Mass>();
            return mass ? std::max(1.0, mass->get_total_kg()) : 80.0;
        }();
        const double tangential_accel = (thrust_n - drag_n) / total_mass;
        Vec3 new_velocity =
            velocity_vec + (achieved_lateral_accel + velocity_dir * tangential_accel) * dt;

        const double new_speed_mag = missile_guidance::norm(new_velocity);
        const double peak_cap = std::max(200.0, missile.max_speed * 1.05);
        if (new_speed_mag > peak_cap) {
            new_velocity = missile_guidance::normalize(new_velocity) * peak_cap;
        } else if (new_speed_mag < 5.0 && speed_mps > 5.0) {
            new_velocity = velocity_dir * 5.0;
        }

        missile_guidance::write_velocity(velocity, new_velocity);
        missile.current_speed_mps = missile_guidance::norm(new_velocity);
    }
};

} // namespace

std::unique_ptr<IGuidanceModel> make_default_guidance_model() {
    return std::make_unique<DefaultGuidanceModel>();
}
