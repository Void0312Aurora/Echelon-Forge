#pragma once

#include <cstdint>

struct PilotReportAir {
    std::uint64_t element_id = 0;
    int phase_id = 0;
    int formation_role_id = 0;
    double formation_error_m = 0.0;
    double bearing_error_deg = 0.0;
    double closure_mps = 0.0;
    double separation_m = 0.0;
};

// Maintained air-domain owner slice projected through PilotReport compatibility shells.
using PilotReportAirOwnerSlice = PilotReportAir;
inline constexpr bool kPilotReportAirOwnedDomainSlice = true;
