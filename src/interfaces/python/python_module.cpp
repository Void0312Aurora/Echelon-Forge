#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/tuple.h>

#include <cstdint>

#include "interfaces/python/dlpack_minimal.h"
#include "components/visual/visual_sensor.h"
#include "core/engine/simulation_kernel.h"
#include "core/engine/world_batch_runtime.h"
#include "core/geometry/spatial_query_runtime.h"
#include "core/mission/execution_episode_runtime.h"
#include "core/mission/execution_frame_runtime.h"
#include "core/mission/execution_observation_runtime.h"
#include "core/mission/execution_step_runtime.h"
#include "core/mission/mission_runtime.h"
#include "core/mission/reward_runtime.h"
#include "core/mission/objective_runtime.h"
#include "core/mission/termination_runtime.h"
#include "gpu/gpu_visual_runtime.h"
#include "gpu/gpu_execution_observation_runtime.h"
#include "gpu/gpu_exact_world_step_contract.h"
#include "gpu/gpu_exact_world_step_command_lane_runtime.h"
#include "gpu/gpu_exact_world_step_front_half_runtime.h"
#include "gpu/gpu_exact_world_step_control_aero_runtime.h"
#include "gpu/gpu_exact_world_step_force_ground_runtime.h"
#include "gpu/gpu_exact_world_step_aircraft_tail_runtime.h"
#include "gpu/gpu_exact_world_step_aircraft_tail_cuda_runtime.h"
#include "gpu/gpu_exact_world_step_aircraft_chain_cuda_runtime.h"
#include "gpu/gpu_exact_world_step_first_scope_chain_cuda_runtime.h"
#include "gpu/gpu_exact_world_step_missile_guidance_runtime.h"
#include "gpu/gpu_exact_world_step_missile_guidance_cuda_runtime.h"
#include "gpu/gpu_exact_world_step_runtime.h"
#include "gpu/gpu_flight_shaping_runtime.h"
#include "gpu/gpu_interaction_broadphase_runtime.h"
#include "gpu/gpu_world_batch_runtime.h"
#include "models/environment/default_environment_snapshot.h"
#include "components/systems/comm.h"
#include "core/interfaces/unit_data.h"
#include "core/interfaces/observation.h"
#include "components/basic/common.h"
#include "components/physics/action.h" // Added action.h
#include "components/physics/instruments.h" // Added instruments.h
#include "components/systems/sensor.h"
#include "components/systems/navigation.h" // Added navigation.h
#include <spdlog/spdlog.h>
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <utility>

namespace nb = nanobind;

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

nb::dict exact_world_step_hidden_surface_dict(const gpu::ExactWorldStepStateV1& state) {
    nb::dict out;

    nb::dict environment_sample;
    environment_sample["present"] = nb::bool_(state.has_environment_sample);
    environment_sample["terrain_elevation_m"] = nb::float_(state.environment_sample.terrain_elevation_m);
    environment_sample["wind_vx_mps"] = nb::float_(state.environment_sample.wind_vx_mps);
    environment_sample["wind_vy_mps"] = nb::float_(state.environment_sample.wind_vy_mps);
    environment_sample["terrain_surface_code"] = nb::int_(state.environment_sample.terrain_surface_code);
    environment_sample["runway_heading_deg"] = nb::float_(state.environment_sample.runway_heading_deg);
    out["environment_sample"] = std::move(environment_sample);

    nb::dict angular_velocity;
    angular_velocity["present"] = nb::bool_(state.has_angular_velocity);
    angular_velocity["p_rad_s"] = nb::float_(state.angular_velocity.p);
    angular_velocity["q_rad_s"] = nb::float_(state.angular_velocity.q);
    angular_velocity["r_rad_s"] = nb::float_(state.angular_velocity.r);
    out["angular_velocity"] = std::move(angular_velocity);

    nb::dict force_accumulator;
    force_accumulator["present"] = nb::bool_(state.has_force_accumulator);
    force_accumulator["fx_n"] = nb::float_(state.force_accumulator.fx);
    force_accumulator["fy_n"] = nb::float_(state.force_accumulator.fy);
    force_accumulator["fz_n"] = nb::float_(state.force_accumulator.fz);
    force_accumulator["torque_roll_nm"] = nb::float_(state.force_accumulator.torque_roll);
    force_accumulator["torque_pitch_nm"] = nb::float_(state.force_accumulator.torque_pitch);
    force_accumulator["torque_yaw_nm"] = nb::float_(state.force_accumulator.torque_yaw);
    out["force_accumulator"] = std::move(force_accumulator);

    nb::dict aero_state;
    aero_state["present"] = nb::bool_(state.has_aero_state);
    aero_state["dynamic_pressure_pa"] = nb::float_(state.aero_state.dynamic_pressure);
    aero_state["angle_of_attack_deg"] = nb::float_(state.aero_state.angle_of_attack);
    aero_state["sideslip_angle_deg"] = nb::float_(state.aero_state.sideslip_angle);
    aero_state["mach_number"] = nb::float_(state.aero_state.mach_number);
    aero_state["lift_coefficient"] = nb::float_(state.aero_state.lift_coefficient);
    aero_state["drag_coefficient"] = nb::float_(state.aero_state.drag_coefficient);
    out["aero_state"] = std::move(aero_state);

    nb::dict control_law_state;
    control_law_state["present"] = nb::bool_(state.has_control_law_state);
    control_law_state["stick_roll_filt"] = nb::float_(state.control_law_state.stick_roll_filt);
    control_law_state["stick_pitch_filt"] = nb::float_(state.control_law_state.stick_pitch_filt);
    control_law_state["stick_yaw_filt"] = nb::float_(state.control_law_state.stick_yaw_filt);
    control_law_state["stick_yaw_cmd"] = nb::float_(state.control_law_state.stick_yaw_cmd);
    out["control_law_state"] = std::move(control_law_state);

    nb::dict egi;
    egi["present"] = nb::bool_(state.has_egi);
    egi["lat_deg"] = nb::float_(state.egi.lat_deg);
    egi["lon_deg"] = nb::float_(state.egi.lon_deg);
    egi["alt_baro_m"] = nb::float_(state.egi.alt_baro_m);
    egi["alt_radar_m"] = nb::float_(state.egi.alt_radar_m);
    egi["vn_mps"] = nb::float_(state.egi.vn_mps);
    egi["ve_mps"] = nb::float_(state.egi.ve_mps);
    egi["vd_mps"] = nb::float_(state.egi.vd_mps);
    egi["heading_deg"] = nb::float_(state.egi.heading_deg);
    egi["pitch_deg"] = nb::float_(state.egi.pitch_deg);
    egi["roll_deg"] = nb::float_(state.egi.roll_deg);
    egi["wind_speed_mps"] = nb::float_(state.egi.wind_speed_mps);
    egi["wind_dir_deg"] = nb::float_(state.egi.wind_dir_deg);
    egi["drift_lat_m"] = nb::float_(state.egi.drift_lat_m);
    egi["drift_lon_m"] = nb::float_(state.egi.drift_lon_m);
    egi["drift_alt_m"] = nb::float_(state.egi.drift_alt_m);
    egi["position_uncertainty_m"] = nb::float_(state.egi.position_uncertainty_m);
    egi["time_since_last_gps_fix_s"] = nb::float_(state.egi.time_since_last_gps_fix);
    egi["ins_drift_rate_mps"] = nb::float_(state.egi.ins_drift_rate_mps);
    egi["gps_available"] = nb::bool_(state.egi.gps_available);
    out["egi"] = std::move(egi);

    return out;
}

nb::list exact_world_step_hidden_surface_list(const std::vector<gpu::ExactWorldStepStateV1>& states) {
    nb::list out;
    for (const auto& state : states) {
        out.append(exact_world_step_hidden_surface_dict(state));
    }
    return out;
}

nb::dict exact_world_step_command_surface_dict(const gpu::ExactWorldStepStateV1& state) {
    nb::dict out;
    out["time_step_s"] = nb::float_(state.time_step_s);
    out["world_time_s"] = nb::float_(state.world_time_s);

    nb::dict transform;
    transform["heading_deg"] = nb::float_(state.transform.heading);
    transform["altitude_m"] = nb::float_(state.transform.z);
    out["transform"] = std::move(transform);

    nb::dict velocity;
    velocity["vx_mps"] = nb::float_(state.velocity.vx);
    velocity["vy_mps"] = nb::float_(state.velocity.vy);
    velocity["vz_mps"] = nb::float_(state.velocity.vz);
    out["velocity"] = std::move(velocity);

    nb::dict movement_command;
    movement_command["present"] = nb::bool_(state.has_movement_command);
    movement_command["target_heading_deg"] = nb::float_(state.movement_command.target_heading);
    movement_command["target_speed_mps"] = nb::float_(state.movement_command.target_speed);
    movement_command["target_altitude_m"] = nb::float_(state.movement_command.target_altitude);
    movement_command["use_stick_control"] = nb::bool_(state.movement_command.use_stick_control);
    movement_command["throttle_cmd"] = nb::float_(state.movement_command.throttle_cmd);
    movement_command["gear_handle"] = nb::bool_(state.movement_command.gear_handle);
    movement_command["active"] = nb::bool_(state.movement_command.active);
    out["movement_command"] = std::move(movement_command);

    nb::dict action_command;
    action_command["present"] = nb::bool_(state.has_action_command);
    action_command["turn_rate_cmd"] = nb::float_(state.action_command.turn_rate_cmd);
    action_command["accel_cmd"] = nb::float_(state.action_command.accel_cmd);
    action_command["climb_rate_cmd"] = nb::float_(state.action_command.climb_rate_cmd);
    action_command["fire_cmd"] = nb::float_(state.action_command.fire_cmd);
    action_command["active"] = nb::bool_(state.action_command.active);
    out["action_command"] = std::move(action_command);

    nb::dict mission_command;
    mission_command["present"] = nb::bool_(state.has_mission_command);
    mission_command["cmd_heading_deg"] = nb::float_(state.mission_command.cmd_heading_deg);
    mission_command["cmd_altitude_m"] = nb::float_(state.mission_command.cmd_altitude_m);
    mission_command["cmd_speed_mps"] = nb::float_(state.mission_command.cmd_speed_mps);
    mission_command["command_code"] = nb::int_(state.mission_command.command_code);
    mission_command["active"] = nb::bool_(state.mission_command.active);
    out["mission_command"] = std::move(mission_command);

    nb::dict action_space_config;
    action_space_config["present"] = nb::bool_(state.has_action_space_config);
    action_space_config["max_turn_rate_deg_s"] = nb::float_(state.action_space_config.max_turn_rate_deg_s);
    action_space_config["max_accel_mps2"] = nb::float_(state.action_space_config.max_accel_mps2);
    action_space_config["max_climb_rate_mps"] = nb::float_(state.action_space_config.max_climb_rate_mps);
    action_space_config["min_speed_mps"] = nb::float_(state.action_space_config.min_speed_mps);
    action_space_config["max_speed_mps"] = nb::float_(state.action_space_config.max_speed_mps);
    action_space_config["min_alt_m"] = nb::float_(state.action_space_config.min_alt_m);
    action_space_config["max_alt_m"] = nb::float_(state.action_space_config.max_alt_m);
    out["action_space_config"] = std::move(action_space_config);

    nb::dict command_lag;
    command_lag["present"] = nb::bool_(state.has_command_lag);
    command_lag["heading_tau_s"] = nb::float_(state.command_lag.heading_tau_s);
    command_lag["speed_tau_s"] = nb::float_(state.command_lag.speed_tau_s);
    command_lag["altitude_tau_s"] = nb::float_(state.command_lag.altitude_tau_s);
    out["command_lag"] = std::move(command_lag);

    nb::dict lagged_command;
    lagged_command["present"] = nb::bool_(state.has_lagged_command);
    lagged_command["target_heading_deg"] = nb::float_(state.lagged_command.target_heading);
    lagged_command["target_speed_mps"] = nb::float_(state.lagged_command.target_speed);
    lagged_command["target_altitude_m"] = nb::float_(state.lagged_command.target_altitude);
    lagged_command["active"] = nb::bool_(state.lagged_command.active);
    out["lagged_command"] = std::move(lagged_command);

    nb::dict command_link;
    command_link["present"] = nb::bool_(state.has_command_link);
    command_link["latency_s"] = nb::float_(state.command_link.latency_s);
    command_link["drop_prob"] = nb::float_(state.command_link.drop_prob);
    out["command_link"] = std::move(command_link);

    nb::dict pending_movement_command;
    pending_movement_command["present"] = nb::bool_(state.has_pending_movement_command);
    pending_movement_command["deliver_time_s"] = nb::float_(state.pending_movement_command.deliver_time);
    pending_movement_command["active"] = nb::bool_(state.pending_movement_command.active);
    out["pending_movement_command"] = std::move(pending_movement_command);

    nb::dict pending_action_command;
    pending_action_command["present"] = nb::bool_(state.has_pending_action_command);
    pending_action_command["deliver_time_s"] = nb::float_(state.pending_action_command.deliver_time);
    pending_action_command["active"] = nb::bool_(state.pending_action_command.active);
    out["pending_action_command"] = std::move(pending_action_command);

    nb::dict pending_mission_command;
    pending_mission_command["present"] = nb::bool_(state.has_pending_mission_command);
    pending_mission_command["deliver_time_s"] = nb::float_(state.pending_mission_command.deliver_time);
    pending_mission_command["active"] = nb::bool_(state.pending_mission_command.active);
    out["pending_mission_command"] = std::move(pending_mission_command);

    return out;
}

nb::list exact_world_step_command_surface_list(const std::vector<gpu::ExactWorldStepStateV1>& states) {
    nb::list out;
    for (const auto& state : states) {
        out.append(exact_world_step_command_surface_dict(state));
    }
    return out;
}

nb::dict exact_world_step_combat_surface_dict(const gpu::ExactWorldStepStateV1& state) {
    nb::dict out;

    nb::dict missile;
    missile["present"] = nb::bool_(state.has_missile);
    missile["attacker_id"] = nb::int_(state.missile.attacker_id);
    missile["target_id"] = nb::int_(state.missile.target_id);
    missile["max_speed_mps"] = nb::float_(state.missile.max_speed);
    missile["turn_rate_deg_s"] = nb::float_(state.missile.turn_rate);
    missile["fuse_distance_m"] = nb::float_(state.missile.fuse_distance);
    missile["damage"] = nb::float_(state.missile.damage);
    missile["seeker_fov_deg"] = nb::float_(state.missile.seeker_fov_deg);
    missile["seeker_lock_range_m"] = nb::float_(state.missile.seeker_lock_range);
    missile["guidance_delay_s"] = nb::float_(state.missile.guidance_delay_s);
    missile["guidance_update_period_s"] = nb::float_(state.missile.guidance_update_period_s);
    missile["last_guidance_time_s"] = nb::float_(state.missile.last_guidance_time);
    missile["launch_time_s"] = nb::float_(state.missile.launch_time);
    missile["max_flight_time_s"] = nb::float_(state.missile.max_flight_time_s);
    missile["nav_gain"] = nb::float_(state.missile.nav_gain);
    missile["active"] = nb::bool_(state.missile.active);
    missile["rng_state"] = nb::int_(state.missile.rng_state);
    missile["proximity_min_dist_m"] = nb::float_(state.missile.proximity_min_dist_m);
    missile["proximity_last_dist_m"] = nb::float_(state.missile.proximity_last_dist_m);
    missile["proximity_engaged"] = nb::bool_(state.missile.proximity_engaged);
    out["missile"] = std::move(missile);

    nb::dict contacts;
    contacts["present"] = nb::bool_(state.has_contact_list_summary);
    contacts["count"] = nb::int_(state.contact_list_summary.count);
    contacts["truncated"] = nb::bool_(state.contact_list_summary.truncated);
    nb::list items;
    const auto count = std::min<std::size_t>(
        state.contact_list_summary.count,
        gpu::kExactWorldStepContactSummaryCapacity
    );
    for (std::size_t i = 0; i < count; ++i) {
        const auto& detection = state.contact_list_summary.contacts[i];
        nb::dict item;
        item["target_id"] = nb::int_(detection.target_id);
        item["range_m"] = nb::float_(detection.range);
        item["bearing_deg"] = nb::float_(detection.bearing);
        item["elevation_deg"] = nb::float_(detection.elevation);
        item["closing_speed_mps"] = nb::float_(detection.closing_speed);
        item["signal_strength"] = nb::float_(detection.signal_strength);
        item["timestamp_s"] = nb::float_(detection.timestamp);
        items.append(std::move(item));
    }
    contacts["items"] = std::move(items);
    out["contact_list_summary"] = std::move(contacts);

    return out;
}

nb::list exact_world_step_combat_surface_list(const std::vector<gpu::ExactWorldStepStateV1>& states) {
    nb::list out;
    for (const auto& state : states) {
        out.append(exact_world_step_combat_surface_dict(state));
    }
    return out;
}

nb::dict exact_step_stage_descriptor_dict(const ExactStepStageDescriptor& descriptor) {
    nb::dict out;
    out["order"] = nb::int_(descriptor.order);
    out["name"] = nb::str(descriptor.name.c_str());
    out["flecs_kind"] = nb::str(descriptor.flecs_kind.c_str());
    out["domain"] = nb::str(descriptor.domain.c_str());
    out["notes"] = nb::str(descriptor.notes.c_str());
    out["gpu_migration_scope"] = nb::bool_(descriptor.gpu_migration_scope);
    out["manual_trace_supported"] = nb::bool_(descriptor.manual_trace_supported);
    return out;
}

nb::list exact_step_stage_descriptor_list(const std::vector<ExactStepStageDescriptor>& descriptors) {
    nb::list out;
    for (const auto& descriptor : descriptors) {
        out.append(exact_step_stage_descriptor_dict(descriptor));
    }
    return out;
}

nb::list string_vector_list(const std::vector<std::string>& values) {
    nb::list out;
    for (const auto& value : values) {
        out.append(nb::str(value.c_str()));
    }
    return out;
}

nb::dict exact_step_stage_contract_descriptor_dict(const ExactStepStageContractDescriptor& descriptor) {
    nb::dict out;
    out["order"] = nb::int_(descriptor.order);
    out["name"] = nb::str(descriptor.name.c_str());
    out["flecs_kind"] = nb::str(descriptor.flecs_kind.c_str());
    out["domain"] = nb::str(descriptor.domain.c_str());
    out["gpu_migration_scope"] = nb::bool_(descriptor.gpu_migration_scope);
    out["manual_trace_supported"] = nb::bool_(descriptor.manual_trace_supported);
    out["reads"] = string_vector_list(descriptor.reads);
    out["writes"] = string_vector_list(descriptor.writes);
    out["trace_surfaces"] = string_vector_list(descriptor.trace_surfaces);
    out["depends_on_stages"] = string_vector_list(descriptor.depends_on_stages);
    out["contract_summary"] = nb::str(descriptor.contract_summary.c_str());
    out["exact_dependency_notes"] = nb::str(descriptor.exact_dependency_notes.c_str());
    return out;
}

nb::list exact_step_stage_contract_descriptor_list(const std::vector<ExactStepStageContractDescriptor>& descriptors) {
    nb::list out;
    for (const auto& descriptor : descriptors) {
        out.append(exact_step_stage_contract_descriptor_dict(descriptor));
    }
    return out;
}

const char* default_unit_name_for(UnitType type) {
    switch (type) {
        case UnitType::Aircraft:
            return "Aircraft";
        case UnitType::Ship:
            return "Ship";
        case UnitType::Missile:
            return "Missile";
        case UnitType::Facility:
            return "Facility";
        case UnitType::C2Node:
            return "AWACS";
        default:
            throw std::invalid_argument("Unsupported UnitType for spawn_unit (use type_name string instead)");
    }
}

template <typename Shape>
auto visual_tensor_to_numpy(std::vector<float>&& data, size_t ndim, const size_t* shape) {
    auto* output = new std::vector<float>(std::move(data));
    nb::capsule owner(output, [](void* ptr) noexcept {
        delete static_cast<std::vector<float>*>(ptr);
    });
    return nb::ndarray<nb::numpy, const float, Shape>(output->data(), ndim, shape, owner);
}

template <typename Shape>
auto uint32_tensor_to_numpy(std::vector<std::uint32_t>&& data, size_t ndim, const size_t* shape) {
    auto* output = new std::vector<std::uint32_t>(std::move(data));
    nb::capsule owner(output, [](void* ptr) noexcept {
        delete static_cast<std::vector<std::uint32_t>*>(ptr);
    });
    return nb::ndarray<nb::numpy, const std::uint32_t, Shape>(output->data(), ndim, shape, owner);
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

std::vector<float> downsample_visual_tensor(std::vector<float>&& input, int factor) {
    using namespace arb;

    if (factor <= 1) {
        return std::move(input);
    }
    if (ARB_HEIGHT % factor != 0 || ARB_WIDTH % factor != 0) {
        throw std::invalid_argument("visual downsample factor must divide native ARB dimensions");
    }

    const size_t in_height = static_cast<size_t>(ARB_HEIGHT);
    const size_t in_width = static_cast<size_t>(ARB_WIDTH);
    const size_t channels = static_cast<size_t>(ARB_CHANNELS);
    const size_t out_height = in_height / static_cast<size_t>(factor);
    const size_t out_width = in_width / static_cast<size_t>(factor);
    const size_t area = static_cast<size_t>(factor) * static_cast<size_t>(factor);

    std::vector<float> output(out_height * out_width * channels, 0.0f);
    const float* src = input.data();
    float* dst = output.data();
    const float scale = 1.0f / static_cast<float>(area);

    for (size_t oy = 0; oy < out_height; ++oy) {
        const size_t iy0 = oy * static_cast<size_t>(factor);
        for (size_t ox = 0; ox < out_width; ++ox) {
            const size_t ix0 = ox * static_cast<size_t>(factor);
            const size_t out_base = (oy * out_width + ox) * channels;
            for (int fy = 0; fy < factor; ++fy) {
                const size_t iy = iy0 + static_cast<size_t>(fy);
                for (int fx = 0; fx < factor; ++fx) {
                    const size_t ix = ix0 + static_cast<size_t>(fx);
                    const size_t in_base = (iy * in_width + ix) * channels;
                    for (size_t c = 0; c < channels; ++c) {
                        dst[out_base + c] += src[in_base + c];
                    }
                }
            }
            for (size_t c = 0; c < channels; ++c) {
                dst[out_base + c] *= scale;
            }
        }
    }

    return output;
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

NB_MODULE(ef_py, m) {
    m.def("set_log_level", [](const std::string& level) {
        if (level == "trace") spdlog::set_level(spdlog::level::trace);
        else if (level == "debug") spdlog::set_level(spdlog::level::debug);
        else if (level == "info") spdlog::set_level(spdlog::level::info);
        else if (level == "warn") spdlog::set_level(spdlog::level::warn);
        else if (level == "error") spdlog::set_level(spdlog::level::err);
        else if (level == "critical") spdlog::set_level(spdlog::level::critical);
        else if (level == "off") spdlog::set_level(spdlog::level::off);
    }, "Set global log level (trace/debug/info/warn/error/critical/off)", nb::arg("level"));
    // Bind Side Enum
    nb::enum_<Side>(m, "Side")
        .value("Blue", Side::Blue)
        .value("Red", Side::Red)
        .value("Neutral", Side::Neutral)
        .value("Unknown", Side::Unknown)
        .export_values();

    nb::enum_<CommMsgType>(m, "CommMsgType")
        .value("None", CommMsgType::None)
        .value("REP_WILCO", CommMsgType::REP_WILCO)
        .value("REP_ROGER", CommMsgType::REP_ROGER)
        .value("REP_UNABLE", CommMsgType::REP_UNABLE)
        .value("REP_CANT_DO", CommMsgType::REP_CANT_DO)
        .value("STATUS_FUEL", CommMsgType::STATUS_FUEL)
        .value("STATUS_AMMO", CommMsgType::STATUS_AMMO)
        .value("STATUS_DAMAGE", CommMsgType::STATUS_DAMAGE)
        .value("STATUS_POS", CommMsgType::STATUS_POS)
        .value("REP_TALLY", CommMsgType::REP_TALLY)
        .value("REP_VISUAL", CommMsgType::REP_VISUAL)
        .value("REP_BLIND", CommMsgType::REP_BLIND)
        .value("REP_SPIKE", CommMsgType::REP_SPIKE)
        .value("REP_FAILED_SORT", CommMsgType::REP_FAILED_SORT)
        .value("REP_ENGAGED", CommMsgType::REP_ENGAGED)
        .value("REP_SPLASH", CommMsgType::REP_SPLASH)
        .value("REP_DEFENDING", CommMsgType::REP_DEFENDING)
        .value("REP_ON_STATION", CommMsgType::REP_ON_STATION)
        .value("REP_FENCE_IN", CommMsgType::REP_FENCE_IN)
        .value("REP_FENCE_OUT", CommMsgType::REP_FENCE_OUT)
        .value("REP_RTB", CommMsgType::REP_RTB)
        .value("WARN_FLAMEOUT", CommMsgType::WARN_FLAMEOUT)
        .value("WARN_BINGO", CommMsgType::WARN_BINGO)
        .value("WARN_LAUNCH", CommMsgType::WARN_LAUNCH)
        .value("ACK_WILCO", CommMsgType::ACK_WILCO)
        .value("ACK_ROGER", CommMsgType::ACK_ROGER)
        .value("ACK_UNABLE", CommMsgType::ACK_UNABLE)
        .value("ACK_CANT_DO", CommMsgType::ACK_CANT_DO)
        .value("ReportContact", CommMsgType::ReportContact)
        .value("AssignTask", CommMsgType::AssignTask)
        .value("StatusUpdate", CommMsgType::StatusUpdate)
        .value("RequestSupport", CommMsgType::RequestSupport)
        .value("REP_JOINED", CommMsgType::REP_JOINED)
        .value("REP_REJOINING", CommMsgType::REP_REJOINING)
        .value("REP_FORM_LOST", CommMsgType::REP_FORM_LOST)
        .value("REP_UNABLE_FORM", CommMsgType::REP_UNABLE_FORM)
        .value("REP_SUPPORTING", CommMsgType::REP_SUPPORTING)
        .value("WARN_SEPARATION", CommMsgType::WARN_SEPARATION)
        .export_values();

    nb::enum_<TaskType>(m, "TaskType")
        .value("Idle", TaskType::Idle)
        .value("Scramble", TaskType::Scramble)
        .value("CAP", TaskType::CAP)
        .value("RTB", TaskType::RTB)
        .value("RecoverLand", TaskType::RecoverLand)
        .value("CAPMission", TaskType::CAPMission);

    nb::enum_<StationType>(m, "StationType")
        .value("Orbit", StationType::Orbit)
        .value("Racetrack", StationType::Racetrack)
        .value("RouteCAP", StationType::RouteCAP);

    nb::enum_<LeaderPhase>(m, "LeaderPhase")
        .value("Idle", LeaderPhase::Idle)
        .value("Scramble", LeaderPhase::Scramble)
        .value("Takeoff", LeaderPhase::Takeoff)
        .value("Departure", LeaderPhase::Departure)
        .value("TransitToStation", LeaderPhase::TransitToStation)
        .value("EstablishCAP", LeaderPhase::EstablishCAP)
        .value("OnStation", LeaderPhase::OnStation)
        .value("Reposition", LeaderPhase::Reposition)
        .value("RTB", LeaderPhase::RTB)
        .value("ApproachArmed", LeaderPhase::ApproachArmed)
        .value("LandingFinal", LeaderPhase::LandingFinal)
        .value("Rollout", LeaderPhase::Rollout)
        .value("Abort", LeaderPhase::Abort);

    nb::enum_<RecoveryApproachType>(m, "RecoveryApproachType")
        .value("None", RecoveryApproachType::None)
        .value("StraightIn", RecoveryApproachType::StraightIn)
        .value("ILS", RecoveryApproachType::ILS)
        .value("Visual", RecoveryApproachType::Visual)
        .value("Overhead", RecoveryApproachType::Overhead)
        .value("TACAN", RecoveryApproachType::TACAN);

    nb::enum_<ServiceProfile>(m, "ServiceProfile")
        .value("Unspecified", ServiceProfile::Unspecified)
        .value("AirForce", ServiceProfile::AirForce)
        .value("Army", ServiceProfile::Army)
        .value("Navy", ServiceProfile::Navy)
        .value("MarineCorps", ServiceProfile::MarineCorps);

    nb::enum_<TaskFamily>(m, "TaskFamily")
        .value("Unspecified", TaskFamily::Unspecified)
        .value("Transit", TaskFamily::Transit)
        .value("Patrol", TaskFamily::Patrol)
        .value("Escort", TaskFamily::Escort)
        .value("Intercept", TaskFamily::Intercept)
        .value("Attack", TaskFamily::Attack)
        .value("Defend", TaskFamily::Defend)
        .value("Recover", TaskFamily::Recover)
        .value("Withdraw", TaskFamily::Withdraw);

    nb::enum_<TacticalUnitType>(m, "TacticalUnitType")
        .value("Unspecified", TacticalUnitType::Unspecified)
        .value("Platform", TacticalUnitType::Platform)
        .value("TacticalUnit", TacticalUnitType::TacticalUnit)
        .value("MissionPackage", TacticalUnitType::MissionPackage)
        .value("CommandNode", TacticalUnitType::CommandNode);

    nb::enum_<CommandRelationship>(m, "CommandRelationship")
        .value("None", CommandRelationship::None)
        .value("COCOM", CommandRelationship::COCOM)
        .value("OPCON", CommandRelationship::OPCON)
        .value("TACON", CommandRelationship::TACON)
        .value("Support", CommandRelationship::Support)
        .value("ADCON", CommandRelationship::ADCON)
        .value("CoordinatingAuthority", CommandRelationship::CoordinatingAuthority)
        .value("DIRLAUTH", CommandRelationship::DIRLAUTH);

    nb::enum_<AuthorityScope>(m, "AuthorityScope")
        .value("Unspecified", AuthorityScope::Unspecified)
        .value("Strategic", AuthorityScope::Strategic)
        .value("Operational", AuthorityScope::Operational)
        .value("Tactical", AuthorityScope::Tactical)
        .value("Execution", AuthorityScope::Execution);

    nb::enum_<AssigneeKind>(m, "AssigneeKind")
        .value("Aircraft", AssigneeKind::Aircraft)
        .value("Element", AssigneeKind::Element)
        .value("Package", AssigneeKind::Package);

    nb::enum_<FormationRole>(m, "FormationRole")
        .value("Unspecified", FormationRole::Unspecified)
        .value("ElementLead", FormationRole::ElementLead)
        .value("Wingman", FormationRole::Wingman);

    nb::enum_<WingmanSlot>(m, "WingmanSlot")
        .value("Unspecified", WingmanSlot::Unspecified)
        .value("Left", WingmanSlot::Left)
        .value("Right", WingmanSlot::Right)
        .value("Trail", WingmanSlot::Trail);

    nb::enum_<FormationMode>(m, "FormationMode")
        .value("Unspecified", FormationMode::Unspecified)
        .value("Prejoin", FormationMode::Prejoin)
        .value("Joining", FormationMode::Joining)
        .value("Cruise", FormationMode::Cruise)
        .value("CAP", FormationMode::CAP)
        .value("Rejoin", FormationMode::Rejoin)
        .value("Recover", FormationMode::Recover)
        .value("SplitAbort", FormationMode::SplitAbort);

    nb::enum_<WingmanCommandMode>(m, "WingmanCommandMode")
        .value("None", WingmanCommandMode::None)
        .value("HoldSlot", WingmanCommandMode::HoldSlot)
        .value("Rejoin", WingmanCommandMode::Rejoin)
        .value("OffsetLeft", WingmanCommandMode::OffsetLeft)
        .value("OffsetRight", WingmanCommandMode::OffsetRight)
        .value("Trail", WingmanCommandMode::Trail)
        .value("Support", WingmanCommandMode::Support)
        .value("AbortForm", WingmanCommandMode::AbortForm);

    nb::enum_<CoordinationMode>(m, "CoordinationMode")
        .value("Unspecified", CoordinationMode::Unspecified)
        .value("Independent", CoordinationMode::Independent)
        .value("Attached", CoordinationMode::Attached)
        .value("Follow", CoordinationMode::Follow)
        .value("Support", CoordinationMode::Support)
        .value("Screen", CoordinationMode::Screen)
        .value("Rejoin", CoordinationMode::Rejoin)
        .value("Recover", CoordinationMode::Recover)
        .value("Detached", CoordinationMode::Detached);

    nb::class_<CommPacket>(m, "CommPacket")
        .def(nb::init<>())
        .def_rw("sender_id", &CommPacket::sender_id)
        .def_rw("target_receiver_id", &CommPacket::target_receiver_id)
        .def_rw("type", &CommPacket::type)
        .def_rw("entity_ref", &CommPacket::entity_ref)
        .def_rw("location_x", &CommPacket::location_x)
        .def_rw("location_y", &CommPacket::location_y)
        .def_rw("location_z", &CommPacket::location_z)
        .def_rw("value", &CommPacket::value)
        .def_rw("status_code", &CommPacket::status_code)
        .def_rw("timestamp", &CommPacket::timestamp);

    nb::class_<PilotReport>(m, "PilotReport")
        .def(nb::init<>())
        .def_rw("report_type", &PilotReport::report_type)
        .def_rw("sender_id", &PilotReport::sender_id)
        .def_rw("task_id", &PilotReport::task_id)
        .def_rw("service_profile", &PilotReport::service_profile)
        .def_rw("task_family", &PilotReport::task_family)
        .def_rw("tactical_unit_type", &PilotReport::tactical_unit_type)
        .def_rw("tactical_unit_id", &PilotReport::tactical_unit_id)
        .def_rw("task_group_id", &PilotReport::task_group_id)
        .def_rw("role_code", &PilotReport::role_code)
        .def_rw("coordination_mode", &PilotReport::coordination_mode)
        .def_rw("element_id", &PilotReport::element_id)
        .def_rw("phase_id", &PilotReport::phase_id)
        .def_rw("formation_role_id", &PilotReport::formation_role_id)
        .def_rw("timestamp_s", &PilotReport::timestamp_s)
        .def_rw("status_value", &PilotReport::status_value)
        .def_rw("entity_ref", &PilotReport::entity_ref)
        .def_rw("location_x_m", &PilotReport::location_x_m)
        .def_rw("location_y_m", &PilotReport::location_y_m)
        .def_rw("location_z_m", &PilotReport::location_z_m)
        .def_rw("formation_error_m", &PilotReport::formation_error_m)
        .def_rw("bearing_error_deg", &PilotReport::bearing_error_deg)
        .def_rw("closure_mps", &PilotReport::closure_mps)
        .def_rw("separation_m", &PilotReport::separation_m)
        .def_rw("active", &PilotReport::active);

    nb::class_<SpatialRunwayDefinition>(m, "SpatialRunwayDefinition")
        .def(nb::init<>())
        .def_rw("runway_id", &SpatialRunwayDefinition::runway_id)
        .def_rw("name", &SpatialRunwayDefinition::name)
        .def_rw("center_x_m", &SpatialRunwayDefinition::center_x_m)
        .def_rw("center_y_m", &SpatialRunwayDefinition::center_y_m)
        .def_rw("threshold_x_m", &SpatialRunwayDefinition::threshold_x_m)
        .def_rw("threshold_y_m", &SpatialRunwayDefinition::threshold_y_m)
        .def_rw("heading_deg", &SpatialRunwayDefinition::heading_deg)
        .def_rw("length_m", &SpatialRunwayDefinition::length_m)
        .def_rw("width_m", &SpatialRunwayDefinition::width_m)
        .def_rw("elevation_m", &SpatialRunwayDefinition::elevation_m)
        .def_rw("glide_slope_deg", &SpatialRunwayDefinition::glide_slope_deg)
        .def_rw("localizer_max_deg", &SpatialRunwayDefinition::localizer_max_deg)
        .def_rw("glideslope_max_deg", &SpatialRunwayDefinition::glideslope_max_deg)
        .def_rw("range_m", &SpatialRunwayDefinition::range_m);

    nb::class_<SpatialRouteWaypoint>(m, "SpatialRouteWaypoint")
        .def(nb::init<>())
        .def_rw("x_m", &SpatialRouteWaypoint::x_m)
        .def_rw("y_m", &SpatialRouteWaypoint::y_m)
        .def_rw("z_m", &SpatialRouteWaypoint::z_m)
        .def_rw("radius_m", &SpatialRouteWaypoint::radius_m)
        .def_rw("altitude_m", &SpatialRouteWaypoint::altitude_m)
        .def_rw("speed_mps", &SpatialRouteWaypoint::speed_mps)
        .def_rw("waypoint_mode", &SpatialRouteWaypoint::waypoint_mode);

    nb::class_<SpatialRunwayFrameResult>(m, "SpatialRunwayFrameResult")
        .def(nb::init<>())
        .def_ro("valid", &SpatialRunwayFrameResult::valid)
        .def_ro("runway_id", &SpatialRunwayFrameResult::runway_id)
        .def_ro("along_m", &SpatialRunwayFrameResult::along_m)
        .def_ro("cross_m", &SpatialRunwayFrameResult::cross_m)
        .def_ro("length_m", &SpatialRunwayFrameResult::length_m)
        .def_ro("width_m", &SpatialRunwayFrameResult::width_m)
        .def_ro("heading_deg", &SpatialRunwayFrameResult::heading_deg);

    nb::class_<SpatialILSResult>(m, "SpatialILSResult")
        .def(nb::init<>())
        .def_ro("valid", &SpatialILSResult::valid)
        .def_ro("runway_id", &SpatialILSResult::runway_id)
        .def_ro("loc_dev", &SpatialILSResult::loc_dev)
        .def_ro("gs_dev", &SpatialILSResult::gs_dev)
        .def_ro("dme_m", &SpatialILSResult::dme_m)
        .def_ro("approach_dist_m", &SpatialILSResult::approach_dist_m)
        .def_ro("heading_deg", &SpatialILSResult::heading_deg);

    nb::class_<SpatialRouteQueryOptions>(m, "SpatialRouteQueryOptions")
        .def(nb::init<>())
        .def_rw("waypoint_index", &SpatialRouteQueryOptions::waypoint_index)
        .def_rw("own_x_m", &SpatialRouteQueryOptions::own_x_m)
        .def_rw("own_y_m", &SpatialRouteQueryOptions::own_y_m)
        .def_rw("own_speed_mps", &SpatialRouteQueryOptions::own_speed_mps)
        .def_rw("base_lookahead_m", &SpatialRouteQueryOptions::base_lookahead_m)
        .def_rw("lnav_max_intercept_deg", &SpatialRouteQueryOptions::lnav_max_intercept_deg)
        .def_rw("lnav_capture_max_intercept_deg", &SpatialRouteQueryOptions::lnav_capture_max_intercept_deg)
        .def_rw("lnav_capture_xtrack_m", &SpatialRouteQueryOptions::lnav_capture_xtrack_m)
        .def_rw("lnav_capture_course_error_deg", &SpatialRouteQueryOptions::lnav_capture_course_error_deg)
        .def_rw("lnav_direct_to_final_fix", &SpatialRouteQueryOptions::lnav_direct_to_final_fix)
        .def_rw("lnav_flyover_capture_window_m", &SpatialRouteQueryOptions::lnav_flyover_capture_window_m)
        .def_rw("lnav_bank_limit_deg", &SpatialRouteQueryOptions::lnav_bank_limit_deg)
        .def_rw("lnav_sequence_gate_scale", &SpatialRouteQueryOptions::lnav_sequence_gate_scale)
        .def_rw("lnav_sequence_gate_min_m", &SpatialRouteQueryOptions::lnav_sequence_gate_min_m)
        .def_rw("lnav_sequence_gate_max_m", &SpatialRouteQueryOptions::lnav_sequence_gate_max_m);

    nb::class_<SpatialRouteQueryResult>(m, "SpatialRouteQueryResult")
        .def(nb::init<>())
        .def_ro("valid", &SpatialRouteQueryResult::valid)
        .def_ro("idx", &SpatialRouteQueryResult::idx)
        .def_ro("count", &SpatialRouteQueryResult::count)
        .def_ro("waypoint_mode", &SpatialRouteQueryResult::waypoint_mode)
        .def_ro("sx_m", &SpatialRouteQueryResult::sx_m)
        .def_ro("sy_m", &SpatialRouteQueryResult::sy_m)
        .def_ro("ex_m", &SpatialRouteQueryResult::ex_m)
        .def_ro("ey_m", &SpatialRouteQueryResult::ey_m)
        .def_ro("lx_m", &SpatialRouteQueryResult::lx_m)
        .def_ro("ly_m", &SpatialRouteQueryResult::ly_m)
        .def_ro("leg_len_m", &SpatialRouteQueryResult::leg_len_m)
        .def_ro("dist_m", &SpatialRouteQueryResult::dist_m)
        .def_ro("direct_to_track_deg", &SpatialRouteQueryResult::direct_to_track_deg)
        .def_ro("desired_track_deg", &SpatialRouteQueryResult::desired_track_deg)
        .def_ro("reward_desired_track_deg", &SpatialRouteQueryResult::reward_desired_track_deg)
        .def_ro("xtk_m", &SpatialRouteQueryResult::xtk_m)
        .def_ro("reward_xtk_m", &SpatialRouteQueryResult::reward_xtk_m)
        .def_ro("along_m", &SpatialRouteQueryResult::along_m)
        .def_ro("dtg_m", &SpatialRouteQueryResult::dtg_m)
        .def_ro("reward_dtg_m", &SpatialRouteQueryResult::reward_dtg_m)
        .def_ro("waypoint_radius_m", &SpatialRouteQueryResult::waypoint_radius_m)
        .def_ro("cmd_track_deg", &SpatialRouteQueryResult::cmd_track_deg)
        .def_ro("lookahead_m", &SpatialRouteQueryResult::lookahead_m)
        .def_ro("next_turn_deg", &SpatialRouteQueryResult::next_turn_deg)
        .def_ro("next_turn_abs_deg", &SpatialRouteQueryResult::next_turn_abs_deg)
        .def_ro("prev_turn_abs_deg", &SpatialRouteQueryResult::prev_turn_abs_deg)
        .def_ro("lead_turn_m", &SpatialRouteQueryResult::lead_turn_m)
        .def_ro("sequence_gate_m", &SpatialRouteQueryResult::sequence_gate_m)
        .def_ro("distance_to_turn_m", &SpatialRouteQueryResult::distance_to_turn_m)
        .def_ro("dist_to_next_turn_start_m", &SpatialRouteQueryResult::dist_to_next_turn_start_m)
        .def_ro("distance_from_prev_turn_m", &SpatialRouteQueryResult::distance_from_prev_turn_m)
        .def_ro("use_direct_to", &SpatialRouteQueryResult::use_direct_to)
        .def_ro("direct_to_fix_guidance", &SpatialRouteQueryResult::direct_to_fix_guidance)
        .def_ro("final_leg", &SpatialRouteQueryResult::final_leg)
        .def_ro("passed_fix", &SpatialRouteQueryResult::passed_fix);

    nb::class_<CompiledScenarioGeometry>(m, "CompiledScenarioGeometry")
        .def(nb::init<>())
        .def("clear", &CompiledScenarioGeometry::clear)
        .def("clear_runways", &CompiledScenarioGeometry::clear_runways)
        .def("add_runway", &CompiledScenarioGeometry::add_runway, nb::arg("runway"))
        .def("clear_route", &CompiledScenarioGeometry::clear_route)
        .def("set_route_leg_origin", &CompiledScenarioGeometry::set_route_leg_origin, nb::arg("x_m"), nb::arg("y_m"))
        .def("add_route_waypoint", &CompiledScenarioGeometry::add_route_waypoint, nb::arg("waypoint"))
        .def("runway_count", &CompiledScenarioGeometry::runway_count)
        .def("route_waypoint_count", &CompiledScenarioGeometry::route_waypoint_count)
        .def("query_runway_local_frame", &CompiledScenarioGeometry::query_runway_local_frame, nb::arg("x_m"), nb::arg("y_m"))
        .def("query_ils", &CompiledScenarioGeometry::query_ils, nb::arg("x_m"), nb::arg("y_m"), nb::arg("alt_m"), nb::arg("threshold_crossing_height_m") = 0.0)
        .def("query_route_guidance", &CompiledScenarioGeometry::query_route_guidance, nb::arg("options"));

    nb::class_<MissionNavInputs>(m, "MissionNavInputs")
        .def(nb::init<>())
        .def_rw("own_altitude_m", &MissionNavInputs::own_altitude_m)
        .def_rw("truth_heading_deg", &MissionNavInputs::truth_heading_deg)
        .def_rw("truth_speed_mps", &MissionNavInputs::truth_speed_mps)
        .def_rw("inst_heading_deg", &MissionNavInputs::inst_heading_deg)
        .def_rw("inst_ground_track_deg", &MissionNavInputs::inst_ground_track_deg)
        .def_rw("inst_ias_mps", &MissionNavInputs::inst_ias_mps)
        .def_rw("waypoint_altitude_m", &MissionNavInputs::waypoint_altitude_m)
        .def_rw("cdi_full_scale_m", &MissionNavInputs::cdi_full_scale_m);

    nb::class_<MissionNavProducts>(m, "MissionNavProducts")
        .def(nb::init<>())
        .def_ro("valid", &MissionNavProducts::valid)
        .def_ro("active_wp_idx", &MissionNavProducts::active_wp_idx)
        .def_ro("total_wps", &MissionNavProducts::total_wps)
        .def_ro("selected_steerpoint", &MissionNavProducts::selected_steerpoint)
        .def_ro("steerpoint_mode_code", &MissionNavProducts::steerpoint_mode_code)
        .def_ro("dist_m", &MissionNavProducts::dist_m)
        .def_ro("xtk_m", &MissionNavProducts::xtk_m)
        .def_ro("dtg_m", &MissionNavProducts::dtg_m)
        .def_ro("direct_bearing_deg", &MissionNavProducts::direct_bearing_deg)
        .def_ro("desired_leg_track_deg", &MissionNavProducts::desired_leg_track_deg)
        .def_ro("bearing_rel_deg", &MissionNavProducts::bearing_rel_deg)
        .def_ro("altitude_delta_m", &MissionNavProducts::altitude_delta_m)
        .def_ro("cdi_norm", &MissionNavProducts::cdi_norm)
        .def_ro("track_angle_error_deg", &MissionNavProducts::track_angle_error_deg)
        .def_ro("next_turn_deg", &MissionNavProducts::next_turn_deg)
        .def_ro("distance_to_turn_m", &MissionNavProducts::distance_to_turn_m)
        .def_ro("own_heading_deg", &MissionNavProducts::own_heading_deg)
        .def_ro("ground_track_deg", &MissionNavProducts::ground_track_deg)
        .def_ro("reference_speed_mps", &MissionNavProducts::reference_speed_mps);

    nb::class_<MissionObservationInputs>(m, "MissionObservationInputs")
        .def(nb::init<>())
        .def_rw("mode_code", &MissionObservationInputs::mode_code)
        .def_rw("command_code", &MissionObservationInputs::command_code)
        .def_rw("target_heading_deg", &MissionObservationInputs::target_heading_deg)
        .def_rw("target_altitude_m", &MissionObservationInputs::target_altitude_m)
        .def_rw("target_speed_mps", &MissionObservationInputs::target_speed_mps)
        .def_rw("has_route_guidance", &MissionObservationInputs::has_route_guidance)
        .def_rw("route_guidance", &MissionObservationInputs::route_guidance)
        .def_rw("nav_inputs", &MissionObservationInputs::nav_inputs);

    nb::class_<MissionObservationProducts>(m, "MissionObservationProducts")
        .def(nb::init<>())
        .def_ro("valid", &MissionObservationProducts::valid)
        .def_ro("mode_code", &MissionObservationProducts::mode_code)
        .def_ro("nav_valid", &MissionObservationProducts::nav_valid)
        .def_ro("nav", &MissionObservationProducts::nav)
        .def_ro("values", &MissionObservationProducts::values);

    nb::class_<StepInfoInputs>(m, "StepInfoInputs")
        .def(nb::init<>())
        .def_rw("on_runway", &StepInfoInputs::on_runway)
        .def_rw("gear_collapsed", &StepInfoInputs::gear_collapsed)
        .def_rw("gear_stress", &StepInfoInputs::gear_stress)
        .def_rw("alt_agl_m", &StepInfoInputs::alt_agl_m)
        .def_rw("on_ground_alt_threshold_m", &StepInfoInputs::on_ground_alt_threshold_m)
        .def_rw("airborne_alt_threshold_m", &StepInfoInputs::airborne_alt_threshold_m)
        .def_rw("has_runway_frame", &StepInfoInputs::has_runway_frame)
        .def_rw("runway_frame", &StepInfoInputs::runway_frame)
        .def_rw("runway_width_margin_m", &StepInfoInputs::runway_width_margin_m)
        .def_rw("runway_length_margin_m", &StepInfoInputs::runway_length_margin_m);

    nb::class_<StepInfoProducts>(m, "StepInfoProducts")
        .def(nb::init<>())
        .def_ro("valid", &StepInfoProducts::valid)
        .def_ro("on_runway", &StepInfoProducts::on_runway)
        .def_ro("gear_collapsed", &StepInfoProducts::gear_collapsed)
        .def_ro("gear_stress", &StepInfoProducts::gear_stress)
        .def_ro("on_ground", &StepInfoProducts::on_ground)
        .def_ro("airborne", &StepInfoProducts::airborne)
        .def_ro("preliftoff", &StepInfoProducts::preliftoff)
        .def_ro("has_runway_frame", &StepInfoProducts::has_runway_frame)
        .def_ro("on_runway_geom", &StepInfoProducts::on_runway_geom)
        .def_ro("runway_cross_m", &StepInfoProducts::runway_cross_m)
        .def_ro("runway_along_m", &StepInfoProducts::runway_along_m);

    m.def("resolve_ground_track_deg", &resolve_ground_track_deg, nb::arg("fallback_heading_deg"), nb::arg("inst_ground_track_deg"));
    m.def("compute_ground_track_error_deg", &compute_ground_track_error_deg, nb::arg("target_heading_deg"), nb::arg("fallback_heading_deg"), nb::arg("inst_ground_track_deg"));
    m.def("compute_command_tracking_error_deg", &compute_command_tracking_error_deg, nb::arg("target_heading_deg"), nb::arg("truth_heading_deg"), nb::arg("command_code"), nb::arg("inst_ground_track_deg"));
    m.def("compute_waypoint_mission_nav", &compute_waypoint_mission_nav, nb::arg("route_result"), nb::arg("inputs"));
    m.def("compute_mission_observation", &compute_mission_observation, nb::arg("inputs"));
    m.def("compute_step_info_runtime", &compute_step_info_runtime, nb::arg("inputs"));

    nb::class_<WaypointRewardInputs>(m, "WaypointRewardInputs")
        .def(nb::init<>())
        .def_rw("valid", &WaypointRewardInputs::valid)
        .def_rw("waypoint_index", &WaypointRewardInputs::waypoint_index)
        .def_rw("waypoint_count", &WaypointRewardInputs::waypoint_count)
        .def_rw("is_flyover", &WaypointRewardInputs::is_flyover)
        .def_rw("has_guidance", &WaypointRewardInputs::has_guidance)
        .def_rw("passed_fix", &WaypointRewardInputs::passed_fix)
        .def_rw("dist_m", &WaypointRewardInputs::dist_m)
        .def_rw("xtk_m", &WaypointRewardInputs::xtk_m)
        .def_rw("dtg_m", &WaypointRewardInputs::dtg_m)
        .def_rw("waypoint_radius_m", &WaypointRewardInputs::waypoint_radius_m)
        .def_rw("leg_len_m", &WaypointRewardInputs::leg_len_m)
        .def_rw("lead_turn_m", &WaypointRewardInputs::lead_turn_m)
        .def_rw("sequence_gate_m", &WaypointRewardInputs::sequence_gate_m)
        .def_rw("has_prev_dist", &WaypointRewardInputs::has_prev_dist)
        .def_rw("prev_dist_m", &WaypointRewardInputs::prev_dist_m)
        .def_rw("route_length_m", &WaypointRewardInputs::route_length_m)
        .def_rw("turn_relief_activation", &WaypointRewardInputs::turn_relief_activation)
        .def_rw("progress_weight", &WaypointRewardInputs::progress_weight)
        .def_rw("progress_negative_scale", &WaypointRewardInputs::progress_negative_scale)
        .def_rw("distance_weight", &WaypointRewardInputs::distance_weight)
        .def_rw("distance_clip_m", &WaypointRewardInputs::distance_clip_m)
        .def_rw("distance_scale_by_route", &WaypointRewardInputs::distance_scale_by_route)
        .def_rw("distance_route_ref_m", &WaypointRewardInputs::distance_route_ref_m)
        .def_rw("distance_route_scale_min", &WaypointRewardInputs::distance_route_scale_min)
        .def_rw("distance_route_scale_max", &WaypointRewardInputs::distance_route_scale_max)
        .def_rw("cross_track_weight", &WaypointRewardInputs::cross_track_weight)
        .def_rw("cross_track_deadband_m", &WaypointRewardInputs::cross_track_deadband_m)
        .def_rw("cross_track_norm_m", &WaypointRewardInputs::cross_track_norm_m)
        .def_rw("cross_track_power", &WaypointRewardInputs::cross_track_power)
        .def_rw("cross_track_clip", &WaypointRewardInputs::cross_track_clip)
        .def_rw("turn_relief_max", &WaypointRewardInputs::turn_relief_max)
        .def_rw("proximity_weight", &WaypointRewardInputs::proximity_weight)
        .def_rw("proximity_ref_m", &WaypointRewardInputs::proximity_ref_m)
        .def_rw("proximity_power", &WaypointRewardInputs::proximity_power)
        .def_rw("reached_bonus", &WaypointRewardInputs::reached_bonus);

    nb::class_<WaypointRewardProducts>(m, "WaypointRewardProducts")
        .def(nb::init<>())
        .def_ro("valid", &WaypointRewardProducts::valid)
        .def_ro("waypoint_progress", &WaypointRewardProducts::waypoint_progress)
        .def_ro("waypoint_distance", &WaypointRewardProducts::waypoint_distance)
        .def_ro("waypoint_cross_track", &WaypointRewardProducts::waypoint_cross_track)
        .def_ro("waypoint_proximity", &WaypointRewardProducts::waypoint_proximity)
        .def_ro("waypoint_reached_bonus", &WaypointRewardProducts::waypoint_reached_bonus)
        .def_ro("arrived", &WaypointRewardProducts::arrived)
        .def_ro("next_prev_dist_valid", &WaypointRewardProducts::next_prev_dist_valid)
        .def_ro("next_prev_dist_m", &WaypointRewardProducts::next_prev_dist_m);

    nb::class_<ApproachRewardInputs>(m, "ApproachRewardInputs")
        .def(nb::init<>())
        .def_rw("valid", &ApproachRewardInputs::valid)
        .def_rw("ils_valid", &ApproachRewardInputs::ils_valid)
        .def_rw("ils_loc_dev", &ApproachRewardInputs::ils_loc_dev)
        .def_rw("ils_gs_dev", &ApproachRewardInputs::ils_gs_dev)
        .def_rw("ils_dme_m", &ApproachRewardInputs::ils_dme_m)
        .def_rw("has_prev_loc", &ApproachRewardInputs::has_prev_loc)
        .def_rw("prev_loc_abs", &ApproachRewardInputs::prev_loc_abs)
        .def_rw("has_prev_gs", &ApproachRewardInputs::has_prev_gs)
        .def_rw("prev_gs_abs", &ApproachRewardInputs::prev_gs_abs)
        .def_rw("has_prev_dme", &ApproachRewardInputs::has_prev_dme)
        .def_rw("prev_dme_m", &ApproachRewardInputs::prev_dme_m)
        .def_rw("localizer_weight", &ApproachRewardInputs::localizer_weight)
        .def_rw("localizer_deadband", &ApproachRewardInputs::localizer_deadband)
        .def_rw("localizer_norm", &ApproachRewardInputs::localizer_norm)
        .def_rw("localizer_power", &ApproachRewardInputs::localizer_power)
        .def_rw("localizer_clip", &ApproachRewardInputs::localizer_clip)
        .def_rw("localizer_improve_weight", &ApproachRewardInputs::localizer_improve_weight)
        .def_rw("glideslope_weight", &ApproachRewardInputs::glideslope_weight)
        .def_rw("glideslope_deadband", &ApproachRewardInputs::glideslope_deadband)
        .def_rw("glideslope_norm", &ApproachRewardInputs::glideslope_norm)
        .def_rw("glideslope_power", &ApproachRewardInputs::glideslope_power)
        .def_rw("glideslope_clip", &ApproachRewardInputs::glideslope_clip)
        .def_rw("glideslope_improve_weight", &ApproachRewardInputs::glideslope_improve_weight)
        .def_rw("dme_progress_weight", &ApproachRewardInputs::dme_progress_weight)
        .def_rw("dme_progress_localizer_band", &ApproachRewardInputs::dme_progress_localizer_band)
        .def_rw("dme_progress_glideslope_band", &ApproachRewardInputs::dme_progress_glideslope_band)
        .def_rw("dme_progress_quality_power", &ApproachRewardInputs::dme_progress_quality_power)
        .def_rw("capture_bonus", &ApproachRewardInputs::capture_bonus)
        .def_rw("capture_localizer_band", &ApproachRewardInputs::capture_localizer_band)
        .def_rw("capture_glideslope_band", &ApproachRewardInputs::capture_glideslope_band)
        .def_rw("sink_rate_weight", &ApproachRewardInputs::sink_rate_weight)
        .def_rw("flare_agl_m", &ApproachRewardInputs::flare_agl_m)
        .def_rw("curr_alt_agl_m", &ApproachRewardInputs::curr_alt_agl_m)
        .def_rw("sink_rate_mps", &ApproachRewardInputs::sink_rate_mps)
        .def_rw("sink_rate_deadband_mps", &ApproachRewardInputs::sink_rate_deadband_mps)
        .def_rw("sink_rate_norm_mps", &ApproachRewardInputs::sink_rate_norm_mps)
        .def_rw("sink_rate_power", &ApproachRewardInputs::sink_rate_power)
        .def_rw("sink_rate_clip", &ApproachRewardInputs::sink_rate_clip);

    nb::class_<ApproachRewardProducts>(m, "ApproachRewardProducts")
        .def(nb::init<>())
        .def_ro("valid", &ApproachRewardProducts::valid)
        .def_ro("approach_localizer", &ApproachRewardProducts::approach_localizer)
        .def_ro("approach_localizer_improve", &ApproachRewardProducts::approach_localizer_improve)
        .def_ro("approach_glideslope", &ApproachRewardProducts::approach_glideslope)
        .def_ro("approach_glideslope_improve", &ApproachRewardProducts::approach_glideslope_improve)
        .def_ro("approach_dme_progress", &ApproachRewardProducts::approach_dme_progress)
        .def_ro("approach_capture_bonus", &ApproachRewardProducts::approach_capture_bonus)
        .def_ro("landing_sink_rate_penalty", &ApproachRewardProducts::landing_sink_rate_penalty)
        .def_ro("clear_history", &ApproachRewardProducts::clear_history)
        .def_ro("next_prev_valid", &ApproachRewardProducts::next_prev_valid)
        .def_ro("next_prev_loc_abs", &ApproachRewardProducts::next_prev_loc_abs)
        .def_ro("next_prev_gs_abs", &ApproachRewardProducts::next_prev_gs_abs)
        .def_ro("next_prev_dme_m", &ApproachRewardProducts::next_prev_dme_m);

    m.def("compute_waypoint_reward_terms", &compute_waypoint_reward_terms, nb::arg("inputs"));
    m.def("compute_approach_reward_terms", &compute_approach_reward_terms, nb::arg("inputs"));

    nb::class_<FlightShapingRuntimeInputs>(m, "FlightShapingRuntimeInputs")
        .def(nb::init<>())
        .def_rw("truth_altitude_m", &FlightShapingRuntimeInputs::truth_altitude_m)
        .def_rw("truth_speed_mps", &FlightShapingRuntimeInputs::truth_speed_mps)
        .def_rw("prev_altitude_m", &FlightShapingRuntimeInputs::prev_altitude_m)
        .def_rw("prev_ias_mps", &FlightShapingRuntimeInputs::prev_ias_mps)
        .def_rw("curr_ias_mps", &FlightShapingRuntimeInputs::curr_ias_mps)
        .def_rw("curr_alt_baro_m", &FlightShapingRuntimeInputs::curr_alt_baro_m)
        .def_rw("curr_alt_agl_m", &FlightShapingRuntimeInputs::curr_alt_agl_m)
        .def_rw("curr_gear_fraction", &FlightShapingRuntimeInputs::curr_gear_fraction)
        .def_rw("curr_roll_deg", &FlightShapingRuntimeInputs::curr_roll_deg)
        .def_rw("curr_pitch_deg", &FlightShapingRuntimeInputs::curr_pitch_deg)
        .def_rw("curr_beta_deg", &FlightShapingRuntimeInputs::curr_beta_deg)
        .def_rw("curr_yaw_rate_deg_s", &FlightShapingRuntimeInputs::curr_yaw_rate_deg_s)
        .def_rw("curr_g_load", &FlightShapingRuntimeInputs::curr_g_load)
        .def_rw("step_count", &FlightShapingRuntimeInputs::step_count)
        .def_rw("target_altitude_m", &FlightShapingRuntimeInputs::target_altitude_m)
        .def_rw("target_speed_mps", &FlightShapingRuntimeInputs::target_speed_mps)
        .def_rw("heading_error_deg", &FlightShapingRuntimeInputs::heading_error_deg)
        .def_rw("ground_track_error_deg", &FlightShapingRuntimeInputs::ground_track_error_deg)
        .def_rw("waypoint_turn_relief_activation", &FlightShapingRuntimeInputs::waypoint_turn_relief_activation)
        .def_rw("preliftoff", &FlightShapingRuntimeInputs::preliftoff)
        .def_rw("on_runway_task", &FlightShapingRuntimeInputs::on_runway_task)
        .def_rw("airborne", &FlightShapingRuntimeInputs::airborne)
        .def_rw("has_runway_cross_m", &FlightShapingRuntimeInputs::has_runway_cross_m)
        .def_rw("runway_cross_m", &FlightShapingRuntimeInputs::runway_cross_m)
        .def_rw("runway_width_m", &FlightShapingRuntimeInputs::runway_width_m)
        .def_rw("ils_valid", &FlightShapingRuntimeInputs::ils_valid)
        .def_rw("ils_loc_dev", &FlightShapingRuntimeInputs::ils_loc_dev)
        .def_rw("liftoff_awarded", &FlightShapingRuntimeInputs::liftoff_awarded)
        .def_rw("gear_bonus_awarded", &FlightShapingRuntimeInputs::gear_bonus_awarded)
        .def_rw("altitude_progress_weight", &FlightShapingRuntimeInputs::altitude_progress_weight)
        .def_rw("speed_progress_weight", &FlightShapingRuntimeInputs::speed_progress_weight)
        .def_rw("speed_progress_negative_weight", &FlightShapingRuntimeInputs::speed_progress_negative_weight)
        .def_rw("stationary_penalty", &FlightShapingRuntimeInputs::stationary_penalty)
        .def_rw("stationary_grace_steps", &FlightShapingRuntimeInputs::stationary_grace_steps)
        .def_rw("stationary_speed_threshold_mps", &FlightShapingRuntimeInputs::stationary_speed_threshold_mps)
        .def_rw("stationary_alt_threshold_m", &FlightShapingRuntimeInputs::stationary_alt_threshold_m)
        .def_rw("liftoff_bonus", &FlightShapingRuntimeInputs::liftoff_bonus)
        .def_rw("liftoff_speed_threshold_mps", &FlightShapingRuntimeInputs::liftoff_speed_threshold_mps)
        .def_rw("liftoff_alt_threshold_m", &FlightShapingRuntimeInputs::liftoff_alt_threshold_m)
        .def_rw("rotation_reward_weight", &FlightShapingRuntimeInputs::rotation_reward_weight)
        .def_rw("rotation_speed_threshold_mps", &FlightShapingRuntimeInputs::rotation_speed_threshold_mps)
        .def_rw("rotation_alt_threshold_m", &FlightShapingRuntimeInputs::rotation_alt_threshold_m)
        .def_rw("rotation_pitch_cap_deg", &FlightShapingRuntimeInputs::rotation_pitch_cap_deg)
        .def_rw("rotation_overpitch_penalty_weight", &FlightShapingRuntimeInputs::rotation_overpitch_penalty_weight)
        .def_rw("gear_up_bonus", &FlightShapingRuntimeInputs::gear_up_bonus)
        .def_rw("gear_up_bonus_min_alt_agl_m", &FlightShapingRuntimeInputs::gear_up_bonus_min_alt_agl_m)
        .def_rw("roll_stability_weight", &FlightShapingRuntimeInputs::roll_stability_weight)
        .def_rw("heading_error_weight", &FlightShapingRuntimeInputs::heading_error_weight)
        .def_rw("heading_hold_deadband_deg", &FlightShapingRuntimeInputs::heading_hold_deadband_deg)
        .def_rw("heading_hold_bonus", &FlightShapingRuntimeInputs::heading_hold_bonus)
        .def_rw("waypoint_turn_heading_relief_max", &FlightShapingRuntimeInputs::waypoint_turn_heading_relief_max)
        .def_rw("altitude_error_weight", &FlightShapingRuntimeInputs::altitude_error_weight)
        .def_rw("altitude_error_min_alt_m", &FlightShapingRuntimeInputs::altitude_error_min_alt_m)
        .def_rw("altitude_error_target_m", &FlightShapingRuntimeInputs::altitude_error_target_m)
        .def_rw("altitude_error_deadband_m", &FlightShapingRuntimeInputs::altitude_error_deadband_m)
        .def_rw("altitude_error_norm_m", &FlightShapingRuntimeInputs::altitude_error_norm_m)
        .def_rw("altitude_error_power", &FlightShapingRuntimeInputs::altitude_error_power)
        .def_rw("altitude_error_clip", &FlightShapingRuntimeInputs::altitude_error_clip)
        .def_rw("altitude_hold_bonus", &FlightShapingRuntimeInputs::altitude_hold_bonus)
        .def_rw("speed_error_weight", &FlightShapingRuntimeInputs::speed_error_weight)
        .def_rw("speed_error_min_ias_mps", &FlightShapingRuntimeInputs::speed_error_min_ias_mps)
        .def_rw("speed_error_target_mps", &FlightShapingRuntimeInputs::speed_error_target_mps)
        .def_rw("speed_error_deadband_mps", &FlightShapingRuntimeInputs::speed_error_deadband_mps)
        .def_rw("speed_error_norm_mps", &FlightShapingRuntimeInputs::speed_error_norm_mps)
        .def_rw("speed_error_power", &FlightShapingRuntimeInputs::speed_error_power)
        .def_rw("speed_error_clip", &FlightShapingRuntimeInputs::speed_error_clip)
        .def_rw("speed_hold_bonus", &FlightShapingRuntimeInputs::speed_hold_bonus)
        .def_rw("roll_abs_weight", &FlightShapingRuntimeInputs::roll_abs_weight)
        .def_rw("roll_abs_deadband_deg", &FlightShapingRuntimeInputs::roll_abs_deadband_deg)
        .def_rw("roll_abs_norm_deg", &FlightShapingRuntimeInputs::roll_abs_norm_deg)
        .def_rw("roll_abs_power", &FlightShapingRuntimeInputs::roll_abs_power)
        .def_rw("pitch_abs_weight", &FlightShapingRuntimeInputs::pitch_abs_weight)
        .def_rw("pitch_abs_deadband_deg", &FlightShapingRuntimeInputs::pitch_abs_deadband_deg)
        .def_rw("pitch_abs_norm_deg", &FlightShapingRuntimeInputs::pitch_abs_norm_deg)
        .def_rw("pitch_abs_power", &FlightShapingRuntimeInputs::pitch_abs_power)
        .def_rw("yaw_rate_abs_weight", &FlightShapingRuntimeInputs::yaw_rate_abs_weight)
        .def_rw("yaw_rate_abs_deadband_deg_s", &FlightShapingRuntimeInputs::yaw_rate_abs_deadband_deg_s)
        .def_rw("yaw_rate_abs_norm_deg_s", &FlightShapingRuntimeInputs::yaw_rate_abs_norm_deg_s)
        .def_rw("yaw_rate_abs_power", &FlightShapingRuntimeInputs::yaw_rate_abs_power)
        .def_rw("beta_abs_weight", &FlightShapingRuntimeInputs::beta_abs_weight)
        .def_rw("beta_abs_deadband_deg", &FlightShapingRuntimeInputs::beta_abs_deadband_deg)
        .def_rw("beta_abs_norm_deg", &FlightShapingRuntimeInputs::beta_abs_norm_deg)
        .def_rw("beta_abs_power", &FlightShapingRuntimeInputs::beta_abs_power)
        .def_rw("g_deviation_weight", &FlightShapingRuntimeInputs::g_deviation_weight)
        .def_rw("g_deviation_deadband", &FlightShapingRuntimeInputs::g_deviation_deadband)
        .def_rw("g_deviation_norm", &FlightShapingRuntimeInputs::g_deviation_norm)
        .def_rw("g_deviation_power", &FlightShapingRuntimeInputs::g_deviation_power)
        .def_rw("g_deviation_min_alt_agl_m", &FlightShapingRuntimeInputs::g_deviation_min_alt_agl_m)
        .def_rw("speed_reward_weight", &FlightShapingRuntimeInputs::speed_reward_weight)
        .def_rw("runway_centerline_penalty_min_ias_mps", &FlightShapingRuntimeInputs::runway_centerline_penalty_min_ias_mps)
        .def_rw("runway_centerline_penalty_max_ias_mps", &FlightShapingRuntimeInputs::runway_centerline_penalty_max_ias_mps)
        .def_rw("runway_centerline_m_penalty_weight", &FlightShapingRuntimeInputs::runway_centerline_m_penalty_weight)
        .def_rw("runway_centerline_m_deadband_m", &FlightShapingRuntimeInputs::runway_centerline_m_deadband_m)
        .def_rw("runway_centerline_m_norm_m", &FlightShapingRuntimeInputs::runway_centerline_m_norm_m)
        .def_rw("runway_centerline_m_power", &FlightShapingRuntimeInputs::runway_centerline_m_power)
        .def_rw("runway_centerline_m_clip", &FlightShapingRuntimeInputs::runway_centerline_m_clip)
        .def_rw("runway_centerline_penalty_weight", &FlightShapingRuntimeInputs::runway_centerline_penalty_weight)
        .def_rw("runway_centerline_safe_frac", &FlightShapingRuntimeInputs::runway_centerline_safe_frac)
        .def_rw("runway_centerline_penalty_power", &FlightShapingRuntimeInputs::runway_centerline_penalty_power)
        .def_rw("runway_centerline_barrier_weight", &FlightShapingRuntimeInputs::runway_centerline_barrier_weight)
        .def_rw("runway_centerline_barrier_clip_frac", &FlightShapingRuntimeInputs::runway_centerline_barrier_clip_frac)
        .def_rw("departure_centerline_max_alt_agl_m", &FlightShapingRuntimeInputs::departure_centerline_max_alt_agl_m)
        .def_rw("departure_centerline_m_penalty_weight", &FlightShapingRuntimeInputs::departure_centerline_m_penalty_weight)
        .def_rw("departure_centerline_m_deadband_m", &FlightShapingRuntimeInputs::departure_centerline_m_deadband_m)
        .def_rw("departure_centerline_m_norm_m", &FlightShapingRuntimeInputs::departure_centerline_m_norm_m)
        .def_rw("departure_centerline_m_power", &FlightShapingRuntimeInputs::departure_centerline_m_power)
        .def_rw("departure_centerline_m_clip", &FlightShapingRuntimeInputs::departure_centerline_m_clip)
        .def_rw("departure_centerline_reward_weight", &FlightShapingRuntimeInputs::departure_centerline_reward_weight)
        .def_rw("departure_centerline_reward_band_m", &FlightShapingRuntimeInputs::departure_centerline_reward_band_m)
        .def_rw("departure_track_error_weight", &FlightShapingRuntimeInputs::departure_track_error_weight)
        .def_rw("departure_track_error_deadband_deg", &FlightShapingRuntimeInputs::departure_track_error_deadband_deg)
        .def_rw("departure_track_error_norm_deg", &FlightShapingRuntimeInputs::departure_track_error_norm_deg)
        .def_rw("departure_track_error_power", &FlightShapingRuntimeInputs::departure_track_error_power)
        .def_rw("departure_track_error_clip", &FlightShapingRuntimeInputs::departure_track_error_clip)
        .def_rw("departure_track_reward_weight", &FlightShapingRuntimeInputs::departure_track_reward_weight)
        .def_rw("departure_track_reward_band_deg", &FlightShapingRuntimeInputs::departure_track_reward_band_deg)
        .def_rw("alignment_reward_weight", &FlightShapingRuntimeInputs::alignment_reward_weight)
        .def_rw("mission_alignment_min_alt_m", &FlightShapingRuntimeInputs::mission_alignment_min_alt_m);

    nb::class_<FlightShapingRuntimeProducts>(m, "FlightShapingRuntimeProducts")
        .def(nb::init<>())
        .def_ro("valid", &FlightShapingRuntimeProducts::valid)
        .def_ro("altitude_progress", &FlightShapingRuntimeProducts::altitude_progress)
        .def_ro("low_alt_descent_penalty", &FlightShapingRuntimeProducts::low_alt_descent_penalty)
        .def_ro("speed_progress", &FlightShapingRuntimeProducts::speed_progress)
        .def_ro("speed_regress", &FlightShapingRuntimeProducts::speed_regress)
        .def_ro("stationary_penalty", &FlightShapingRuntimeProducts::stationary_penalty)
        .def_ro("liftoff_bonus", &FlightShapingRuntimeProducts::liftoff_bonus)
        .def_ro("next_liftoff_awarded", &FlightShapingRuntimeProducts::next_liftoff_awarded)
        .def_ro("rotation_reward", &FlightShapingRuntimeProducts::rotation_reward)
        .def_ro("rotation_overpitch_penalty", &FlightShapingRuntimeProducts::rotation_overpitch_penalty)
        .def_ro("gear_up_bonus", &FlightShapingRuntimeProducts::gear_up_bonus)
        .def_ro("next_gear_bonus_awarded", &FlightShapingRuntimeProducts::next_gear_bonus_awarded)
        .def_ro("roll_stability", &FlightShapingRuntimeProducts::roll_stability)
        .def_ro("heading_error_penalty", &FlightShapingRuntimeProducts::heading_error_penalty)
        .def_ro("heading_hold_bonus", &FlightShapingRuntimeProducts::heading_hold_bonus)
        .def_ro("altitude_error_penalty", &FlightShapingRuntimeProducts::altitude_error_penalty)
        .def_ro("altitude_hold_bonus", &FlightShapingRuntimeProducts::altitude_hold_bonus)
        .def_ro("speed_error_penalty", &FlightShapingRuntimeProducts::speed_error_penalty)
        .def_ro("speed_hold_bonus", &FlightShapingRuntimeProducts::speed_hold_bonus)
        .def_ro("roll_abs_penalty", &FlightShapingRuntimeProducts::roll_abs_penalty)
        .def_ro("pitch_abs_penalty", &FlightShapingRuntimeProducts::pitch_abs_penalty)
        .def_ro("yaw_rate_abs_penalty", &FlightShapingRuntimeProducts::yaw_rate_abs_penalty)
        .def_ro("beta_abs_penalty", &FlightShapingRuntimeProducts::beta_abs_penalty)
        .def_ro("g_deviation_penalty", &FlightShapingRuntimeProducts::g_deviation_penalty)
        .def_ro("speed_reward", &FlightShapingRuntimeProducts::speed_reward)
        .def_ro("runway_centerline_m_penalty", &FlightShapingRuntimeProducts::runway_centerline_m_penalty)
        .def_ro("runway_centerline_penalty", &FlightShapingRuntimeProducts::runway_centerline_penalty)
        .def_ro("runway_centerline_barrier", &FlightShapingRuntimeProducts::runway_centerline_barrier)
        .def_ro("departure_centerline_m_penalty", &FlightShapingRuntimeProducts::departure_centerline_m_penalty)
        .def_ro("departure_centerline_reward", &FlightShapingRuntimeProducts::departure_centerline_reward)
        .def_ro("departure_track_error_penalty", &FlightShapingRuntimeProducts::departure_track_error_penalty)
        .def_ro("departure_track_reward", &FlightShapingRuntimeProducts::departure_track_reward)
        .def_ro("alignment_reward", &FlightShapingRuntimeProducts::alignment_reward);

    m.def("compute_flight_shaping_terms", &compute_flight_shaping_terms, nb::arg("inputs"));
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

    nb::enum_<ConditionalObjectiveProperty>(m, "ConditionalObjectiveProperty")
        .value("Unknown", ConditionalObjectiveProperty::Unknown)
        .value("Altitude", ConditionalObjectiveProperty::Altitude)
        .value("AltitudeAGL", ConditionalObjectiveProperty::AltitudeAGL)
        .value("Speed", ConditionalObjectiveProperty::Speed)
        .value("GroundSpeed", ConditionalObjectiveProperty::GroundSpeed)
        .value("Gear", ConditionalObjectiveProperty::Gear)
        .value("HeadingErrorDeg", ConditionalObjectiveProperty::HeadingErrorDeg)
        .value("CommandCode", ConditionalObjectiveProperty::CommandCode)
        .value("GroundTrackErrorDeg", ConditionalObjectiveProperty::GroundTrackErrorDeg)
        .value("RunwayCrossAbsM", ConditionalObjectiveProperty::RunwayCrossAbsM)
        .value("RunwayFromThresholdM", ConditionalObjectiveProperty::RunwayFromThresholdM)
        .value("OnRunwayGeom", ConditionalObjectiveProperty::OnRunwayGeom)
        .value("OnRunway", ConditionalObjectiveProperty::OnRunway)
        .value("OnGround", ConditionalObjectiveProperty::OnGround)
        .value("SinkRateAbsMps", ConditionalObjectiveProperty::SinkRateAbsMps)
        .value("IlsLocalizerAbs", ConditionalObjectiveProperty::IlsLocalizerAbs)
        .value("IlsGlideslopeAbs", ConditionalObjectiveProperty::IlsGlideslopeAbs)
        .value("DmeM", ConditionalObjectiveProperty::DmeM)
        .value("Heading", ConditionalObjectiveProperty::Heading)
        .value("X", ConditionalObjectiveProperty::X)
        .value("Y", ConditionalObjectiveProperty::Y)
        .export_values();

    nb::enum_<ConditionalObjectiveOp>(m, "ConditionalObjectiveOp")
        .value("GreaterEqual", ConditionalObjectiveOp::GreaterEqual)
        .value("GreaterThan", ConditionalObjectiveOp::GreaterThan)
        .value("LessEqual", ConditionalObjectiveOp::LessEqual)
        .value("LessThan", ConditionalObjectiveOp::LessThan)
        .export_values();

    nb::enum_<ConditionalObjectiveTargetKind>(m, "ConditionalObjectiveTargetKind")
        .value("Literal", ConditionalObjectiveTargetKind::Literal)
        .value("CommandAltitude", ConditionalObjectiveTargetKind::CommandAltitude)
        .value("CommandSpeed", ConditionalObjectiveTargetKind::CommandSpeed)
        .value("CommandHeading", ConditionalObjectiveTargetKind::CommandHeading)
        .export_values();

    nb::class_<ConditionalObjectiveCondition>(m, "ConditionalObjectiveCondition")
        .def(nb::init<>())
        .def_rw("property_code", &ConditionalObjectiveCondition::property_code)
        .def_rw("op_code", &ConditionalObjectiveCondition::op_code)
        .def_rw("target_kind", &ConditionalObjectiveCondition::target_kind)
        .def_rw("target_value", &ConditionalObjectiveCondition::target_value)
        .def_rw("target_scale", &ConditionalObjectiveCondition::target_scale);

    nb::class_<ConditionalObjectiveSpec>(m, "ConditionalObjectiveSpec")
        .def(nb::init<>())
        .def_rw("conditions", &ConditionalObjectiveSpec::conditions)
        .def_rw("reward_bonus", &ConditionalObjectiveSpec::reward_bonus);

    nb::class_<ConditionalObjectiveInputs>(m, "ConditionalObjectiveInputs")
        .def(nb::init<>())
        .def_rw("altitude_m", &ConditionalObjectiveInputs::altitude_m)
        .def_rw("altitude_agl_m", &ConditionalObjectiveInputs::altitude_agl_m)
        .def_rw("speed_mps", &ConditionalObjectiveInputs::speed_mps)
        .def_rw("ground_speed_mps", &ConditionalObjectiveInputs::ground_speed_mps)
        .def_rw("gear_fraction", &ConditionalObjectiveInputs::gear_fraction)
        .def_rw("heading_error_deg", &ConditionalObjectiveInputs::heading_error_deg)
        .def_rw("command_code", &ConditionalObjectiveInputs::command_code)
        .def_rw("ground_track_error_deg", &ConditionalObjectiveInputs::ground_track_error_deg)
        .def_rw("has_runway_cross_m", &ConditionalObjectiveInputs::has_runway_cross_m)
        .def_rw("runway_cross_m", &ConditionalObjectiveInputs::runway_cross_m)
        .def_rw("has_runway_from_threshold_m", &ConditionalObjectiveInputs::has_runway_from_threshold_m)
        .def_rw("runway_from_threshold_m", &ConditionalObjectiveInputs::runway_from_threshold_m)
        .def_rw("on_runway_geom", &ConditionalObjectiveInputs::on_runway_geom)
        .def_rw("on_runway_task", &ConditionalObjectiveInputs::on_runway_task)
        .def_rw("on_ground", &ConditionalObjectiveInputs::on_ground)
        .def_rw("sink_rate_abs_mps", &ConditionalObjectiveInputs::sink_rate_abs_mps)
        .def_rw("ils_localizer_abs", &ConditionalObjectiveInputs::ils_localizer_abs)
        .def_rw("ils_glideslope_abs", &ConditionalObjectiveInputs::ils_glideslope_abs)
        .def_rw("dme_m", &ConditionalObjectiveInputs::dme_m)
        .def_rw("heading_deg", &ConditionalObjectiveInputs::heading_deg)
        .def_rw("x_m", &ConditionalObjectiveInputs::x_m)
        .def_rw("y_m", &ConditionalObjectiveInputs::y_m)
        .def_rw("target_altitude_m", &ConditionalObjectiveInputs::target_altitude_m)
        .def_rw("target_speed_mps", &ConditionalObjectiveInputs::target_speed_mps)
        .def_rw("target_heading_deg", &ConditionalObjectiveInputs::target_heading_deg);

    nb::class_<ObjectiveShapingConfig>(m, "ObjectiveShapingConfig")
        .def(nb::init<>())
        .def_rw("runway_cross_penalty_weight", &ObjectiveShapingConfig::runway_cross_penalty_weight)
        .def_rw("runway_cross_deadband_m", &ObjectiveShapingConfig::runway_cross_deadband_m)
        .def_rw("runway_cross_norm_m", &ObjectiveShapingConfig::runway_cross_norm_m)
        .def_rw("runway_cross_power", &ObjectiveShapingConfig::runway_cross_power)
        .def_rw("runway_cross_clip", &ObjectiveShapingConfig::runway_cross_clip)
        .def_rw("ground_track_penalty_weight", &ObjectiveShapingConfig::ground_track_penalty_weight)
        .def_rw("ground_track_deadband_deg", &ObjectiveShapingConfig::ground_track_deadband_deg)
        .def_rw("ground_track_norm_deg", &ObjectiveShapingConfig::ground_track_norm_deg)
        .def_rw("ground_track_power", &ObjectiveShapingConfig::ground_track_power)
        .def_rw("ground_track_clip", &ObjectiveShapingConfig::ground_track_clip);

    nb::class_<ConditionalObjectiveProducts>(m, "ConditionalObjectiveProducts")
        .def(nb::init<>())
        .def_ro("valid", &ConditionalObjectiveProducts::valid)
        .def_ro("matched", &ConditionalObjectiveProducts::matched)
        .def_ro("unknown_property", &ConditionalObjectiveProducts::unknown_property)
        .def_ro("status0", &ConditionalObjectiveProducts::status0)
        .def_ro("status1", &ConditionalObjectiveProducts::status1)
        .def_ro("status2", &ConditionalObjectiveProducts::status2)
        .def_ro("status_count", &ConditionalObjectiveProducts::status_count)
        .def_ro("success_runway_cross_penalty", &ConditionalObjectiveProducts::success_runway_cross_penalty)
        .def_ro("success_ground_track_error_penalty", &ConditionalObjectiveProducts::success_ground_track_error_penalty)
        .def_ro("objective_bonus", &ConditionalObjectiveProducts::objective_bonus);

    m.def(
        "evaluate_conditional_objective",
        &evaluate_conditional_objective,
        nb::arg("spec"),
        nb::arg("inputs"),
        nb::arg("shaping")
    );

    nb::enum_<TerminationReasonCode>(m, "TerminationReasonCode")
        .value("Running", TerminationReasonCode::Running)
        .value("NanGuard", TerminationReasonCode::NanGuard)
        .value("CrashHealth", TerminationReasonCode::CrashHealth)
        .value("FailfastDeepStall", TerminationReasonCode::FailfastDeepStall)
        .value("FailfastInvertedLowAlt", TerminationReasonCode::FailfastInvertedLowAlt)
        .value("FailfastExtremePitch", TerminationReasonCode::FailfastExtremePitch)
        .value("GearCollapse", TerminationReasonCode::GearCollapse)
        .value("OffRunwayTerminate", TerminationReasonCode::OffRunwayTerminate)
        .value("SuccessWaypoint", TerminationReasonCode::SuccessWaypoint)
        .value("SuccessObjective", TerminationReasonCode::SuccessObjective)
        .value("Success", TerminationReasonCode::Success)
        .value("FailureUnknown", TerminationReasonCode::FailureUnknown)
        .value("TerminatedUnknown", TerminationReasonCode::TerminatedUnknown)
        .value("Timeout", TerminationReasonCode::Timeout)
        .export_values();

    nb::class_<SafetyRuntimeInputs>(m, "SafetyRuntimeInputs")
        .def(nb::init<>())
        .def_rw("finite_state_valid", &SafetyRuntimeInputs::finite_state_valid)
        .def_rw("crash_penalty", &SafetyRuntimeInputs::crash_penalty)
        .def_rw("survival_reward", &SafetyRuntimeInputs::survival_reward)
        .def_rw("health", &SafetyRuntimeInputs::health)
        .def_rw("airborne", &SafetyRuntimeInputs::airborne)
        .def_rw("aoa_valid", &SafetyRuntimeInputs::aoa_valid)
        .def_rw("aoa_abs_deg", &SafetyRuntimeInputs::aoa_abs_deg)
        .def_rw("stall_threshold_deg", &SafetyRuntimeInputs::stall_threshold_deg)
        .def_rw("stall_penalty_weight", &SafetyRuntimeInputs::stall_penalty_weight)
        .def_rw("stall_penalty_clip", &SafetyRuntimeInputs::stall_penalty_clip)
        .def_rw("g_abs", &SafetyRuntimeInputs::g_abs)
        .def_rw("overload_g_threshold", &SafetyRuntimeInputs::overload_g_threshold)
        .def_rw("overload_penalty_weight", &SafetyRuntimeInputs::overload_penalty_weight)
        .def_rw("overload_penalty_clip", &SafetyRuntimeInputs::overload_penalty_clip)
        .def_rw("curr_alt_agl_m", &SafetyRuntimeInputs::curr_alt_agl_m)
        .def_rw("overload_min_alt_agl_m", &SafetyRuntimeInputs::overload_min_alt_agl_m)
        .def_rw("altitude_m", &SafetyRuntimeInputs::altitude_m)
        .def_rw("roll_abs_deg", &SafetyRuntimeInputs::roll_abs_deg)
        .def_rw("pitch_abs_deg", &SafetyRuntimeInputs::pitch_abs_deg)
        .def_rw("failfast_penalty", &SafetyRuntimeInputs::failfast_penalty)
        .def_rw("gear_collapsed", &SafetyRuntimeInputs::gear_collapsed)
        .def_rw("gear_collapse_penalty", &SafetyRuntimeInputs::gear_collapse_penalty)
        .def_rw("runway_surface_phase", &SafetyRuntimeInputs::runway_surface_phase)
        .def_rw("on_runway_task", &SafetyRuntimeInputs::on_runway_task)
        .def_rw("gear_stress", &SafetyRuntimeInputs::gear_stress)
        .def_rw("gear_stress_penalty_weight", &SafetyRuntimeInputs::gear_stress_penalty_weight)
        .def_rw("off_runway_penalty", &SafetyRuntimeInputs::off_runway_penalty)
        .def_rw("speed_mps", &SafetyRuntimeInputs::speed_mps)
        .def_rw("off_runway_steps", &SafetyRuntimeInputs::off_runway_steps)
        .def_rw("off_runway_terminate_speed", &SafetyRuntimeInputs::off_runway_terminate_speed)
        .def_rw("off_runway_terminate_grace_s", &SafetyRuntimeInputs::off_runway_terminate_grace_s)
        .def_rw("time_step_s", &SafetyRuntimeInputs::time_step_s)
        .def_rw("off_runway_terminate_penalty", &SafetyRuntimeInputs::off_runway_terminate_penalty);

    nb::class_<SafetyRuntimeProducts>(m, "SafetyRuntimeProducts")
        .def(nb::init<>())
        .def_ro("valid", &SafetyRuntimeProducts::valid)
        .def_ro("early_return", &SafetyRuntimeProducts::early_return)
        .def_ro("terminated", &SafetyRuntimeProducts::terminated)
        .def_ro("status_flag", &SafetyRuntimeProducts::status_flag)
        .def_ro("reason_code", &SafetyRuntimeProducts::reason_code)
        .def_ro("survival", &SafetyRuntimeProducts::survival)
        .def_ro("crash_penalty", &SafetyRuntimeProducts::crash_penalty)
        .def_ro("nan_guard_marker", &SafetyRuntimeProducts::nan_guard_marker)
        .def_ro("stall_penalty", &SafetyRuntimeProducts::stall_penalty)
        .def_ro("overload_penalty", &SafetyRuntimeProducts::overload_penalty)
        .def_ro("failfast_penalty", &SafetyRuntimeProducts::failfast_penalty)
        .def_ro("gear_collapse_penalty", &SafetyRuntimeProducts::gear_collapse_penalty)
        .def_ro("off_runway_penalty", &SafetyRuntimeProducts::off_runway_penalty)
        .def_ro("gear_stress_penalty", &SafetyRuntimeProducts::gear_stress_penalty)
        .def_ro("off_runway_terminate_penalty", &SafetyRuntimeProducts::off_runway_terminate_penalty);

    m.def("compute_safety_runtime", &compute_safety_runtime, nb::arg("inputs"));
    m.def(
        "finalize_termination_reason",
        &finalize_termination_reason,
        nb::arg("current_reason"),
        nb::arg("terminated"),
        nb::arg("truncated"),
        nb::arg("status_flag")
    );
    m.def("termination_reason_name", &termination_reason_name, nb::arg("reason"));

    nb::class_<ExecutionStepRuntimeInputs>(m, "ExecutionStepRuntimeInputs")
        .def(nb::init<>())
        .def_rw("safety", &ExecutionStepRuntimeInputs::safety)
        .def_rw("has_waypoint", &ExecutionStepRuntimeInputs::has_waypoint)
        .def_rw("waypoint", &ExecutionStepRuntimeInputs::waypoint)
        .def_rw("waypoint_episode_success", &ExecutionStepRuntimeInputs::waypoint_episode_success)
        .def_rw("waypoint_episode_success_bonus", &ExecutionStepRuntimeInputs::waypoint_episode_success_bonus)
        .def_rw("has_approach", &ExecutionStepRuntimeInputs::has_approach)
        .def_rw("approach", &ExecutionStepRuntimeInputs::approach)
        .def_rw("has_objectives", &ExecutionStepRuntimeInputs::has_objectives)
        .def_rw("objectives", &ExecutionStepRuntimeInputs::objectives)
        .def_rw("objective_inputs", &ExecutionStepRuntimeInputs::objective_inputs)
        .def_rw("objective_shaping", &ExecutionStepRuntimeInputs::objective_shaping)
        .def_rw("truncated", &ExecutionStepRuntimeInputs::truncated);

    nb::class_<ExecutionStepRuntimeProducts>(m, "ExecutionStepRuntimeProducts")
        .def(nb::init<>())
        .def_ro("valid", &ExecutionStepRuntimeProducts::valid)
        .def_ro("safety", &ExecutionStepRuntimeProducts::safety)
        .def_ro("waypoint_evaluated", &ExecutionStepRuntimeProducts::waypoint_evaluated)
        .def_ro("waypoint", &ExecutionStepRuntimeProducts::waypoint)
        .def_ro("waypoint_episode_success", &ExecutionStepRuntimeProducts::waypoint_episode_success)
        .def_ro("waypoint_episode_success_bonus", &ExecutionStepRuntimeProducts::waypoint_episode_success_bonus)
        .def_ro("approach_evaluated", &ExecutionStepRuntimeProducts::approach_evaluated)
        .def_ro("approach", &ExecutionStepRuntimeProducts::approach)
        .def_ro("objective_evaluated", &ExecutionStepRuntimeProducts::objective_evaluated)
        .def_ro("matched_objective_index", &ExecutionStepRuntimeProducts::matched_objective_index)
        .def_ro("objective_status_count", &ExecutionStepRuntimeProducts::objective_status_count)
        .def_ro("objective", &ExecutionStepRuntimeProducts::objective)
        .def_ro("compiled_reward_total", &ExecutionStepRuntimeProducts::compiled_reward_total)
        .def_ro("terminated", &ExecutionStepRuntimeProducts::terminated)
        .def_ro("status0", &ExecutionStepRuntimeProducts::status0)
        .def_ro("status1", &ExecutionStepRuntimeProducts::status1)
        .def_ro("status2", &ExecutionStepRuntimeProducts::status2)
        .def_ro("status3", &ExecutionStepRuntimeProducts::status3)
        .def_ro("reason_code", &ExecutionStepRuntimeProducts::reason_code)
        .def_ro("final_reason_code", &ExecutionStepRuntimeProducts::final_reason_code);

    m.def("compute_execution_step_runtime", &compute_execution_step_runtime, nb::arg("inputs"));

    nb::class_<ExecutionFrameRuntimeInputs>(m, "ExecutionFrameRuntimeInputs")
        .def(nb::init<>())
        .def_rw("has_mission_observation", &ExecutionFrameRuntimeInputs::has_mission_observation)
        .def_rw("mission_observation", &ExecutionFrameRuntimeInputs::mission_observation)
        .def_rw("has_step_info", &ExecutionFrameRuntimeInputs::has_step_info)
        .def_rw("step_info", &ExecutionFrameRuntimeInputs::step_info)
        .def_rw("has_execution_step", &ExecutionFrameRuntimeInputs::has_execution_step)
        .def_rw("execution_step", &ExecutionFrameRuntimeInputs::execution_step)
        .def_rw("has_flight_shaping", &ExecutionFrameRuntimeInputs::has_flight_shaping)
        .def_rw("flight_shaping", &ExecutionFrameRuntimeInputs::flight_shaping);

    nb::class_<ExecutionFrameRuntimeProducts>(m, "ExecutionFrameRuntimeProducts")
        .def(nb::init<>())
        .def_ro("valid", &ExecutionFrameRuntimeProducts::valid)
        .def_ro("mission_observation_evaluated", &ExecutionFrameRuntimeProducts::mission_observation_evaluated)
        .def_ro("mission_observation", &ExecutionFrameRuntimeProducts::mission_observation)
        .def_ro("step_info_evaluated", &ExecutionFrameRuntimeProducts::step_info_evaluated)
        .def_ro("step_info", &ExecutionFrameRuntimeProducts::step_info)
        .def_ro("execution_step_evaluated", &ExecutionFrameRuntimeProducts::execution_step_evaluated)
        .def_ro("execution_step", &ExecutionFrameRuntimeProducts::execution_step)
        .def_ro("flight_shaping_evaluated", &ExecutionFrameRuntimeProducts::flight_shaping_evaluated)
        .def_ro("flight_shaping", &ExecutionFrameRuntimeProducts::flight_shaping);

    m.def("compute_execution_frame_runtime", &compute_execution_frame_runtime, nb::arg("inputs"));

    nb::class_<ExecutionEpisodeRuntimeInputs>(m, "ExecutionEpisodeRuntimeInputs")
        .def(nb::init<>())
        .def_rw("has_mission_observation", &ExecutionEpisodeRuntimeInputs::has_mission_observation)
        .def_rw("mission_observation", &ExecutionEpisodeRuntimeInputs::mission_observation)
        .def_rw("has_step_info", &ExecutionEpisodeRuntimeInputs::has_step_info)
        .def_rw("step_info", &ExecutionEpisodeRuntimeInputs::step_info)
        .def_rw("has_execution_step", &ExecutionEpisodeRuntimeInputs::has_execution_step)
        .def_rw("execution_step", &ExecutionEpisodeRuntimeInputs::execution_step)
        .def_rw("has_flight_shaping", &ExecutionEpisodeRuntimeInputs::has_flight_shaping)
        .def_rw("flight_shaping", &ExecutionEpisodeRuntimeInputs::flight_shaping)
        .def_rw("include_roll_stability", &ExecutionEpisodeRuntimeInputs::include_roll_stability);

    nb::class_<ExecutionEpisodeRuntimeProducts>(m, "ExecutionEpisodeRuntimeProducts")
        .def(nb::init<>())
        .def_ro("valid", &ExecutionEpisodeRuntimeProducts::valid)
        .def_ro("mission_observation_evaluated", &ExecutionEpisodeRuntimeProducts::mission_observation_evaluated)
        .def_ro("mission_observation", &ExecutionEpisodeRuntimeProducts::mission_observation)
        .def_ro("step_info_evaluated", &ExecutionEpisodeRuntimeProducts::step_info_evaluated)
        .def_ro("step_info", &ExecutionEpisodeRuntimeProducts::step_info)
        .def_ro("execution_step_evaluated", &ExecutionEpisodeRuntimeProducts::execution_step_evaluated)
        .def_ro("execution_step", &ExecutionEpisodeRuntimeProducts::execution_step)
        .def_ro("flight_shaping_evaluated", &ExecutionEpisodeRuntimeProducts::flight_shaping_evaluated)
        .def_ro("flight_shaping", &ExecutionEpisodeRuntimeProducts::flight_shaping)
        .def_ro("outcome_evaluated", &ExecutionEpisodeRuntimeProducts::outcome_evaluated)
        .def_ro("compiled_reward_total", &ExecutionEpisodeRuntimeProducts::compiled_reward_total)
        .def_ro("terminated", &ExecutionEpisodeRuntimeProducts::terminated)
        .def_ro("status0", &ExecutionEpisodeRuntimeProducts::status0)
        .def_ro("status1", &ExecutionEpisodeRuntimeProducts::status1)
        .def_ro("status2", &ExecutionEpisodeRuntimeProducts::status2)
        .def_ro("status3", &ExecutionEpisodeRuntimeProducts::status3)
        .def_ro("reason_code", &ExecutionEpisodeRuntimeProducts::reason_code)
        .def_ro("final_reason_code", &ExecutionEpisodeRuntimeProducts::final_reason_code);

    m.def("compute_execution_episode_runtime", &compute_execution_episode_runtime, nb::arg("inputs"));
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

    nb::class_<gpu::WorldBatchStepState>(m, "WorldBatchStepState")
        .def(nb::init<>())
        .def_rw("x_m", &gpu::WorldBatchStepState::x_m)
        .def_rw("y_m", &gpu::WorldBatchStepState::y_m)
        .def_rw("z_m", &gpu::WorldBatchStepState::z_m)
        .def_rw("vx_mps", &gpu::WorldBatchStepState::vx_mps)
        .def_rw("vy_mps", &gpu::WorldBatchStepState::vy_mps)
        .def_rw("vz_mps", &gpu::WorldBatchStepState::vz_mps)
        .def_rw("wind_vx_mps", &gpu::WorldBatchStepState::wind_vx_mps)
        .def_rw("wind_vy_mps", &gpu::WorldBatchStepState::wind_vy_mps)
        .def_rw("cmd_vx_mps", &gpu::WorldBatchStepState::cmd_vx_mps)
        .def_rw("cmd_vy_mps", &gpu::WorldBatchStepState::cmd_vy_mps)
        .def_rw("cmd_vz_mps", &gpu::WorldBatchStepState::cmd_vz_mps)
        .def_rw("max_delta_vxy_mps_per_step", &gpu::WorldBatchStepState::max_delta_vxy_mps_per_step)
        .def_rw("max_delta_vz_mps_per_step", &gpu::WorldBatchStepState::max_delta_vz_mps_per_step)
        .def_rw("time_step_s", &gpu::WorldBatchStepState::time_step_s)
        .def_rw("fuel_kg", &gpu::WorldBatchStepState::fuel_kg)
        .def_rw("fuel_idle_burn_kgps", &gpu::WorldBatchStepState::fuel_idle_burn_kgps)
        .def_rw("fuel_burn_per_speed_kgps_per_mps", &gpu::WorldBatchStepState::fuel_burn_per_speed_kgps_per_mps)
        .def_rw("mission_time_s", &gpu::WorldBatchStepState::mission_time_s);

    nb::class_<gpu::WorldBatchStepExperimentStats>(m, "WorldBatchStepExperimentStats")
        .def(nb::init<>())
        .def_ro("used_cuda", &gpu::WorldBatchStepExperimentStats::used_cuda)
        .def_ro("used_cuda_graph", &gpu::WorldBatchStepExperimentStats::used_cuda_graph)
        .def_ro("host_to_device_ms", &gpu::WorldBatchStepExperimentStats::host_to_device_ms)
        .def_ro("graph_capture_ms", &gpu::WorldBatchStepExperimentStats::graph_capture_ms)
        .def_ro("kernel_ms", &gpu::WorldBatchStepExperimentStats::kernel_ms)
        .def_ro("device_to_host_ms", &gpu::WorldBatchStepExperimentStats::device_to_host_ms)
        .def_ro("total_ms", &gpu::WorldBatchStepExperimentStats::total_ms);

    m.def("last_world_batch_step_stats", &gpu::last_world_batch_step_stats);
    m.def("step_world_batch_state_batch", &gpu::step_world_batch_experiment_batch,
          nb::arg("initial_states"), nb::arg("steps"), nb::arg("use_cuda_graph") = false);
    m.def("step_world_batch_state_batch_reference", &gpu::step_world_batch_reference_cpu_batch,
          nb::arg("initial_states"), nb::arg("steps"));
    m.def("upload_world_batch_step_states", &gpu::upload_world_batch_step_states, nb::arg("initial_states"));
    m.def("replay_world_batch_step_device_sequence", &gpu::replay_world_batch_step_device_sequence,
          nb::arg("steps"), nb::arg("use_cuda_graph") = false);
    m.def("download_world_batch_step_states", &gpu::download_world_batch_step_states);
    m.def("exact_world_step_state_v1_size_bytes", &gpu::exact_world_step_state_v1_size_bytes);
    m.def(
        "exact_world_step_states_v1_apply_signatures_packed",
        [](const nb::bytes& packed) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            return gpu::exact_world_step_state_v1_apply_signatures(states);
        },
        nb::arg("packed")
    );
    m.def(
        "exact_world_step_state_v1_component_digests_packed",
        [](const nb::bytes& packed) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            nb::list out;
            for (const auto& state : states) {
                nb::dict digests;
                for (const auto& [name, value] : gpu::exact_world_step_state_v1_component_digests(state)) {
                    digests[nb::str(name.c_str())] = nb::int_(value);
                }
                out.append(std::move(digests));
            }
            return out;
        },
        nb::arg("packed")
    );
    m.def(
        "exact_world_step_state_v1_hidden_surfaces_packed",
        [](const nb::bytes& packed) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            return exact_world_step_hidden_surface_list(states);
        },
        nb::arg("packed")
    );
    m.def(
        "exact_world_step_state_v1_command_surfaces_packed",
        [](const nb::bytes& packed) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            return exact_world_step_command_surface_list(states);
        },
        nb::arg("packed")
    );
    m.def(
        "exact_world_step_state_v1_combat_surfaces_packed",
        [](const nb::bytes& packed) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            return exact_world_step_combat_surface_list(states);
        },
        nb::arg("packed")
    );
    nb::class_<gpu::ExactWorldStepPrototypeStats>(m, "ExactWorldStepPrototypeStats")
        .def(nb::init<>())
        .def_ro("used_cuda", &gpu::ExactWorldStepPrototypeStats::used_cuda)
        .def_ro("host_to_device_ms", &gpu::ExactWorldStepPrototypeStats::host_to_device_ms)
        .def_ro("kernel_ms", &gpu::ExactWorldStepPrototypeStats::kernel_ms)
        .def_ro("device_to_host_ms", &gpu::ExactWorldStepPrototypeStats::device_to_host_ms)
        .def_ro("total_ms", &gpu::ExactWorldStepPrototypeStats::total_ms);
    nb::class_<gpu::ExactWorldStepCommandLaneStats>(m, "ExactWorldStepCommandLaneStats")
        .def(nb::init<>())
        .def_ro("state_count", &gpu::ExactWorldStepCommandLaneStats::state_count)
        .def_ro("total_ms", &gpu::ExactWorldStepCommandLaneStats::total_ms);
    nb::class_<gpu::ExactWorldStepFrontHalfStats>(m, "ExactWorldStepFrontHalfStats")
        .def(nb::init<>())
        .def_ro("state_count", &gpu::ExactWorldStepFrontHalfStats::state_count)
        .def_ro("used_cuda", &gpu::ExactWorldStepFrontHalfStats::used_cuda)
        .def_ro("command_lane_ms", &gpu::ExactWorldStepFrontHalfStats::command_lane_ms)
        .def_ro("host_to_device_ms", &gpu::ExactWorldStepFrontHalfStats::host_to_device_ms)
        .def_ro("kernel_ms", &gpu::ExactWorldStepFrontHalfStats::kernel_ms)
        .def_ro("device_to_host_ms", &gpu::ExactWorldStepFrontHalfStats::device_to_host_ms)
        .def_ro("cpu_post_command_ms", &gpu::ExactWorldStepFrontHalfStats::cpu_post_command_ms)
        .def_ro("total_ms", &gpu::ExactWorldStepFrontHalfStats::total_ms);
    nb::class_<gpu::ExactWorldStepControlAeroStats>(m, "ExactWorldStepControlAeroStats")
        .def(nb::init<>())
        .def_ro("state_count", &gpu::ExactWorldStepControlAeroStats::state_count)
        .def_ro("total_ms", &gpu::ExactWorldStepControlAeroStats::total_ms);
    nb::class_<gpu::ExactWorldStepForceGroundStats>(m, "ExactWorldStepForceGroundStats")
        .def(nb::init<>())
        .def_ro("state_count", &gpu::ExactWorldStepForceGroundStats::state_count)
        .def_ro("total_ms", &gpu::ExactWorldStepForceGroundStats::total_ms);
    nb::class_<gpu::ExactWorldStepAircraftTailStats>(m, "ExactWorldStepAircraftTailStats")
        .def(nb::init<>())
        .def_ro("state_count", &gpu::ExactWorldStepAircraftTailStats::state_count)
        .def_ro("total_ms", &gpu::ExactWorldStepAircraftTailStats::total_ms);
    nb::class_<gpu::ExactWorldStepAircraftTailCudaStats>(m, "ExactWorldStepAircraftTailCudaStats")
        .def(nb::init<>())
        .def_ro("state_count", &gpu::ExactWorldStepAircraftTailCudaStats::state_count)
        .def_ro("used_cuda", &gpu::ExactWorldStepAircraftTailCudaStats::used_cuda)
        .def_ro("host_to_device_ms", &gpu::ExactWorldStepAircraftTailCudaStats::host_to_device_ms)
        .def_ro("kernel_ms", &gpu::ExactWorldStepAircraftTailCudaStats::kernel_ms)
        .def_ro("device_to_host_ms", &gpu::ExactWorldStepAircraftTailCudaStats::device_to_host_ms)
        .def_ro("cpu_fallback_ms", &gpu::ExactWorldStepAircraftTailCudaStats::cpu_fallback_ms)
        .def_ro("total_ms", &gpu::ExactWorldStepAircraftTailCudaStats::total_ms);
    nb::class_<gpu::ExactWorldStepAircraftChainCudaStats>(m, "ExactWorldStepAircraftChainCudaStats")
        .def(nb::init<>())
        .def_ro("state_count", &gpu::ExactWorldStepAircraftChainCudaStats::state_count)
        .def_ro("used_cuda", &gpu::ExactWorldStepAircraftChainCudaStats::used_cuda)
        .def_ro("command_lane_ms", &gpu::ExactWorldStepAircraftChainCudaStats::command_lane_ms)
        .def_ro("host_to_device_ms", &gpu::ExactWorldStepAircraftChainCudaStats::host_to_device_ms)
        .def_ro("kernel_ms", &gpu::ExactWorldStepAircraftChainCudaStats::kernel_ms)
        .def_ro("device_to_host_ms", &gpu::ExactWorldStepAircraftChainCudaStats::device_to_host_ms)
        .def_ro("cpu_post_command_ms", &gpu::ExactWorldStepAircraftChainCudaStats::cpu_post_command_ms)
        .def_ro("total_ms", &gpu::ExactWorldStepAircraftChainCudaStats::total_ms);
    nb::class_<gpu::ExactWorldStepFirstScopeChainCudaStats>(m, "ExactWorldStepFirstScopeChainCudaStats")
        .def(nb::init<>())
        .def_ro("state_count", &gpu::ExactWorldStepFirstScopeChainCudaStats::state_count)
        .def_ro("missile_count", &gpu::ExactWorldStepFirstScopeChainCudaStats::missile_count)
        .def_ro("used_cuda", &gpu::ExactWorldStepFirstScopeChainCudaStats::used_cuda)
        .def_ro("command_lane_ms", &gpu::ExactWorldStepFirstScopeChainCudaStats::command_lane_ms)
        .def_ro("host_to_device_ms", &gpu::ExactWorldStepFirstScopeChainCudaStats::host_to_device_ms)
        .def_ro("front_kernel_ms", &gpu::ExactWorldStepFirstScopeChainCudaStats::front_kernel_ms)
        .def_ro("guidance_kernel_ms", &gpu::ExactWorldStepFirstScopeChainCudaStats::guidance_kernel_ms)
        .def_ro("tail_kernel_ms", &gpu::ExactWorldStepFirstScopeChainCudaStats::tail_kernel_ms)
        .def_ro("kernel_ms", &gpu::ExactWorldStepFirstScopeChainCudaStats::kernel_ms)
        .def_ro("device_to_host_ms", &gpu::ExactWorldStepFirstScopeChainCudaStats::device_to_host_ms)
        .def_ro("cpu_fallback_ms", &gpu::ExactWorldStepFirstScopeChainCudaStats::cpu_fallback_ms)
        .def_ro("total_ms", &gpu::ExactWorldStepFirstScopeChainCudaStats::total_ms);
    nb::class_<gpu::ExactWorldStepMissileGuidanceStats>(m, "ExactWorldStepMissileGuidanceStats")
        .def(nb::init<>())
        .def_ro("state_count", &gpu::ExactWorldStepMissileGuidanceStats::state_count)
        .def_ro("missile_count", &gpu::ExactWorldStepMissileGuidanceStats::missile_count)
        .def_ro("total_ms", &gpu::ExactWorldStepMissileGuidanceStats::total_ms);
    nb::class_<gpu::ExactWorldStepMissileGuidanceCudaStats>(m, "ExactWorldStepMissileGuidanceCudaStats")
        .def(nb::init<>())
        .def_ro("state_count", &gpu::ExactWorldStepMissileGuidanceCudaStats::state_count)
        .def_ro("missile_count", &gpu::ExactWorldStepMissileGuidanceCudaStats::missile_count)
        .def_ro("used_cuda", &gpu::ExactWorldStepMissileGuidanceCudaStats::used_cuda)
        .def_ro("host_to_device_ms", &gpu::ExactWorldStepMissileGuidanceCudaStats::host_to_device_ms)
        .def_ro("kernel_ms", &gpu::ExactWorldStepMissileGuidanceCudaStats::kernel_ms)
        .def_ro("device_to_host_ms", &gpu::ExactWorldStepMissileGuidanceCudaStats::device_to_host_ms)
        .def_ro("cpu_fallback_ms", &gpu::ExactWorldStepMissileGuidanceCudaStats::cpu_fallback_ms)
        .def_ro("total_ms", &gpu::ExactWorldStepMissileGuidanceCudaStats::total_ms);
    nb::class_<ExactWorldStepFirstScopeChainCachedSessionStats>(m, "ExactWorldStepFirstScopeChainCachedSessionStats")
        .def(nb::init<>())
        .def_ro("state_count", &ExactWorldStepFirstScopeChainCachedSessionStats::state_count)
        .def_ro("used_gpu", &ExactWorldStepFirstScopeChainCachedSessionStats::used_gpu)
        .def_ro("prime_extract_ms", &ExactWorldStepFirstScopeChainCachedSessionStats::prime_extract_ms)
        .def_ro("pilot_update_ms", &ExactWorldStepFirstScopeChainCachedSessionStats::pilot_update_ms)
        .def_ro("mission_update_ms", &ExactWorldStepFirstScopeChainCachedSessionStats::mission_update_ms)
        .def_ro("step_total_ms", &ExactWorldStepFirstScopeChainCachedSessionStats::step_total_ms)
        .def_ro("write_back_ms", &ExactWorldStepFirstScopeChainCachedSessionStats::write_back_ms)
        .def_ro("chain_command_lane_ms", &ExactWorldStepFirstScopeChainCachedSessionStats::chain_command_lane_ms)
        .def_ro("chain_host_to_device_ms", &ExactWorldStepFirstScopeChainCachedSessionStats::chain_host_to_device_ms)
        .def_ro("chain_front_kernel_ms", &ExactWorldStepFirstScopeChainCachedSessionStats::chain_front_kernel_ms)
        .def_ro("chain_guidance_kernel_ms", &ExactWorldStepFirstScopeChainCachedSessionStats::chain_guidance_kernel_ms)
        .def_ro("chain_tail_kernel_ms", &ExactWorldStepFirstScopeChainCachedSessionStats::chain_tail_kernel_ms)
        .def_ro("chain_kernel_ms", &ExactWorldStepFirstScopeChainCachedSessionStats::chain_kernel_ms)
        .def_ro("chain_device_to_host_ms", &ExactWorldStepFirstScopeChainCachedSessionStats::chain_device_to_host_ms)
        .def_ro("chain_cpu_fallback_ms", &ExactWorldStepFirstScopeChainCachedSessionStats::chain_cpu_fallback_ms)
        .def_ro("chain_total_ms", &ExactWorldStepFirstScopeChainCachedSessionStats::chain_total_ms);
    nb::enum_<WorldBatchExactStepBackend>(m, "WorldBatchExactStepBackend")
        .value("CpuSimulationKernel", WorldBatchExactStepBackend::CpuSimulationKernel)
        .value("ExactFirstScopeChainCachedCpu", WorldBatchExactStepBackend::ExactFirstScopeChainCachedCpu)
        .value("ExactFirstScopeChainCachedGpu", WorldBatchExactStepBackend::ExactFirstScopeChainCachedGpu);
    m.def("last_exact_world_step_command_lane_stats", &gpu::last_exact_world_step_command_lane_stats);
    m.def("last_exact_world_step_front_half_stats", &gpu::last_exact_world_step_front_half_stats);
    m.def("last_exact_world_step_control_aero_stats", &gpu::last_exact_world_step_control_aero_stats);
    m.def("last_exact_world_step_force_ground_stats", &gpu::last_exact_world_step_force_ground_stats);
    m.def("last_exact_world_step_aircraft_tail_stats", &gpu::last_exact_world_step_aircraft_tail_stats);
    m.def("last_exact_world_step_aircraft_tail_cuda_stats", &gpu::last_exact_world_step_aircraft_tail_cuda_stats);
    m.def("last_exact_world_step_aircraft_chain_cuda_stats", &gpu::last_exact_world_step_aircraft_chain_cuda_stats);
    m.def("last_exact_world_step_first_scope_chain_cuda_stats", &gpu::last_exact_world_step_first_scope_chain_cuda_stats);
    m.def(
        "last_exact_world_step_first_scope_chain_cuda_output_device_ptr",
        []() {
            return static_cast<std::uintptr_t>(
                reinterpret_cast<std::uintptr_t>(
                    gpu::last_exact_world_step_first_scope_chain_cuda_output_device_ptr()
                )
            );
        }
    );
    m.def(
        "last_exact_world_step_first_scope_chain_cuda_output_state_count",
        &gpu::last_exact_world_step_first_scope_chain_cuda_output_state_count
    );
    m.def("last_exact_world_step_missile_guidance_stats", &gpu::last_exact_world_step_missile_guidance_stats);
    m.def("last_exact_world_step_missile_guidance_cuda_stats", &gpu::last_exact_world_step_missile_guidance_cuda_stats);
    m.def("last_exact_world_step_prototype_stats", &gpu::last_exact_world_step_prototype_stats);
    m.def(
        "step_exact_world_step_command_lane_reference_cpu_packed",
        [](const nb::bytes& packed) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            const auto stepped = gpu::step_exact_world_step_command_lane_reference_cpu_batch(states);
            const auto stepped_packed = gpu::pack_exact_world_step_states_v1(stepped);
            return nb::bytes(stepped_packed.data(), stepped_packed.size());
        },
        nb::arg("packed")
    );
    m.def(
        "step_exact_world_step_front_half_reference_cpu_packed",
        [](const nb::bytes& packed) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            const auto stepped = gpu::step_exact_world_step_front_half_reference_cpu_batch(states);
            const auto stepped_packed = gpu::pack_exact_world_step_states_v1(stepped);
            return nb::bytes(stepped_packed.data(), stepped_packed.size());
        },
        nb::arg("packed")
    );
    m.def(
        "step_exact_world_step_front_half_packed",
        [](const nb::bytes& packed, bool use_gpu) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            const auto stepped = use_gpu
                ? gpu::step_exact_world_step_front_half_batch(states)
                : gpu::step_exact_world_step_front_half_reference_cpu_batch(states);
            const auto stepped_packed = gpu::pack_exact_world_step_states_v1(stepped);
            return nb::bytes(stepped_packed.data(), stepped_packed.size());
        },
        nb::arg("packed"),
        nb::arg("use_gpu") = true
    );
    m.def(
        "step_exact_world_step_front_half_until_stage_packed",
        [](const nb::bytes& packed, const std::string& stop_stage_name) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            gpu::ExactWorldStepFrontHalfStopStage stop_stage = gpu::ExactWorldStepFrontHalfStopStage::GroundContact;
            if (stop_stage_name == "FlightControl") {
                stop_stage = gpu::ExactWorldStepFrontHalfStopStage::FlightControl;
            } else if (stop_stage_name == "ClearForces") {
                stop_stage = gpu::ExactWorldStepFrontHalfStopStage::ClearForces;
            } else if (stop_stage_name == "ComputeAeroState") {
                stop_stage = gpu::ExactWorldStepFrontHalfStopStage::ComputeAeroState;
            } else if (stop_stage_name == "ComputeForces") {
                stop_stage = gpu::ExactWorldStepFrontHalfStopStage::ComputeForces;
            } else if (stop_stage_name == "ComputeAerodynamics") {
                stop_stage = gpu::ExactWorldStepFrontHalfStopStage::ComputeAerodynamics;
            } else if (stop_stage_name == "GroundContact") {
                stop_stage = gpu::ExactWorldStepFrontHalfStopStage::GroundContact;
            } else {
                throw std::invalid_argument("unknown front-half stop stage: " + stop_stage_name);
            }
            const auto stepped = gpu::step_exact_world_step_front_half_until_stage_batch(states, stop_stage);
            const auto stepped_packed = gpu::pack_exact_world_step_states_v1(stepped);
            return nb::bytes(stepped_packed.data(), stepped_packed.size());
        },
        nb::arg("packed"),
        nb::arg("stop_stage_name")
    );
    m.def(
        "step_exact_world_step_control_aero_reference_cpu_packed",
        [](const nb::bytes& packed) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            const auto stepped = gpu::step_exact_world_step_control_aero_reference_cpu_batch(states);
            const auto stepped_packed = gpu::pack_exact_world_step_states_v1(stepped);
            return nb::bytes(stepped_packed.data(), stepped_packed.size());
        },
        nb::arg("packed")
    );
    m.def(
        "step_exact_world_step_force_ground_reference_cpu_packed",
        [](const nb::bytes& packed) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            const auto stepped = gpu::step_exact_world_step_force_ground_reference_cpu_batch(states);
            const auto stepped_packed = gpu::pack_exact_world_step_states_v1(stepped);
            return nb::bytes(stepped_packed.data(), stepped_packed.size());
        },
        nb::arg("packed")
    );
    m.def(
        "step_exact_world_step_aircraft_tail_reference_cpu_packed",
        [](const nb::bytes& packed) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            const auto stepped = gpu::step_exact_world_step_aircraft_tail_reference_cpu_batch(states);
            const auto stepped_packed = gpu::pack_exact_world_step_states_v1(stepped);
            return nb::bytes(stepped_packed.data(), stepped_packed.size());
        },
        nb::arg("packed")
    );
    m.def(
        "step_exact_world_step_aircraft_tail_cuda_packed",
        [](const nb::bytes& packed, bool use_gpu) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            const auto stepped = use_gpu
                ? gpu::step_exact_world_step_aircraft_tail_cuda_batch(states)
                : gpu::step_exact_world_step_aircraft_tail_cuda_reference_cpu_batch(states);
            const auto stepped_packed = gpu::pack_exact_world_step_states_v1(stepped);
            return nb::bytes(stepped_packed.data(), stepped_packed.size());
        },
        nb::arg("packed"),
        nb::arg("use_gpu") = true
    );
    m.def(
        "step_exact_world_step_aircraft_tail_until_stage_packed",
        [](const nb::bytes& packed, const std::string& stop_stage_name, bool use_gpu) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            gpu::ExactWorldStepAircraftTailStopStage stop_stage =
                gpu::ExactWorldStepAircraftTailStopStage::MassUpdate;
            if (stop_stage_name == "RotationalIntegrate") {
                stop_stage = gpu::ExactWorldStepAircraftTailStopStage::RotationalIntegrate;
            } else if (stop_stage_name == "LeapfrogIntegrate") {
                stop_stage = gpu::ExactWorldStepAircraftTailStopStage::LeapfrogIntegrate;
            } else if (stop_stage_name == "NavigationSystem") {
                stop_stage = gpu::ExactWorldStepAircraftTailStopStage::NavigationSystem;
            } else if (stop_stage_name == "UpdateInstruments") {
                stop_stage = gpu::ExactWorldStepAircraftTailStopStage::UpdateInstruments;
            } else if (stop_stage_name == "FuelConsumption") {
                stop_stage = gpu::ExactWorldStepAircraftTailStopStage::FuelConsumption;
            } else if (stop_stage_name == "MassUpdate") {
                stop_stage = gpu::ExactWorldStepAircraftTailStopStage::MassUpdate;
            } else {
                throw std::invalid_argument("unknown aircraft-tail stop stage: " + stop_stage_name);
            }
            const auto stepped = use_gpu
                ? gpu::step_exact_world_step_aircraft_tail_cuda_until_stage_batch(states, stop_stage)
                : gpu::step_exact_world_step_aircraft_tail_until_stage_batch(states, stop_stage);
            const auto stepped_packed = gpu::pack_exact_world_step_states_v1(stepped);
            return nb::bytes(stepped_packed.data(), stepped_packed.size());
        },
        nb::arg("packed"),
        nb::arg("stop_stage_name"),
        nb::arg("use_gpu") = true
    );
    m.def(
        "step_exact_world_step_aircraft_chain_cuda_packed",
        [](const nb::bytes& packed, bool use_gpu) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            const auto stepped = use_gpu
                ? gpu::step_exact_world_step_aircraft_chain_cuda_batch(states)
                : gpu::step_exact_world_step_aircraft_chain_cuda_reference_cpu_batch(states);
            const auto stepped_packed = gpu::pack_exact_world_step_states_v1(stepped);
            return nb::bytes(stepped_packed.data(), stepped_packed.size());
        },
        nb::arg("packed"),
        nb::arg("use_gpu") = true
    );
    m.def(
        "step_exact_world_step_missile_guidance_reference_cpu_packed",
        [](const nb::bytes& packed) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            const auto stepped = gpu::step_exact_world_step_missile_guidance_reference_cpu_batch(states);
            const auto stepped_packed = gpu::pack_exact_world_step_states_v1(stepped);
            return nb::bytes(stepped_packed.data(), stepped_packed.size());
        },
        nb::arg("packed")
    );
    m.def(
        "step_exact_world_step_missile_guidance_cuda_packed",
        [](const nb::bytes& packed, bool use_gpu) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            const auto stepped = use_gpu
                ? gpu::step_exact_world_step_missile_guidance_cuda_batch(states)
                : gpu::step_exact_world_step_missile_guidance_cuda_reference_cpu_batch(states);
            const auto stepped_packed = gpu::pack_exact_world_step_states_v1(stepped);
            return nb::bytes(stepped_packed.data(), stepped_packed.size());
        },
        nb::arg("packed"),
        nb::arg("use_gpu") = true
    );
    m.def(
        "step_exact_world_step_first_scope_reference_cpu_packed",
        [](const nb::bytes& packed) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            states = gpu::step_exact_world_step_command_lane_reference_cpu_batch(states);
            states = gpu::step_exact_world_step_control_aero_reference_cpu_batch(states);
            states = gpu::step_exact_world_step_force_ground_reference_cpu_batch(states);
            states = gpu::step_exact_world_step_missile_guidance_reference_cpu_batch(states);
            states = gpu::step_exact_world_step_aircraft_tail_reference_cpu_batch(states);
            const auto stepped_packed = gpu::pack_exact_world_step_states_v1(states);
            return nb::bytes(stepped_packed.data(), stepped_packed.size());
        },
        nb::arg("packed")
    );
    m.def(
        "step_exact_world_step_first_scope_guidance_gpu_packed",
        [](const nb::bytes& packed, bool use_gpu) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            states = gpu::step_exact_world_step_command_lane_reference_cpu_batch(states);
            states = gpu::step_exact_world_step_control_aero_reference_cpu_batch(states);
            states = gpu::step_exact_world_step_force_ground_reference_cpu_batch(states);
            states = use_gpu
                ? gpu::step_exact_world_step_missile_guidance_cuda_batch(states)
                : gpu::step_exact_world_step_missile_guidance_cuda_reference_cpu_batch(states);
            states = gpu::step_exact_world_step_aircraft_tail_reference_cpu_batch(states);
            const auto stepped_packed = gpu::pack_exact_world_step_states_v1(states);
            return nb::bytes(stepped_packed.data(), stepped_packed.size());
        },
        nb::arg("packed"),
        nb::arg("use_gpu") = true
    );
    m.def(
        "step_exact_world_step_first_scope_chain_cuda_packed",
        [](const nb::bytes& packed, bool use_gpu) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            const auto stepped = use_gpu
                ? gpu::step_exact_world_step_first_scope_chain_cuda_batch(states)
                : gpu::step_exact_world_step_first_scope_chain_cuda_reference_cpu_batch(states);
            const auto stepped_packed = gpu::pack_exact_world_step_states_v1(stepped);
            return nb::bytes(stepped_packed.data(), stepped_packed.size());
        },
        nb::arg("packed"),
        nb::arg("use_gpu") = true
    );
    m.def(
        "upload_exact_world_step_first_scope_chain_cuda_states_packed",
        [](const nb::bytes& packed) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            return gpu::upload_exact_world_step_first_scope_chain_cuda_states(states);
        },
        nb::arg("packed")
    );
    m.def(
        "replay_exact_world_step_first_scope_chain_cuda_device_sequence",
        &gpu::replay_exact_world_step_first_scope_chain_cuda_device_sequence
    );
    m.def(
        "download_exact_world_step_first_scope_chain_cuda_states_packed",
        []() {
            const auto states = gpu::download_exact_world_step_first_scope_chain_cuda_states();
            const auto packed = gpu::pack_exact_world_step_states_v1(states);
            return nb::bytes(packed.data(), packed.size());
        }
    );
    m.def(
        "step_exact_world_step_states_v1_prototype_packed",
        [](const nb::bytes& packed, int steps, bool use_gpu) {
            auto states = gpu::unpack_exact_world_step_states_v1(
                std::string_view(packed.c_str(), packed.size())
            );
            const auto stepped = use_gpu
                ? gpu::step_exact_world_step_states_v1_prototype_batch(states, steps)
                : gpu::step_exact_world_step_states_v1_prototype_reference_cpu_batch(states, steps);
            const auto stepped_packed = gpu::pack_exact_world_step_states_v1(stepped);
            return nb::bytes(stepped_packed.data(), stepped_packed.size());
        },
        nb::arg("packed"),
        nb::arg("steps"),
        nb::arg("use_gpu") = true
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

    nb::class_<RWREvent>(m, "RWREvent")
        .def_ro("source_id", &RWREvent::source_id)
        .def_ro("bearing", &RWREvent::bearing)
        .def_ro("signal_strength", &RWREvent::signal_strength)
        .def_ro("is_lock", &RWREvent::is_lock)
        .def_ro("is_launch", &RWREvent::is_launch);

    // Bind UnitType Enum
    nb::enum_<UnitType>(m, "UnitType")
        .value("Aircraft", UnitType::Aircraft)
        .value("Ship", UnitType::Ship)
        .value("Missile", UnitType::Missile)
        .value("Facility", UnitType::Facility)
        .value("C2Node", UnitType::C2Node);

    // Bind InstrumentState
    nb::class_<InstrumentState>(m, "InstrumentState")
        .def(nb::init<>())
        .def_rw("alt_baro", &InstrumentState::alt_baro_m)
        .def_rw("alt_radar", &InstrumentState::alt_radar_m)
        .def_rw("ias", &InstrumentState::ias_mps)
        .def_rw("mach", &InstrumentState::mach)
        .def_rw("vvi", &InstrumentState::vvi_mps)
        .def_rw("pitch", &InstrumentState::pitch_deg)
        .def_rw("roll", &InstrumentState::roll_deg)
        .def_rw("heading", &InstrumentState::heading_deg)
        .def_rw("aoa", &InstrumentState::aoa_deg)
        .def_rw("beta", &InstrumentState::beta_deg)
        .def_rw("g_load", &InstrumentState::g_load_normal)
        .def_rw("g_load_axial", &InstrumentState::g_load_axial)
        .def_rw("p", &InstrumentState::p_deg_s)
        .def_rw("q", &InstrumentState::q_deg_s)
        .def_rw("r", &InstrumentState::r_deg_s)
        .def_rw("engine_rpm", &InstrumentState::engine_rpm_pct)
        .def_rw("engine_temp", &InstrumentState::engine_temp_c)
        .def_rw("fuel_flow", &InstrumentState::fuel_flow_kg_h)
        .def_rw("throttle_pos", &InstrumentState::throttle_pos)
        .def_rw("fuel_internal", &InstrumentState::fuel_internal_kg)
        .def_rw("fuel_external", &InstrumentState::fuel_external_kg)
        .def_rw("gear_pos", &InstrumentState::gear_pos)
        .def_rw("flaps_pos", &InstrumentState::flaps_pos)
        .def_rw("speedbrake_pos", &InstrumentState::speedbrake_pos)
        .def_rw("master_arm", &InstrumentState::master_arm)
        .def_rw("oat", &InstrumentState::oat_c)
        .def_rw("cmd_heading", &InstrumentState::cmd_heading_deg)
        .def_rw("cmd_alt", &InstrumentState::cmd_alt_m)
        .def_rw("cmd_speed", &InstrumentState::cmd_speed_mps)
        .def_rw("rwr_active", &InstrumentState::rwr_active)
        .def_rw("missiles_remaining", &InstrumentState::missiles_remaining)
        // EGI / Navigation
        .def_rw("lat", &InstrumentState::lat_deg)
        .def_rw("lon", &InstrumentState::lon_deg)
        .def_rw("vn", &InstrumentState::vn_mps)
        .def_rw("ve", &InstrumentState::ve_mps)
        .def_rw("vd", &InstrumentState::vd_mps)
        .def_rw("ground_speed", &InstrumentState::ground_speed_mps)
        .def_rw("ground_track", &InstrumentState::ground_track_deg)
        .def_rw("wind_speed", &InstrumentState::wind_speed_mps)
        .def_rw("wind_dir", &InstrumentState::wind_dir_deg)
        .def_rw("gps_available", &InstrumentState::gps_available)
        .def_rw("position_uncertainty", &InstrumentState::position_uncertainty_m)
        // Internal physics (for reward, not observation)
        .def_rw("gear_stress", &InstrumentState::gear_stress)
        .def_rw("gear_collapsed", &InstrumentState::gear_collapsed)
        .def_rw("on_runway", &InstrumentState::on_runway);

    // Bind EGI
    nb::class_<EGI>(m, "EGI")
        .def(nb::init<>())
        .def_rw("lat", &EGI::lat_deg)
        .def_rw("lon", &EGI::lon_deg)
        .def_rw("alt_baro", &EGI::alt_baro_m)
        .def_rw("alt_radar", &EGI::alt_radar_m)
        .def_rw("vn", &EGI::vn_mps)
        .def_rw("ve", &EGI::ve_mps)
        .def_rw("vd", &EGI::vd_mps)
        .def_rw("heading", &EGI::heading_deg)
        .def_rw("pitch", &EGI::pitch_deg)
        .def_rw("roll", &EGI::roll_deg)
        .def_rw("wind_speed", &EGI::wind_speed_mps)
        .def_rw("wind_dir", &EGI::wind_dir_deg)
        .def_rw("drift_lat", &EGI::drift_lat_m)
        .def_rw("drift_lon", &EGI::drift_lon_m)
        .def_rw("drift_alt", &EGI::drift_alt_m)
        .def_rw("pos_uncertainty", &EGI::position_uncertainty_m)
        .def_rw("time_since_fix", &EGI::time_since_last_gps_fix)
        .def_rw("gps_avail", &EGI::gps_available);

    // Bind MissileTuning
    nb::class_<MissileTuning>(m, "MissileTuning")
        .def(nb::init<>())
        .def_rw("max_speed", &MissileTuning::max_speed)
        .def_rw("turn_rate", &MissileTuning::turn_rate)
        .def_rw("fuse_distance", &MissileTuning::fuse_distance)
        .def_rw("damage", &MissileTuning::damage)
        .def_rw("seeker_fov_deg", &MissileTuning::seeker_fov_deg)
        .def_rw("seeker_lock_range", &MissileTuning::seeker_lock_range)
        .def_rw("guidance_delay_s", &MissileTuning::guidance_delay_s)
        .def_rw("guidance_update_period_s", &MissileTuning::guidance_update_period_s)
        .def_rw("max_flight_time_s", &MissileTuning::max_flight_time_s)
        .def_rw("nav_gain", &MissileTuning::nav_gain)
        .def_rw("sensor_max_range", &MissileTuning::sensor_max_range)
        .def_rw("sensor_fov_deg", &MissileTuning::sensor_fov_deg)
        .def_rw("sensor_scan_period", &MissileTuning::sensor_scan_period)
        .def_rw("sensor_detection_prob", &MissileTuning::sensor_detection_prob)
        .def_rw("sensor_bearing_noise_std", &MissileTuning::sensor_bearing_noise_std)
        .def_rw("sensor_range_noise_std", &MissileTuning::sensor_range_noise_std)
        .def_rw("sensor_track_memory_s", &MissileTuning::sensor_track_memory_s);

    // Bind PilotAction
    nb::class_<PilotAction>(m, "PilotAction")
        .def(nb::init<>())
        .def_rw("stick_pitch", &PilotAction::stick_pitch)
        .def_rw("stick_roll", &PilotAction::stick_roll)
        .def_rw("rudder", &PilotAction::rudder)
        .def_rw("throttle", &PilotAction::throttle)
        .def_rw("gear_handle", &PilotAction::gear_handle)
        .def_rw("flaps", &PilotAction::flaps)
        .def_rw("speedbrake", &PilotAction::speedbrake)
        .def_rw("brake", &PilotAction::brake)
        .def_rw("brake_left", &PilotAction::brake_left)
        .def_rw("brake_right", &PilotAction::brake_right)
        .def_rw("radar_active", &PilotAction::radar_active)
        .def_rw("radar_scan_az", &PilotAction::radar_scan_az)
        .def_rw("radar_scan_el", &PilotAction::radar_scan_el)
        .def_rw("tms_up", &PilotAction::tms_up)
        .def_rw("master_arm", &PilotAction::master_arm)
        .def_rw("fire_weapon", &PilotAction::fire_weapon)
        .def_rw("fire_gun", &PilotAction::fire_gun)
        .def_rw("weapon_select_id", &PilotAction::weapon_select_id)
        .def_rw("jettison_emergency", &PilotAction::jettison_emergency)
        .def_rw("program_chaff", &PilotAction::program_chaff)
        .def_rw("program_flare", &PilotAction::program_flare)
        .def_rw("active", &PilotAction::active);

    // Bind MissionCommand
    nb::class_<MissionCommand>(m, "MissionCommand")
        .def(nb::init<>())
        .def_rw("cmd_heading_deg", &MissionCommand::cmd_heading_deg)
        .def_rw("cmd_altitude_m", &MissionCommand::cmd_altitude_m)
        .def_rw("cmd_speed_mps", &MissionCommand::cmd_speed_mps)
        .def_rw("command_code", &MissionCommand::command_code)
        .def_rw("route_ref_id", &MissionCommand::route_ref_id)
        .def_rw("recovery_base_id", &MissionCommand::recovery_base_id)
        .def_rw("recovery_runway_id", &MissionCommand::recovery_runway_id)
        .def_rw("recovery_approach_type", &MissionCommand::recovery_approach_type)
        .def_rw("formation_id", &MissionCommand::formation_id)
        .def_rw("form_offset_x", &MissionCommand::form_offset_x)
        .def_rw("form_offset_y", &MissionCommand::form_offset_y)
        .def_rw("form_offset_z", &MissionCommand::form_offset_z)
        .def_rw("assigned_target_id", &MissionCommand::assigned_target_id)
        .def_rw("authorization_to_fire", &MissionCommand::authorization_to_fire)
        .def_rw("active", &MissionCommand::active);

    nb::class_<TaskOrder>(m, "TaskOrder")
        .def(nb::init<>())
        .def_rw("task_id", &TaskOrder::task_id)
        .def_rw("task_type", &TaskOrder::task_type)
        .def_rw("service_profile", &TaskOrder::service_profile)
        .def_rw("task_family", &TaskOrder::task_family)
        .def_rw("tactical_unit_type", &TaskOrder::tactical_unit_type)
        .def_rw("priority", &TaskOrder::priority)
        .def_rw("issuer_id", &TaskOrder::issuer_id)
        .def_rw("assignee_id", &TaskOrder::assignee_id)
        .def_rw("command_relationship", &TaskOrder::command_relationship)
        .def_rw("authority_scope", &TaskOrder::authority_scope)
        .def_rw("parent_node_id", &TaskOrder::parent_node_id)
        .def_rw("task_group_id", &TaskOrder::task_group_id)
        .def_rw("supported_node_id", &TaskOrder::supported_node_id)
        .def_rw("supporting_node_id", &TaskOrder::supporting_node_id)
        .def_rw("role_code", &TaskOrder::role_code)
        .def_rw("coordination_mode", &TaskOrder::coordination_mode)
        .def_rw("relative_slot_code", &TaskOrder::relative_slot_code)
        .def_rw("assignee_kind", &TaskOrder::assignee_kind)
        .def_rw("recovery_site_id", &TaskOrder::recovery_site_id)
        .def_rw("element_id", &TaskOrder::element_id)
        .def_rw("package_id", &TaskOrder::package_id)
        .def_rw("lead_aircraft_id", &TaskOrder::lead_aircraft_id)
        .def_rw("active", &TaskOrder::active)
        .def_rw("issue_time_s", &TaskOrder::issue_time_s)
        .def_rw("anchor_x_m", &TaskOrder::anchor_x_m)
        .def_rw("anchor_y_m", &TaskOrder::anchor_y_m)
        .def_rw("anchor_z_m", &TaskOrder::anchor_z_m)
        .def_rw("station_type", &TaskOrder::station_type)
        .def_rw("station_radius_m", &TaskOrder::station_radius_m)
        .def_rw("station_leg_length_m", &TaskOrder::station_leg_length_m)
        .def_rw("station_heading_deg", &TaskOrder::station_heading_deg)
        .def_rw("altitude_block_min_m", &TaskOrder::altitude_block_min_m)
        .def_rw("altitude_block_max_m", &TaskOrder::altitude_block_max_m)
        .def_rw("target_altitude_m", &TaskOrder::target_altitude_m)
        .def_rw("speed_min_mps", &TaskOrder::speed_min_mps)
        .def_rw("speed_max_mps", &TaskOrder::speed_max_mps)
        .def_rw("target_speed_mps", &TaskOrder::target_speed_mps)
        .def_rw("entry_condition_code", &TaskOrder::entry_condition_code)
        .def_rw("exit_condition_code", &TaskOrder::exit_condition_code)
        .def_rw("on_station_time_s", &TaskOrder::on_station_time_s)
        .def_rw("fuel_bingo_override_kg", &TaskOrder::fuel_bingo_override_kg)
        .def_rw("recovery_base_id", &TaskOrder::recovery_base_id)
        .def_rw("recovery_runway_id", &TaskOrder::recovery_runway_id)
        .def_rw("recovery_approach_type", &TaskOrder::recovery_approach_type)
        .def_rw("formation_template_id", &TaskOrder::formation_template_id)
        .def_rw("formation_contract_id", &TaskOrder::formation_contract_id)
        .def_rw("formation_role_id", &TaskOrder::formation_role_id)
        .def_rw("wingman_slot_id", &TaskOrder::wingman_slot_id)
        .def_rw("join_policy_id", &TaskOrder::join_policy_id)
        .def_rw("rejoin_policy_id", &TaskOrder::rejoin_policy_id)
        .def_rw("mutual_support_mode", &TaskOrder::mutual_support_mode)
        .def_rw("support_sector_id", &TaskOrder::support_sector_id);

    nb::class_<LeaderIntent>(m, "LeaderIntent")
        .def(nb::init<>())
        .def_rw("phase_id", &LeaderIntent::phase_id)
        .def_rw("element_phase_id", &LeaderIntent::element_phase_id)
        .def_rw("service_profile", &LeaderIntent::service_profile)
        .def_rw("task_family", &LeaderIntent::task_family)
        .def_rw("tactical_unit_type", &LeaderIntent::tactical_unit_type)
        .def_rw("tactical_unit_id", &LeaderIntent::tactical_unit_id)
        .def_rw("task_group_id", &LeaderIntent::task_group_id)
        .def_rw("role_code", &LeaderIntent::role_code)
        .def_rw("coordination_mode", &LeaderIntent::coordination_mode)
        .def_rw("relative_slot_code", &LeaderIntent::relative_slot_code)
        .def_rw("recovery_site_id", &LeaderIntent::recovery_site_id)
        .def_rw("command_code", &LeaderIntent::command_code)
        .def_rw("route_ref_id", &LeaderIntent::route_ref_id)
        .def_rw("recovery_base_id", &LeaderIntent::recovery_base_id)
        .def_rw("recovery_runway_id", &LeaderIntent::recovery_runway_id)
        .def_rw("recovery_approach_type", &LeaderIntent::recovery_approach_type)
        .def_rw("cmd_heading_deg", &LeaderIntent::cmd_heading_deg)
        .def_rw("cmd_altitude_m", &LeaderIntent::cmd_altitude_m)
        .def_rw("cmd_speed_mps", &LeaderIntent::cmd_speed_mps)
        .def_rw("formation_id", &LeaderIntent::formation_id)
        .def_rw("form_offset_x", &LeaderIntent::form_offset_x)
        .def_rw("form_offset_y", &LeaderIntent::form_offset_y)
        .def_rw("form_offset_z", &LeaderIntent::form_offset_z)
        .def_rw("assigned_target_id", &LeaderIntent::assigned_target_id)
        .def_rw("authorization_to_fire", &LeaderIntent::authorization_to_fire)
        .def_rw("formation_mode_id", &LeaderIntent::formation_mode_id)
        .def_rw("join_required_flag", &LeaderIntent::join_required_flag)
        .def_rw("rejoin_required_flag", &LeaderIntent::rejoin_required_flag)
        .def_rw("split_flag", &LeaderIntent::split_flag)
        .def_rw("support_anchor_x_m", &LeaderIntent::support_anchor_x_m)
        .def_rw("support_anchor_y_m", &LeaderIntent::support_anchor_y_m)
        .def_rw("support_slot_offset_x_m", &LeaderIntent::support_slot_offset_x_m)
        .def_rw("support_slot_offset_y_m", &LeaderIntent::support_slot_offset_y_m)
        .def_rw("wingman_command_mode", &LeaderIntent::wingman_command_mode)
        .def_rw("approach_armed", &LeaderIntent::approach_armed)
        .def_rw("commit_to_land", &LeaderIntent::commit_to_land)
        .def_rw("abort_flag", &LeaderIntent::abort_flag)
        .def_rw("active", &LeaderIntent::active);

    nb::class_<WorldEntityRef>(m, "WorldEntityRef")
        .def(nb::init<>())
        .def_rw("world_index", &WorldEntityRef::world_index)
        .def_rw("entity_id", &WorldEntityRef::entity_id);

    nb::class_<WorldTerrainAssignment>(m, "WorldTerrainAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldTerrainAssignment::world_index)
        .def_rw("terrain_type", &WorldTerrainAssignment::terrain_type);

    nb::class_<WorldWindAssignment>(m, "WorldWindAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldWindAssignment::world_index)
        .def_rw("speed_mps", &WorldWindAssignment::speed_mps)
        .def_rw("dir_from_deg", &WorldWindAssignment::dir_from_deg)
        .def_rw("shear_mps_per_km", &WorldWindAssignment::shear_mps_per_km);

    nb::class_<WorldZoneDefinition>(m, "WorldZoneDefinition")
        .def(nb::init<>())
        .def_rw("world_index", &WorldZoneDefinition::world_index)
        .def_rw("name", &WorldZoneDefinition::name)
        .def_rw("x", &WorldZoneDefinition::x)
        .def_rw("y", &WorldZoneDefinition::y)
        .def_rw("width", &WorldZoneDefinition::width)
        .def_rw("length", &WorldZoneDefinition::length)
        .def_rw("heading", &WorldZoneDefinition::heading)
        .def_rw("surface_type", &WorldZoneDefinition::surface_type);

    nb::class_<WorldSpawnRequest>(m, "WorldSpawnRequest")
        .def(nb::init<>())
        .def_rw("world_index", &WorldSpawnRequest::world_index)
        .def_rw("side", &WorldSpawnRequest::side)
        .def_rw("type_name", &WorldSpawnRequest::type_name)
        .def_rw("entity_name", &WorldSpawnRequest::entity_name)
        .def_rw("is_agent", &WorldSpawnRequest::is_agent)
        .def_rw("x", &WorldSpawnRequest::x)
        .def_rw("y", &WorldSpawnRequest::y)
        .def_rw("z", &WorldSpawnRequest::z)
        .def_rw("heading", &WorldSpawnRequest::heading)
        .def_rw("pitch", &WorldSpawnRequest::pitch)
        .def_rw("roll", &WorldSpawnRequest::roll)
        .def_rw("vx", &WorldSpawnRequest::vx)
        .def_rw("vy", &WorldSpawnRequest::vy)
        .def_rw("vz", &WorldSpawnRequest::vz);

    nb::class_<WorldPilotActionAssignment>(m, "WorldPilotActionAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldPilotActionAssignment::world_index)
        .def_rw("entity_id", &WorldPilotActionAssignment::entity_id)
        .def_rw("action", &WorldPilotActionAssignment::action);

    nb::class_<WorldMissionCommandAssignment>(m, "WorldMissionCommandAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldMissionCommandAssignment::world_index)
        .def_rw("entity_id", &WorldMissionCommandAssignment::entity_id)
        .def_rw("command", &WorldMissionCommandAssignment::command);

    nb::class_<WorldTaskOrderAssignment>(m, "WorldTaskOrderAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldTaskOrderAssignment::world_index)
        .def_rw("entity_id", &WorldTaskOrderAssignment::entity_id)
        .def_rw("order", &WorldTaskOrderAssignment::order);

    nb::class_<WorldLeaderIntentAssignment>(m, "WorldLeaderIntentAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldLeaderIntentAssignment::world_index)
        .def_rw("entity_id", &WorldLeaderIntentAssignment::entity_id)
        .def_rw("intent", &WorldLeaderIntentAssignment::intent);

    nb::class_<WorldPilotReportAssignment>(m, "WorldPilotReportAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldPilotReportAssignment::world_index)
        .def_rw("entity_id", &WorldPilotReportAssignment::entity_id)
        .def_rw("report", &WorldPilotReportAssignment::report);

    nb::class_<SimulationKernel>(m, "SimulationKernel")
        .def(nb::init<>())
        .def("get_instrument_state", [](SimulationKernel& self, uint64_t entity_id) {
            auto e = self.get_world().entity(entity_id);
            if (e.is_valid()) {
                const InstrumentState* inst = e.get<InstrumentState>();
                if (inst) return *inst;
            }
            return InstrumentState{};
        }, "Get the instrument state for a unit")
        .def("get_egi_state", [](SimulationKernel& self, uint64_t entity_id) {
            auto e = self.get_world().entity(entity_id);
            if (e.is_valid()) {
                const EGI* egi = e.get<EGI>();
                if (egi) return *egi;
            }
            return EGI{};
        }, "Get the EGI state for a unit")
        .def("reset", &SimulationKernel::reset, "Reset the simulation", nb::arg("seed") = 42)
        .def("load_database", &SimulationKernel::load_database, nb::arg("path"), "Load unit definitions from JSON directory")
        .def("step", &SimulationKernel::step, "Advance simulation by one fixed tick")
        .def(
            "exact_gpu_migration_stage_inventory",
            [](const SimulationKernel& self) {
                return exact_step_stage_descriptor_list(self.exact_gpu_migration_stage_inventory());
            },
            "Describe the current exact-step system inventory and which stages are in the first GPU migration scope."
        )
        .def(
            "exact_gpu_migration_stage_contract_inventory",
            [](const SimulationKernel& self) {
                return exact_step_stage_contract_descriptor_list(self.exact_gpu_migration_stage_contract_inventory());
            },
            "Describe the structured read/write contracts for the current exact-step GPU migration stage scope."
        )
        .def(
            "begin_exact_stage_trace_frame",
            &SimulationKernel::begin_exact_stage_trace_frame,
            "Begin a manual exact-stage frame for per-system trace replay."
        )
        .def(
            "end_exact_stage_trace_frame",
            &SimulationKernel::end_exact_stage_trace_frame,
            "End a manual exact-stage frame for per-system trace replay."
        )
        .def(
            "run_exact_stage_trace_stage",
            &SimulationKernel::run_exact_stage_trace_stage,
            nb::arg("stage_name"),
            "Run one manual exact-stage traceable system inside an active exact-stage frame."
        )
        .def(
            "run_exact_stage_direct",
            &SimulationKernel::run_exact_stage_direct,
            nb::arg("stage_name"),
            "Run one exact system directly without opening a new frame."
        )
        .def(
            "step_exact_stage_traceable_pipeline",
            &SimulationKernel::step_exact_stage_traceable_pipeline,
            "Run the current exact-step GPU-migration traceable pipeline stage-by-stage."
        )
        .def("get_time_step", &SimulationKernel::get_time_step, "Get the fixed time step in seconds")
        .def("set_time_step", &SimulationKernel::set_time_step, "Set the fixed time step in seconds")
        .def(
            "restore_exact_replay_world_time",
            &SimulationKernel::restore_exact_replay_world_time,
            nb::arg("world_time_s"),
            "Reset and restore the Flecs world clock for exact-stage replay."
        )
        .def("load_unit_definitions", [](SimulationKernel& self, const std::string& path) {
            std::string error;
            bool ok = self.load_unit_definitions(path, &error);
            if (!ok) {
                spdlog::warn("Failed to load unit definitions: {}", error);
            }
            return ok;
        }, "Load unit definitions from JSON", nb::arg("path"))
        .def("clear_zones", &SimulationKernel::clear_zones, "Clear all environment zones")
        .def("add_zone", &SimulationKernel::add_zone, 
             "Add a new environment zone",
             nb::arg("name"), nb::arg("x"), nb::arg("y"), nb::arg("width"), nb::arg("height"), nb::arg("heading"), nb::arg("surface_type"))
        .def("set_wind", &SimulationKernel::set_wind,
             "Set global wind (speed m/s, dir_from_deg NAV, shear m/s per km)",
             nb::arg("speed_mps"), nb::arg("dir_from_deg"), nb::arg("shear_mps_per_km") = 0.0)
        .def("set_terrain_type", &SimulationKernel::set_terrain_type,
             "Set terrain profile (e.g. 'flat', 'legacy', 'hill')",
             nb::arg("terrain_type"))
        .def("spawn_unit", [](SimulationKernel& self, Side side, const std::string& type, 
                              double x, double y, double z, 
                              double heading, double pitch, double roll,
                              double vx, double vy, double vz) {
            // We return the Entity ID as an integer for MVP
            auto e = self.spawn_unit(side, type, x, y, z, heading, pitch, roll, vx, vy, vz);
            return e.id();
        }, "Spawn a unit by name with orientation and return its Entity ID", 
           nb::arg("side"), nb::arg("type_name"), 
           nb::arg("x"), nb::arg("y"), nb::arg("z"), 
           nb::arg("heading")=0.0, nb::arg("pitch")=0.0, nb::arg("roll")=0.0,
           nb::arg("vx")=0.0, nb::arg("vy")=0.0, nb::arg("vz")=0.0)
        .def("spawn_unit", [](SimulationKernel& self, Side side, UnitType type,
                              double x, double y, double z,
                              double heading, double pitch, double roll,
                              double vx, double vy, double vz) {
            auto e = self.spawn_unit(side, default_unit_name_for(type), x, y, z, heading, pitch, roll, vx, vy, vz);
            return e.id();
        }, "Spawn a default unit for the given UnitType with orientation and return its Entity ID",
           nb::arg("side"), nb::arg("type"),
           nb::arg("x"), nb::arg("y"), nb::arg("z"),
           nb::arg("heading")=0.0, nb::arg("pitch")=0.0, nb::arg("roll")=0.0,
           nb::arg("vx")=0.0, nb::arg("vy")=0.0, nb::arg("vz")=0.0)

        // Action Interface
        .def("set_command", &SimulationKernel::set_unit_command, "Set movement command for a unit",
             nb::arg("entity_id"), nb::arg("heading_deg"), nb::arg("speed_mps"), nb::arg("altitude_m"))
        .def("set_stick_command", &SimulationKernel::set_unit_stick_command, "Set stick inputs",
             nb::arg("entity_id"), nb::arg("stick_roll"), nb::arg("stick_pitch"), nb::arg("throttle"), nb::arg("gear_down")=true)
        .def("set_action", &SimulationKernel::set_unit_action, "Set normalized action for a unit",
             nb::arg("entity_id"),
             nb::arg("turn_rate_cmd"),
             nb::arg("accel_cmd"),
             nb::arg("climb_rate_cmd"),
             nb::arg("fire_cmd"),
             nb::arg("release_chaff") = false,
             nb::arg("release_flare") = false,
             nb::arg("jettison_tanks") = false)
        .def("set_action_space_config", &SimulationKernel::set_action_space_config, "Override action mapping scales for a unit",
             nb::arg("entity_id"),
             nb::arg("max_turn_rate_deg_s"),
             nb::arg("max_accel_mps2"),
             nb::arg("max_climb_rate_mps"),
             nb::arg("min_speed_mps"),
             nb::arg("max_speed_mps"),
             nb::arg("min_alt_m"),
             nb::arg("max_alt_m"))
        
        // Digital Pilot Bindings
        .def("set_pilot_action", &SimulationKernel::set_pilot_action, 
             "Set raw pilot inputs (stick, throttle, etc) for Digital Pilot",
             nb::arg("entity_id"), nb::arg("action"))
        .def("set_mission_command", &SimulationKernel::set_mission_command,
             "Set high-level mission intent for Digital Pilot",
             nb::arg("entity_id"), nb::arg("command"))
        .def("set_task_order", &SimulationKernel::set_task_order,
             "Set the C2 task order for the entity",
             nb::arg("entity_id"), nb::arg("task_order"))
        .def("set_leader_intent", &SimulationKernel::set_leader_intent,
             "Set the leader-layer intent for the entity",
             nb::arg("entity_id"), nb::arg("leader_intent"))
        .def("set_pilot_report", &SimulationKernel::set_pilot_report,
             "Store the latest pilot report for the entity",
             nb::arg("entity_id"), nb::arg("pilot_report"))

        .def("set_command_lag", &SimulationKernel::set_command_lag, "Override command lag time constants for a unit",
             nb::arg("entity_id"),
             nb::arg("heading_tau_s"),
             nb::arg("speed_tau_s"),
             nb::arg("altitude_tau_s"))
        .def("set_command_link", &SimulationKernel::set_command_link, "Set command link latency/drop probability",
             nb::arg("entity_id"), nb::arg("latency_s"), nb::arg("drop_prob"))
             
        .def("fire_missile", [](SimulationKernel& self, uint64_t attacker_id, uint64_t target_id) {
             auto e = self.fire_missile(attacker_id, target_id);
             return e.id(); // Return ID just like spawn_unit
        }, "Fire a missile from attacker to target", nb::arg("attacker_id"), nb::arg("target_id"))
        
        // Helper to get unit position (state observation)
        .def("get_unit_position", [](SimulationKernel& self, uint64_t entity_id) {
             auto p = self.get_unit_position(entity_id);
             return std::make_tuple(p[0], p[1], p[2]);
        }, "Get unit position (x,y,z)")
        
        // Helper to get unit heading (degrees, NAV convention: 0=North, CW)
        .def("get_unit_heading", [](SimulationKernel& self, uint64_t entity_id) {
             flecs::world& world = self.get_world();
             auto e = world.entity(entity_id);
             if(!e.is_valid()) return 0.0;
             const Transform* t = e.get<Transform>();
             if (t) return t->heading;
             const Velocity* v = e.get<Velocity>();
             if(!v) return 0.0;
             // Math angle: atan2(vy, vx) where 0=East, CCW positive
             double math_rad = std::atan2(v->vy, v->vx);
             double math_deg = math_rad * 180.0 / M_PI;
             // NAV angle: 0=North, CW positive => NAV = 90 - Math
             double nav_deg = 90.0 - math_deg;
             // Normalize to [0, 360)
             while (nav_deg < 0) nav_deg += 360.0;
             while (nav_deg >= 360.0) nav_deg -= 360.0;
             return nav_deg;
        }, "Get unit heading in degrees (NAV: 0=North, CW)")
        
        // Helper to get unit type
        .def("get_unit_type", [](SimulationKernel& self, uint64_t entity_id) {
             flecs::world& world = self.get_world();
             auto e = world.entity(entity_id);
             if(!e.is_valid()) return 0;
             const KeyEntity* k = e.get<KeyEntity>();
             return k ? (int)k->type : 0;
        }, "Get unit type enum value")
        
        // Helper to check if unit is active/alive
        .def("is_unit_active", [](SimulationKernel& self, uint64_t entity_id) {
             flecs::world& world = self.get_world();
             return world.entity(entity_id).is_valid();
        }, "Check if unit exists")
        
        .def("get_all_units", &SimulationKernel::get_all_units, "Get all units state")
        .def("get_detections", &SimulationKernel::get_detections, "Get unit sensor contacts")
        .def("get_unit_health", &SimulationKernel::get_unit_health, "Get unit health [current, max]")
        .def("get_unit_fuel", &SimulationKernel::get_unit_fuel, nb::arg("entity_id"),
             "Returns [internal, max_internal, external, max_external]")
        .def("get_task_order", &SimulationKernel::get_task_order, "Get the latest task order", nb::arg("entity_id"))
        .def("get_leader_intent", &SimulationKernel::get_leader_intent, "Get the latest leader intent", nb::arg("entity_id"))
        .def("get_mission_command", &SimulationKernel::get_mission_command, "Get the active mission command", nb::arg("entity_id"))
        .def("get_pilot_report", &SimulationKernel::get_pilot_report, "Get the latest pilot report", nb::arg("entity_id"))
        .def("get_agent_observation", &SimulationKernel::get_agent_observation, "Get complete agent observation")
        .def("get_visual_observation", [](SimulationKernel& self, uint64_t entity_id) {
             size_t shape[3] = {
                 static_cast<size_t>(arb::ARB_HEIGHT),
                 static_cast<size_t>(arb::ARB_WIDTH),
                 static_cast<size_t>(arb::ARB_CHANNELS),
             };
             return visual_tensor_to_numpy<
                 nb::shape<
                     static_cast<size_t>(arb::ARB_HEIGHT),
                     static_cast<size_t>(arb::ARB_WIDTH),
                     static_cast<size_t>(arb::ARB_CHANNELS)
                 >
             >(self.get_visual_observation(entity_id), 3, shape);
        }, "Get ARB visual observation [H, W, C] tensor", nb::arg("entity_id"))
        .def("get_visual_observation_downsampled", [](SimulationKernel& self, uint64_t entity_id, int factor) {
             const int downsample = factor > 1 ? factor : 1;
             auto downsampled = self.get_visual_observation_downsampled(entity_id, downsample);
             size_t shape[3] = {
                 static_cast<size_t>(arb::ARB_HEIGHT / downsample),
                 static_cast<size_t>(arb::ARB_WIDTH / downsample),
                 static_cast<size_t>(arb::ARB_CHANNELS),
             };
             return visual_tensor_to_numpy<
                 nb::shape<
                     nb::any,
                     nb::any,
                     static_cast<size_t>(arb::ARB_CHANNELS)
                 >
             >(std::move(downsampled), 3, shape);
        }, "Get ARB visual observation [H/f, W/f, C] tensor", nb::arg("entity_id"), nb::arg("factor"))
        .def("get_unit_messages", &SimulationKernel::get_unit_messages, "Get inbox")
        .def("send_message_command", &SimulationKernel::send_message_command, 
             nb::arg("entity_id"), nb::arg("recipient_id"), nb::arg("msg_type"), nb::arg("msg_arg"))
        .def("debug_get_last_scan_time", &SimulationKernel::debug_get_last_scan_time, "Debug: get sensor last_scan_time")
        .def("debug_get_contact_count", &SimulationKernel::debug_get_contact_count, "Debug: get ContactList size")
        .def("set_contact_list", &SimulationKernel::set_contact_list,
             "Override the ContactList for a unit or missile",
             nb::arg("entity_id"), nb::arg("detections"))
        .def("set_missile_tuning", &SimulationKernel::set_missile_tuning,
             "Override missile parameters for diagnostics", nb::arg("tuning"));

    nb::class_<WorldBatchRuntime>(m, "WorldBatchRuntime")
        .def(nb::init<size_t>(), nb::arg("world_count") = 0)
        .def("world_count", &WorldBatchRuntime::world_count)
        .def("resize", &WorldBatchRuntime::resize, nb::arg("world_count"))
        .def("set_worker_threads", &WorldBatchRuntime::set_worker_threads, nb::arg("worker_threads"))
        .def("worker_threads", &WorldBatchRuntime::worker_threads)
        .def("effective_worker_threads", &WorldBatchRuntime::effective_worker_threads)
        .def("world", nb::overload_cast<size_t>(&WorldBatchRuntime::world), nb::rv_policy::reference_internal, nb::arg("index"))
        .def("reset_batch", &WorldBatchRuntime::reset_batch, nb::arg("seeds") = std::vector<uint32_t>{})
        .def("step_batch", &WorldBatchRuntime::step_batch)
        .def("step_worlds", &WorldBatchRuntime::step_worlds, nb::arg("world_indices"))
        .def("set_exact_world_step_backend", &WorldBatchRuntime::set_exact_world_step_backend, nb::arg("backend"))
        .def("exact_world_step_backend", &WorldBatchRuntime::exact_world_step_backend)
        .def("exact_world_step_backend_ready", &WorldBatchRuntime::exact_world_step_backend_ready)
        .def("clear_exact_world_step_backend_session", &WorldBatchRuntime::clear_exact_world_step_backend_session)
        .def("load_database", &WorldBatchRuntime::load_database, nb::arg("path"))
        .def("load_unit_definitions", [](WorldBatchRuntime& self, const std::string& path) {
            std::string error;
            bool ok = self.load_unit_definitions(path, &error);
            if (!ok && !error.empty()) {
                spdlog::warn("WorldBatchRuntime failed to load unit definitions: {}", error);
            }
            return ok;
        }, nb::arg("path"))
        .def("set_time_step", &WorldBatchRuntime::set_time_step, nb::arg("dt"))
        .def("set_terrain_types_batch", &WorldBatchRuntime::set_terrain_types_batch, nb::arg("assignments"))
        .def("set_winds_batch", &WorldBatchRuntime::set_winds_batch, nb::arg("assignments"))
        .def("clear_zones_batch", &WorldBatchRuntime::clear_zones_batch, nb::arg("world_indices") = std::vector<uint64_t>{})
        .def("add_zones_batch", &WorldBatchRuntime::add_zones_batch, nb::arg("zones"))
        .def("spawn_units_batch", &WorldBatchRuntime::spawn_units_batch, nb::arg("requests"))
        .def(
            "apply_world_setup_batch",
            &WorldBatchRuntime::apply_world_setup_batch,
            nb::arg("seeds"),
            nb::arg("terrain_assignments"),
            nb::arg("wind_assignments"),
            nb::arg("zones"),
            nb::arg("requests"),
            nb::arg("time_steps") = std::vector<double>{}
        )
        .def("set_pilot_actions_batch", &WorldBatchRuntime::set_pilot_actions_batch, nb::arg("assignments"))
        .def("set_mission_commands_batch", &WorldBatchRuntime::set_mission_commands_batch, nb::arg("assignments"))
        .def("set_task_orders_batch", &WorldBatchRuntime::set_task_orders_batch, nb::arg("assignments"))
        .def("set_leader_intents_batch", &WorldBatchRuntime::set_leader_intents_batch, nb::arg("assignments"))
        .def("set_pilot_reports_batch", &WorldBatchRuntime::set_pilot_reports_batch, nb::arg("assignments"))
        .def("get_agent_observations_batch", &WorldBatchRuntime::get_agent_observations_batch, nb::arg("refs"))
        .def("get_instrument_states_batch", &WorldBatchRuntime::get_instrument_states_batch, nb::arg("refs"))
        .def("get_mission_commands_batch", &WorldBatchRuntime::get_mission_commands_batch, nb::arg("refs"))
        .def("get_task_orders_batch", &WorldBatchRuntime::get_task_orders_batch, nb::arg("refs"))
        .def("get_leader_intents_batch", &WorldBatchRuntime::get_leader_intents_batch, nb::arg("refs"))
        .def("get_pilot_reports_batch", &WorldBatchRuntime::get_pilot_reports_batch, nb::arg("refs"))
        .def(
            "get_sensor_candidate_ids_batch",
            &WorldBatchRuntime::get_sensor_candidate_ids_batch,
            nb::arg("refs"),
            nb::arg("use_gpu") = false
        )
        .def(
            "get_visual_candidate_ids_batch",
            &WorldBatchRuntime::get_visual_candidate_ids_batch,
            nb::arg("refs"),
            nb::arg("range_m") = 25000.0,
            nb::arg("use_gpu") = false
        )
        .def(
            "get_comm_candidate_ids_batch",
            &WorldBatchRuntime::get_comm_candidate_ids_batch,
            nb::arg("refs"),
            nb::arg("use_gpu") = false
        )
        .def(
            "extract_packed_flight_states_batch",
            &WorldBatchRuntime::extract_packed_flight_states_batch,
            nb::arg("refs")
        )
        .def(
            "apply_packed_flight_states_batch",
            &WorldBatchRuntime::apply_packed_flight_states_batch,
            nb::arg("refs"),
            nb::arg("states")
        )
        .def(
            "step_packed_flight_states_experiment_batch",
            &WorldBatchRuntime::step_packed_flight_states_experiment_batch,
            nb::arg("refs"),
            nb::arg("steps"),
            nb::arg("use_cuda_graph") = false,
            nb::arg("write_back") = false
        )
        .def(
            "step_exact_world_step_first_scope_chain_experiment_batch_packed",
            [](WorldBatchRuntime& self,
               const std::vector<WorldEntityRef>& refs,
               bool use_gpu,
               bool write_back) {
                const auto stepped = self.step_exact_world_step_first_scope_chain_experiment_batch(
                    refs,
                    use_gpu,
                    write_back
                );
                const auto packed = gpu::pack_exact_world_step_states_v1(stepped);
                return nb::bytes(packed.data(), packed.size());
            },
            nb::arg("refs"),
            nb::arg("use_gpu") = true,
            nb::arg("write_back") = false
        )
        .def(
            "prime_exact_world_step_first_scope_chain_cached_session",
            &WorldBatchRuntime::prime_exact_world_step_first_scope_chain_cached_session,
            nb::arg("refs")
        )
        .def(
            "set_pilot_actions_exact_world_step_first_scope_chain_cached_session",
            &WorldBatchRuntime::set_pilot_actions_exact_world_step_first_scope_chain_cached_session,
            nb::arg("assignments")
        )
        .def(
            "set_mission_commands_exact_world_step_first_scope_chain_cached_session",
            &WorldBatchRuntime::set_mission_commands_exact_world_step_first_scope_chain_cached_session,
            nb::arg("assignments")
        )
        .def(
            "step_exact_world_step_first_scope_chain_cached_session_packed",
            [](WorldBatchRuntime& self, bool use_gpu, bool write_back) {
                const auto stepped = self.step_exact_world_step_first_scope_chain_cached_session(
                    use_gpu,
                    write_back
                );
                const auto packed = gpu::pack_exact_world_step_states_v1(stepped);
                return nb::bytes(packed.data(), packed.size());
            },
            nb::arg("use_gpu") = true,
            nb::arg("write_back") = false
        )
        .def(
            "apply_exact_world_step_first_scope_chain_cached_session_to_world",
            &WorldBatchRuntime::apply_exact_world_step_first_scope_chain_cached_session_to_world
        )
        .def(
            "extract_exact_world_step_first_scope_chain_cached_session_packed",
            [](const WorldBatchRuntime& self) {
                const auto packed = gpu::pack_exact_world_step_states_v1(
                    self.extract_exact_world_step_first_scope_chain_cached_session()
                );
                return nb::bytes(packed.data(), packed.size());
            }
        )
        .def(
            "last_exact_world_step_first_scope_chain_cached_session_stats",
            &WorldBatchRuntime::last_exact_world_step_first_scope_chain_cached_session_stats,
            nb::rv_policy::reference_internal
        )
        .def(
            "upload_exact_world_step_first_scope_chain_experiment_batch",
            &WorldBatchRuntime::upload_exact_world_step_first_scope_chain_experiment_batch,
            nb::arg("refs")
        )
        .def(
            "replay_exact_world_step_first_scope_chain_experiment_device_sequence",
            &WorldBatchRuntime::replay_exact_world_step_first_scope_chain_experiment_device_sequence
        )
        .def(
            "download_exact_world_step_first_scope_chain_experiment_batch_packed",
            [](WorldBatchRuntime& self, bool write_back) {
                const auto stepped = self.download_exact_world_step_first_scope_chain_experiment_batch(write_back);
                const auto packed = gpu::pack_exact_world_step_states_v1(stepped);
                return nb::bytes(packed.data(), packed.size());
            },
            nb::arg("write_back") = false
        )
        .def(
            "extract_exact_world_step_states_v1_batch_packed",
            [](const WorldBatchRuntime& self, const std::vector<WorldEntityRef>& refs) {
                const auto packed = gpu::pack_exact_world_step_states_v1(
                    self.extract_exact_world_step_states_v1_batch(refs)
                );
                return nb::bytes(packed.data(), packed.size());
            },
            nb::arg("refs")
        )
        .def(
            "apply_exact_world_step_states_v1_batch_packed",
            [](WorldBatchRuntime& self, const std::vector<WorldEntityRef>& refs, const nb::bytes& packed) {
                auto states = gpu::unpack_exact_world_step_states_v1(
                    std::string_view(packed.c_str(), packed.size())
                );
                self.apply_exact_world_step_states_v1_batch(refs, states);
            },
            nb::arg("refs"),
            nb::arg("packed")
        )
        .def(
            "extract_exact_world_step_state_v1_apply_signatures_batch",
            [](const WorldBatchRuntime& self, const std::vector<WorldEntityRef>& refs) {
                return gpu::exact_world_step_state_v1_apply_signatures(
                    self.extract_exact_world_step_states_v1_batch(refs)
                );
            },
            nb::arg("refs")
        )
        .def(
            "extract_exact_world_step_state_v1_hidden_surfaces_batch",
            [](const WorldBatchRuntime& self, const std::vector<WorldEntityRef>& refs) {
                return exact_world_step_hidden_surface_list(
                    self.extract_exact_world_step_states_v1_batch(refs)
                );
            },
            nb::arg("refs")
        );
    
    nb::class_<UnitData>(m, "UnitData")
        .def_ro("id", &UnitData::id)
        .def_ro("side", &UnitData::side)
        .def_ro("type", &UnitData::type)
        .def_ro("x", &UnitData::x)
        .def_ro("y", &UnitData::y)
        .def_ro("z", &UnitData::z)
        .def_ro("heading", &UnitData::heading);

    nb::class_<Detection>(m, "Detection")
        .def(nb::init<>())
        .def_rw("target_id", &Detection::target_id)
        .def_rw("range", &Detection::range)
        .def_rw("bearing", &Detection::bearing)
        .def_rw("elevation", &Detection::elevation)
        .def_rw("closing_speed", &Detection::closing_speed)
        .def_rw("signal_strength", &Detection::signal_strength)
        .def_rw("timestamp", &Detection::timestamp);

    nb::class_<TrackData>(m, "TrackData")
        .def_ro("id", &TrackData::id)
        .def_ro("range", &TrackData::range)
        .def_ro("azimuth", &TrackData::azimuth)
        .def_ro("elevation", &TrackData::elevation)
        .def_ro("closing_speed", &TrackData::closing_speed)
        .def_ro("time_since_update", &TrackData::time_since_update)
        .def_ro("source", &TrackData::source)
        .def_ro("classification", &TrackData::classification);

    nb::class_<AgentObservation>(m, "AgentObservation")
        .def_ro("sim_time", &AgentObservation::sim_time)
        .def_ro("id", &AgentObservation::id)
        .def_ro("x", &AgentObservation::x)
        .def_ro("y", &AgentObservation::y)
        .def_ro("z", &AgentObservation::z)
        .def_ro("vx", &AgentObservation::vx)
        .def_ro("vy", &AgentObservation::vy)
        .def_ro("vz", &AgentObservation::vz)
        .def_ro("heading", &AgentObservation::heading)
        .def_ro("pitch", &AgentObservation::pitch)
        .def_ro("roll", &AgentObservation::roll)
        .def_ro("speed", &AgentObservation::speed)
        .def_ro("health", &AgentObservation::health)
        .def_ro("contacts", &AgentObservation::contacts)
        .def_ro("rwr_warnings", &AgentObservation::rwr_warnings)
        .def_ro("missiles_remaining", &AgentObservation::missiles_remaining)
        .def_ro("can_fire", &AgentObservation::can_fire)
        .def_ro("gear_state", &AgentObservation::gear_state)
        .def_ro("throttle", &AgentObservation::throttle)
        .def_ro("total_reward", &AgentObservation::total_reward);
}
