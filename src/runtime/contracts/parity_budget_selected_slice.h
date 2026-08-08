#pragma once

#include <algorithm>
#include <cmath>

#include "runtime/contracts/cuda_resident_selected_slice_contract.h"
#include "runtime/contracts/parity_budget_types.h"

namespace runtime::parity {

inline const std::vector<std::string> &resident_candidate_sync_barrier_contract() {
    static const std::vector<std::string> barriers = {
        "input_injection", "stage_publish", "partial_sync_commit", "window_commit", "export"};
    return barriers;
}

inline const std::vector<ParityBudgetBarrierRule> &resident_candidate_barrier_contract() {
    static const std::vector<ParityBudgetBarrierRule> rules = {
        ParityBudgetBarrierRule{
            .barrier_id = "input_injection",
            .candidate_rule =
                "canonical setup and selected pilot-flight-control deltas become visible to the "
                "admitted backend window",
            .visible_shards = {"identity", "pilot_flight_controls"},
            .comparison_eligible = true,
        },
        ParityBudgetBarrierRule{
            .barrier_id = "stage_publish",
            .candidate_rule =
                "backend-local diagnostic checkpoint; never sufficient for maintained parity or "
                "host truth",
            .visible_shards = {},
        },
        ParityBudgetBarrierRule{
            .barrier_id = "partial_sync_commit",
            .candidate_rule = "disabled for the selected resident-state slice; no partial "
                              "reconstructed shard and no "
                              "partial host truth are declared",
            .visible_shards = {},
            .enabled = false,
        },
        ParityBudgetBarrierRule{
            .barrier_id = "window_commit",
            .candidate_rule =
                "identity, clock, snapshot, kinematics, dynamics, and episode shards receive a "
                "committed backend snapshot and shard versions",
            .visible_shards = {"identity", "clock", "snapshot", "kinematics", "dynamics",
                               "episode"},
            .comparison_eligible = true,
        },
        ParityBudgetBarrierRule{
            .barrier_id = "export",
            .candidate_rule =
                "canonical host snapshot or lifetime-scoped device output becomes consumable with "
                "snapshot, provenance, and barrier metadata",
            .visible_shards = {"identity", "clock", "snapshot", "kinematics", "dynamics",
                               "instrument", "observation", "reward", "termination", "events",
                               "export_envelope"},
            .comparison_eligible = true,
            .host_truth_available = true,
        },
    };
    return rules;
}

inline const std::vector<ParityBudgetSelectedFieldFamily> &
resident_candidate_selected_slice_field_contract() {
    using enum ParityBudgetValueKind;
    static const std::vector<ParityBudgetSelectedFieldFamily> fields = {
        ParityBudgetSelectedFieldFamily{
            .field_family = "input_identity",
            .selected_fields =
                {
                    current_selected_field("pilot_action.world_index", "WorldPilotActionAssignment",
                                           unsigned_integer, "identity"),
                    current_selected_field("pilot_action.entity_id", "WorldPilotActionAssignment",
                                           unsigned_integer, "identity"),
                    current_selected_field("pilot_action.action.active", "PilotAction", boolean,
                                           "pilot_flight_controls"),
                },
            .comparator = std::string(kParityComparatorExact),
            .comparison_barriers = {"input_injection"},
        },
        ParityBudgetSelectedFieldFamily{
            .field_family = "pilot_flight_controls",
            .selected_fields =
                {
                    current_selected_field("pilot_action.action.stick_pitch", "PilotAction",
                                           float64, "pilot_flight_controls"),
                    current_selected_field("pilot_action.action.stick_roll", "PilotAction", float64,
                                           "pilot_flight_controls"),
                    current_selected_field("pilot_action.action.rudder", "PilotAction", float64,
                                           "pilot_flight_controls"),
                    current_selected_field("pilot_action.action.throttle", "PilotAction", float64,
                                           "pilot_flight_controls"),
                    current_selected_field("pilot_action.action.gear_handle", "PilotAction",
                                           float32, "pilot_flight_controls"),
                    current_selected_field("pilot_action.action.flaps", "PilotAction", float32,
                                           "pilot_flight_controls"),
                    current_selected_field("pilot_action.action.speedbrake", "PilotAction", float32,
                                           "pilot_flight_controls"),
                    current_selected_field("pilot_action.action.brake", "PilotAction", float64,
                                           "pilot_flight_controls"),
                    current_selected_field("pilot_action.action.brake_left", "PilotAction", boolean,
                                           "pilot_flight_controls"),
                    current_selected_field("pilot_action.action.brake_right", "PilotAction",
                                           boolean, "pilot_flight_controls"),
                },
            .comparator = std::string(kParityComparatorExact),
            .comparison_barriers = {"input_injection"},
        },
        ParityBudgetSelectedFieldFamily{
            .field_family = "world_identity_clock_and_versions",
            .selected_fields =
                {
                    current_selected_field("entity_ref.world_index", "WorldEntityRef",
                                           unsigned_integer, "identity"),
                    current_selected_field("entity_ref.entity_id", "WorldEntityRef",
                                           unsigned_integer, "identity"),
                    future_selected_field("clock.tick", "DeviceClockContract", unsigned_integer,
                                          "clock"),
                    future_selected_field("clock.simulation_time_s", "DeviceClockContract", float64,
                                          "clock"),
                    future_selected_field("snapshot.world_id", "SnapshotIdentityContract",
                                          unsigned_integer, "snapshot"),
                    future_selected_field("snapshot.global_version", "SnapshotIdentityContract",
                                          unsigned_integer, "snapshot"),
                    future_selected_field("snapshot.barrier_id", "SnapshotIdentityContract", string,
                                          "snapshot"),
                    future_selected_field("snapshot.barrier_sequence", "SnapshotIdentityContract",
                                          unsigned_integer, "snapshot"),
                    future_selected_field("snapshot.shard_versions", "SnapshotIdentityContract",
                                          structured, "snapshot"),
                    future_selected_field("snapshot.lineage", "SnapshotIdentityContract",
                                          structured, "snapshot"),
                },
            .comparator = std::string(kParityComparatorExact),
            .comparison_barriers = {"window_commit", "export"},
        },
        ParityBudgetSelectedFieldFamily{
            .field_family = "airframe_kinematics",
            .selected_fields =
                {
                    current_selected_field("kinematics.x", "WorldEntityKinematics", float64,
                                           "kinematics"),
                    current_selected_field("kinematics.y", "WorldEntityKinematics", float64,
                                           "kinematics"),
                    current_selected_field("kinematics.z", "WorldEntityKinematics", float64,
                                           "kinematics"),
                    current_selected_field("kinematics.vx", "WorldEntityKinematics", float64,
                                           "kinematics"),
                    current_selected_field("kinematics.vy", "WorldEntityKinematics", float64,
                                           "kinematics"),
                    current_selected_field("kinematics.vz", "WorldEntityKinematics", float64,
                                           "kinematics"),
                    current_selected_field("kinematics.heading", "WorldEntityKinematics", float64,
                                           "kinematics"),
                    current_selected_field("kinematics.pitch", "WorldEntityKinematics", float64,
                                           "kinematics"),
                    current_selected_field("kinematics.roll", "WorldEntityKinematics", float64,
                                           "kinematics"),
                },
            .comparator = std::string(kParityComparatorAbsoluteOrRelative),
            .absolute_tolerance = 1.0e-9,
            .relative_tolerance = 1.0e-12,
            .comparison_barriers = {"window_commit", "export"},
        },
        ParityBudgetSelectedFieldFamily{
            .field_family = "air_execution_instruments",
            .selected_fields =
                {
                    current_selected_field("instrument.alt_baro_m", "InstrumentState", float64,
                                           "instrument"),
                    current_selected_field("instrument.alt_radar_m", "InstrumentState", float64,
                                           "instrument"),
                    current_selected_field("instrument.ias_mps", "InstrumentState", float64,
                                           "instrument"),
                    current_selected_field("instrument.mach", "InstrumentState", float64,
                                           "instrument"),
                    current_selected_field("instrument.vvi_mps", "InstrumentState", float64,
                                           "instrument"),
                    current_selected_field("instrument.pitch_deg", "InstrumentState", float64,
                                           "instrument"),
                    current_selected_field("instrument.roll_deg", "InstrumentState", float64,
                                           "instrument"),
                    current_selected_field("instrument.heading_deg", "InstrumentState", float64,
                                           "instrument"),
                    current_selected_field("instrument.aoa_deg", "InstrumentState", float64,
                                           "instrument"),
                    current_selected_field("instrument.beta_deg", "InstrumentState", float64,
                                           "instrument"),
                    current_selected_field("instrument.g_load_normal", "InstrumentState", float64,
                                           "instrument"),
                    current_selected_field("instrument.g_load_axial", "InstrumentState", float64,
                                           "instrument"),
                    current_selected_field("instrument.p_deg_s", "InstrumentState", float64,
                                           "instrument"),
                    current_selected_field("instrument.q_deg_s", "InstrumentState", float64,
                                           "instrument"),
                    current_selected_field("instrument.r_deg_s", "InstrumentState", float64,
                                           "instrument"),
                    current_selected_field("instrument.engine_rpm_pct", "InstrumentState", float64,
                                           "instrument"),
                    current_selected_field("instrument.fuel_flow_kg_h", "InstrumentState", float64,
                                           "instrument"),
                    current_selected_field("instrument.throttle_pos", "InstrumentState", float64,
                                           "instrument"),
                    current_selected_field("instrument.fuel_internal_kg", "InstrumentState",
                                           float64, "instrument"),
                    current_selected_field("instrument.fuel_external_kg", "InstrumentState",
                                           float64, "instrument"),
                    current_selected_field("instrument.gear_pos", "InstrumentState", float32,
                                           "instrument"),
                    current_selected_field("instrument.flaps_pos", "InstrumentState", float32,
                                           "instrument"),
                    current_selected_field("instrument.speedbrake_pos", "InstrumentState", float32,
                                           "instrument"),
                },
            .comparator = std::string(kParityComparatorAbsoluteOrRelative),
            .absolute_tolerance = 1.0e-8,
            .relative_tolerance = 1.0e-10,
            .comparison_barriers = {"export"},
        },
        ParityBudgetSelectedFieldFamily{
            .field_family = "agent_observation_identity",
            .selected_fields =
                {
                    current_selected_field("observation.id", "AgentObservation", unsigned_integer,
                                           "observation"),
                },
            .comparator = std::string(kParityComparatorExact),
            .comparison_barriers = {"export"},
        },
        ParityBudgetSelectedFieldFamily{
            .field_family = "agent_observation_numeric",
            .selected_fields =
                {
                    current_selected_field("observation.sim_time", "AgentObservation", float64,
                                           "observation"),
                    current_selected_field("observation.x", "AgentObservation", float64,
                                           "observation"),
                    current_selected_field("observation.y", "AgentObservation", float64,
                                           "observation"),
                    current_selected_field("observation.z", "AgentObservation", float64,
                                           "observation"),
                    current_selected_field("observation.vx", "AgentObservation", float64,
                                           "observation"),
                    current_selected_field("observation.vy", "AgentObservation", float64,
                                           "observation"),
                    current_selected_field("observation.vz", "AgentObservation", float64,
                                           "observation"),
                    current_selected_field("observation.heading", "AgentObservation", float64,
                                           "observation"),
                    current_selected_field("observation.pitch", "AgentObservation", float64,
                                           "observation"),
                    current_selected_field("observation.roll", "AgentObservation", float64,
                                           "observation"),
                    current_selected_field("observation.speed", "AgentObservation", float64,
                                           "observation"),
                    current_selected_field("observation.health", "AgentObservation", float64,
                                           "observation"),
                    current_selected_field("observation.gear_state", "AgentObservation", float64,
                                           "observation"),
                    current_selected_field("observation.throttle", "AgentObservation", float64,
                                           "observation"),
                    current_selected_field("observation.total_reward", "AgentObservation", float64,
                                           "observation"),
                },
            .comparator = std::string(kParityComparatorAbsoluteOrRelative),
            .absolute_tolerance = 1.0e-8,
            .relative_tolerance = 1.0e-10,
            .comparison_barriers = {"export"},
        },
        ParityBudgetSelectedFieldFamily{
            .field_family = "reward_numeric",
            .selected_fields =
                {
                    current_selected_field("execution_episode_step.reward_total",
                                           "ExecutionEpisodeControllerStepResult", float64,
                                           "reward"),
                    current_selected_field("reward_report.fact_terms[].value", "RewardTerm",
                                           float64, "reward"),
                    current_selected_field("reward_report.shaping_terms[].value", "RewardTerm",
                                           float64, "reward"),
                },
            .comparator = std::string(kParityComparatorAbsoluteOrRelative),
            .absolute_tolerance = 1.0e-8,
            .relative_tolerance = 1.0e-10,
            .comparison_barriers = {"export"},
        },
        ParityBudgetSelectedFieldFamily{
            .field_family = "reward_termination_identity",
            .selected_fields =
                {
                    current_selected_field("reward_report.fact_terms[].name", "RewardTerm", string,
                                           "reward"),
                    current_selected_field("reward_report.fact_terms[].term_owner", "RewardTerm",
                                           string, "reward"),
                    current_selected_field("reward_report.shaping_terms[].name", "RewardTerm",
                                           string, "reward"),
                    current_selected_field("reward_report.shaping_terms[].term_owner", "RewardTerm",
                                           string, "reward"),
                    current_selected_field("reward_report.fact_snapshot_version", "RewardReport",
                                           unsigned_integer, "reward"),
                    current_selected_field("execution_episode_step.terminated",
                                           "ExecutionEpisodeControllerStepResult", boolean,
                                           "termination"),
                    current_selected_field("execution_episode_step.truncated",
                                           "ExecutionEpisodeControllerStepResult", boolean,
                                           "termination"),
                    current_selected_field("termination_spec.reason", "TerminationSpec", string,
                                           "termination"),
                    current_selected_field("termination_spec.reason_source", "TerminationSpec",
                                           string, "termination"),
                    current_selected_field("termination_spec.snapshot_version", "TerminationSpec",
                                           unsigned_integer, "termination"),
                },
            .comparator = std::string(kParityComparatorExact),
            .comparison_barriers = {"export"},
        },
        ParityBudgetSelectedFieldFamily{
            .field_family = "exact_event_identity",
            .selected_fields =
                {
                    future_selected_field("events.timestamp", "EventOrderKeyContract", float64,
                                          "events"),
                    future_selected_field("events.priority", "EventOrderKeyContract",
                                          signed_integer, "events"),
                    future_selected_field("events.event_id", "EventOrderKeyContract",
                                          unsigned_integer, "events"),
                    future_selected_field("events.event_family_membership", "EventOrderKeyContract",
                                          string, "events"),
                },
            .comparator = std::string(kParityComparatorExact),
            .comparison_barriers = {"export"},
        },
        ParityBudgetSelectedFieldFamily{
            .field_family = "exact_export_envelope",
            .selected_fields =
                {
                    future_selected_field("export.schema_version", "ExportEnvelopeContract", string,
                                          "export_envelope"),
                    future_selected_field("export.field_set", "ExportEnvelopeContract", structured,
                                          "export_envelope"),
                    future_selected_field("export.visibility_label", "ExportEnvelopeContract",
                                          string, "export_envelope"),
                    future_selected_field("export.provenance", "ExportEnvelopeContract", string,
                                          "export_envelope"),
                    future_selected_field("export.source_snapshot_version",
                                          "ExportEnvelopeContract", unsigned_integer,
                                          "export_envelope"),
                },
            .comparator = std::string(kParityComparatorExact),
            .comparison_barriers = {"export"},
        },
    };
    return fields;
}

inline bool parity_budget_selected_field_is_valid(const ParityBudgetSelectedField &field) {
    if (is_blank(field.field_path) || is_blank(field.surface_owner) || is_blank(field.shard)) {
        return false;
    }
    switch (field.surface_status) {
    case ParityBudgetSurfaceStatus::current_dto:
    case ParityBudgetSurfaceStatus::future_frozen_contract:
        break;
    default:
        return false;
    }
    switch (field.value_kind) {
    case ParityBudgetValueKind::boolean:
    case ParityBudgetValueKind::signed_integer:
    case ParityBudgetValueKind::unsigned_integer:
    case ParityBudgetValueKind::float32:
    case ParityBudgetValueKind::float64:
    case ParityBudgetValueKind::string:
    case ParityBudgetValueKind::structured:
        return true;
    }
    return false;
}

inline bool
parity_budget_selected_field_family_is_valid(const ParityBudgetSelectedFieldFamily &field_family) {
    if (is_blank(field_family.field_family) || field_family.selected_fields.empty() ||
        field_family.comparison_barriers.empty()) {
        return false;
    }
    if (std::any_of(field_family.selected_fields.begin(), field_family.selected_fields.end(),
                    [](const ParityBudgetSelectedField &field) {
                        return !parity_budget_selected_field_is_valid(field);
                    }) ||
        std::any_of(field_family.comparison_barriers.begin(),
                    field_family.comparison_barriers.end(),
                    [](const std::string &barrier) { return is_blank(barrier); })) {
        return false;
    }
    if (field_family.comparator == kParityComparatorExact) {
        return field_family.absolute_tolerance == 0.0 && field_family.relative_tolerance == 0.0;
    }
    if (field_family.comparator == kParityComparatorAbsoluteOrRelative) {
        const bool fields_are_floating =
            std::all_of(field_family.selected_fields.begin(), field_family.selected_fields.end(),
                        [](const ParityBudgetSelectedField &field) {
                            return field.value_kind == ParityBudgetValueKind::float32 ||
                                   field.value_kind == ParityBudgetValueKind::float64;
                        });
        return fields_are_floating && std::isfinite(field_family.absolute_tolerance) &&
               std::isfinite(field_family.relative_tolerance) &&
               field_family.absolute_tolerance > 0.0 && field_family.relative_tolerance > 0.0;
    }
    return false;
}

inline bool parity_budget_barrier_rule_is_valid(const ParityBudgetBarrierRule &rule) {
    return !is_blank(rule.barrier_id) && !is_blank(rule.candidate_rule);
}

inline bool resident_candidate_budget_has_frozen_selected_slice(const ParityBudgetRecord &record) {
    if (record.backend_profile_id != "resident_state.unmaintained_candidate") {
        return true;
    }
    const auto &required_barriers = resident_candidate_sync_barrier_contract();
    if (record.sync_barriers != required_barriers ||
        record.selected_slice_fields != resident_candidate_selected_slice_field_contract() ||
        record.barrier_rules != resident_candidate_barrier_contract()) {
        return false;
    }
    for (const auto &field_family : record.selected_slice_fields) {
        if (!parity_budget_selected_field_family_is_valid(field_family)) {
            return false;
        }
    }
    for (const std::string &required_barrier : required_barriers) {
        if (!contains_value(record.sync_barriers, required_barrier)) {
            return false;
        }
        const auto rule =
            std::find_if(record.barrier_rules.begin(), record.barrier_rules.end(),
                         [required_barrier](const ParityBudgetBarrierRule &candidate) {
                             return candidate.barrier_id == required_barrier;
                         });
        if (rule == record.barrier_rules.end() || !parity_budget_barrier_rule_is_valid(*rule)) {
            return false;
        }
    }
    const auto find_rule = [&record](std::string_view barrier_id) {
        return std::find_if(record.barrier_rules.begin(), record.barrier_rules.end(),
                            [barrier_id](const ParityBudgetBarrierRule &candidate) {
                                return candidate.barrier_id == barrier_id;
                            });
    };
    const auto input_injection = find_rule("input_injection");
    const auto stage_publish = find_rule("stage_publish");
    const auto partial_sync_commit = find_rule("partial_sync_commit");
    const auto window_commit = find_rule("window_commit");
    const auto export_rule = find_rule("export");
    if (!input_injection->enabled || !input_injection->comparison_eligible ||
        input_injection->host_truth_available || input_injection->visible_shards.empty() ||
        !stage_publish->enabled || stage_publish->comparison_eligible ||
        stage_publish->host_truth_available || !stage_publish->visible_shards.empty() ||
        partial_sync_commit->enabled || partial_sync_commit->comparison_eligible ||
        partial_sync_commit->host_truth_available || !partial_sync_commit->visible_shards.empty() ||
        !window_commit->enabled || !window_commit->comparison_eligible ||
        window_commit->host_truth_available || window_commit->visible_shards.empty() ||
        !export_rule->enabled || !export_rule->comparison_eligible ||
        !export_rule->host_truth_available || export_rule->visible_shards.empty()) {
        return false;
    }
    std::vector<std::string> selected_fields;
    for (const auto &field_family : record.selected_slice_fields) {
        for (const auto &comparison_barrier : field_family.comparison_barriers) {
            const auto rule =
                std::find_if(record.barrier_rules.begin(), record.barrier_rules.end(),
                             [&comparison_barrier](const ParityBudgetBarrierRule &candidate) {
                                 return candidate.barrier_id == comparison_barrier;
                             });
            if (rule == record.barrier_rules.end() || !rule->comparison_eligible) {
                return false;
            }
        }
        for (const auto &field : field_family.selected_fields) {
            for (const auto &comparison_barrier : field_family.comparison_barriers) {
                const auto rule =
                    std::find_if(record.barrier_rules.begin(), record.barrier_rules.end(),
                                 [&comparison_barrier](const ParityBudgetBarrierRule &candidate) {
                                     return candidate.barrier_id == comparison_barrier;
                                 });
                if (rule == record.barrier_rules.end() ||
                    !contains_value(rule->visible_shards, field.shard)) {
                    return false;
                }
            }
            if (contains_value(selected_fields, field.field_path)) {
                return false;
            }
            selected_fields.push_back(field.field_path);
        }
    }
    return true;
}

inline bool parity_budget_is_maintained_baseline(const ParityBudgetRecord &record) {
    return record.budget_id == kParityBudgetCpuExactReferenceV1 &&
           record.backend_profile_id == "cpu_exact.reference" &&
           record.profile_class == kParityBudgetProfileClassReference &&
           record.budget_scope.maintained_status == "maintained_exact_baseline";
}

inline ParityBudgetValidationResult
validate_parity_budget_record_contract(const ParityBudgetRecord &record) {
    ParityBudgetValidationResult result{};

    if (is_blank(record.budget_id)) {
        result.add_error("budget_id is required");
    }
    if (record.budget_version <= 0) {
        result.add_error("budget_version must be positive");
    }
    if (is_blank(record.backend_profile_id)) {
        result.add_error("backend_profile_id is required");
    }
    if (is_blank(record.profile_class)) {
        result.add_error("profile_class is required");
    }
    if (is_blank(record.comparison_reference)) {
        result.add_error("comparison_reference is required");
    }
    if (record.budget_scope.clock_domains.empty()) {
        result.add_error("budget_scope.clock_domains is required");
    }
    if (record.budget_scope.output_families.empty()) {
        result.add_error("budget_scope.output_families is required");
    }
    if (!parity_budget_has_required_comparison_metadata(record)) {
        result.add_error(
            "comparison domains must define event_order, snapshot_versions, "
            "observation_export, diagnostics_trace, sync_barriers, and mismatch_policy");
    }
    if (record.diagnostics_requirements.empty()) {
        result.add_error("diagnostics_requirements is required");
    }
    if (!resident_candidate_budget_has_frozen_selected_slice(record)) {
        result.add_error(
            "resident-state candidate must freeze selected field families, comparators, "
            "tolerances, and all five barrier rules");
    }
    if (!parity_budget_has_acceptance_gate(record)) {
        result.reject(std::string(kParityBudgetRejectionAcceptanceGateMissing));
        result.add_error("acceptance_gate is required");
        return result;
    }

    if (!result.valid) {
        result.rejection_reason = std::string(kParityBudgetRejectionMetadataIncomplete);
        return result;
    }

    result.accepted_for_maintained_use = parity_budget_is_maintained_baseline(record);
    if (!result.accepted_for_maintained_use) {
        if (record.profile_class == kParityBudgetProfileClassDiagnosticsOnly) {
            result.rejection_reason =
                std::string(kParityBudgetRejectionDiagnosticsOnlyNotMaintained);
        } else {
            result.rejection_reason = std::string(kParityBudgetRejectionCandidateNotMaintained);
        }
    }
    return result;
}

} // namespace runtime::parity
