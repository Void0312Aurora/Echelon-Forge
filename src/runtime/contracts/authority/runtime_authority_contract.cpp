#include "runtime/contracts/authority/runtime_authority_contract.h"

#include <nlohmann/json.hpp>

#include <array>
#include <algorithm>
#include <cstdint>
#include <codecvt>
#include <iomanip>
#include <locale>
#include <sstream>
#include <set>
#include <vector>
#include <utility>

#include "runtime/composition/composition_json.h"
#include "runtime/crypto/sha256.h"

namespace runtime::authority_contracts {
namespace {

using Json = nlohmann::json;

Json sorted_json_value(const Json &value) {
    if (value.is_object()) {
        Json result = Json::object();
        std::vector<std::string> keys;
        keys.reserve(value.size());
        for (const auto &item : value.items())
            keys.push_back(item.key());
        std::sort(keys.begin(), keys.end());
        for (const auto &key : keys)
            result[key] = sorted_json_value(value.at(key));
        return result;
    }
    if (value.is_array()) {
        Json result = Json::array();
        for (const auto &item : value)
            result.push_back(sorted_json_value(item));
        return result;
    }
    return value;
}

std::string sorted_json_dump(const Json &value) {
    return sorted_json_value(value).dump();
}

ValidationResult invalid(std::string code, std::string detail) {
    return ValidationResult{false, std::move(code), std::move(detail)};
}

bool exact_fields(const Json &value, std::initializer_list<const char *> fields) {
    if (!value.is_object() || value.size() != fields.size()) return false;
    for (const auto field : fields) {
        if (!value.contains(field)) return false;
    }
    return true;
}

bool sha256_string(const Json &value) {
    if (!value.is_string() || value.get<std::string>().size() != 64U) return false;
    for (const auto character : value.get<std::string>()) {
        if (!((character >= '0' && character <= '9') || (character >= 'a' && character <= 'f')))
            return false;
    }
    return true;
}

bool generation_string(const Json &value) {
    if (!value.is_string()) return false;
    const auto text = value.get<std::string>();
    if (text.empty() || (text.size() > 1U && text.front() == '0')) return false;
    return std::all_of(text.begin(), text.end(),
                       [](char character) { return character >= '0' && character <= '9'; });
}

bool identifier_string(const Json &value, bool allow_empty = false) {
    if (!value.is_string()) return false;
    const auto text = value.get<std::string>();
    if (text.empty()) return allow_empty;
    if (text.size() > 128U || !((text.front() >= 'A' && text.front() <= 'Z') ||
                                (text.front() >= 'a' && text.front() <= 'z')))
        return false;
    return std::all_of(text.begin() + 1, text.end(), [](char character) {
        return (character >= 'A' && character <= 'Z') || (character >= 'a' && character <= 'z') ||
               (character >= '0' && character <= '9') || character == '.' || character == '_' ||
               character == ':' || character == '-';
    });
}

bool nonempty_string(const Json &value) {
    return value.is_string() && !value.get<std::string>().empty();
}

bool generation_window(const Json &value, const char *minimum, const char *maximum) {
    if (!generation_string(value.at(minimum)) || !generation_string(value.at(maximum)))
        return false;
    const auto &low = value.at(minimum).get_ref<const std::string &>();
    const auto &high = value.at(maximum).get_ref<const std::string &>();
    return low.size() < high.size() || (low.size() == high.size() && low <= high);
}

std::u16string utf16_key(const std::string &text) {
    static std::wstring_convert<std::codecvt_utf8_utf16<char16_t>, char16_t> converter;
    return converter.from_bytes(text);
}

bool sorted_unique_strings(const Json &value, bool identifiers) {
    if (!value.is_array() || value.empty()) return false;
    std::u16string previous;
    bool first = true;
    for (const auto &item : value) {
        if (!(identifiers ? identifier_string(item) : nonempty_string(item))) return false;
        const auto &current = item.get_ref<const std::string &>();
        const auto current_key = utf16_key(current);
        if (!first && current_key <= previous) return false;
        previous = current_key;
        first = false;
    }
    return true;
}

bool has_noncanonical_numeric_token(std::string_view json) {
    bool in_string = false;
    bool escaped = false;
    for (std::size_t index = 0; index < json.size(); ++index) {
        const char character = json[index];
        if (in_string) {
            if (escaped)
                escaped = false;
            else if (character == '\\')
                escaped = true;
            else if (character == '"')
                in_string = false;
            continue;
        }
        if (character == '"') {
            in_string = true;
            continue;
        }
        if (character != '-' && !(character >= '0' && character <= '9')) continue;
        const auto token_end = json.find_first_of(",]} \t\r\n", index);
        const auto token = json.substr(
            index, token_end == std::string_view::npos ? json.size() - index : token_end - index);
        if (token.find('.') != std::string_view::npos ||
            token.find('e') != std::string_view::npos ||
            token.find('E') != std::string_view::npos ||
            (token.size() > 1U && token.front() == '-' && token[1] == '0')) {
            return true;
        }
        index += token.empty() ? 0U : token.size() - 1U;
    }
    return false;
}

} // namespace

std::string authority_digest_sha256_hex(std::string_view domain, std::string_view media_type,
                                        std::string_view payload_bytes) {
    if (domain.empty() || media_type.empty() || domain.find('\0') != std::string_view::npos ||
        media_type.find('\0') != std::string_view::npos) {
        return {};
    }
    std::string input = "echelon-forge-authority-v1";
    input.push_back('\0');
    input.append(domain);
    input.push_back('\0');
    input.append(media_type);
    input.push_back('\0');
    input.append(payload_bytes);
    return runtime::crypto::sha256_hex(input);
}

std::string sha256_hex(std::string_view bytes) {
    return runtime::crypto::sha256_hex(bytes);
}

std::optional<std::string> canonical_authority_json(std::string_view json_bytes) {
    try {
        const auto value = Json::parse(json_bytes.begin(), json_bytes.end());
        return sorted_json_dump(value);
    } catch (const Json::exception &) {
        return std::nullopt;
    }
}

std::optional<std::string>
checkpoint_replay_aggregate_sha256(std::string_view checkpoint_payload_json) {
    try {
        const auto payload =
            Json::parse(checkpoint_payload_json.begin(), checkpoint_payload_json.end());
        if (!payload.is_object() || !payload.contains("state_schema_generation") ||
            !payload.contains("transfer_fence_sequence") || !payload.contains("world_fragments")) {
            return std::nullopt;
        }
        const Json material = {
            {"state_schema_generation", payload.at("state_schema_generation")},
            {"transfer_fence_sequence", payload.at("transfer_fence_sequence")},
            {"world_fragments", payload.at("world_fragments")},
        };
        return runtime::crypto::sha256_hex(sorted_json_dump(material));
    } catch (const Json::exception &) {
        return std::nullopt;
    }
}

ValidationResult validate_authority_envelope_json(std::string_view envelope_json,
                                                  std::string_view canonical_payload_bytes) {
    if (envelope_json.starts_with("\xEF\xBB\xBF") ||
        canonical_payload_bytes.starts_with("\xEF\xBB\xBF") ||
        has_noncanonical_numeric_token(envelope_json) ||
        has_noncanonical_numeric_token(canonical_payload_bytes)) {
        return invalid("authority.noncanonical_payload",
                       "BOM or non-canonical numeric token is forbidden");
    }
    Json envelope;
    Json payload;
    try {
        envelope = Json::parse(envelope_json.begin(), envelope_json.end());
        payload = Json::parse(canonical_payload_bytes.begin(), canonical_payload_bytes.end());
    } catch (const Json::exception &error) {
        return invalid("authority.input_error", error.what());
    }
    if (!exact_fields(envelope, {"canonicalization", "domain", "envelope_version", "media_type",
                                 "payload", "payload_sha256", "signatures"})) {
        return invalid("authority.envelope_fields", "envelope fields are not exact");
    }
    if (!envelope.at("canonicalization").is_string() ||
        !envelope.at("envelope_version").is_string() || !envelope.at("domain").is_string() ||
        !envelope.at("media_type").is_string() ||
        envelope.at("canonicalization").get<std::string>() != std::string(kCanonicalization) ||
        envelope.at("envelope_version").get<std::string>() != std::string(kEnvelopeVersion) ||
        !envelope.at("domain").is_string() || !envelope.at("media_type").is_string()) {
        return invalid("authority.version", "canonicalization or envelope version mismatch");
    }
    if (!envelope.at("signatures").is_array()) {
        return invalid("authority.signatures", "signatures must be an array");
    }
    for (const auto &signature : envelope.at("signatures")) {
        if (!exact_fields(signature, {"algorithm", "key_id", "signature", "signer_context"}) ||
            !nonempty_string(signature.at("algorithm")) ||
            !nonempty_string(signature.at("key_id")) ||
            !nonempty_string(signature.at("signature")) ||
            !nonempty_string(signature.at("signer_context"))) {
            return invalid("authority.signatures", "signature context fields are not exact");
        }
    }
    if (envelope.dump() != envelope_json || payload.dump() != canonical_payload_bytes ||
        envelope.at("payload") != payload) {
        return invalid("authority.noncanonical_payload", "native payload bytes are not canonical");
    }
    if (!payload.is_object()) {
        return invalid("authority.payload_type", "authority payload must be an object");
    }
    if (!payload.contains("authority_kind") || !payload.at("authority_kind").is_string()) {
        return invalid("authority.payload_type", "authority_kind must be a string");
    }
    const auto kind = payload.at("authority_kind").get<std::string>();
    const auto expected_domain = kind == "release_manifest"          ? "release.manifest"
                                 : kind == "resolved_execution_plan" ? "composition.execution-plan"
                                 : kind == "resolved_composition_plan" ? "composition.resolved-plan"
                                 : kind == "rollout_decision"          ? "release.rollout-decision"
                                 : kind == "state_checkpoint"          ? "runtime.state-checkpoint"
                                                                       : "";
    const auto expected_media =
        kind == "release_manifest" ? "application/vnd.echelon-forge.release-manifest.v1+json"
        : kind == "resolved_execution_plan"
            ? "application/vnd.echelon-forge.resolved-execution-plan.v1+json"
        : kind == "resolved_composition_plan"
            ? "application/vnd.echelon-forge.resolved-composition-plan.v1+json"
        : kind == "rollout_decision" ? "application/vnd.echelon-forge.rollout-decision.v1+json"
        : kind == "state_checkpoint" ? "application/vnd.echelon-forge.state-checkpoint.v1+json"
                                     : "";
    if (expected_domain[0] == '\0' || expected_media[0] == '\0' ||
        envelope.at("domain").get<std::string>() != expected_domain ||
        envelope.at("media_type").get<std::string>() != expected_media) {
        return invalid("authority.owner", "authority kind/domain owner mismatch");
    }
    const auto expected_schema = std::string("echelon_forge.") + kind + ".v1";
    const auto expected_contract = std::string("echelon_forge.") + kind + "_contract.v1";
    const auto expected_writer = kind == "release_manifest"            ? "release_artifact_pipeline"
                                 : kind == "resolved_execution_plan"   ? "plan_compiler"
                                 : kind == "resolved_composition_plan" ? "plan_compiler"
                                 : kind == "rollout_decision"          ? "release_controller"
                                                                       : "runtime_host";
    if (!payload.contains("schema_version") || !payload.contains("contract_version") ||
        !payload.contains("writer_role") || !payload.contains("writer_generation") ||
        !payload.at("schema_version").is_string() || !payload.at("contract_version").is_string() ||
        !payload.at("writer_role").is_string() || payload.at("schema_version") != expected_schema ||
        payload.at("contract_version") != expected_contract ||
        payload.at("writer_role") != expected_writer ||
        !generation_string(payload.at("writer_generation"))) {
        return invalid("authority.owner", "authority schema/contract/writer generation mismatch");
    }
    if (kind == "release_manifest" && !exact_fields(payload, {"authority_kind",
                                                              "contract_version",
                                                              "package_set",
                                                              "provenance_sha256",
                                                              "reader_generation_max",
                                                              "reader_generation_min",
                                                              "release_id",
                                                              "sbom_sha256",
                                                              "schema_version",
                                                              "source_revision",
                                                              "supported_rows",
                                                              "toolchain_identity",
                                                              "writer_generation",
                                                              "writer_role",
                                                              "compatibility_generation",
                                                              "minimum_reader_generation",
                                                              "state_schema_generation",
                                                              "rollback_policy",
                                                              "stored_artifact_inventory_sha256",
                                                              "rollback_deadline",
                                                              "last_reader_deadline",
                                                              "irreversible_write_boundary"})) {
        return invalid("authority.payload_fields", "release payload fields are not exact");
    }
    if (kind == "release_manifest") {
        for (const auto field : {"authority_kind",
                                 "contract_version",
                                 "release_id",
                                 "schema_version",
                                 "source_revision",
                                 "toolchain_identity",
                                 "writer_generation",
                                 "writer_role",
                                 "reader_generation_min",
                                 "reader_generation_max",
                                 "provenance_sha256",
                                 "sbom_sha256",
                                 "compatibility_generation",
                                 "minimum_reader_generation",
                                 "state_schema_generation",
                                 "rollback_policy",
                                 "stored_artifact_inventory_sha256",
                                 "rollback_deadline",
                                 "last_reader_deadline",
                                 "irreversible_write_boundary"}) {
            if (!payload.at(field).is_string() || payload.at(field).get<std::string>().empty()) {
                return invalid("authority.payload_type",
                               "release string field is empty or non-string");
            }
        }
        if (payload.at("authority_kind") != "release_manifest" ||
            payload.at("schema_version") != "echelon_forge.release_manifest.v1" ||
            payload.at("contract_version") != "echelon_forge.release_manifest_contract.v1" ||
            payload.at("writer_role") != "release_artifact_pipeline" ||
            !identifier_string(payload.at("release_id")) ||
            !nonempty_string(payload.at("toolchain_identity")) ||
            !nonempty_string(payload.at("source_revision")) ||
            !generation_string(payload.at("writer_generation")) ||
            !generation_string(payload.at("reader_generation_min")) ||
            !generation_string(payload.at("reader_generation_max")) ||
            !generation_string(payload.at("compatibility_generation")) ||
            !generation_string(payload.at("minimum_reader_generation")) ||
            !generation_string(payload.at("state_schema_generation")) ||
            !generation_window(payload, "reader_generation_min", "reader_generation_max")) {
            return invalid("authority.payload_type",
                           "release owner/version/generation is not admitted");
        }
        if (!sorted_unique_strings(payload.at("supported_rows"), false) ||
            !payload.at("package_set").is_array() || payload.at("package_set").empty()) {
            return invalid("authority.payload_type", "release package/support rows are not arrays");
        }
        std::u16string previous_package;
        bool first_package = true;
        for (const auto &package : payload.at("package_set")) {
            if (!exact_fields(package, {"name", "sha256"}) ||
                !nonempty_string(package.at("name")) || !sha256_string(package.at("sha256"))) {
                return invalid("authority.payload_type", "release package entry is not typed");
            }
            const auto &name = package.at("name").get_ref<const std::string &>();
            const auto name_key = utf16_key(name);
            if (!first_package && name_key <= previous_package)
                return invalid("authority.payload_type",
                               "release package_set is not sorted and unique");
            previous_package = name_key;
            first_package = false;
        }
        for (const auto field :
             {"provenance_sha256", "sbom_sha256", "stored_artifact_inventory_sha256"}) {
            if (!sha256_string(payload.at(field)))
                return invalid("authority.payload_type", "release hash is not SHA-256");
        }
        if (payload.at("rollback_policy") != "checkpoint-recovery" &&
            payload.at("rollback_policy") != "package-restart") {
            return invalid("authority.payload_type", "release rollback policy is not admitted");
        }
    }
    if (kind == "resolved_execution_plan") {
        if (!exact_fields(payload,
                          {"authority_kind", "backend", "backend_request_sha256",
                           "catalog_lock_sha256", "composition_id", "contract_version",
                           "profile_projection_sha256", "provider_versions", "plan_id",
                           "reader_generation_max", "reader_generation_min", "request_sha256",
                           "requested_manifest_sha256", "requested_profile", "resolved_manifest",
                           "resolved_manifest_sha256", "schema_version", "writer_generation",
                           "writer_role"})) {
            return invalid("authority.payload_fields",
                           "execution plan payload fields are not exact");
        }
        for (const auto field :
             {"request_sha256", "catalog_lock_sha256", "profile_projection_sha256",
              "backend_request_sha256", "requested_manifest_sha256", "resolved_manifest_sha256"}) {
            if (!sha256_string(payload.at(field)))
                return invalid("authority.payload_type", "execution plan hash is not SHA-256");
        }
        if (!identifier_string(payload.at("plan_id")) ||
            !identifier_string(payload.at("composition_id")) ||
            !generation_window(payload, "reader_generation_min", "reader_generation_max") ||
            !payload.at("requested_profile").is_object() ||
            !exact_fields(payload.at("requested_profile"), {"profile_id", "profile_version"}) ||
            !identifier_string(payload.at("requested_profile").at("profile_id")) ||
            !nonempty_string(payload.at("requested_profile").at("profile_version"))) {
            return invalid("authority.payload_type",
                           "execution plan identity/profile is not typed");
        }
        const auto &backend = payload.at("backend");
        if (!exact_fields(backend, {"implementation_version", "profile_id", "provider_id",
                                    "required_capabilities"}) ||
            !identifier_string(backend.at("provider_id")) ||
            !identifier_string(backend.at("profile_id")) ||
            !nonempty_string(backend.at("implementation_version")) ||
            !sorted_unique_strings(backend.at("required_capabilities"), false)) {
            return invalid("authority.payload_type", "execution plan backend is not typed");
        }
        const auto &resolved = payload.at("resolved_manifest");
        if (!resolved.is_object() ||
            !runtime::composition::parse_resolved_composition_json(resolved.dump())) {
            return invalid("authority.payload_type", "execution plan resolved manifest is invalid");
        }
        if (payload.at("requested_manifest_sha256") != resolved.at("requested_manifest_sha256") ||
            payload.at("resolved_manifest_sha256") != resolved.at("resolved_manifest_sha256") ||
            resolved.at("manifest").at("composition_id") != payload.at("composition_id") ||
            resolved.at("manifest").at("requested_profile") != payload.at("requested_profile") ||
            resolved.at("manifest").at("backend_request").at("provider_id") !=
                backend.at("provider_id") ||
            resolved.at("manifest").at("backend_request").at("backend_profile_id") !=
                backend.at("profile_id")) {
            return invalid("authority.payload_binding",
                           "execution plan does not bind its resolved manifest");
        }
    }
    if (kind == "resolved_composition_plan") {
        if (!exact_fields(payload,
                          {"adapter_role", "authority_kind", "contract_version", "plan_id",
                           "reader_generation_max", "reader_generation_min", "request_sha256",
                           "resolved_plan", "schema_version", "source_artifact_schema_version",
                           "source_artifact_sha256", "source_request_manifest_binding_sha256",
                           "source_requested_manifest_sha256", "writer_generation",
                           "writer_role"})) {
            return invalid("authority.payload_fields", "plan payload fields are not exact");
        }
        const auto &resolved = payload.at("resolved_plan");
        if (!resolved.is_object() ||
            !exact_fields(resolved,
                          {"manifest", "provider_construction_order", "requested_manifest_sha256",
                           "resolved_manifest_sha256", "resolver_contract_version",
                           "schema_version", "system_registration_order"}) ||
            resolved.at("schema_version") != "echelon_forge.resolved_simulation_composition.v1" ||
            !resolved.at("resolver_contract_version").is_string() ||
            resolved.at("resolver_contract_version").get<std::string>() !=
                "echelon_forge.simulation_composition_resolver.v1" ||
            !resolved.at("manifest").is_object() ||
            !resolved.at("provider_construction_order").is_array() ||
            !resolved.at("system_registration_order").is_array() ||
            !sha256_string(resolved.at("requested_manifest_sha256")) ||
            !sha256_string(resolved.at("resolved_manifest_sha256")) ||
            !sha256_string(payload.at("source_artifact_sha256")) ||
            !sha256_string(payload.at("source_requested_manifest_sha256")) ||
            !sha256_string(payload.at("source_request_manifest_binding_sha256")) ||
            payload.at("adapter_role") != "legacy_resolved_manifest_reader" ||
            !identifier_string(payload.at("plan_id")) ||
            !sha256_string(payload.at("request_sha256")) ||
            payload.at("source_artifact_schema_version") !=
                "echelon_forge.resolved_simulation_composition.v1" ||
            !generation_window(payload, "reader_generation_min", "reader_generation_max")) {
            return invalid("authority.payload_type", "resolved plan nested schema is not admitted");
        }
        if (!runtime::composition::parse_resolved_composition_json(resolved.dump())) {
            return invalid("authority.payload_type",
                           "native resolved-plan parser rejected legacy source");
        }
        if (payload.at("source_requested_manifest_sha256") !=
            resolved.at("requested_manifest_sha256")) {
            return invalid("authority.payload_binding",
                           "source requested-manifest digest differs from nested plan");
        }
        std::string binding_input = payload.at("request_sha256").get<std::string>();
        binding_input.push_back('\0');
        binding_input += payload.at("source_requested_manifest_sha256").get<std::string>();
        if (runtime::crypto::sha256_hex(binding_input) !=
            payload.at("source_request_manifest_binding_sha256").get<std::string>()) {
            return invalid("authority.payload_binding",
                           "source request/manifest provenance binding differs");
        }
        auto resolved_body = resolved;
        resolved_body.erase("resolved_manifest_sha256");
        if (runtime::crypto::sha256_hex(resolved_body.dump()) !=
                resolved.at("resolved_manifest_sha256").get<std::string>() ||
            runtime::crypto::sha256_hex(resolved.dump()) !=
                payload.at("source_artifact_sha256").get<std::string>()) {
            return invalid("authority.payload_digest",
                           "resolved plan legacy digest does not match source bytes");
        }
    }
    if (kind == "rollout_decision") {
        if (!exact_fields(payload,
                          {"authority_kind", "checkpoint_id", "cohort", "contract_version",
                           "decision_id", "decision_sequence", "irreversible_write_boundary",
                           "manifest_sha256", "plan_sha256", "plan_reader_generation_min",
                           "plan_reader_generation_max", "predecessor_decision_id", "release_id",
                           "rollback_deadline", "schema_version", "state", "writer_generation",
                           "writer_role"})) {
            return invalid("authority.payload_fields", "rollout payload fields are not exact");
        }
        if (payload.at("authority_kind") != "rollout_decision" ||
            payload.at("schema_version") != "echelon_forge.rollout_decision.v1" ||
            payload.at("contract_version") != "echelon_forge.rollout_decision_contract.v1" ||
            payload.at("writer_role") != "release_controller" ||
            !identifier_string(payload.at("decision_id")) ||
            !identifier_string(payload.at("release_id")) ||
            !nonempty_string(payload.at("cohort")) ||
            !nonempty_string(payload.at("rollback_deadline")) ||
            !nonempty_string(payload.at("irreversible_write_boundary")) ||
            (!identifier_string(payload.at("predecessor_decision_id"), true)) ||
            (!identifier_string(payload.at("checkpoint_id"), true)) ||
            !generation_window(payload, "plan_reader_generation_min",
                               "plan_reader_generation_max") ||
            !generation_string(payload.at("decision_sequence")) ||
            !payload.at("state").is_string() ||
            std::set<std::string>{"prepared", "shadow", "canary-ready", "production-canary",
                                  "adoption-expanding", "rollback-window", "stable", "backed-out"}
                    .count(payload.at("state").get<std::string>()) == 0 ||
            !sha256_string(payload.at("manifest_sha256")) ||
            !sha256_string(payload.at("plan_sha256")) ||
            !payload.at("decision_sequence").is_string()) {
            return invalid("authority.payload_type", "rollout state/hash/generation is not typed");
        }
    }
    if (kind == "state_checkpoint") {
        if (!exact_fields(payload,
                          {"aggregate_state_sha256", "authority_kind", "checkpoint_id",
                           "contract_version", "decision_id", "host_boot_id", "incarnation_epoch",
                           "plan_sha256", "release_id", "run_id", "schema_version",
                           "state_schema_generation", "target_reader_generation_min",
                           "target_reader_generation_max", "transfer_fence_sequence",
                           "world_fragments", "writer_generation", "writer_role"})) {
            return invalid("authority.payload_fields", "checkpoint payload fields are not exact");
        }
        if (payload.at("authority_kind") != "state_checkpoint" ||
            payload.at("schema_version") != "echelon_forge.state_checkpoint.v1" ||
            payload.at("contract_version") != "echelon_forge.state_checkpoint_contract.v1" ||
            payload.at("writer_role") != "runtime_host" ||
            !identifier_string(payload.at("checkpoint_id")) ||
            !identifier_string(payload.at("release_id")) ||
            !identifier_string(payload.at("decision_id")) ||
            !identifier_string(payload.at("run_id")) ||
            !identifier_string(payload.at("host_boot_id")) ||
            !generation_string(payload.at("incarnation_epoch")) ||
            !generation_string(payload.at("transfer_fence_sequence")) ||
            !generation_string(payload.at("state_schema_generation")) ||
            !generation_window(payload, "target_reader_generation_min",
                               "target_reader_generation_max") ||
            !sha256_string(payload.at("plan_sha256")) ||
            !sha256_string(payload.at("aggregate_state_sha256")) ||
            !payload.at("world_fragments").is_array() || payload.at("world_fragments").empty()) {
            return invalid("authority.payload_type", "checkpoint hash/fragments are not typed");
        }
        std::set<std::string> world_ids;
        for (const auto &fragment : payload.at("world_fragments")) {
            if (!exact_fields(fragment,
                              {"episode_ids", "fragment_sequence", "state_sha256", "world_id"}) ||
                !identifier_string(fragment.at("world_id")) ||
                !sorted_unique_strings(fragment.at("episode_ids"), true) ||
                !generation_string(fragment.at("fragment_sequence")) ||
                !sha256_string(fragment.at("state_sha256")) ||
                !world_ids.insert(fragment.at("world_id").get<std::string>()).second) {
                return invalid("authority.payload_type",
                               "checkpoint fragment coverage is not unique/typed");
            }
        }
        std::string previous_sequence;
        bool first_sequence = true;
        for (const auto &fragment : payload.at("world_fragments")) {
            const auto &sequence = fragment.at("fragment_sequence").get_ref<const std::string &>();
            if (!first_sequence &&
                (sequence.size() < previous_sequence.size() ||
                 (sequence.size() == previous_sequence.size() && sequence <= previous_sequence))) {
                return invalid("authority.payload_type",
                               "checkpoint fragments are not ordered and unique");
            }
            previous_sequence = sequence;
            first_sequence = false;
        }
    }
    if (kind == "resolved_composition_plan" &&
        !exact_fields(payload,
                      {"adapter_role", "authority_kind", "contract_version", "plan_id",
                       "reader_generation_max", "reader_generation_min", "request_sha256",
                       "resolved_plan", "schema_version", "source_artifact_schema_version",
                       "source_artifact_sha256", "source_request_manifest_binding_sha256",
                       "source_requested_manifest_sha256", "writer_generation", "writer_role"})) {
        return invalid("authority.payload_fields", "plan payload fields are not exact");
    }
    if (kind == "rollout_decision" &&
        !exact_fields(payload, {"authority_kind", "checkpoint_id", "cohort", "contract_version",
                                "decision_id", "decision_sequence", "irreversible_write_boundary",
                                "manifest_sha256", "plan_sha256", "plan_reader_generation_min",
                                "plan_reader_generation_max", "predecessor_decision_id",
                                "release_id", "rollback_deadline", "schema_version", "state",
                                "writer_generation", "writer_role"})) {
        return invalid("authority.payload_fields", "rollout payload fields are not exact");
    }
    if (kind == "state_checkpoint" &&
        !exact_fields(payload,
                      {"aggregate_state_sha256", "authority_kind", "checkpoint_id",
                       "contract_version", "decision_id", "host_boot_id", "incarnation_epoch",
                       "plan_sha256", "release_id", "run_id", "schema_version",
                       "state_schema_generation", "target_reader_generation_min",
                       "target_reader_generation_max", "transfer_fence_sequence", "world_fragments",
                       "writer_generation", "writer_role"})) {
        return invalid("authority.payload_fields", "checkpoint payload fields are not exact");
    }
    const auto expected = authority_digest_sha256_hex(envelope.at("domain").get<std::string>(),
                                                      envelope.at("media_type").get<std::string>(),
                                                      canonical_payload_bytes);
    if (!envelope.at("payload_sha256").is_string() ||
        envelope.at("payload_sha256").get<std::string>() != expected) {
        return invalid("authority.digest", "detached digest mismatch");
    }
    return ValidationResult{true, {}, {}};
}

ValidationResult validate_resolved_execution_plan_json(std::string_view plan_json) {
    if (plan_json.starts_with("\xEF\xBB\xBF") || has_noncanonical_numeric_token(plan_json)) {
        return invalid("plan.noncanonical_payload",
                       "BOM or non-canonical numeric token is forbidden");
    }
    Json plan;
    try {
        plan = Json::parse(plan_json.begin(), plan_json.end());
    } catch (const Json::exception &error) {
        return invalid("plan.input_error", error.what());
    }
    if (plan.dump() != plan_json) {
        return invalid("plan.noncanonical_payload", "closed plan bytes are not canonical JSON");
    }
    if (!exact_fields(plan, {"authority_envelope_json", "authority_payload_bytes", "canonical_json",
                             "canonicalization", "hash_algorithm", "input_bindings", "owner_inputs",
                             "owner_join", "plan_contract_version", "plan_id", "plan_sha256",
                             "reader_generation_max", "reader_generation_min", "schema_version",
                             "writer_generation", "writer_role"})) {
        return invalid("plan.fields", "closed plan fields are not exact");
    }
    if (plan.at("schema_version") != "echelon_forge.resolved_execution_plan.v1" ||
        plan.at("plan_contract_version") != "1.0.0" || plan.at("writer_role") != "plan_compiler" ||
        plan.at("canonicalization") != "echelon_forge.sorted_utf8_json.v1" ||
        plan.at("hash_algorithm") != "sha256" || !identifier_string(plan.at("plan_id")) ||
        !generation_string(plan.at("writer_generation")) ||
        !generation_window(plan, "reader_generation_min", "reader_generation_max") ||
        !sha256_string(plan.at("plan_sha256")) || !plan.at("canonical_json").is_string() ||
        !plan.at("authority_envelope_json").is_string() ||
        !plan.at("authority_payload_bytes").is_object()) {
        return invalid("plan.type", "closed plan version, identity, or generation is not admitted");
    }
    const auto &bindings = plan.at("input_bindings");
    if (!exact_fields(bindings, {"backend_request_sha256", "catalog_lock_sha256",
                                 "profile_projection_sha256", "request_sha256",
                                 "requested_manifest_sha256", "resolved_manifest_sha256"})) {
        return invalid("plan.bindings", "input bindings are not exact");
    }
    for (const auto field :
         {"backend_request_sha256", "catalog_lock_sha256", "profile_projection_sha256",
          "request_sha256", "requested_manifest_sha256", "resolved_manifest_sha256"}) {
        if (!sha256_string(bindings.at(field)))
            return invalid("plan.bindings", "input binding is not SHA-256");
    }
    const auto &owner_inputs = plan.at("owner_inputs");
    if (!exact_fields(owner_inputs, {"backend_request", "catalog_lock", "profile_projection",
                                     "request", "requested_manifest", "resolved_manifest"})) {
        return invalid("plan.owner_inputs", "owner input fields are not exact");
    }
    for (const auto field : {"backend_request", "catalog_lock", "profile_projection", "request",
                             "requested_manifest", "resolved_manifest"}) {
        if (!owner_inputs.at(field).is_object())
            return invalid("plan.owner_inputs", "owner input is not an object");
    }
    const auto request_sha =
        runtime::crypto::sha256_hex(sorted_json_dump(owner_inputs.at("request")));
    if (request_sha != bindings.at("request_sha256").get<std::string>())
        return invalid("plan.owner_inputs", "request digest mismatch");
    const auto backend_sha =
        runtime::crypto::sha256_hex(sorted_json_dump(owner_inputs.at("backend_request")));
    if (backend_sha != bindings.at("backend_request_sha256").get<std::string>())
        return invalid("plan.owner_inputs", "backend request digest mismatch");
    const auto requested_sha =
        runtime::crypto::sha256_hex(sorted_json_dump(owner_inputs.at("requested_manifest")));
    if (requested_sha != bindings.at("requested_manifest_sha256").get<std::string>())
        return invalid("plan.owner_inputs", "requested manifest digest mismatch");
    Json lock_payload = owner_inputs.at("catalog_lock");
    if (!lock_payload.contains("canonical_json") || !lock_payload.contains("lock_sha256") ||
        !lock_payload.at("canonical_json").is_string() ||
        !sha256_string(lock_payload.at("lock_sha256"))) {
        return invalid("plan.owner_inputs", "catalog lock identity fields are absent");
    }
    if (lock_payload.at("canonical_json").get<std::string>() != sorted_json_dump([&]() {
            Json copy = lock_payload;
            copy.erase("canonical_json");
            copy.erase("lock_sha256");
            return copy;
        }())) {
        return invalid("plan.owner_inputs",
                       "catalog lock canonical bytes are not sorted UTF-8 JSON");
    }
    const auto lock_sha =
        runtime::crypto::sha256_hex(lock_payload.at("canonical_json").get<std::string>());
    if (lock_sha != lock_payload.at("lock_sha256").get<std::string>() ||
        lock_sha != bindings.at("catalog_lock_sha256").get<std::string>()) {
        return invalid("plan.owner_inputs", "catalog lock digest mismatch");
    }
    if (!lock_payload.contains("request_sha256") ||
        lock_payload.at("request_sha256") != bindings.at("request_sha256")) {
        return invalid("plan.owner_inputs", "catalog lock is not bound to the request");
    }
    Json projection_payload = owner_inputs.at("profile_projection");
    if (!projection_payload.contains("canonical_json") ||
        !projection_payload.contains("projection_sha256") ||
        !projection_payload.at("canonical_json").is_string() ||
        !sha256_string(projection_payload.at("projection_sha256")) ||
        runtime::crypto::sha256_hex(projection_payload.at("canonical_json").get<std::string>()) !=
            projection_payload.at("projection_sha256").get<std::string>() ||
        projection_payload.at("projection_sha256").get<std::string>() !=
            bindings.at("profile_projection_sha256").get<std::string>()) {
        return invalid("plan.owner_inputs", "profile projection digest mismatch");
    }
    {
        Json copy = projection_payload;
        copy.erase("canonical_json");
        copy.erase("projection_sha256");
        if (projection_payload.at("canonical_json") != sorted_json_dump(copy) ||
            projection_payload.at("request_sha256") != bindings.at("request_sha256") ||
            projection_payload.at("lock_sha256") != bindings.at("catalog_lock_sha256")) {
            return invalid("plan.owner_inputs",
                           "profile projection is not bound to request and catalog lock");
        }
    }
    Json resolved_payload = owner_inputs.at("resolved_manifest");
    if (!resolved_payload.contains("resolved_manifest_sha256") ||
        !sha256_string(resolved_payload.at("resolved_manifest_sha256"))) {
        return invalid("plan.owner_inputs", "resolved manifest identity is absent");
    }
    const auto resolved_hash = resolved_payload.at("resolved_manifest_sha256").get<std::string>();
    resolved_payload.erase("resolved_manifest_sha256");
    if (runtime::crypto::sha256_hex(sorted_json_dump(resolved_payload)) != resolved_hash ||
        resolved_hash != bindings.at("resolved_manifest_sha256").get<std::string>()) {
        return invalid("plan.owner_inputs", "resolved manifest digest mismatch");
    }
    const auto &owner = plan.at("owner_join");
    if (!exact_fields(owner, {"backend_implementation_version", "backend_profile_id",
                              "backend_provider_id", "catalog_backend_capabilities",
                              "catalog_backend_implementation_id", "catalog_backend_owner_id",
                              "catalog_backend_provenance", "composition_id", "requested_profile",
                              "resolver_contract_version"}) ||
        !nonempty_string(owner.at("backend_implementation_version")) ||
        !identifier_string(owner.at("backend_profile_id")) ||
        !identifier_string(owner.at("backend_provider_id")) ||
        !identifier_string(owner.at("composition_id")) ||
        !nonempty_string(owner.at("resolver_contract_version")) ||
        !sorted_unique_strings(owner.at("catalog_backend_capabilities"), false) ||
        !nonempty_string(owner.at("catalog_backend_implementation_id")) ||
        !nonempty_string(owner.at("catalog_backend_owner_id")) ||
        !owner.at("catalog_backend_provenance").is_object() ||
        !exact_fields(owner.at("requested_profile"), {"profile_id", "profile_version"}) ||
        !identifier_string(owner.at("requested_profile").at("profile_id")) ||
        !nonempty_string(owner.at("requested_profile").at("profile_version"))) {
        return invalid("plan.owner_join", "owner-derived join is not typed");
    }

    Json envelope;
    try {
        envelope = Json::parse(plan.at("authority_envelope_json").get<std::string>());
    } catch (const Json::exception &error) {
        return invalid("plan.authority", error.what());
    }
    const auto payload_bytes = plan.at("authority_payload_bytes").dump();
    const auto authority_result = validate_authority_envelope_json(
        plan.at("authority_envelope_json").get<std::string>(), payload_bytes);
    if (!authority_result.valid) return authority_result;
    if (envelope.at("payload") != plan.at("authority_payload_bytes") ||
        envelope.at("payload").at("plan_id") != plan.at("plan_id") ||
        envelope.at("payload").at("writer_generation") != plan.at("writer_generation") ||
        envelope.at("payload").at("reader_generation_min") != plan.at("reader_generation_min") ||
        envelope.at("payload").at("reader_generation_max") != plan.at("reader_generation_max")) {
        return invalid("plan.authority_binding",
                       "embedded plan authority does not match wrapper identity");
    }
    const auto &authority_payload = envelope.at("payload");
    const auto &resolved = authority_payload.at("resolved_manifest");
    const auto &manifest = resolved.at("manifest");
    const auto &backend = authority_payload.at("backend");
    if (owner_inputs.at("resolved_manifest") != resolved ||
        owner_inputs.at("requested_manifest") != resolved.at("manifest") ||
        bindings.at("catalog_lock_sha256").get<std::string>() !=
            authority_payload.at("catalog_lock_sha256").get<std::string>() ||
        bindings.at("profile_projection_sha256").get<std::string>() !=
            authority_payload.at("profile_projection_sha256").get<std::string>() ||
        bindings.at("backend_request_sha256").get<std::string>() !=
            authority_payload.at("backend_request_sha256").get<std::string>()) {
        return invalid("plan.owner_binding",
                       "embedded owner inputs disagree with execution-plan authority");
    }
    if (bindings.at("request_sha256").get<std::string>() !=
            authority_payload.at("request_sha256").get<std::string>() ||
        bindings.at("requested_manifest_sha256").get<std::string>() !=
            authority_payload.at("requested_manifest_sha256").get<std::string>() ||
        bindings.at("resolved_manifest_sha256").get<std::string>() !=
            authority_payload.at("resolved_manifest_sha256").get<std::string>() ||
        owner.at("composition_id").get<std::string>() !=
            manifest.at("composition_id").get<std::string>() ||
        owner.at("requested_profile") != manifest.at("requested_profile") ||
        owner.at("resolver_contract_version") != resolved.at("resolver_contract_version") ||
        owner.at("backend_provider_id").get<std::string>() !=
            manifest.at("backend_request").at("provider_id").get<std::string>() ||
        owner.at("backend_profile_id").get<std::string>() !=
            manifest.at("backend_request").at("backend_profile_id").get<std::string>()) {
        return invalid("plan.owner_binding",
                       "input bindings or owner join disagree with the embedded resolved plan");
    }
    const auto &request_input = owner_inputs.at("request");
    const auto &projection_input = owner_inputs.at("profile_projection");
    if (!request_input.contains("requested_profile") ||
        !request_input.contains("contract_versions") ||
        !projection_input.contains("requested_profile") ||
        !projection_input.contains("request_sha256") || !projection_input.contains("lock_sha256") ||
        request_input.at("requested_profile") != manifest.at("requested_profile") ||
        projection_input.at("requested_profile") != manifest.at("requested_profile") ||
        projection_input.at("request_sha256") != bindings.at("request_sha256") ||
        projection_input.at("lock_sha256") != bindings.at("catalog_lock_sha256") ||
        resolved.at("requested_manifest_sha256") != bindings.at("requested_manifest_sha256")) {
        return invalid("plan.owner_binding",
                       "request, projection, and manifest owner joins disagree");
    }
    const auto &backend_input = owner_inputs.at("backend_request");
    const auto &lock_input = owner_inputs.at("catalog_lock");
    const auto &backend_manifest = manifest.at("backend_request");
    if (!exact_fields(backend_input,
                      {"backend_profile_id", "provider_id", "provider_implementation_version",
                       "required_capabilities", "schema_version"}) ||
        backend_input.at("provider_id") != backend.at("provider_id") ||
        backend_input.at("backend_profile_id") != backend.at("profile_id") ||
        backend_input.at("required_capabilities") != backend.at("required_capabilities") ||
        backend_input.at("provider_implementation_version") !=
            backend.at("implementation_version") ||
        backend_manifest.at("provider_id") != backend_input.at("provider_id") ||
        backend_manifest.at("backend_profile_id") != backend_input.at("backend_profile_id")) {
        return invalid("plan.owner_binding",
                       "backend request is not bound to the execution-plan authority");
    }
    if (!lock_input.contains("entries") || !lock_input.at("entries").is_array()) {
        return invalid("plan.owner_binding", "catalog lock entries are absent");
    }
    std::size_t backend_entries = 0;
    for (const auto &entry : lock_input.at("entries")) {
        if (!entry.is_object() || !entry.contains("category") || entry.at("category") != "backend")
            continue;
        ++backend_entries;
        if (!exact_fields(entry,
                          {"capabilities", "category", "descriptor_id", "implementation_id",
                           "implementation_version", "owner_id", "provenance", "trust_decision"}) ||
            entry.at("descriptor_id") != backend_input.at("provider_id") ||
            entry.at("implementation_version") !=
                backend_input.at("provider_implementation_version") ||
            entry.at("trust_decision") != "admitted" ||
            entry.at("owner_id") != owner.at("catalog_backend_owner_id") ||
            entry.at("implementation_id") != owner.at("catalog_backend_implementation_id") ||
            entry.at("provenance") != owner.at("catalog_backend_provenance") ||
            entry.at("capabilities") != owner.at("catalog_backend_capabilities")) {
            return invalid("plan.owner_binding",
                           "backend request is not bound to the admitted catalog entry");
        }
    }
    if (backend_entries != 1)
        return invalid("plan.owner_binding", "catalog lock backend cardinality is not one");
    if (!manifest.contains("providers") || !manifest.at("providers").is_array()) {
        return invalid("plan.owner_binding", "resolved provider rows are absent");
    }
    std::size_t backend_provider_rows = 0;
    for (const auto &provider : manifest.at("providers")) {
        if (!provider.is_object() || !provider.contains("provider_id") ||
            provider.at("provider_id") != backend_input.at("provider_id")) {
            continue;
        }
        ++backend_provider_rows;
        if (!provider.contains("implementation_version") ||
            provider.at("implementation_version") !=
                backend_input.at("provider_implementation_version")) {
            return invalid("plan.owner_binding",
                           "backend implementation version differs from resolved provider row");
        }
    }
    if (backend_provider_rows != 1) {
        return invalid("plan.owner_binding",
                       "resolved manifest backend provider cardinality is not one");
    }
    if (!authority_payload.contains("provider_versions") ||
        !authority_payload.at("provider_versions").is_array() ||
        authority_payload.at("provider_versions").size() != manifest.at("providers").size()) {
        return invalid("plan.owner_binding",
                       "provider version projection is not bound to the resolved manifest");
    }
    for (std::size_t index = 0; index < manifest.at("providers").size(); ++index) {
        const auto &provider = manifest.at("providers").at(index);
        const auto &version = authority_payload.at("provider_versions").at(index);
        if (!exact_fields(version, {"implementation_version", "provider_id"}) ||
            version.at("provider_id") != provider.at("provider_id") ||
            version.at("implementation_version") != provider.at("implementation_version")) {
            return invalid("plan.owner_binding",
                           "provider version projection is not bound to the resolved manifest");
        }
    }

    Json canonical_payload = plan;
    canonical_payload.erase("canonical_json");
    canonical_payload.erase("plan_sha256");
    const auto canonical_bytes = sorted_json_dump(canonical_payload);
    if (plan.at("canonical_json").get<std::string>() != canonical_bytes) {
        return invalid("plan.noncanonical_payload",
                       "canonical_json does not match the closed plan payload");
    }
    if (runtime::crypto::sha256_hex(canonical_bytes) != plan.at("plan_sha256").get<std::string>()) {
        return invalid("plan.digest", "closed plan digest mismatch");
    }
    return ValidationResult{true, {}, {}};
}

std::string resolved_execution_plan_sha256_hex(std::string_view canonical_payload_bytes) {
    return runtime::crypto::sha256_hex(canonical_payload_bytes);
}

std::optional<std::string> resolved_manifest_from_execution_plan_json(std::string_view plan_json) {
    const auto result = validate_resolved_execution_plan_json(plan_json);
    if (!result.valid) return std::nullopt;
    try {
        const auto plan = Json::parse(plan_json.begin(), plan_json.end());
        return plan.at("authority_payload_bytes").at("resolved_manifest").dump();
    } catch (const Json::exception &) {
        return std::nullopt;
    }
}

} // namespace runtime::authority_contracts
