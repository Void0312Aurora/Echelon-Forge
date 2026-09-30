#include <doctest/doctest.h>

#include <fstream>
#include <filesystem>
#include <sstream>
#include <string>
#include <utility>

#include <nlohmann/json.hpp>

#include "runtime_run_recorder.h"
#include "runtime_file_artifact_ledger_store.h"
#include "runtime/contracts/authority/runtime_authority_contract.h"

namespace {

runtime::host::RuntimeArtifactLedgerAccessContext
runtime_ledger_access(std::string identity = "runtime-test") {
    return {runtime::host::RuntimeArtifactLedgerRole::RuntimeHost, std::move(identity)};
}

runtime::host::RuntimeArtifactLedgerAccessContext
backup_ledger_access(std::string identity = "backup-test") {
    return {runtime::host::RuntimeArtifactLedgerRole::BackupOperator, std::move(identity)};
}

bool seed_authority_blobs(const std::filesystem::path &root) {
    auto read = [](const char *path) -> std::string {
        std::ifstream input(path, std::ios::binary);
        std::ostringstream bytes;
        bytes << input.rdbuf();
        return bytes.str();
    };
    runtime::host::RuntimeFileArtifactLedgerStore compiler(
        root, {runtime::host::RuntimeArtifactLedgerRole::PlanCompiler, "plan-compiler"});
    std::string digest;
    std::string location;
    std::string detail;
    const auto plan_bytes = read(EF_RESOLVED_EXECUTION_PLAN_PATH);
    const auto request = nlohmann::json::parse(read(EF_RUNTIME_COMPOSITION_REQUEST_PATH));
    const auto request_bytes =
        runtime::authority_contracts::canonical_authority_json(request.dump()).value();
    return compiler.put_artifact(plan_bytes,
                                 "application/vnd.echelon-forge.resolved-execution-plan.v1+json",
                                 "active-release", digest, location, detail) &&
           compiler.put_artifact(
               request_bytes, "application/vnd.echelon-forge.runtime-composition-request.v1+json",
               "active-release", digest, location, detail);
}

class FakeStore final : public runtime::host::RuntimeRunRecorderStore {
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
    bool commit_header(std::string_view, std::uint64_t, std::string_view, std::string_view header,
                       std::string &detail) override {
        if (!available) {
            detail = "store unavailable";
            return false;
        }
        if (header.find("run-1") == std::string_view::npos) {
            detail = "wrong header";
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
        next_sequence = appended_sequences;
        last_record_sha256 = last_record_digest;
        return true;
    }
    bool append_record(std::string_view, std::uint64_t, std::string_view, std::uint64_t sequence,
                       std::string_view payload, runtime::host::RuntimeRunRecorderAppendAck &ack,
                       std::string &detail) override {
        if (!header_committed) {
            detail = "header not committed";
            return false;
        }
        if (sequence != appended_sequences) {
            detail = "sequence mismatch";
            return false;
        }
        const auto digest = runtime::authority_contracts::sha256_hex(payload);
        ack = {true, sequence, forge_payload_ack ? std::string(64, 'f') : digest, digest};
        last_record_digest = digest;
        ++appended_sequences;
        return true;
    }
    bool finalize_receipt(std::string_view, std::uint64_t, std::string_view,
                          std::string_view receipt_json,
                          runtime::host::RuntimeRunRecorderFinalizeAck &ack,
                          std::string &detail) override {
        if (!header_committed) {
            detail = "header not committed";
            return false;
        }
        const auto receipt = nlohmann::json::parse(receipt_json.begin(), receipt_json.end());
        ack = {true, receipt.at("payload_sha256").get<std::string>()};
        final_receipt = receipt;
        finalized = true;
        if (fail_finalize_once_after_persist) {
            fail_finalize_once_after_persist = false;
            detail = "simulated outcome audit acknowledgement failure";
            return false;
        }
        return true;
    }

    bool commit_checkpoint(std::string_view, std::uint64_t, std::string_view,
                           std::string_view checkpoint_json, std::string_view validation_json,
                           runtime::host::RuntimeRunRecorderCheckpointAck &ack,
                           std::string &detail) override {
        if (!header_committed) {
            detail = "header not committed";
            return false;
        }
        const auto checkpoint =
            nlohmann::json::parse(checkpoint_json.begin(), checkpoint_json.end());
        const auto validation =
            nlohmann::json::parse(validation_json.begin(), validation_json.end());
        if (validation.value("accepted", false) != true ||
            validation.value("checkpoint_id", std::string{}) !=
                checkpoint.at("payload").at("checkpoint_id").get<std::string>()) {
            detail = "validation evidence is not accepted";
            return false;
        }
        ack = {true, runtime::authority_contracts::sha256_hex(checkpoint_json),
               runtime::authority_contracts::sha256_hex(validation_json), "1"};
        checkpoint_committed = true;
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
    bool fail_finalize_once_after_persist = false;
    bool checkpoint_committed = false;
    bool forge_payload_ack = false;
    std::uint64_t appended_sequences = 0;
    std::string last_record_digest;
    nlohmann::json final_receipt;
};

std::string receipt_json(std::string_view run_id, std::uint64_t sequence,
                         std::string_view record_sha256, std::string_view terminal_state) {
    const nlohmann::json payload = {
        {"journal_last_record_sha256", record_sha256},
        {"journal_last_sequence", sequence},
        {"run_id", run_id},
        {"terminal_state", terminal_state},
    };
    const auto canonical_payload =
        runtime::authority_contracts::canonical_authority_json(payload.dump()).value();
    const auto digest = runtime::authority_contracts::authority_digest_sha256_hex(
        "runtime.run-receipt", "application/vnd.echelon-forge.run-receipt.v1+json",
        canonical_payload);
    return nlohmann::json({
                              {"canonicalization", "echelon_forge.canonical_json.v2"},
                              {"domain", "runtime.run-receipt"},
                              {"envelope_version", "echelon_forge.authority_envelope.v1"},
                              {"media_type", "application/vnd.echelon-forge.run-receipt.v1+json"},
                              {"payload", payload},
                              {"payload_sha256", digest},
                              {"signatures", nlohmann::json::array()},
                          })
        .dump();
}

std::string vector_receipt_json(std::string_view record_sha256 = {}) {
    std::ifstream input(EF_RUN_RECEIPT_VECTOR_PATH, std::ios::binary);
    if (!input) throw std::runtime_error("failed to open canonical RunReceipt vector");
    std::ostringstream buffer;
    buffer << input.rdbuf();
    const auto vector = nlohmann::json::parse(buffer.str());
    auto receipt = nlohmann::json::parse(vector.at("canonical_envelope_json").get<std::string>());
    std::ifstream plan_input(EF_RESOLVED_EXECUTION_PLAN_PATH, std::ios::binary);
    std::ostringstream plan_buffer;
    plan_buffer << plan_input.rdbuf();
    const auto plan_bytes = plan_buffer.str();
    const auto request_sha256 = nlohmann::json::parse(plan_bytes)
                                    .at("input_bindings")
                                    .at("request_sha256")
                                    .get<std::string>();
    const auto plan_blob_sha256 = runtime::authority_contracts::sha256_hex(plan_bytes);
    receipt.at("payload").at("plan_binding")["plan_location"] = "ledger://blob-" + plan_blob_sha256;
    receipt.at("payload").at("plan_binding")["request_location"] =
        "ledger://blob-" + request_sha256;
    receipt.at("payload").at("inputs")["artifacts"] = {
        {"request", request_sha256}, {"resolved_execution_plan", plan_blob_sha256}};
    if (!record_sha256.empty()) {
        receipt.at("payload").at("journal_last_record_sha256") = record_sha256;
    }
    const auto canonical_payload =
        runtime::authority_contracts::canonical_authority_json(receipt.at("payload").dump())
            .value();
    receipt.at("payload_sha256") = runtime::authority_contracts::authority_digest_sha256_hex(
        "runtime.run-receipt", "application/vnd.echelon-forge.run-receipt.v1+json",
        canonical_payload);
    return receipt.dump();
}

std::string vector_receipt_with_run_id(std::string_view run_id) {
    auto receipt = nlohmann::json::parse(vector_receipt_json());
    receipt.at("payload").at("run_id") = run_id;
    const auto canonical_payload =
        runtime::authority_contracts::canonical_authority_json(receipt.at("payload").dump())
            .value();
    receipt.at("payload_sha256") = runtime::authority_contracts::authority_digest_sha256_hex(
        "runtime.run-receipt", "application/vnd.echelon-forge.run-receipt.v1+json",
        canonical_payload);
    return receipt.dump();
}

std::string authority_envelope_from_vector(const char *path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) throw std::runtime_error("failed to open authority envelope vector");
    std::ostringstream buffer;
    buffer << input.rdbuf();
    return nlohmann::json::parse(buffer.str()).at("envelope_json").get<std::string>();
}

std::string vector_run_header(std::string_view run_id) {
    const auto receipt = nlohmann::json::parse(vector_receipt_json());
    auto payload = receipt.at("payload");
    std::ifstream plan_input(EF_RESOLVED_EXECUTION_PLAN_PATH, std::ios::binary);
    std::ostringstream plan_buffer;
    plan_buffer << plan_input.rdbuf();
    const auto plan_bytes = plan_buffer.str();
    const auto request_sha256 = nlohmann::json::parse(plan_bytes)
                                    .at("input_bindings")
                                    .at("request_sha256")
                                    .get<std::string>();
    const auto plan_blob_sha256 = runtime::authority_contracts::sha256_hex(plan_bytes);
    payload.at("plan_binding")["plan_location"] = "ledger://blob-" + plan_blob_sha256;
    payload.at("plan_binding")["request_location"] = "ledger://blob-" + request_sha256;
    payload.at("inputs")["artifacts"] = {{"request", request_sha256},
                                         {"resolved_execution_plan", plan_blob_sha256}};
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
         authority_envelope_from_vector(EF_ROLLOUT_AUTHORITY_VECTOR_PATH)},
    };
    const nlohmann::json measurement_material = {
        {"executable", bindings.at("executable")},
        {"inputs", bindings.at("inputs")},
        {"package", bindings.at("package")},
        {"platform", bindings.at("platform")},
    };
    auto admission_material = bindings;
    admission_material.erase("release_manifest_envelope_json");
    admission_material.erase("rollout_decision_envelope_json");
    const auto canonical_measurement =
        runtime::authority_contracts::canonical_authority_json(measurement_material.dump()).value();
    const auto canonical_bindings =
        runtime::authority_contracts::canonical_authority_json(admission_material.dump()).value();
    return runtime::authority_contracts::canonical_authority_json(
               nlohmann::json{{"admission_binding_sha256",
                               runtime::authority_contracts::sha256_hex(canonical_bindings)},
                              {"observed_measurement_sha256",
                               runtime::authority_contracts::sha256_hex(canonical_measurement)},
                              {"receipt_bindings", bindings},
                              {"run_id", run_id}}
                   .dump())
        .value();
}

std::string checkpoint_json_for_run(std::string_view run_id) {
    const auto receipt = nlohmann::json::parse(vector_receipt_json()).at("payload");
    const nlohmann::json payload = {
        {"aggregate_state_sha256",
         runtime::authority_contracts::sha256_hex("native-checkpoint-state")},
        {"authority_kind", "state_checkpoint"},
        {"checkpoint_id", "checkpoint-1"},
        {"contract_version", "echelon_forge.state_checkpoint_contract.v1"},
        {"decision_id", receipt.at("release_binding").at("rollout_decision_id")},
        {"host_boot_id", receipt.at("host_boot_id")},
        {"incarnation_epoch", "1"},
        {"plan_sha256", receipt.at("plan_binding").at("plan_sha256")},
        {"release_id", receipt.at("release_binding").at("release_id")},
        {"run_id", run_id},
        {"schema_version", "echelon_forge.state_checkpoint.v1"},
        {"state_schema_generation", "1"},
        {"target_reader_generation_max", receipt.at("reader_generation_max")},
        {"target_reader_generation_min", receipt.at("reader_generation_min")},
        {"transfer_fence_sequence", "1"},
        {"world_fragments",
         nlohmann::json::array({nlohmann::json{{"episode_ids", {"episode-1"}},
                                               {"fragment_sequence", "0"},
                                               {"state_sha256", std::string(64, '3')},
                                               {"world_id", "world-1"}}})},
        {"writer_generation", "1"},
        {"writer_role", "runtime_host"},
    };
    const auto canonical_payload =
        runtime::authority_contracts::canonical_authority_json(payload.dump()).value();
    const nlohmann::json checkpoint = {
        {"canonicalization", "echelon_forge.canonical_json.v2"},
        {"domain", "runtime.state-checkpoint"},
        {"envelope_version", "echelon_forge.authority_envelope.v1"},
        {"media_type", "application/vnd.echelon-forge.state-checkpoint.v1+json"},
        {"payload", payload},
        {"payload_sha256",
         runtime::authority_contracts::authority_digest_sha256_hex(
             "runtime.state-checkpoint", "application/vnd.echelon-forge.state-checkpoint.v1+json",
             canonical_payload)},
        {"signatures", nlohmann::json::array()},
    };
    return runtime::authority_contracts::canonical_authority_json(checkpoint.dump()).value();
}

std::string hex_bytes(std::string_view bytes) {
    static constexpr char digits[] = "0123456789abcdef";
    std::string result;
    result.reserve(bytes.size() * 2U);
    for (const unsigned char byte : bytes) {
        result.push_back(digits[byte >> 4U]);
        result.push_back(digits[byte & 0x0fU]);
    }
    return result;
}

std::string checkpoint_validation_for_native(std::string_view checkpoint_json) {
    const auto checkpoint = nlohmann::json::parse(checkpoint_json);
    const auto &payload = checkpoint.at("payload");
    const std::string state_payload("native-checkpoint-state");
    const nlohmann::json validation = {
        {"accepted", true},
        {"aggregate_replay_sha256",
         runtime::authority_contracts::checkpoint_replay_aggregate_sha256(payload.dump()).value()},
        {"checkpoint_id", payload.at("checkpoint_id")},
        {"state_payload_hex", hex_bytes(state_payload)},
        {"state_sha256", runtime::authority_contracts::sha256_hex(state_payload)},
        {"validator_id", "native-test-validator"},
    };
    return runtime::authority_contracts::canonical_authority_json(validation.dump()).value();
}

std::string reseal_receipt(nlohmann::json receipt) {
    const auto canonical_payload =
        runtime::authority_contracts::canonical_authority_json(receipt.at("payload").dump())
            .value();
    receipt["payload_sha256"] = runtime::authority_contracts::authority_digest_sha256_hex(
        "runtime.run-receipt", "application/vnd.echelon-forge.run-receipt.v1+json",
        canonical_payload);
    return runtime::authority_contracts::canonical_authority_json(receipt.dump()).value();
}

std::string reseal_checkpoint(nlohmann::json checkpoint) {
    const auto canonical_payload =
        runtime::authority_contracts::canonical_authority_json(checkpoint.at("payload").dump())
            .value();
    checkpoint["payload_sha256"] = runtime::authority_contracts::authority_digest_sha256_hex(
        "runtime.state-checkpoint", "application/vnd.echelon-forge.state-checkpoint.v1+json",
        canonical_payload);
    return runtime::authority_contracts::canonical_authority_json(checkpoint.dump()).value();
}

} // namespace

TEST_SUITE("runtime_run_recorder") {

    TEST_CASE("header durable acknowledgement precedes append and finalize") {
        FakeStore store;
        runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-1");
        CHECK(recorder.admit(R"({"plan_sha256":"abc","run_id":"run-1"})"));
        CHECK(store.header_committed);
        CHECK(recorder.append(0, "step-0"));
        CHECK_FALSE(recorder.append(0, "duplicate"));
        CHECK(recorder.finalize(
            vector_receipt_json(runtime::authority_contracts::sha256_hex("step-0"))));
        CHECK(store.finalized);
        CHECK(recorder.state() == runtime::host::RuntimeRunRecorderState::Finalized);
    }

    TEST_CASE(
        "observed finalization replaces caller journal facts and binds committed checkpoints") {
        FakeStore store;
        runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-1");
        REQUIRE(recorder.admit(R"({"run_id":"run-1"})"));
        REQUIRE(recorder.append(0, "observed-step"));

        auto checkpoint = nlohmann::json::parse(checkpoint_json_for_run("run-1"));
        const auto checkpoint_state_sha256 =
            checkpoint.at("payload").at("aggregate_state_sha256").get<std::string>();
        const auto checkpoint_validation = nlohmann::json{
            {"accepted", true},
            {"checkpoint_id", "checkpoint-1"},
            {"state_sha256", checkpoint_state_sha256},
        };
        REQUIRE(recorder.persist_checkpoint(checkpoint.dump(), checkpoint_validation.dump()));
        std::string artifact_digest;
        std::string artifact_location;
        REQUIRE(recorder.put_artifact("runtime-state", "observed-result",
                                      "application/vnd.echelon-forge.runtime-state.v1+octets",
                                      "run-retained", artifact_digest, artifact_location));
        REQUIRE(recorder.record_native_result(
            runtime::authority_contracts::sha256_hex("observed-result"),
            runtime::authority_contracts::sha256_hex("observed-result")));
        REQUIRE(recorder.finalize_observed(vector_receipt_json(), "completed", "observed"));
        REQUIRE(store.finalized);
        const auto &payload = store.final_receipt.at("payload");
        CHECK(payload.at("journal_last_sequence") == 1);
        CHECK(payload.at("journal_last_record_sha256") == store.last_record_digest);
        CHECK(payload.at("terminal_reason") == "observed");
        REQUIRE(payload.at("checkpoints").at("created_refs").size() == 1);
        CHECK(payload.at("checkpoints").at("created_refs").front().at("checkpoint_id") ==
              "checkpoint-run-1-1");
    }

    TEST_CASE("failed header admission fail-stops without mutation") {
        FakeStore store;
        store.available = false;
        runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-1");
        CHECK_FALSE(recorder.admit(R"({"run_id":"run-1"})"));
        CHECK(recorder.state() == runtime::host::RuntimeRunRecorderState::Rejected);
        CHECK_FALSE(recorder.append(0, "step-0"));
        CHECK_FALSE(store.header_committed);
    }

    TEST_CASE("receipt finalization retries exact durable bytes without a second terminal frame") {
        FakeStore store;
        store.fail_finalize_once_after_persist = true;
        runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-1");
        REQUIRE(recorder.admit(R"({"run_id":"run-1"})"));
        const auto first =
            recorder.finalize_observed(vector_receipt_json(), "failed", "simulated audit retry");
        CHECK_FALSE(first);
        const auto second =
            recorder.finalize_observed(vector_receipt_json(), "failed", "simulated audit retry");
        INFO(second.code);
        INFO(second.detail);
        REQUIRE(second);
        CHECK(store.appended_sequences == 1);
        CHECK(recorder.state() == runtime::host::RuntimeRunRecorderState::Finalized);
    }

    TEST_CASE("a new recorder acknowledges an immutable receipt from the prior writer") {
        const auto root = std::filesystem::temp_directory_path() /
                          "echelon-forge-p5b-native-ledger-receipt-retry";
        std::error_code cleanup_error;
        std::filesystem::remove_all(root, cleanup_error);
        REQUIRE(seed_authority_blobs(root));
        std::string original_receipt;
        std::uint64_t original_next_sequence = 0U;
        {
            runtime::host::RuntimeFileArtifactLedgerStore store(root,
                                                                runtime_ledger_access("writer-1"));
            runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-1");
            REQUIRE(recorder.admit(vector_run_header("run-1")));
            REQUIRE(recorder.note_lifecycle("construction"));
            REQUIRE(recorder.note_lifecycle("validation"));
            REQUIRE(recorder.bind_runtime_identity("boot-1", "1", "world-1", "1", "episode-1", "1",
                                                   "request-1"));
            REQUIRE(recorder.note_lifecycle("publication"));
            REQUIRE(recorder.note_lifecycle("episode"));
            std::string artifact_digest;
            std::string artifact_location;
            REQUIRE(recorder.put_artifact("runtime-state", "native-output",
                                          "application/vnd.echelon-forge.runtime-state.v1+octets",
                                          "run-retained", artifact_digest, artifact_location));
            REQUIRE(recorder.record_native_result(
                runtime::authority_contracts::sha256_hex("native-output"),
                runtime::authority_contracts::sha256_hex("native-output")));
            REQUIRE(recorder.note_lifecycle("drain"));
            REQUIRE(recorder.note_lifecycle("shutdown"));
            REQUIRE(recorder.note_lifecycle("reclamation"));
            REQUIRE(recorder.finalize_observed(vector_receipt_json(), "completed", "completed"));
            original_next_sequence = recorder.next_sequence();
            std::string detail;
            REQUIRE(store.read_receipt("run-1", original_receipt, detail));
        }
        {
            runtime::host::RuntimeFileArtifactLedgerStore store(
                root,
                {runtime::host::RuntimeArtifactLedgerRole::CrashReconciler, "crash-reconciler"});
            runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-2");
            REQUIRE(recorder.admit(vector_run_header("run-1")));
            CHECK(recorder.fence_generation() == 2U);
            CHECK(recorder.next_sequence() == original_next_sequence);
            const auto retried =
                recorder.finalize_observed(vector_receipt_json(), "crashed", "ignored retry data");
            INFO(retried.detail);
            REQUIRE(retried);
            CHECK(recorder.next_sequence() == original_next_sequence);
            std::string recovered_receipt;
            std::string detail;
            REQUIRE(store.read_receipt("run-1", recovered_receipt, detail));
            CHECK(recovered_receipt == original_receipt);
        }
        std::filesystem::remove_all(root, cleanup_error);
    }

    TEST_CASE("append rejects a durable ACK that does not bind the submitted payload") {
        FakeStore store;
        store.forge_payload_ack = true;
        runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-1");
        REQUIRE(recorder.admit(R"({"run_id":"run-1"})"));
        CHECK_FALSE(recorder.append(0, "step-0"));
        CHECK(recorder.state() == runtime::host::RuntimeRunRecorderState::Rejected);
    }

    TEST_CASE("receipt run identity is checked by native owner") {
        FakeStore store;
        runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-1");
        REQUIRE(recorder.admit(R"({"run_id":"run-1"})"));
        REQUIRE(recorder.append(0, "step-0"));
        CHECK_FALSE(recorder.finalize(vector_receipt_with_run_id("other")));
        CHECK(recorder.state() == runtime::host::RuntimeRunRecorderState::Rejected);
    }

    TEST_CASE("strict receipt finalization requires the recorder owner projection") {
        FakeStore store;
        runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-1");
        REQUIRE(recorder.admit(vector_run_header("run-1")));
        REQUIRE(recorder.note_lifecycle("construction"));
        CHECK_FALSE(recorder.finalize(vector_receipt_json()));
        CHECK_FALSE(store.finalized);
    }

    TEST_CASE("native checkpoint admission is canonical, run-bound, and durable") {
        FakeStore store;
        runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-1");
        REQUIRE(recorder.admit(R"({"run_id":"run-1"})"));
        REQUIRE(recorder.append(0, "pre-checkpoint"));
        const nlohmann::json payload = {
            {"aggregate_state_sha256", std::string(64, '3')},
            {"authority_kind", "state_checkpoint"},
            {"checkpoint_id", "checkpoint-1"},
            {"contract_version", "echelon_forge.state_checkpoint_contract.v1"},
            {"decision_id", "decision-1"},
            {"host_boot_id", "boot-1"},
            {"incarnation_epoch", "1"},
            {"plan_sha256", std::string(64, '2')},
            {"release_id", "release-1"},
            {"run_id", "run-1"},
            {"schema_version", "echelon_forge.state_checkpoint.v1"},
            {"state_schema_generation", "1"},
            {"target_reader_generation_max", "1"},
            {"target_reader_generation_min", "1"},
            {"transfer_fence_sequence", "1"},
            {"world_fragments",
             nlohmann::json::array({nlohmann::json{{"episode_ids", {"episode-1"}},
                                                   {"fragment_sequence", "0"},
                                                   {"state_sha256", std::string(64, '3')},
                                                   {"world_id", "world-1"}}})},
            {"writer_generation", "1"},
            {"writer_role", "runtime_host"},
        };
        const auto canonical_payload =
            runtime::authority_contracts::canonical_authority_json(payload.dump()).value();
        nlohmann::json checkpoint = {
            {"canonicalization", "echelon_forge.canonical_json.v2"},
            {"domain", "runtime.state-checkpoint"},
            {"envelope_version", "echelon_forge.authority_envelope.v1"},
            {"media_type", "application/vnd.echelon-forge.state-checkpoint.v1+json"},
            {"payload", payload},
            {"payload_sha256",
             runtime::authority_contracts::authority_digest_sha256_hex(
                 "runtime.state-checkpoint",
                 "application/vnd.echelon-forge.state-checkpoint.v1+json", canonical_payload)},
            {"signatures", nlohmann::json::array()},
        };
        const auto checkpoint_json =
            runtime::authority_contracts::canonical_authority_json(checkpoint.dump()).value();
        const auto checkpoint_status = recorder.persist_checkpoint(
            checkpoint_json,
            R"({"accepted":true,"checkpoint_id":"checkpoint-1","state_sha256":"3333333333333333333333333333333333333333333333333333333333333333"})");
        INFO(checkpoint_status.code);
        INFO(checkpoint_status.detail);
        CHECK(checkpoint_status);
        CHECK(store.checkpoint_committed);
        CHECK_FALSE(recorder.persist_checkpoint("{}", R"({"accepted":true})"));
    }

    TEST_CASE("native checkpoint admission rejects an unknown state schema") {
        FakeStore store;
        runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-1");
        REQUIRE(recorder.admit(vector_run_header("run-1")));
        auto checkpoint = nlohmann::json::parse(checkpoint_json_for_run("run-1"));
        checkpoint.at("payload")["state_schema_generation"] = "999";
        const auto checkpoint_json = reseal_checkpoint(std::move(checkpoint));
        const auto status = recorder.persist_checkpoint(
            checkpoint_json, checkpoint_validation_for_native(checkpoint_json));
        CHECK_FALSE(status);
        CHECK(recorder.state() == runtime::host::RuntimeRunRecorderState::Rejected);
        CHECK_FALSE(store.checkpoint_committed);
    }

    TEST_CASE("native file ArtifactLedger adapter durably binds the recorder") {
        const auto root =
            std::filesystem::temp_directory_path() / "echelon-forge-p5b-native-ledger";
        std::error_code cleanup_error;
        std::filesystem::remove_all(root, cleanup_error);
        REQUIRE(seed_authority_blobs(root));
        {
            runtime::host::RuntimeFileArtifactLedgerStore store(root, runtime_ledger_access());
            bool duplicate_rejected = false;
            try {
                runtime::host::RuntimeFileArtifactLedgerStore duplicate(root,
                                                                        runtime_ledger_access());
            } catch (...) {
                duplicate_rejected = true;
            }
            CHECK(duplicate_rejected);
            runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-1");
            REQUIRE(recorder.admit(vector_run_header("run-1")));
            REQUIRE(recorder.note_lifecycle("construction"));
            REQUIRE(recorder.note_lifecycle("validation"));
            REQUIRE(recorder.bind_runtime_identity("boot-1", "1", "world-1", "1", "episode-1", "1",
                                                   "request-1"));
            REQUIRE(recorder.note_lifecycle("publication"));
            REQUIRE(recorder.note_lifecycle("episode"));
            REQUIRE(recorder.append(recorder.next_sequence(), "step-0"));
            const auto checkpoint = checkpoint_json_for_run("run-1");
            const auto checkpoint_id =
                "checkpoint-run-1-" + std::to_string(recorder.next_sequence());
            const auto checkpoint_status = recorder.persist_checkpoint(
                checkpoint, checkpoint_validation_for_native(checkpoint));
            INFO(checkpoint_status.code);
            INFO(checkpoint_status.detail);
            REQUIRE(checkpoint_status);
            std::string artifact_digest;
            std::string artifact_location;
            REQUIRE(recorder.put_artifact("runtime-state", "trace-bytes",
                                          "application/octet-stream", "run-retained",
                                          artifact_digest, artifact_location));
            REQUIRE(recorder.record_native_result(
                runtime::authority_contracts::sha256_hex("trace-bytes"),
                runtime::authority_contracts::sha256_hex("trace-bytes")));
            {
                std::string durable_bundle;
                std::string detail;
                REQUIRE(store.read_checkpoint(checkpoint_id, durable_bundle, detail));
                auto orphan = nlohmann::json::parse(durable_bundle);
                orphan.at("checkpoint").at("payload")["checkpoint_id"] = "checkpoint-orphan";
                orphan.at("validation")["checkpoint_id"] = "checkpoint-orphan";
                const auto orphan_checkpoint = reseal_checkpoint(orphan.at("checkpoint"));
                orphan["checkpoint"] = nlohmann::json::parse(orphan_checkpoint);
                orphan.at("validation")["aggregate_replay_sha256"] =
                    runtime::authority_contracts::checkpoint_replay_aggregate_sha256(
                        orphan.at("checkpoint").at("payload").dump())
                        .value();
                const auto orphan_directory =
                    root / "checkpoints" /
                    runtime::authority_contracts::sha256_hex("checkpoint-orphan");
                std::filesystem::create_directories(orphan_directory);
                {
                    std::ofstream output(orphan_directory / "bundle.json",
                                         std::ios::binary | std::ios::trunc);
                    output << runtime::authority_contracts::canonical_authority_json(orphan.dump())
                                  .value();
                }
                std::string rejected;
                CHECK_FALSE(store.read_checkpoint("checkpoint-orphan", rejected, detail));
                std::filesystem::remove_all(orphan_directory, cleanup_error);
            }
            auto receipt = nlohmann::json::parse(vector_receipt_json());
            auto &artifact = receipt.at("payload").at("results").at("output_artifacts").at(0);
            artifact["digest"] = artifact_digest;
            artifact["size"] = 11;
            artifact["retrieval_location"] = artifact_location;
            REQUIRE(recorder.note_lifecycle("drain"));
            REQUIRE(recorder.note_lifecycle("shutdown"));
            REQUIRE(recorder.note_lifecycle("reclamation"));
            const auto canonical_payload =
                runtime::authority_contracts::canonical_authority_json(receipt.at("payload").dump())
                    .value();
            receipt["payload_sha256"] = runtime::authority_contracts::authority_digest_sha256_hex(
                "runtime.run-receipt", "application/vnd.echelon-forge.run-receipt.v1+json",
                canonical_payload);
            REQUIRE(recorder.finalize_observed(receipt.dump(), "completed", "completed"));
            CHECK(std::filesystem::is_regular_file(
                root / "journals" / runtime::authority_contracts::sha256_hex("journal:run-1") /
                "receipt.json"));
            const auto backup =
                std::filesystem::temp_directory_path() / "echelon-forge-p5b-native-backup";
            const auto restored_root =
                std::filesystem::temp_directory_path() / "echelon-forge-p5b-native-restored";
            std::filesystem::remove_all(backup, cleanup_error);
            std::filesystem::remove_all(restored_root, cleanup_error);
            std::string detail;
            REQUIRE(store.backup_to(backup, detail));
            REQUIRE(runtime::host::RuntimeFileArtifactLedgerStore::restore_from(
                backup, restored_root, backup_ledger_access(), detail));
            {
                runtime::host::RuntimeFileArtifactLedgerStore restored(
                    restored_root,
                    {runtime::host::RuntimeArtifactLedgerRole::ReadOnlyAuditor, "restore-reader"});
                std::string restored_receipt;
                REQUIRE(restored.read_receipt("run-1", restored_receipt, detail));
                CHECK(nlohmann::json::parse(restored_receipt).at("payload").at("terminal_state") ==
                      "completed");
                std::string restored_checkpoint;
                REQUIRE(restored.read_checkpoint(checkpoint_id, restored_checkpoint, detail));
            }
            std::filesystem::remove_all(restored_root, cleanup_error);
            const auto backup_bundle_path =
                backup / "checkpoints" / runtime::authority_contracts::sha256_hex(checkpoint_id) /
                "bundle.json";
            std::ifstream backup_bundle_input(backup_bundle_path, std::ios::binary);
            REQUIRE(backup_bundle_input);
            auto tampered_bundle = nlohmann::json::parse(backup_bundle_input);
            auto &tampered_checkpoint = tampered_bundle.at("checkpoint");
            tampered_checkpoint.at("payload")["plan_sha256"] = std::string(64, 'f');
            const auto tampered_checkpoint_payload =
                runtime::authority_contracts::canonical_authority_json(
                    tampered_checkpoint.at("payload").dump())
                    .value();
            tampered_checkpoint["payload_sha256"] =
                runtime::authority_contracts::authority_digest_sha256_hex(
                    "runtime.state-checkpoint",
                    "application/vnd.echelon-forge.state-checkpoint.v1+json",
                    tampered_checkpoint_payload);
            tampered_bundle.at("validation")["aggregate_replay_sha256"] =
                runtime::authority_contracts::checkpoint_replay_aggregate_sha256(
                    tampered_checkpoint.at("payload").dump())
                    .value();
            {
                std::ofstream output(backup_bundle_path, std::ios::binary | std::ios::trunc);
                REQUIRE(output);
                output << runtime::authority_contracts::canonical_authority_json(
                              tampered_bundle.dump())
                              .value();
            }
            CHECK_FALSE(runtime::host::RuntimeFileArtifactLedgerStore::restore_from(
                backup, restored_root, backup_ledger_access(), detail));
            CHECK_FALSE(std::filesystem::exists(restored_root));
            std::filesystem::remove_all(backup, cleanup_error);
            std::string availability;
            REQUIRE(store.availability_report(availability, detail));
            const auto report = nlohmann::json::parse(availability);
            CHECK(report.at("available") == true);
            CHECK(report.at("hash_correct") == true);
            CHECK(report.at("private_root") == true);
            CHECK(report.at("journal_count") == 1);
            CHECK(report.at("receipt_count") == 1);
            CHECK(report.at("checkpoint_count") == 1);
            CHECK(report.at("blob_count") == 3);
            CHECK(report.at("audit_event_count").get<std::size_t>() >= 10);
            {
                std::ifstream plan_input(EF_RESOLVED_EXECUTION_PLAN_PATH, std::ios::binary);
                std::ostringstream plan_bytes;
                plan_bytes << plan_input.rdbuf();
                const auto plan_digest = runtime::authority_contracts::sha256_hex(plan_bytes.str());
                const auto data = root / "blobs" / (plan_digest + ".data");
                const auto held = root / "blobs" / (plan_digest + ".data.held");
                std::filesystem::rename(data, held);
                std::string missing_authority_receipt;
                CHECK_FALSE(store.read_receipt("run-1", missing_authority_receipt, detail));
                std::filesystem::rename(held, data);
                REQUIRE(store.read_receipt("run-1", missing_authority_receipt, detail));
            }
            bool audit_identity_persisted = false;
            for (const auto &entry : std::filesystem::directory_iterator(root / "audit")) {
                std::ifstream input(entry.path(), std::ios::binary);
                const auto event = nlohmann::json::parse(input);
                audit_identity_persisted =
                    audit_identity_persisted || event.at("audit_identity") == "runtime-test";
            }
            CHECK(audit_identity_persisted);
            {
                std::ofstream output(root / "blobs" / (artifact_digest + ".data"),
                                     std::ios::binary | std::ios::app);
                REQUIRE(output);
                output << "tamper";
            }
            CHECK_FALSE(store.availability_report(availability, detail));
        }
        std::filesystem::remove_all(root, cleanup_error);
    }

    TEST_CASE("native ArtifactLedger roles fail closed") {
        const auto root =
            std::filesystem::temp_directory_path() / "echelon-forge-p5b-native-ledger-acl";
        std::error_code cleanup_error;
        std::filesystem::remove_all(root, cleanup_error);
        {
            runtime::host::RuntimeFileArtifactLedgerStore reader(
                root, {runtime::host::RuntimeArtifactLedgerRole::ReadOnlyAuditor, "auditor"});
            std::uint64_t generation = 0;
            std::string detail;
            CHECK_FALSE(reader.acquire_fence("journal:unauthorized", "writer", generation, detail));
            std::string digest;
            std::string location;
            CHECK_FALSE(reader.put_artifact("bytes", "application/octet-stream", "run-retained",
                                            digest, location, detail));
            CHECK_FALSE(reader.backup_to(root / "auditor-backup", detail));
        }
        std::filesystem::remove_all(root, cleanup_error);
        {
            runtime::host::RuntimeFileArtifactLedgerStore plan_compiler(
                root, {runtime::host::RuntimeArtifactLedgerRole::PlanCompiler, "plan-compiler"});
            std::string digest;
            std::string location;
            std::string detail;
            REQUIRE(plan_compiler.put_artifact(
                "closed-plan", "application/vnd.echelon-forge.resolved-execution-plan.v1+json",
                "active-release", digest, location, detail));
            CHECK(location == "ledger://blob-" + digest);
            CHECK_FALSE(plan_compiler.put_artifact("runtime-output", "application/octet-stream",
                                                   "run-retained", digest, location, detail));
            std::string receipt;
            CHECK_FALSE(plan_compiler.read_receipt("run-1", receipt, detail));
        }
        std::filesystem::remove_all(root, cleanup_error);
        {
            runtime::host::RuntimeFileArtifactLedgerStore release_pipeline(
                root, {runtime::host::RuntimeArtifactLedgerRole::ReleaseArtifactPipeline,
                       "release-pipeline"});
            std::string digest;
            std::string location;
            std::string detail;
            REQUIRE(release_pipeline.put_artifact(
                "release-envelope", "application/vnd.echelon-forge.release-manifest.v1+json",
                "active-release", digest, location, detail));
            REQUIRE(release_pipeline.put_artifact(
                "release-package", "application/vnd.echelon-forge.release-package.v1+octets",
                "rollback-window", digest, location, detail));
            CHECK_FALSE(release_pipeline.put_artifact(
                "closed-plan", "application/vnd.echelon-forge.resolved-execution-plan.v1+json",
                "active-release", digest, location, detail));
        }
        std::filesystem::remove_all(root, cleanup_error);
        {
            runtime::host::RuntimeFileArtifactLedgerStore reconciler(
                root, {runtime::host::RuntimeArtifactLedgerRole::CrashReconciler, "reconciler"});
            std::uint64_t generation = 0;
            std::string detail;
            CHECK_FALSE(reconciler.acquire_fence("journal:new", "writer", generation, detail));
            CHECK_FALSE(
                reconciler.commit_header("new", 1, "writer", vector_run_header("new"), detail));
        }
        std::filesystem::remove_all(root, cleanup_error);
    }

    TEST_CASE(
        "native ArtifactLedger ignores complete and truncated audit temp files after restart") {
        const auto root =
            std::filesystem::temp_directory_path() / "echelon-forge-p5b-native-audit-restart";
        std::error_code cleanup_error;
        std::filesystem::remove_all(root, cleanup_error);
        std::filesystem::path committed_event;
        {
            runtime::host::RuntimeFileArtifactLedgerStore store(root, runtime_ledger_access());
            std::string digest;
            std::string location;
            std::string detail;
            REQUIRE(store.put_artifact("audit-seed", "application/octet-stream", "run-retained",
                                       digest, location, detail));
            for (const auto &entry : std::filesystem::directory_iterator(root / "audit")) {
                committed_event = entry.path();
                break;
            }
            REQUIRE(std::filesystem::is_regular_file(committed_event));
        }
        const auto complete_temp =
            root / "audit" / (committed_event.filename().string() + ".tmp-0123456789abcdef");
        const auto truncated_temp =
            root / "audit" / (committed_event.filename().string() + ".tmp-fedcba9876543210");
        std::filesystem::copy_file(committed_event, complete_temp);
        {
            std::ofstream output(truncated_temp, std::ios::binary | std::ios::trunc);
            REQUIRE(output);
            output << "{\"truncated\":";
        }
        {
            runtime::host::RuntimeFileArtifactLedgerStore restarted(root, runtime_ledger_access());
            CHECK_FALSE(std::filesystem::exists(complete_temp));
            CHECK_FALSE(std::filesystem::exists(truncated_temp));
            std::string report;
            std::string detail;
            REQUIRE(restarted.availability_report(report, detail));
            CHECK(nlohmann::json::parse(report).at("available") == true);
            std::string digest;
            std::string location;
            REQUIRE(restarted.put_artifact("audit-after-restart", "application/octet-stream",
                                           "run-retained", digest, location, detail));
            REQUIRE(restarted.availability_report(report, detail));
        }
        std::filesystem::remove_all(root, cleanup_error);
    }

    TEST_CASE("native file ArtifactLedger rejects a torn frame before receipt commit") {
        const auto root =
            std::filesystem::temp_directory_path() / "echelon-forge-p5b-native-ledger-torn";
        std::error_code cleanup_error;
        std::filesystem::remove_all(root, cleanup_error);
        REQUIRE(seed_authority_blobs(root));
        {
            runtime::host::RuntimeFileArtifactLedgerStore store(root, runtime_ledger_access());
            runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-1");
            REQUIRE(recorder.admit(vector_run_header("run-1")));
            REQUIRE(recorder.append(recorder.next_sequence(), "step-0"));
            const auto frame = root / "journals" /
                               runtime::authority_contracts::sha256_hex("journal:run-1") /
                               "frame-1.json";
            {
                std::ofstream output(frame, std::ios::binary | std::ios::trunc);
                REQUIRE(output.good());
                output << "{}";
            }
            CHECK_FALSE(
                recorder.finalize_observed(vector_receipt_json(), "completed", "completed"));
            CHECK_FALSE(std::filesystem::exists(
                root / "journals" / runtime::authority_contracts::sha256_hex("journal:run-1") /
                "receipt.json"));
        }
        std::filesystem::remove_all(root, cleanup_error);
    }

    TEST_CASE("native file ArtifactLedger enforces the recorder contract on direct calls") {
        const auto root = std::filesystem::temp_directory_path() /
                          "echelon-forge-p5b-native-ledger-direct-contract";
        std::error_code cleanup_error;
        std::filesystem::remove_all(root, cleanup_error);
        REQUIRE(seed_authority_blobs(root));
        {
            runtime::host::RuntimeFileArtifactLedgerStore store(root, runtime_ledger_access());
            std::string detail;
            CHECK_FALSE(store.backup_to(root / "nested-backup", detail));

            std::uint64_t generation = 0;
            REQUIRE(store.acquire_fence("journal:run-1", "writer-1", generation, detail));
            REQUIRE(generation == 1);
            CHECK_FALSE(store.commit_header("run-1", generation, "writer-1",
                                            vector_run_header("run-1"), detail));
            runtime::host::RuntimeRunRecorderAppendAck append_ack;
            CHECK_FALSE(store.append_record("run-1", generation, "writer-1", 0, "step-0",
                                            append_ack, detail));
            runtime::host::RuntimeRunRecorderCheckpointAck checkpoint_ack;
            const auto checkpoint = checkpoint_json_for_run("run-1");
            CHECK_FALSE(store.commit_checkpoint("run-1", generation, "writer-1", checkpoint,
                                                checkpoint_validation_for_native(checkpoint),
                                                checkpoint_ack, detail));
            runtime::host::RuntimeRunRecorderFinalizeAck finalize_ack;
            CHECK_FALSE(store.finalize_receipt("run-1", generation, "writer-1",
                                               vector_receipt_json(), finalize_ack, detail));
        }
        std::filesystem::remove_all(root, cleanup_error);
    }

    TEST_CASE("native file ArtifactLedger rejects a cross-stream fence swap") {
        const auto root = std::filesystem::temp_directory_path() /
                          "echelon-forge-p5b-native-ledger-cross-stream-fence";
        std::error_code cleanup_error;
        std::filesystem::remove_all(root, cleanup_error);
        REQUIRE(seed_authority_blobs(root));
        {
            runtime::host::RuntimeFileArtifactLedgerStore store(root, runtime_ledger_access());
            runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-1");
            REQUIRE(recorder.admit(vector_run_header("run-1")));

            std::string detail;
            std::uint64_t other_generation = 0;
            REQUIRE(store.acquire_fence("journal:run-2", "writer-2", other_generation, detail));
            REQUIRE(other_generation == 1U);
            const auto run_one_fence =
                root / "fences" /
                (runtime::authority_contracts::sha256_hex("journal:run-1") + ".json");
            const auto run_two_fence =
                root / "fences" /
                (runtime::authority_contracts::sha256_hex("journal:run-2") + ".json");
            std::filesystem::copy_file(run_two_fence, run_one_fence,
                                       std::filesystem::copy_options::overwrite_existing);

            const auto append = recorder.append(recorder.next_sequence(), "step-after-swap");
            CHECK_FALSE(append);
            CHECK(append.detail.find("stale or absent") != std::string::npos);
        }
        std::filesystem::remove_all(root, cleanup_error);
    }

    TEST_CASE("native recorder replaces caller checkpoint references with durable ownership") {
        const auto root = std::filesystem::temp_directory_path() /
                          "echelon-forge-p5b-native-ledger-checkpoint-refs";
        std::error_code cleanup_error;
        std::filesystem::remove_all(root, cleanup_error);
        REQUIRE(seed_authority_blobs(root));
        {
            runtime::host::RuntimeFileArtifactLedgerStore store(root, runtime_ledger_access());
            const auto header_json = vector_run_header("run-1");
            runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-1");
            REQUIRE(recorder.admit(header_json));
            REQUIRE(recorder.note_lifecycle("construction"));
            REQUIRE(recorder.note_lifecycle("validation"));
            REQUIRE(recorder.bind_runtime_identity("boot-1", "1", "world-1", "1", "episode-1", "1",
                                                   "request-1"));
            REQUIRE(recorder.note_lifecycle("publication"));
            REQUIRE(recorder.note_lifecycle("episode"));
            const auto checkpoint = checkpoint_json_for_run("run-1");
            REQUIRE(recorder.persist_checkpoint(checkpoint,
                                                checkpoint_validation_for_native(checkpoint)));
            std::string artifact_digest;
            std::string artifact_location;
            REQUIRE(recorder.put_artifact("runtime-state", "native-output",
                                          "application/octet-stream", "run-retained",
                                          artifact_digest, artifact_location));
            REQUIRE(recorder.record_native_result(
                runtime::authority_contracts::sha256_hex("native-output"),
                runtime::authority_contracts::sha256_hex("native-output")));
            auto base = nlohmann::json::parse(vector_receipt_json());
            const nlohmann::json forged_ref = {
                {"checkpoint_id", "checkpoint-absent"},
                {"checkpoint_sha256", std::string(64, 'a')},
                {"validation_sha256", std::string(64, 'b')},
                {"state_schema_generation", "1"},
                {"retrieval_location", "ledger://checkpoint-checkpoint-absent"},
            };
            base.at("payload").at("checkpoints").at("source_refs") =
                nlohmann::json::array({forged_ref});
            base.at("payload").at("checkpoints").at("created_refs") =
                nlohmann::json::array({forged_ref});
            REQUIRE(recorder.note_lifecycle("drain"));
            REQUIRE(recorder.note_lifecycle("shutdown"));
            REQUIRE(recorder.note_lifecycle("reclamation"));
            REQUIRE(recorder.finalize_observed(base.dump(), "completed", "completed"));
            std::string receipt_json;
            std::string detail;
            REQUIRE(store.read_receipt("run-1", receipt_json, detail));
            const auto stored = nlohmann::json::parse(receipt_json).at("payload").at("checkpoints");
            CHECK(stored.at("source_refs").empty());
            REQUIRE(stored.at("created_refs").size() == 1);
            CHECK(stored.at("created_refs").front().at("checkpoint_id") != "checkpoint-absent");
        }
        std::filesystem::remove_all(root, cleanup_error);
    }

    TEST_CASE("native file ArtifactLedger resumes an admitted journal under a newer fence") {
        const auto root =
            std::filesystem::temp_directory_path() / "echelon-forge-p5b-native-ledger-resume";
        std::error_code cleanup_error;
        std::filesystem::remove_all(root, cleanup_error);
        REQUIRE(seed_authority_blobs(root));
        {
            runtime::host::RuntimeFileArtifactLedgerStore first_store(
                root, runtime_ledger_access("writer-1"));
            runtime::host::RuntimeRunRecorder first(first_store, "run-1", "writer-1");
            REQUIRE(first.admit(vector_run_header("run-1")));
            REQUIRE(first.note_lifecycle("construction"));
            REQUIRE(first.note_lifecycle("validation"));
            REQUIRE(first.bind_runtime_identity("boot-1", "1", "world-1", "1", "episode-1", "1",
                                                "request-1"));
            REQUIRE(first.note_lifecycle("publication"));
            REQUIRE(first.note_lifecycle("episode"));
            REQUIRE(first.append(first.next_sequence(), "step-before-crash"));
            const auto checkpoint = checkpoint_json_for_run("run-1");
            REQUIRE(
                first.persist_checkpoint(checkpoint, checkpoint_validation_for_native(checkpoint)));
        }
        {
            runtime::host::RuntimeFileArtifactLedgerStore recovery_store(
                root,
                {runtime::host::RuntimeArtifactLedgerRole::CrashReconciler, "crash-reconciler"});
            runtime::host::RuntimeRunRecorder recovered(recovery_store, "run-1", "writer-2");
            REQUIRE(recovered.admit(vector_run_header("run-1")));
            CHECK(recovered.fence_generation() == 2);
            const auto recovery_sequence = recovered.next_sequence();
            CHECK(recovery_sequence > 2);
            const auto observed_exit = runtime::authority_contracts::sha256_hex(
                "native-root-lock-released:journal:run-1:1:writer-1:2:writer-2");
            const auto crash_append = recovered.append(
                recovery_sequence, nlohmann::json{{"event", "crash_reconciled"},
                                                  {"observed_exit_sha256", observed_exit},
                                                  {"prior_writer_generation", 1},
                                                  {"prior_writer_id", "writer-1"},
                                                  {"recovery_writer_generation", 2},
                                                  {"recovery_writer_id", "writer-2"}}
                                       .dump());
            INFO(crash_append.detail);
            REQUIRE(crash_append);
            const auto recovered_final =
                recovered.finalize_observed(vector_receipt_json(), "crashed", "prior writer lost");
            INFO(recovered_final.detail);
            REQUIRE(recovered_final);
            std::string receipt;
            std::string detail;
            REQUIRE(recovery_store.read_receipt("run-1", receipt, detail));
            const auto recovered_payload = nlohmann::json::parse(receipt).at("payload");
            CHECK(recovered_payload.at("terminal_state") == "crashed");
            CHECK(recovered_payload.at("host_boot_id") == "boot-1");
            CHECK(recovered_payload.at("incarnation_epoch") == "1");
            REQUIRE(recovered_payload.at("checkpoints").at("created_refs").size() == 1);
            CHECK(recovered_payload.at("checkpoints")
                      .at("created_refs")
                      .front()
                      .at("checkpoint_id") != "");
        }
        std::filesystem::remove_all(root, cleanup_error);
    }

    TEST_CASE("crash recovery after a durable terminal frame advances the lifecycle tail") {
        const auto root = std::filesystem::temp_directory_path() /
                          "echelon-forge-p5b-native-ledger-terminal-crash";
        std::error_code cleanup_error;
        std::filesystem::remove_all(root, cleanup_error);
        REQUIRE(seed_authority_blobs(root));
        {
            runtime::host::RuntimeFileArtifactLedgerStore store(root,
                                                                runtime_ledger_access("writer-1"));
            runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-1");
            REQUIRE(recorder.admit(vector_run_header("run-1")));
            REQUIRE(recorder.note_lifecycle("construction"));
            REQUIRE(recorder.note_lifecycle("validation"));
            REQUIRE(recorder.bind_runtime_identity("boot-1", "1", "world-1", "1", "episode-1", "1",
                                                   "request-1"));
            REQUIRE(recorder.note_lifecycle("publication"));
            REQUIRE(recorder.note_lifecycle("episode"));
            REQUIRE(recorder.note_lifecycle("terminal"));
        }
        {
            runtime::host::RuntimeFileArtifactLedgerStore store(
                root,
                {runtime::host::RuntimeArtifactLedgerRole::CrashReconciler, "crash-reconciler"});
            runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-2");
            REQUIRE(recorder.admit(vector_run_header("run-1")));
            const auto marker_sequence = recorder.next_sequence();
            const auto observed_exit = runtime::authority_contracts::sha256_hex(
                "native-root-lock-released:journal:run-1:1:writer-1:2:writer-2");
            REQUIRE(recorder.append(marker_sequence,
                                    nlohmann::json{{"event", "crash_reconciled"},
                                                   {"observed_exit_sha256", observed_exit},
                                                   {"prior_writer_generation", 1},
                                                   {"prior_writer_id", "writer-1"},
                                                   {"recovery_writer_generation", 2},
                                                   {"recovery_writer_id", "writer-2"}}
                                        .dump()));
            const auto recovered =
                recorder.finalize_observed(vector_receipt_json(), "crashed", "prior writer lost");
            INFO(recovered.detail);
            REQUIRE(recovered);
            std::string receipt_json;
            std::string detail;
            REQUIRE(store.read_receipt("run-1", receipt_json, detail));
            const auto recovered_receipt = nlohmann::json::parse(receipt_json);
            const auto &payload = recovered_receipt.at("payload");
            CHECK(payload.at("journal_last_sequence") == marker_sequence + 1U);
            REQUIRE(payload.at("lifecycle").size() >= 2U);
            CHECK(payload.at("lifecycle").back().at("event") == "terminal");
            CHECK(payload.at("lifecycle").back().at("durable_sequence") == marker_sequence + 1U);
        }
        std::filesystem::remove_all(root, cleanup_error);
    }

    TEST_CASE("native owner rejects a resealed incomplete receipt payload") {
        FakeStore store;
        runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-1");
        REQUIRE(recorder.admit(R"({"run_id":"run-1"})"));
        REQUIRE(recorder.append(0, "step-0"));
        CHECK_FALSE(recorder.finalize(receipt_json("run-1", 0, std::string(64, 'a'), "failed")));
        CHECK(recorder.state() == runtime::host::RuntimeRunRecorderState::Rejected);
    }

    TEST_CASE("native owner rejects malformed envelope signatures") {
        FakeStore store;
        runtime::host::RuntimeRunRecorder recorder(store, "run-1", "writer-1");
        REQUIRE(recorder.admit(R"({"run_id":"run-1"})"));
        REQUIRE(recorder.append(0, "step-0"));
        auto receipt = nlohmann::json::parse(
            vector_receipt_json(runtime::authority_contracts::sha256_hex("step-0")));
        receipt.at("signatures") = nlohmann::json::array({nlohmann::json::object()});
        CHECK_FALSE(recorder.finalize(receipt.dump()));
    }

} // TEST_SUITE
