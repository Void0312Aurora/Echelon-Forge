#include "interfaces/python/binding_utils.h"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <utility>
#include <vector>

#include "components/physics/instruments.h"
#include "core/interfaces/observation.h"
#include "core/mission/runtime/execution_observation_runtime.h"
#include "core/mission/runtime/mission_runtime.h"
#include "gpu/gpu_execution_observation_runtime.h"
#include "runtime/compatibility/runtime_facade_visual_observation.h"

namespace {

gpu::ExecutionObservationBatchRequest make_request(const InstrumentState &inst,
                                                   const MissionObservationInputs &mission_inputs,
                                                   const float *ils, int max_contacts, int max_rwr,
                                                   const AgentObservation &truth) {
    gpu::ExecutionObservationBatchRequest req{};
    req.inst.alt_baro_m = inst.alt_baro_m;
    req.inst.alt_radar_m = inst.alt_radar_m;
    req.inst.ias_mps = inst.ias_mps;
    req.inst.mach = inst.mach;
    req.inst.vvi_mps = inst.vvi_mps;
    req.inst.pitch_deg = inst.pitch_deg;
    req.inst.roll_deg = inst.roll_deg;
    req.inst.heading_deg = inst.heading_deg;
    req.inst.aoa_deg = inst.aoa_deg;
    req.inst.beta_deg = inst.beta_deg;
    req.inst.g_load_normal = inst.g_load_normal;
    req.inst.g_load_axial = inst.g_load_axial;
    req.inst.p_deg_s = inst.p_deg_s;
    req.inst.q_deg_s = inst.q_deg_s;
    req.inst.r_deg_s = inst.r_deg_s;
    req.inst.engine_rpm_pct = inst.engine_rpm_pct;
    req.inst.fuel_flow_kg_h = inst.fuel_flow_kg_h;
    req.inst.fuel_internal_kg = inst.fuel_internal_kg;
    req.inst.fuel_external_kg = inst.fuel_external_kg;
    req.inst.gear_pos = inst.gear_pos;
    req.inst.flaps_pos = inst.flaps_pos;
    req.inst.speedbrake_pos = inst.speedbrake_pos;
    req.inst.oat_c = inst.oat_c;
    req.inst.cmd_heading_deg = inst.cmd_heading_deg;
    req.inst.cmd_alt_m = inst.cmd_alt_m;
    req.inst.cmd_speed_mps = inst.cmd_speed_mps;
    req.inst.rwr_active = inst.rwr_active;
    req.inst.missiles_remaining = inst.missiles_remaining;
    req.inst.lat_deg = inst.lat_deg;
    req.inst.lon_deg = inst.lon_deg;
    req.inst.vn_mps = inst.vn_mps;
    req.inst.ve_mps = inst.ve_mps;
    req.inst.vd_mps = inst.vd_mps;
    req.inst.ground_speed_mps = inst.ground_speed_mps;
    req.inst.ground_track_deg = inst.ground_track_deg;
    req.inst.wind_speed_mps = inst.wind_speed_mps;
    req.inst.wind_dir_deg = inst.wind_dir_deg;
    req.inst.gps_available = inst.gps_available;
    req.inst.position_uncertainty_m = inst.position_uncertainty_m;

    req.mission.mode_code = mission_inputs.mode_code;
    req.mission.command_code = mission_inputs.command_code;
    req.mission.target_heading_deg = mission_inputs.target_heading_deg;
    req.mission.target_altitude_m = mission_inputs.target_altitude_m;
    req.mission.target_speed_mps = mission_inputs.target_speed_mps;
    req.mission.takeoff_procedure_code = mission_inputs.takeoff_procedure_code;
    req.mission.takeoff_clearance_code = mission_inputs.takeoff_clearance_code;
    req.mission.takeoff_interval_s = mission_inputs.takeoff_interval_s;
    req.mission.runway_slot_code = mission_inputs.runway_slot_code;
    req.mission.form_offset_x = mission_inputs.form_offset_x;
    req.mission.form_offset_y = mission_inputs.form_offset_y;
    req.mission.form_offset_z = mission_inputs.form_offset_z;
    req.mission.self_role_code = mission_inputs.self_role_code;
    req.mission.self_formation_role_code = mission_inputs.self_formation_role_code;
    req.mission.relative_slot_code = mission_inputs.relative_slot_code;
    req.mission.reference_relative_slot_code = mission_inputs.reference_relative_slot_code;
    if (mission_inputs.has_route_guidance && mission_inputs.route_guidance.valid) {
        req.mission.has_route_guidance = true;
        req.mission.route_idx = mission_inputs.route_guidance.idx;
        req.mission.route_count = mission_inputs.route_guidance.count;
        req.mission.route_waypoint_flyover =
            mission_inputs.route_guidance.waypoint_mode == "flyover";
        req.mission.route_dist_m = mission_inputs.route_guidance.dist_m;
        req.mission.route_reward_xtk_m = mission_inputs.route_guidance.reward_xtk_m;
        req.mission.route_reward_dtg_m = mission_inputs.route_guidance.reward_dtg_m;
        req.mission.route_direct_to_track_deg = mission_inputs.route_guidance.direct_to_track_deg;
        req.mission.route_reward_desired_track_deg =
            mission_inputs.route_guidance.reward_desired_track_deg;
        req.mission.route_next_turn_deg = mission_inputs.route_guidance.next_turn_deg;
        req.mission.route_distance_to_turn_m = mission_inputs.route_guidance.distance_to_turn_m;
        req.mission.nav_own_altitude_m = mission_inputs.nav_inputs.own_altitude_m;
        req.mission.nav_truth_heading_deg = mission_inputs.nav_inputs.truth_heading_deg;
        req.mission.nav_truth_speed_mps = mission_inputs.nav_inputs.truth_speed_mps;
        req.mission.nav_inst_heading_deg = mission_inputs.nav_inputs.inst_heading_deg;
        req.mission.nav_inst_ground_track_deg = mission_inputs.nav_inputs.inst_ground_track_deg;
        req.mission.nav_inst_ias_mps = mission_inputs.nav_inputs.inst_ias_mps;
        req.mission.nav_waypoint_altitude_m = mission_inputs.nav_inputs.waypoint_altitude_m;
        req.mission.nav_cdi_full_scale_m = mission_inputs.nav_inputs.cdi_full_scale_m;
    }
    req.ils_valid = ils[0];
    req.ils_loc = ils[1];
    req.ils_gs = ils[2];
    req.ils_dme = ils[3];
    req.contact_count = std::min(max_contacts, static_cast<int>(truth.contacts.size()));
    req.rwr_count = std::min(max_rwr, static_cast<int>(truth.rwr_warnings.size()));
    return req;
}

} // namespace

void bind_gpu_facade_only(nb::module_ &m) {
    m.def(
        "compute_execution_observation_runtime_numpy",
        [](const InstrumentState &inst, const AgentObservation &truth, float ils_valid,
           float ils_loc, float ils_gs, float ils_dme, int max_contacts, int max_rwr) {
            auto out = compute_execution_observation_runtime(
                inst, truth, ils_valid, ils_loc, ils_gs, ils_dme, max_contacts, max_rwr);
            size_t inst_shape[1] = {out.instrument_values.size()};
            size_t contact_shape[2] = {static_cast<size_t>(std::max(0, max_contacts)), 5u};
            size_t rwr_shape[2] = {static_cast<size_t>(std::max(0, max_rwr)), 4u};
            return nb::make_tuple(
                visual_tensor_to_numpy<nb::ndim<1>>(std::move(out.instrument_values), 1,
                                                    inst_shape),
                visual_tensor_to_numpy<nb::ndim<2>>(std::move(out.contact_values), 2,
                                                    contact_shape),
                visual_tensor_to_numpy<nb::ndim<2>>(std::move(out.rwr_values), 2, rwr_shape));
        },
        nb::arg("inst"), nb::arg("truth"), nb::arg("ils_valid"), nb::arg("ils_loc"),
        nb::arg("ils_gs"), nb::arg("ils_dme"), nb::arg("max_contacts"), nb::arg("max_rwr"));

    m.def(
        "compute_execution_observation_batch_numpy",
        [](const std::vector<InstrumentState> &inst_batch,
           const std::vector<AgentObservation> &truth_batch,
           const std::vector<MissionObservationInputs> &mission_inputs_batch,
           nb::ndarray<nb::numpy, const float, nb::ndim<2>, nb::c_contig> ils_batch,
           int max_contacts, int max_rwr, bool use_gpu) {
            if (inst_batch.size() != truth_batch.size() ||
                inst_batch.size() != mission_inputs_batch.size() || ils_batch.ndim() != 2 ||
                ils_batch.shape(0) != inst_batch.size() || ils_batch.shape(1) < 4) {
                throw std::invalid_argument("invalid observation batch shape or sizes");
            }
            if (use_gpu) {
                throw std::invalid_argument(
                    "facade-only observation binding does not enable GPU execution");
            }
            std::vector<gpu::ExecutionObservationBatchRequest> requests;
            std::vector<std::vector<TrackData>> contacts;
            std::vector<std::vector<RWREvent>> rwr;
            requests.reserve(inst_batch.size());
            contacts.reserve(inst_batch.size());
            rwr.reserve(inst_batch.size());
            const auto *ils = static_cast<const float *>(ils_batch.data());
            const size_t ils_stride = static_cast<size_t>(ils_batch.shape(1));
            for (size_t i = 0; i < inst_batch.size(); ++i) {
                requests.push_back(make_request(inst_batch[i], mission_inputs_batch[i],
                                                ils + i * ils_stride, max_contacts, max_rwr,
                                                truth_batch[i]));
                contacts.push_back(truth_batch[i].contacts);
                rwr.push_back(truth_batch[i].rwr_warnings);
            }
            const int mode =
                mission_inputs_batch.empty() ? 0 : mission_inputs_batch.front().mode_code;
            const size_t instrument_count = gpu::kExecutionObservationInstrumentCount;
            const size_t mission_count = gpu::execution_observation_mission_float_count(mode);
            const size_t contact_count = static_cast<size_t>(std::max(0, max_contacts)) * 5u;
            const size_t rwr_count = static_cast<size_t>(std::max(0, max_rwr)) * 4u;
            const size_t per_request =
                gpu::execution_observation_output_float_count(max_contacts, max_rwr, mode);
            const auto flat = gpu::compute_execution_observation_reference_cpu_batch(
                requests, contacts, rwr, max_contacts, max_rwr);
            const size_t batch = inst_batch.size();
            if (flat.size() != batch * per_request) {
                throw std::runtime_error("unexpected flattened batch observation output size");
            }
            std::vector<float> inst_out(batch * instrument_count);
            std::vector<float> contact_out(batch * contact_count);
            std::vector<float> rwr_out(batch * rwr_count);
            std::vector<float> mission_out(batch * mission_count);
            for (size_t i = 0; i < batch; ++i) {
                const size_t base = i * per_request;
                std::copy_n(flat.begin() + base, instrument_count,
                            inst_out.begin() + i * instrument_count);
                std::copy_n(flat.begin() + base + instrument_count, contact_count,
                            contact_out.begin() + i * contact_count);
                std::copy_n(flat.begin() + base + instrument_count + contact_count, rwr_count,
                            rwr_out.begin() + i * rwr_count);
                std::copy_n(flat.begin() + base + instrument_count + contact_count + rwr_count,
                            mission_count, mission_out.begin() + i * mission_count);
            }
            size_t inst_shape[2] = {batch, instrument_count};
            size_t contact_shape[3] = {batch, static_cast<size_t>(std::max(0, max_contacts)), 5u};
            size_t rwr_shape[3] = {batch, static_cast<size_t>(std::max(0, max_rwr)), 4u};
            size_t mission_shape[2] = {batch, mission_count};
            return nb::make_tuple(
                visual_tensor_to_numpy<nb::ndim<2>>(std::move(inst_out), 2, inst_shape),
                visual_tensor_to_numpy<nb::ndim<3>>(std::move(contact_out), 3, contact_shape),
                visual_tensor_to_numpy<nb::ndim<3>>(std::move(rwr_out), 3, rwr_shape),
                visual_tensor_to_numpy<nb::ndim<2>>(std::move(mission_out), 2, mission_shape));
        },
        nb::arg("inst_batch"), nb::arg("truth_batch"), nb::arg("mission_inputs_batch"),
        nb::arg("ils_batch"), nb::arg("max_contacts"), nb::arg("max_rwr"),
        nb::arg("use_gpu") = false);

    m.def(
        "compute_world_batch_visual_observation_batch_numpy",
        [](RuntimeFacade &facade, const std::vector<WorldEntityRef> &refs, int downsample,
           bool use_gpu) {
            auto outputs =
                render_runtime_facade_visual_observation_batch(facade, refs, downsample, use_gpu);
            size_t shape[4] = {
                outputs.batch_size,
                static_cast<size_t>(outputs.out_h),
                static_cast<size_t>(outputs.out_w),
                static_cast<size_t>(arb::ARB_CHANNELS),
            };
            return visual_tensor_to_numpy<nb::ndim<4>>(std::move(outputs.flat), 4, shape);
        },
        nb::arg("runtime_facade"), nb::arg("refs"), nb::arg("downsample") = 1,
        nb::arg("use_gpu") = false);

    m.def(
        "compute_world_batch_visual_observation_batch_export",
        [](RuntimeFacade &facade, const std::vector<WorldEntityRef> &refs, int downsample,
           bool use_gpu) {
            if (use_gpu) {
                throw std::invalid_argument(
                    "facade-only visual export does not expose a device-resident view");
            }
            auto outputs =
                render_runtime_facade_visual_observation_batch(facade, refs, downsample, false);
            size_t shape[4] = {
                outputs.batch_size,
                static_cast<size_t>(outputs.out_h),
                static_cast<size_t>(outputs.out_w),
                static_cast<size_t>(arb::ARB_CHANNELS),
            };
            return nb::make_tuple(
                visual_tensor_to_numpy<nb::ndim<4>>(std::move(outputs.flat), 4, shape), nb::none());
        },
        nb::arg("runtime_facade"), nb::arg("refs"), nb::arg("downsample") = 1,
        nb::arg("use_gpu") = false);
}
