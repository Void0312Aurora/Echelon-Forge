#pragma once

#include "runtime/facade/runtime_facade_types.h"
#include "runtime/host/runtime_run_recorder.h"

#include <cstdint>
#include <memory>
#include <string>
#include <vector>

class RuntimeFacade;

// Build-tree-only qualification owner. This is not a production entrypoint,
// installed binding, replacement facade, or additional receipt authority.
namespace runtime::host::integration {

struct RuntimeFacadeRunQualificationConfig {
    std::string run_id;
    std::string writer_id;
    std::string header_json;
    std::string receipt_template_json;
    RuntimeExecutionProvenanceSources execution_sources;
    std::uint64_t expected_steps = 3;
};

struct RuntimeFacadeRunQualificationTestAccess;

class RuntimeFacadeRunQualification final {
  public:
    RuntimeFacadeRunQualification(RuntimeRunRecorderStore &store,
                                  RuntimeFacadeRunQualificationConfig config);
    ~RuntimeFacadeRunQualification();
    RuntimeFacadeRunQualification(const RuntimeFacadeRunQualification &) = delete;
    RuntimeFacadeRunQualification &operator=(const RuntimeFacadeRunQualification &) = delete;

    // Durable admission succeeds before the first RuntimeFacade is constructed.
    [[nodiscard]] RuntimeRunRecorderStatus start();
    // Exactly one world, episode and spawned entity; no autoreset or branch API.
    [[nodiscard]] RuntimeRunRecorderStatus setup(BatchWorldSetupRequest request);
    [[nodiscard]] RuntimeRunRecorderStatus
    step(const std::vector<WorldPilotActionAssignment> &actions = {});
    // Completion is derived from the live native owner, never a caller flag.
    [[nodiscard]] RuntimeRunRecorderStatus finish();

    [[nodiscard]] bool facade_constructed() const noexcept;
    [[nodiscard]] bool facade_destroyed() const noexcept;
    [[nodiscard]] std::string evidence_json() const;

  private:
    struct State;
    std::unique_ptr<State> state_;
    RuntimeFacade &native_facade_for_test();
    friend struct RuntimeFacadeRunQualificationTestAccess;
};

} // namespace runtime::host::integration
