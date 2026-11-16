#include "tests/runtime_facade_run_qualification.h"
#include "runtime/host/runtime_file_artifact_ledger_store.h"
#include "runtime/contracts/authority/runtime_authority_contract.h"
#include "runtime/facade/runtime_facade.h"

#include <doctest/doctest.h>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <nlohmann/json.hpp>
#include <random>
#include <sstream>
#include <stdexcept>

namespace runtime::host::integration {
struct RuntimeFacadeRunQualificationTestAccess {
    static RuntimeFacade &facade(RuntimeFacadeRunQualification &run) {
        return run.native_facade_for_test();
    }
};
} // namespace runtime::host::integration

namespace {
using Json = nlohmann::json;
using namespace runtime::host;
using namespace runtime::host::integration;
namespace authority = runtime::authority_contracts;

std::string read(const std::filesystem::path &path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) throw std::runtime_error("cannot read qualification input: " + path.string());
    std::ostringstream bytes;
    bytes << input.rdbuf();
    return bytes.str();
}
void write(const std::filesystem::path &path, const std::string &bytes) {
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    output << bytes;
    if (!output.good()) throw std::runtime_error("cannot write qualification output");
}
std::string canonical(const Json &value) {
    return authority::canonical_authority_json(value.dump()).value();
}
std::filesystem::path fixture(const char *name) {
    return std::filesystem::path(EF_SOURCE_ROOT) / "tests/architecture/composition/fixtures" / name;
}
Json vector_envelope(const char *name) {
    return Json::parse(Json::parse(read(fixture(name))).at("envelope_json").get<std::string>());
}

class Directory {
  public:
    Directory() {
        // The existing native recorder creates its capability with the OS RNG.
        // Load that platform module before measuring the executable/module set.
        std::random_device random;
        (void)random();
        if (const auto *external = std::getenv("EF_FACADE_RUN_OUTPUT")) {
            path = external;
            std::filesystem::create_directories(path);
            return;
        }
        for (unsigned attempt = 0; attempt < 128; ++attempt) {
            auto candidate =
                std::filesystem::temp_directory_path() /
                ("ef-facade-run-" + std::to_string(random()) + "-" + std::to_string(random()));
            if (std::filesystem::create_directory(candidate)) {
                path = std::move(candidate);
                owned = true;
                return;
            }
        }
        throw std::runtime_error("cannot reserve qualification directory");
    }
    ~Directory() {
        if (owned) {
            std::error_code error;
            std::filesystem::remove_all(path, error);
        }
    }
    std::filesystem::path path;
    bool owned = false;
};

RuntimeExecutionProvenanceSources sources_for(const std::filesystem::path &lock) {
#if defined(NDEBUG)
    const std::string mode = "Release";
#else
    const std::string mode = "Debug";
#endif
    return {
        .resolved_execution_plan_path = fixture("default_resolved_execution_plan.v1.json").string(),
        .request_path = fixture("default_runtime_composition_request.v1.json").string(),
        .package_path = fixture("candidate_release_package.v1.bin").string(),
        .wheel_path = fixture("candidate_release_package.v1.bin").string(),
        .owner_facts = {.build_mode = mode,
                        .build_dirty = true,
                        .linker = "link.exe",
                        .cxx_abi = "msvc-native",
                        .python_abi = "qualification-native-only",
                        .node_abi = "qualification-native-only"},
        .resolved_input_lock_path = lock.string(),
    };
}

RuntimeFacadeRunQualificationConfig
measured_config(const std::string &run, const RuntimeExecutionProvenanceSources &sources) {
    // Existing version vectors supply only the static authority/receipt shell.
    // Current executable, modules, package, input facts and every completion
    // field are replaced by their native owners; no receipt vector is output.
    auto receipt = Json::parse(Json::parse(read(fixture("run_receipt.v1.json")))
                                   .at("canonical_envelope_json")
                                   .get<std::string>());
    auto &payload = receipt.at("payload");
    payload["run_id"] = run;
    payload["journal_id"] = run;
    payload["receipt_id"] = "receipt-" + run;
    payload["attempt_id"] = "attempt-" + run;
    const auto plan_bytes = read(sources.resolved_execution_plan_path);
    const auto plan = Json::parse(plan_bytes);
    const auto plan_sha = plan.at("plan_sha256").get<std::string>();
    const auto request_sha = plan.at("input_bindings").at("request_sha256").get<std::string>();
    auto release = vector_envelope("authority_cross_language_vector.v1.json");
    auto rollout = vector_envelope("authority_rollout_decision.v1.json");
    rollout.at("payload")["plan_sha256"] = plan_sha;
    rollout["payload_sha256"] = authority::authority_digest_sha256_hex(
        "release.rollout-decision", "application/vnd.echelon-forge.rollout-decision.v1+json",
        canonical(rollout.at("payload")));
    payload["plan_binding"] = {
        {"compiler_identity", "PlanCompiler"},
        {"compiler_version", "1.0.0"},
        {"plan_canonical_sha256", plan_sha},
        {"plan_generation", plan.at("writer_generation")},
        {"plan_id", plan.at("plan_id")},
        {"plan_location", "ledger://blob-" + authority::sha256_hex(plan_bytes)},
        {"plan_sha256", plan_sha},
        {"request_canonical_sha256", request_sha},
        {"request_location", "ledger://blob-" + request_sha},
        {"request_sha256", request_sha}};
    payload["reader_generation_min"] = plan.at("reader_generation_min");
    payload["reader_generation_max"] = plan.at("reader_generation_max");
    payload["release_binding"] = {
        {"release_id", release.at("payload").at("release_id")},
        {"release_manifest_sha256", release.at("payload_sha256")},
        {"rollout_decision_id", rollout.at("payload").at("decision_id")},
        {"rollout_decision_sha256", rollout.at("payload_sha256")},
        {"provenance_sha256", release.at("payload").at("provenance_sha256")},
        {"sbom_sha256", release.at("payload").at("sbom_sha256")},
        {"attestation_sha256", payload.at("release_binding").at("attestation_sha256")}};
    payload["package"]["identity"] = "cmo";
    payload["build"]["source_revision"] = release.at("payload").at("source_revision");
    payload["build"]["toolchain"] = release.at("payload").at("toolchain_identity");
    payload["inputs"]["artifacts"] = {
        {"request", request_sha}, {"resolved_execution_plan", authority::sha256_hex(plan_bytes)}};
    Json bindings;
    for (const auto *name : {"receipt_id", "attempt_id", "plan_binding", "release_binding",
                             "executable", "package", "build", "platform", "inputs", "backend",
                             "reader_generation_min", "reader_generation_max"})
        bindings[name] = payload.at(name);
    bindings["release_manifest_envelope_json"] = canonical(release);
    bindings["rollout_decision_envelope_json"] = canonical(rollout);
    std::string observed, detail;
    if (!collect_runtime_execution_bindings_json(sources, bindings.dump(), observed, detail))
        throw std::runtime_error("qualification measurement failed: " + detail);
    bindings = Json::parse(observed);
    for (const auto *name : {"backend", "build", "executable", "inputs", "package", "platform"})
        payload[name] = bindings.at(name);
    Json admission = bindings;
    admission.erase("release_manifest_envelope_json");
    admission.erase("rollout_decision_envelope_json");
    const Json measurement = {{"executable", bindings.at("executable")},
                              {"inputs", bindings.at("inputs")},
                              {"package", bindings.at("package")},
                              {"platform", bindings.at("platform")}};
    return {.run_id = run,
            .writer_id = "writer-" + run,
            .header_json = canonical(Json{
                {"run_id", run},
                {"receipt_bindings", bindings},
                {"admission_binding_sha256", authority::sha256_hex(canonical(admission))},
                {"observed_measurement_sha256", authority::sha256_hex(canonical(measurement))}}),
            .receipt_template_json = receipt.dump(),
            .execution_sources = sources,
            .expected_steps = 3};
}

void stage(const std::filesystem::path &root, const RuntimeExecutionProvenanceSources &sources) {
    RuntimeFileArtifactLedgerStore compiler(
        root, {RuntimeArtifactLedgerRole::PlanCompiler, "facade-qualification-compiler"});
    std::string digest, location, detail;
    for (const auto &[path, media] :
         {std::pair{sources.resolved_execution_plan_path,
                    "application/vnd.echelon-forge.resolved-execution-plan.v1+json"},
          std::pair{sources.request_path,
                    "application/vnd.echelon-forge.runtime-composition-request.v1+json"},
          std::pair{sources.resolved_input_lock_path,
                    "application/vnd.echelon-forge.resolved-input-lock.v1+json"}}) {
        auto bytes = read(path);
        if (path == sources.request_path) bytes = canonical(Json::parse(bytes));
        if (!compiler.put_artifact(bytes, media, "active-release", digest, location, detail))
            throw std::runtime_error("qualification input staging failed: " + detail);
    }
}
BatchWorldSetupRequest scene() {
    BatchWorldSetupRequest request;
    WorldSpawnRequest spawn;
    spawn.world_index = 0;
    spawn.type_name = "Aircraft";
    spawn.side = Side::Blue;
    spawn.z = 3000.0;
    request.spawn_requests = {spawn};
    return request;
}
Json reopen(const std::filesystem::path &root, const std::string &run) {
    RuntimeFileArtifactLedgerStore reader(
        root, {RuntimeArtifactLedgerRole::ReadOnlyAuditor, "facade-qualification-auditor"});
    std::string bytes, detail;
    if (!reader.read_receipt(run, bytes, detail))
        throw std::runtime_error("native durable reopen failed: " + detail);
    return Json::parse(bytes);
}
} // namespace

static void verify_positive_attempt(std::uint64_t steps) {
    Directory directory;
    auto lock = directory.path / "input-lock.json";
    if (const auto *external = std::getenv("EF_FACADE_INPUT_LOCK_PATH"))
        lock = external;
    else
        write(lock, R"({"effective_seed_set":[42]})");
    const auto sources = sources_for(lock);
    const auto root = directory.path / "ledger";
    stage(root, sources);
    Json evidence;
    {
        RuntimeFileArtifactLedgerStore store(
            root, {RuntimeArtifactLedgerRole::RuntimeHost, "facade-qualification-host"});
        auto config = measured_config("facade-current-attempt", sources);
        config.expected_steps = steps;
        RuntimeFacadeRunQualification run(store, config);
        CHECK_FALSE(run.facade_constructed());
        const auto admitted = run.start();
        INFO(admitted.detail);
        REQUIRE(admitted);
        REQUIRE(run.facade_constructed());
        REQUIRE_FALSE(run.facade_destroyed());
        const auto initialized = run.setup(scene());
        INFO(initialized.detail);
        REQUIRE(initialized);
        for (std::uint64_t step = 0; step < steps; ++step)
            REQUIRE(run.step());
        const auto completed = run.finish();
        INFO(completed.detail);
        REQUIRE(completed);
        REQUIRE(run.facade_destroyed());
        evidence = Json::parse(run.evidence_json());
        CHECK(evidence.at("steps_completed") == steps);
        CHECK(evidence.at("seed") == 42);
        CHECK(evidence.at("host_mode") == "native_cpp");
    }
    const auto receipt = reopen(root, "facade-current-attempt");
    const auto &payload = receipt.at("payload");
    CHECK(payload.at("run_id") == evidence.at("run_id"));
    CHECK(payload.at("terminal_state") == "completed");
    CHECK(payload.at("host_boot_id") == evidence.at("host_boot_id"));
    CHECK(payload.at("execution_scope").at("world_ids").front() == evidence.at("world_id"));
    CHECK(payload.at("execution_scope").at("episode_ids").front() == evidence.at("episode_id"));
    CHECK(payload.at("inputs").at("artifacts").at("resolved_input_lock") ==
          authority::sha256_hex(read(lock)));
    write(directory.path / "observed.json", evidence.dump());
}

TEST_CASE("maintained facade records a real fixed-step attempt") {
    const auto *steps = std::getenv("EF_FACADE_FIXED_STEPS");
    verify_positive_attempt(steps == nullptr ? 3 : std::stoull(steps));
}

TEST_CASE("maintained facade records seven native steps") {
    verify_positive_attempt(7);
}

TEST_CASE("maintained facade rejects admission before constructing the native owner") {
    Directory directory;
    const auto lock = directory.path / "input-lock.json";
    write(lock, R"({"effective_seed_set":[42]})");
    const auto sources = sources_for(lock);
    const auto root = directory.path / "ledger";
    stage(root, sources);
    auto config = measured_config("rejected-attempt", sources);
    SUBCASE("header names a different run") {
        config.run_id = "other-attempt";
    }
    SUBCASE("zero budget is rejected instead of pretending completion") {
        config.expected_steps = 0;
    }
    {
        RuntimeFileArtifactLedgerStore store(
            root, {RuntimeArtifactLedgerRole::RuntimeHost, "facade-qualification-host"});
        RuntimeFacadeRunQualification run(store, config);
        CHECK_FALSE(run.start());
        CHECK_FALSE(run.facade_constructed());
        CHECK_FALSE(run.facade_destroyed());
        CHECK(run.evidence_json().empty());
    }
    RuntimeFileArtifactLedgerStore reader(
        root, {RuntimeArtifactLedgerRole::ReadOnlyAuditor, "facade-qualification-auditor"});
    std::string bytes, detail;
    CHECK_FALSE(reader.read_receipt(config.run_id, bytes, detail));
}

TEST_CASE("maintained facade rejects real native outcome drift") {
    std::string mode;
    SUBCASE("no native steps") {
        mode = "zero";
    }
    SUBCASE("fewer native steps") {
        mode = "short";
    }
    SUBCASE("more native steps") {
        mode = "long";
    }
    SUBCASE("actual native seed reset") {
        mode = "seed";
    }
    SUBCASE("actual same-seed reset and new episode") {
        mode = "reset";
    }
    SUBCASE("actual partial native setup fault fences the generation") {
        mode = "health";
    }
    SUBCASE("actual input source bytes drift after admission") {
        mode = "payload";
    }
    Directory directory;
    const auto lock = directory.path / "input-lock.json";
    write(lock, R"({"effective_seed_set":[42]})");
    const auto sources = sources_for(lock);
    const auto root = directory.path / "ledger";
    stage(root, sources);
    {
        RuntimeFileArtifactLedgerStore store(
            root, {RuntimeArtifactLedgerRole::RuntimeHost, "facade-qualification-host"});
        RuntimeFacadeRunQualification run(store, measured_config("failed-attempt", sources));
        REQUIRE(run.start());
        REQUIRE(run.setup(scene()));
        const unsigned steps = mode == "zero" ? 0 : mode == "short" ? 2 : mode == "long" ? 4 : 3;
        for (unsigned step = 0; step < steps; ++step)
            REQUIRE(run.step());
        auto &native = RuntimeFacadeRunQualificationTestAccess::facade(run);
        if (mode == "seed") native.reset_batch(BatchResetRequest{.seeds = {239}});
        if (mode == "reset") {
            const auto dt = static_cast<double>(16666667) / 1'000'000'000.0;
            auto next_episode = scene();
            next_episode.seeds = {42};
            next_episode.time_steps = {dt};
            (void)native.apply_world_setup(next_episode);
            for (unsigned step = 0; step < 3; ++step)
                native.step_batch();
        }
        if (mode == "health") {
            auto invalid = scene();
            invalid.seeds = {42};
            invalid.terrain_assignments = {{.world_index = 0, .terrain_type = "invalid-terrain"}};
            CHECK_THROWS(native.apply_world_setup(invalid));
            CHECK_FALSE(native.batch_failure_status().healthy);
            REQUIRE_FALSE(native.batch_failure_status().requires_host_recreate);
        }
        if (mode == "payload") write(lock, R"({"effective_seed_set":[239]})");
        const auto finished = run.finish();
        INFO(mode, ": ", finished.detail);
        CHECK_FALSE(finished);
        CHECK(run.facade_destroyed());
        CHECK(run.evidence_json().empty());
    }
    const auto receipt = reopen(root, "failed-attempt");
    const auto &payload = receipt.at("payload");
    CHECK(payload.at("terminal_state") == "failed");
    CHECK(payload.at("completion").at("durable_ack") == true);
    CHECK(payload.at("results").at("native_validation").at("accepted") == false);
    CHECK(payload.at("results").at("result_digest") == "");
    CHECK(payload.at("results").at("output_artifacts").empty());
}

TEST_CASE("maintained facade receipt independently reopens" * doctest::skip()) {
    const auto *output = std::getenv("EF_FACADE_RUN_OUTPUT");
    REQUIRE(output != nullptr);
    const std::filesystem::path directory(output);
    const auto *requested_run = std::getenv("EF_FACADE_AUDIT_RUN_ID");
    const std::string run_id = requested_run == nullptr ? "facade-current-attempt" : requested_run;
    if (std::getenv("EF_FACADE_EXPECT_REOPEN_FAILURE") != nullptr) {
        RuntimeFileArtifactLedgerStore reader(
            directory / "ledger",
            {RuntimeArtifactLedgerRole::ReadOnlyAuditor, "facade-qualification-negative-auditor"});
        std::string bytes, detail;
        CHECK_FALSE(reader.read_receipt(run_id, bytes, detail));
        CHECK_FALSE(detail.empty());
        return;
    }
    const auto receipt = reopen(directory / "ledger", run_id);
    write(directory / "receipt.json", receipt.dump());
}
