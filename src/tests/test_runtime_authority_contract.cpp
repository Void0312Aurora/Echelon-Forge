#include <doctest/doctest.h>

#include <fstream>
#include <nlohmann/json.hpp>

#include "runtime/contracts/authority/runtime_authority_contract.h"

namespace {

nlohmann::json authority_vector() {
    std::ifstream input(
        std::string(EF_SOURCE_ROOT) +
        "/tests/architecture/composition/fixtures/authority_cross_language_vector.v1.json");
    REQUIRE(input.good());
    return nlohmann::json::parse(input);
}

nlohmann::json authority_fixture(const char *name) {
    std::ifstream input(std::string(EF_SOURCE_ROOT) + "/tests/architecture/composition/fixtures/" +
                        name);
    REQUIRE(input.good());
    return nlohmann::json::parse(input);
}

} // namespace

TEST_SUITE("runtime_authority_contract") {

    TEST_CASE("native executes the checked-in cross-language vector") {
        const auto vector = authority_vector();
        const auto result = runtime::authority_contracts::validate_authority_envelope_json(
            vector.at("envelope_json").get<std::string>(),
            vector.at("canonical_payload_bytes").get<std::string>());
        CHECK(result.valid);
        CHECK(vector.at("payload_sha256") ==
              runtime::authority_contracts::authority_digest_sha256_hex(
                  vector.at("domain").get<std::string>(),
                  vector.at("media_type").get<std::string>(),
                  vector.at("canonical_payload_bytes").get<std::string>()));
    }

    TEST_CASE("native rejects detached digest mutation") {
        const auto vector = authority_vector();
        auto envelope = nlohmann::json::parse(vector.at("envelope_json").get<std::string>());
        envelope.at("payload_sha256") = std::string(64, '0');
        const auto result = runtime::authority_contracts::validate_authority_envelope_json(
            envelope.dump(), vector.at("canonical_payload_bytes").get<std::string>());
        CHECK_FALSE(result.valid);
        CHECK(result.code == "authority.digest");
    }

    TEST_CASE("native rejects unknown payload fields before admission") {
        const auto vector = authority_vector();
        auto envelope = nlohmann::json::parse(vector.at("envelope_json").get<std::string>());
        envelope.at("payload")["hidden_default"] = true;
        const auto payload_bytes = envelope.at("payload").dump();
        envelope.at("payload_sha256") = runtime::authority_contracts::authority_digest_sha256_hex(
            envelope.at("domain").get<std::string>(), envelope.at("media_type").get<std::string>(),
            payload_bytes);
        const auto result = runtime::authority_contracts::validate_authority_envelope_json(
            envelope.dump(), payload_bytes);
        CHECK_FALSE(result.valid);
        CHECK(result.code == "authority.payload_fields");
    }

    TEST_CASE("native executes plan, rollout, and checkpoint authority fixtures") {
        for (const auto name :
             {"authority_resolved_composition_plan.v1.json",
              "authority_resolved_composition_plan.generation2.v1.json",
              "authority_rollout_decision.v1.json", "authority_state_checkpoint.v1.json"}) {
            const auto vector = authority_fixture(name);
            const auto result = runtime::authority_contracts::validate_authority_envelope_json(
                vector.at("envelope_json").get<std::string>(),
                vector.at("canonical_payload_bytes").get<std::string>());
            CHECK(result.valid);
            CHECK(vector.at("payload_sha256") ==
                  runtime::authority_contracts::authority_digest_sha256_hex(
                      vector.at("domain").get<std::string>(),
                      vector.at("media_type").get<std::string>(),
                      vector.at("canonical_payload_bytes").get<std::string>()));
        }
    }

    TEST_CASE("native fails closed for plan shell and rollout/checkpoint semantic mutations") {
        nlohmann::json plan_payload = {
            {"adapter_role", "legacy_resolved_manifest_reader"},
            {"authority_kind", "resolved_composition_plan"},
            {"contract_version", "echelon_forge.resolved_composition_plan_contract.v1"},
            {"plan_id", "plan-1"},
            {"reader_generation_max", "1"},
            {"reader_generation_min", "1"},
            {"request_sha256", std::string(64, 'a')},
            {"resolved_plan", nullptr},
            {"schema_version", "echelon_forge.resolved_composition_plan.v1"},
            {"source_artifact_schema_version", "echelon_forge.resolved_simulation_composition.v1"},
            {"source_artifact_sha256", std::string(64, 'b')},
            {"source_request_manifest_binding_sha256", std::string(64, 'd')},
            {"source_requested_manifest_sha256", std::string(64, 'c')},
            {"writer_generation", "1"},
            {"writer_role", "plan_compiler"},
        };
        nlohmann::json plan_envelope = {
            {"canonicalization", "echelon_forge.canonical_json.v2"},
            {"domain", "composition.resolved-plan"},
            {"envelope_version", "echelon_forge.authority_envelope.v1"},
            {"media_type", "application/vnd.echelon-forge.resolved-composition-plan.v1+json"},
            {"payload", plan_payload},
            {"signatures", nlohmann::json::array()},
        };
        const auto plan_bytes = plan_payload.dump();
        plan_envelope["payload_sha256"] = runtime::authority_contracts::authority_digest_sha256_hex(
            plan_envelope.at("domain").get<std::string>(),
            plan_envelope.at("media_type").get<std::string>(), plan_bytes);
        const auto plan_result = runtime::authority_contracts::validate_authority_envelope_json(
            plan_envelope.dump(), plan_bytes);
        CHECK_FALSE(plan_result.valid);
        CHECK(plan_result.code == "authority.payload_type");

        auto rollout = authority_fixture("authority_rollout_decision.v1.json");
        auto rollout_envelope =
            nlohmann::json::parse(rollout.at("envelope_json").get<std::string>());
        rollout_envelope["payload"]["writer_role"] = "runtime_host";
        const auto rollout_bytes = rollout_envelope.at("payload").dump();
        rollout_envelope["payload_sha256"] =
            runtime::authority_contracts::authority_digest_sha256_hex(
                rollout_envelope.at("domain").get<std::string>(),
                rollout_envelope.at("media_type").get<std::string>(), rollout_bytes);
        const auto rollout_result = runtime::authority_contracts::validate_authority_envelope_json(
            rollout_envelope.dump(), rollout_bytes);
        CHECK_FALSE(rollout_result.valid);
        CHECK(rollout_result.code == "authority.owner");

        auto checkpoint = authority_fixture("authority_state_checkpoint.v1.json");
        auto checkpoint_envelope =
            nlohmann::json::parse(checkpoint.at("envelope_json").get<std::string>());
        checkpoint_envelope["payload"]["world_fragments"][0]["episode_ids"] =
            nlohmann::json::array({"episode-2", "episode-1"});
        const auto checkpoint_bytes = checkpoint_envelope.at("payload").dump();
        checkpoint_envelope["payload_sha256"] =
            runtime::authority_contracts::authority_digest_sha256_hex(
                checkpoint_envelope.at("domain").get<std::string>(),
                checkpoint_envelope.at("media_type").get<std::string>(), checkpoint_bytes);
        const auto checkpoint_result =
            runtime::authority_contracts::validate_authority_envelope_json(
                checkpoint_envelope.dump(), checkpoint_bytes);
        CHECK_FALSE(checkpoint_result.valid);
        CHECK(checkpoint_result.code == "authority.payload_type");
    }

} // TEST_SUITE
