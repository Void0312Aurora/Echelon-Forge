#pragma once

#include <cstddef>
#include <memory>
#include <string>

#include "runtime/contracts/cuda_resident_replay_contract.h"

namespace runtime::cuda_resident::performance::probe {

struct Mode {
    bool host_snapshot = false;
    bool device_consumer = false;
    std::string id;
};

struct WindowTiming {
    double end_to_end_ms = 0.0;
    double advance_ms = 0.0;
    double collection_ms = 0.0;
};

class ProbeSession final {
  public:
    ProbeSession(const replay::ReplayTrace &trace, const std::string &database_path);
    ~ProbeSession();

    ProbeSession(const ProbeSession &) = delete;
    ProbeSession &operator=(const ProbeSession &) = delete;
    ProbeSession(ProbeSession &&) = delete;
    ProbeSession &operator=(ProbeSession &&) = delete;

    void reset_fixture();
    [[nodiscard]] WindowTiming run_window(const Mode &mode);
    [[nodiscard]] std::string state_digest() const;
    [[nodiscard]] double setup_ms() const noexcept;
    [[nodiscard]] std::size_t device_bytes() const noexcept;
    [[nodiscard]] std::size_t state_slot_bytes() const noexcept;

  private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

} // namespace runtime::cuda_resident::performance::probe
