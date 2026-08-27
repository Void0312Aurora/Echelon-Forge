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

namespace runtime::authority_contracts {
namespace {

using Json = nlohmann::json;

std::string sha256_hex(std::string_view input) {
    constexpr std::array<std::uint32_t, 64> constants = {
        0x428a2f98U, 0x71374491U, 0xb5c0fbcfU, 0xe9b5dba5U, 0x3956c25bU, 0x59f111f1U, 0x923f82a4U,
        0xab1c5ed5U, 0xd807aa98U, 0x12835b01U, 0x243185beU, 0x550c7dc3U, 0x72be5d74U, 0x80deb1feU,
        0x9bdc06a7U, 0xc19bf174U, 0xe49b69c1U, 0xefbe4786U, 0x0fc19dc6U, 0x240ca1ccU, 0x2de92c6fU,
        0x4a7484aaU, 0x5cb0a9dcU, 0x76f988daU, 0x983e5152U, 0xa831c66dU, 0xb00327c8U, 0xbf597fc7U,
        0xc6e00bf3U, 0xd5a79147U, 0x06ca6351U, 0x14292967U, 0x27b70a85U, 0x2e1b2138U, 0x4d2c6dfcU,
        0x53380d13U, 0x650a7354U, 0x766a0abbU, 0x81c2c92eU, 0x92722c85U, 0xa2bfe8a1U, 0xa81a664bU,
        0xc24b8b70U, 0xc76c51a3U, 0xd192e819U, 0xd6990624U, 0xf40e3585U, 0x106aa070U, 0x19a4c116U,
        0x1e376c08U, 0x2748774cU, 0x34b0bcb5U, 0x391c0cb3U, 0x4ed8aa4aU, 0x5b9cca4fU, 0x682e6ff3U,
        0x748f82eeU, 0x78a5636fU, 0x84c87814U, 0x8cc70208U, 0x90befffaU, 0xa4506cebU, 0xbef9a3f7U,
        0xc67178f2U,
    };
    // This compact implementation is the same SHA-256 primitive used by the
    // existing projection contract, kept local so authority validation has no
    // dependency on the transitional composition target.
    std::array<std::uint32_t, 8> state = {0x6a09e667U, 0xbb67ae85U, 0x3c6ef372U, 0xa54ff53aU,
                                          0x510e527fU, 0x9b05688cU, 0x1f83d9abU, 0x5be0cd19U};
    std::vector<std::uint8_t> bytes(input.begin(), input.end());
    const auto bit_length = static_cast<std::uint64_t>(bytes.size()) * 8U;
    bytes.push_back(0x80U);
    while (bytes.size() % 64U != 56U) bytes.push_back(0U);
    for (int shift = 56; shift >= 0; shift -= 8) bytes.push_back(static_cast<std::uint8_t>((bit_length >> shift) & 0xffU));
    const auto rotr = [](std::uint32_t value, unsigned count) { return (value >> count) | (value << (32U - count)); };
    for (std::size_t offset = 0; offset < bytes.size(); offset += 64U) {
        std::array<std::uint32_t, 64> words{};
        for (std::size_t index = 0; index < 16; ++index) {
            const auto base = offset + index * 4U;
            words[index] = (static_cast<std::uint32_t>(bytes[base]) << 24U) |
                           (static_cast<std::uint32_t>(bytes[base + 1U]) << 16U) |
                           (static_cast<std::uint32_t>(bytes[base + 2U]) << 8U) |
                           static_cast<std::uint32_t>(bytes[base + 3U]);
        }
        for (std::size_t index = 16; index < words.size(); ++index) {
            const auto s0 = rotr(words[index - 15U], 7) ^ rotr(words[index - 15U], 18) ^ (words[index - 15U] >> 3U);
            const auto s1 = rotr(words[index - 2U], 17) ^ rotr(words[index - 2U], 19) ^ (words[index - 2U] >> 10U);
            words[index] = words[index - 16U] + s0 + words[index - 7U] + s1;
        }
        auto [a, b, c, d, e, f, g, h] = state;
        for (std::size_t index = 0; index < words.size(); ++index) {
            const auto s1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
            const auto choose = (e & f) ^ (~e & g);
            const auto temp1 = h + s1 + choose + constants[index] + words[index];
            const auto s0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
            const auto majority = (a & b) ^ (a & c) ^ (b & c);
            const auto temp2 = s0 + majority;
            h = g; g = f; f = e; e = d + temp1; d = c; c = b; b = a; a = temp1 + temp2;
        }
        state[0] += a; state[1] += b; state[2] += c; state[3] += d;
        state[4] += e; state[5] += f; state[6] += g; state[7] += h;
    }
    std::ostringstream output;
    output << std::hex << std::setfill('0');
    for (const auto word : state) output << std::setw(8) << word;
    return output.str();
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
        if (!((character >= '0' && character <= '9') || (character >= 'a' && character <= 'f'))) return false;
    }
    return true;
}

bool generation_string(const Json &value) {
    if (!value.is_string()) return false;
    const auto text = value.get<std::string>();
    if (text.empty() || (text.size() > 1U && text.front() == '0')) return false;
    return std::all_of(text.begin(), text.end(), [](char character) { return character >= '0' && character <= '9'; });
}

bool identifier_string(const Json &value, bool allow_empty = false) {
    if (!value.is_string()) return false;
    const auto text = value.get<std::string>();
    if (text.empty()) return allow_empty;
    if (text.size() > 128U || !((text.front() >= 'A' && text.front() <= 'Z') ||
                                (text.front() >= 'a' && text.front() <= 'z'))) return false;
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
    if (!generation_string(value.at(minimum)) || !generation_string(value.at(maximum))) return false;
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
            if (escaped) escaped = false;
            else if (character == '\\') escaped = true;
            else if (character == '"') in_string = false;
            continue;
        }
        if (character == '"') {
            in_string = true;
            continue;
        }
        if (character != '-' && !(character >= '0' && character <= '9')) continue;
        const auto token_end = json.find_first_of(",]} \t\r\n", index);
        const auto token = json.substr(index, token_end == std::string_view::npos ? json.size() - index : token_end - index);
        if (token.find('.') != std::string_view::npos || token.find('e') != std::string_view::npos ||
            token.find('E') != std::string_view::npos || (token.size() > 1U && token.front() == '-' && token[1] == '0')) {
            return true;
        }
        index += token.empty() ? 0U : token.size() - 1U;
    }
    return false;
}

} // namespace

std::string authority_digest_sha256_hex(std::string_view domain,
                                        std::string_view media_type,
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
    return sha256_hex(input);
}

ValidationResult validate_authority_envelope_json(std::string_view envelope_json,
                                                   std::string_view canonical_payload_bytes) {
    if (envelope_json.starts_with("\xEF\xBB\xBF") || canonical_payload_bytes.starts_with("\xEF\xBB\xBF") ||
        has_noncanonical_numeric_token(envelope_json) || has_noncanonical_numeric_token(canonical_payload_bytes)) {
        return invalid("authority.noncanonical_payload", "BOM or non-canonical numeric token is forbidden");
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
    if (!envelope.at("canonicalization").is_string() || !envelope.at("envelope_version").is_string() ||
        !envelope.at("domain").is_string() || !envelope.at("media_type").is_string() ||
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
            !nonempty_string(signature.at("algorithm")) || !nonempty_string(signature.at("key_id")) ||
            !nonempty_string(signature.at("signature")) || !nonempty_string(signature.at("signer_context"))) {
            return invalid("authority.signatures", "signature context fields are not exact");
        }
    }
    if (envelope.dump() != envelope_json || payload.dump() != canonical_payload_bytes || envelope.at("payload") != payload) {
        return invalid("authority.noncanonical_payload", "native payload bytes are not canonical");
    }
    if (!payload.is_object()) {
        return invalid("authority.payload_type", "authority payload must be an object");
    }
    if (!payload.contains("authority_kind") || !payload.at("authority_kind").is_string()) {
        return invalid("authority.payload_type", "authority_kind must be a string");
    }
    const auto kind = payload.at("authority_kind").get<std::string>();
    const auto expected_domain = kind == "release_manifest" ? "release.manifest" :
                                 kind == "resolved_composition_plan" ? "composition.resolved-plan" :
                                 kind == "rollout_decision" ? "release.rollout-decision" :
                                 kind == "state_checkpoint" ? "runtime.state-checkpoint" : "";
    const auto expected_media = kind == "release_manifest" ? "application/vnd.echelon-forge.release-manifest.v1+json" :
                                kind == "resolved_composition_plan" ? "application/vnd.echelon-forge.resolved-composition-plan.v1+json" :
                                kind == "rollout_decision" ? "application/vnd.echelon-forge.rollout-decision.v1+json" :
                                kind == "state_checkpoint" ? "application/vnd.echelon-forge.state-checkpoint.v1+json" : "";
    if (expected_domain[0] == '\0' || expected_media[0] == '\0' || envelope.at("domain").get<std::string>() != expected_domain ||
        envelope.at("media_type").get<std::string>() != expected_media) {
        return invalid("authority.owner", "authority kind/domain owner mismatch");
    }
    const auto expected_schema = std::string("echelon_forge.") + kind + ".v1";
    const auto expected_contract = std::string("echelon_forge.") + kind + "_contract.v1";
    const auto expected_writer = kind == "release_manifest" ? "release_artifact_pipeline" :
                                 kind == "resolved_composition_plan" ? "plan_compiler" :
                                 kind == "rollout_decision" ? "release_controller" : "runtime_host";
    if (!payload.contains("schema_version") || !payload.contains("contract_version") || !payload.contains("writer_role") ||
        !payload.contains("writer_generation") || !payload.at("schema_version").is_string() ||
        !payload.at("contract_version").is_string() || !payload.at("writer_role").is_string() ||
        payload.at("schema_version") != expected_schema || payload.at("contract_version") != expected_contract ||
        payload.at("writer_role") != expected_writer || !generation_string(payload.at("writer_generation"))) {
        return invalid("authority.owner", "authority schema/contract/writer generation mismatch");
    }
    if (kind == "release_manifest" &&
        !exact_fields(payload, {"authority_kind", "contract_version", "package_set", "provenance_sha256",
                                "reader_generation_max", "reader_generation_min", "release_id", "sbom_sha256",
                                 "schema_version", "source_revision", "supported_rows", "toolchain_identity",
                                 "writer_generation", "writer_role", "compatibility_generation", "minimum_reader_generation",
                                 "state_schema_generation", "rollback_policy", "stored_artifact_inventory_sha256",
                                 "rollback_deadline", "last_reader_deadline", "irreversible_write_boundary"})) {
        return invalid("authority.payload_fields", "release payload fields are not exact");
    }
    if (kind == "release_manifest") {
        for (const auto field : {"authority_kind", "contract_version", "release_id", "schema_version",
                                 "source_revision", "toolchain_identity", "writer_generation", "writer_role",
                                  "reader_generation_min", "reader_generation_max", "provenance_sha256", "sbom_sha256",
                                  "compatibility_generation", "minimum_reader_generation", "state_schema_generation", "rollback_policy",
                                  "stored_artifact_inventory_sha256", "rollback_deadline", "last_reader_deadline",
                                  "irreversible_write_boundary"}) {
            if (!payload.at(field).is_string() || payload.at(field).get<std::string>().empty()) {
                return invalid("authority.payload_type", "release string field is empty or non-string");
            }
        }
        if (payload.at("authority_kind") != "release_manifest" || payload.at("schema_version") != "echelon_forge.release_manifest.v1" ||
            payload.at("contract_version") != "echelon_forge.release_manifest_contract.v1" || payload.at("writer_role") != "release_artifact_pipeline" ||
            !identifier_string(payload.at("release_id")) || !nonempty_string(payload.at("toolchain_identity")) ||
            !nonempty_string(payload.at("source_revision")) ||
            !generation_string(payload.at("writer_generation")) || !generation_string(payload.at("reader_generation_min")) ||
            !generation_string(payload.at("reader_generation_max")) || !generation_string(payload.at("compatibility_generation")) ||
            !generation_string(payload.at("minimum_reader_generation")) || !generation_string(payload.at("state_schema_generation")) ||
            !generation_window(payload, "reader_generation_min", "reader_generation_max")) {
            return invalid("authority.payload_type", "release owner/version/generation is not admitted");
        }
        if (!sorted_unique_strings(payload.at("supported_rows"), false) || !payload.at("package_set").is_array() ||
            payload.at("package_set").empty()) {
            return invalid("authority.payload_type", "release package/support rows are not arrays");
        }
        std::u16string previous_package;
        bool first_package = true;
        for (const auto &package : payload.at("package_set")) {
            if (!exact_fields(package, {"name", "sha256"}) || !nonempty_string(package.at("name")) ||
                !sha256_string(package.at("sha256"))) {
                return invalid("authority.payload_type", "release package entry is not typed");
            }
            const auto &name = package.at("name").get_ref<const std::string &>();
            const auto name_key = utf16_key(name);
            if (!first_package && name_key <= previous_package) return invalid("authority.payload_type", "release package_set is not sorted and unique");
            previous_package = name_key;
            first_package = false;
        }
        for (const auto field : {"provenance_sha256", "sbom_sha256", "stored_artifact_inventory_sha256"}) {
            if (!sha256_string(payload.at(field))) return invalid("authority.payload_type", "release hash is not SHA-256");
        }
        if (payload.at("rollback_policy") != "checkpoint-recovery" && payload.at("rollback_policy") != "package-restart") {
            return invalid("authority.payload_type", "release rollback policy is not admitted");
        }
    }
    if (kind == "resolved_composition_plan") {
        if (!exact_fields(payload, {"adapter_role", "authority_kind", "contract_version", "plan_id", "reader_generation_max",
                                     "reader_generation_min", "request_sha256", "resolved_plan", "schema_version",
                                     "source_artifact_schema_version", "source_artifact_sha256", "source_request_manifest_binding_sha256",
                                     "source_requested_manifest_sha256",
                                     "writer_generation", "writer_role"})) {
            return invalid("authority.payload_fields", "plan payload fields are not exact");
        }
        const auto &resolved = payload.at("resolved_plan");
        if (!resolved.is_object() || !exact_fields(resolved, {"manifest", "provider_construction_order", "requested_manifest_sha256",
                                                               "resolved_manifest_sha256", "resolver_contract_version", "schema_version",
                                                               "system_registration_order"}) ||
            resolved.at("schema_version") != "echelon_forge.resolved_simulation_composition.v1" ||
            !resolved.at("resolver_contract_version").is_string() || resolved.at("resolver_contract_version").get<std::string>() != "echelon_forge.simulation_composition_resolver.v1" ||
            !resolved.at("manifest").is_object() || !resolved.at("provider_construction_order").is_array() ||
            !resolved.at("system_registration_order").is_array() ||
            !sha256_string(resolved.at("requested_manifest_sha256")) ||
            !sha256_string(resolved.at("resolved_manifest_sha256")) ||
            !sha256_string(payload.at("source_artifact_sha256")) ||
            !sha256_string(payload.at("source_requested_manifest_sha256")) ||
            !sha256_string(payload.at("source_request_manifest_binding_sha256")) ||
            payload.at("adapter_role") != "legacy_resolved_manifest_reader" ||
            !identifier_string(payload.at("plan_id")) || !sha256_string(payload.at("request_sha256")) ||
            payload.at("source_artifact_schema_version") != "echelon_forge.resolved_simulation_composition.v1" ||
            !generation_window(payload, "reader_generation_min", "reader_generation_max")) {
            return invalid("authority.payload_type", "resolved plan nested schema is not admitted");
        }
        if (!runtime::composition::parse_resolved_composition_json(resolved.dump())) {
            return invalid("authority.payload_type", "native resolved-plan parser rejected legacy source");
        }
        if (payload.at("source_requested_manifest_sha256") != resolved.at("requested_manifest_sha256")) {
            return invalid("authority.payload_binding", "source requested-manifest digest differs from nested plan");
        }
        std::string binding_input = payload.at("request_sha256").get<std::string>();
        binding_input.push_back('\0');
        binding_input += payload.at("source_requested_manifest_sha256").get<std::string>();
        if (sha256_hex(binding_input) != payload.at("source_request_manifest_binding_sha256").get<std::string>()) {
            return invalid("authority.payload_binding", "source request/manifest provenance binding differs");
        }
        auto resolved_body = resolved;
        resolved_body.erase("resolved_manifest_sha256");
        if (sha256_hex(resolved_body.dump()) != resolved.at("resolved_manifest_sha256").get<std::string>() ||
            sha256_hex(resolved.dump()) != payload.at("source_artifact_sha256").get<std::string>()) {
            return invalid("authority.payload_digest", "resolved plan legacy digest does not match source bytes");
        }
    }
    if (kind == "rollout_decision") {
        if (!exact_fields(payload, {"authority_kind", "checkpoint_id", "cohort", "contract_version", "decision_id",
                                    "decision_sequence", "irreversible_write_boundary", "manifest_sha256", "plan_sha256",
                                    "plan_reader_generation_min", "plan_reader_generation_max", "predecessor_decision_id",
                                    "release_id", "rollback_deadline", "schema_version", "state", "writer_generation", "writer_role"})) {
            return invalid("authority.payload_fields", "rollout payload fields are not exact");
        }
        if (payload.at("authority_kind") != "rollout_decision" ||
            payload.at("schema_version") != "echelon_forge.rollout_decision.v1" ||
            payload.at("contract_version") != "echelon_forge.rollout_decision_contract.v1" ||
            payload.at("writer_role") != "release_controller" ||
            !identifier_string(payload.at("decision_id")) || !identifier_string(payload.at("release_id")) ||
            !nonempty_string(payload.at("cohort")) || !nonempty_string(payload.at("rollback_deadline")) ||
            !nonempty_string(payload.at("irreversible_write_boundary")) ||
            (!identifier_string(payload.at("predecessor_decision_id"), true)) ||
            (!identifier_string(payload.at("checkpoint_id"), true)) ||
            !generation_window(payload, "plan_reader_generation_min", "plan_reader_generation_max") ||
            !generation_string(payload.at("decision_sequence")) || !payload.at("state").is_string() ||
            std::set<std::string>{"prepared", "shadow", "canary-ready", "production-canary", "adoption-expanding", "rollback-window", "stable", "backed-out"}.count(payload.at("state").get<std::string>()) == 0 ||
            !sha256_string(payload.at("manifest_sha256")) || !sha256_string(payload.at("plan_sha256")) ||
            !payload.at("decision_sequence").is_string()) {
            return invalid("authority.payload_type", "rollout state/hash/generation is not typed");
        }
    }
    if (kind == "state_checkpoint") {
        if (!exact_fields(payload, {"aggregate_state_sha256", "authority_kind", "checkpoint_id", "contract_version", "decision_id",
                                    "host_boot_id", "incarnation_epoch", "plan_sha256", "release_id", "run_id", "schema_version",
                                    "state_schema_generation", "target_reader_generation_min", "target_reader_generation_max",
                                    "transfer_fence_sequence", "world_fragments", "writer_generation", "writer_role"})) {
            return invalid("authority.payload_fields", "checkpoint payload fields are not exact");
        }
        if (payload.at("authority_kind") != "state_checkpoint" ||
            payload.at("schema_version") != "echelon_forge.state_checkpoint.v1" ||
            payload.at("contract_version") != "echelon_forge.state_checkpoint_contract.v1" ||
            payload.at("writer_role") != "runtime_host" ||
            !identifier_string(payload.at("checkpoint_id")) || !identifier_string(payload.at("release_id")) ||
            !identifier_string(payload.at("decision_id")) || !identifier_string(payload.at("run_id")) ||
            !identifier_string(payload.at("host_boot_id")) ||
            !generation_string(payload.at("incarnation_epoch")) || !generation_string(payload.at("transfer_fence_sequence")) ||
            !generation_string(payload.at("state_schema_generation")) ||
            !generation_window(payload, "target_reader_generation_min", "target_reader_generation_max") ||
            !sha256_string(payload.at("plan_sha256")) || !sha256_string(payload.at("aggregate_state_sha256")) ||
            !payload.at("world_fragments").is_array() || payload.at("world_fragments").empty()) {
            return invalid("authority.payload_type", "checkpoint hash/fragments are not typed");
        }
        std::set<std::string> world_ids;
        for (const auto &fragment : payload.at("world_fragments")) {
            if (!exact_fields(fragment, {"episode_ids", "fragment_sequence", "state_sha256", "world_id"}) ||
                !identifier_string(fragment.at("world_id")) || !sorted_unique_strings(fragment.at("episode_ids"), true) ||
                !generation_string(fragment.at("fragment_sequence")) || !sha256_string(fragment.at("state_sha256")) ||
                !world_ids.insert(fragment.at("world_id").get<std::string>()).second) {
                return invalid("authority.payload_type", "checkpoint fragment coverage is not unique/typed");
            }
        }
        std::string previous_sequence;
        bool first_sequence = true;
        for (const auto &fragment : payload.at("world_fragments")) {
            const auto &sequence = fragment.at("fragment_sequence").get_ref<const std::string &>();
            if (!first_sequence && (sequence.size() < previous_sequence.size() ||
                                    (sequence.size() == previous_sequence.size() && sequence <= previous_sequence))) {
                return invalid("authority.payload_type", "checkpoint fragments are not ordered and unique");
            }
            previous_sequence = sequence;
            first_sequence = false;
        }
    }
    if (kind == "resolved_composition_plan" &&
        !exact_fields(payload, {"adapter_role", "authority_kind", "contract_version", "plan_id", "reader_generation_max",
                                 "reader_generation_min", "request_sha256", "resolved_plan", "schema_version",
                                 "source_artifact_schema_version", "source_artifact_sha256", "source_request_manifest_binding_sha256",
                                 "source_requested_manifest_sha256",
                                 "writer_generation", "writer_role"})) {
        return invalid("authority.payload_fields", "plan payload fields are not exact");
    }
    if (kind == "rollout_decision" &&
        !exact_fields(payload, {"authority_kind", "checkpoint_id", "cohort", "contract_version", "decision_id",
                                "decision_sequence", "irreversible_write_boundary", "manifest_sha256", "plan_sha256",
                                "plan_reader_generation_min", "plan_reader_generation_max", "predecessor_decision_id",
                                "release_id", "rollback_deadline", "schema_version", "state", "writer_generation", "writer_role"})) {
        return invalid("authority.payload_fields", "rollout payload fields are not exact");
    }
    if (kind == "state_checkpoint" &&
        !exact_fields(payload, {"aggregate_state_sha256", "authority_kind", "checkpoint_id", "contract_version", "decision_id",
                                "host_boot_id", "incarnation_epoch", "plan_sha256", "release_id", "run_id", "schema_version",
                                "state_schema_generation", "target_reader_generation_min", "target_reader_generation_max",
                                "transfer_fence_sequence", "world_fragments", "writer_generation", "writer_role"})) {
        return invalid("authority.payload_fields", "checkpoint payload fields are not exact");
    }
    const auto expected = authority_digest_sha256_hex(
        envelope.at("domain").get<std::string>(), envelope.at("media_type").get<std::string>(),
        canonical_payload_bytes);
    if (!envelope.at("payload_sha256").is_string() ||
        envelope.at("payload_sha256").get<std::string>() != expected) {
        return invalid("authority.digest", "detached digest mismatch");
    }
    return ValidationResult{true, {}, {}};
}

} // namespace runtime::authority_contracts
