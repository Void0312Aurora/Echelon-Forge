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
    int max_reports_per_update;
    int max_messages_per_update;
    int reports_sent_last_update = 0;
    int messages_sent_last_update = 0;
    int reports_dropped_last_update = 0;
    int messages_dropped_last_update = 0;
    std::uint64_t reports_sent_total = 0;
    std::uint64_t messages_sent_total = 0;
    std::uint64_t reports_dropped_total = 0;
    std::uint64_t messages_dropped_total = 0;
};
