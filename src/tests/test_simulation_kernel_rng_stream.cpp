#include "core/engine/simulation_kernel_rng_stream.h"

#include <doctest/doctest.h>
#include <ostream>

TEST_SUITE("simulation_kernel_rng_stream") {
    TEST_CASE("seeded words retain mt19937 order and reset their position") {
        SimulationKernelRngStream stream;
        stream.seed(42);
        std::mt19937 reference(42);
        const auto words = stream.draw_words<2>();
        CHECK(words[0] == reference());
        CHECK(words[1] == reference());
        CHECK(stream.draw_position() == 2);
        const auto next = stream.draw_words<1>();
        CHECK(next[0] == reference());
        CHECK(stream.draw_position() == 3);
        stream.seed(42);
        CHECK(stream.draw_position() == 0);
        CHECK(stream.draw_words<2>() == words);
    }

    TEST_CASE("restore resumes the same engine and draw position") {
        SimulationKernelRngStream source;
        source.seed(7);
        (void)source.draw_words<3>();
        SimulationKernelRngStream target;
        target.restore(source.engine(), source.draw_position());
        CHECK(target.draw_words<2>() == source.draw_words<2>());
        CHECK(target.draw_position() == 5);
    }

    TEST_CASE("overflow rejects a whole draw batch without advancing the engine") {
        SimulationKernelRngStream stream;
        std::mt19937 reference(19);
        const auto maximum = std::numeric_limits<std::uint64_t>::max();
        stream.restore(reference, maximum - 1);
        CHECK_THROWS_AS((void)stream.draw_words<2>(), std::overflow_error);
        CHECK(stream.draw_position() == maximum - 1);
        CHECK(stream.engine() == reference);
        CHECK(stream.draw_words<0>().empty());
        CHECK(stream.draw_position() == maximum - 1);
        CHECK(stream.draw_words<1>()[0] == reference());
        CHECK(stream.draw_position() == maximum);
        const auto before = stream.engine();
        CHECK_THROWS_AS((void)stream.draw_words<1>(), std::overflow_error);
        CHECK(stream.engine() == before);
        CHECK(stream.draw_position() == maximum);
    }
}
