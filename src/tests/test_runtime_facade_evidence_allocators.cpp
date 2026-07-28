#include "runtime/facade/runtime_facade.h"

#include <doctest/doctest.h>

#include <stdexcept>
#include <utility>

// T10 slice 3 / I54-R: move-semantics regression gates for the run-global
// evidence producers (VA-2 snapshot version, VA-8 trace id). A defaulted move
// would copy the uint64 cursors, leaving the moved-from facade able to
// silently mint ids that duplicate the destination's run; these cases pin the
// repaired contract: the run identity moves with the facade and the
// moved-from source fails fast (std::logic_error) on all four producers.
// Python cannot reach this surface (nanobind holds RuntimeFacade by pointer
// and no binding returns it by value), so the regression lives here.
TEST_SUITE("runtime_facade_evidence_allocators") {

    TEST_CASE("move construction transfers the run and fail-fasts the moved-from source") {
        RuntimeFacade source(0);
        CHECK(source.allocate_run_snapshot_version() == 1);
        CHECK(source.allocate_run_snapshot_version() == 2);
        CHECK(source.allocate_trace_id() == 1);

        RuntimeFacade destination(std::move(source));

        // The run identity (both cursors) moves with the facade: the
        // destination continues exactly where the source stopped.
        CHECK(destination.peek_next_run_snapshot_version() == 3);
        CHECK(destination.allocate_run_snapshot_version() == 3);
        CHECK(destination.peek_next_trace_id() == 2);
        CHECK(destination.allocate_trace_id() == 2);

        // The moved-from source must fail fast instead of silently minting
        // ids that duplicate the destination's run.
        CHECK_THROWS_AS(source.allocate_run_snapshot_version(), std::logic_error);
        CHECK_THROWS_AS(source.peek_next_run_snapshot_version(), std::logic_error);
        CHECK_THROWS_AS(source.allocate_trace_id(), std::logic_error);
        CHECK_THROWS_AS(source.peek_next_trace_id(), std::logic_error);

        // The fail-fast probes above must not perturb the live destination.
        CHECK(destination.allocate_run_snapshot_version() == 4);
        CHECK(destination.allocate_trace_id() == 3);
    }

    TEST_CASE("move assignment adopts the source run and fail-fasts the moved-from source") {
        RuntimeFacade source(0);
        for (int i = 0; i < 5; ++i) {
            (void)source.allocate_run_snapshot_version();
        }
        (void)source.allocate_trace_id();

        RuntimeFacade target(0);
        // The target has its own younger run; move-assignment must replace it
        // with the source run (no rewind of the adopted sequence).
        (void)target.allocate_run_snapshot_version();

        target = std::move(source);

        CHECK(target.peek_next_run_snapshot_version() == 6);
        CHECK(target.allocate_run_snapshot_version() == 6);
        CHECK(target.peek_next_trace_id() == 2);
        CHECK(target.allocate_trace_id() == 2);

        // The moved-from source must not be able to rewind or duplicate the
        // run it just handed over.
        CHECK_THROWS_AS(source.allocate_run_snapshot_version(), std::logic_error);
        CHECK_THROWS_AS(source.peek_next_run_snapshot_version(), std::logic_error);
        CHECK_THROWS_AS(source.allocate_trace_id(), std::logic_error);
        CHECK_THROWS_AS(source.peek_next_trace_id(), std::logic_error);
    }

    TEST_CASE("self move assignment keeps the allocators live") {
        RuntimeFacade facade(0);
        CHECK(facade.allocate_run_snapshot_version() == 1);
        CHECK(facade.allocate_trace_id() == 1);

        RuntimeFacade &alias = facade;
        facade = std::move(alias);

        CHECK(facade.allocate_run_snapshot_version() == 2);
        CHECK(facade.allocate_trace_id() == 2);
    }
}
