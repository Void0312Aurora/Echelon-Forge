#include "core/mission/runtime/execution_observation_runtime.h"

#include <algorithm>
#include <cmath>

namespace {

float sanitize_scalar(double value) {
    if (!std::isfinite(value)) {
        return 0.0f;
    }
    const double clipped = std::clamp(value, -1.0e6, 1.0e6);
    return static_cast<float>(clipped);
}

}  // namespace

ExecutionObservationRuntimeProducts compute_execution_observation_runtime(
    const InstrumentState& inst,
    const AgentObservation& truth,
    double ils_valid,
    double ils_loc,
    double ils_gs,
    double ils_dme,
    int max_contacts,
    int max_rwr
) {
    ExecutionObservationRuntimeProducts out{};
    out.valid = true;

    out.instrument_values = {
        sanitize_scalar(inst.ias_mps),
        sanitize_scalar(inst.mach),
        sanitize_scalar(inst.alt_baro_m),
        sanitize_scalar(inst.alt_radar_m),
        sanitize_scalar(inst.vvi_mps),
        sanitize_scalar(inst.aoa_deg),
        sanitize_scalar(inst.beta_deg),
        sanitize_scalar(inst.pitch_deg),
        sanitize_scalar(inst.roll_deg),
        sanitize_scalar(inst.heading_deg),
        sanitize_scalar(inst.g_load_normal),
        sanitize_scalar(inst.g_load_axial),
        sanitize_scalar(inst.p_deg_s),
        sanitize_scalar(inst.q_deg_s),
        sanitize_scalar(inst.r_deg_s),
        sanitize_scalar(inst.engine_rpm_pct),
        sanitize_scalar(inst.fuel_internal_kg + inst.fuel_external_kg),
        sanitize_scalar(inst.fuel_flow_kg_h),
        sanitize_scalar(inst.gear_pos),
        sanitize_scalar(inst.flaps_pos),
        sanitize_scalar(inst.speedbrake_pos),
        sanitize_scalar(inst.cmd_heading_deg),
        sanitize_scalar(inst.cmd_alt_m),
        sanitize_scalar(inst.cmd_speed_mps),
        sanitize_scalar(inst.lat_deg),
        sanitize_scalar(inst.lon_deg),
        sanitize_scalar(inst.vn_mps),
        sanitize_scalar(inst.ve_mps),
        sanitize_scalar(inst.vd_mps),
        sanitize_scalar(inst.ground_speed_mps),
        sanitize_scalar(inst.ground_track_deg),
        sanitize_scalar(inst.wind_speed_mps),
        sanitize_scalar(inst.wind_dir_deg),
        sanitize_scalar(inst.oat_c),
        sanitize_scalar(inst.gps_available ? 1.0 : 0.0),
        sanitize_scalar(inst.position_uncertainty_m),
        sanitize_scalar(inst.rwr_active ? 1.0 : 0.0),
        sanitize_scalar(inst.missiles_remaining),
        sanitize_scalar(ils_valid),
        sanitize_scalar(ils_loc),
        sanitize_scalar(ils_gs),
        sanitize_scalar(ils_dme),
    };

    const int contact_count = std::max(0, max_contacts);
    out.contact_values.assign(static_cast<size_t>(contact_count) * 5u, 0.0f);
    for (int idx = 0; idx < contact_count && idx < static_cast<int>(truth.contacts.size()); ++idx) {
        const TrackData& track = truth.contacts[static_cast<size_t>(idx)];
        const size_t base = static_cast<size_t>(idx) * 5u;
        out.contact_values[base + 0u] = sanitize_scalar(track.range);
        out.contact_values[base + 1u] = sanitize_scalar(track.azimuth);
        out.contact_values[base + 2u] = sanitize_scalar(track.elevation);
        out.contact_values[base + 3u] = sanitize_scalar(track.closing_speed);
        out.contact_values[base + 4u] = sanitize_scalar(track.time_since_update);
    }

    const int rwr_count = std::max(0, max_rwr);
    out.rwr_values.assign(static_cast<size_t>(rwr_count) * 4u, 0.0f);
    for (int idx = 0; idx < rwr_count && idx < static_cast<int>(truth.rwr_warnings.size()); ++idx) {
        const RWREvent& warning = truth.rwr_warnings[static_cast<size_t>(idx)];
        const size_t base = static_cast<size_t>(idx) * 4u;
        out.rwr_values[base + 0u] = sanitize_scalar(warning.bearing);
        out.rwr_values[base + 1u] = sanitize_scalar(warning.signal_strength);
        out.rwr_values[base + 2u] = sanitize_scalar(warning.is_lock ? 1.0 : 0.0);
        out.rwr_values[base + 3u] = sanitize_scalar(warning.is_launch ? 1.0 : 0.0);
    }

    return out;
}
