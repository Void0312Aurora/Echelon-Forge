#pragma once

#include <array>
#include <string_view>

namespace runtime::cuda_resident::parity_release {

inline constexpr std::string_view kSchemaV1 =
    "cuda_resident.selected_slice_parity.v1";
inline constexpr std::string_view kPolicyId =
    "cuda_resident.cr2.selected_payload_release.v1";
inline constexpr std::string_view kSourceBudgetRef =
    "parity_budget.resident_state.unmaintained_candidate.v1";
inline constexpr std::string_view kTraceProfileId =
    "cr2.full_window.fixed_air.v1";
inline constexpr std::string_view kTraceSignatureSha256 =
    "54c0a905d07bf19212da7fa0dee1baa23599d4f80dc84e38f1f9957c41b28e3c";
inline constexpr std::string_view kPayloadBarrier = "export";
inline constexpr std::string_view kPayloadCapturePath = "host_diagnostic_export";
inline constexpr std::string_view kCanonicalWorldKey =
    "(session_index,window_index,world_slot,field_path)";
inline constexpr std::string_view kIdentityPolicy =
    "allocator_id_lane_local_diagnostic_excluded_from_digest.v1";
inline constexpr std::string_view kResetPolicy =
    "same_backend_two_runner_released_value_exact.v1";

struct NumericFieldRule {
    std::string_view path;
    double absolute_tolerance;
    double relative_tolerance;
    std::string_view comparator;
    bool finite_required;
    bool normalize_signed_zero;
};

struct IdentityFieldRule {
    std::string_view path;
    std::string_view disposition;
};

struct ExcludedFieldRule {
    std::string_view path;
    std::string_view reason;
};

struct BarrierRule {
    std::string_view barrier;
    std::string_view disposition;
    std::string_view reason;
};

inline constexpr auto kReleasedNumericFields = std::to_array<NumericFieldRule>({
    {"agent_observations.sim_time", 1.0e-8, 1.0e-12, "abs_rel", true, true},
    {"agent_observations.x", 5.0e-4, 1.0e-7, "abs_rel", true, true},
    {"agent_observations.y", 0.0, 0.0, "exact", true, true},
    {"agent_observations.z", 5.0e-4, 1.0e-7, "abs_rel", true, true},
    {"agent_observations.vx", 5.0e-2, 1.0e-4, "abs_rel", true, true},
    {"agent_observations.vy", 0.0, 0.0, "exact", true, true},
    {"agent_observations.vz", 2.0e-3, 1.0e-4, "abs_rel", true, true},
    {"agent_observations.heading", 0.0, 0.0, "exact", true, true},
    {"agent_observations.roll", 0.0, 0.0, "exact", true, true},
    {"agent_observations.speed", 5.0e-2, 1.0e-4, "abs_rel", true, true},
    {"agent_observations.gear_state", 0.0, 0.0, "exact", true, true},
    {"instrument_states.throttle_pos", 0.0, 0.0, "exact", true, true},
});

// The allocator/entity id is checked lane-locally by the Runner. It is retained
// in the diagnostic payload, but never participates in a cross-lane or reset
// digest. Cross-lane identity is the explicit array-order world_slot below.
inline constexpr auto kIdentityDiagnosticFields = std::to_array<IdentityFieldRule>({
    {"agent_observations.id", "lane_local_diagnostic_excluded_from_digest"},
});

inline constexpr auto kRawObservationFields = std::to_array<std::string_view>({
    "agent_observations.sim_time", "agent_observations.id", "agent_observations.x",
    "agent_observations.y", "agent_observations.z", "agent_observations.vx",
    "agent_observations.vy", "agent_observations.vz", "agent_observations.heading",
    "agent_observations.pitch", "agent_observations.roll", "agent_observations.speed",
    "agent_observations.health", "agent_observations.contact_count",
    "agent_observations.rwr_warning_count", "agent_observations.missiles_remaining",
    "agent_observations.can_fire", "agent_observations.gear_state",
    "agent_observations.throttle", "agent_observations.total_reward",
});

inline constexpr auto kRawInstrumentFields = std::to_array<std::string_view>({
    "instrument_states.alt_baro_m", "instrument_states.alt_radar_m",
    "instrument_states.ias_mps", "instrument_states.mach", "instrument_states.vvi_mps",
    "instrument_states.pitch_deg", "instrument_states.roll_deg",
    "instrument_states.heading_deg", "instrument_states.aoa_deg",
    "instrument_states.beta_deg", "instrument_states.g_load_normal",
    "instrument_states.g_load_axial", "instrument_states.p_deg_s", "instrument_states.q_deg_s",
    "instrument_states.r_deg_s", "instrument_states.engine_rpm_pct",
    "instrument_states.engine_temp_c", "instrument_states.fuel_flow_kg_h",
    "instrument_states.throttle_pos", "instrument_states.fuel_internal_kg",
    "instrument_states.fuel_external_kg", "instrument_states.gear_pos",
    "instrument_states.flaps_pos", "instrument_states.speedbrake_pos",
    "instrument_states.master_arm", "instrument_states.oat_c",
    "instrument_states.cmd_heading_deg", "instrument_states.cmd_alt_m",
    "instrument_states.cmd_speed_mps", "instrument_states.rwr_active",
    "instrument_states.weapon_selected", "instrument_states.missiles_remaining",
    "instrument_states.lat_deg", "instrument_states.lon_deg", "instrument_states.vn_mps",
    "instrument_states.ve_mps", "instrument_states.vd_mps",
    "instrument_states.ground_speed_mps", "instrument_states.ground_track_deg",
    "instrument_states.wind_speed_mps", "instrument_states.wind_dir_deg",
    "instrument_states.gps_available", "instrument_states.position_uncertainty_m",
    "instrument_states.gear_stress", "instrument_states.gear_collapsed",
    "instrument_states.on_runway",
});

inline constexpr auto kExcludedFields = std::to_array<ExcludedFieldRule>({
    {"agent_observations.pitch", "semantic_divergence"},
    {"agent_observations.health", "outside_minimal_release"},
    {"agent_observations.contact_count", "outside_minimal_release"},
    {"agent_observations.rwr_warning_count", "outside_minimal_release"},
    {"agent_observations.missiles_remaining", "outside_minimal_release"},
    {"agent_observations.can_fire", "outside_minimal_release"},
    {"agent_observations.throttle", "semantic_divergence"},
    {"agent_observations.total_reward", "ownership_divergence"},
    {"instrument_states.alt_baro_m", "outside_minimal_release"},
    {"instrument_states.alt_radar_m", "outside_minimal_release"},
    {"instrument_states.ias_mps", "outside_minimal_release"},
    {"instrument_states.mach", "outside_minimal_release"},
    {"instrument_states.vvi_mps", "outside_minimal_release"},
    {"instrument_states.pitch_deg", "semantic_divergence"},
    {"instrument_states.roll_deg", "outside_minimal_release"},
    {"instrument_states.heading_deg", "outside_minimal_release"},
    {"instrument_states.aoa_deg", "semantic_divergence"},
    {"instrument_states.beta_deg", "outside_minimal_release"},
    {"instrument_states.g_load_normal", "semantic_divergence"},
    {"instrument_states.g_load_axial", "semantic_divergence"},
    {"instrument_states.p_deg_s", "outside_minimal_release"},
    {"instrument_states.q_deg_s", "outside_minimal_release"},
    {"instrument_states.r_deg_s", "outside_minimal_release"},
    {"instrument_states.engine_rpm_pct", "outside_minimal_release"},
    {"instrument_states.engine_temp_c", "ownership_divergence"},
    {"instrument_states.fuel_flow_kg_h", "ownership_divergence"},
    {"instrument_states.fuel_internal_kg", "ownership_divergence"},
    {"instrument_states.fuel_external_kg", "outside_minimal_release"},
    {"instrument_states.gear_pos", "outside_minimal_release"},
    {"instrument_states.flaps_pos", "outside_minimal_release"},
    {"instrument_states.speedbrake_pos", "outside_minimal_release"},
    {"instrument_states.master_arm", "outside_minimal_release"},
    {"instrument_states.oat_c", "outside_minimal_release"},
    {"instrument_states.cmd_heading_deg", "outside_minimal_release"},
    {"instrument_states.cmd_alt_m", "outside_minimal_release"},
    {"instrument_states.cmd_speed_mps", "outside_minimal_release"},
    {"instrument_states.rwr_active", "outside_minimal_release"},
    {"instrument_states.weapon_selected", "outside_minimal_release"},
    {"instrument_states.missiles_remaining", "outside_minimal_release"},
    {"instrument_states.lat_deg", "outside_minimal_release"},
    {"instrument_states.lon_deg", "outside_minimal_release"},
    {"instrument_states.vn_mps", "outside_minimal_release"},
    {"instrument_states.ve_mps", "outside_minimal_release"},
    {"instrument_states.vd_mps", "outside_minimal_release"},
    {"instrument_states.ground_speed_mps", "outside_minimal_release"},
    {"instrument_states.ground_track_deg", "outside_minimal_release"},
    {"instrument_states.wind_speed_mps", "outside_minimal_release"},
    {"instrument_states.wind_dir_deg", "outside_minimal_release"},
    {"instrument_states.gps_available", "outside_minimal_release"},
    {"instrument_states.position_uncertainty_m", "outside_minimal_release"},
    {"instrument_states.gear_stress", "outside_minimal_release"},
    {"instrument_states.gear_collapsed", "outside_minimal_release"},
    {"instrument_states.on_runway", "outside_minimal_release"},
});

inline constexpr auto kBarrierRules = std::to_array<BarrierRule>({
    {"input_injection", "trace_only", "trace_signature_covers_all_pilot_action_fields"},
    {"window_commit", "metadata_only", "no_common_host_payload_at_commit_boundary"},
    {"export", "payload_released", "real_common_public_dto_export"},
});

inline constexpr auto kOuterLaneEvidenceFields = std::to_array<std::string_view>({
    "lane",
    "backend_id",
});

inline constexpr auto kDiagnosticOnlyMetadataFields = std::to_array<std::string_view>({
    "snapshot.lineage",
    "snapshot.source_backend_id",
    "export.provenance",
    "reset_generation",
    "source_snapshot_version",
});

inline constexpr bool contains_released(std::string_view value) {
    for (const auto &field : kReleasedNumericFields) {
        if (field.path == value) {
            return true;
        }
    }
    return false;
}

inline constexpr bool contains_identity(std::string_view value) {
    for (const auto &field : kIdentityDiagnosticFields) {
        if (field.path == value) {
            return true;
        }
    }
    return false;
}

inline constexpr bool contains_excluded(std::string_view value) {
    for (const auto &field : kExcludedFields) {
        if (field.path == value) {
            return true;
        }
    }
    return false;
}

inline constexpr bool partition_is_complete() {
    for (const auto field : kRawObservationFields) {
        const unsigned count = static_cast<unsigned>(contains_released(field)) +
                               static_cast<unsigned>(contains_identity(field)) +
                               static_cast<unsigned>(contains_excluded(field));
        if (count != 1) {
            return false;
        }
    }
    for (const auto field : kRawInstrumentFields) {
        const unsigned count = static_cast<unsigned>(contains_released(field)) +
                               static_cast<unsigned>(contains_identity(field)) +
                               static_cast<unsigned>(contains_excluded(field));
        if (count != 1) {
            return false;
        }
    }
    return true;
}

static_assert(partition_is_complete(),
              "CR2-4b raw DTO fields must have exactly one release disposition");
static_assert(kRawObservationFields.size() + kRawInstrumentFields.size() ==
                  kReleasedNumericFields.size() + kIdentityDiagnosticFields.size() +
                      kExcludedFields.size(),
              "CR2-4b release disposition must not add duplicate or unknown fields");

inline constexpr bool kCandidatePromotionBlocked = true;
inline constexpr bool kMaintainedClaimAllowed = false;
inline constexpr bool kPublicSupportEnabled = false;
inline constexpr bool kMeasuredConsumerPathUnchanged = true;

} // namespace runtime::cuda_resident::parity_release
