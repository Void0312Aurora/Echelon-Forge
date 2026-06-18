#pragma once

#include <cstdint>
#include <string_view>

enum class StructuralBreakupPhase : std::uint8_t {
    Intact = 0,
    PartialDetachment = 1,
    PartialBreakup = 2,
    FullBreakup = 3,
};

enum class StructuralBreakMode : std::uint32_t {
    None = 0,
    WingLoss = 1u << 0,
    TailLoss = 1u << 1,
    EngineDetach = 1u << 2,
    FuselageRupture = 1u << 3,
    MultiAxis = 1u << 4,
};

enum class StructuralBreakGroup : std::uint32_t {
    None = 0,
    WingLeft = 1u << 0,
    WingRight = 1u << 1,
    TailLeft = 1u << 2,
    TailRight = 1u << 3,
    VerticalTail = 1u << 4,
    EngineRight = 1u << 5,
    Fuselage = 1u << 6,
};

struct StructuralBreakupState {
    StructuralBreakupPhase breakup_state = StructuralBreakupPhase::Intact;
    std::uint32_t active_break_modes = 0;
    std::uint32_t active_structural_groups = 0;
    std::uint32_t detached_part_count = 0;
    bool airframe_breakup = false;
};

inline constexpr std::uint32_t structural_break_mode_mask(StructuralBreakMode mode) {
    return static_cast<std::uint32_t>(mode);
}

inline constexpr std::uint32_t structural_break_group_mask(StructuralBreakGroup group) {
    return static_cast<std::uint32_t>(group);
}

inline bool structural_breakup_has_mode(const StructuralBreakupState &state,
                                        StructuralBreakMode mode) {
    return (state.active_break_modes & structural_break_mode_mask(mode)) != 0u;
}

inline bool structural_breakup_has_group(const StructuralBreakupState &state,
                                         StructuralBreakGroup group) {
    return (state.active_structural_groups & structural_break_group_mask(group)) != 0u;
}

inline std::string_view structural_breakup_phase_name(StructuralBreakupPhase state) {
    switch (state) {
    case StructuralBreakupPhase::Intact:
        return "intact";
    case StructuralBreakupPhase::PartialDetachment:
        return "partial_detachment";
    case StructuralBreakupPhase::PartialBreakup:
        return "partial_breakup";
    case StructuralBreakupPhase::FullBreakup:
        return "full_breakup";
    }
    return "intact";
}
