#include "interfaces/python/binding_utils.h"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "components/basic/common.h"
#include "components/physics/instruments.h"
#include "components/systems/ew.h"
#include "components/visual/visual_sensor.h"
#include "core/engine/simulation_kernel.h"
#include "core/engine/world_batch_runtime.h"
#include "core/interfaces/observation.h"
#include "core/interfaces/unit_data.h"
#include "core/mission/runtime/execution_observation_runtime.h"
#include "core/mission/runtime/execution_frame_runtime.h"
#include "core/mission/runtime/execution_episode_runtime.h"
#include "core/mission/runtime/mission_runtime.h"
#include "gpu/gpu_execution_observation_runtime.h"
#include "gpu/gpu_flight_shaping_runtime.h"
#include "gpu/gpu_interaction_broadphase_runtime.h"
#include "gpu/gpu_visual_runtime.h"
#include "interfaces/python/dlpack_minimal.h"
#include "models/environment/default_environment_snapshot.h"

namespace {
struct ManagedDLPackTensor {
    DLManagedTensor managed{};
    std::vector<std::int64_t> shape;
    std::vector<std::int64_t> strides;
};

void delete_managed_dlpack_tensor(DLManagedTensor* tensor) {
    if (tensor == nullptr) {
        return;
    }
    delete static_cast<ManagedDLPackTensor*>(tensor->manager_ctx);
}

void delete_dlpack_capsule(PyObject* capsule) {
    if (capsule == nullptr || !PyCapsule_IsValid(capsule, "dltensor")) {
        return;
    }
    auto* managed = static_cast<DLManagedTensor*>(PyCapsule_GetPointer(capsule, "dltensor"));
    if (managed != nullptr && managed->deleter != nullptr) {
        managed->deleter(managed);
    }
}

class GpuTensorView {
public:
    GpuTensorView() = default;

    GpuTensorView(
        const void* data_ptr,
        std::vector<std::int64_t> shape,
        int device_id,
        std::vector<std::int64_t> strides = {}
    )
        : data_ptr_(data_ptr),
          shape_(std::move(shape)),
          strides_(std::move(strides)),
          device_id_(device_id) {}

    bool valid() const {
        return data_ptr_ != nullptr && !shape_.empty();
    }

    std::vector<std::int64_t> shape() const {
        return shape_;
    }

    std::vector<std::int64_t> strides() const {
        return strides_;
    }

    int device_id() const {
        return device_id_;
    }

    std::size_t numel() const {
        std::size_t out = 1;
        for (const auto dim : shape_) {
            if (dim <= 0) {
                return 0;
            }
            out *= static_cast<std::size_t>(dim);
        }
        return out;
    }

    nb::tuple dlpack_device() const {
        return nb::make_tuple(static_cast<int>(kDLCUDA), int(device_id_));
    }

    nb::object dlpack(
        nb::object stream,
        nb::object max_version,
        nb::object dl_device,
        nb::object copy
    ) const {
        (void)stream;
        (void)max_version;
        if (!valid()) {
            throw std::runtime_error("GpuTensorView is not valid");
        }
        if (!copy.is_none() && nb::cast<bool>(copy)) {
            throw std::runtime_error("GpuTensorView does not support copy=True");
        }
        if (!dl_device.is_none()) {
            nb::tuple requested = nb::cast<nb::tuple>(dl_device);
            if (requested.size() >= 2) {
                const int requested_type = nb::cast<int>(requested[0]);
                const int requested_id = nb::cast<int>(requested[1]);
                if (requested_type != static_cast<int>(kDLCUDA) || requested_id != device_id_) {
                    throw std::runtime_error("GpuTensorView cannot export to a different dl_device");
                }
            }
        }

        auto* holder = new ManagedDLPackTensor();
        holder->shape = shape_;
        holder->strides = strides_;
        holder->managed.dl_tensor.data = const_cast<void*>(data_ptr_);
        holder->managed.dl_tensor.device = {kDLCUDA, device_id_};
        holder->managed.dl_tensor.ndim = static_cast<int32_t>(holder->shape.size());
        holder->managed.dl_tensor.dtype = {kDLFloat, 32, 1};
        holder->managed.dl_tensor.shape = holder->shape.data();
        holder->managed.dl_tensor.strides = holder->strides.empty() ? nullptr : holder->strides.data();
        holder->managed.dl_tensor.byte_offset = 0;
        holder->managed.manager_ctx = holder;
        holder->managed.deleter = &delete_managed_dlpack_tensor;

        PyObject* capsule = PyCapsule_New(
            static_cast<void*>(&holder->managed),
            "dltensor",
            &delete_dlpack_capsule
        );
        if (capsule == nullptr) {
            delete holder;
            throw nb::python_error();
        }
        return nb::steal<nb::object>(capsule);
    }

private:
    const void* data_ptr_ = nullptr;
    std::vector<std::int64_t> shape_;
    std::vector<std::int64_t> strides_;
    int device_id_ = 0;
};

int current_cuda_device_id() {
    const auto device = gpu::probe_device();
    return device.active_device >= 0 ? device.active_device : 0;
}

nb::object maybe_gpu_tensor_view(
    const void* data_ptr,
    std::size_t float_count,
    std::vector<std::int64_t> shape,
    std::vector<std::int64_t> strides = {}
) {
    if (data_ptr == nullptr || shape.empty()) {
        return nb::none();
    }
    std::size_t expected = 1;
    for (const auto dim : shape) {
        if (dim <= 0) {
            return nb::none();
        }
        expected *= static_cast<std::size_t>(dim);
    }
    if (float_count != 0 && expected != float_count) {
        return nb::none();
    }
    return nb::cast(
        GpuTensorView(
            data_ptr,
            std::move(shape),
            current_cuda_device_id(),
            std::move(strides)
        )
    );
}

FlightShapingRuntimeProducts unpack_flight_shaping_products(const float* src) {
    FlightShapingRuntimeProducts out{};
    out.valid = src[0] > 0.5f;
    out.altitude_progress = static_cast<double>(src[1]);
    out.low_alt_descent_penalty = static_cast<double>(src[2]);
    out.speed_progress = static_cast<double>(src[3]);
    out.speed_regress = static_cast<double>(src[4]);
    out.stationary_penalty = static_cast<double>(src[5]);
    out.liftoff_bonus = static_cast<double>(src[6]);
    out.next_liftoff_awarded = src[7] > 0.5f;
    out.rotation_reward = static_cast<double>(src[8]);
    out.rotation_overpitch_penalty = static_cast<double>(src[9]);
    out.gear_up_bonus = static_cast<double>(src[10]);
    out.next_gear_bonus_awarded = src[11] > 0.5f;
    out.roll_stability = static_cast<double>(src[12]);
    out.heading_error_penalty = static_cast<double>(src[13]);
    out.heading_hold_bonus = static_cast<double>(src[14]);
    out.altitude_error_penalty = static_cast<double>(src[15]);
    out.altitude_hold_bonus = static_cast<double>(src[16]);
    out.speed_error_penalty = static_cast<double>(src[17]);
    out.speed_hold_bonus = static_cast<double>(src[18]);
    out.roll_abs_penalty = static_cast<double>(src[19]);
    out.pitch_abs_penalty = static_cast<double>(src[20]);
    out.yaw_rate_abs_penalty = static_cast<double>(src[21]);
    out.beta_abs_penalty = static_cast<double>(src[22]);
    out.g_deviation_penalty = static_cast<double>(src[23]);
    out.speed_reward = static_cast<double>(src[24]);
    out.runway_centerline_m_penalty = static_cast<double>(src[25]);
    out.runway_centerline_penalty = static_cast<double>(src[26]);
    out.runway_centerline_barrier = static_cast<double>(src[27]);
    out.departure_centerline_m_penalty = static_cast<double>(src[28]);
    out.departure_centerline_reward = static_cast<double>(src[29]);
    out.departure_track_error_penalty = static_cast<double>(src[30]);
    out.departure_track_reward = static_cast<double>(src[31]);
    out.alignment_reward = static_cast<double>(src[32]);
    return out;
}

std::vector<FlightShapingRuntimeProducts> unpack_flight_shaping_products_batch(
    const std::vector<float>& flat,
    std::size_t batch_size
) {
    if (flat.size() != batch_size * static_cast<std::size_t>(gpu::kFlightShapingOutputCount)) {
        throw std::runtime_error("unexpected flattened flight-shaping batch output size");
    }
    std::vector<FlightShapingRuntimeProducts> out;
    out.reserve(batch_size);
    for (std::size_t idx = 0; idx < batch_size; ++idx) {
        out.push_back(
            unpack_flight_shaping_products(
                flat.data() + static_cast<std::ptrdiff_t>(idx * static_cast<std::size_t>(gpu::kFlightShapingOutputCount))
            )
        );
    }
    return out;
}

bool default_environment_snapshots_equal(
    const DefaultEnvironmentSnapshot& lhs,
    const DefaultEnvironmentSnapshot& rhs
) {
    if (lhs.valid != rhs.valid || lhs.flat_terrain != rhs.flat_terrain) {
        return false;
    }
    if (lhs.raster.origin_x != rhs.raster.origin_x ||
        lhs.raster.origin_y != rhs.raster.origin_y ||
        lhs.raster.resolution_m != rhs.raster.resolution_m ||
        lhs.raster.width != rhs.raster.width ||
        lhs.raster.height != rhs.raster.height ||
        lhs.raster.surface_codes != rhs.raster.surface_codes) {
        return false;
    }
    if (lhs.zones.size() != rhs.zones.size()) {
        return false;
    }
    for (std::size_t idx = 0; idx < lhs.zones.size(); ++idx) {
        const auto& a = lhs.zones[idx];
        const auto& b = rhs.zones[idx];
        if (a.center_x != b.center_x ||
            a.center_y != b.center_y ||
            a.width != b.width ||
            a.length != b.length ||
            a.heading_deg != b.heading_deg ||
            a.type != b.type ||
            a.surface_code != b.surface_code) {
            return false;
        }
    }
    return true;
}

bool collect_visual_scene_for_binding(
    SimulationKernel& kernel,
    uint64_t entity_id,
    int downsample,
    gpu::VisualRenderRequest* out_request,
    std::vector<gpu::VisibleObjectPacked>* out_objects,
    IEnvironmentModel** out_env,
    const std::vector<uint64_t>* candidate_ids = nullptr
) {
    auto e = kernel.get_world().entity(entity_id);
    if (!e.is_valid()) {
        return false;
    }
    const Transform* cam_t = e.get<Transform>();
    const Alliance* cam_a = e.get<Alliance>();
    if (cam_t == nullptr || out_request == nullptr || out_objects == nullptr) {
        return false;
    }
    const auto* env_ref = kernel.get_world().get<EnvironmentModelRef>();
    if (out_env != nullptr) {
        *out_env = env_ref != nullptr ? env_ref->model : nullptr;
    }

    const int factor = std::max(1, downsample);
    gpu::VisualRenderRequest request{};
    request.cam_pos = {cam_t->x, cam_t->y, cam_t->z};
    request.cam_heading_deg = cam_t->heading;
    request.cam_pitch_deg = cam_t->pitch;
    request.fov_h_deg = 180.0;
    request.fov_v_deg = 90.0;
    request.out_height = arb::ARB_HEIGHT / factor;
    request.out_width = arb::ARB_WIDTH / factor;
    request.include_terrain = true;
    request.allow_gpu_terrain = true;
    *out_request = request;

    const int my_side = cam_a ? static_cast<int>(cam_a->side) : 0;
    out_objects->clear();
    kernel.get_world().each(
        [&](flecs::entity other_e, const Transform& t, const Velocity& v, const Alliance& a, const KeyEntity& k) {
            if (other_e.id() == entity_id) {
                return;
            }
            if (candidate_ids != nullptr && !std::binary_search(candidate_ids->begin(), candidate_ids->end(), other_e.id())) {
                return;
            }

            gpu::VisibleObjectPacked obj{};
            obj.x = t.x;
            obj.y = t.y;
            obj.z = t.z;
            obj.vx = v.vx;
            obj.vy = v.vy;
            obj.vz = v.vz;

            switch (k.type) {
                case UnitType::Aircraft: obj.bounding_radius = 10.0; obj.cls = 0; break;
                case UnitType::Ship: obj.bounding_radius = 50.0; obj.cls = 2; break;
                case UnitType::Missile: obj.bounding_radius = 2.0; obj.cls = 0; break;
                case UnitType::Facility: obj.bounding_radius = 20.0; obj.cls = 1; break;
                default: obj.bounding_radius = 5.0; obj.cls = 1; break;
            }

            const int other_side = static_cast<int>(a.side);
            if (other_side == my_side) {
                obj.team = 1;
            } else if (other_side == 0) {
                obj.team = 0;
            } else {
                obj.team = -1;
            }
            out_objects->push_back(obj);
        }
    );
    return true;
}

gpu::ExecutionObservationBatchRequest build_execution_observation_batch_request(
    const InstrumentState& inst,
    const MissionObservationInputs& mission_inputs,
    double ils_valid,
    double ils_loc,
    double ils_gs,
    double ils_dme,
    int max_contacts,
    int max_rwr,
    const AgentObservation& truth
) {
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
        req.mission.route_waypoint_flyover = mission_inputs.route_guidance.waypoint_mode == "flyover";
        req.mission.route_dist_m = mission_inputs.route_guidance.dist_m;
        req.mission.route_reward_xtk_m = mission_inputs.route_guidance.reward_xtk_m;
        req.mission.route_reward_dtg_m = mission_inputs.route_guidance.reward_dtg_m;
        req.mission.route_direct_to_track_deg = mission_inputs.route_guidance.direct_to_track_deg;
        req.mission.route_reward_desired_track_deg = mission_inputs.route_guidance.reward_desired_track_deg;
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

    req.ils_valid = ils_valid;
    req.ils_loc = ils_loc;
    req.ils_gs = ils_gs;
    req.ils_dme = ils_dme;
    req.contact_count = std::min(max_contacts, static_cast<int>(truth.contacts.size()));
    req.rwr_count = std::min(max_rwr, static_cast<int>(truth.rwr_warnings.size()));
    return req;
}

struct BatchExecutionObservationOutputs {
    std::size_t batch_size = 0;
    std::size_t instrument_count = 0;
    std::size_t contact_section = 0;
    std::size_t rwr_section = 0;
    std::size_t mission_count = 0;
    std::size_t per_request = 0;
    std::vector<float> inst_out;
    std::vector<float> contacts_out;
    std::vector<float> rwr_out;
    std::vector<float> mission_out;
    const void* device_ptr = nullptr;
    std::size_t device_float_count = 0;
};

BatchExecutionObservationOutputs compute_execution_observation_batch_binding_outputs(
    const std::vector<InstrumentState>& inst_batch,
    const std::vector<AgentObservation>& truth_batch,
    const std::vector<MissionObservationInputs>& mission_inputs_batch,
    nb::ndarray<nb::numpy, const float, nb::ndim<2>, nb::c_contig> ils_batch,
    int max_contacts,
    int max_rwr,
    bool use_gpu
) {
    if (inst_batch.size() != truth_batch.size() || inst_batch.size() != mission_inputs_batch.size()) {
        throw std::invalid_argument("batch observation inputs must have matching batch size");
    }
    if (
        ils_batch.ndim() != 2 ||
        ils_batch.shape(0) != static_cast<ssize_t>(inst_batch.size()) ||
        ils_batch.shape(1) < 4
    ) {
        throw std::invalid_argument("ils_batch must have shape [batch, >=4]");
    }

    BatchExecutionObservationOutputs out{};
    out.batch_size = inst_batch.size();
    const auto* ils_ptr = static_cast<const float*>(ils_batch.data());
    const std::size_t ils_stride = static_cast<std::size_t>(ils_batch.shape(1));

    std::vector<gpu::ExecutionObservationBatchRequest> requests;
    std::vector<std::vector<TrackData>> contacts_batch;
    std::vector<std::vector<RWREvent>> rwr_batch;
    requests.reserve(out.batch_size);
    contacts_batch.reserve(out.batch_size);
    rwr_batch.reserve(out.batch_size);
    for (std::size_t idx = 0; idx < out.batch_size; ++idx) {
        const std::size_t ils_base = idx * ils_stride;
        requests.push_back(
            build_execution_observation_batch_request(
                inst_batch[idx],
                mission_inputs_batch[idx],
                static_cast<double>(ils_ptr[ils_base + 0]),
                static_cast<double>(ils_ptr[ils_base + 1]),
                static_cast<double>(ils_ptr[ils_base + 2]),
                static_cast<double>(ils_ptr[ils_base + 3]),
                max_contacts,
                max_rwr,
                truth_batch[idx]
            )
        );
        contacts_batch.push_back(truth_batch[idx].contacts);
        rwr_batch.push_back(truth_batch[idx].rwr_warnings);
    }

    const int mission_mode_code = mission_inputs_batch.empty() ? 0 : mission_inputs_batch.front().mode_code;
    out.instrument_count = gpu::kExecutionObservationInstrumentCount;
    out.mission_count = gpu::execution_observation_mission_float_count(mission_mode_code);
    out.contact_section = static_cast<std::size_t>(std::max(0, max_contacts)) * 5u;
    out.rwr_section = static_cast<std::size_t>(std::max(0, max_rwr)) * 4u;
    out.per_request = gpu::execution_observation_output_float_count(max_contacts, max_rwr, mission_mode_code);

    const std::vector<float> flat = use_gpu
        ? gpu::compute_execution_observation_experiment_batch(
            requests,
            contacts_batch,
            rwr_batch,
            max_contacts,
            max_rwr
        )
        : gpu::compute_execution_observation_reference_cpu_batch(
            requests,
            contacts_batch,
            rwr_batch,
            max_contacts,
            max_rwr
        );
    if (flat.size() != out.batch_size * out.per_request) {
        throw std::runtime_error("unexpected flattened batch observation output size");
    }

    out.inst_out.assign(out.batch_size * out.instrument_count, 0.0f);
    out.contacts_out.assign(out.batch_size * out.contact_section, 0.0f);
    out.rwr_out.assign(out.batch_size * out.rwr_section, 0.0f);
    out.mission_out.assign(out.batch_size * out.mission_count, 0.0f);
    for (std::size_t idx = 0; idx < out.batch_size; ++idx) {
        const std::size_t src_base = idx * out.per_request;
        std::copy_n(
            flat.begin() + static_cast<std::ptrdiff_t>(src_base),
            static_cast<std::ptrdiff_t>(out.instrument_count),
            out.inst_out.begin() + static_cast<std::ptrdiff_t>(idx * out.instrument_count)
        );
        std::copy_n(
            flat.begin() + static_cast<std::ptrdiff_t>(src_base + out.instrument_count),
            static_cast<std::ptrdiff_t>(out.contact_section),
            out.contacts_out.begin() + static_cast<std::ptrdiff_t>(idx * out.contact_section)
        );
        std::copy_n(
            flat.begin() + static_cast<std::ptrdiff_t>(src_base + out.instrument_count + out.contact_section),
            static_cast<std::ptrdiff_t>(out.rwr_section),
            out.rwr_out.begin() + static_cast<std::ptrdiff_t>(idx * out.rwr_section)
        );
        std::copy_n(
            flat.begin() + static_cast<std::ptrdiff_t>(
                src_base + out.instrument_count + out.contact_section + out.rwr_section
            ),
            static_cast<std::ptrdiff_t>(out.mission_count),
            out.mission_out.begin() + static_cast<std::ptrdiff_t>(idx * out.mission_count)
        );
    }

    if (use_gpu) {
        out.device_ptr = gpu::last_execution_observation_output_device_ptr();
        out.device_float_count = gpu::last_execution_observation_output_float_count();
    }
    return out;
}

struct BatchVisualObservationOutputs {
    std::size_t batch_size = 0;
    int out_h = 0;
    int out_w = 0;
    std::size_t frame_size = 0;
    std::vector<float> flat;
    const void* device_ptr = nullptr;
    std::size_t device_float_count = 0;
};

BatchVisualObservationOutputs compute_world_batch_visual_binding_outputs(
    WorldBatchRuntime& runtime,
    const std::vector<WorldEntityRef>& refs,
    int downsample,
    bool use_gpu
) {
    const int factor = std::max(1, downsample);
    const auto visual_candidate_ids = runtime.get_visual_candidate_ids_batch(refs, 25000.0, use_gpu);
    std::vector<gpu::VisualRenderRequest> requests;
    std::vector<std::vector<gpu::VisibleObjectPacked>> objects_batch;
    requests.reserve(refs.size());
    objects_batch.reserve(refs.size());

    std::vector<IEnvironmentModel*> envs;
    envs.reserve(refs.size());
    std::vector<DefaultEnvironmentSnapshot> snapshots;
    snapshots.reserve(refs.size());

    for (std::size_t idx = 0; idx < refs.size(); ++idx) {
        const auto& ref = refs[idx];
        auto& world = runtime.world(static_cast<size_t>(ref.world_index));
        gpu::VisualRenderRequest request{};
        std::vector<gpu::VisibleObjectPacked> objects;
        IEnvironmentModel* env = nullptr;
        const std::vector<uint64_t>* candidates =
            idx < visual_candidate_ids.size() ? &visual_candidate_ids[idx] : nullptr;
        if (!collect_visual_scene_for_binding(world, ref.entity_id, factor, &request, &objects, &env, candidates)) {
            throw std::runtime_error("failed to collect visual scene for world batch visual helper");
        }
        DefaultEnvironmentSnapshot snapshot{};
        if (env != nullptr) {
            (void)extract_default_environment_snapshot(env, &snapshot);
        }
        requests.push_back(request);
        objects_batch.push_back(std::move(objects));
        envs.push_back(env);
        snapshots.push_back(std::move(snapshot));
    }

    BatchVisualObservationOutputs out{};
    out.batch_size = refs.size();
    out.out_h = requests.empty() ? (arb::ARB_HEIGHT / factor) : requests.front().out_height;
    out.out_w = requests.empty() ? (arb::ARB_WIDTH / factor) : requests.front().out_width;
    out.frame_size =
        static_cast<std::size_t>(out.out_h) *
        static_cast<std::size_t>(out.out_w) *
        static_cast<std::size_t>(arb::ARB_CHANNELS);
    out.flat.assign(out.frame_size * refs.size(), 0.0f);

    bool can_batch = !refs.empty();
    for (std::size_t idx = 1; idx < snapshots.size(); ++idx) {
        if (!default_environment_snapshots_equal(snapshots[0], snapshots[idx])) {
            can_batch = false;
            break;
        }
    }

    if (can_batch && !requests.empty()) {
        auto rendered = use_gpu
            ? gpu::render_visual_experiment_batch(requests, objects_batch, envs.front())
            : gpu::render_visual_reference_cpu_batch(requests, objects_batch, envs.front());
        out.flat = std::move(rendered);
        if (use_gpu) {
            out.device_ptr = gpu::last_visual_output_device_ptr();
            out.device_float_count = gpu::last_visual_output_float_count();
        }
    } else {
        for (std::size_t idx = 0; idx < refs.size(); ++idx) {
            auto rendered = use_gpu
                ? gpu::render_visual_experiment(requests[idx], objects_batch[idx], envs[idx])
                : gpu::render_visual_reference_cpu(requests[idx], objects_batch[idx], envs[idx]);
            std::copy(
                rendered.begin(),
                rendered.end(),
                out.flat.begin() + static_cast<std::ptrdiff_t>(idx * out.frame_size)
            );
        }
    }

    return out;
}
} // namespace

void bind_gpu(nb::module_& m) {
    m.def(
        "compute_flight_shaping_batch",
        [](const std::vector<FlightShapingRuntimeInputs>& inputs_batch, bool use_gpu) {
            if (inputs_batch.empty()) {
                return std::vector<FlightShapingRuntimeProducts>{};
            }
            if (use_gpu) {
                return unpack_flight_shaping_products_batch(
                    gpu::compute_flight_shaping_experiment_batch(inputs_batch),
                    inputs_batch.size()
                );
            }
            std::vector<FlightShapingRuntimeProducts> out;
            out.reserve(inputs_batch.size());
            for (const auto& inputs : inputs_batch) {
                out.push_back(compute_flight_shaping_terms(inputs));
            }
            return out;
        },
        nb::arg("inputs_batch"),
        nb::arg("use_gpu") = false
    );

    m.def(
        "compute_execution_observation_runtime_numpy",
        [](const InstrumentState& inst,
           const AgentObservation& truth,
           float ils_valid,
           float ils_loc,
           float ils_gs,
           float ils_dme,
           int max_contacts,
           int max_rwr) {
            ExecutionObservationRuntimeProducts out = compute_execution_observation_runtime(
                inst,
                truth,
                static_cast<double>(ils_valid),
                static_cast<double>(ils_loc),
                static_cast<double>(ils_gs),
                static_cast<double>(ils_dme),
                max_contacts,
                max_rwr
            );
            size_t instrument_shape[1] = {out.instrument_values.size()};
            size_t contact_shape[2] = {static_cast<size_t>(std::max(0, max_contacts)), 5u};
            size_t rwr_shape[2] = {static_cast<size_t>(std::max(0, max_rwr)), 4u};
            return nb::make_tuple(
                visual_tensor_to_numpy<nb::ndim<1>>(std::move(out.instrument_values), 1, instrument_shape),
                visual_tensor_to_numpy<nb::ndim<2>>(std::move(out.contact_values), 2, contact_shape),
                visual_tensor_to_numpy<nb::ndim<2>>(std::move(out.rwr_values), 2, rwr_shape)
            );
        },
        nb::arg("inst"),
        nb::arg("truth"),
        nb::arg("ils_valid"),
        nb::arg("ils_loc"),
        nb::arg("ils_gs"),
        nb::arg("ils_dme"),
        nb::arg("max_contacts"),
        nb::arg("max_rwr")
    );
    m.def(
        "compute_execution_observation_batch_numpy",
        [](const std::vector<InstrumentState>& inst_batch,
           const std::vector<AgentObservation>& truth_batch,
           const std::vector<MissionObservationInputs>& mission_inputs_batch,
           nb::ndarray<nb::numpy, const float, nb::ndim<2>, nb::c_contig> ils_batch,
           int max_contacts,
           int max_rwr,
           bool use_gpu) {
            auto outputs = compute_execution_observation_batch_binding_outputs(
                inst_batch,
                truth_batch,
                mission_inputs_batch,
                ils_batch,
                max_contacts,
                max_rwr,
                use_gpu
            );
            size_t inst_shape[2] = {outputs.batch_size, outputs.instrument_count};
            size_t contacts_shape[3] = {
                outputs.batch_size,
                static_cast<std::size_t>(std::max(0, max_contacts)),
                5u
            };
            size_t rwr_shape[3] = {
                outputs.batch_size,
                static_cast<std::size_t>(std::max(0, max_rwr)),
                4u
            };
            size_t mission_shape[2] = {outputs.batch_size, outputs.mission_count};
            return nb::make_tuple(
                visual_tensor_to_numpy<nb::ndim<2>>(std::move(outputs.inst_out), 2, inst_shape),
                visual_tensor_to_numpy<nb::ndim<3>>(std::move(outputs.contacts_out), 3, contacts_shape),
                visual_tensor_to_numpy<nb::ndim<3>>(std::move(outputs.rwr_out), 3, rwr_shape),
                visual_tensor_to_numpy<nb::ndim<2>>(std::move(outputs.mission_out), 2, mission_shape)
            );
        },
        nb::arg("inst_batch"),
        nb::arg("truth_batch"),
        nb::arg("mission_inputs_batch"),
        nb::arg("ils_batch"),
        nb::arg("max_contacts"),
        nb::arg("max_rwr"),
        nb::arg("use_gpu") = false
    );
    m.def(
        "compute_execution_observation_batch_export",
        [](const std::vector<InstrumentState>& inst_batch,
           const std::vector<AgentObservation>& truth_batch,
           const std::vector<MissionObservationInputs>& mission_inputs_batch,
           nb::ndarray<nb::numpy, const float, nb::ndim<2>, nb::c_contig> ils_batch,
           int max_contacts,
           int max_rwr,
           bool use_gpu) {
            auto outputs = compute_execution_observation_batch_binding_outputs(
                inst_batch,
                truth_batch,
                mission_inputs_batch,
                ils_batch,
                max_contacts,
                max_rwr,
                use_gpu
            );
            size_t inst_shape[2] = {outputs.batch_size, outputs.instrument_count};
            size_t contacts_shape[3] = {
                outputs.batch_size,
                static_cast<std::size_t>(std::max(0, max_contacts)),
                5u
            };
            size_t rwr_shape[3] = {
                outputs.batch_size,
                static_cast<std::size_t>(std::max(0, max_rwr)),
                4u
            };
            size_t mission_shape[2] = {outputs.batch_size, outputs.mission_count};
            nb::object device_view = nb::none();
            if (use_gpu) {
                device_view = maybe_gpu_tensor_view(
                    outputs.device_ptr,
                    outputs.device_float_count,
                    {
                        static_cast<std::int64_t>(outputs.batch_size),
                        static_cast<std::int64_t>(outputs.per_request),
                    }
                );
            }
            return nb::make_tuple(
                visual_tensor_to_numpy<nb::ndim<2>>(std::move(outputs.inst_out), 2, inst_shape),
                visual_tensor_to_numpy<nb::ndim<3>>(std::move(outputs.contacts_out), 3, contacts_shape),
                visual_tensor_to_numpy<nb::ndim<3>>(std::move(outputs.rwr_out), 3, rwr_shape),
                visual_tensor_to_numpy<nb::ndim<2>>(std::move(outputs.mission_out), 2, mission_shape),
                device_view
            );
        },
        nb::arg("inst_batch"),
        nb::arg("truth_batch"),
        nb::arg("mission_inputs_batch"),
        nb::arg("ils_batch"),
        nb::arg("max_contacts"),
        nb::arg("max_rwr"),
        nb::arg("use_gpu") = false
    );

    nb::class_<gpu::DeviceInfo>(m, "GpuDeviceInfo")
        .def(nb::init<>())
        .def_ro("cuda_runtime_built", &gpu::DeviceInfo::cuda_runtime_built)
        .def_ro("cuda_runtime_available", &gpu::DeviceInfo::cuda_runtime_available)
        .def_ro("device_count", &gpu::DeviceInfo::device_count)
        .def_ro("active_device", &gpu::DeviceInfo::active_device)
        .def_ro("compute_major", &gpu::DeviceInfo::compute_major)
        .def_ro("compute_minor", &gpu::DeviceInfo::compute_minor)
        .def_ro("runtime_version", &gpu::DeviceInfo::runtime_version)
        .def_ro("total_global_mem_bytes", &gpu::DeviceInfo::total_global_mem_bytes)
        .def_ro("free_global_mem_bytes", &gpu::DeviceInfo::free_global_mem_bytes)
        .def_ro("device_name", &gpu::DeviceInfo::device_name)
        .def_ro("error_message", &gpu::DeviceInfo::error_message);

    nb::class_<GpuTensorView>(m, "GpuTensorView")
        .def_prop_ro("valid", &GpuTensorView::valid)
        .def_prop_ro("shape", &GpuTensorView::shape)
        .def_prop_ro("strides", &GpuTensorView::strides)
        .def_prop_ro("device_id", &GpuTensorView::device_id)
        .def_prop_ro("numel", &GpuTensorView::numel)
        .def_prop_ro("dtype", [](const GpuTensorView&) { return std::string("float32"); })
        .def("__dlpack_device__", &GpuTensorView::dlpack_device)
        .def(
            "__dlpack__",
            &GpuTensorView::dlpack,
            nb::arg("stream") = nb::none(),
            nb::arg("max_version") = nb::none(),
            nb::arg("dl_device") = nb::none(),
            nb::arg("copy") = nb::none()
        );

    nb::class_<gpu::VisualExperimentStats>(m, "VisualExperimentStats")
        .def(nb::init<>())
        .def_ro("used_cuda", &gpu::VisualExperimentStats::used_cuda)
        .def_ro("host_to_device_ms", &gpu::VisualExperimentStats::host_to_device_ms)
        .def_ro("kernel_ms", &gpu::VisualExperimentStats::kernel_ms)
        .def_ro("device_to_host_ms", &gpu::VisualExperimentStats::device_to_host_ms)
        .def_ro("total_ms", &gpu::VisualExperimentStats::total_ms);

    nb::class_<gpu::ExecutionObservationExperimentStats>(m, "ExecutionObservationExperimentStats")
        .def(nb::init<>())
        .def_ro("used_cuda", &gpu::ExecutionObservationExperimentStats::used_cuda)
        .def_ro("host_to_device_ms", &gpu::ExecutionObservationExperimentStats::host_to_device_ms)
        .def_ro("kernel_ms", &gpu::ExecutionObservationExperimentStats::kernel_ms)
        .def_ro("device_to_host_ms", &gpu::ExecutionObservationExperimentStats::device_to_host_ms)
        .def_ro("total_ms", &gpu::ExecutionObservationExperimentStats::total_ms);

    nb::class_<gpu::FlightShapingExperimentStats>(m, "FlightShapingExperimentStats")
        .def(nb::init<>())
        .def_ro("used_cuda", &gpu::FlightShapingExperimentStats::used_cuda)
        .def_ro("host_to_device_ms", &gpu::FlightShapingExperimentStats::host_to_device_ms)
        .def_ro("kernel_ms", &gpu::FlightShapingExperimentStats::kernel_ms)
        .def_ro("device_to_host_ms", &gpu::FlightShapingExperimentStats::device_to_host_ms)
        .def_ro("total_ms", &gpu::FlightShapingExperimentStats::total_ms);

    m.def("probe_gpu_device", &gpu::probe_device);
    m.def("last_visual_experiment_stats", &gpu::last_visual_experiment_stats);
    m.def("last_execution_observation_stats", &gpu::last_execution_observation_stats);
    m.def("last_flight_shaping_stats", &gpu::last_flight_shaping_stats);

    nb::class_<gpu::InteractionEntityPacked>(m, "InteractionEntityPacked")
        .def(nb::init<>())
        .def_rw("world_index", &gpu::InteractionEntityPacked::world_index)
        .def_rw("local_index", &gpu::InteractionEntityPacked::local_index)
        .def_rw("x", &gpu::InteractionEntityPacked::x)
        .def_rw("y", &gpu::InteractionEntityPacked::y)
        .def_rw("z", &gpu::InteractionEntityPacked::z)
        .def_rw("bounding_radius_m", &gpu::InteractionEntityPacked::bounding_radius_m);

    nb::class_<gpu::InteractionQueryPacked>(m, "InteractionQueryPacked")
        .def(nb::init<>())
        .def_rw("world_index", &gpu::InteractionQueryPacked::world_index)
        .def_rw("x", &gpu::InteractionQueryPacked::x)
        .def_rw("y", &gpu::InteractionQueryPacked::y)
        .def_rw("z", &gpu::InteractionQueryPacked::z)
        .def_rw("range_m", &gpu::InteractionQueryPacked::range_m);

    nb::class_<gpu::InteractionBroadphaseConfig>(m, "InteractionBroadphaseConfig")
        .def(nb::init<>())
        .def_rw("cell_size_m", &gpu::InteractionBroadphaseConfig::cell_size_m)
        .def_rw("max_entity_radius_m", &gpu::InteractionBroadphaseConfig::max_entity_radius_m)
        .def_rw("entities_per_world", &gpu::InteractionBroadphaseConfig::entities_per_world)
        .def_rw("hash_bucket_count", &gpu::InteractionBroadphaseConfig::hash_bucket_count)
        .def_rw("bucket_capacity", &gpu::InteractionBroadphaseConfig::bucket_capacity);

    nb::class_<gpu::InteractionBroadphaseExperimentStats>(m, "InteractionBroadphaseExperimentStats")
        .def(nb::init<>())
        .def_ro("used_cuda", &gpu::InteractionBroadphaseExperimentStats::used_cuda)
        .def_ro("host_to_device_ms", &gpu::InteractionBroadphaseExperimentStats::host_to_device_ms)
        .def_ro("kernel_ms", &gpu::InteractionBroadphaseExperimentStats::kernel_ms)
        .def_ro("device_to_host_ms", &gpu::InteractionBroadphaseExperimentStats::device_to_host_ms)
        .def_ro("total_ms", &gpu::InteractionBroadphaseExperimentStats::total_ms)
        .def_ro("overflow_bucket_count", &gpu::InteractionBroadphaseExperimentStats::overflow_bucket_count)
        .def_ro("overflow_query_count", &gpu::InteractionBroadphaseExperimentStats::overflow_query_count);

    m.def("interaction_broadphase_word_count", &gpu::interaction_broadphase_word_count, nb::arg("entities_per_world"));
    m.def("last_interaction_broadphase_stats", &gpu::last_interaction_broadphase_stats);
    m.def(
        "build_interaction_broadphase_batch_numpy",
        [](const std::vector<gpu::InteractionEntityPacked>& entities,
           const std::vector<gpu::InteractionQueryPacked>& queries,
           const gpu::InteractionBroadphaseConfig& config,
           bool use_gpu) {
            const auto query_count = queries.size();
            const auto words_per_query = gpu::interaction_broadphase_word_count(config.entities_per_world);
            auto out = use_gpu
                ? gpu::build_interaction_broadphase_experiment_batch(entities, queries, config)
                : gpu::build_interaction_broadphase_reference_cpu_batch(entities, queries, config);
            size_t shape[2] = {query_count, words_per_query};
            return uint32_tensor_to_numpy<nb::ndim<2>>(
                std::move(out),
                2,
                shape
            );
        },
        nb::arg("entities"),
        nb::arg("queries"),
        nb::arg("config"),
        nb::arg("use_gpu") = false
    );

    m.def(
        "compute_world_batch_visual_observation_batch_numpy",
        [](WorldBatchRuntime& runtime,
           const std::vector<WorldEntityRef>& refs,
           int downsample,
           bool use_gpu) {
            auto outputs = compute_world_batch_visual_binding_outputs(runtime, refs, downsample, use_gpu);
            size_t shape[4] = {
                outputs.batch_size,
                static_cast<std::size_t>(outputs.out_h),
                static_cast<std::size_t>(outputs.out_w),
                static_cast<std::size_t>(arb::ARB_CHANNELS),
            };
            return visual_tensor_to_numpy<nb::ndim<4>>(std::move(outputs.flat), 4, shape);
        },
        nb::arg("batch_runtime"),
        nb::arg("refs"),
        nb::arg("downsample") = 1,
        nb::arg("use_gpu") = false
    );
    m.def(
        "compute_world_batch_visual_observation_batch_export",
        [](WorldBatchRuntime& runtime,
           const std::vector<WorldEntityRef>& refs,
           int downsample,
           bool use_gpu) {
            auto outputs = compute_world_batch_visual_binding_outputs(runtime, refs, downsample, use_gpu);
            size_t shape[4] = {
                outputs.batch_size,
                static_cast<std::size_t>(outputs.out_h),
                static_cast<std::size_t>(outputs.out_w),
                static_cast<std::size_t>(arb::ARB_CHANNELS),
            };
            nb::object device_view = nb::none();
            if (use_gpu) {
                device_view = maybe_gpu_tensor_view(
                    outputs.device_ptr,
                    outputs.device_float_count,
                    {
                        static_cast<std::int64_t>(outputs.batch_size),
                        static_cast<std::int64_t>(outputs.out_h),
                        static_cast<std::int64_t>(outputs.out_w),
                        static_cast<std::int64_t>(arb::ARB_CHANNELS),
                    }
                );
            }
            return nb::make_tuple(
                visual_tensor_to_numpy<nb::ndim<4>>(std::move(outputs.flat), 4, shape),
                device_view
            );
        },
        nb::arg("batch_runtime"),
        nb::arg("refs"),
        nb::arg("downsample") = 1,
        nb::arg("use_gpu") = false
    );
}
