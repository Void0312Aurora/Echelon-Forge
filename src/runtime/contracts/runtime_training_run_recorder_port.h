#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace runtime::host::integration {

struct RuntimeTrainingWorldScopeGeneration {
    std::string scope;
    std::uint64_t generation = 0;
};

struct RuntimeTrainingWorldSnapshot {
    std::size_t world_index = 0;
    bool well_formed = false;
    std::uint64_t step = 0;
    std::string state_digest;
    std::string rng_digest;
    std::optional<std::uint32_t> episode_seed;
    std::vector<RuntimeTrainingWorldScopeGeneration> scope_generations;
};

struct RuntimeTrainingFacadeSnapshot {
    bool healthy = false;
    bool requires_host_recreate = false;
    std::uint64_t batch_generation = 0;
    std::size_t world_count = 0;
    bool evidence_available = false;
    std::string resolved_manifest_sha256;
    std::string executable_graph_sha256;
    std::string host_mode;
    std::vector<std::string> cpu_scheduler_topology_json;
    std::vector<RuntimeTrainingWorldSnapshot> worlds;
};

class RuntimeTrainingRunRecorder;

std::shared_ptr<RuntimeTrainingRunRecorder>
create_training_run_recorder(std::size_t count, const std::string &configuration);
void note_training_run_lifecycle(RuntimeTrainingRunRecorder &recorder, const char *event);
bool try_note_training_run_lifecycle(RuntimeTrainingRunRecorder &recorder, const char *event);
void capture_training_run_snapshot(RuntimeTrainingRunRecorder &recorder,
                                   const RuntimeTrainingFacadeSnapshot &snapshot,
                                   std::uint64_t facade_incarnation, bool after_step);
void fail_training_run_recorder(RuntimeTrainingRunRecorder &recorder, const std::string &reason);
bool is_training_run_recorder_terminal(const RuntimeTrainingRunRecorder &recorder) noexcept;
void prepare_finish_training_run_recorder(RuntimeTrainingRunRecorder &recorder,
                                          const RuntimeTrainingFacadeSnapshot &snapshot,
                                          std::uint64_t facade_incarnation);
void finalize_training_run_recorder(RuntimeTrainingRunRecorder &recorder);
void abort_training_run_recorder_construction(RuntimeTrainingRunRecorder &recorder,
                                              const std::string &reason);
std::string reopen_training_run_receipt(const std::string &root, const std::string &run);

} // namespace runtime::host::integration
