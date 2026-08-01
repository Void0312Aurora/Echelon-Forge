#include "runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <cstddef>
#include <stdexcept>
#include <string>

#include "tests/test_cuda_resident_replay_support.h"

using namespace runtime::cuda_resident::replay::test_support;

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
        [&](const ReplayTrace &input) {
            return malformed(input, ReplayLaneKind::cpu_reference);
        },
        [&](const ReplayTrace &input) {
            return malformed(input, ReplayLaneKind::cuda_resident);
        });
    const ReplayComparisonReport report = harness.run(trace);
    CHECK(report.status == ReplayRunStatus::rejected);
    CHECK(report.rejection_reason == "incomplete_selected_slice");
    CHECK(report.quarantined);
    CHECK_FALSE(report.complete_selected_slice);
    CHECK(std::any_of(report.mismatches.begin(), report.mismatches.end(),
                      [](const auto &mismatch) {
                          return mismatch.mismatch_code == "missing_frame";
                      }));

    ReplayTrace forbidden_input = trace;
    forbidden_input.windows[0].actions[0].radar_active = true;
    CHECK(CudaResidentReplayHarness::trace_signature(forbidden_input) !=
          CudaResidentReplayHarness::trace_signature(trace));
}
