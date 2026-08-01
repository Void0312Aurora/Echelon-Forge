#include "tests/test_cuda_resident_replay_support.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

#include "runtime/contracts/cuda_resident_phase_d_fixture_contract.h"

namespace runtime::cuda_resident::replay::test_support {

using runtime::cuda_resident::DeviceClockContract;
using runtime::cuda_resident::ExportEnvelopeContract;
using runtime::cuda_resident::ShardVersionContract;
using runtime::cuda_resident::SnapshotIdentityContract;
using runtime::cuda_resident::replay::ReplayFieldValue;
using runtime::cuda_resident::replay::ReplayLaneFrame;
using runtime::cuda_resident::replay::ReplayTrace;
using runtime::parity::ParityBudgetValueKind;

namespace {

void add_value(ReplayLaneFrame &frame, std::size_t world, std::string_view family,
               std::string_view path, ParityBudgetValueKind kind, std::string canonical,
               bool numeric = false, double numeric_value = 0.0) {
    frame.fields.push_back({
        .world_index = world,
        .field_family = std::string(family),
        .field_path = std::string(path),
        .value_kind = kind,
        .available = true,
        .numeric = numeric,
        .numeric_value = numeric_value,
        .canonical_value = std::move(canonical),
    });
}

void add_double(ReplayLaneFrame &frame, std::size_t world, std::string_view family,
                std::string_view path, double value) {
    add_value(frame, world, family, path, ParityBudgetValueKind::float64,
              runtime::cuda_resident::replay::replay_canonical_double(value), true, value);
}

void add_float(ReplayLaneFrame &frame, std::size_t world, std::string_view family,
               std::string_view path, float value) {
    add_value(frame, world, family, path, ParityBudgetValueKind::float32,
              runtime::cuda_resident::replay::replay_canonical_float(value), true,
              static_cast<double>(value));
}

void add_uint(ReplayLaneFrame &frame, std::size_t world, std::string_view family,
              std::string_view path, std::uint64_t value) {
    add_value(frame, world, family, path, ParityBudgetValueKind::unsigned_integer,
              std::to_string(value));
}

void add_int(ReplayLaneFrame &frame, std::size_t world, std::string_view family,
             std::string_view path, int value) {
    add_value(frame, world, family, path, ParityBudgetValueKind::signed_integer,
              std::to_string(value));
}

void add_bool(ReplayLaneFrame &frame, std::size_t world, std::string_view family,
              std::string_view path, bool value) {
    add_value(frame, world, family, path, ParityBudgetValueKind::boolean,
              runtime::cuda_resident::replay::replay_canonical_bool(value));
}

void add_string(ReplayLaneFrame &frame, std::size_t world, std::string_view family,
                std::string_view path, std::string_view value) {
    add_value(frame, world, family, path, ParityBudgetValueKind::string, std::string(value));
}

void add_structured(ReplayLaneFrame &frame, std::size_t world, std::string_view family,
                    std::string_view path, std::string value) {
    add_value(frame, world, family, path, ParityBudgetValueKind::structured,
              std::move(value));
}

std::string canonical_shard_versions(const std::vector<ShardVersionContract> &versions) {
    std::string value;
    for (const auto &version : versions) {
        value += version.shard_id;
        value.push_back('=');
        value += std::to_string(version.version);
        value.push_back(';');
    }
    return value;
}

std::string canonical_lineage(const SnapshotIdentityContract &snapshot) {
    return std::to_string(snapshot.lineage.source_snapshot_version) + "|" +
           snapshot.lineage.source_backend_id + "|" + snapshot.lineage.source_request_id;
}

std::string canonical_field_set(const std::vector<std::string> &fields) {
    std::string value;
    for (const auto &field : fields) {
        value += field;
        value.push_back(';');
    }
    return value;
}

std::vector<ShardVersionContract> expected_shard_versions(std::size_t window) {
    using namespace runtime::cuda_resident;
    const std::uint64_t global_version = 3 + static_cast<std::uint64_t>(window) * 2;
    const std::uint64_t legacy_version = 2 + static_cast<std::uint64_t>(window);
    const std::uint64_t control_version = 2 + static_cast<std::uint64_t>(window);
    const std::uint64_t phase_d_version = 1 + static_cast<std::uint64_t>(window);
    std::vector<ShardVersionContract> versions;
    versions.reserve(kCudaResidentShardCount);
    for (std::size_t shard = 0; shard < kCudaResidentShardCount; ++shard) {
        std::uint64_t version = legacy_version;
        if (shard == static_cast<std::size_t>(CudaResidentShard::identity)) {
            version = global_version;
        } else if (shard == static_cast<std::size_t>(CudaResidentShard::pilot_flight_controls)) {
            version = control_version;
        } else if (shard >= static_cast<std::size_t>(CudaResidentShard::instrument) &&
                   shard <= static_cast<std::size_t>(CudaResidentShard::events)) {
            version = phase_d_version;
        } else if (shard == static_cast<std::size_t>(CudaResidentShard::export_envelope)) {
            version = global_version;
        }
        versions.push_back({.shard_id = std::string(kCudaResidentShardIds[shard]),
                            .version = version});
    }
    return versions;
}

ProjectedWorld make_projection_metadata(std::size_t world, std::uint64_t entity_id,
                                        std::size_t window, std::string_view barrier_id,
                                        std::string_view backend_id,
                                        std::string_view request_id,
                                        std::string_view provenance) {
    using namespace runtime::cuda_resident;
    ProjectedWorld projected{};
    const std::uint64_t global_version = 3 + static_cast<std::uint64_t>(window) * 2;
    const std::uint64_t window_sequence = 5 + static_cast<std::uint64_t>(window) * 3;
    projected.ref = {.world_index = world, .entity_id = entity_id};
    projected.clock.tick = static_cast<std::uint64_t>(window + 1);
    projected.snapshot.world_id = world;
    projected.snapshot.global_version = global_version;
    projected.snapshot.barrier_id = std::string(barrier_id);
    projected.snapshot.barrier_sequence =
        window_sequence + (barrier_id == "export" ? 1U : 0U);
    projected.snapshot.shard_versions = expected_shard_versions(window);
    projected.snapshot.lineage = {
        .source_snapshot_version = global_version,
        .source_backend_id = std::string(backend_id),
        .source_request_id = std::string(request_id),
    };
    projected.envelope.schema_version = std::string(kCudaResidentPhaseDSnapshotSchemaV3);
    projected.envelope.field_set = {
        "entity_ref", "seed",       "reset_generation", "clock",
        "snapshot",   "kinematics", "dynamics",         "instrument",
        "observation", "reward",    "termination",       "events",
        "source_barrier_id",
    };
    projected.envelope.visibility_label = "export";
    projected.envelope.provenance = std::string(provenance);
    projected.envelope.source_snapshot_version = global_version;
    return projected;
}

void append_input_fields(ReplayLaneFrame &frame, std::size_t world, std::uint64_t entity_id,
                         const PilotAction &action) {
    using namespace runtime::cuda_resident;
    add_uint(frame, world, "input_identity", "pilot_action.world_index", world);
    add_uint(frame, world, "input_identity", "pilot_action.entity_id", entity_id);
    add_bool(frame, world, "input_identity", "pilot_action.action.active", action.active);
    add_double(frame, world, "pilot_flight_controls", "pilot_action.action.stick_pitch",
               action.stick_pitch);
    add_double(frame, world, "pilot_flight_controls", "pilot_action.action.stick_roll",
               action.stick_roll);
    add_double(frame, world, "pilot_flight_controls", "pilot_action.action.rudder", action.rudder);
    add_double(frame, world, "pilot_flight_controls", "pilot_action.action.throttle",
               action.throttle);
    add_float(frame, world, "pilot_flight_controls", "pilot_action.action.gear_handle",
              action.gear_handle);
    add_float(frame, world, "pilot_flight_controls", "pilot_action.action.flaps", action.flaps);
    add_float(frame, world, "pilot_flight_controls", "pilot_action.action.speedbrake",
              action.speedbrake);
    add_double(frame, world, "pilot_flight_controls", "pilot_action.action.brake", action.brake);
    add_bool(frame, world, "pilot_flight_controls", "pilot_action.action.brake_left",
             action.brake_left);
    add_bool(frame, world, "pilot_flight_controls", "pilot_action.action.brake_right",
             action.brake_right);
}

void append_projection_fields(ReplayLaneFrame &frame, const ProjectedWorld &projected) {
    using namespace runtime::cuda_resident;
    const std::size_t world = static_cast<std::size_t>(projected.ref.world_index);
    add_uint(frame, world, "world_identity_clock_and_versions", "entity_ref.world_index",
             projected.ref.world_index);
    add_uint(frame, world, "world_identity_clock_and_versions", "entity_ref.entity_id",
             projected.ref.entity_id);
    add_uint(frame, world, "world_identity_clock_and_versions", "clock.tick",
             projected.clock.tick);
    add_double(frame, world, "world_identity_clock_and_versions", "clock.simulation_time_s",
               projected.clock.simulation_time_s);
    add_uint(frame, world, "world_identity_clock_and_versions", "snapshot.world_id",
             projected.snapshot.world_id);
    add_uint(frame, world, "world_identity_clock_and_versions", "snapshot.global_version",
             projected.snapshot.global_version);
    add_string(frame, world, "world_identity_clock_and_versions", "snapshot.barrier_id",
               projected.snapshot.barrier_id);
    add_uint(frame, world, "world_identity_clock_and_versions", "snapshot.barrier_sequence",
             projected.snapshot.barrier_sequence);
    add_structured(frame, world, "world_identity_clock_and_versions", "snapshot.shard_versions",
                    canonical_shard_versions(projected.snapshot.shard_versions));
    add_structured(frame, world, "world_identity_clock_and_versions", "snapshot.lineage",
                   canonical_lineage(projected.snapshot));

    add_double(frame, world, "airframe_kinematics", "kinematics.x", projected.kinematics.x);
    add_double(frame, world, "airframe_kinematics", "kinematics.y", projected.kinematics.y);
    add_double(frame, world, "airframe_kinematics", "kinematics.z", projected.kinematics.z);
    add_double(frame, world, "airframe_kinematics", "kinematics.vx", projected.kinematics.vx);
    add_double(frame, world, "airframe_kinematics", "kinematics.vy", projected.kinematics.vy);
    add_double(frame, world, "airframe_kinematics", "kinematics.vz", projected.kinematics.vz);
    add_double(frame, world, "airframe_kinematics", "kinematics.heading",
               projected.kinematics.heading);
    add_double(frame, world, "airframe_kinematics", "kinematics.pitch", projected.kinematics.pitch);
    add_double(frame, world, "airframe_kinematics", "kinematics.roll", projected.kinematics.roll);

    const auto &instrument = projected.instrument;
    add_double(frame, world, "air_execution_instruments", "instrument.alt_baro_m",
               instrument.alt_baro_m);
    add_double(frame, world, "air_execution_instruments", "instrument.alt_radar_m",
               instrument.alt_radar_m);
    add_double(frame, world, "air_execution_instruments", "instrument.ias_mps", instrument.ias_mps);
    add_double(frame, world, "air_execution_instruments", "instrument.mach", instrument.mach);
    add_double(frame, world, "air_execution_instruments", "instrument.vvi_mps", instrument.vvi_mps);
    add_double(frame, world, "air_execution_instruments", "instrument.pitch_deg",
               instrument.pitch_deg);
    add_double(frame, world, "air_execution_instruments", "instrument.roll_deg",
               instrument.roll_deg);
    add_double(frame, world, "air_execution_instruments", "instrument.heading_deg",
               instrument.heading_deg);
    add_double(frame, world, "air_execution_instruments", "instrument.aoa_deg", instrument.aoa_deg);
    add_double(frame, world, "air_execution_instruments", "instrument.beta_deg", instrument.beta_deg);
    add_double(frame, world, "air_execution_instruments", "instrument.g_load_normal",
               instrument.g_load_normal);
    add_double(frame, world, "air_execution_instruments", "instrument.g_load_axial",
               instrument.g_load_axial);
    add_double(frame, world, "air_execution_instruments", "instrument.p_deg_s", instrument.p_deg_s);
    add_double(frame, world, "air_execution_instruments", "instrument.q_deg_s", instrument.q_deg_s);
    add_double(frame, world, "air_execution_instruments", "instrument.r_deg_s", instrument.r_deg_s);
    add_double(frame, world, "air_execution_instruments", "instrument.engine_rpm_pct",
               instrument.engine_rpm_pct);
    add_double(frame, world, "air_execution_instruments", "instrument.fuel_flow_kg_h",
               instrument.fuel_flow_kg_h);
    add_double(frame, world, "air_execution_instruments", "instrument.throttle_pos",
               instrument.throttle_pos);
    add_double(frame, world, "air_execution_instruments", "instrument.fuel_internal_kg",
               instrument.fuel_internal_kg);
    add_double(frame, world, "air_execution_instruments", "instrument.fuel_external_kg",
               instrument.fuel_external_kg);
    add_float(frame, world, "air_execution_instruments", "instrument.gear_pos",
              static_cast<float>(instrument.gear_pos));
    add_float(frame, world, "air_execution_instruments", "instrument.flaps_pos",
              static_cast<float>(instrument.flaps_pos));
    add_float(frame, world, "air_execution_instruments", "instrument.speedbrake_pos",
              static_cast<float>(instrument.speedbrake_pos));

    const auto &observation = projected.observation;
    add_uint(frame, world, "agent_observation_identity", "observation.id", observation.id);
    add_double(frame, world, "agent_observation_numeric", "observation.sim_time",
               observation.sim_time);
    add_double(frame, world, "agent_observation_numeric", "observation.x", observation.x);
    add_double(frame, world, "agent_observation_numeric", "observation.y", observation.y);
    add_double(frame, world, "agent_observation_numeric", "observation.z", observation.z);
    add_double(frame, world, "agent_observation_numeric", "observation.vx", observation.vx);
    add_double(frame, world, "agent_observation_numeric", "observation.vy", observation.vy);
    add_double(frame, world, "agent_observation_numeric", "observation.vz", observation.vz);
    add_double(frame, world, "agent_observation_numeric", "observation.heading",
               observation.heading);
    add_double(frame, world, "agent_observation_numeric", "observation.pitch", observation.pitch);
    add_double(frame, world, "agent_observation_numeric", "observation.roll", observation.roll);
    add_double(frame, world, "agent_observation_numeric", "observation.speed", observation.speed);
    add_double(frame, world, "agent_observation_numeric", "observation.health", observation.health);
    add_double(frame, world, "agent_observation_numeric", "observation.gear_state",
               observation.gear_state);
    add_double(frame, world, "agent_observation_numeric", "observation.throttle",
               observation.throttle);
    add_double(frame, world, "agent_observation_numeric", "observation.total_reward",
               observation.total_reward);

    add_double(frame, world, "reward_numeric", "execution_episode_step.reward_total",
               projected.total_reward);
    add_double(frame, world, "reward_numeric", "reward_report.fact_terms[].value",
               projected.survival_reward);
    add_double(frame, world, "reward_numeric", "reward_report.shaping_terms[].value",
               projected.speed_reward);
    add_string(frame, world, "reward_termination_identity", "reward_report.fact_terms[].name",
               kPhaseDRewardTermNames[0]);
    add_string(frame, world, "reward_termination_identity", "reward_report.fact_terms[].term_owner",
               kPhaseDRewardTermOwners[0]);
    add_string(frame, world, "reward_termination_identity", "reward_report.shaping_terms[].name",
               kPhaseDRewardTermNames[1]);
    add_string(frame, world,
               "reward_termination_identity", "reward_report.shaping_terms[].term_owner",
               kPhaseDRewardTermOwners[1]);
    add_uint(frame, world, "reward_termination_identity", "reward_report.fact_snapshot_version",
             projected.reward_snapshot_version);
    add_bool(frame, world, "reward_termination_identity", "execution_episode_step.terminated",
             projected.terminated);
    add_bool(frame, world, "reward_termination_identity", "execution_episode_step.truncated",
             projected.truncated);
    add_string(frame, world, "reward_termination_identity", "termination_spec.reason",
               projected.termination_reason);
    add_string(frame, world, "reward_termination_identity", "termination_spec.reason_source",
               projected.termination_reason_source);
    add_uint(frame, world, "reward_termination_identity", "termination_spec.snapshot_version",
             projected.termination_snapshot_version);

    add_value(frame, world, "exact_event_identity", "events.timestamp",
              ParityBudgetValueKind::float64, "[]");
    add_value(frame, world, "exact_event_identity", "events.priority",
              ParityBudgetValueKind::signed_integer, "[]");
    add_value(frame, world, "exact_event_identity", "events.event_id",
              ParityBudgetValueKind::unsigned_integer, "[]");
    add_value(frame, world, "exact_event_identity", "events.event_family_membership",
              ParityBudgetValueKind::string, "[]");
    add_string(frame, world, "exact_export_envelope", "export.schema_version",
               projected.envelope.schema_version);
    add_structured(frame, world, "exact_export_envelope", "export.field_set",
                   canonical_field_set(projected.envelope.field_set));
    add_string(frame, world, "exact_export_envelope", "export.visibility_label",
               projected.envelope.visibility_label);
    add_string(frame, world, "exact_export_envelope", "export.provenance",
               projected.envelope.provenance);
    add_uint(frame, world, "exact_export_envelope", "export.source_snapshot_version",
             projected.envelope.source_snapshot_version);
}

InstrumentState to_public_instrument(
    const runtime::cuda_resident::CudaWorldInstrumentState &source) {
    InstrumentState result{};
    result.alt_baro_m = source.alt_baro_m;
    result.alt_radar_m = source.alt_radar_m;
    result.ias_mps = source.ias_mps;
    result.mach = source.mach;
    result.vvi_mps = source.vvi_mps;
    result.pitch_deg = source.pitch_deg;
    result.roll_deg = source.roll_deg;
    result.heading_deg = source.heading_deg;
    result.aoa_deg = source.aoa_deg;
    result.beta_deg = source.beta_deg;
    result.g_load_normal = source.g_load_normal;
    result.g_load_axial = source.g_load_axial;
    result.p_deg_s = source.p_deg_s;
    result.q_deg_s = source.q_deg_s;
    result.r_deg_s = source.r_deg_s;
    result.engine_rpm_pct = source.engine_rpm_pct;
    result.fuel_flow_kg_h = source.fuel_flow_kg_h;
    result.throttle_pos = source.throttle_pos;
    result.fuel_internal_kg = source.fuel_internal_kg;
    result.fuel_external_kg = source.fuel_external_kg;
    result.gear_pos = static_cast<float>(source.gear_pos);
    result.flaps_pos = static_cast<float>(source.flaps_pos);
    result.speedbrake_pos = static_cast<float>(source.speedbrake_pos);
    return result;
}

AgentObservation to_public_observation(
    const runtime::cuda_resident::CudaWorldObservationState &source) {
    AgentObservation result{};
    result.id = source.id;
    result.sim_time = source.sim_time;
    result.x = source.x;
    result.y = source.y;
    result.z = source.z;
    result.vx = source.vx;
    result.vy = source.vy;
    result.vz = source.vz;
    result.heading = source.heading;
    result.pitch = source.pitch;
    result.roll = source.roll;
    result.speed = source.speed;
    result.health = source.health;
    result.gear_state = source.gear_state;
    result.throttle = source.throttle;
    result.total_reward = source.total_reward;
    return result;
}

runtime::backend::EntityKinematics to_public_kinematics(
    const runtime::cuda_resident::CudaWorldKinematicsState &source) {
    return {
        .x = source.x,
        .y = source.y,
        .z = source.z,
        .vx = source.vx,
        .vy = source.vy,
        .vz = source.vz,
        .heading = source.heading,
        .pitch = source.pitch,
        .roll = source.roll,
    };
}

void derive_cpu_reward_and_termination(ProjectedWorld &projected) {
    using namespace runtime::cuda_resident;
    const double speed = projected.observation.speed;
    projected.survival_reward = kPhaseDSurvivalReward;
    projected.speed_reward = phase_d_speed_reward(speed);
    projected.total_reward = projected.survival_reward + projected.speed_reward;
    projected.reward_snapshot_version = projected.snapshot.global_version;
    const bool finite = std::isfinite(speed) && std::isfinite(projected.observation.z) &&
                        std::isfinite(projected.observation.pitch) &&
                        std::isfinite(projected.observation.roll);
    const bool envelope = projected.observation.z < 100.0 || projected.observation.z > 10000.0 ||
                          speed < 50.0 || speed > 350.0 ||
                          std::abs(projected.observation.vy) > 50.0 ||
                          std::abs(projected.observation.vz) > 50.0 ||
                          std::abs(projected.observation.pitch) > 10.0 ||
                          std::abs(projected.observation.roll) > 10.0;
    projected.terminated = !finite || envelope;
    projected.truncated = false;
    projected.termination_reason = !finite ? "nan_guard"
                                           : (envelope ? "envelope_violation" : "running");
    projected.termination_reason_source = "cuda_resident.phase_d";
    projected.termination_snapshot_version = projected.snapshot.global_version;
}

} // namespace

ProjectedWorld project_cuda_state(const runtime::cuda_resident::CudaWorldResidentState &state,
                                  std::size_t window, std::string_view barrier_id,
                                  std::string_view request_id) {
    using namespace runtime::cuda_resident;
    ProjectedWorld projected = make_projection_metadata(
        static_cast<std::size_t>(state.world_index), state.entity_id, window, barrier_id,
        kCudaResidentRb7BackendId, request_id, kCudaResidentPhaseDSnapshotProvenance);
    projected.clock = {.tick = state.clock_tick, .simulation_time_s = state.simulation_time_s};
    projected.snapshot.global_version = state.global_version;
    projected.snapshot.barrier_sequence =
        state.barrier_sequence + (barrier_id == "export" ? 1U : 0U);
    projected.snapshot.shard_versions.clear();
    for (std::size_t shard = 0; shard < kCudaResidentShardCount; ++shard) {
        std::uint64_t version = state.shard_versions[shard];
        if (shard == static_cast<std::size_t>(CudaResidentShard::export_envelope)) {
            version = state.global_version;
        }
        projected.snapshot.shard_versions.push_back(
            {.shard_id = std::string(kCudaResidentShardIds[shard]), .version = version});
    }
    projected.kinematics = to_public_kinematics(state.kinematics);
    projected.instrument = to_public_instrument(state.phase_d.instrument);
    projected.observation = to_public_observation(state.phase_d.observation);
    projected.survival_reward = state.phase_d.reward.survival_term;
    projected.speed_reward = state.phase_d.reward.speed_term;
    projected.total_reward = state.phase_d.reward.total_reward;
    projected.reward_snapshot_version = state.phase_d.reward.fact_snapshot_version;
    projected.terminated = state.phase_d.termination.terminated;
    projected.truncated = state.phase_d.termination.truncated;
    switch (state.phase_d.termination.reason_code) {
    case CudaResidentTerminationCode::running:
        projected.termination_reason = "running";
        break;
    case CudaResidentTerminationCode::nan_guard:
        projected.termination_reason = "nan_guard";
        break;
    case CudaResidentTerminationCode::envelope_violation:
        projected.termination_reason = "envelope_violation";
        break;
    }
    projected.termination_reason_source = "cuda_resident.phase_d";
    projected.termination_snapshot_version = state.phase_d.termination.snapshot_version;
    return projected;
}

ProjectedWorld project_cuda_snapshot(
    const runtime::cuda_resident::CudaResidentWorldSnapshot &snapshot, std::size_t window,
    std::string_view request_id) {
    using namespace runtime::cuda_resident;
    ProjectedWorld projected = make_projection_metadata(
        static_cast<std::size_t>(snapshot.entity_ref.world_index), snapshot.entity_ref.entity_id,
        window, "export", kCudaResidentRb7BackendId, request_id,
        kCudaResidentPhaseDSnapshotProvenance);
    projected.ref = snapshot.entity_ref;
    projected.clock = snapshot.clock;
    projected.snapshot = snapshot.identity;
    projected.kinematics = to_public_kinematics(snapshot.kinematics);
    projected.instrument = to_public_instrument(snapshot.phase_d.instrument);
    projected.observation = to_public_observation(snapshot.phase_d.observation);
    projected.survival_reward = snapshot.phase_d.reward.survival_term;
    projected.speed_reward = snapshot.phase_d.reward.speed_term;
    projected.total_reward = snapshot.phase_d.reward.total_reward;
    projected.reward_snapshot_version = snapshot.phase_d.reward.fact_snapshot_version;
    projected.terminated = snapshot.phase_d.termination.terminated;
    projected.truncated = snapshot.phase_d.termination.truncated;
    switch (snapshot.phase_d.termination.reason_code) {
    case CudaResidentTerminationCode::running:
        projected.termination_reason = "running";
        break;
    case CudaResidentTerminationCode::nan_guard:
        projected.termination_reason = "nan_guard";
        break;
    case CudaResidentTerminationCode::envelope_violation:
        projected.termination_reason = "envelope_violation";
        break;
    }
    projected.termination_reason_source = "cuda_resident.phase_d";
    projected.termination_snapshot_version = snapshot.phase_d.termination.snapshot_version;
    projected.envelope = snapshot.identity.global_version == 0
                             ? projected.envelope
                             : projected.envelope;
    return projected;
}

ProjectedWorld project_cpu_oracle(const ReplayTrace &trace, std::size_t world,
                                  std::uint64_t entity_id, std::size_t window,
                                  std::string_view barrier_id, std::string_view request_id) {
    using namespace runtime::cuda_resident;
    ProjectedWorld projected = make_projection_metadata(
        world, entity_id, window, barrier_id, "fixed_air_cpu_fixture_oracle", request_id,
        "fixed_air_cpu_fixture_oracle.rb8.diagnostics_only");
    const auto &expected = kCudaResidentPhaseBFirstExpected[world];
    projected.kinematics = {
        .x = expected.kinematics[0],
        .y = expected.kinematics[1],
        .z = expected.kinematics[2],
        .vx = expected.kinematics[3],
        .vy = expected.kinematics[4],
        .vz = expected.kinematics[5],
        .heading = expected.kinematics[6],
        .pitch = expected.kinematics[7],
        .roll = expected.kinematics[8],
    };
    const double speed = std::sqrt(projected.kinematics.vx * projected.kinematics.vx +
                                   projected.kinematics.vy * projected.kinematics.vy +
                                   projected.kinematics.vz * projected.kinematics.vz);
    constexpr double radians_to_degrees = 57.2957795130823208768;
    projected.instrument.alt_baro_m = projected.kinematics.z;
    projected.instrument.alt_radar_m = projected.kinematics.z;
    projected.instrument.ias_mps = speed;
    projected.instrument.mach = expected.dynamics[9];
    projected.instrument.vvi_mps = projected.kinematics.vz;
    projected.instrument.pitch_deg = projected.kinematics.pitch;
    projected.instrument.roll_deg = projected.kinematics.roll;
    projected.instrument.heading_deg = projected.kinematics.heading;
    projected.instrument.aoa_deg = expected.dynamics[7];
    projected.instrument.beta_deg = expected.dynamics[8];
    projected.instrument.g_load_normal = 1.0;
    projected.instrument.g_load_axial = 0.0;
    projected.instrument.p_deg_s = expected.dynamics[0] * radians_to_degrees;
    projected.instrument.q_deg_s = expected.dynamics[1] * radians_to_degrees;
    projected.instrument.r_deg_s = expected.dynamics[2] * radians_to_degrees;
    projected.instrument.engine_rpm_pct = trace.windows[window].actions[world].throttle * 100.0;
    projected.instrument.fuel_flow_kg_h = 0.0;
    projected.instrument.throttle_pos = trace.windows[window].actions[world].throttle;
    projected.instrument.fuel_internal_kg = kPhaseBFuelMassKg;
    projected.instrument.fuel_external_kg = 0.0;
    projected.instrument.gear_pos = trace.windows[window].actions[world].gear_handle;
    projected.instrument.flaps_pos = trace.windows[window].actions[world].flaps;
    projected.instrument.speedbrake_pos = trace.windows[window].actions[world].speedbrake;
    projected.observation.id = entity_id;
    projected.observation.sim_time = trace.time_steps[world];
    projected.observation.x = projected.kinematics.x;
    projected.observation.y = projected.kinematics.y;
    projected.observation.z = projected.kinematics.z;
    projected.observation.vx = projected.kinematics.vx;
    projected.observation.vy = projected.kinematics.vy;
    projected.observation.vz = projected.kinematics.vz;
    projected.observation.heading = projected.kinematics.heading;
    projected.observation.pitch = projected.kinematics.pitch;
    projected.observation.roll = projected.kinematics.roll;
    projected.observation.speed = speed;
    projected.observation.health = kPhaseDHealth;
    projected.observation.gear_state = trace.windows[window].actions[world].gear_handle;
    projected.observation.throttle = trace.windows[window].actions[world].throttle;
    projected.observation.total_reward =
        kPhaseDSurvivalReward + phase_d_speed_reward(projected.observation.speed);
    projected.clock.simulation_time_s = trace.time_steps[world];
    derive_cpu_reward_and_termination(projected);
    return projected;
}

ReplayLaneFrame make_input_frame(const ReplayTrace &trace, std::size_t window,
                                 const std::vector<std::uint64_t> &entity_ids) {
    ReplayLaneFrame frame{
        .window_index = window,
        .barrier_id = "input_injection",
        .source_snapshot_version = 0,
    };
    for (std::size_t world = 0; world < entity_ids.size(); ++world) {
        append_input_fields(frame, world, entity_ids[world], trace.windows[window].actions[world]);
    }
    return frame;
}

ReplayLaneFrame make_projection_frame(const ReplayTrace &trace, std::size_t window,
                                      std::string_view barrier_id,
                                      const std::vector<ProjectedWorld> &worlds) {
    ReplayLaneFrame frame{
        .window_index = window,
        .barrier_id = std::string(barrier_id),
        .source_snapshot_version = worlds.empty() ? 0 : worlds.front().snapshot.global_version,
    };
    (void)trace;
    for (const auto &world : worlds) append_projection_fields(frame, world);
    return frame;
}

} // namespace runtime::cuda_resident::replay::test_support
