#pragma once

#include <cstdint>

struct LeaderIntentNaval {
    struct CommandAuthorityDirective {
        int warfare_role_code = 0;
        std::uint64_t officer_in_tactical_command = 0;

        bool operator==(const CommandAuthorityDirective&) const = default;
    };

    int warfare_role_code = 0;
    std::uint64_t officer_in_tactical_command = 0;
};

// Maintained naval-domain owner slice projected through LeaderIntent compatibility shells.
using LeaderIntentNavalOwnerSlice = LeaderIntentNaval;
inline constexpr bool kLeaderIntentNavalOwnedDomainSlice = true;

[[nodiscard]] inline LeaderIntentNaval::CommandAuthorityDirective
leader_intent_naval_command_authority(
    const LeaderIntentNavalOwnerSlice& naval
) noexcept {
    return {
        .warfare_role_code = naval.warfare_role_code,
        .officer_in_tactical_command = naval.officer_in_tactical_command,
    };
}
