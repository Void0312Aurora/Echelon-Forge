#include "runtime/host/integration/runtime_kernel_candidate.h"
#include "runtime/host/integration/runtime_kernel_candidate_facade.h"
#include "runtime/contracts/authority/runtime_authority_contract.h"

#include <doctest/doctest.h>

#include <cstdint>
#include <filesystem>
#include <fstream>
#include <functional>
#include <nlohmann/json.hpp>
#include <sstream>
#include <string>
#include <vector>

using runtime::host::RuntimeHostState;
using runtime::host::integration::RuntimeKernelCandidate;

namespace {

class CandidateRunStore final : public runtime::host::RuntimeRunRecorderStore {
  public:
    bool acquire_fence(std::string_view, std::string_view, std::uint64_t &generation,
                       std::string &detail) override {
        if (!available) {
            detail = "store unavailable";
            return false;
        }
        generation = 1;
        return true;
    }

    bool commit_header(std::string_view, std::uint64_t, std::string_view, std::string_view,
                       std::string &detail) override {
        if (!available) {
            detail = "store unavailable";
            return false;
        }
        header_committed = true;
        return true;
    }

    bool resume_journal(std::string_view, std::uint64_t, std::string_view, std::string_view,
                        std::uint64_t &next_sequence, std::string &last_record_sha256,
                        std::string &detail) override {
        if (!available || !header_committed) {
            detail = "store unavailable or header absent";
            return false;
        }
        next_sequence = records.size();
        last_record_sha256 = records.empty()
                                 ? std::string{}
                                 : runtime::authority_contracts::sha256_hex(records.back());
        return true;
    }

    bool append_record(std::string_view, std::uint64_t, std::string_view,
                       std::uint64_t sequence,
                       std::string_view payload, runtime::host::RuntimeRunRecorderAppendAck &ack,
                       std::string &detail) override {
        if (!available) {
            detail = "store unavailable";
            return false;
        }
        if (fail_sequence.has_value() && sequence == *fail_sequence) {
            fail_sequence.reset();
            detail = "injected append failure";
            return false;
        }
        if (!header_committed || sequence != records.size()) {
            detail = "append before header or out of sequence";
            return false;
        }
        records.emplace_back(payload);
        const auto digest = runtime::authority_contracts::sha256_hex(payload);
        ack = {.durable = true,
               .sequence = sequence,
               .payload_sha256 = digest,
               .record_sha256 = digest};
        return true;
    }

    bool finalize_receipt(std::string_view, std::uint64_t, std::string_view,
                          std::string_view receipt_json,
                          runtime::host::RuntimeRunRecorderFinalizeAck &ack,
                          std::string &detail) override {
        if (!available || !header_committed) {
            detail = "store unavailable or header absent";
            return false;
        }
        final_receipt = nlohmann::json::parse(receipt_json.begin(), receipt_json.end());
        ack = {.durable = true,
               .receipt_sha256 = final_receipt.at("payload_sha256").get<std::string>()};
        finalized = true;
        return true;
    }

    bool commit_checkpoint(std::string_view, std::uint64_t, std::string_view,
                           std::string_view checkpoint_json,
                           std::string_view validation_json,
                           runtime::host::RuntimeRunRecorderCheckpointAck &ack,
                           std::string &) override {
        if (checkpoint_callback) checkpoint_callback();
        ack = {.durable = true,
               .checkpoint_sha256 = runtime::authority_contracts::sha256_hex(checkpoint_json),
               .validation_sha256 = runtime::authority_contracts::sha256_hex(validation_json),
               .state_schema_generation = "1"};
        return true;
    }

    bool put_artifact(std::string_view bytes, std::string_view, std::string_view,
                      std::string &digest, std::string &retrieval_location,
                      std::string &) override {
        digest = runtime::authority_contracts::sha256_hex(bytes);
        retrieval_location = "ledger://blob-" + digest;
        return true;
    }

    bool available = true;
    bool header_committed = false;
    bool finalized = false;
    std::optional<std::uint64_t> fail_sequence;
    std::function<void()> checkpoint_callback;
    std::vector<std::string> records;
    nlohmann::json final_receipt;
};

std::string checkpoint_for_run(std::string_view run_id) {
    std::ifstream input(EF_STATE_CHECKPOINT_VECTOR_PATH, std::ios::binary);
    std::ostringstream buffer;
    buffer << input.rdbuf();
    auto envelope = nlohmann::json::parse(buffer.str()).at("envelope_json");
    auto checkpoint = nlohmann::json::parse(envelope.get<std::string>());
    checkpoint.at("payload").at("run_id") = run_id;
    const auto canonical_payload =
        runtime::authority_contracts::canonical_authority_json(checkpoint.at("payload").dump())
            .value();
    checkpoint.at("payload_sha256") = runtime::authority_contracts::authority_digest_sha256_hex(
        "runtime.state-checkpoint", "application/vnd.echelon-forge.state-checkpoint.v1+json",
        canonical_payload);
    return runtime::authority_contracts::canonical_authority_json(checkpoint.dump()).value();
}

std::string authority_envelope_from_vector(const char *path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) throw std::runtime_error("failed to open authority envelope vector");
    std::ostringstream buffer;
    buffer << input.rdbuf();
    return nlohmann::json::parse(buffer.str()).at("envelope_json").get<std::string>();
}

runtime::host::RuntimeExecutionProvenanceSources execution_sources() {
#if defined(NDEBUG)
    constexpr auto build_mode = "Release";
#else
    constexpr auto build_mode = "Debug";
#endif
    return {
        .resolved_execution_plan_path = EF_RESOLVED_EXECUTION_PLAN_PATH,
        .request_path = EF_RUNTIME_COMPOSITION_REQUEST_PATH,
        .package_path = EF_CANDIDATE_RELEASE_PACKAGE_PATH,
        .wheel_path = EF_CANDIDATE_RELEASE_PACKAGE_PATH,
        .owner_facts = {
            .build_mode = build_mode,
            .build_dirty = false,
            .linker = "link.exe",
            .cxx_abi = "msvc-native",
            .python_abi = "cp312-win_amd64",
            .node_abi = "native-runtime",
        },
    };
}

std::string file_bytes(const char *path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) throw std::runtime_error("failed to open test authority input");
    std::ostringstream buffer;
    buffer << input.rdbuf();
    return buffer.str();
}

std::string rollout_envelope_for_plan(std::string_view plan_sha256) {
    auto rollout = nlohmann::json::parse(
        authority_envelope_from_vector(EF_ROLLOUT_AUTHORITY_VECTOR_PATH));
    rollout.at("payload")["plan_sha256"] = plan_sha256;
    const auto canonical_payload =
        runtime::authority_contracts::canonical_authority_json(rollout.at("payload").dump())
            .value();
    rollout["payload_sha256"] = runtime::authority_contracts::authority_digest_sha256_hex(
        "release.rollout-decision",
        "application/vnd.echelon-forge.rollout-decision.v1+json", canonical_payload);
    return runtime::authority_contracts::canonical_authority_json(rollout.dump()).value();
}

std::string receipt_template_for_run(
    std::string_view run_id, std::string_view plan_sha256_override = {},
    const runtime::host::RuntimeExecutionProvenanceSources &sources = execution_sources()) {
    std::ifstream input(EF_RUN_RECEIPT_VECTOR_PATH, std::ios::binary);
    if (!input) throw std::runtime_error("failed to open canonical RunReceipt vector");
    std::ostringstream buffer;
    buffer << input.rdbuf();
    const auto vector = nlohmann::json::parse(buffer.str());
    auto receipt = nlohmann::json::parse(vector.at("canonical_envelope_json").get<std::string>());
    receipt.at("payload")["receipt_id"] = "receipt-" + std::string(run_id);
    receipt.at("payload")["attempt_id"] = "attempt-" + std::string(run_id);
    receipt.at("payload").at("run_id") = run_id;
    receipt.at("payload").at("journal_id") = run_id;
    const auto plan_bytes = file_bytes(EF_RESOLVED_EXECUTION_PLAN_PATH);
    const auto plan = nlohmann::json::parse(plan_bytes);
    const std::string plan_sha256 = plan_sha256_override.empty()
                                        ? plan.at("plan_sha256").get<std::string>()
                                        : std::string(plan_sha256_override);
    receipt.at("payload").at("plan_binding") = {
        {"compiler_identity", "PlanCompiler"},
        {"compiler_version", "1.0.0"},
        {"plan_canonical_sha256", plan_sha256},
        {"plan_generation", plan.at("writer_generation")},
        {"plan_id", plan.at("plan_id")},
        {"plan_location", "ledger://blob-" + runtime::authority_contracts::sha256_hex(plan_bytes)},
        {"plan_sha256", plan_sha256},
        {"request_canonical_sha256", plan.at("input_bindings").at("request_sha256")},
        {"request_location",
         "ledger://blob-" +
             plan.at("input_bindings").at("request_sha256").get<std::string>()},
        {"request_sha256", plan.at("input_bindings").at("request_sha256")},
    };
    const auto release_envelope = authority_envelope_from_vector(EF_RELEASE_AUTHORITY_VECTOR_PATH);
    const auto rollout_envelope = rollout_envelope_for_plan(plan_sha256);
    const auto release = nlohmann::json::parse(release_envelope);
    const auto rollout = nlohmann::json::parse(rollout_envelope);
    receipt.at("payload")["reader_generation_min"] = plan.at("reader_generation_min");
    receipt.at("payload")["reader_generation_max"] = plan.at("reader_generation_max");
    receipt.at("payload").at("release_binding") = {
        {"release_id", release.at("payload").at("release_id")},
        {"release_manifest_sha256", release.at("payload_sha256")},
        {"rollout_decision_id", rollout.at("payload").at("decision_id")},
        {"rollout_decision_sha256", rollout.at("payload_sha256")},
        {"provenance_sha256", release.at("payload").at("provenance_sha256")},
        {"sbom_sha256", release.at("payload").at("sbom_sha256")},
        {"attestation_sha256", receipt.at("payload").at("release_binding").at("attestation_sha256")},
    };
    receipt.at("payload").at("package")["identity"] = "cmo";
    receipt.at("payload").at("build")["source_revision"] =
        release.at("payload").at("source_revision");
    receipt.at("payload").at("build")["toolchain"] =
        release.at("payload").at("toolchain_identity");
    receipt.at("payload").at("inputs")["artifacts"] = {
        {"request", plan.at("input_bindings").at("request_sha256")},
        {"resolved_execution_plan", runtime::authority_contracts::sha256_hex(plan_bytes)},
    };
    nlohmann::json measurement_template = {
        {"backend", receipt.at("payload").at("backend")},
        {"build", receipt.at("payload").at("build")},
        {"executable", receipt.at("payload").at("executable")},
        {"inputs", receipt.at("payload").at("inputs")},
        {"package", receipt.at("payload").at("package")},
        {"platform", receipt.at("payload").at("platform")},
        {"plan_binding", receipt.at("payload").at("plan_binding")},
        {"reader_generation_max", receipt.at("payload").at("reader_generation_max")},
        {"reader_generation_min", receipt.at("payload").at("reader_generation_min")},
        {"release_manifest_envelope_json", release_envelope},
        {"rollout_decision_envelope_json", rollout_envelope},
    };
    std::string observed_json;
    std::string observed_detail;
    if (!runtime::host::collect_runtime_execution_bindings_json(
            sources, measurement_template.dump(), observed_json, observed_detail)) {
        throw std::runtime_error("failed to collect test execution provenance: " +
                                 observed_detail);
    }
    const auto observed = nlohmann::json::parse(observed_json);
    for (const auto section : {"backend", "build", "executable", "inputs", "package", "platform"}) {
        receipt.at("payload")[section] = observed.at(section);
    }
    return receipt.dump();
}

std::string run_header_for_run(
    std::string_view run_id, std::string_view plan_sha256_override = {},
    const runtime::host::RuntimeExecutionProvenanceSources &sources = execution_sources()) {
    const auto receipt = nlohmann::json::parse(
        receipt_template_for_run(run_id, plan_sha256_override, sources));
    const auto &payload = receipt.at("payload");
    nlohmann::json bindings = {
        {"attempt_id", payload.at("attempt_id")},
        {"backend", payload.at("backend")},
        {"build", payload.at("build")},
        {"executable", payload.at("executable")},
        {"inputs", payload.at("inputs")},
        {"package", payload.at("package")},
        {"platform", payload.at("platform")},
        {"plan_binding", payload.at("plan_binding")},
        {"reader_generation_max", payload.at("reader_generation_max")},
        {"reader_generation_min", payload.at("reader_generation_min")},
        {"receipt_id", payload.at("receipt_id")},
        {"release_binding", payload.at("release_binding")},
        {"release_manifest_envelope_json",
         authority_envelope_from_vector(EF_RELEASE_AUTHORITY_VECTOR_PATH)},
        {"rollout_decision_envelope_json",
         rollout_envelope_for_plan(payload.at("plan_binding").at("plan_sha256").get<std::string>())},
    };
    const nlohmann::json measurement_material = {
        {"executable", bindings.at("executable")},
        {"inputs", bindings.at("inputs")},
        {"package", bindings.at("package")},
        {"platform", bindings.at("platform")},
    };
    const auto canonical_measurement =
        runtime::authority_contracts::canonical_authority_json(measurement_material.dump()).value();
    auto admission_material = bindings;
    admission_material.erase("release_manifest_envelope_json");
    admission_material.erase("rollout_decision_envelope_json");
    const auto canonical_bindings =
        runtime::authority_contracts::canonical_authority_json(admission_material.dump()).value();
    const nlohmann::json header = {
        {"admission_binding_sha256",
         runtime::authority_contracts::sha256_hex(canonical_bindings)},
        {"observed_measurement_sha256",
         runtime::authority_contracts::sha256_hex(canonical_measurement)},
        {"receipt_bindings", bindings},
        {"run_id", run_id},
    };
    return runtime::authority_contracts::canonical_authority_json(header.dump()).value();
}

} // namespace

TEST_SUITE("runtime_kernel_candidate") {

    TEST_CASE("P5-B recorder admission and mutation ACKs gate the real candidate") {
        CandidateRunStore tampered_authority_store;
        auto tampered_header = nlohmann::json::parse(run_header_for_run("run-tampered-authority"));
        auto tampered_rollout = nlohmann::json::parse(
            tampered_header.at("receipt_bindings")
                .at("rollout_decision_envelope_json")
                .get<std::string>());
        tampered_rollout.at("payload")["release_id"] = "release-forged";
        tampered_header.at("receipt_bindings")["rollout_decision_envelope_json"] =
            runtime::authority_contracts::canonical_authority_json(tampered_rollout.dump()).value();
        const auto tampered_header_json =
            runtime::authority_contracts::canonical_authority_json(tampered_header.dump()).value();
        CHECK_THROWS_AS(RuntimeKernelCandidate({
                            .host_id = {.high = 0x5035422D41555448ULL, .low = 1},
                            .run_recorder_store = &tampered_authority_store,
                            .run_id = "run-tampered-authority",
                            .run_writer_id = "writer-1",
                            .run_header_json = tampered_header_json,
                            .run_receipt_template_json =
                                receipt_template_for_run("run-tampered-authority"),
                            .run_execution_sources = execution_sources(),
                        }),
                        std::invalid_argument);
        CHECK_FALSE(tampered_authority_store.header_committed);

        CandidateRunStore mismatched_provenance_store;
        auto mismatched_sources = execution_sources();
        mismatched_sources.wheel_path = EF_RUN_RECEIPT_VECTOR_PATH;
        CHECK_THROWS_AS(RuntimeKernelCandidate({
                            .host_id = {.high = 0x5035422D50524F56ULL, .low = 1},
                            .run_recorder_store = &mismatched_provenance_store,
                            .run_id = "run-mismatched-provenance",
                            .run_writer_id = "writer-1",
                            .run_header_json =
                                run_header_for_run("run-mismatched-provenance"),
                            .run_receipt_template_json =
                                receipt_template_for_run("run-mismatched-provenance"),
                            .run_execution_sources = mismatched_sources,
                        }),
                        std::invalid_argument);
        CHECK_FALSE(mismatched_provenance_store.header_committed);

        CandidateRunStore missing_owner_facts_store;
        auto missing_owner_facts = execution_sources();
        missing_owner_facts.owner_facts.build_mode.clear();
        CHECK_THROWS_AS(RuntimeKernelCandidate({
                            .host_id = {.high = 0x5035422D4F574E52ULL, .low = 1},
                            .run_recorder_store = &missing_owner_facts_store,
                            .run_id = "run-missing-owner-facts",
                            .run_writer_id = "writer-1",
                            .run_header_json = run_header_for_run(
                                "run-missing-owner-facts"),
                            .run_receipt_template_json = receipt_template_for_run(
                                "run-missing-owner-facts"),
                            .run_execution_sources = missing_owner_facts,
                        }),
                        std::invalid_argument);
        CHECK_FALSE(missing_owner_facts_store.header_committed);

        CandidateRunStore mismatched_build_facts_store;
        auto mismatched_build_facts = execution_sources();
        mismatched_build_facts.owner_facts.build_mode =
            mismatched_build_facts.owner_facts.build_mode == "Debug" ? "Release" : "Debug";
        CHECK_THROWS_AS(RuntimeKernelCandidate({
                            .host_id = {.high = 0x5035422D4255494CULL, .low = 1},
                            .run_recorder_store = &mismatched_build_facts_store,
                            .run_id = "run-mismatched-build-facts",
                            .run_writer_id = "writer-1",
                            .run_header_json =
                                run_header_for_run("run-mismatched-build-facts"),
                            .run_receipt_template_json =
                                receipt_template_for_run("run-mismatched-build-facts"),
                            .run_execution_sources = mismatched_build_facts,
                        }),
                        std::invalid_argument);
        CHECK_FALSE(mismatched_build_facts_store.header_committed);

        CandidateRunStore mismatched_request_store;
        auto mismatched_request = execution_sources();
        mismatched_request.request_path = EF_RESOLVED_EXECUTION_PLAN_PATH;
        CHECK_THROWS_AS(RuntimeKernelCandidate({
                            .host_id = {.high = 0x5035422D52455155ULL, .low = 1},
                            .run_recorder_store = &mismatched_request_store,
                            .run_id = "run-mismatched-request",
                            .run_writer_id = "writer-1",
                            .run_header_json = run_header_for_run("run-mismatched-request"),
                            .run_receipt_template_json =
                                receipt_template_for_run("run-mismatched-request"),
                            .run_execution_sources = mismatched_request,
                        }),
                        std::invalid_argument);
        CHECK_FALSE(mismatched_request_store.header_committed);

        CandidateRunStore unavailable;
        unavailable.available = false;
        CHECK_THROWS_AS(RuntimeKernelCandidate({
                            .host_id = {.high = 0x5035422D52454A45ULL, .low = 1},
                            .run_recorder_store = &unavailable,
                            .run_id = "run-rejected",
                            .run_writer_id = "writer-1",
                            .run_header_json = run_header_for_run("run-rejected"),
                            .run_receipt_template_json = receipt_template_for_run("run-rejected"),
                            .run_execution_sources = execution_sources(),
                        }),
                        std::invalid_argument);
        CHECK(unavailable.records.empty());

        CandidateRunStore store;
        RuntimeKernelCandidate admitted({
            .host_id = {.high = 0x5035422D41444D49ULL, .low = 1},
            .run_recorder_store = &store,
            .run_id = "run-admitted",
            .run_writer_id = "writer-1",
            .run_header_json = run_header_for_run("run-admitted"),
            .run_receipt_template_json = receipt_template_for_run("run-admitted"),
            .run_execution_sources = execution_sources(),
        });
        REQUIRE(store.header_committed);
        REQUIRE(admitted.start());
        bool checkpoint_mutation_blocked = false;
        store.checkpoint_callback = [&] {
            checkpoint_mutation_blocked = !admitted.step(admitted.world_ref());
        };
        const auto checkpoint_status = admitted.persist_checkpoint(
            checkpoint_for_run("run-admitted"),
            R"({"accepted":true,"checkpoint_id":"checkpoint-1"})");
        INFO(checkpoint_status.code);
        INFO(checkpoint_status.detail);
        CHECK(checkpoint_status);
        CHECK(checkpoint_mutation_blocked);
        REQUIRE(store.records.size() == 9);
        CHECK(store.records.front().find(R"("lifecycle_event":"journal_admitted")") !=
              std::string::npos);
        CHECK(store.records.at(1).find(R"("event":"runtime_configuration")") !=
              std::string::npos);
        CHECK(store.records.at(1).find(R"("phase":"intent")") != std::string::npos);
        CHECK(store.records.at(1).find(R"("seed":42)") != std::string::npos);
        CHECK(store.records.at(1).find(R"("time_step_ns":16666667)") !=
              std::string::npos);
        CHECK(store.records.at(2).find(R"("phase":"outcome")") != std::string::npos);
        CHECK(store.records.at(7).find(R"("lifecycle_event":"episode")") !=
              std::string::npos);
        CHECK(store.records.back().find(R"("event":"checkpoint_commit")") !=
              std::string::npos);

        WorldSpawnRequest request{};
        request.side = Side::Blue;
        request.type_name = "Aircraft";
        REQUIRE(admitted.spawn_unit(admitted.world_ref(), request).has_value());
        REQUIRE(store.records.size() == 12);
        CHECK(store.records.at(9).find(R"("operation":"spawn_unit")") != std::string::npos);
        CHECK(store.records.at(9).find(R"("phase":"intent")") != std::string::npos);
        CHECK(store.records.at(10).find(R"("phase":"outcome")") != std::string::npos);
        CHECK(store.records.back().find(R"("event":"runtime_entity_observed")") !=
              std::string::npos);

        const auto episode_before = admitted.episode_ref();
        store.available = false;
        CHECK_FALSE(admitted.step(admitted.world_ref()));
        CHECK(admitted.episode_ref() == episode_before);
        store.available = true;
        const auto shutdown = admitted.shutdown(1, 10);
        REQUIRE(shutdown.status);
        CHECK(shutdown.state == RuntimeHostState::Stopped);
        REQUIRE(store.finalized);
        CHECK(store.final_receipt.at("payload").at("terminal_state") == "failed");
        CHECK(store.final_receipt.at("payload").at("terminal_reason") ==
              "durable evidence append failed");
        CHECK(store.final_receipt.at("payload")
                  .at("results")
                  .at("native_validation")
                  .at("accepted") == false);

        CandidateRunStore terminal_store;
        auto tampered_template =
            nlohmann::json::parse(receipt_template_for_run("run-completed"));
        auto &tampered_payload = tampered_template.at("payload");
        tampered_payload["receipt_id"] = "receipt-forged";
        tampered_payload["attempt_id"] = "attempt-forged";
        tampered_payload["host_boot_id"] = "boot-forged";
        tampered_payload["incarnation_epoch"] = "999";
        tampered_payload["execution_scope"] =
            nlohmann::json{{"world_ids", {"world-forged"}},
                           {"entity_ids", {"entity-forged"}},
                           {"episode_ids", {"episode-forged"}},
                           {"request_ids", {"request-forged"}},
                           {"epochs", {{"world", "999"},
                                       {"entity", "999"},
                                       {"episode", "999"},
                                       {"request", "999"}}}};
        tampered_payload.at("results").at("output_artifacts").push_back(
            tampered_payload.at("results").at("output_artifacts").front());
        tampered_payload.at("results").at("output_artifacts").front()["name"] = "forged-output";
        tampered_payload["checkpoints"] = {
            {"source_refs", {nlohmann::json{{"checkpoint_id", "forged-source"}}}},
            {"created_refs", {nlohmann::json{{"checkpoint_id", "forged-created"}}}},
        };
        tampered_payload["qualification_refs"] =
            nlohmann::json::array({{{"identity", "forged"}, {"digest", std::string(64, 'f')}}});
        tampered_payload["side_effect_receipts"] = nlohmann::json::array(
            {{{"identity", "forged"},
              {"digest", std::string(64, 'f')},
              {"media_type", "application/forged"},
              {"retrieval_location", "workspace://forged"}}});
        tampered_payload["authenticity"] =
            {{"attestation_sha256", std::string(64, 'f')}, {"signatures", nlohmann::json::array()}};
        RuntimeKernelCandidate completed({
            .host_id = {.high = 0x5035422D434F4D50ULL, .low = 1},
            .run_recorder_store = &terminal_store,
            .run_id = "run-completed",
            .run_writer_id = "writer-1",
            .run_header_json = run_header_for_run("run-completed"),
            .run_receipt_template_json = tampered_template.dump(),
            .run_execution_sources = execution_sources(),
        });
        REQUIRE(completed.start());
        REQUIRE(completed.spawn_unit(completed.world_ref(), request).has_value());
        const auto completed_shutdown = completed.shutdown(1, 10);
        INFO(completed_shutdown.status.detail);
        REQUIRE(completed_shutdown.status);
        REQUIRE(terminal_store.finalized);
        CHECK(terminal_store.final_receipt.at("payload").at("run_id") == "run-completed");
        CHECK(terminal_store.final_receipt.at("payload").at("receipt_id") ==
              "receipt-run-completed");
        CHECK(terminal_store.final_receipt.at("payload").at("attempt_id") ==
              "attempt-run-completed");
        CHECK(terminal_store.final_receipt.at("payload").at("host_boot_id") != "boot-forged");
        CHECK(terminal_store.final_receipt.at("payload").at("incarnation_epoch") != "999");
        CHECK(terminal_store.final_receipt.at("payload").at("terminal_state") == "completed");
        CHECK(terminal_store.final_receipt.at("payload")
                  .at("results")
                  .at("native_validation")
                  .at("accepted") == true);
        CHECK(terminal_store.final_receipt.at("payload").at("results").at("result_digest") ==
              terminal_store.final_receipt.at("payload")
                  .at("results")
                  .at("native_validation")
                  .at("evidence_sha256"));
        const auto &owner_outputs =
            terminal_store.final_receipt.at("payload").at("results").at("output_artifacts");
        REQUIRE(owner_outputs.size() == 1);
        CHECK(owner_outputs.front().at("name") == "runtime-state");
        CHECK(owner_outputs.front().at("media_type") ==
              "application/vnd.echelon-forge.runtime-state.v1+octets");
        CHECK(terminal_store.final_receipt.at("payload").at("checkpoints").at("source_refs").empty());
        CHECK(terminal_store.final_receipt.at("payload").at("checkpoints").at("created_refs").empty());
        CHECK(terminal_store.final_receipt.at("payload").at("qualification_refs").empty());
        CHECK(terminal_store.final_receipt.at("payload").at("side_effect_receipts").empty());
        CHECK(terminal_store.final_receipt.at("payload").at("authenticity").at("attestation_sha256") !=
              std::string(64, 'f'));
        CHECK(terminal_store.final_receipt.at("payload").at("execution_scope").at("entity_ids").size() == 1);
        const auto &completed_lifecycle =
            terminal_store.final_receipt.at("payload").at("lifecycle");
        REQUIRE(completed_lifecycle.size() == 9);
        CHECK(completed_lifecycle.front().at("event") == "journal_admitted");
        CHECK(completed_lifecycle.back().at("event") == "terminal");
        CHECK(completed_lifecycle.back().at("durable_sequence") ==
              terminal_store.final_receipt.at("payload").at("journal_last_sequence"));

        const auto mutable_package =
            std::filesystem::temp_directory_path() / "ef_p5b_candidate_release_mutation.bin";
        std::error_code copy_error;
        std::filesystem::copy_file(EF_CANDIDATE_RELEASE_PACKAGE_PATH, mutable_package,
                                   std::filesystem::copy_options::overwrite_existing, copy_error);
        REQUIRE_FALSE(copy_error);
        auto mutable_sources = execution_sources();
        mutable_sources.package_path = mutable_package.string();
        mutable_sources.wheel_path = mutable_package.string();
        CandidateRunStore mutated_package_store;
        RuntimeKernelCandidate mutated_package_candidate({
            .host_id = {.high = 0x5035422D4D555441ULL, .low = 1},
            .run_recorder_store = &mutated_package_store,
            .run_id = "run-mutated-package",
            .run_writer_id = "writer-1",
            .run_header_json =
                run_header_for_run("run-mutated-package", {}, mutable_sources),
            .run_receipt_template_json =
                receipt_template_for_run("run-mutated-package", {}, mutable_sources),
            .run_execution_sources = mutable_sources,
        });
        REQUIRE(mutated_package_candidate.start());
        {
            std::ofstream output(mutable_package, std::ios::binary | std::ios::app);
            REQUIRE(output);
            output << "post-admission mutation\n";
        }
        const auto mutated_shutdown = mutated_package_candidate.shutdown(1, 10);
        INFO(mutated_shutdown.status.detail);
        REQUIRE(mutated_shutdown.status);
        REQUIRE(mutated_package_store.finalized);
        CHECK(mutated_package_store.final_receipt.at("payload").at("terminal_state") == "failed");
        CHECK(mutated_package_store.final_receipt.at("payload").at("terminal_reason") ==
              "execution provenance changed after admission");
        std::filesystem::remove(mutable_package, copy_error);

        CandidateRunStore outcome_failure_store;
        RuntimeKernelCandidate outcome_failure({
            .host_id = {.high = 0x5035422D4F555443ULL, .low = 1},
            .run_recorder_store = &outcome_failure_store,
            .run_id = "run-outcome-failure",
            .run_writer_id = "writer-1",
            .run_header_json = run_header_for_run("run-outcome-failure"),
            .run_receipt_template_json = receipt_template_for_run("run-outcome-failure"),
            .run_execution_sources = execution_sources(),
        });
        REQUIRE(outcome_failure.start());
        outcome_failure_store.fail_sequence = outcome_failure_store.records.size() + 1U;
        CHECK_FALSE(outcome_failure.spawn_unit(outcome_failure.world_ref(), request).has_value());
        REQUIRE(outcome_failure_store.finalized);
        CHECK(outcome_failure_store.final_receipt.at("payload").at("terminal_state") == "failed");
        CHECK(outcome_failure_store.final_receipt.at("payload").at("terminal_reason") ==
              "durable spawn outcome append failed after mutation");
        CHECK_FALSE(outcome_failure.step(outcome_failure.world_ref()));
    }

    TEST_CASE("P4-C candidate publishes only a fenced internal kernel") {
        RuntimeKernelCandidate candidate({
            .host_id = {.high = 0x5044432D484F5354ULL, .low = 1},
            .mode = runtime::host::RuntimeHostMode::Dark,
            .lifecycle_deadline_tick = 100,
        });

        REQUIRE(candidate.start());
        const auto snapshot = candidate.host_snapshot();
        REQUIRE(snapshot.state == RuntimeHostState::Active);
        REQUIRE(snapshot.active.has_value());
        CHECK_FALSE(snapshot.production_authorized);
        CHECK(candidate.composition_immutable());
        CHECK(candidate.composition_snapshot().resolved_manifest_sha256.size() == 64);

        const auto world = candidate.world_ref();
        REQUIRE(world.well_formed());
        WorldSpawnRequest request{};
        request.world_index = 0;
        request.side = Side::Blue;
        request.type_name = "Aircraft";
        request.x = 10.0;
        request.y = 20.0;
        request.z = 3000.0;
        const auto entity = candidate.spawn_unit(world, request);
        REQUIRE(entity.has_value());
        REQUIRE(entity->well_formed());

        WorldEntityKinematics before{};
        REQUIRE(candidate.try_get_entity_kinematics(*entity, &before));
        before.x = 99.0;
        REQUIRE(candidate.try_set_entity_kinematics(*entity, before));
        WorldEntityKinematics after{};
        REQUIRE(candidate.try_get_entity_kinematics(*entity, &after));
        CHECK(after.x == doctest::Approx(99.0));

        REQUIRE(candidate.step(world));
        CHECK(candidate.composition_immutable());

        auto stale_world = world;
        ++stale_world.world_generation;
        CHECK_FALSE(candidate.step(stale_world));
        auto stale_entity = *entity;
        ++stale_entity.entity_generation;
        CHECK_FALSE(candidate.try_get_entity_kinematics(stale_entity, &after));

        const auto running_episode = candidate.episode_ref();
        REQUIRE(running_episode.well_formed());
        candidate.arm_terminal_receipt_for_test();
        runtime::host::RuntimeEpisodeTransitionReceipt terminal_receipt{};
        REQUIRE(candidate.submit_episode(
            running_episode, runtime::host::RuntimeEpisodeIntentKind::Action,
            {.high = 0x4550432D5445524DULL, .low = 1}, std::string(64, 'c'), &terminal_receipt));
        REQUIRE(terminal_receipt.terminal);
        CHECK(candidate.episode_ref() == terminal_receipt.episode_after);
        WorldSpawnRequest terminal_spawn = request;
        terminal_spawn.x = 123.0;
        CHECK_FALSE(candidate.spawn_unit(candidate.world_ref(), terminal_spawn).has_value());
        CHECK_FALSE(candidate.try_set_entity_kinematics(*entity, before));
        runtime::host::RuntimeEpisodeTransitionReceipt reset_receipt{};
        REQUIRE(candidate.submit_episode(
            terminal_receipt.episode_after, runtime::host::RuntimeEpisodeIntentKind::Reset,
            {.high = 0x4550432D52455345ULL, .low = 1}, std::string(64, 'b'), &reset_receipt));
        REQUIRE(reset_receipt.reset_applied);
        CHECK(reset_receipt.episode_after.world.world_generation == world.world_generation + 1);
        CHECK_FALSE(candidate.try_get_entity_kinematics(*entity, &after));
        REQUIRE(candidate.step(candidate.world_ref()));

        const auto shutdown = candidate.shutdown(10, 100);
        REQUIRE(shutdown.status);
        CHECK(shutdown.state == RuntimeHostState::Stopped);
        CHECK(candidate.host_snapshot().state == RuntimeHostState::Stopped);
    }

    TEST_CASE("P4-C candidate rejects a plan hash that is not the sealed composition") {
        const std::string rejected_plan_sha256(64, 'f');
        RuntimeKernelCandidate candidate({
            .host_id = {.high = 0x5044432D504C414EULL, .low = 3},
            .plan = {.plan_id = "p4c.kernel-candidate.v1",
                     .plan_sha256 = rejected_plan_sha256},
        });
        CHECK_FALSE(candidate.start());

        RuntimeKernelCandidate partial({
            .host_id = {.high = 0x5044432D50415254ULL, .low = 4},
            .plan = {.plan_id = "p4c.kernel-candidate.v1"},
        });
        CHECK_FALSE(partial.start());

    }

    TEST_CASE("P4-C facade adapter keeps batch operations on epoch-bearing refs") {
        RuntimeKernelCandidate candidate({
            .host_id = {.high = 0x5044432D42415443ULL, .low = 2},
            .mode = runtime::host::RuntimeHostMode::Shadow,
            .lifecycle_deadline_tick = 100,
        });
        REQUIRE(candidate.start());
        runtime::host::integration::RuntimeKernelCandidateFacadeAdapter facade(candidate);

        WorldSpawnRequest first{};
        first.side = Side::Blue;
        first.type_name = "Aircraft";
        WorldSpawnRequest second = first;
        second.side = Side::Red;
        second.x = 100.0;
        const auto entities = facade.apply_spawn_batch({first, second});
        REQUIRE(entities.size() == 2);
        CHECK(entities.front().world == facade.world_ref());
        CHECK(entities.back().world == facade.world_ref());
        CHECK(facade.composition_immutable());
        CHECK(facade.step_batch());

        WorldSpawnRequest invalid = first;
        invalid.type_name.clear();
        const auto partial = facade.apply_spawn_batch({first, invalid});
        REQUIRE(partial.size() == 1);
        WorldEntityKinematics state{};
        CHECK(facade.try_get_entity_kinematics(partial.front(), &state));

        auto stale = entities.front();
        ++stale.world.incarnation.incarnation_epoch;
        CHECK_FALSE(facade.try_get_entity_kinematics(stale, &state));
        REQUIRE(candidate.shutdown(10, 100).status);
        CHECK_FALSE(facade.step_batch());
    }

    TEST_CASE("P4-C candidate sustains repeated epochs and fences retired references") {
        RuntimeKernelCandidate candidate({
            .host_id = {.high = 0x5044432D53545253ULL, .low = 5},
            .mode = runtime::host::RuntimeHostMode::Shadow,
            .lifecycle_deadline_tick = 1000,
        });

        REQUIRE(candidate.start());
        runtime::host::integration::RuntimeKernelCandidateFacadeAdapter facade(candidate);
        const auto sealed = candidate.composition_snapshot();
        const auto orphaned_before = runtime::host::RuntimeHostCandidate::orphaned_host_count();

        for (std::uint64_t cycle = 1; cycle <= 256; ++cycle) {
            const auto world = candidate.world_ref();
            WorldSpawnRequest request{};
            request.world_index = 0;
            request.side = cycle % 2 == 0 ? Side::Red : Side::Blue;
            request.type_name = "Aircraft";
            request.x = static_cast<double>(cycle);
            request.y = static_cast<double>(cycle * 2);
            request.z = 3000.0 + static_cast<double>(cycle);
            std::vector<WorldSpawnRequest> batch = {request, request, request, request};
            batch[1].side = Side::Red;
            batch[2].x += 10.0;
            batch[3].y += 10.0;
            const auto entities = facade.apply_spawn_batch(batch);
            REQUIRE(entities.size() == batch.size());
            REQUIRE(facade.step_batch());

            const auto running_episode = candidate.episode_ref();
            candidate.arm_terminal_receipt_for_test();
            runtime::host::RuntimeEpisodeTransitionReceipt terminal_receipt{};
            REQUIRE(candidate.submit_episode(running_episode,
                                             runtime::host::RuntimeEpisodeIntentKind::Action,
                                             {.high = 0x4550432D53545253ULL, .low = cycle},
                                             std::string(64, 'd'), &terminal_receipt));
            REQUIRE(terminal_receipt.terminal);

            const auto retired_entity = entities.front();
            runtime::host::RuntimeEpisodeTransitionReceipt reset_receipt{};
            REQUIRE(candidate.submit_episode(terminal_receipt.episode_after,
                                             runtime::host::RuntimeEpisodeIntentKind::Reset,
                                             {.high = 0x4550432D53545252ULL, .low = cycle},
                                             std::string(64, 'e'), &reset_receipt));
            REQUIRE(reset_receipt.reset_applied);

            WorldEntityKinematics state{};
            CHECK_FALSE(facade.try_get_entity_kinematics(retired_entity, &state));
            CHECK_FALSE(facade.try_set_entity_kinematics(retired_entity, state));
            CHECK(candidate.composition_snapshot() == sealed);
            CHECK(candidate.composition_immutable());
        }

        const auto shutdown = candidate.shutdown(10, 1000);
        REQUIRE(shutdown.status);
        CHECK(shutdown.state == runtime::host::RuntimeHostState::Stopped);
        CHECK(runtime::host::RuntimeHostCandidate::orphaned_host_count() <= orphaned_before);
    }

    TEST_CASE("P4-C candidate implicit teardown releases generated WAL ownership") {
        const auto orphaned_before = runtime::host::RuntimeHostCandidate::orphaned_host_count();
        {
            RuntimeKernelCandidate candidate({
                .host_id = {.high = 0x5044432D54454152ULL, .low = 6},
                .mode = runtime::host::RuntimeHostMode::Dark,
                .lifecycle_deadline_tick = 100,
            });
            REQUIRE(candidate.start());
            const auto entity =
                candidate.spawn_unit(candidate.world_ref(), WorldSpawnRequest{
                                                                .world_index = 0,
                                                                .side = Side::Blue,
                                                                .type_name = "Aircraft",
                                                                .x = 1.0,
                                                                .y = 2.0,
                                                                .z = 3000.0,
                                                            });
            REQUIRE(entity.has_value());
        }
        CHECK(runtime::host::RuntimeHostCandidate::orphaned_host_count() <= orphaned_before);
    }

    TEST_CASE("P5-B admitted candidate closed before start emits a cancelled receipt") {
        CandidateRunStore store;
        {
            RuntimeKernelCandidate candidate({
                .host_id = {.high = 0x5035422D43414E43ULL, .low = 1},
                .run_recorder_store = &store,
                .run_id = "run-cancelled",
                .run_writer_id = "writer-1",
                .run_header_json = run_header_for_run("run-cancelled"),
                .run_receipt_template_json = receipt_template_for_run("run-cancelled"),
                .run_execution_sources = execution_sources(),
            });
        }
        REQUIRE(store.finalized);
        CHECK(store.final_receipt.at("payload").at("terminal_state") == "cancelled");
        CHECK(store.final_receipt.at("payload").at("terminal_reason") ==
              "candidate closed before start");
    }

} // TEST_SUITE("runtime_kernel_candidate")
