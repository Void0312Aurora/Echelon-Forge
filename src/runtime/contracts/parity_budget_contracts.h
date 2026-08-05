#pragma once

#include <algorithm>
#include <cctype>
#include <cmath>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "runtime/contracts/cuda_resident_selected_slice_contract.h"

namespace runtime::parity {

inline constexpr std::string_view kParityBudgetCpuExactReferenceV1 =
    "parity_budget.cpu_exact.reference.v1";
inline constexpr std::string_view kParityBudgetGpuHelpersDiagnosticsOnlyV1 =
    "parity_budget.gpu_helpers.diagnostics_only.v1";
inline constexpr std::string_view kParityBudgetGpuExactUnmaintainedCandidateV1 =
    "parity_budget.gpu_exact.unmaintained_candidate.v1";
inline constexpr std::string_view kParityBudgetResidentStateUnmaintainedCandidateV1 =
    "parity_budget.resident_state.unmaintained_candidate.v1";
inline constexpr std::string_view kParityBudgetShadowCompareUnmaintainedCandidateV1 =
    "parity_budget.shadow_compare.unmaintained_candidate.v1";

inline constexpr std::string_view kParityBudgetProfileClassReference = "reference";
inline constexpr std::string_view kParityBudgetProfileClassAcceleratedExact = "accelerated_exact";
inline constexpr std::string_view kParityBudgetProfileClassResidentState = "resident_state";
inline constexpr std::string_view kParityBudgetProfileClassDiagnosticsOnly = "diagnostics_only";
inline constexpr std::string_view kParityBudgetProfileClassApproximate = "approximate";

inline constexpr std::string_view kParityBudgetRejectionMissingBudgetRef =
    "missing_parity_budget_ref";
inline constexpr std::string_view kParityBudgetRejectionUnknownBudgetRef =
    "unknown_parity_budget_ref";
inline constexpr std::string_view kParityBudgetRejectionProfileClassIncompatible =
    "parity_budget_profile_class_incompatible";
inline constexpr std::string_view kParityBudgetRejectionAcceptanceGateMissing =
    "parity_budget_acceptance_gate_missing";
inline constexpr std::string_view kParityBudgetRejectionCandidateNotMaintained =
    "parity_budget_candidate_is_not_accepted_for_maintained_use";
inline constexpr std::string_view kParityBudgetRejectionDiagnosticsOnlyNotMaintained =
    "parity_budget_diagnostics_only_is_not_accepted_for_maintained_use";
inline constexpr std::string_view kParityBudgetRejectionMetadataIncomplete =
    "parity_budget_metadata_incomplete";
inline constexpr std::string_view kParityComparatorExact = "exact";
inline constexpr std::string_view kParityComparatorAbsoluteOrRelative = "absolute_or_relative";

struct ParityBudgetScope {
    std::string maintained_status;
    std::vector<std::string> clock_domains;
    std::vector<std::string> state_shards;
    std::vector<std::string> output_families;
    std::vector<std::string> diagnostics_only_surfaces;
};

struct ParityBudgetComparisonDomain {
    std::string mode;
    std::vector<std::string> identity_fields;
    std::vector<std::string> envelope_fields;
    std::vector<std::string> structured_fields;
    std::vector<std::string> tolerance_requirements;
    std::string payload_policy;
    std::string prose_policy;
    std::string normalization;
    std::string allowed_drift;
};

struct ParityBudgetMismatchPolicy {
    std::string maintained_profile_result;
    std::string candidate_result;
    std::string diagnostics_result;
    bool quarantine_required = false;
};

enum class ParityBudgetSurfaceStatus {
    current_dto,
    future_frozen_contract,
};

enum class ParityBudgetValueKind {
    boolean,
    signed_integer,
    unsigned_integer,
    float32,
    float64,
    string,
    structured,
};

struct ParityBudgetSelectedField {
    std::string field_path;
    std::string surface_owner;
    ParityBudgetSurfaceStatus surface_status = ParityBudgetSurfaceStatus::current_dto;
    ParityBudgetValueKind value_kind = ParityBudgetValueKind::structured;
    std::string shard;

    bool operator==(const ParityBudgetSelectedField &) const = default;
};

struct ParityBudgetSelectedFieldFamily {
    std::string field_family;
    std::vector<ParityBudgetSelectedField> selected_fields;
    std::string comparator;
    double absolute_tolerance = 0.0;
    double relative_tolerance = 0.0;
    std::vector<std::string> comparison_barriers;

    bool operator==(const ParityBudgetSelectedFieldFamily &) const = default;
};

struct ParityBudgetBarrierRule {
    std::string barrier_id;
    std::string candidate_rule;
    std::vector<std::string> visible_shards;
    bool enabled = true;
    bool comparison_eligible = false;
    bool host_truth_available = false;

    bool operator==(const ParityBudgetBarrierRule &) const = default;
};

struct ParityBudgetRecord {
    std::string budget_id;
    int budget_version = 0;
    std::string backend_profile_id;
    std::string profile_class;
    std::string comparison_reference;
    ParityBudgetScope budget_scope;
    ParityBudgetComparisonDomain event_order;
    ParityBudgetComparisonDomain snapshot_versions;
    ParityBudgetComparisonDomain numeric_state;
    ParityBudgetComparisonDomain observation_export;
    ParityBudgetComparisonDomain diagnostics_trace;
    std::vector<std::string> sync_barriers;
    std::vector<std::string> diagnostics_requirements;
    ParityBudgetMismatchPolicy mismatch_policy;
    std::string acceptance_gate;
    std::string change_reason;
    std::vector<ParityBudgetSelectedFieldFamily> selected_slice_fields;
    std::vector<ParityBudgetBarrierRule> barrier_rules;
};

struct ParityBudgetValidationResult {
    bool valid = true;
    bool accepted_for_maintained_use = false;
    std::string rejection_reason;
    std::vector<std::string> errors;

    void add_error(std::string error) {
        valid = false;
        errors.push_back(std::move(error));
    }

    void reject(std::string reason) {
        valid = false;
        accepted_for_maintained_use = false;
        rejection_reason = std::move(reason);
    }
};

inline bool is_blank(std::string_view value) {
    return std::all_of(value.begin(), value.end(),
                       [](unsigned char c) { return std::isspace(c) != 0; });
}

inline bool contains_value(const std::vector<std::string> &items, std::string_view expected) {
    return std::find(items.begin(), items.end(), expected) != items.end();
}

inline bool profile_class_compatible_with_parity_budget(std::string_view profile_class,
                                                        std::string_view budget_profile_class) {
    if (profile_class == budget_profile_class) {
        return true;
    }

    return false;
}

inline bool parity_budget_has_required_comparison_metadata(const ParityBudgetRecord &record) {
    return !is_blank(record.event_order.mode) && !record.event_order.identity_fields.empty() &&
           !is_blank(record.snapshot_versions.mode) &&
           !record.snapshot_versions.identity_fields.empty() &&
           !is_blank(record.observation_export.mode) &&
           !record.observation_export.envelope_fields.empty() &&
           !is_blank(record.observation_export.payload_policy) &&
           !is_blank(record.diagnostics_trace.mode) &&
           !record.diagnostics_trace.structured_fields.empty() &&
           !is_blank(record.diagnostics_trace.prose_policy) && !record.sync_barriers.empty() &&
           !is_blank(record.mismatch_policy.maintained_profile_result) &&
           !is_blank(record.mismatch_policy.diagnostics_result);
}

inline bool parity_budget_has_acceptance_gate(const ParityBudgetRecord &record) {
    return !is_blank(record.acceptance_gate);
}

inline ParityBudgetSelectedField current_selected_field(std::string field_path,
                                                        std::string surface_owner,
                                                        ParityBudgetValueKind value_kind,
                                                        std::string shard) {
    return ParityBudgetSelectedField{
        .field_path = std::move(field_path),
        .surface_owner = std::move(surface_owner),
        .surface_status = ParityBudgetSurfaceStatus::current_dto,
        .value_kind = value_kind,
        .shard = std::move(shard),
    };
}

inline ParityBudgetSelectedField future_selected_field(std::string field_path,
                                                       std::string surface_owner,
                                                       ParityBudgetValueKind value_kind,
                                                       std::string shard) {
    return ParityBudgetSelectedField{
        .field_path = std::move(field_path),
        .surface_owner = std::move(surface_owner),
        .surface_status = ParityBudgetSurfaceStatus::future_frozen_contract,
        .value_kind = value_kind,
        .shard = std::move(shard),
    };
}

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
            .candidate_rule =
                "disabled for the RB2 selected slice; no partial reconstructed shard and no "
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

inline ParityBudgetRecord make_cpu_exact_reference_budget() {
    return ParityBudgetRecord{
        .budget_id = std::string(kParityBudgetCpuExactReferenceV1),
        .budget_version = 1,
        .backend_profile_id = "cpu_exact.reference",
        .profile_class = std::string(kParityBudgetProfileClassReference),
        .comparison_reference = "self",
        .budget_scope =
            ParityBudgetScope{
                .maintained_status = "maintained_exact_baseline",
                .clock_domains = {"physics.fixed_tick", "sensor.scan_slot"},
                .state_shards = {"scheduler", "physics", "track", "observation", "engagement"},
                .output_families =
                    {
                        "observation_packet",
                        "committed_snapshot",
                        "diagnostics_trace",
                    },
                .diagnostics_only_surfaces = {"human_readable_diagnostics_prose"},
            },
        .event_order =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity",
                .identity_fields = {"timestamp", "priority", "event_id", "event_family_membership"},
                .allowed_drift = "none",
            },
        .snapshot_versions =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity",
                .identity_fields =
                    {
                        "world_id",
                        "global_version",
                        "barrier_id",
                        "barrier_sequence",
                        "shard_versions",
                        "lineage",
                    },
                .normalization = "exported_snapshot_version",
                .allowed_drift = "none",
            },
        .numeric_state =
            ParityBudgetComparisonDomain{
                .mode = "exact",
                .tolerance_requirements = {},
                .allowed_drift = "none",
            },
        .observation_export =
            ParityBudgetComparisonDomain{
                .mode = "exact_envelope",
                .envelope_fields =
                    {
                        "schema_version",
                        "field_set",
                        "visibility_label",
                        "provenance",
                        "source_snapshot_version",
                    },
                .payload_policy = "inherit_numeric_state",
            },
        .diagnostics_trace =
            ParityBudgetComparisonDomain{
                .mode = "exact_structured_ancestry",
                .structured_fields =
                    {
                        "source_request_id",
                        "event_id",
                        "source_snapshot_version",
                        "resulting_snapshot_version",
                        "mismatch_code",
                    },
                .prose_policy = "diagnostics_only",
            },
        .sync_barriers = {"input_injection", "tick_commit", "window_commit", "export"},
        .diagnostics_requirements =
            {
                "backend_profile_id",
                "budget_id",
                "budget_version",
                "comparison_reference",
                "source_snapshot_version",
                "resulting_snapshot_version",
                "sync_barrier_id",
                "mismatch_domain",
                "mismatch_code",
                "mismatch_summary",
            },
        .mismatch_policy =
            ParityBudgetMismatchPolicy{
                .maintained_profile_result = "fail",
                .candidate_result = "not_applicable",
                .diagnostics_result = "report_only",
                .quarantine_required = true,
            },
        .acceptance_gate = "maintained_cpu_reference_existing_baseline",
        .change_reason = "initial maintained exact reference budget",
        .selected_slice_fields = {},
        .barrier_rules = {},
    };
}

inline ParityBudgetRecord make_gpu_helpers_diagnostics_only_budget() {
    return ParityBudgetRecord{
        .budget_id = std::string(kParityBudgetGpuHelpersDiagnosticsOnlyV1),
        .budget_version = 1,
        .backend_profile_id = "gpu_helpers.diagnostics_only",
        .profile_class = std::string(kParityBudgetProfileClassDiagnosticsOnly),
        .comparison_reference = "cpu_exact.reference",
        .budget_scope =
            ParityBudgetScope{
                .maintained_status = "diagnostics_only_not_truth",
                .clock_domains = {"declared_by_helper_export"},
                .state_shards = {},
                .output_families = {"helper_metrics", "helper_trace", "probe_export"},
                .diagnostics_only_surfaces = {"all_exported_surfaces"},
            },
        .event_order =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity_if_replayed_against_reference",
                .identity_fields = {"timestamp", "priority", "event_id", "event_family_membership"},
                .allowed_drift = "none",
            },
        .snapshot_versions =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity_if_snapshot_link_is_reported",
                .identity_fields =
                    {
                        "source_snapshot_version",
                        "barrier_id",
                        "barrier_sequence",
                    },
                .normalization = "exported_snapshot_version",
                .allowed_drift = "none",
            },
        .numeric_state =
            ParityBudgetComparisonDomain{
                .mode = "diagnostics_only",
                .tolerance_requirements =
                    {
                        "field_family_comparator_threshold_if_promoted",
                    },
            },
        .observation_export =
            ParityBudgetComparisonDomain{
                .mode = "exact_if_present",
                .envelope_fields =
                    {
                        "schema_version",
                        "field_set",
                        "visibility_label",
                        "provenance",
                        "source_snapshot_version",
                    },
                .payload_policy = "inherit_numeric_state",
            },
        .diagnostics_trace =
            ParityBudgetComparisonDomain{
                .mode = "exact_if_present",
                .structured_fields =
                    {
                        "source_request_id",
                        "event_id",
                        "source_snapshot_version",
                        "mismatch_code",
                    },
                .prose_policy = "diagnostics_only",
            },
        .sync_barriers = {"export"},
        .diagnostics_requirements =
            {
                "backend_profile_id",
                "budget_id",
                "budget_version",
                "comparison_reference",
                "source_snapshot_version",
                "export_barrier_id",
                "helper_name",
                "helper_build_or_feature_flag",
                "diagnostics_label",
                "mismatch_summary",
            },
        .mismatch_policy =
            ParityBudgetMismatchPolicy{
                .maintained_profile_result = "not_applicable",
                .candidate_result = "not_applicable",
                .diagnostics_result = "report_only",
                .quarantine_required = false,
            },
        .acceptance_gate = "not_eligible_for_maintained_truth_without_reclassification",
        .change_reason = "initial diagnostics-only placeholder for GPU helper exports",
        .selected_slice_fields = {},
        .barrier_rules = {},
    };
}

inline ParityBudgetRecord make_gpu_exact_unmaintained_candidate_budget() {
    return ParityBudgetRecord{
        .budget_id = std::string(kParityBudgetGpuExactUnmaintainedCandidateV1),
        .budget_version = 1,
        .backend_profile_id = "gpu_exact.unmaintained_candidate",
        .profile_class = std::string(kParityBudgetProfileClassAcceleratedExact),
        .comparison_reference = "cpu_exact.reference",
        .budget_scope =
            ParityBudgetScope{
                .maintained_status = "unmaintained_candidate",
                .clock_domains = {"physics.fixed_tick", "sensor.scan_slot"},
                .state_shards = {"scheduler", "physics", "track", "observation", "engagement"},
                .output_families =
                    {
                        "observation_packet",
                        "committed_snapshot",
                        "diagnostics_trace",
                    },
                .diagnostics_only_surfaces =
                    {
                        "accelerator_kernel_notes",
                        "human_readable_diagnostics_prose",
                    },
            },
        .event_order =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity_required_for_promotion",
                .identity_fields = {"timestamp", "priority", "event_id", "event_family_membership"},
                .allowed_drift = "none",
            },
        .snapshot_versions =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity_required_for_promotion",
                .identity_fields =
                    {
                        "world_id",
                        "global_version",
                        "barrier_id",
                        "barrier_sequence",
                        "shard_versions",
                        "lineage",
                    },
                .normalization = "exported_snapshot_version",
                .allowed_drift = "none",
            },
        .numeric_state =
            ParityBudgetComparisonDomain{
                .mode = "exact_required_for_accelerated_exact",
                .tolerance_requirements = {},
                .allowed_drift = "none",
            },
        .observation_export =
            ParityBudgetComparisonDomain{
                .mode = "exact_required_for_promotion",
                .envelope_fields =
                    {
                        "schema_version",
                        "field_set",
                        "visibility_label",
                        "provenance",
                        "source_snapshot_version",
                    },
                .payload_policy = "inherit_numeric_state",
            },
        .diagnostics_trace =
            ParityBudgetComparisonDomain{
                .mode = "exact_required_for_promotion",
                .structured_fields =
                    {
                        "source_request_id",
                        "event_id",
                        "source_snapshot_version",
                        "resulting_snapshot_version",
                        "mismatch_code",
                    },
                .prose_policy = "diagnostics_only",
            },
        .sync_barriers = {"input_injection", "tick_commit", "window_commit", "export"},
        .diagnostics_requirements =
            {
                "backend_profile_id",
                "budget_id",
                "budget_version",
                "comparison_reference",
                "source_snapshot_version",
                "resulting_snapshot_version",
                "sync_barrier_id",
                "accelerator_backend_id",
                "accelerator_build_or_feature_flag",
                "mismatch_domain",
                "mismatch_code",
                "mismatch_summary",
            },
        .mismatch_policy =
            ParityBudgetMismatchPolicy{
                .maintained_profile_result = "not_accepted",
                .candidate_result = "fail_and_remain_unmaintained",
                .diagnostics_result = "report_only",
                .quarantine_required = true,
            },
        .acceptance_gate = "future_accelerated_exact_promotion_review_with_replay_evidence",
        .change_reason = "initial unmaintained candidate budget; no exact GPU acceptance claimed",
        .selected_slice_fields = {},
        .barrier_rules = {},
    };
}

inline ParityBudgetRecord make_resident_state_unmaintained_candidate_budget() {
    return ParityBudgetRecord{
        .budget_id = std::string(kParityBudgetResidentStateUnmaintainedCandidateV1),
        .budget_version = 1,
        .backend_profile_id = "resident_state.unmaintained_candidate",
        .profile_class = std::string(kParityBudgetProfileClassResidentState),
        .comparison_reference = "cpu_exact.reference",
        .budget_scope =
            ParityBudgetScope{
                .maintained_status = "unmaintained_candidate",
                .clock_domains = {"physics.fixed_tick", "sensor.scan_slot"},
                .state_shards = {"observation", "physics_or_track_if_declared_by_future_profile"},
                .output_families =
                    {
                        "observation_packet",
                        "committed_snapshot",
                        "diagnostics_trace",
                    },
                .diagnostics_only_surfaces =
                    {
                        "unsynced_backend_local_state",
                        "human_readable_diagnostics_prose",
                    },
            },
        .event_order =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity_required_at_declared_barriers",
                .identity_fields = {"timestamp", "priority", "event_id", "event_family_membership"},
                .allowed_drift = "none",
            },
        .snapshot_versions =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity_required_for_host_visible_exports",
                .identity_fields =
                    {
                        "world_id",
                        "global_version",
                        "barrier_id",
                        "barrier_sequence",
                        "shard_versions",
                        "lineage",
                    },
                .normalization = "exported_snapshot_version",
                .allowed_drift = "none",
            },
        .numeric_state =
            ParityBudgetComparisonDomain{
                .mode = "exact_by_default_with_explicit_future_tolerance_only",
                .tolerance_requirements = {"field_family", "comparator", "threshold"},
                .allowed_drift = "none",
            },
        .observation_export =
            ParityBudgetComparisonDomain{
                .mode = "exact_for_host_visible_exports",
                .envelope_fields =
                    {
                        "schema_version",
                        "field_set",
                        "visibility_label",
                        "provenance",
                        "source_snapshot_version",
                    },
                .payload_policy = "inherit_numeric_state",
            },
        .diagnostics_trace =
            ParityBudgetComparisonDomain{
                .mode = "exact_for_host_visible_exports",
                .structured_fields =
                    {
                        "source_request_id",
                        "event_id",
                        "source_snapshot_version",
                        "resulting_snapshot_version",
                        "mismatch_code",
                    },
                .prose_policy = "diagnostics_only",
            },
        .sync_barriers = resident_candidate_sync_barrier_contract(),
        .diagnostics_requirements =
            {
                "backend_profile_id",
                "budget_id",
                "budget_version",
                "comparison_reference",
                "source_snapshot_version",
                "resulting_snapshot_version",
                "sync_barrier_id",
                "host_state_owner",
                "backend_state_owner",
                "sync_policy",
                "resident_state_scope",
                "mismatch_domain",
                "mismatch_code",
                "mismatch_summary",
            },
        .mismatch_policy =
            ParityBudgetMismatchPolicy{
                .maintained_profile_result = "not_accepted",
                .candidate_result = "fail_and_remain_unmaintained",
                .diagnostics_result = "report_only",
                .quarantine_required = true,
            },
        .acceptance_gate =
            "future_resident_state_promotion_review_with_ownership_sync_and_replay_evidence",
        .change_reason = "initial unmaintained resident-state candidate budget; host/backend split "
                         "not yet accepted as maintained",
        .selected_slice_fields = resident_candidate_selected_slice_field_contract(),
        .barrier_rules = resident_candidate_barrier_contract(),
    };
}

inline ParityBudgetRecord make_shadow_compare_unmaintained_candidate_budget() {
    return ParityBudgetRecord{
        .budget_id = std::string(kParityBudgetShadowCompareUnmaintainedCandidateV1),
        .budget_version = 1,
        .backend_profile_id = "shadow_compare.unmaintained_candidate",
        .profile_class = std::string(kParityBudgetProfileClassDiagnosticsOnly),
        .comparison_reference = "cpu_exact.reference",
        .budget_scope =
            ParityBudgetScope{
                .maintained_status = "unmaintained_candidate",
                .clock_domains = {"reference_clock_only"},
                .state_shards = {},
                .output_families = {"shadow_report", "mismatch_report", "diagnostics_trace"},
                .diagnostics_only_surfaces =
                    {
                        "shadow_report",
                        "mismatch_report",
                        "human_readable_diagnostics_prose",
                    },
            },
        .event_order =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity_for_reference_stream",
                .identity_fields = {"timestamp", "priority", "event_id", "event_family_membership"},
                .allowed_drift = "none",
            },
        .snapshot_versions =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity_for_reference_links",
                .identity_fields =
                    {
                        "source_snapshot_version",
                        "barrier_id",
                        "barrier_sequence",
                    },
                .normalization = "exported_snapshot_version",
                .allowed_drift = "none",
            },
        .numeric_state =
            ParityBudgetComparisonDomain{
                .mode = "diagnostics_only_until_promoted",
                .tolerance_requirements = {"field_family", "comparator", "threshold"},
            },
        .observation_export =
            ParityBudgetComparisonDomain{
                .mode = "exact_if_exported",
                .envelope_fields =
                    {
                        "schema_version",
                        "field_set",
                        "visibility_label",
                        "provenance",
                        "source_snapshot_version",
                    },
                .payload_policy = "inherit_numeric_state",
            },
        .diagnostics_trace =
            ParityBudgetComparisonDomain{
                .mode = "exact_for_shadow_report_ancestry",
                .structured_fields =
                    {
                        "source_request_id",
                        "event_id",
                        "source_snapshot_version",
                        "mismatch_code",
                    },
                .prose_policy = "diagnostics_only",
            },
        .sync_barriers = {"reference_export", "shadow_report_export"},
        .diagnostics_requirements =
            {
                "backend_profile_id",
                "budget_id",
                "budget_version",
                "comparison_reference",
                "source_snapshot_version",
                "shadow_run_id",
                "compared_profile_id",
                "sync_barrier_id",
                "mismatch_domain",
                "mismatch_code",
                "mismatch_summary",
            },
        .mismatch_policy =
            ParityBudgetMismatchPolicy{
                .maintained_profile_result = "not_applicable",
                .candidate_result = "report_only_and_remain_unmaintained",
                .diagnostics_result = "report_only",
                .quarantine_required = false,
            },
        .acceptance_gate = "future_shadow_compare_review_before_any_maintained_claim",
        .change_reason = "initial unmaintained shadow-compare placeholder; no shadow capability "
                         "acceptance claimed",
        .selected_slice_fields = {},
        .barrier_rules = {},
    };
}

inline const std::vector<ParityBudgetRecord> &parity_budget_registry_seed() {
    static const std::vector<ParityBudgetRecord> registry = {
        make_cpu_exact_reference_budget(),
        make_gpu_helpers_diagnostics_only_budget(),
        make_gpu_exact_unmaintained_candidate_budget(),
        make_resident_state_unmaintained_candidate_budget(),
        make_shadow_compare_unmaintained_candidate_budget(),
    };
    return registry;
}

inline const ParityBudgetRecord *find_parity_budget_record(std::string_view budget_id) {
    const auto &registry = parity_budget_registry_seed();
    const auto it = std::find_if(
        registry.begin(), registry.end(),
        [budget_id](const ParityBudgetRecord &record) { return record.budget_id == budget_id; });
    return it == registry.end() ? nullptr : &(*it);
}

inline ParityBudgetValidationResult
validate_profile_owned_parity_budget(std::string_view backend_profile_id,
                                     std::string_view profile_class, std::string_view budget_ref) {
    ParityBudgetValidationResult result{};

    if (is_blank(budget_ref)) {
        result.reject(std::string(kParityBudgetRejectionMissingBudgetRef));
        result.add_error("budget_ref is required");
        return result;
    }

    const ParityBudgetRecord *record = find_parity_budget_record(budget_ref);
    if (record == nullptr) {
        result.reject(std::string(kParityBudgetRejectionUnknownBudgetRef));
        result.add_error("budget_ref was not found in the registry seed");
        return result;
    }

    result = validate_parity_budget_record_contract(*record);
    if (!result.valid) {
        return result;
    }

    if (!is_blank(backend_profile_id) && record->backend_profile_id != backend_profile_id) {
        result.reject(std::string(kParityBudgetRejectionMetadataIncomplete));
        result.add_error("backend_profile_id does not own the referenced budget");
        return result;
    }

    if (!profile_class_compatible_with_parity_budget(profile_class, record->profile_class)) {
        result.reject(std::string(kParityBudgetRejectionProfileClassIncompatible));
        result.add_error("profile_class is not compatible with the referenced budget");
        return result;
    }

    return result;
}

inline std::optional<ParityBudgetValidationResult> validate_parity_budget_registry_seed() {
    const auto &registry = parity_budget_registry_seed();
    if (registry.empty()) {
        ParityBudgetValidationResult result{};
        result.reject(std::string(kParityBudgetRejectionMetadataIncomplete));
        result.add_error("registry seed must not be empty");
        return result;
    }

    std::vector<std::string> seen_budget_ids;
    seen_budget_ids.reserve(registry.size());
    std::vector<std::string> maintained_budget_ids;

    for (const auto &record : registry) {
        if (contains_value(seen_budget_ids, record.budget_id)) {
            ParityBudgetValidationResult result{};
            result.reject(std::string(kParityBudgetRejectionMetadataIncomplete));
            result.add_error("duplicate budget_id: " + record.budget_id);
            return result;
        }
        seen_budget_ids.push_back(record.budget_id);

        const ParityBudgetValidationResult record_result =
            validate_parity_budget_record_contract(record);
        if (!record_result.valid) {
            return record_result;
        }

        if (record_result.accepted_for_maintained_use) {
            maintained_budget_ids.push_back(record.budget_id);
        }
    }

    if (maintained_budget_ids.size() != 1 ||
        maintained_budget_ids.front() != kParityBudgetCpuExactReferenceV1) {
        ParityBudgetValidationResult result{};
        result.reject(std::string(kParityBudgetRejectionMetadataIncomplete));
        result.add_error(
            "registry seed must keep only parity_budget.cpu_exact.reference.v1 as maintained");
        return result;
    }

    return std::nullopt;
}

} // namespace runtime::parity
