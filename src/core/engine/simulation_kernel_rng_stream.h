#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <random>
#include <stdexcept>

// The kernel's reset-seeded mt19937 stream, together with the number of words drawn from it
// since the last reset or restore. State transfer exports both (`rng.v2`) and checks the
// restored position against its census entry. Every draw therefore goes through `draw_words`,
// which advances the position by exactly the number of words drawn. A draw site cannot forget
// to count, and it does not need the kernel to do so.
class SimulationKernelRngStream {
  public:
    void seed(unsigned int seed) {
        engine_.seed(seed);
        draw_position_ = 0;
    }

    // Draws N consecutive words. The position check covers all N before the first draw, so an
    // exhausted position leaves the engine untouched.
    template <std::size_t N> [[nodiscard]] std::array<std::uint64_t, N> draw_words() {
        if (N > std::numeric_limits<std::uint64_t>::max() - draw_position_) {
            throw std::overflow_error("SimulationKernel RNG draw position is exhausted");
        }
        std::array<std::uint64_t, N> words{};
        for (auto &word : words) {
            word = static_cast<std::uint64_t>(engine_());
        }
        draw_position_ += N;
        return words;
    }

    [[nodiscard]] std::uint64_t draw_position() const noexcept { return draw_position_; }
    [[nodiscard]] const std::mt19937 &engine() const noexcept { return engine_; }

    // State-transfer restore: the engine and the position are one unit of truth.
    void restore(const std::mt19937 &engine, std::uint64_t draw_position) {
        engine_ = engine;
        draw_position_ = draw_position;
    }

  private:
    std::mt19937 engine_;
    std::uint64_t draw_position_ = 0;
};
