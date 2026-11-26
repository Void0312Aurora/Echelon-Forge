#include "runtime/contracts/runtime_training_run_recorder_port.h"

#if defined(EF_ENABLE_TRAINING_RUN_RECORDER)
#include "runtime/host/runtime_file_artifact_ledger_store.h"
#include "runtime/host/runtime_run_recorder.h"
#include "runtime/contracts/authority/runtime_authority_contract.h"
#include "runtime/contracts/composition/runtime_composition_evidence.v1.generated.h"

#include <atomic>
#include <algorithm>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <utility>
#include <vector>
#include <filesystem>
#include <fstream>
#include <map>
#include <nlohmann/json.hpp>
#include <random>
#include <set>
#include <sstream>

namespace runtime::host::integration {
namespace {
using Json = nlohmann::json;
namespace authority = runtime::authority_contracts;

struct LocalIdentity128 {
    std::uint64_t high = 0;
    std::uint64_t low = 0;
    [[nodiscard]] bool well_formed() const noexcept { return high != 0 || low != 0; }
};

struct LocalIncarnationRef {
    LocalIdentity128 host_id;
    std::uint64_t incarnation_epoch = 0;
    [[nodiscard]] bool well_formed() const noexcept {
        return host_id.well_formed() && incarnation_epoch != 0;
    }
};

struct LocalWorldRef {
    LocalIncarnationRef incarnation;
    std::size_t world_index = 0;
    std::uint64_t world_generation = 0;
    [[nodiscard]] bool well_formed() const noexcept {
        return incarnation.well_formed() && world_generation != 0;
    }
};

std::string read(const std::string &path) {
    std::ifstream file(path, std::ios::binary);
    if (!file) throw std::runtime_error("training_recorder.input_unreadable:" + path);
    std::ostringstream bytes;
    bytes << file.rdbuf();
    return bytes.str();
}
std::string canonical(const Json &value) {
    const auto bytes = authority::canonical_authority_json(value.dump());
    if (!bytes) throw std::runtime_error("training_recorder.noncanonical_input");
    return *bytes;
}
void require(const RuntimeRunRecorderStatus &status) {
    if (!status) throw std::runtime_error(status.code + ":" + status.detail);
}
LocalIdentity128 process_identity() {
    static const auto identity = [] {
        std::random_device rng;
        LocalIdentity128 value{(std::uint64_t(rng()) << 32) | rng(),
                               (std::uint64_t(rng()) << 32) | rng()};
        if (!value.well_formed()) value.low = 1U;
        return value;
    }();
    return identity;
}
std::string identity_text(LocalIdentity128 id) {
    return "boot-" + std::to_string(id.high) + "-" + std::to_string(id.low);
}
Json sorted(const std::set<std::string> &values) {
    return std::vector<std::string>(values.begin(), values.end());
}
} // namespace

class RuntimeTrainingRunRecorder final {
  public:
    Json config;
    RuntimeExecutionProvenanceSources sources;
    std::unique_ptr<RuntimeFileArtifactLedgerStore> store;
    std::unique_ptr<RuntimeRunRecorder> recorder;
    Json receipt;
    Json lock;
    Json topology;
    Json bindings = Json::array();
    Json episodes = Json::array();
    Json last_worlds = Json::array();
    LocalIncarnationRef incarnation;
    std::vector<LocalWorldRef> worlds;
    std::set<std::string> episode_ids;
    std::uint64_t steps = 0;
    std::uint64_t expected_steps = 0;
    std::uint64_t batch_generation = 0;
    std::uint64_t composition_incarnation = 0;
    std::string boot;
    std::string fault;
    std::string admitted;
    bool terminal = false;

    RuntimeTrainingRunRecorder(std::size_t count, const std::string &configuration) {
        // Initialize the OS RNG before measuring the process module set.
        const auto id = process_identity();
        config = Json::parse(configuration);
        const auto &input = config.at("execution_sources");
        const auto &facts = input.at("owner_facts");
        sources = {.resolved_execution_plan_path = input.at("resolved_execution_plan_path"),
                   .request_path = input.at("request_path"),
                   .package_path = input.at("package_path"),
                   .wheel_path = input.at("wheel_path"),
                   .owner_facts = {.build_mode = facts.at("build_mode"),
                                   .build_dirty = facts.at("build_dirty"),
                                   .linker = facts.at("linker"),
                                   .cxx_abi = facts.at("cxx_abi"),
                                   .python_abi = facts.at("python_abi"),
                                   .node_abi = facts.at("node_abi")},
                   .resolved_input_lock_path = input.at("resolved_input_lock_path")};
        const auto lock_bytes = read(sources.resolved_input_lock_path);
        lock = Json::parse(lock_bytes);
        if (count == 0 || count != lock.at("config").value("n_envs", std::size_t{1}) ||
            authority::sha256_hex(lock_bytes) != config.at("input_lock_digest").get<std::string>())
            throw std::runtime_error("training_recorder.input_lock_mismatch");
        auto execution_config = lock.at("config");
        if (execution_config.contains("runtime")) {
            execution_config["runtime"].erase("run_recorder");
            execution_config["runtime"].erase("production_evidence");
            if (execution_config["runtime"].empty()) execution_config.erase("runtime");
        }
        if (execution_config != config.at("training_config"))
            throw std::runtime_error("training_recorder.training_config_mismatch");
        const auto budget = lock.at("config").at("total_timesteps").get<std::uint64_t>();
        if (budget == 0) throw std::runtime_error("training_recorder.empty_budget");
        expected_steps = budget / count + (budget % count != 0);
        const auto seed = config.at("training_seed").get<std::uint32_t>();
        if (count - 1 > std::numeric_limits<std::uint32_t>::max() - seed)
            throw std::runtime_error("training_recorder.seed_overflow");
        if (std::find(lock.at("effective_seed_set").begin(), lock.at("effective_seed_set").end(),
                      Json(seed)) == lock.at("effective_seed_set").end())
            throw std::runtime_error("training_recorder.seed_mismatch");
        const auto run = config.at("run_id").get<std::string>();
        receipt = Json::parse(read(config.at("receipt_template_path")));
        auto header = Json::parse(read(config.at("header_path")));
        auto template_bindings = header.at("receipt_bindings");
        template_bindings["receipt_id"] = "receipt-" + run;
        template_bindings["attempt_id"] = "attempt-" + run;
        std::string observed, detail;
        if (!collect_runtime_execution_bindings_json(sources, template_bindings.dump(), observed,
                                                     detail))
            throw std::runtime_error("training_recorder.provenance:" + detail);
        admitted = observed;
        const auto measured = Json::parse(observed);
        auto admission = measured;
        admission.erase("release_manifest_envelope_json");
        admission.erase("rollout_decision_envelope_json");
        header = {{"run_id", run},
                  {"receipt_bindings", measured},
                  {"admission_binding_sha256", authority::sha256_hex(canonical(admission))},
                  {"observed_measurement_sha256",
                   authority::sha256_hex(canonical(Json{{"executable", measured.at("executable")},
                                                        {"inputs", measured.at("inputs")},
                                                        {"package", measured.at("package")},
                                                        {"platform", measured.at("platform")}}))}};
        if (!validate_runtime_run_header_json(run, canonical(header), detail))
            throw std::runtime_error("training_recorder.header:" + detail);
        // Stage only existing owner-produced input bytes in the same native ledger.
        const auto root = config.at("ledger_root").get<std::string>();
        {
            RuntimeFileArtifactLedgerStore compiler(
                root, {RuntimeArtifactLedgerRole::PlanCompiler, "training-input-staging"});
            for (const auto &[path, media] :
                 {std::pair{sources.resolved_execution_plan_path,
                            "application/vnd.echelon-forge.resolved-execution-plan.v1+json"},
                  std::pair{sources.request_path,
                            "application/vnd.echelon-forge.runtime-composition-request.v1+json"},
                  std::pair{sources.resolved_input_lock_path,
                            "application/vnd.echelon-forge.resolved-input-lock.v1+json"}}) {
                auto bytes = read(path);
                if (path == sources.request_path) bytes = canonical(Json::parse(bytes));
                std::string digest, location;
                if (!compiler.put_artifact(bytes, media, "active-release", digest, location,
                                           detail))
                    throw std::runtime_error("training_recorder.staging:" + detail);
            }
        }
        for (const auto &[key, value] : measured.items())
            if (key != "release_manifest_envelope_json" && key != "rollout_decision_envelope_json")
                receipt["payload"][key] = value;
        store = std::make_unique<RuntimeFileArtifactLedgerStore>(
            root, RuntimeArtifactLedgerAccessContext{RuntimeArtifactLedgerRole::RuntimeHost,
                                                     "training-host"});
        recorder = std::make_unique<RuntimeRunRecorder>(*store, run, config.at("writer_id"));
        require(recorder->admit(canonical(header)));
        static std::atomic<std::uint64_t> sequence{0};
        incarnation = {id, ++sequence};
        boot = identity_text(id);
        for (std::size_t i = 0; i < count; ++i) {
            worlds.push_back({incarnation, i, 1});
            bindings.push_back(
                {{"world_index", i},
                 {"world_id", world_id(i)},
                 {"host_boot_id", boot},
                 {"incarnation_epoch", std::to_string(incarnation.incarnation_epoch)},
                 {"world_epoch", "1"}});
        }
    }
    std::string world_id(std::size_t index) const {
        return "training-world-" + std::to_string(incarnation.incarnation_epoch) + "-" +
               std::to_string(index);
    }
    void fail(const std::string &reason) {
        if (fault.empty()) fault = reason;
    }
    void capture(const RuntimeTrainingFacadeSnapshot &snapshot, std::uint64_t facade_incarnation,
                 bool after_step) {
        if (!fault.empty() || terminal)
            throw std::runtime_error("training_recorder.fenced:" + fault);
        if (!snapshot.healthy || snapshot.requires_host_recreate ||
            snapshot.world_count != worlds.size())
            throw std::runtime_error("training_recorder.failed_generation");
        if (composition_incarnation == 0) {
            composition_incarnation = facade_incarnation;
            batch_generation = snapshot.batch_generation;
        }
        if (composition_incarnation != facade_incarnation ||
            batch_generation != snapshot.batch_generation)
            throw std::runtime_error("training_recorder.generation_changed");
        if (!snapshot.evidence_available || snapshot.worlds.size() != worlds.size() ||
            snapshot.cpu_scheduler_topology_json.size() != worlds.size())
            throw std::runtime_error("training_recorder.missing_world");
        const auto observed_topology = Json::parse(snapshot.cpu_scheduler_topology_json.front());
        for (const auto &bytes : snapshot.cpu_scheduler_topology_json) {
            const auto snapshot_json = Json::parse(bytes);
            if (snapshot_json.at("sha256") !=
                    authority::sha256_hex(canonical(snapshot_json.at("topology"))) ||
                snapshot_json.at("sha256") != observed_topology.at("sha256"))
                throw std::runtime_error("training_recorder.topology_mismatch");
        }
        if (!topology.is_null() && (topology.at("sha256") != observed_topology.at("sha256") ||
                                    topology.at("topology") != observed_topology.at("topology")))
            throw std::runtime_error("training_recorder.topology_drift");
        topology = observed_topology;
        const auto plan = Json::parse(read(sources.resolved_execution_plan_path));
        if (snapshot.resolved_manifest_sha256 !=
                plan.at("input_bindings").at("resolved_manifest_sha256").get<std::string>() ||
            snapshot.executable_graph_sha256 !=
                runtime::composition_evidence_contracts::generated::kExecutableGraphSha256)
            throw std::runtime_error("training_recorder.composition_mismatch");
        last_worlds = Json::array();
        for (std::size_t i = 0; i < worlds.size(); ++i) {
            const auto &facts = snapshot.worlds.at(i);
            if (!worlds[i].well_formed() || !facts.well_formed || facts.world_index != i)
                throw std::runtime_error("training_recorder.missing_world_generation");
            std::uint64_t episode_generation = 0;
            Json native_generations = Json::object();
            for (const auto &scope : facts.scope_generations) {
                if (scope.generation == 0)
                    throw std::runtime_error("training_recorder.missing_generation");
                native_generations[scope.scope] = scope.generation;
                if (scope.scope == "episode") episode_generation = scope.generation;
            }
            if (episode_generation == 0)
                throw std::runtime_error("training_recorder.missing_episode");
            const auto episode = "training-episode-" +
                                 std::to_string(incarnation.incarnation_epoch) + "-" +
                                 std::to_string(i) + "-" + std::to_string(episode_generation);
            if (episode_ids.insert(episode).second) {
                if (steps == 0 &&
                    facts.episode_seed != config.at("training_seed").get<std::uint32_t>() + i)
                    throw std::runtime_error("training_recorder.executed_seed_mismatch");
                episodes.push_back({{"world_index", i},
                                    {"world_id", world_id(i)},
                                    {"world_generation", worlds[i].world_generation},
                                    {"episode_id", episode},
                                    {"episode_generation", episode_generation},
                                    {"seed", *facts.episode_seed},
                                    {"native_scope_generations", native_generations}});
            }
            if (after_step && facts.step == 0)
                throw std::runtime_error("training_recorder.step_not_committed");
            last_worlds.push_back({{"world_index", i},
                                   {"episode_id", episode},
                                   {"step", facts.step},
                                   {"state_digest", facts.state_digest},
                                   {"rng_digest", facts.rng_digest},
                                   {"seed", *facts.episode_seed}});
        }
        std::set<std::string> world_ids;
        for (std::size_t i = 0; i < worlds.size(); ++i)
            world_ids.insert(world_id(i));
        require(recorder->bind_runtime_scope(
            boot, std::to_string(incarnation.incarnation_epoch),
            canonical(Json{
                {"world_ids", sorted(world_ids)},
                {"entity_ids", Json::array()},
                {"episode_ids", sorted(episode_ids)},
                {"request_ids", Json::array({"request-" + config.at("run_id").get<std::string>()})},
                {"epochs",
                 {{"world", "1"},
                  {"entity", "0"},
                  {"episode", std::to_string(episodes.size())},
                  {"request", std::to_string(incarnation.incarnation_epoch)}}}})));
        if (after_step) {
            ++steps;
            require(recorder->append(recorder->next_sequence(),
                                     canonical(Json{{"event", "training_batch_step"},
                                                    {"batch_generation", batch_generation},
                                                    {"batch_steps", steps},
                                                    {"worlds", last_worlds}})));
        }
    }
    void artifact(const char *name, const Json &value, const char *media, std::string &digest) {
        std::string location;
        require(recorder->put_artifact(name, canonical(value), media, "run-retained", digest,
                                       location));
    }
    void prepare_finish(const RuntimeTrainingFacadeSnapshot &snapshot,
                        std::uint64_t facade_incarnation) {
        if (steps < expected_steps) fail("training_recorder.incomplete_execution_budget");
        if (!fault.empty()) return;
        capture(snapshot, facade_incarnation, false);
        std::string observed, detail;
        if (!collect_runtime_execution_bindings_json(sources, admitted, observed, detail) ||
            observed != admitted)
            throw std::runtime_error("training_recorder.input_drift:" + detail);
        std::string topology_digest, scope_digest, result_digest, validation_digest;
        artifact("runtime-cpu-scheduler-topology", topology,
                 "application/vnd.echelon-forge.runtime-cpu-scheduler-topology.v1+json",
                 topology_digest);
        artifact("runtime-world-scope-binding",
                 Json{{"schema_version", "echelon_forge.runtime_world_scope_binding.v1"},
                      {"world_bindings", bindings},
                      {"episodes", episodes},
                      {"batch_generation", batch_generation}},
                 "application/vnd.echelon-forge.runtime-world-scope-binding.v1+json", scope_digest);
        Json outcome_worlds = Json::array();
        Json indices = Json::array();
        for (std::size_t i = 0; i < worlds.size(); ++i) {
            indices.push_back(i);
            outcome_worlds.push_back(
                {{"world_index", i}, {"state", "completed"}, {"step_committed", true}});
        }
        Json result = {
            {"schema_version", "echelon_forge.training_run_observation.v1"},
            {"run_id", config.at("run_id")},
            {"input_lock_semantics_executed", true},
            {"input_lock_digest", config.at("input_lock_digest")},
            {"batch_steps", steps},
            {"expected_batch_steps", expected_steps},
            {"last_worlds", last_worlds},
            {"native_runtime",
             {{"resolved_manifest_sha256", snapshot.resolved_manifest_sha256},
              {"executable_graph_sha256", snapshot.executable_graph_sha256},
              {"realized_topology_digest", topology.at("sha256")},
              {"host_mode", snapshot.host_mode},
              {"input_lock_semantics_executed", true},
              {"topology_artifact_digest", topology_digest},
              {"world_scope_artifact_digest", scope_digest},
              {"receipt_world_bindings", bindings}}},
            {"outcome",
             {{"schema_version", "echelon_forge.batch_operation_outcome.v1"},
              {"batch_generation_ref", "training-generation-" + std::to_string(batch_generation)},
              {"operation_ref", config.at("run_id")},
              {"operation", "training"},
              {"domain", "batch"},
              {"result", "completed"},
              {"worlds", outcome_worlds},
              {"expected_world_indices", indices},
              {"recovery_admission", "none"},
              {"diagnostics", Json::array()}}}};
        artifact("runtime-training-observation", result,
                 "application/vnd.echelon-forge.training-run-observation.v1+json", result_digest);
        artifact("runtime-training-validation",
                 Json{{"accepted", true},
                      {"result_digest", result_digest},
                      {"batch_steps", steps},
                      {"world_count", worlds.size()}},
                 "application/octet-stream", validation_digest);
        require(recorder->record_native_result(result_digest, validation_digest));
    }
};
std::shared_ptr<RuntimeTrainingRunRecorder>
create_training_run_recorder(std::size_t count, const std::string &configuration) {
    return std::make_shared<RuntimeTrainingRunRecorder>(count, configuration);
}

void note_training_run_lifecycle(RuntimeTrainingRunRecorder &recorder, const char *event) {
    require(recorder.recorder->note_lifecycle(event));
}

bool try_note_training_run_lifecycle(RuntimeTrainingRunRecorder &recorder, const char *event) {
    if (!recorder.recorder) return false;
    const auto status = recorder.recorder->note_lifecycle(event);
    if (!status) {
        recorder.fail(status.code + ":" + status.detail);
        return false;
    }
    return true;
}

void capture_training_run_snapshot(RuntimeTrainingRunRecorder &recorder,
                                   const RuntimeTrainingFacadeSnapshot &snapshot,
                                   std::uint64_t facade_incarnation, bool after_step) {
    recorder.capture(snapshot, facade_incarnation, after_step);
}

void fail_training_run_recorder(RuntimeTrainingRunRecorder &recorder, const std::string &reason) {
    recorder.fail(reason);
}

bool is_training_run_recorder_terminal(const RuntimeTrainingRunRecorder &recorder) noexcept {
    return recorder.terminal;
}

void prepare_finish_training_run_recorder(RuntimeTrainingRunRecorder &recorder,
                                          const RuntimeTrainingFacadeSnapshot &snapshot,
                                          std::uint64_t facade_incarnation) {
    recorder.prepare_finish(snapshot, facade_incarnation);
}

void finalize_training_run_recorder(RuntimeTrainingRunRecorder &recorder) {
    if (!recorder.recorder) {
        recorder.terminal = true;
        return;
    }
    require(recorder.recorder->finalize_observed(
        recorder.receipt.dump(), recorder.fault.empty() ? "completed" : "failed",
        recorder.fault.empty() ? "native training execution budget completed" : recorder.fault));
    recorder.terminal = true;
    recorder.recorder.reset();
    recorder.store.reset();
}

void abort_training_run_recorder_construction(RuntimeTrainingRunRecorder &recorder,
                                              const std::string &reason) {
    recorder.fail(reason);
    if (recorder.recorder && recorder.recorder->terminalizable()) {
        (void)recorder.recorder->finalize_observed(recorder.receipt.dump(), "failed",
                                                   recorder.fault);
    }
}

std::string reopen_training_run_receipt(const std::string &root, const std::string &run) {
    using namespace runtime::host;
    RuntimeFileArtifactLedgerStore reader(
        root, {RuntimeArtifactLedgerRole::ReadOnlyAuditor, "training-auditor"});
    std::string bytes, detail;
    if (!reader.read_receipt(run, bytes, detail)) {
        throw std::runtime_error("training_recorder.reopen:" + detail);
    }
    return bytes;
}

} // namespace runtime::host::integration
#endif
