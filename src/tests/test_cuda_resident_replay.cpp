#include "runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <array>
#include <cstddef>
#include <stdexcept>
#include <string>
#include <string_view>

#include "runtime/contracts/cuda_resident_observation_projection_fixture_contract.h"
#include "tests/test_cuda_resident_replay_support.h"

using namespace runtime::cuda_resident::replay::test_support;

TEST_CASE("RB8 CUDA export projection detects every envelope-field mutation") {
    using namespace runtime::cuda_resident;
    using namespace runtime::cuda_resident::replay;

    const ReplayTrace trace = make_trace();
    const ReplayLaneResult reference = run_cpu_reference(trace);
    const ProjectedWorld expected_world = project_cpu_oracle(
        trace, 0, fixed_air_fixture_entity_id(0), 0, "export", trace.windows[0].request_id);
    CudaResidentWorldSnapshot snapshot{};
    snapshot.entity_ref = expected_world.ref;
    snapshot.identity = expected_world.snapshot;

    struct MutationCase {
        std::string_view field_path;
        void (*mutate)(ExportEnvelopeContract &);
    };
    const std::array<MutationCase, 5> mutations{{
        {"export.schema_version",
         [](ExportEnvelopeContract &value) { value.schema_version += ".mutated"; }},
        {"export.field_set",
         [](ExportEnvelopeContract &value) { value.field_set.push_back("mutated"); }},
        {"export.visibility_label",
         [](ExportEnvelopeContract &value) { value.visibility_label = "mutated"; }},
        {"export.provenance",
         [](ExportEnvelopeContract &value) { value.provenance += ".mutated"; }},
        {"export.source_snapshot_version",
         [](ExportEnvelopeContract &value) { ++value.source_snapshot_version; }},
    }};

    for (const auto &mutation : mutations) {
        CAPTURE(std::string(mutation.field_path));
        ExportEnvelopeContract envelope = expected_world.envelope;
        mutation.mutate(envelope);
        const ProjectedWorld projected =
            project_cuda_snapshot(snapshot, envelope, 0, trace.windows[0].request_id);
        ReplayLaneFrame projected_frame = make_projection_frame(trace, 0, "export", {projected});
        const auto projected_field =
            std::find_if(projected_frame.fields.begin(), projected_frame.fields.end(),
                         [&](const ReplayFieldValue &field) {
                             return field.field_family == "exact_export_envelope" &&
                                    field.field_path == mutation.field_path;
                         });
        REQUIRE(projected_field != projected_frame.fields.end());

        ReplayLaneResult shadow = reference;
        shadow.lane = ReplayLaneKind::cuda_resident;
        shadow.backend_id = "synthetic.cuda_envelope_mutation";
        const auto export_frame =
            std::find_if(shadow.frames.begin(), shadow.frames.end(), [](const auto &frame) {
                return frame.window_index == 0 && frame.barrier_id == "export";
            });
        REQUIRE(export_frame != shadow.frames.end());
        const auto shadow_field =
            std::find_if(export_frame->fields.begin(), export_frame->fields.end(),
                         [&](const ReplayFieldValue &field) {
                             return field.world_index == 0 &&
                                    field.field_family == "exact_export_envelope" &&
                                    field.field_path == mutation.field_path;
                         });
        REQUIRE(shadow_field != export_frame->fields.end());
        *shadow_field = *projected_field;

        CudaResidentReplayHarness harness([&](const ReplayTrace &) { return reference; },
                                          [&](const ReplayTrace &) { return shadow; });
        const ReplayComparisonReport report = harness.run(trace);
        CHECK(report.status == ReplayRunStatus::quarantined);
        CHECK(report.coverage.mismatched_field_instances == 1);
        CHECK(std::any_of(report.mismatches.begin(), report.mismatches.end(),
                          [&](const auto &mismatch) {
                              return mismatch.field_family == "exact_export_envelope" &&
                                     mismatch.field_path == mutation.field_path &&
                                     mismatch.mismatch_code == "value_mismatch";
                          }));
    }
}

TEST_CASE("RB8 independent CPU/GPU replay consumes the frozen 93-field budget") {
    using namespace runtime::cuda_resident;
    using namespace runtime::cuda_resident::replay;
    if (!CudaWorldStore::compiled_with_cuda()) {
        CHECK(true);
        return;
    }

    const ReplayTrace trace = make_trace();
    const std::string before_signature = CudaResidentReplayHarness::trace_signature(trace);
    std::size_t reference_calls = 0;
    std::size_t shadow_calls = 0;
    CudaResidentReplayHarness harness(
        [&](const ReplayTrace &input) {
            ++reference_calls;
            return run_cpu_reference(input);
        },
        [&](const ReplayTrace &input) {
            ++shadow_calls;
            return run_cuda_resident(input);
        });

    const ReplayComparisonReport report = harness.run(trace);
    CHECK(reference_calls == 1);
    CHECK(shadow_calls == 1);
    CHECK(CudaResidentReplayHarness::trace_signature(trace) == before_signature);
    CHECK(report.parity_budget_ref ==
          std::string(runtime::parity::kParityBudgetResidentStateUnmaintainedCandidateV1));
    CHECK(report.shadow_parity_budget_ref ==
          std::string(runtime::parity::kParityBudgetShadowCompareUnmaintainedCandidateV1));
    CHECK(report.coverage.expected_selected_field_count == 93);
    CHECK(report.coverage.consumed_selected_field_count == 93);
    CHECK(report.coverage.expected_field_family_count == 11);
    CHECK(report.coverage.consumed_field_families.size() == 11);
    CHECK(report.coverage.expected_barrier_count == 3);
    CHECK(report.coverage.consumed_barriers ==
          std::vector<std::string>{"input_injection", "window_commit", "export"});
    std::size_t expected_instances = 0;
    for (const auto &family : runtime::parity::resident_candidate_selected_slice_field_contract()) {
        expected_instances += family.selected_fields.size() * family.comparison_barriers.size() *
                              trace.seeds.size() * trace.windows.size();
    }
    CHECK(report.coverage.expected_field_instances == expected_instances);
    CHECK(report.coverage.selected_field_instances == report.coverage.expected_field_instances);
    CHECK(report.coverage.available_field_instances == report.coverage.expected_field_instances);
    CHECK(report.coverage.unavailable_field_instances == 0);
    CHECK(report.complete_selected_slice);
    CHECK(report.candidate_promotion_blocked);
    CHECK_FALSE(report.maintained_claim_allowed);
    CHECK_FALSE(report.mismatches.empty());
    CHECK(report.quarantined);
    CHECK(report.first_divergence() != nullptr);
    CHECK_FALSE(report.first_divergence()->barrier_id.empty());
    CHECK_FALSE(report.first_divergence()->field_family.empty());
    CHECK_FALSE(report.first_divergence()->field_path.empty());
    CHECK_FALSE(report.mismatch_summary.empty());

    const ReplayComparisonReport rerun = harness.rerun(trace, report);
    CHECK(reference_calls == 2);
    CHECK(shadow_calls == 2);
    CHECK(rerun.deterministic);
    CHECK(rerun.stable_signature == report.stable_signature);
    CHECK(rerun.complete_selected_slice);
    CHECK(rerun.quarantined);

    ReplayTrace changed_trace = trace;
    changed_trace.run_id = "rb8.fixed_air.replay.changed";
    const ReplayComparisonReport rejected_rerun = harness.rerun(changed_trace, report);
    CHECK(rejected_rerun.status == ReplayRunStatus::rejected);
    CHECK(rejected_rerun.rejection_reason == "rerun_trace_identity_mismatch");
    CHECK(rejected_rerun.quarantined);
}

TEST_CASE("RB8 runner failure is rejected and cannot fall back") {
    using namespace runtime::cuda_resident::replay;
    const ReplayTrace trace = make_trace();
    CudaResidentReplayHarness harness(
        [](const ReplayTrace &) -> ReplayLaneResult {
            throw std::runtime_error("synthetic reference failure");
        },
        [](const ReplayTrace &input) { return run_cuda_resident(input); });
    const ReplayComparisonReport report = harness.run(trace);
    CHECK(report.status == ReplayRunStatus::rejected);
    CHECK(report.rejection_reason == "reference_runner_failed");
    CHECK(report.quarantined);
    CHECK(report.candidate_promotion_blocked);
    CHECK_FALSE(report.maintained_claim_allowed);
    CHECK(report.first_divergence() != nullptr);
    CHECK(report.first_divergence()->mismatch_code == "runner_failed");
}

TEST_CASE("RB8 malformed frame topology is rejected instead of being partially compared") {
    using namespace runtime::cuda_resident::replay;
    const ReplayTrace trace = make_trace();
    const auto malformed = [](const ReplayTrace &input, ReplayLaneKind lane) {
        return ReplayLaneResult{
            .lane = lane,
            .backend_id = replay_lane_name(lane),
            .trace_signature = CudaResidentReplayHarness::trace_signature(input),
            .completed = true,
            .failure_code = "",
            .frames = {},
        };
    };
    CudaResidentReplayHarness harness(
        [&](const ReplayTrace &input) { return malformed(input, ReplayLaneKind::cpu_reference); },
        [&](const ReplayTrace &input) { return malformed(input, ReplayLaneKind::cuda_resident); });
    const ReplayComparisonReport report = harness.run(trace);
    CHECK(report.status == ReplayRunStatus::rejected);
    CHECK(report.rejection_reason == "incomplete_selected_slice");
    CHECK(report.quarantined);
    CHECK_FALSE(report.complete_selected_slice);
    CHECK(std::any_of(report.mismatches.begin(), report.mismatches.end(), [](const auto &mismatch) {
        return mismatch.mismatch_code == "missing_frame";
    }));

    ReplayTrace forbidden_input = trace;
    forbidden_input.windows[0].actions[0].radar_active = true;
    CHECK(CudaResidentReplayHarness::trace_signature(forbidden_input) !=
          CudaResidentReplayHarness::trace_signature(trace));
}
