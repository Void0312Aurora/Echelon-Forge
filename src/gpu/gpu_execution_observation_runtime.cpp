#include "gpu/gpu_execution_observation_runtime.h"

#include <algorithm>
#include <stdexcept>

#include "components/physics/instruments.h"
#include "core/mission/execution_observation_runtime.h"

namespace gpu::detail {

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
std::vector<float> compute_execution_observation_experiment_batch_cuda(
    const std::vector<ExecutionObservationBatchRequest>& requests,
    const std::vector<std::vector<TrackData>>& contacts_batch,
    const std::vector<std::vector<RWREvent>>& rwr_batch,
    int max_contacts,
    int max_rwr
);
bool compute_execution_observation_experiment_batch_cuda_device_resident(
    const std::vector<ExecutionObservationBatchRequest>& requests,
    const std::vector<std::vector<TrackData>>& contacts_batch,
    const std::vector<std::vector<RWREvent>>& rwr_batch,
    int max_contacts,
    int max_rwr
);
ExecutionObservationExperimentStats last_execution_observation_cuda_stats();
const void* last_execution_observation_output_device_ptr_cuda();
std::size_t last_execution_observation_output_float_count_cuda();
#endif

}  // namespace gpu::detail

namespace gpu {

namespace {

InstrumentState to_instrument_state(const ExecutionObservationBatchRequest::InstrumentPacked& src) {
    InstrumentState inst{};
    inst.alt_baro_m = src.alt_baro_m;
    inst.alt_radar_m = src.alt_radar_m;
    inst.ias_mps = src.ias_mps;
    inst.mach = src.mach;
    inst.vvi_mps = src.vvi_mps;
    inst.pitch_deg = src.pitch_deg;
    inst.roll_deg = src.roll_deg;
    inst.heading_deg = src.heading_deg;
    inst.aoa_deg = src.aoa_deg;
    inst.beta_deg = src.beta_deg;
    inst.g_load_normal = src.g_load_normal;
    inst.g_load_axial = src.g_load_axial;
    inst.p_deg_s = src.p_deg_s;
    inst.q_deg_s = src.q_deg_s;
    inst.r_deg_s = src.r_deg_s;
    inst.engine_rpm_pct = src.engine_rpm_pct;
    inst.fuel_flow_kg_h = src.fuel_flow_kg_h;
    inst.fuel_internal_kg = src.fuel_internal_kg;
    inst.fuel_external_kg = src.fuel_external_kg;
    inst.gear_pos = src.gear_pos;
    inst.flaps_pos = src.flaps_pos;
    inst.speedbrake_pos = src.speedbrake_pos;
    inst.oat_c = src.oat_c;
    inst.cmd_heading_deg = src.cmd_heading_deg;
    inst.cmd_alt_m = src.cmd_alt_m;
    inst.cmd_speed_mps = src.cmd_speed_mps;
    inst.rwr_active = src.rwr_active;
    inst.missiles_remaining = src.missiles_remaining;
    inst.lat_deg = src.lat_deg;
    inst.lon_deg = src.lon_deg;
    inst.vn_mps = src.vn_mps;
    inst.ve_mps = src.ve_mps;
    inst.vd_mps = src.vd_mps;
    inst.ground_speed_mps = src.ground_speed_mps;
    inst.ground_track_deg = src.ground_track_deg;
    inst.wind_speed_mps = src.wind_speed_mps;
    inst.wind_dir_deg = src.wind_dir_deg;
    inst.gps_available = src.gps_available;
    inst.position_uncertainty_m = src.position_uncertainty_m;
    return inst;
}

MissionObservationInputs to_mission_observation_inputs(const ExecutionObservationBatchRequest& src) {
    MissionObservationInputs inputs{};
    inputs.mode_code = src.mission.mode_code;
    inputs.command_code = src.mission.command_code;
    inputs.target_heading_deg = src.mission.target_heading_deg;
    inputs.target_altitude_m = src.mission.target_altitude_m;
    inputs.target_speed_mps = src.mission.target_speed_mps;
    if (src.mission.has_route_guidance) {
        inputs.has_route_guidance = true;
        inputs.route_guidance.valid = true;
        inputs.route_guidance.idx = src.mission.route_idx;
        inputs.route_guidance.count = src.mission.route_count;
        inputs.route_guidance.waypoint_mode = src.mission.route_waypoint_flyover ? "flyover" : "flyby";
        inputs.route_guidance.dist_m = src.mission.route_dist_m;
        inputs.route_guidance.reward_xtk_m = src.mission.route_reward_xtk_m;
        inputs.route_guidance.reward_dtg_m = src.mission.route_reward_dtg_m;
        inputs.route_guidance.direct_to_track_deg = src.mission.route_direct_to_track_deg;
        inputs.route_guidance.reward_desired_track_deg = src.mission.route_reward_desired_track_deg;
        inputs.route_guidance.next_turn_deg = src.mission.route_next_turn_deg;
        inputs.route_guidance.distance_to_turn_m = src.mission.route_distance_to_turn_m;
        inputs.nav_inputs.own_altitude_m = src.mission.nav_own_altitude_m;
        inputs.nav_inputs.truth_heading_deg = src.mission.nav_truth_heading_deg;
        inputs.nav_inputs.truth_speed_mps = src.mission.nav_truth_speed_mps;
        inputs.nav_inputs.inst_heading_deg = src.mission.nav_inst_heading_deg;
        inputs.nav_inputs.inst_ground_track_deg = src.mission.nav_inst_ground_track_deg;
        inputs.nav_inputs.inst_ias_mps = src.mission.nav_inst_ias_mps;
        inputs.nav_inputs.waypoint_altitude_m = src.mission.nav_waypoint_altitude_m;
        inputs.nav_inputs.cdi_full_scale_m = src.mission.nav_cdi_full_scale_m;
    }
    return inputs;
}

int resolve_uniform_mission_mode_code(const std::vector<ExecutionObservationBatchRequest>& requests) {
    if (requests.empty()) {
        return 0;
    }
    const int mode_code = requests.front().mission.mode_code;
    for (const auto& request : requests) {
        if (request.mission.mode_code != mode_code) {
            throw std::invalid_argument("execution observation batch requires a uniform mission mode code");
        }
    }
    return mode_code;
}

}  // namespace

std::size_t execution_observation_mission_float_count(int mission_mode_code) {
    switch (mission_mode_code) {
        case 0:
            return static_cast<std::size_t>(kExecutionObservationMissionBasicCount);
        case 1:
            return static_cast<std::size_t>(kExecutionObservationMissionNavV1Count);
        case 2:
            return static_cast<std::size_t>(kExecutionObservationMissionNavV2Count);
        default:
            throw std::invalid_argument("Unknown execution observation mission mode code");
    }
}

std::size_t execution_observation_output_float_count(int max_contacts, int max_rwr, int mission_mode_code) {
    const std::size_t contacts = static_cast<std::size_t>(std::max(0, max_contacts));
    const std::size_t rwr = static_cast<std::size_t>(std::max(0, max_rwr));
    return static_cast<std::size_t>(kExecutionObservationInstrumentCount) +
           contacts * static_cast<std::size_t>(kExecutionObservationContactWidth) +
           rwr * static_cast<std::size_t>(kExecutionObservationRwrWidth) +
           execution_observation_mission_float_count(mission_mode_code);
}

ExecutionObservationExperimentStats last_execution_observation_stats() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::last_execution_observation_cuda_stats();
#else
    return ExecutionObservationExperimentStats{};
#endif
}

const void* last_execution_observation_output_device_ptr() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::last_execution_observation_output_device_ptr_cuda();
#else
    return nullptr;
#endif
}

std::size_t last_execution_observation_output_float_count() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::last_execution_observation_output_float_count_cuda();
#else
    return 0;
#endif
}

std::vector<float> compute_execution_observation_reference_cpu_batch(
    const std::vector<ExecutionObservationBatchRequest>& requests,
    const std::vector<std::vector<TrackData>>& contacts_batch,
    const std::vector<std::vector<RWREvent>>& rwr_batch,
    int max_contacts,
    int max_rwr
) {
    if (requests.size() != contacts_batch.size() || requests.size() != rwr_batch.size()) {
        throw std::invalid_argument("compute_execution_observation_reference_cpu_batch expects matching batch sizes");
    }
    if (requests.empty()) {
        return {};
    }
    const std::size_t request_count = requests.size();
    const int mission_mode_code = resolve_uniform_mission_mode_code(requests);
    const std::size_t per_request = execution_observation_output_float_count(max_contacts, max_rwr, mission_mode_code);
    std::vector<float> out(request_count * per_request, 0.0f);
    const std::size_t instrument_count = static_cast<std::size_t>(kExecutionObservationInstrumentCount);
    const std::size_t contact_count = static_cast<std::size_t>(std::max(0, max_contacts));
    const std::size_t rwr_count = static_cast<std::size_t>(std::max(0, max_rwr));
    const std::size_t contact_section = contact_count * static_cast<std::size_t>(kExecutionObservationContactWidth);
    const std::size_t rwr_section = rwr_count * static_cast<std::size_t>(kExecutionObservationRwrWidth);

    for (std::size_t request_index = 0; request_index < request_count; ++request_index) {
        AgentObservation truth{};
        const int bounded_contacts = std::min(
            std::max(0, requests[request_index].contact_count),
            static_cast<int>(contacts_batch[request_index].size())
        );
        const int bounded_rwr = std::min(
            std::max(0, requests[request_index].rwr_count),
            static_cast<int>(rwr_batch[request_index].size())
        );
        truth.contacts.assign(
            contacts_batch[request_index].begin(),
            contacts_batch[request_index].begin() + bounded_contacts
        );
        truth.rwr_warnings.assign(
            rwr_batch[request_index].begin(),
            rwr_batch[request_index].begin() + bounded_rwr
        );
        const auto products = compute_execution_observation_runtime(
            to_instrument_state(requests[request_index].inst),
            truth,
            requests[request_index].ils_valid,
            requests[request_index].ils_loc,
            requests[request_index].ils_gs,
            requests[request_index].ils_dme,
            max_contacts,
            max_rwr
        );
        const auto mission_products = compute_mission_observation(
            to_mission_observation_inputs(requests[request_index])
        );
        const std::size_t base = request_index * per_request;
        std::copy(
            products.instrument_values.begin(),
            products.instrument_values.begin() + static_cast<std::ptrdiff_t>(instrument_count),
            out.begin() + static_cast<std::ptrdiff_t>(base)
        );
        std::copy(
            products.contact_values.begin(),
            products.contact_values.end(),
            out.begin() + static_cast<std::ptrdiff_t>(base + instrument_count)
        );
        std::copy(
            products.rwr_values.begin(),
            products.rwr_values.end(),
            out.begin() + static_cast<std::ptrdiff_t>(base + instrument_count + contact_section)
        );
        std::copy(
            mission_products.values.begin(),
            mission_products.values.end(),
            out.begin() + static_cast<std::ptrdiff_t>(base + instrument_count + contact_section + rwr_section)
        );
    }
    return out;
}

std::vector<float> compute_execution_observation_experiment_batch(
    const std::vector<ExecutionObservationBatchRequest>& requests,
    const std::vector<std::vector<TrackData>>& contacts_batch,
    const std::vector<std::vector<RWREvent>>& rwr_batch,
    int max_contacts,
    int max_rwr
) {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    auto out = detail::compute_execution_observation_experiment_batch_cuda(
        requests,
        contacts_batch,
        rwr_batch,
        max_contacts,
        max_rwr
    );
    if (!out.empty()) {
        return out;
    }
#endif
    return compute_execution_observation_reference_cpu_batch(
        requests,
        contacts_batch,
        rwr_batch,
        max_contacts,
        max_rwr
    );
}

bool compute_execution_observation_experiment_batch_device_resident(
    const std::vector<ExecutionObservationBatchRequest>& requests,
    const std::vector<std::vector<TrackData>>& contacts_batch,
    const std::vector<std::vector<RWREvent>>& rwr_batch,
    int max_contacts,
    int max_rwr
) {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::compute_execution_observation_experiment_batch_cuda_device_resident(
        requests,
        contacts_batch,
        rwr_batch,
        max_contacts,
        max_rwr
    );
#else
    (void)requests;
    (void)contacts_batch;
    (void)rwr_batch;
    (void)max_contacts;
    (void)max_rwr;
    return false;
#endif
}

}  // namespace gpu
