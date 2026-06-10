#pragma once

#include <cstdint>

struct PilotReportNaval {
    struct CommandAuthorityDirective {
        int warfare_role_code = 0;
        std::uint64_t officer_in_tactical_command = 0;

        bool operator==(const CommandAuthorityDirective&) const = default;
    };

    int warfare_role_code = 0;
    std::uint64_t officer_in_tactical_command = 0;
};

// Maintained naval-domain owner slice projected through PilotReport compatibility shells.
using PilotReportNavalOwnerSlice = PilotReportNaval;
inline constexpr bool kPilotReportNavalOwnedDomainSlice = true;

[[nodiscard]] inline PilotReportNaval::CommandAuthorityDirective
pilot_report_naval_command_authority(
    const PilotReportNavalOwnerSlice& naval
) noexcept {
    return {
        .warfare_role_code = naval.warfare_role_code,
        .officer_in_tactical_command = naval.officer_in_tactical_command,
    };
}
