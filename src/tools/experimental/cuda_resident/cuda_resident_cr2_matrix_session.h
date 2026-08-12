#pragma once

#include <cstddef>
#include <memory>
#include <string>

#include "runtime/contracts/cuda_resident_replay_contract.h"

namespace runtime::cuda_resident::matrix::probe {

struct Mode {
    bool host_export = false;
    bool device_consumer = false;
    // CP-6: submit the learner-equivalent consumer instead of the smoke
    // consumer on the device lane. Only meaningful with device_consumer.
    bool learner_consumer = false;
    std::string id;
};

struct WindowTiming {
    double end_to_end_ms = 0.0;
    double input_evaluate_advance_ms = 0.0;
    double collection_ms = 0.0;
};

struct DrainResult {
    std::size_t receipt_count = 0;
    std::size_t materialized_count = 0;
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
    [[nodiscard]] DrainResult drain_device_consumers(bool materialize_first);
    [[nodiscard]] std::string released_state_digest() const;
    [[nodiscard]] double setup_ms() const noexcept;
    [[nodiscard]] std::size_t device_bytes() const noexcept;
    [[nodiscard]] std::size_t state_slot_bytes() const noexcept;
    [[nodiscard]] std::size_t effective_worker_threads() const noexcept;
    [[nodiscard]] std::string backend_id() const;

  private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

} // namespace runtime::cuda_resident::matrix::probe
