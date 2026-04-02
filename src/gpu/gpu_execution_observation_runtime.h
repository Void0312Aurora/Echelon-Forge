#pragma once

#include <cstddef>
#include <vector>

#include "core/interfaces/observation.h"
#include "core/mission/mission_runtime.h"

namespace gpu {

constexpr int kExecutionObservationInstrumentCount = 42;
constexpr int kExecutionObservationContactWidth = 5;
constexpr int kExecutionObservationRwrWidth = 4;
constexpr int kExecutionObservationMissionBasicCount = 4;
constexpr int kExecutionObservationMissionNavV1Count = 11;
constexpr int kExecutionObservationMissionNavV2Count = 14;

struct ExecutionObservationBatchRequest {
    struct InstrumentPacked {
        double alt_baro_m = 0.0;
        double alt_radar_m = 0.0;
        double ias_mps = 0.0;
        double mach = 0.0;
        double vvi_mps = 0.0;
        double pitch_deg = 0.0;
        double roll_deg = 0.0;
        double heading_deg = 0.0;
        double aoa_deg = 0.0;
        double beta_deg = 0.0;
        double g_load_normal = 0.0;
        double g_load_axial = 0.0;
        double p_deg_s = 0.0;
        double q_deg_s = 0.0;
        double r_deg_s = 0.0;
        double engine_rpm_pct = 0.0;
        double fuel_flow_kg_h = 0.0;
        double fuel_internal_kg = 0.0;
        double fuel_external_kg = 0.0;
        float gear_pos = 0.0f;
        float flaps_pos = 0.0f;
        float speedbrake_pos = 0.0f;
        double oat_c = 0.0;
        double cmd_heading_deg = 0.0;
        double cmd_alt_m = 0.0;
        double cmd_speed_mps = 0.0;
        bool rwr_active = false;
        int missiles_remaining = 0;
        double lat_deg = 0.0;
        double lon_deg = 0.0;
        double vn_mps = 0.0;
        double ve_mps = 0.0;
        double vd_mps = 0.0;
        double ground_speed_mps = 0.0;
        double ground_track_deg = 0.0;
        double wind_speed_mps = 0.0;
        double wind_dir_deg = 0.0;
        bool gps_available = false;
        double position_uncertainty_m = 0.0;
    } inst{};
    struct MissionPacked {
        int mode_code = 0;
        double command_code = 0.0;
        double target_heading_deg = 0.0;
        double target_altitude_m = 0.0;
        double target_speed_mps = 0.0;
        bool has_route_guidance = false;
        int route_idx = 0;
        int route_count = 0;
        bool route_waypoint_flyover = false;
        double route_dist_m = 0.0;
        double route_reward_xtk_m = 0.0;
        double route_reward_dtg_m = 0.0;
        double route_direct_to_track_deg = 0.0;
        double route_reward_desired_track_deg = 0.0;
        double route_next_turn_deg = 0.0;
        double route_distance_to_turn_m = 0.0;
        double nav_own_altitude_m = 0.0;
        double nav_truth_heading_deg = 0.0;
        double nav_truth_speed_mps = 0.0;
        double nav_inst_heading_deg = 0.0;
        double nav_inst_ground_track_deg = 0.0;
        double nav_inst_ias_mps = 0.0;
        double nav_waypoint_altitude_m = 0.0;
        double nav_cdi_full_scale_m = 1500.0;
    } mission{};
    double ils_valid = 0.0;
    double ils_loc = 0.0;
    double ils_gs = 0.0;
    double ils_dme = 0.0;
    int contact_count = 0;
    int rwr_count = 0;
};

struct ExecutionObservationExperimentStats {
    bool used_cuda = false;
    double host_to_device_ms = 0.0;
    double kernel_ms = 0.0;
    double device_to_host_ms = 0.0;
    double total_ms = 0.0;
};

std::size_t execution_observation_mission_float_count(int mission_mode_code);
std::size_t execution_observation_output_float_count(int max_contacts, int max_rwr, int mission_mode_code);

ExecutionObservationExperimentStats last_execution_observation_stats();
const void* last_execution_observation_output_device_ptr();
std::size_t last_execution_observation_output_float_count();

std::vector<float> compute_execution_observation_reference_cpu_batch(
    const std::vector<ExecutionObservationBatchRequest>& requests,
    const std::vector<std::vector<TrackData>>& contacts_batch,
    const std::vector<std::vector<RWREvent>>& rwr_batch,
    int max_contacts,
    int max_rwr
);

std::vector<float> compute_execution_observation_experiment_batch(
    const std::vector<ExecutionObservationBatchRequest>& requests,
    const std::vector<std::vector<TrackData>>& contacts_batch,
    const std::vector<std::vector<RWREvent>>& rwr_batch,
    int max_contacts,
    int max_rwr
);

bool compute_execution_observation_experiment_batch_device_resident(
    const std::vector<ExecutionObservationBatchRequest>& requests,
    const std::vector<std::vector<TrackData>>& contacts_batch,
    const std::vector<std::vector<RWREvent>>& rwr_batch,
    int max_contacts,
    int max_rwr
);

}  // namespace gpu
