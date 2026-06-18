#pragma once

#include <flecs.h>

#include <algorithm>
#include <array>
#include <cstdint>
#include <initializer_list>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "components/basic/common.h"
#include "components/combat/common/damage_common.h"
#include "components/combat/structural_failure.h"
#include "core/interfaces/engagement_event_recorder.h"

namespace structural_failure {

inline bool is_structurally_damaging_mode(std::string_view mode) {
    return mode == "structural_weakening" || mode == "puncture" || mode == "cut" ||
           mode == "blast_deformation";
}

inline double structural_near_field_loss_weight(std::string_view mode) {
    if (mode == "cut") {
        return 1.40;
    }
    return 1.0;
}

inline double structural_near_field_mode_loss(std::string_view mode, double severity) {
    const double bounded_severity = std::clamp(severity, 0.0, 1.0);
    if (mode == "cut") {
        return 0.28 * bounded_severity;
    }
    if (mode == "blast_deformation") {
        return 0.18 * bounded_severity;
    }
    if (mode == "structural_weakening") {
        return 0.18 * bounded_severity;
    }
    if (mode == "puncture") {
        return 0.14 * bounded_severity;
    }
    return 0.0;
}

inline bool has_tg_p7_split_surface(const ComponentDamageState &component_damage) {
    static constexpr std::array<std::string_view, 8> kSplitReceivers = {
        "engine_core_afterburner_segment",        "engine_core_hot_section_segment",
        "engine_core_forward_compressor_segment", "wing_spar_center_left_inner_wing_segment",
        "wing_spar_center_left_root_segment",     "wing_spar_center_carrythrough_segment",
        "wing_spar_center_right_root_segment",    "wing_spar_center_right_inner_wing_segment",
    };

    return std::any_of(kSplitReceivers.begin(), kSplitReceivers.end(), [&](std::string_view name) {
        return component_damage.component_integrity.find(std::string(name)) !=
               component_damage.component_integrity.end();
    });
}

inline bool component_failed_at(const ComponentDamageState &component_damage, std::string_view name,
                                double threshold) {
    const std::string key{name};
    const auto integrity_it = component_damage.component_integrity.find(key);
    if (integrity_it == component_damage.component_integrity.end() ||
        integrity_it->second > threshold) {
        return false;
    }
    const auto mode_it = component_damage.component_primary_failure_mode.find(key);
    return mode_it != component_damage.component_primary_failure_mode.end() &&
           is_structurally_damaging_mode(mode_it->second);
}

inline double structural_component_near_field_loss(const ComponentDamageState &component_damage,
                                                   std::string_view name) {
    const std::string key{name};
    const auto integrity_it = component_damage.component_integrity.find(key);
    if (integrity_it == component_damage.component_integrity.end()) {
        return 0.0;
    }
    const auto mode_it = component_damage.component_primary_failure_mode.find(key);
    if (mode_it == component_damage.component_primary_failure_mode.end() ||
        !is_structurally_damaging_mode(mode_it->second)) {
        return 0.0;
    }
    double mode_loss = 0.0;
    if (const auto severity_by_component_it =
            component_damage.component_failure_mode_severity.find(key);
        severity_by_component_it != component_damage.component_failure_mode_severity.end()) {
        if (const auto severity_it = severity_by_component_it->second.find(mode_it->second);
            severity_it != severity_by_component_it->second.end()) {
            mode_loss = structural_near_field_mode_loss(mode_it->second, severity_it->second);
        }
    }
    return std::clamp(std::max(1.0 - integrity_it->second, mode_loss) *
                          structural_near_field_loss_weight(mode_it->second),
                      0.0, 1.0);
}

inline bool cumulative_structural_loss_at(const ComponentDamageState &component_damage,
                                          std::initializer_list<std::string_view> names,
                                          double cumulative_threshold,
                                          std::uint32_t minimum_component_count,
                                          double minimum_component_loss) {
    double cumulative_loss = 0.0;
    std::uint32_t damaged_component_count = 0;
    for (const std::string_view name : names) {
        const double loss = structural_component_near_field_loss(component_damage, name);
        cumulative_loss += loss;
        if (loss >= minimum_component_loss) {
            ++damaged_component_count;
        }
    }
    return damaged_component_count >= minimum_component_count &&
           cumulative_loss >= cumulative_threshold;
}

inline std::uint32_t count_bits(std::uint32_t mask) {
    std::uint32_t count = 0;
    while (mask != 0u) {
        count += mask & 1u;
        mask >>= 1u;
    }
    return count;
}

inline void add_group_if(std::uint32_t &groups, bool condition, StructuralBreakGroup group) {
    if (condition) {
        groups |= structural_break_group_mask(group);
    }
}

inline std::uint32_t modes_from_groups(std::uint32_t groups) {
    std::uint32_t modes = 0;
    const std::uint32_t wing_groups = structural_break_group_mask(StructuralBreakGroup::WingLeft) |
                                      structural_break_group_mask(StructuralBreakGroup::WingRight);
    const std::uint32_t tail_groups =
        structural_break_group_mask(StructuralBreakGroup::TailLeft) |
        structural_break_group_mask(StructuralBreakGroup::TailRight) |
        structural_break_group_mask(StructuralBreakGroup::VerticalTail);

    if ((groups & wing_groups) != 0u) {
        modes |= structural_break_mode_mask(StructuralBreakMode::WingLoss);
    }
    if ((groups & tail_groups) != 0u) {
        modes |= structural_break_mode_mask(StructuralBreakMode::TailLoss);
    }
    if ((groups & structural_break_group_mask(StructuralBreakGroup::EngineRight)) != 0u) {
        modes |= structural_break_mode_mask(StructuralBreakMode::EngineDetach);
    }
    if ((groups & structural_break_group_mask(StructuralBreakGroup::Fuselage)) != 0u) {
        modes |= structural_break_mode_mask(StructuralBreakMode::FuselageRupture);
    }
    return modes;
}

inline StructuralBreakupPhase phase_from_family_count(std::uint32_t family_count) {
    if (family_count >= 3u) {
        return StructuralBreakupPhase::FullBreakup;
    }
    if (family_count == 2u) {
        return StructuralBreakupPhase::PartialBreakup;
    }
    if (family_count == 1u) {
        return StructuralBreakupPhase::PartialDetachment;
    }
    return StructuralBreakupPhase::Intact;
}

inline std::string structural_break_mode_name(StructuralBreakMode mode) {
    switch (mode) {
    case StructuralBreakMode::WingLoss:
        return "wing_loss";
    case StructuralBreakMode::TailLoss:
        return "tail_loss";
    case StructuralBreakMode::EngineDetach:
        return "engine_detach";
    case StructuralBreakMode::FuselageRupture:
        return "fuselage_rupture";
    case StructuralBreakMode::MultiAxis:
        return "multi_axis";
    case StructuralBreakMode::None:
        break;
    }
    return "none";
}

inline StructuralBreakMode break_mode_for_group(StructuralBreakGroup group) {
    switch (group) {
    case StructuralBreakGroup::WingLeft:
    case StructuralBreakGroup::WingRight:
        return StructuralBreakMode::WingLoss;
    case StructuralBreakGroup::TailLeft:
    case StructuralBreakGroup::TailRight:
    case StructuralBreakGroup::VerticalTail:
        return StructuralBreakMode::TailLoss;
    case StructuralBreakGroup::EngineRight:
        return StructuralBreakMode::EngineDetach;
    case StructuralBreakGroup::Fuselage:
        return StructuralBreakMode::FuselageRupture;
    case StructuralBreakGroup::None:
        break;
    }
    return StructuralBreakMode::None;
}

inline std::string detached_part_ref_for_group(StructuralBreakGroup group) {
    switch (group) {
    case StructuralBreakGroup::WingLeft:
        return "left_wing";
    case StructuralBreakGroup::WingRight:
        return "right_wing";
    case StructuralBreakGroup::TailLeft:
        return "left_stabilator";
    case StructuralBreakGroup::TailRight:
        return "right_stabilator";
    case StructuralBreakGroup::VerticalTail:
        return "vertical_stabilizer";
    case StructuralBreakGroup::EngineRight:
        return "engine_core";
    case StructuralBreakGroup::Fuselage:
        return "center_fuselage";
    case StructuralBreakGroup::None:
        break;
    }
    return "";
}

inline std::vector<std::string> component_names_for_group(StructuralBreakGroup group) {
    switch (group) {
    case StructuralBreakGroup::WingLeft:
        return {"wing_spar_center",
                "wing_spar_center_left_inner_wing_segment",
                "wing_spar_center_left_root_segment",
                "left_aileron_actuator",
                "left_leading_edge_flap_actuator",
                "left_wing_fuel_cell"};
    case StructuralBreakGroup::WingRight:
        return {"wing_spar_center",
                "wing_spar_center_right_root_segment",
                "wing_spar_center_right_inner_wing_segment",
                "right_aileron_actuator",
                "right_leading_edge_flap_actuator",
                "right_wing_fuel_cell"};
    case StructuralBreakGroup::TailLeft:
        return {"left_horizontal_tail_actuator_or_surface_component"};
    case StructuralBreakGroup::TailRight:
        return {"right_horizontal_tail_actuator_or_surface_component"};
    case StructuralBreakGroup::VerticalTail:
        return {"rudder_actuator"};
    case StructuralBreakGroup::EngineRight:
        return {"engine_core", "engine_core_afterburner_segment", "engine_core_hot_section_segment",
                "engine_core_forward_compressor_segment", "afterburner_nozzle"};
    case StructuralBreakGroup::Fuselage:
        return {"center_fuselage_fuel_cell", "dedicated_intake_lip_or_duct_component",
                "wing_spar_center_carrythrough_segment"};
    case StructuralBreakGroup::None:
        break;
    }
    return {};
}

inline StructuralBreakupState
evaluate_structural_breakup_state(const ComponentDamageState &component_damage,
                                  const StructuralBreakupState &prior = StructuralBreakupState{}) {
    const bool tg_p7 = has_tg_p7_split_surface(component_damage);
    std::uint32_t newly_failed_groups = 0;

    if (tg_p7) {
        constexpr double kWingNearFieldCumulativeLossThreshold = 0.20;
        constexpr double kWingNearFieldComponentLossThreshold = 0.05;
        constexpr std::uint32_t kWingNearFieldMinimumComponentCount = 2;
        const bool left_wing_primary =
            component_failed_at(component_damage, "wing_spar_center_left_inner_wing_segment",
                                0.25) ||
            component_failed_at(component_damage, "wing_spar_center_left_root_segment", 0.25);
        const std::uint32_t left_wing_contributors =
            (component_failed_at(component_damage, "left_aileron_actuator", 0.25) ? 1u : 0u) +
            (component_failed_at(component_damage, "left_leading_edge_flap_actuator", 0.25) ? 1u
                                                                                            : 0u) +
            (component_failed_at(component_damage, "left_wing_fuel_cell", 0.25) ? 1u : 0u);
        const bool left_wing_near_field_loss = cumulative_structural_loss_at(
            component_damage,
            {"wing_spar_center_left_inner_wing_segment", "wing_spar_center_left_root_segment",
             "left_aileron_actuator", "left_leading_edge_flap_actuator", "left_wing_fuel_cell"},
            kWingNearFieldCumulativeLossThreshold, kWingNearFieldMinimumComponentCount,
            kWingNearFieldComponentLossThreshold);
        add_group_if(newly_failed_groups,
                     left_wing_primary || left_wing_contributors >= 2u || left_wing_near_field_loss,
                     StructuralBreakGroup::WingLeft);

        const bool right_wing_primary =
            component_failed_at(component_damage, "wing_spar_center_right_root_segment", 0.25) ||
            component_failed_at(component_damage, "wing_spar_center_right_inner_wing_segment",
                                0.25);
        const std::uint32_t right_wing_contributors =
            (component_failed_at(component_damage, "right_aileron_actuator", 0.25) ? 1u : 0u) +
            (component_failed_at(component_damage, "right_leading_edge_flap_actuator", 0.25) ? 1u
                                                                                             : 0u) +
            (component_failed_at(component_damage, "right_wing_fuel_cell", 0.25) ? 1u : 0u);
        const bool right_wing_near_field_loss = cumulative_structural_loss_at(
            component_damage,
            {"wing_spar_center_right_root_segment", "wing_spar_center_right_inner_wing_segment",
             "right_aileron_actuator", "right_leading_edge_flap_actuator", "right_wing_fuel_cell"},
            kWingNearFieldCumulativeLossThreshold, kWingNearFieldMinimumComponentCount,
            kWingNearFieldComponentLossThreshold);
        add_group_if(newly_failed_groups,
                     right_wing_primary || right_wing_contributors >= 2u ||
                         right_wing_near_field_loss,
                     StructuralBreakGroup::WingRight);

        const std::uint32_t failed_engine_segments =
            (component_failed_at(component_damage, "engine_core_afterburner_segment", 0.15) ? 1u
                                                                                            : 0u) +
            (component_failed_at(component_damage, "engine_core_hot_section_segment", 0.15) ? 1u
                                                                                            : 0u) +
            (component_failed_at(component_damage, "engine_core_forward_compressor_segment", 0.15)
                 ? 1u
                 : 0u);
        const bool engine_segment_co_condition =
            component_failed_at(component_damage, "engine_core_afterburner_segment", 0.40) ||
            component_failed_at(component_damage, "engine_core_hot_section_segment", 0.40) ||
            component_failed_at(component_damage, "engine_core_forward_compressor_segment", 0.40);
        const bool afterburner_co_failure =
            component_failed_at(component_damage, "afterburner_nozzle", 0.25) &&
            engine_segment_co_condition;
        add_group_if(newly_failed_groups, failed_engine_segments >= 2u || afterburner_co_failure,
                     StructuralBreakGroup::EngineRight);

        add_group_if(
            newly_failed_groups,
            component_failed_at(component_damage, "wing_spar_center_carrythrough_segment", 0.20),
            StructuralBreakGroup::Fuselage);
    } else {
        constexpr double kWingNearFieldCumulativeLossThreshold = 0.20;
        constexpr double kWingNearFieldComponentLossThreshold = 0.05;
        constexpr std::uint32_t kWingNearFieldMinimumComponentCount = 2;
        const bool shared_spar_failed =
            component_failed_at(component_damage, "wing_spar_center", 0.25);
        const std::uint32_t left_wing_contributors =
            (component_failed_at(component_damage, "left_aileron_actuator", 0.25) ? 1u : 0u) +
            (component_failed_at(component_damage, "left_leading_edge_flap_actuator", 0.25) ? 1u
                                                                                            : 0u) +
            (component_failed_at(component_damage, "left_wing_fuel_cell", 0.25) ? 1u : 0u);
        const std::uint32_t right_wing_contributors =
            (component_failed_at(component_damage, "right_aileron_actuator", 0.25) ? 1u : 0u) +
            (component_failed_at(component_damage, "right_leading_edge_flap_actuator", 0.25) ? 1u
                                                                                             : 0u) +
            (component_failed_at(component_damage, "right_wing_fuel_cell", 0.25) ? 1u : 0u);
        const bool left_wing_near_field_loss = cumulative_structural_loss_at(
            component_damage,
            {"wing_spar_center", "left_aileron_actuator", "left_leading_edge_flap_actuator",
             "left_wing_fuel_cell"},
            kWingNearFieldCumulativeLossThreshold, kWingNearFieldMinimumComponentCount,
            kWingNearFieldComponentLossThreshold);
        const bool right_wing_near_field_loss = cumulative_structural_loss_at(
            component_damage,
            {"wing_spar_center", "right_aileron_actuator", "right_leading_edge_flap_actuator",
             "right_wing_fuel_cell"},
            kWingNearFieldCumulativeLossThreshold, kWingNearFieldMinimumComponentCount,
            kWingNearFieldComponentLossThreshold);
        add_group_if(newly_failed_groups,
                     shared_spar_failed || left_wing_contributors >= 2u ||
                         left_wing_near_field_loss,
                     StructuralBreakGroup::WingLeft);
        add_group_if(newly_failed_groups,
                     shared_spar_failed || right_wing_contributors >= 2u ||
                         right_wing_near_field_loss,
                     StructuralBreakGroup::WingRight);

        const bool engine_core_failed = component_failed_at(component_damage, "engine_core", 0.15);
        const bool afterburner_co_failure =
            component_failed_at(component_damage, "afterburner_nozzle", 0.25) &&
            component_failed_at(component_damage, "engine_core", 0.40);
        add_group_if(newly_failed_groups, engine_core_failed || afterburner_co_failure,
                     StructuralBreakGroup::EngineRight);
    }

    add_group_if(newly_failed_groups,
                 component_failed_at(component_damage,
                                     "left_horizontal_tail_actuator_or_surface_component", 0.20),
                 StructuralBreakGroup::TailLeft);
    add_group_if(newly_failed_groups,
                 component_failed_at(component_damage,
                                     "right_horizontal_tail_actuator_or_surface_component", 0.20),
                 StructuralBreakGroup::TailRight);
    add_group_if(newly_failed_groups,
                 component_failed_at(component_damage, "rudder_actuator", 0.25),
                 StructuralBreakGroup::VerticalTail);
    add_group_if(
        newly_failed_groups,
        component_failed_at(component_damage, "center_fuselage_fuel_cell", 0.30) ||
            component_failed_at(component_damage, "dedicated_intake_lip_or_duct_component", 0.20),
        StructuralBreakGroup::Fuselage);

    StructuralBreakupState next = prior;
    next.active_structural_groups |= newly_failed_groups;

    std::uint32_t modes = modes_from_groups(next.active_structural_groups);
    const std::uint32_t family_count = count_bits(modes);
    if (family_count >= 3u) {
        modes |= structural_break_mode_mask(StructuralBreakMode::MultiAxis);
    }
    next.active_break_modes |= modes;
    next.breakup_state = std::max(next.breakup_state, phase_from_family_count(family_count));
    next.airframe_breakup = next.breakup_state == StructuralBreakupPhase::FullBreakup;
    next.detached_part_count = count_bits(next.active_structural_groups);
    return next;
}

inline std::uint64_t
record_structural_breakup_event(IEngagementEventRecorder &recorder, std::uint64_t target_id,
                                const StructuralBreakupState &next, StructuralBreakMode mode,
                                const std::string &detached_part_ref,
                                std::vector<std::string> component_names, double source_time_s) {
    StructuralBreakupEvent event{};
    event.header.source_time_s = source_time_s;
    event.header.confidence = 1.0;
    event.breakup_state = std::string(structural_breakup_phase_name(next.breakup_state));
    event.break_mode = structural_break_mode_name(mode);
    event.detached_part_ref = detached_part_ref;
    event.detached_part_count = next.detached_part_count;
    event.airframe_breakup = next.airframe_breakup;
    return recorder.record_structural_breakup_event({
        .target_id = target_id,
        .contributing_component_names = std::move(component_names),
        .event = std::move(event),
    });
}

inline std::uint64_t record_structural_transition_events(IEngagementEventRecorder &recorder,
                                                         std::uint64_t target_id,
                                                         const StructuralBreakupState &prior,
                                                         const StructuralBreakupState &next,
                                                         double source_time_s) {
    const std::uint32_t new_groups =
        next.active_structural_groups & ~prior.active_structural_groups;
    static constexpr std::array<StructuralBreakGroup, 7> kGroups = {
        StructuralBreakGroup::WingLeft,     StructuralBreakGroup::WingRight,
        StructuralBreakGroup::TailLeft,     StructuralBreakGroup::TailRight,
        StructuralBreakGroup::VerticalTail, StructuralBreakGroup::EngineRight,
        StructuralBreakGroup::Fuselage,
    };

    std::uint64_t last_event_id = 0;
    for (const StructuralBreakGroup group : kGroups) {
        if ((new_groups & structural_break_group_mask(group)) == 0u) {
            continue;
        }
        if (const std::uint64_t event_id = record_structural_breakup_event(
                recorder, target_id, next, break_mode_for_group(group),
                detached_part_ref_for_group(group), component_names_for_group(group),
                source_time_s);
            event_id != 0) {
            last_event_id = event_id;
        }
    }

    const bool multi_axis_new = structural_breakup_has_mode(next, StructuralBreakMode::MultiAxis) &&
                                !structural_breakup_has_mode(prior, StructuralBreakMode::MultiAxis);
    if (multi_axis_new) {
        if (const std::uint64_t event_id = record_structural_breakup_event(
                recorder, target_id, next, StructuralBreakMode::MultiAxis, "multi_axis", {},
                source_time_s);
            event_id != 0) {
            last_event_id = event_id;
        }
    }
    return last_event_id;
}

} // namespace structural_failure

inline void register_structural_failure_system(flecs::world &ecs) {
    ecs.system<const ComponentDamageState, const KeyEntity>("StructuralFailureUpdate")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter &it) {
            while (it.next()) {
                auto component_damage = it.field<const ComponentDamageState>(0);
                auto key = it.field<const KeyEntity>(1);
                const EngagementEventRecorderRef *recorder_ref =
                    it.world().get<EngagementEventRecorderRef>();
                const ecs_world_info_t *world_info = ecs_get_world_info(it.world().c_ptr());
                const double current_time =
                    world_info ? static_cast<double>(world_info->world_time_total) : 0.0;
                for (auto i : it) {
                    if (key[i].type != UnitType::Aircraft) {
                        continue;
                    }
                    flecs::entity entity = it.entity(i);
                    StructuralBreakupState prior{};
                    if (const StructuralBreakupState *existing =
                            entity.get<StructuralBreakupState>()) {
                        prior = *existing;
                    }
                    StructuralBreakupState next =
                        structural_failure::evaluate_structural_breakup_state(component_damage[i],
                                                                              prior);
                    if (recorder_ref && recorder_ref->recorder) {
                        const std::uint64_t last_event_id =
                            structural_failure::record_structural_transition_events(
                                *recorder_ref->recorder, static_cast<std::uint64_t>(entity.id()),
                                prior, next, current_time);
                        if (last_event_id != 0) {
                            next.last_breakup_event_id = last_event_id;
                        }
                    }
                    entity.set<StructuralBreakupState>(next);
                }
            }
        });
}
