#include "runtime/facade/runtime_facade.h"

#include "runtime/contracts/counterfactual_replay_contracts.h"

#include <doctest/doctest.h>

#include <cmath>
#include <limits>
#include <string>
#include <type_traits>

// T10 slice 5: contract gates for the maintained-run replay-envelope producer
// (RuntimeFacade::build_maintained_replay_envelope). These cases pin the
// assembly and fail-closed contract over identity-backed RuntimeWindowResult
// inputs whose individual evidence fields are adjusted for precise gate
// control.  Each positive fixture still originates at RuntimeFacade::run_window
// so it carries the opaque facade/window association; the dedicated negative
// cases below prove that a hand-built or foreign result cannot borrow numeric
// ids to enter the producer. The real-run end-to-end proof -- actual scenario, actual maintained
// windows, real exported packets, over the I59 opt-in adapter path -- lives in
// tests/runtime/engagement/test_maintained_replay_envelope.py, which also pins
// the adapter seam's opt-in contract and the unchanged default path.
namespace {

using runtime::counterfactual::MaintainedReplayEnvelopeResult;

static_assert(std::is_aggregate_v<RuntimeWindowResult>,
              "RuntimeWindowResult must preserve aggregate/designated initialization");

// A window-result shape equivalent to what one maintained opt-in window
// produces: real-format provenance strings on the observation packet, minted
// trace ids on the engagement packet, a window_commit barrier record, and the
// manifest-stamped export node id.
RuntimeWindowResult minted_window_result(RuntimeFacade &facade, std::uint64_t anchor_trace_id) {
    RuntimeWindowResult window_result = facade.run_window(RuntimeWindowRequest{});
    window_result.context.source_time_s = 12.5;
    window_result.observation_packet.snapshot_version = 1;
    window_result.observation_packet.provenance.observation_packet_ids = {"obs:1"};
    window_result.observation_packet.provenance.source_observation_versions = {"global:1"};
    window_result.engagement_packet.trace_ids = {anchor_trace_id};
    window_result.engagement_packet.producer_node_id = "observation_export.v1";
    window_result.barrier_trace.push_back(RuntimeWindowBarrierRecord{
        .sequence = 2,
        .barrier_id = "input_injection",
    });
    window_result.barrier_trace.push_back(RuntimeWindowBarrierRecord{
        .sequence = 3,
        .barrier_id = "window_commit",
    });
    window_result.barrier_trace.push_back(RuntimeWindowBarrierRecord{
        .sequence = 4,
        .barrier_id = "export",
    });
    return window_result;
}

} // namespace

TEST_SUITE("runtime_facade_maintained_replay_envelope") {

    TEST_CASE("runtime window result preserves designated aggregate initialization") {
        const RuntimeWindowResult result{.context = {}};
        CHECK(result.context.window_id.empty());
    }

    TEST_CASE("minted window evidence assembles an admitted validated envelope field by field") {
        RuntimeFacade facade(0);
        const std::uint64_t minted = facade.allocate_trace_id();
        CHECK(minted == 1);
        const RuntimeWindowResult window_result = minted_window_result(facade, minted);

        const MaintainedReplayEnvelopeResult result = facade.build_maintained_replay_envelope(
            window_result, "run:cpp", "episode:cpp", 424242);

        REQUIRE(result.admitted);
        CHECK(result.rejection_reason.empty());
        CHECK(result.errors.empty());

        // Identity: namespaced envelope id plus the caller-owned run identity.
        CHECK(result.envelope.replay_envelope_id == "replay:maintained:run:cpp:trace:1");
        CHECK(result.envelope.run_id == "run:cpp");
        CHECK(result.envelope.episode_id == "episode:cpp");
        CHECK(result.envelope.has_deterministic_seed);
        CHECK(result.envelope.deterministic_seed == 424242);

        // Every evidence field maps to the window product it came from.
        CHECK(result.envelope.has_source_time);
        CHECK(result.envelope.source_time_s == window_result.context.source_time_s);
        CHECK(result.envelope.snapshot_ref.snapshot_version_ref ==
              window_result.observation_packet.provenance.source_observation_versions.front());
        CHECK(result.envelope.barrier_ref.barrier_id == "window_commit");
        CHECK(result.envelope.barrier_ref.barrier_sequence == 3);
        CHECK(result.envelope.barrier_ref.barrier_detail ==
              window_result.engagement_packet.barrier_detail);
        CHECK(result.envelope.event_order_ref.sort_key == "timestamp_priority_event_id");
        CHECK(result.envelope.event_order_ref.event_id == "event:trace:1");
        CHECK(result.envelope.event_order_ref.producer_node_id ==
              window_result.engagement_packet.producer_node_id);
        CHECK(result.envelope.facade_provenance_ref.packet_ref ==
              window_result.observation_packet.provenance.observation_packet_ids.front());
        CHECK(result.envelope.facade_provenance_ref.packet_kind == "ObservationBatchPacket");
        CHECK(
            result.envelope.facade_provenance_ref.information_state_source.observation_packet_ids ==
            window_result.observation_packet.provenance.observation_packet_ids);
        CHECK(result.envelope.facade_provenance_ref.information_state_source.source_label ==
              window_result.observation_packet.provenance.source_label);

        // Honest restore claim for the maintained window path.
        CHECK_FALSE(result.envelope.snapshot_restore_supported);
        CHECK(result.envelope.restore_support_boundary ==
              "restore_unsupported_until_snapshot_restore_proof");

        // The assembled envelope passes the fail-closed WP15 validator.
        const auto validation = runtime::counterfactual::validate_replay_envelope(result.envelope);
        CHECK(validation.valid);
        CHECK(validation.errors.empty());

        // Evidence refs: producer label first, then the canonical ordered refs.
        REQUIRE(result.evidence_refs.size() == 5);
        CHECK(result.evidence_refs[0] == "RuntimeFacade.build_maintained_replay_envelope");
        CHECK(result.evidence_refs[1] == "snapshot_version_ref=global:1");
        CHECK(result.evidence_refs[2] == "barrier_id=window_commit");
        CHECK(result.evidence_refs[3] == "event_order_ref=event:trace:1");
        CHECK(result.evidence_refs[4] == "facade_provenance_ref=obs:1");
    }

    TEST_CASE("window identity rejects a foreign facade with overlapping numeric ids") {
        RuntimeFacade first(0);
        RuntimeFacade second(0);
        const std::uint64_t first_trace = first.allocate_trace_id();
        const std::uint64_t second_trace = second.allocate_trace_id();
        CHECK(first_trace == 1);
        CHECK(second_trace == 1);

        const RuntimeWindowResult first_window = minted_window_result(first, first_trace);
        const RuntimeWindowResult second_window = minted_window_result(second, second_trace);

        // Both facades deliberately overlap at numeric trace id 1.  The
        // opaque run identity, not the cursor range, is the admission fact.
        const auto foreign_from_first = second.build_maintained_replay_envelope(
            first_window, "run:foreign", "episode:foreign", 7);
        CHECK_FALSE(foreign_from_first.admitted);
        CHECK(foreign_from_first.rejection_reason ==
              "maintained_replay_envelope_window_identity_not_minted_by_this_facade");

        const auto foreign_from_second = first.build_maintained_replay_envelope(
            second_window, "run:foreign", "episode:foreign", 7);
        CHECK_FALSE(foreign_from_second.admitted);
        CHECK(foreign_from_second.rejection_reason ==
              "maintained_replay_envelope_window_identity_not_minted_by_this_facade");
    }

    TEST_CASE("window identity rejects a hand-built result with copied local evidence") {
        RuntimeFacade facade(0);
        const std::uint64_t trace_id = facade.allocate_trace_id();
        REQUIRE(trace_id == 1);
        const RuntimeWindowResult real_window = minted_window_result(facade, trace_id);

        // A caller-authored DTO can copy every visible evidence field and the
        // same numeric trace id, but cannot manufacture the non-bindable token.
        RuntimeWindowResult hand_built{};
        hand_built.context.source_time_s = real_window.context.source_time_s;
        hand_built.observation_packet = real_window.observation_packet;
        hand_built.engagement_packet = real_window.engagement_packet;
        hand_built.barrier_trace = real_window.barrier_trace;
        const auto synthetic = facade.build_maintained_replay_envelope(hand_built, "run:synthetic",
                                                                       "episode:synthetic", 7);
        CHECK_FALSE(synthetic.admitted);
        CHECK(synthetic.rejection_reason == "maintained_replay_envelope_window_identity_missing");
    }

    TEST_CASE("producer is read-only and idempotent over the allocator cursors") {
        RuntimeFacade facade(0);
        (void)facade.allocate_trace_id();
        (void)facade.allocate_run_snapshot_version();
        const std::uint64_t trace_cursor = facade.peek_next_trace_id();
        const std::uint64_t snapshot_cursor = facade.peek_next_run_snapshot_version();
        const RuntimeWindowResult window_result = minted_window_result(facade, 1);

        const MaintainedReplayEnvelopeResult first = facade.build_maintained_replay_envelope(
            window_result, "run:idempotent", "episode:idempotent", 7);
        const MaintainedReplayEnvelopeResult second = facade.build_maintained_replay_envelope(
            window_result, "run:idempotent", "episode:idempotent", 7);

        REQUIRE(first.admitted);
        REQUIRE(second.admitted);
        CHECK(first.envelope.replay_envelope_id == second.envelope.replay_envelope_id);
        CHECK(first.evidence_refs == second.evidence_refs);
        // Mints nothing: both run-global cursors are exactly where they were.
        CHECK(facade.peek_next_trace_id() == trace_cursor);
        CHECK(facade.peek_next_run_snapshot_version() == snapshot_cursor);
    }

    TEST_CASE("placeholder trace ids against an untouched allocator fail closed") {
        RuntimeFacade facade(0);
        // No allocate_trace_id call: peek == 1, so the default maintained
        // path's placeholder trace_ids = [1] is provably not run-minted.
        const RuntimeWindowResult window_result = minted_window_result(facade, 1);

        const MaintainedReplayEnvelopeResult result = facade.build_maintained_replay_envelope(
            window_result, "run:placeholder", "episode:placeholder", 7);

        CHECK_FALSE(result.admitted);
        CHECK(result.rejection_reason ==
              "maintained_replay_envelope_trace_ids_not_minted_by_this_run");
        // Rejection leaks no partially assembled evidence.
        CHECK(result.envelope.replay_envelope_id.empty());
        CHECK(result.evidence_refs.empty());
    }

    TEST_CASE("trace ids at or beyond the allocator cursor fail closed") {
        RuntimeFacade facade(0);
        const std::uint64_t minted = facade.allocate_trace_id();
        RuntimeWindowResult window_result = minted_window_result(facade, minted);
        // peek is now 2; an id equal to the cursor was never handed out.
        window_result.engagement_packet.trace_ids = {minted, facade.peek_next_trace_id()};

        const MaintainedReplayEnvelopeResult result = facade.build_maintained_replay_envelope(
            window_result, "run:foreign", "episode:foreign", 7);

        CHECK_FALSE(result.admitted);
        CHECK(result.rejection_reason ==
              "maintained_replay_envelope_trace_ids_not_minted_by_this_run");
    }

    TEST_CASE("missing evidence inputs fail closed with stable named reasons") {
        RuntimeFacade facade(0);
        const std::uint64_t minted = facade.allocate_trace_id();

        SUBCASE("blank run id") {
            const auto result = facade.build_maintained_replay_envelope(
                minted_window_result(facade, minted), "  ", "episode:x", 7);
            CHECK_FALSE(result.admitted);
            CHECK(result.rejection_reason == "maintained_replay_envelope_run_id_required");
        }
        SUBCASE("blank episode id") {
            const auto result = facade.build_maintained_replay_envelope(
                minted_window_result(facade, minted), "run:x", "", 7);
            CHECK_FALSE(result.admitted);
            CHECK(result.rejection_reason == "maintained_replay_envelope_episode_id_required");
        }
        SUBCASE("missing observation packet provenance") {
            RuntimeWindowResult window_result = minted_window_result(facade, minted);
            window_result.observation_packet.provenance.observation_packet_ids.clear();
            const auto result =
                facade.build_maintained_replay_envelope(window_result, "run:x", "episode:x", 7);
            CHECK_FALSE(result.admitted);
            CHECK(result.rejection_reason ==
                  "maintained_replay_envelope_observation_packet_provenance_missing");
        }
        SUBCASE("missing engagement trace ids") {
            RuntimeWindowResult window_result = minted_window_result(facade, minted);
            window_result.engagement_packet.trace_ids.clear();
            const auto result =
                facade.build_maintained_replay_envelope(window_result, "run:x", "episode:x", 7);
            CHECK_FALSE(result.admitted);
            CHECK(result.rejection_reason ==
                  "maintained_replay_envelope_engagement_trace_ids_missing");
        }
        SUBCASE("missing window_commit barrier record") {
            RuntimeWindowResult window_result = minted_window_result(facade, minted);
            window_result.barrier_trace.clear();
            window_result.barrier_trace.push_back(RuntimeWindowBarrierRecord{
                .sequence = 1,
                .barrier_id = "export",
            });
            const auto result =
                facade.build_maintained_replay_envelope(window_result, "run:x", "episode:x", 7);
            CHECK_FALSE(result.admitted);
            CHECK(result.rejection_reason ==
                  "maintained_replay_envelope_window_commit_barrier_missing");
        }
        SUBCASE("missing engagement producer node") {
            RuntimeWindowResult window_result = minted_window_result(facade, minted);
            window_result.engagement_packet.producer_node_id.clear();
            const auto result =
                facade.build_maintained_replay_envelope(window_result, "run:x", "episode:x", 7);
            CHECK_FALSE(result.admitted);
            CHECK(result.rejection_reason ==
                  "maintained_replay_envelope_engagement_producer_node_missing");
        }
        SUBCASE("non-finite window source time") {
            RuntimeWindowResult window_result = minted_window_result(facade, minted);
            window_result.context.source_time_s = std::numeric_limits<double>::quiet_NaN();
            const auto result =
                facade.build_maintained_replay_envelope(window_result, "run:x", "episode:x", 7);
            CHECK_FALSE(result.admitted);
            CHECK(result.rejection_reason == "maintained_replay_envelope_source_time_not_finite");
        }
    }

    TEST_CASE("run-global snapshot qualification is opt-in, additive, and allocator-checked") {
        RuntimeFacade facade(0);
        const std::uint64_t minted_trace = facade.allocate_trace_id();
        const std::uint64_t minted_snapshot = facade.allocate_run_snapshot_version();
        const RuntimeWindowResult window_result = minted_window_result(facade, minted_trace);

        SUBCASE("default (0) leaves the packet's per-export string byte-identical") {
            const auto result =
                facade.build_maintained_replay_envelope(window_result, "run:va2", "episode:va2", 7);
            REQUIRE(result.admitted);
            CHECK(result.envelope.snapshot_ref.snapshot_version_ref == "global:1");
        }
        SUBCASE("opt-in qualifies additively, keeping the per-export value as the prefix") {
            const auto result = facade.build_maintained_replay_envelope(
                window_result, "run:va2", "episode:va2", 7, minted_snapshot);
            REQUIRE(result.admitted);
            CHECK(result.envelope.snapshot_ref.snapshot_version_ref == "global:1:run_snapshot:1");
            // The pre-existing field meaning survives as the exact prefix.
            CHECK(result.envelope.snapshot_ref.snapshot_version_ref.rfind("global:1", 0) == 0);
            CHECK(result.evidence_refs[1] == "snapshot_version_ref=global:1:run_snapshot:1");
        }
        SUBCASE("a version at or beyond the allocator cursor fails closed") {
            const auto result =
                facade.build_maintained_replay_envelope(window_result, "run:va2", "episode:va2", 7,
                                                        facade.peek_next_run_snapshot_version());
            CHECK_FALSE(result.admitted);
            CHECK(result.rejection_reason ==
                  "maintained_replay_envelope_run_snapshot_version_not_minted_by_this_run");
            CHECK(result.envelope.snapshot_ref.snapshot_version_ref.empty());
        }
    }
}
