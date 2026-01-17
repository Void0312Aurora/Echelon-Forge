#pragma once

#include "components/basic/common.h"

enum class LinkType {
    Generic,
    VHF_Radio,       // LOS limited, medium range
    Link16,          // Omni, high range
    MADL_Directional // Short range, stealth
};

struct DataLink {
    bool active;
    int network_id; // e.g., 1 for Blue Team, 2 for Red Team
    LinkType type;
    double max_range_km;
};
