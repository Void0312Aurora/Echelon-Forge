#include "runtime/contracts/cuda_resident_backend_admission.h"
#include "core/engine/world_batch_runtime.h"
#include "runtime/facade/runtime_facade.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <ostream>
#include <string>
#include <string_view>
#include <type_traits>
#include <utility>
#include <vector>

static_assert(sizeof(RuntimeBatchConfig) == 2 * sizeof(std::size_t));

#define EF_PARITY_ASSERT_TYPE(owner, member, expected_type)                                        \
    static_assert(std::is_same_v<decltype(owner::member), expected_type>)

EF_PARITY_ASSERT_TYPE(WorldPilotActionAssignment, world_index, std::uint64_t);
EF_PARITY_ASSERT_TYPE(WorldPilotActionAssignment, entity_id, std::uint64_t);
EF_PARITY_ASSERT_TYPE(WorldPilotActionAssignment, action, PilotAction);
EF_PARITY_ASSERT_TYPE(PilotAction, active, bool);
EF_PARITY_ASSERT_TYPE(PilotAction, stick_pitch, double);
EF_PARITY_ASSERT_TYPE(PilotAction, stick_roll, double);
EF_PARITY_ASSERT_TYPE(PilotAction, rudder, double);
EF_PARITY_ASSERT_TYPE(PilotAction, throttle, double);
EF_PARITY_ASSERT_TYPE(PilotAction, gear_handle, float);
EF_PARITY_ASSERT_TYPE(PilotAction, flaps, float);
EF_PARITY_ASSERT_TYPE(PilotAction, speedbrake, float);
EF_PARITY_ASSERT_TYPE(PilotAction, brake, double);
EF_PARITY_ASSERT_TYPE(PilotAction, brake_left, bool);
EF_PARITY_ASSERT_TYPE(PilotAction, brake_right, bool);
EF_PARITY_ASSERT_TYPE(WorldEntityRef, world_index, std::uint64_t);
EF_PARITY_ASSERT_TYPE(WorldEntityRef, entity_id, std::uint64_t);
EF_PARITY_ASSERT_TYPE(WorldEntityKinematics, x, double);
EF_PARITY_ASSERT_TYPE(WorldEntityKinematics, y, double);
EF_PARITY_ASSERT_TYPE(WorldEntityKinematics, z, double);
EF_PARITY_ASSERT_TYPE(WorldEntityKinematics, vx, double);
EF_PARITY_ASSERT_TYPE(WorldEntityKinematics, vy, double);
EF_PARITY_ASSERT_TYPE(WorldEntityKinematics, vz, double);
EF_PARITY_ASSERT_TYPE(WorldEntityKinematics, heading, double);
EF_PARITY_ASSERT_TYPE(WorldEntityKinematics, pitch, double);
EF_PARITY_ASSERT_TYPE(WorldEntityKinematics, roll, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, alt_baro_m, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, alt_radar_m, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, ias_mps, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, mach, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, vvi_mps, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, pitch_deg, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, roll_deg, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, heading_deg, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, aoa_deg, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, beta_deg, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, g_load_normal, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, g_load_axial, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, p_deg_s, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, q_deg_s, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, r_deg_s, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, engine_rpm_pct, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, fuel_flow_kg_h, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, throttle_pos, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, fuel_internal_kg, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, fuel_external_kg, double);
EF_PARITY_ASSERT_TYPE(InstrumentState, gear_pos, float);
EF_PARITY_ASSERT_TYPE(InstrumentState, flaps_pos, float);
EF_PARITY_ASSERT_TYPE(InstrumentState, speedbrake_pos, float);
EF_PARITY_ASSERT_TYPE(AgentObservation, id, std::uint64_t);
EF_PARITY_ASSERT_TYPE(AgentObservation, sim_time, double);
EF_PARITY_ASSERT_TYPE(AgentObservation, x, double);
EF_PARITY_ASSERT_TYPE(AgentObservation, y, double);
EF_PARITY_ASSERT_TYPE(AgentObservation, z, double);
EF_PARITY_ASSERT_TYPE(AgentObservation, vx, double);
EF_PARITY_ASSERT_TYPE(AgentObservation, vy, double);
EF_PARITY_ASSERT_TYPE(AgentObservation, vz, double);
EF_PARITY_ASSERT_TYPE(AgentObservation, heading, double);
EF_PARITY_ASSERT_TYPE(AgentObservation, pitch, double);
EF_PARITY_ASSERT_TYPE(AgentObservation, roll, double);
EF_PARITY_ASSERT_TYPE(AgentObservation, speed, double);
EF_PARITY_ASSERT_TYPE(AgentObservation, health, double);
EF_PARITY_ASSERT_TYPE(AgentObservation, gear_state, double);
EF_PARITY_ASSERT_TYPE(AgentObservation, throttle, double);
EF_PARITY_ASSERT_TYPE(AgentObservation, total_reward, double);
EF_PARITY_ASSERT_TYPE(RewardTerm, name, std::string);
EF_PARITY_ASSERT_TYPE(RewardTerm, value, double);
EF_PARITY_ASSERT_TYPE(RewardTerm, term_owner, std::string);
EF_PARITY_ASSERT_TYPE(RewardReport, fact_terms, std::vector<RewardTerm>);
EF_PARITY_ASSERT_TYPE(RewardReport, shaping_terms, std::vector<RewardTerm>);
EF_PARITY_ASSERT_TYPE(RewardReport, fact_snapshot_version, std::uint64_t);
EF_PARITY_ASSERT_TYPE(TerminationSpec, reason, std::string);
EF_PARITY_ASSERT_TYPE(TerminationSpec, reason_source, std::string);
EF_PARITY_ASSERT_TYPE(TerminationSpec, snapshot_version, std::uint64_t);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::DeviceClockContract, tick, std::uint64_t);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::DeviceClockContract, simulation_time_s, double);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::ShardVersionContract, shard_id, std::string);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::ShardVersionContract, version, std::uint64_t);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::SnapshotLineageContract, source_snapshot_version,
                      std::uint64_t);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::SnapshotLineageContract, source_backend_id,
                      std::string);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::SnapshotLineageContract, source_request_id,
                      std::string);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::SnapshotIdentityContract, world_id, std::uint64_t);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::SnapshotIdentityContract, global_version,
                      std::uint64_t);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::SnapshotIdentityContract, barrier_id, std::string);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::SnapshotIdentityContract, barrier_sequence,
                      std::uint64_t);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::SnapshotIdentityContract, shard_versions,
                      std::vector<runtime::cuda_resident::ShardVersionContract>);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::SnapshotIdentityContract, lineage,
                      runtime::cuda_resident::SnapshotLineageContract);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::EventOrderKeyContract, timestamp, double);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::EventOrderKeyContract, priority, int);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::EventOrderKeyContract, event_id, std::uint64_t);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::EventOrderKeyContract, event_family_membership,
                      std::string);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::ExportEnvelopeContract, schema_version, std::string);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::ExportEnvelopeContract, field_set,
                      std::vector<std::string>);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::ExportEnvelopeContract, visibility_label,
                      std::string);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::ExportEnvelopeContract, provenance, std::string);
EF_PARITY_ASSERT_TYPE(runtime::cuda_resident::ExportEnvelopeContract, source_snapshot_version,
                      std::uint64_t);

#undef EF_PARITY_ASSERT_TYPE

runtime::parity::ParityBudgetSelectedField
expected_current_field(std::string field_path, std::string surface_owner,
                       runtime::parity::ParityBudgetValueKind value_kind, std::string shard) {
    return {
        .field_path = std::move(field_path),
        .surface_owner = std::move(surface_owner),
        .surface_status = runtime::parity::ParityBudgetSurfaceStatus::current_dto,
        .value_kind = value_kind,
        .shard = std::move(shard),
    };
}

runtime::parity::ParityBudgetSelectedField
expected_future_field(std::string field_path, std::string surface_owner,
                      runtime::parity::ParityBudgetValueKind value_kind, std::string shard) {
    return {
        .field_path = std::move(field_path),
        .surface_owner = std::move(surface_owner),
        .surface_status = runtime::parity::ParityBudgetSurfaceStatus::future_frozen_contract,
        .value_kind = value_kind,
        .shard = std::move(shard),
    };
}

TEST_CASE("bounded air manifest is valid and excludes broad capabilities") {
    using namespace runtime::cuda_resident;

    const CapabilityManifest &manifest = bounded_air_execution_manifest();
    const CapabilityManifestValidationResult validation = validate_capability_manifest(manifest);

    CHECK(validation.valid);
    CHECK(manifest.fixed_step_only);
    CHECK_FALSE(manifest.dynamic_entity_families);
    CHECK_FALSE(manifest.implicit_cpu_fallback);
    CHECK(contains(manifest.supported_feature_ids, kFeaturePilotFlightControls));
    CHECK(contains(manifest.supported_feature_ids, kFeatureAirframeDynamics));
    CHECK_FALSE(contains(manifest.supported_feature_ids, "sensors"));
    CHECK_FALSE(contains(manifest.supported_feature_ids, "weapons_and_effects"));
    CHECK(manifest.required_feature_ids == bounded_air_execution_required_feature_contract());
    CHECK(manifest.supported_feature_ids == bounded_air_execution_supported_feature_contract());
    CHECK(manifest.forbidden_feature_ids == bounded_air_execution_forbidden_feature_contract());

    CapabilityManifest fallback_manifest = manifest;
    fallback_manifest.implicit_cpu_fallback = true;
    CHECK_FALSE(validate_capability_manifest(fallback_manifest).valid);

    CapabilityManifest expanded_manifest = manifest;
    const auto communications =
        std::find(expanded_manifest.forbidden_feature_ids.begin(),
                  expanded_manifest.forbidden_feature_ids.end(), "communications");
    REQUIRE(communications != expanded_manifest.forbidden_feature_ids.end());
    expanded_manifest.forbidden_feature_ids.erase(communications);
    expanded_manifest.supported_feature_ids.push_back("communications");
    CHECK_FALSE(validate_capability_manifest(expanded_manifest).valid);
}

TEST_CASE(
    "CUDA resident candidate admission requires compiled backend and exact manifest support") {
    using namespace runtime::cuda_resident;

    const BackendRequest request = make_bounded_air_execution_candidate_request();

    const BackendAdmissionResult not_compiled = admit_backend_request(request, {});
    CHECK_FALSE(not_compiled.admitted);
    CHECK(not_compiled.rejection_reason ==
          kBackendAdmissionRejectionExperimentalBackendNotCompiled);

    const BackendAdmissionResult manifest_not_compiled =
        admit_backend_request(request, BackendAvailability{.compiled_experimental_backend = true});
    CHECK_FALSE(manifest_not_compiled.admitted);
    CHECK(manifest_not_compiled.rejection_reason == kBackendAdmissionRejectionManifestNotCompiled);

    const BackendAdmissionResult admitted = admit_backend_request(
        request,
        BackendAvailability{
            .compiled_experimental_backend = true,
            .supported_manifest_ids = {std::string(kCapabilityManifestIdBoundedAirExecutionV1)},
        });
    CHECK(admitted.admitted);
    CHECK(admitted.experimental_selection);
    CHECK_FALSE(admitted.maintained_selection);
    CHECK(admitted.admitted_feature_ids == request.requested_feature_ids);
}

TEST_CASE("CUDA resident candidate admission rejects missing profile and unsupported features") {
    using namespace runtime::cuda_resident;

    const BackendAdmissionResult missing = admit_backend_request({}, {});
    CHECK_FALSE(missing.admitted);
    CHECK(missing.rejection_reason == kBackendAdmissionRejectionMissingProfile);

    BackendRequest unknown = make_cpu_reference_backend_request();
    unknown.backend_profile_id = "unknown.backend";
    const BackendAdmissionResult unknown_result = admit_backend_request(unknown, {});
    CHECK_FALSE(unknown_result.admitted);
    CHECK(unknown_result.rejection_reason == kBackendAdmissionRejectionUnknownProfile);

    BackendRequest missing_manifest = make_bounded_air_execution_candidate_request();
    missing_manifest.capability_manifest_id.clear();
    const BackendAdmissionResult missing_manifest_result =
        admit_backend_request(missing_manifest, {});
    CHECK_FALSE(missing_manifest_result.admitted);
    CHECK(missing_manifest_result.rejection_reason == kBackendAdmissionRejectionMissingManifest);

    BackendRequest missing_feature = make_bounded_air_execution_candidate_request();
    missing_feature.requested_feature_ids.pop_back();
    const BackendAdmissionResult missing_feature_result =
        admit_backend_request(missing_feature, {});
    CHECK_FALSE(missing_feature_result.admitted);
    CHECK(missing_feature_result.rejection_reason ==
          kBackendAdmissionRejectionRequiredFeatureMissing);

    BackendRequest unsupported = make_bounded_air_execution_candidate_request();
    unsupported.requested_feature_ids.push_back("pilot_action.weapon_controls");
    const BackendAdmissionResult rejected = admit_backend_request(
        unsupported,
        BackendAvailability{
            .compiled_experimental_backend = true,
            .supported_manifest_ids = {std::string(kCapabilityManifestIdBoundedAirExecutionV1)},
        });
    CHECK_FALSE(rejected.admitted);
    CHECK(rejected.rejection_reason == kBackendAdmissionRejectionUnsupportedFeature);
}

TEST_CASE("parity budget freezes exact selected-slice inventory and typed comparators") {
    using namespace runtime::parity;

    const ParityBudgetRecord budget = make_resident_state_unmaintained_candidate_budget();
    const ParityBudgetValidationResult validation = validate_parity_budget_record_contract(budget);

    CHECK(validation.valid);
    CHECK_FALSE(validation.accepted_for_maintained_use);
    CHECK(budget.selected_slice_fields.size() == 11);
    CHECK(budget.barrier_rules.size() == 5);

    using enum ParityBudgetValueKind;
    std::vector<std::string> actual_family_names;
    std::vector<ParityBudgetSelectedField> actual_fields;
    for (const ParityBudgetSelectedFieldFamily &family : budget.selected_slice_fields) {
        actual_family_names.push_back(family.field_family);
        for (const ParityBudgetSelectedField &field : family.selected_fields) {
            actual_fields.push_back(field);
        }
    }
    const std::vector<std::string> expected_family_names = {
        "input_identity",
        "pilot_flight_controls",
        "world_identity_clock_and_versions",
        "airframe_kinematics",
        "air_execution_instruments",
        "agent_observation_identity",
        "agent_observation_numeric",
        "reward_numeric",
        "reward_termination_identity",
        "exact_event_identity",
        "exact_export_envelope",
    };
    const std::vector<ParityBudgetSelectedField> expected_fields = {
        expected_current_field("pilot_action.world_index", "WorldPilotActionAssignment",
                               unsigned_integer, "identity"),
        expected_current_field("pilot_action.entity_id", "WorldPilotActionAssignment",
                               unsigned_integer, "identity"),
        expected_current_field("pilot_action.action.active", "PilotAction", boolean,
                               "pilot_flight_controls"),
        expected_current_field("pilot_action.action.stick_pitch", "PilotAction", float64,
                               "pilot_flight_controls"),
        expected_current_field("pilot_action.action.stick_roll", "PilotAction", float64,
                               "pilot_flight_controls"),
        expected_current_field("pilot_action.action.rudder", "PilotAction", float64,
                               "pilot_flight_controls"),
        expected_current_field("pilot_action.action.throttle", "PilotAction", float64,
                               "pilot_flight_controls"),
        expected_current_field("pilot_action.action.gear_handle", "PilotAction", float32,
                               "pilot_flight_controls"),
        expected_current_field("pilot_action.action.flaps", "PilotAction", float32,
                               "pilot_flight_controls"),
        expected_current_field("pilot_action.action.speedbrake", "PilotAction", float32,
                               "pilot_flight_controls"),
        expected_current_field("pilot_action.action.brake", "PilotAction", float64,
                               "pilot_flight_controls"),
        expected_current_field("pilot_action.action.brake_left", "PilotAction", boolean,
                               "pilot_flight_controls"),
        expected_current_field("pilot_action.action.brake_right", "PilotAction", boolean,
                               "pilot_flight_controls"),
        expected_current_field("entity_ref.world_index", "WorldEntityRef", unsigned_integer,
                               "identity"),
        expected_current_field("entity_ref.entity_id", "WorldEntityRef", unsigned_integer,
                               "identity"),
        expected_future_field("clock.tick", "DeviceClockContract", unsigned_integer, "clock"),
        expected_future_field("clock.simulation_time_s", "DeviceClockContract", float64, "clock"),
        expected_future_field("snapshot.world_id", "SnapshotIdentityContract", unsigned_integer,
                              "snapshot"),
        expected_future_field("snapshot.global_version", "SnapshotIdentityContract",
                              unsigned_integer, "snapshot"),
        expected_future_field("snapshot.barrier_id", "SnapshotIdentityContract", string,
                              "snapshot"),
        expected_future_field("snapshot.barrier_sequence", "SnapshotIdentityContract",
                              unsigned_integer, "snapshot"),
        expected_future_field("snapshot.shard_versions", "SnapshotIdentityContract", structured,
                              "snapshot"),
        expected_future_field("snapshot.lineage", "SnapshotIdentityContract", structured,
                              "snapshot"),
        expected_current_field("kinematics.x", "WorldEntityKinematics", float64, "kinematics"),
        expected_current_field("kinematics.y", "WorldEntityKinematics", float64, "kinematics"),
        expected_current_field("kinematics.z", "WorldEntityKinematics", float64, "kinematics"),
        expected_current_field("kinematics.vx", "WorldEntityKinematics", float64, "kinematics"),
        expected_current_field("kinematics.vy", "WorldEntityKinematics", float64, "kinematics"),
        expected_current_field("kinematics.vz", "WorldEntityKinematics", float64, "kinematics"),
        expected_current_field("kinematics.heading", "WorldEntityKinematics", float64,
                               "kinematics"),
        expected_current_field("kinematics.pitch", "WorldEntityKinematics", float64, "kinematics"),
        expected_current_field("kinematics.roll", "WorldEntityKinematics", float64, "kinematics"),
        expected_current_field("instrument.alt_baro_m", "InstrumentState", float64, "instrument"),
        expected_current_field("instrument.alt_radar_m", "InstrumentState", float64, "instrument"),
        expected_current_field("instrument.ias_mps", "InstrumentState", float64, "instrument"),
        expected_current_field("instrument.mach", "InstrumentState", float64, "instrument"),
        expected_current_field("instrument.vvi_mps", "InstrumentState", float64, "instrument"),
        expected_current_field("instrument.pitch_deg", "InstrumentState", float64, "instrument"),
        expected_current_field("instrument.roll_deg", "InstrumentState", float64, "instrument"),
        expected_current_field("instrument.heading_deg", "InstrumentState", float64, "instrument"),
        expected_current_field("instrument.aoa_deg", "InstrumentState", float64, "instrument"),
        expected_current_field("instrument.beta_deg", "InstrumentState", float64, "instrument"),
        expected_current_field("instrument.g_load_normal", "InstrumentState", float64,
                               "instrument"),
        expected_current_field("instrument.g_load_axial", "InstrumentState", float64, "instrument"),
        expected_current_field("instrument.p_deg_s", "InstrumentState", float64, "instrument"),
        expected_current_field("instrument.q_deg_s", "InstrumentState", float64, "instrument"),
        expected_current_field("instrument.r_deg_s", "InstrumentState", float64, "instrument"),
        expected_current_field("instrument.engine_rpm_pct", "InstrumentState", float64,
                               "instrument"),
        expected_current_field("instrument.fuel_flow_kg_h", "InstrumentState", float64,
                               "instrument"),
        expected_current_field("instrument.throttle_pos", "InstrumentState", float64, "instrument"),
        expected_current_field("instrument.fuel_internal_kg", "InstrumentState", float64,
                               "instrument"),
        expected_current_field("instrument.fuel_external_kg", "InstrumentState", float64,
                               "instrument"),
        expected_current_field("instrument.gear_pos", "InstrumentState", float32, "instrument"),
        expected_current_field("instrument.flaps_pos", "InstrumentState", float32, "instrument"),
        expected_current_field("instrument.speedbrake_pos", "InstrumentState", float32,
                               "instrument"),
        expected_current_field("observation.id", "AgentObservation", unsigned_integer,
                               "observation"),
        expected_current_field("observation.sim_time", "AgentObservation", float64, "observation"),
        expected_current_field("observation.x", "AgentObservation", float64, "observation"),
        expected_current_field("observation.y", "AgentObservation", float64, "observation"),
        expected_current_field("observation.z", "AgentObservation", float64, "observation"),
        expected_current_field("observation.vx", "AgentObservation", float64, "observation"),
        expected_current_field("observation.vy", "AgentObservation", float64, "observation"),
        expected_current_field("observation.vz", "AgentObservation", float64, "observation"),
        expected_current_field("observation.heading", "AgentObservation", float64, "observation"),
        expected_current_field("observation.pitch", "AgentObservation", float64, "observation"),
        expected_current_field("observation.roll", "AgentObservation", float64, "observation"),
        expected_current_field("observation.speed", "AgentObservation", float64, "observation"),
        expected_current_field("observation.health", "AgentObservation", float64, "observation"),
        expected_current_field("observation.gear_state", "AgentObservation", float64,
                               "observation"),
        expected_current_field("observation.throttle", "AgentObservation", float64, "observation"),
        expected_current_field("observation.total_reward", "AgentObservation", float64,
                               "observation"),
        expected_current_field("reward_report.fact_terms[].value", "RewardTerm", float64, "reward"),
        expected_current_field("reward_report.shaping_terms[].value", "RewardTerm", float64,
                               "reward"),
        expected_current_field("reward_report.fact_terms[].name", "RewardTerm", string, "reward"),
        expected_current_field("reward_report.fact_terms[].term_owner", "RewardTerm", string,
                               "reward"),
        expected_current_field("reward_report.shaping_terms[].name", "RewardTerm", string,
                               "reward"),
        expected_current_field("reward_report.shaping_terms[].term_owner", "RewardTerm", string,
                               "reward"),
        expected_current_field("reward_report.fact_snapshot_version", "RewardReport",
                               unsigned_integer, "reward"),
        expected_current_field("termination_spec.reason", "TerminationSpec", string, "termination"),
        expected_current_field("termination_spec.reason_source", "TerminationSpec", string,
                               "termination"),
        expected_current_field("termination_spec.snapshot_version", "TerminationSpec",
                               unsigned_integer, "termination"),
        expected_future_field("events.timestamp", "EventOrderKeyContract", float64, "events"),
        expected_future_field("events.priority", "EventOrderKeyContract", signed_integer, "events"),
        expected_future_field("events.event_id", "EventOrderKeyContract", unsigned_integer,
                              "events"),
        expected_future_field("events.event_family_membership", "EventOrderKeyContract", string,
                              "events"),
        expected_future_field("export.schema_version", "ExportEnvelopeContract", string,
                              "export_envelope"),
        expected_future_field("export.field_set", "ExportEnvelopeContract", structured,
                              "export_envelope"),
        expected_future_field("export.visibility_label", "ExportEnvelopeContract", string,
                              "export_envelope"),
        expected_future_field("export.provenance", "ExportEnvelopeContract", string,
                              "export_envelope"),
        expected_future_field("export.source_snapshot_version", "ExportEnvelopeContract",
                              unsigned_integer, "export_envelope"),
    };
    CHECK(actual_family_names == expected_family_names);
    CHECK(actual_fields.size() == 90);
    CHECK(actual_fields == expected_fields);
    CHECK(budget.snapshot_versions.identity_fields ==
          std::vector<std::string>{"world_id", "global_version", "barrier_id", "barrier_sequence",
                                   "shard_versions", "lineage"});

    const auto observation_identity =
        std::find_if(budget.selected_slice_fields.begin(), budget.selected_slice_fields.end(),
                     [](const ParityBudgetSelectedFieldFamily &family) {
                         return family.field_family == "agent_observation_identity";
                     });
    REQUIRE(observation_identity != budget.selected_slice_fields.end());
    REQUIRE(observation_identity->selected_fields.size() == 1);
    CHECK(observation_identity->comparator == kParityComparatorExact);
    CHECK(observation_identity->selected_fields.front().field_path == "observation.id");
    CHECK(observation_identity->selected_fields.front().value_kind ==
          ParityBudgetValueKind::unsigned_integer);

    for (const ParityBudgetSelectedFieldFamily &family : budget.selected_slice_fields) {
        if (family.comparator != kParityComparatorAbsoluteOrRelative) {
            continue;
        }
        for (const ParityBudgetSelectedField &field : family.selected_fields) {
            CHECK((field.value_kind == ParityBudgetValueKind::float32 ||
                   field.value_kind == ParityBudgetValueKind::float64));
        }
    }

    ParityBudgetRecord renamed_field = budget;
    renamed_field.selected_slice_fields.front().selected_fields.front().field_path = "nonsense";
    CHECK_FALSE(validate_parity_budget_record_contract(renamed_field).valid);

    ParityBudgetRecord deleted_field = budget;
    deleted_field.selected_slice_fields.at(4).selected_fields.pop_back();
    CHECK_FALSE(validate_parity_budget_record_contract(deleted_field).valid);

    ParityBudgetRecord wrong_owner = budget;
    wrong_owner.selected_slice_fields.at(4).selected_fields.front().surface_owner =
        "AgentObservation";
    CHECK_FALSE(validate_parity_budget_record_contract(wrong_owner).valid);
}

TEST_CASE("parity budget freezes barrier visibility host truth and export-only surfaces") {
    using namespace runtime::parity;

    const ParityBudgetRecord budget = make_resident_state_unmaintained_candidate_budget();
    CHECK(budget.sync_barriers == resident_candidate_sync_barrier_contract());

    const auto find_rule = [&budget](const std::string &barrier_id) {
        return std::find_if(budget.barrier_rules.begin(), budget.barrier_rules.end(),
                            [&barrier_id](const ParityBudgetBarrierRule &rule) {
                                return rule.barrier_id == barrier_id;
                            });
    };
    const auto partial_sync = find_rule("partial_sync_commit");
    const auto window_commit = find_rule("window_commit");
    const auto export_rule = find_rule("export");
    REQUIRE(partial_sync != budget.barrier_rules.end());
    REQUIRE(window_commit != budget.barrier_rules.end());
    REQUIRE(export_rule != budget.barrier_rules.end());
    CHECK_FALSE(partial_sync->enabled);
    CHECK_FALSE(partial_sync->host_truth_available);
    CHECK_FALSE(contains_value(window_commit->visible_shards, "events"));
    CHECK_FALSE(contains_value(window_commit->visible_shards, "export_envelope"));
    CHECK(contains_value(export_rule->visible_shards, "events"));
    CHECK(contains_value(export_rule->visible_shards, "export_envelope"));

    for (std::string_view family_name : {"exact_event_identity", "exact_export_envelope"}) {
        const auto family =
            std::find_if(budget.selected_slice_fields.begin(), budget.selected_slice_fields.end(),
                         [&family_name](const ParityBudgetSelectedFieldFamily &candidate) {
                             return candidate.field_family == family_name;
                         });
        REQUIRE(family != budget.selected_slice_fields.end());
        CHECK(family->comparison_barriers == std::vector<std::string>{"export"});
        for (const ParityBudgetSelectedField &field : family->selected_fields) {
            CHECK(field.surface_status == ParityBudgetSurfaceStatus::future_frozen_contract);
        }
    }

    ParityBudgetRecord invalid_partial_sync = budget;
    const auto invalid_rule = std::find_if(invalid_partial_sync.barrier_rules.begin(),
                                           invalid_partial_sync.barrier_rules.end(),
                                           [](const ParityBudgetBarrierRule &rule) {
                                               return rule.barrier_id == "partial_sync_commit";
                                           });
    REQUIRE(invalid_rule != invalid_partial_sync.barrier_rules.end());
    invalid_rule->enabled = true;
    CHECK_FALSE(validate_parity_budget_record_contract(invalid_partial_sync).valid);

    ParityBudgetRecord disabled_window = budget;
    const auto disabled_window_rule = std::find_if(
        disabled_window.barrier_rules.begin(), disabled_window.barrier_rules.end(),
        [](const ParityBudgetBarrierRule &rule) { return rule.barrier_id == "window_commit"; });
    REQUIRE(disabled_window_rule != disabled_window.barrier_rules.end());
    disabled_window_rule->enabled = false;
    CHECK_FALSE(validate_parity_budget_record_contract(disabled_window).valid);

    ParityBudgetRecord stage_host_truth = budget;
    const auto stage_publish = std::find_if(
        stage_host_truth.barrier_rules.begin(), stage_host_truth.barrier_rules.end(),
        [](const ParityBudgetBarrierRule &rule) { return rule.barrier_id == "stage_publish"; });
    REQUIRE(stage_publish != stage_host_truth.barrier_rules.end());
    stage_publish->host_truth_available = true;
    CHECK_FALSE(validate_parity_budget_record_contract(stage_host_truth).valid);
}

TEST_CASE("RuntimeFacade keeps CPU default and candidate selection fail closed") {
    RuntimeBatchConfig config{};
    CHECK(config.world_count == 0);
    CHECK(config.worker_threads == 1);

    RuntimeFacade facade(config);
    const RuntimeCapabilities capabilities = facade.capabilities();
    CHECK_FALSE(capabilities.supports_resident_state);
    CHECK_FALSE(capabilities.supports_exact_gpu_backend);
    CHECK_FALSE(capabilities.supports_device_observation_view);

    const auto cpu_request = runtime::cuda_resident::make_cpu_reference_backend_request();
    const RuntimeBackendAdmission cpu = facade.admit_backend_request(RuntimeBackendRequest{
        .backend_profile_id = cpu_request.backend_profile_id,
        .capability_manifest_id = cpu_request.capability_manifest_id,
        .parity_budget_ref = cpu_request.parity_budget_ref,
        .requested_feature_ids = cpu_request.requested_feature_ids,
        .allow_unmaintained_candidate = cpu_request.allow_unmaintained_candidate,
    });
    CHECK(cpu.admitted);
    CHECK(cpu.maintained_selection);

    const auto candidate_request =
        runtime::cuda_resident::make_bounded_air_execution_candidate_request();
    const RuntimeBackendAdmission candidate = facade.admit_backend_request(RuntimeBackendRequest{
        .backend_profile_id = candidate_request.backend_profile_id,
        .capability_manifest_id = candidate_request.capability_manifest_id,
        .parity_budget_ref = candidate_request.parity_budget_ref,
        .requested_feature_ids = candidate_request.requested_feature_ids,
        .allow_unmaintained_candidate = candidate_request.allow_unmaintained_candidate,
    });
    CHECK_FALSE(candidate.admitted);
    CHECK(candidate.rejection_reason ==
          runtime::cuda_resident::kBackendAdmissionRejectionExperimentalBackendNotCompiled);
}
