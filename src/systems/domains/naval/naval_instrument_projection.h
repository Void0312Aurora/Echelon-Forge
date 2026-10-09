#pragma once

#include <algorithm>
#include <cmath>
#include <numbers>
#include <flecs.h>
#include "components/basic/common.h"
#include "components/domains/naval/command/mission_command_naval.h"
#include "components/domains/naval/platform/submarine_platform.h"
#include "components/physics/forces.h"
#include "components/physics/instruments.h"
#include "components/systems/navigation.h"

// Attitude/vertical motion are simulation truth, as for aircraft instruments.
// Navigation uses the EGI reported solution when installed. Without EGI only
// velocity/track fall back to truth; GPS/position uncertainty remain unavailable.
// This projection owns no aero or EW fields and runs in UpdateInstruments.
inline void project_naval_instruments(flecs::entity entity, InstrumentState &inst,
                                      const Transform &transform, const Velocity &velocity) {
    inst.alt_baro_m = transform.z;
    inst.vvi_mps = velocity.vz;
    inst.heading_deg = Math::normalize_heading_deg(transform.heading);
    inst.pitch_deg = transform.pitch;
    inst.roll_deg = transform.roll;
    inst.p_deg_s = inst.q_deg_s = inst.r_deg_s = 0.0;
    if (const auto *rates = entity.get<AngularVelocity>()) {
        constexpr double rad_to_deg = 180.0 / std::numbers::pi_v<double>;
        inst.p_deg_s = rates->p * rad_to_deg;
        inst.q_deg_s = rates->q * rad_to_deg;
        inst.r_deg_s = rates->r * rad_to_deg;
    }
    InstrumentNavigationProjection nav;
    if (const auto *egi = entity.get<EGI>()) {
        nav = project_egi_to_instrument_navigation(*egi, inst.heading_deg);
    } else {
        nav.vn_mps = velocity.vy;
        nav.ve_mps = velocity.vx;
        nav.vd_mps = -velocity.vz;
        nav.ground_speed_mps = std::hypot(velocity.vx, velocity.vy);
        nav.ground_track_deg =
            Math::ground_track_deg_from_velocity(velocity.vx, velocity.vy, inst.heading_deg);
    }
    inst.lat_deg = nav.lat_deg;
    inst.lon_deg = nav.lon_deg;
    inst.vn_mps = nav.vn_mps;
    inst.ve_mps = nav.ve_mps;
    inst.vd_mps = nav.vd_mps;
    inst.ground_speed_mps = nav.ground_speed_mps;
    inst.ground_track_deg = nav.ground_track_deg;
    inst.gps_available = nav.gps_available;
    inst.position_uncertainty_m = nav.position_uncertainty_m;
    inst.cmd_heading_deg = inst.heading_deg;
    inst.cmd_speed_mps = inst.ground_speed_mps;
    inst.cmd_alt_m = transform.z;
    if (const auto *command = entity.get<NavalCommandIntent>(); command && command->active) {
        if (std::isfinite(command->cmd_heading_deg))
            inst.cmd_heading_deg = Math::normalize_heading_deg(command->cmd_heading_deg);
        if (std::isfinite(command->cmd_speed_mps)) inst.cmd_speed_mps = command->cmd_speed_mps;
        if (entity.has<SubmarinePlatform>() && std::isfinite(command->cmd_depth_m))
            inst.cmd_alt_m = -std::max(0.0, command->cmd_depth_m);
    }
}
