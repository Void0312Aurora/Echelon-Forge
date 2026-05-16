#pragma once

#include <cstdint>

#include "components/tasking/naval/naval_tasking_enums.h"

struct TaskOrderNaval {
    int warfare_role_code = 0;
    std::uint64_t officer_in_tactical_command = 0;
    NavalStationType naval_station_type = NavalStationType::Unspecified;
};
