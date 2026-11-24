#include "tests/runtime_facade_run_qualification.h"

#include "runtime/contracts/authority/runtime_authority_contract.h"
#include "runtime/contracts/composition/runtime_composition_evidence.v1.generated.h"
#include "runtime/facade/runtime_facade.h"

#include <atomic>
#include <cmath>
#include <limits>
#include <nlohmann/json.hpp>
#include <random>
#include <stdexcept>
#include <utility>

namespace runtime::host::integration {
namespace {
using Json = nlohmann::json;

RuntimeRunRecorderStatus rejected(std::string detail) {
    return {false, "facade_qualification.rejected", std::move(detail)};
}

std::string boot_identity() {
    // Initialize the platform RNG before sealing current-process provenance.
    static const std::string boot = [] {
        std::random_device random;
        return "facade-qualification-boot-" + std::to_string(random()) + "-" +
               std::to_string(random());
    }();
    return boot;
}

std::uint64_t scope_generation(const RuntimeCompositionEvidence &evidence, const char *scope) {
    if (evidence.world_instances.size() != 1 || evidence.world_instances.front().world_index != 0)
        throw std::runtime_error("qualification requires exactly one native world");
    for (const auto &item : evidence.world_instances.front().scope_generations) {
        if (item.scope == scope) return item.generation;
    }
    throw std::runtime_error("native scope generation is absent");
}

} // namespace

struct RuntimeFacadeRunQualification::State {
    RuntimeFacadeRunQualificationConfig config;
    RuntimeRunRecorder recorder;
    std::unique_ptr<RuntimeFacade> facade;
    std::string host_boot_id = boot_identity();
    std::string incarnation;
    std::string world_id;
    std::string episode_id;
    std::uint32_t seed = 0;
    std::uint64_t time_step_ns = 0;
    std::uint64_t world_epoch = 0;
    std::uint64_t episode_epoch = 0;
    std::uint64_t batch_generation = 0;
    std::uint64_t entity_id = 0;
    std::string admitted_manifest;
    std::string initial_topology;
    double last_time = 0.0;
    double frame_delta = 0.0;
    bool constructed = false;
    bool destroyed = false;
    bool initialized = false;
    bool terminal = false;
    std::string fault;
    std::string evidence;

    State(RuntimeRunRecorderStore &store, RuntimeFacadeRunQualificationConfig value)
        : config(std::move(value)), recorder(store, config.run_id, config.writer_id) {
        static std::atomic<std::uint64_t> sequence{0};
        incarnation = std::to_string(++sequence);
        const auto identity = runtime::authority_contracts::sha256_hex(
            host_boot_id + ":" + incarnation + ":" + config.run_id);
        world_id = "facade-world-" + identity.substr(0, 24);
        episode_id = "facade-episode-" + identity.substr(0, 24);
    }

    RuntimeRunRecorderStatus fail(std::string reason) {
        fault = std::move(reason);
        return rejected(fault);
    }

    std::string verify_composition(const RuntimeCompositionEvidenceResult &actual) const {
        namespace generated = runtime::composition_evidence_contracts::generated;
        if (!actual.available || actual.evidence.host_mode != "native_cpp" ||
            actual.evidence.resolved_manifest_sha256 != admitted_manifest ||
            actual.evidence.executable_graph_sha256 != generated::kExecutableGraphSha256 ||
            actual.evidence.backend.provider_id != generated::kBackendProviderId ||
            actual.evidence.backend.backend_profile_id != generated::kBackendProfileId ||
            actual.cpu_scheduler_topology_json.size() != 1)
            throw std::runtime_error(
                "actual facade composition differs from admitted default plan");
        const auto topology = Json::parse(actual.cpu_scheduler_topology_json.front());
        const auto canonical =
            runtime::authority_contracts::canonical_authority_json(topology.at("topology").dump());
        if (!canonical ||
            topology.at("topology").at("contract") != "echelon_forge.cpu_scheduler_topology.v1" ||
            topology.at("sha256") != runtime::authority_contracts::sha256_hex(*canonical))
            throw std::runtime_error("native scheduler topology integrity differs");
        return topology.at("sha256").get<std::string>();
    }

    RuntimeRunRecorderStatus retire(bool complete) {
        const auto lifecycle = [&](const char *event) {
            const auto status = recorder.note_lifecycle(event);
            if (!status) throw std::runtime_error(status.detail);
        };
        if (facade != nullptr) {
            const auto status = facade->batch_failure_status();
            if (status.requires_host_recreate) {
                // An unfinished Flecs pipeline is not safe for in-process
                // destruction. Retire the disposable process after its failed
                // receipt; never claim reclamation of this resource.
                (void)facade.release();
                complete = false;
                fault = "native generation requires host recreation";
            } else {
                lifecycle("drain");
                facade.reset();
                destroyed = true;
                // Both events follow actual destruction, not a Python close.
                lifecycle("shutdown");
                lifecycle("reclamation");
            }
        }
        const auto finalized = recorder.finalize_observed(
            config.receipt_template_json, complete ? "completed" : "failed",
            complete ? "fixed-step maintained facade qualification completed" : fault);
        terminal = static_cast<bool>(finalized);
        return finalized;
    }
};

RuntimeFacadeRunQualification::RuntimeFacadeRunQualification(
    RuntimeRunRecorderStore &store, RuntimeFacadeRunQualificationConfig config)
    : state_(std::make_unique<State>(store, std::move(config))) {}

RuntimeFacadeRunQualification::~RuntimeFacadeRunQualification() {
    if (!state_->terminal && state_->recorder.terminalizable()) {
        try {
            if (state_->fault.empty()) state_->fault = "qualification abandoned before finish";
            (void)state_->retire(false);
        } catch (...) {
            // Destruction cannot turn a failed terminal write into completion.
        }
    }
}

RuntimeRunRecorderStatus RuntimeFacadeRunQualification::start() {
    auto &s = *state_;
    if (s.constructed || s.terminal || !s.fault.empty()) return rejected("run is not new");
    if (s.config.expected_steps == 0 || s.config.expected_steps > 4096)
        return s.fail("fixed step budget must be in [1,4096]");
    try {
        std::string detail, observed, request, plan;
        if (!validate_runtime_run_header_json(s.config.run_id, s.config.header_json, detail))
            return s.fail(detail);
        const auto header = Json::parse(s.config.header_json);
        const auto &bindings = header.at("receipt_bindings");
        if (!collect_runtime_execution_bindings_json(s.config.execution_sources, bindings.dump(),
                                                     observed, detail, &request) ||
            observed != bindings.dump())
            return s.fail("current execution provenance differs: " + detail);
        if (!load_runtime_execution_plan_json(s.config.execution_sources, bindings.dump(), plan,
                                              detail))
            return s.fail(detail);
        const auto plan_document = Json::parse(plan);
        if (plan_document.at("input_bindings").at("resolved_manifest_sha256").get<std::string>() !=
            std::string(
                runtime::composition_evidence_contracts::generated::kResolvedManifestSha256))
            return s.fail("plan is not the maintained default facade composition");
        s.admitted_manifest =
            plan_document.at("input_bindings").at("resolved_manifest_sha256").get<std::string>();
        const auto configuration = Json::parse(request).at("configuration");
        const auto seed = configuration.at("seed").get<std::uint64_t>();
        if (seed > std::numeric_limits<std::uint32_t>::max())
            return s.fail("request seed is outside the native seed range");
        s.seed = static_cast<std::uint32_t>(seed);
        s.time_step_ns = configuration.at("time_step_ns").get<std::uint64_t>();
        if (s.time_step_ns == 0) return s.fail("request timestep must be positive");
        const auto admission = s.recorder.admit(s.config.header_json);
        if (!admission) return s.fail("durable admission failed: " + admission.detail);

        s.facade = std::make_unique<RuntimeFacade>(1);
        s.constructed = true;
        const auto construction = s.recorder.note_lifecycle("construction");
        if (!construction) return s.fail(construction.detail);
        return {true, {}, {}};
    } catch (const std::exception &error) {
        return s.fail(error.what());
    }
}

RuntimeRunRecorderStatus RuntimeFacadeRunQualification::setup(BatchWorldSetupRequest request) {
    auto &s = *state_;
    if (s.facade == nullptr || s.initialized || !s.fault.empty())
        return s.fail("exactly one setup is admitted");
    try {
        const double dt = static_cast<double>(s.time_step_ns) / 1'000'000'000.0;
        if ((!request.seeds.empty() && request.seeds != std::vector<std::uint32_t>{s.seed}) ||
            (!request.time_steps.empty() && request.time_steps != std::vector<double>{dt}) ||
            request.spawn_requests.size() != 1 || request.spawn_requests.front().world_index != 0 ||
            !request.typed_platform_spawn_requests.empty())
            return s.fail("setup does not match the single-world admitted seed/time scope");
        request.seeds = {s.seed};
        request.time_steps = {dt};
        const auto result = s.facade->apply_world_setup(request);
        if (result.entity_ids.size() != 1 || result.entity_ids.front() == 0)
            return s.fail("native setup did not produce the requested entity");
        s.entity_id = result.entity_ids.front();
        const auto initial_observation = s.facade->get_agent_observations_batch({{0, s.entity_id}});
        if (initial_observation.size() != 1) return s.fail("native initial observation is absent");
        s.last_time = initial_observation.front().sim_time;
        if (!std::isfinite(s.last_time) || s.last_time != 0.0)
            return s.fail("native episode does not start at finite zero time");
        const auto facts = s.facade->native_snapshot_facts(0);
        const auto composition = s.facade->export_composition_evidence();
        s.initial_topology = s.verify_composition(composition);
        if (!facts.well_formed() || facts.episode_seed != s.seed || facts.step != 0 ||
            !composition.available || composition.evidence.host_mode != "native_cpp")
            return s.fail("native initial facts do not match the admitted request");
        s.world_epoch = scope_generation(composition.evidence, "world");
        s.episode_epoch = scope_generation(composition.evidence, "episode");
        s.batch_generation = s.facade->batch_failure_status().generation;
        for (const auto *event : {"validation", "publication"}) {
            const auto status = s.recorder.note_lifecycle(event);
            if (!status) return s.fail(status.detail);
        }
        const auto bound = s.recorder.bind_runtime_identity(
            s.host_boot_id, s.incarnation, s.world_id, std::to_string(s.world_epoch), s.episode_id,
            std::to_string(s.episode_epoch), "request-" + s.config.run_id);
        if (!bound) return s.fail(bound.detail);
        const auto episode = s.recorder.note_lifecycle("episode");
        if (!episode) return s.fail(episode.detail);
        s.initialized = true;
        return {true, {}, {}};
    } catch (const std::exception &error) {
        return s.fail(error.what());
    }
}

RuntimeRunRecorderStatus
RuntimeFacadeRunQualification::step(const std::vector<WorldPilotActionAssignment> &actions) {
    auto &s = *state_;
    if (!s.initialized || s.facade == nullptr || !s.fault.empty())
        return rejected("step requires an initialized healthy attempt");
    try {
        if (!actions.empty()) s.facade->set_pilot_actions_batch(actions);
        s.facade->step_batch();
        const auto facts = s.facade->native_snapshot_facts(0);
        const auto observations = s.facade->get_agent_observations_batch({{0, s.entity_id}});
        if (observations.size() != 1) return s.fail("native step observation is absent");
        const double time = observations.front().sim_time;
        s.frame_delta = time - s.last_time;
        s.last_time = time;
        const auto recorded = s.recorder.append(s.recorder.next_sequence(),
                                                Json{{"event", "facade_qualification_native_step"},
                                                     {"step", facts.step},
                                                     {"sim_time_s", time},
                                                     {"cpu_frame_delta_s", s.frame_delta},
                                                     {"state_digest", facts.state_digest},
                                                     {"episode_seed", facts.episode_seed.value()}}
                                                    .dump());
        if (!recorded) return s.fail(recorded.detail);
        return {true, {}, {}};
    } catch (const std::exception &error) {
        return s.fail(error.what());
    }
}

RuntimeRunRecorderStatus RuntimeFacadeRunQualification::finish() {
    auto &s = *state_;
    if (s.terminal) return rejected("attempt is already terminal");
    if (!s.recorder.terminalizable()) return rejected("attempt was not durably admitted");
    try {
        if (s.fault.empty()) {
            if (!s.initialized || s.facade == nullptr) throw std::runtime_error("setup is absent");
            const auto health = s.facade->batch_failure_status();
            if (!health.healthy) throw std::runtime_error("native generation is unhealthy");
            const auto facts = s.facade->native_snapshot_facts(0);
            if (!facts.well_formed())
                throw std::runtime_error("terminal native facts are malformed");
            const auto composition = s.facade->export_composition_evidence();
            const auto topology_sha = s.verify_composition(composition);
            if (topology_sha != s.initial_topology)
                throw std::runtime_error("actual scheduler topology drifted within the attempt");
            if (facts.episode_seed != s.seed) throw std::runtime_error("native seed drift");
            if (health.generation != s.batch_generation ||
                scope_generation(composition.evidence, "world") != s.world_epoch ||
                scope_generation(composition.evidence, "episode") != s.episode_epoch)
                throw std::runtime_error("native world/episode generation drift");
            const auto observations = s.facade->get_agent_observations_batch({{0, s.entity_id}});
            if (observations.size() != 1) throw std::runtime_error("native observation is absent");
            const double time = observations.front().sim_time;
            const double declared_dt = static_cast<double>(s.time_step_ns) / 1'000'000'000.0;
            const double configured_dt = s.facade->world_time_step(0);
            if (configured_dt != declared_dt)
                throw std::runtime_error("native configured timestep differs from request");
            // This selected reference owner advances Flecs with ecs_ftime_t.
            // Its frame increment can be narrower than the double accumulated
            // world clock. Verify both the configured dt and that actual clock
            // increment, rather than pretending the declared ns are exact dt.
            const double expected_time = static_cast<double>(s.config.expected_steps) *
                                         static_cast<double>(static_cast<ecs_ftime_t>(declared_dt));
            if (!std::isfinite(time) || !std::isfinite(expected_time) ||
                !std::isfinite(s.frame_delta) || s.frame_delta <= 0.0 ||
                facts.step != s.config.expected_steps || std::abs(time - expected_time) > 1e-9)
                throw std::runtime_error(
                    "native step/time outcome differs from fixed budget: " +
                    Json{{"steps", facts.step}, {"time", time}, {"expected_time", expected_time}}
                        .dump());
            std::string observed, detail;
            if (!collect_runtime_execution_bindings_json(s.config.execution_sources,
                                                         s.recorder.admission_bindings_json(),
                                                         observed, detail) ||
                observed != s.recorder.admission_bindings_json())
                throw std::runtime_error("execution input provenance drift: " + detail);
            const auto result = Json{
                {"run_id", s.config.run_id},
                {"host_boot_id", s.host_boot_id},
                {"incarnation_epoch", s.incarnation},
                {"world_id", s.world_id},
                {"episode_id", s.episode_id},
                {"world_index", 0},
                {"world_epoch", std::to_string(s.world_epoch)},
                {"episode_epoch", std::to_string(s.episode_epoch)},
                {"batch_generation", health.generation},
                {"seed", facts.episode_seed.value()},
                {"steps_completed", facts.step},
                {"sim_time_s", time},
                {"admitted_time_step_ns", s.time_step_ns},
                {"native_world_time_step_s", configured_dt},
                {"cpu_frame_delta_s", s.frame_delta},
                {"cpu_frame_delta_precision", "ecs_ftime_t"},
                {"resolved_manifest_sha256", composition.evidence.resolved_manifest_sha256},
                {"executable_graph_sha256", composition.evidence.executable_graph_sha256},
                {"cpu_scheduler_topology_sha256", topology_sha},
                {"state_digest", facts.state_digest},
                {"rng_digest", facts.rng_digest},
                {"healthy", health.healthy},
                {"host_mode", composition.evidence.host_mode},
                {"input_lock_semantics_executed",
                 false}}.dump();
            std::string result_digest, location, validation_digest;
            std::string topology_digest;
            auto status = s.recorder.put_artifact(
                "cpu-scheduler-topology", composition.cpu_scheduler_topology_json.front(),
                "application/vnd.echelon-forge.runtime-cpu-scheduler-topology.v1+json",
                "run-retained", topology_digest, location);
            if (!status) throw std::runtime_error(status.detail);
            status = s.recorder.put_artifact("maintained-facade-native-result", result,
                                             "application/octet-stream", "run-retained",
                                             result_digest, location);
            if (!status) throw std::runtime_error(status.detail);
            const auto validation = Json{{"accepted", true},
                                         {"native_result_sha256", result_digest},
                                         {"expected_steps", s.config.expected_steps},
                                         {"observed_steps", facts.step},
                                         {"admitted_time_step_ns", s.time_step_ns},
                                         {"native_world_time_step_s", configured_dt},
                                         {"cpu_frame_delta_s", s.frame_delta},
                                         {"cpu_frame_delta_precision", "ecs_ftime_t"},
                                         {"observed_sim_time_s", time},
                                         {"observed_seed", facts.episode_seed.value()}}
                                        .dump();
            status = s.recorder.put_artifact("maintained-facade-native-validation", validation,
                                             "application/octet-stream", "run-retained",
                                             validation_digest, location);
            if (!status) throw std::runtime_error(status.detail);
            status = s.recorder.record_native_result(result_digest, validation_digest);
            if (!status) throw std::runtime_error(status.detail);
            s.evidence = result;
        }
    } catch (const std::exception &error) {
        s.fault = error.what();
    }
    const bool complete = s.fault.empty();
    const auto finalized = s.retire(complete);
    if (!finalized) return finalized;
    return s.fault.empty() ? finalized : rejected(s.fault);
}

bool RuntimeFacadeRunQualification::facade_constructed() const noexcept {
    return state_->constructed;
}
bool RuntimeFacadeRunQualification::facade_destroyed() const noexcept {
    return state_->destroyed;
}
std::string RuntimeFacadeRunQualification::evidence_json() const {
    return state_->evidence;
}

RuntimeFacade &RuntimeFacadeRunQualification::native_facade_for_test() {
    if (state_->facade == nullptr) throw std::logic_error("qualification facade is not live");
    return *state_->facade;
}

} // namespace runtime::host::integration
