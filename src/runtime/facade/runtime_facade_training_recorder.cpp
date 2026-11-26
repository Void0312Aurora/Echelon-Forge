#include "runtime/facade/runtime_facade_internal.h"

#include "runtime/contracts/runtime_training_run_recorder_port.h"

#include <exception>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>

#if defined(EF_ENABLE_TRAINING_RUN_RECORDER)
namespace {

using runtime::host::integration::RuntimeTrainingFacadeSnapshot;
using runtime::host::integration::RuntimeTrainingWorldScopeGeneration;
using runtime::host::integration::RuntimeTrainingWorldSnapshot;

RuntimeTrainingFacadeSnapshot capture_facade_training_snapshot(RuntimeFacade &facade) {
    const auto health = facade.batch_failure_status();
    const auto evidence = facade.export_composition_evidence();
    RuntimeTrainingFacadeSnapshot snapshot{
        .healthy = health.healthy,
        .requires_host_recreate = health.requires_host_recreate,
        .batch_generation = health.generation,
        .world_count = facade.world_count(),
        .evidence_available = evidence.available,
        .resolved_manifest_sha256 = evidence.evidence.resolved_manifest_sha256,
        .executable_graph_sha256 = evidence.evidence.executable_graph_sha256,
        .host_mode = evidence.evidence.host_mode,
        .cpu_scheduler_topology_json = evidence.cpu_scheduler_topology_json,
    };
    const auto count = facade.world_count();
    if (evidence.available && evidence.evidence.world_instances.size() == count) {
        snapshot.worlds.reserve(count);
        for (std::size_t i = 0; i < count; ++i) {
            const auto facts = facade.native_snapshot_facts(i);
            const auto &instance = evidence.evidence.world_instances.at(i);
            RuntimeTrainingWorldSnapshot world{
                .world_index = instance.world_index,
                .well_formed = facts.well_formed(),
                .step = facts.step,
                .state_digest = facts.state_digest,
                .rng_digest = facts.rng_digest,
                .episode_seed = facts.episode_seed,
            };
            world.scope_generations.reserve(instance.scope_generations.size());
            for (const auto &scope : instance.scope_generations) {
                world.scope_generations.push_back(RuntimeTrainingWorldScopeGeneration{
                    .scope = scope.scope,
                    .generation = scope.generation,
                });
            }
            snapshot.worlds.push_back(std::move(world));
        }
    }
    return snapshot;
}

} // namespace

RuntimeFacade::RuntimeFacade(std::size_t count, const std::string &configuration)
    : identity_(std::make_shared<RuntimeFacadeIdentity>()) {
    auto recording = runtime::host::integration::create_training_run_recorder(count, configuration);
    identity_->run_recorder = recording;
    try {
        auto materialized =
            runtime::backend_provider::materialize_default_world_batch_backend(count);
        if (!materialized) throw std::runtime_error(materialized.error.detail);
        identity_->backend_identity = std::move(materialized.identity);
        runtime_ = std::move(materialized.backend);
        runtime::host::integration::note_training_run_lifecycle(*recording, "construction");
        runtime::host::integration::note_training_run_lifecycle(*recording, "validation");
        runtime::host::integration::note_training_run_lifecycle(*recording, "publication");
        runtime::host::integration::note_training_run_lifecycle(*recording, "episode");
    } catch (...) {
        runtime::host::integration::abort_training_run_recorder_construction(
            *recording, "training_recorder.construction_failed");
        throw;
    }
}

void runtime_training_record_before_step(RuntimeFacade &facade, RuntimeFacadeIdentity &identity) {
    if (identity.run_recorder) {
        runtime::host::integration::capture_training_run_snapshot(
            *identity.run_recorder, capture_facade_training_snapshot(facade),
            identity.composition_incarnation, false);
    }
}

void runtime_training_record_after_step(RuntimeFacade &facade, RuntimeFacadeIdentity &identity) {
    if (identity.run_recorder) {
        runtime::host::integration::capture_training_run_snapshot(
            *identity.run_recorder, capture_facade_training_snapshot(facade),
            identity.composition_incarnation, true);
    }
}

void runtime_training_record_failure(RuntimeFacadeIdentity &identity, const std::string &reason) {
    if (identity.run_recorder) {
        runtime::host::integration::fail_training_run_recorder(*identity.run_recorder, reason);
    }
}

void RuntimeFacade::fail_recorded_run(const std::string &reason) {
    if (identity_ && identity_->run_recorder) {
        runtime::host::integration::fail_training_run_recorder(*identity_->run_recorder, reason);
    }
}

bool RuntimeFacade::training_run_recorder_enabled() noexcept {
    return true;
}

void RuntimeFacade::finish_recorded_run() {
    if (!identity_ || !identity_->run_recorder) return;
    auto &recording = *identity_->run_recorder;
    if (runtime::host::integration::is_training_run_recorder_terminal(recording)) return;
    if (runtime_) {
        try {
            runtime::host::integration::prepare_finish_training_run_recorder(
                recording, capture_facade_training_snapshot(*this),
                identity_->composition_incarnation);
        } catch (const std::exception &error) {
            runtime::host::integration::fail_training_run_recorder(recording, error.what());
        }
        if (runtime_->failure_status().requires_host_recreate) {
            runtime::host::integration::fail_training_run_recorder(
                recording, "training_recorder.host_recreation_required");
            (void)runtime_.release();
        } else {
            const bool drain_ok =
                runtime::host::integration::try_note_training_run_lifecycle(recording, "drain");
            runtime_.reset();
            if (drain_ok && runtime::host::integration::try_note_training_run_lifecycle(
                                recording, "shutdown")) {
                (void)runtime::host::integration::try_note_training_run_lifecycle(recording,
                                                                                  "reclamation");
            }
        }
    } else {
        runtime::host::integration::fail_training_run_recorder(
            recording, "training_recorder.backend_already_torn_down");
    }
    runtime::host::integration::finalize_training_run_recorder(recording);
}

std::string RuntimeFacade::reopen_recorded_run(const std::string &root, const std::string &run) {
    return runtime::host::integration::reopen_training_run_receipt(root, run);
}
#else
RuntimeFacade::RuntimeFacade(std::size_t, const std::string &) {
    throw std::runtime_error(
        "training_recorder.disabled: build with EF_ENABLE_TRAINING_RUN_RECORDER=ON");
}
void runtime_training_record_before_step(RuntimeFacade &, RuntimeFacadeIdentity &) {}
void runtime_training_record_after_step(RuntimeFacade &, RuntimeFacadeIdentity &) {}
void runtime_training_record_failure(RuntimeFacadeIdentity &, const std::string &) {}
bool RuntimeFacade::training_run_recorder_enabled() noexcept {
    return false;
}
void RuntimeFacade::finish_recorded_run() {}
void RuntimeFacade::fail_recorded_run(const std::string &) {}
std::string RuntimeFacade::reopen_recorded_run(const std::string &, const std::string &) {
    throw std::runtime_error("training_recorder.disabled");
}
#endif
