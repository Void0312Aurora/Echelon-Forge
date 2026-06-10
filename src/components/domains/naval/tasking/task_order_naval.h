#pragma once

#include <cstdint>

#include "components/domains/naval/tasking/naval_tasking_enums.h"

struct TaskOrderNaval {
    struct CommandAuthorityDirective {
        int warfare_role_code = 0;
        std::uint64_t officer_in_tactical_command = 0;

        bool operator==(const CommandAuthorityDirective &) const = default;
    };

    int warfare_role_code = 0;
    std::uint64_t officer_in_tactical_command = 0;
    NavalStationType naval_station_type = NavalStationType::Unspecified;
};

// Maintained naval-domain owner slice projected through TaskOrder compatibility shells.
using TaskOrderNavalOwnerSlice = TaskOrderNaval;
inline constexpr bool kTaskOrderNavalOwnedDomainSlice = true;

[[nodiscard]] inline TaskOrderNaval::CommandAuthorityDirective
task_order_naval_command_authority(const TaskOrderNavalOwnerSlice &naval) noexcept {
    return {
        .warfare_role_code = naval.warfare_role_code,
        .officer_in_tactical_command = naval.officer_in_tactical_command,
    };
}
