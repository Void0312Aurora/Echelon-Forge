#include "runtime/contracts/runtime_composition_projection_contract.h"

#include <nlohmann/json.hpp>

#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <initializer_list>
#include <limits>
#include <regex>
#include <sstream>
#include <string>
#include <string_view>
#include <tuple>
#include <set>
#include <utility>
#include <vector>

namespace runtime::projection_contracts {
namespace {

using Json = nlohmann::json;

constexpr std::array<std::string_view, 6> kCategories = {
    kCategoryModel,  kCategorySystem,   kCategoryBackend,
    kCategoryDomain, kCategoryEvidence, kCategorySecurity,
};

void add_issue(ProjectionValidationResult &result, std::string_view code, std::string path,
               std::string detail);

[[nodiscard]] bool is_ascii(std::string_view value) noexcept {
    return std::all_of(value.begin(), value.end(), [](char character) {
        return static_cast<unsigned char>(character) < 0x80U;
    });
}

[[nodiscard]] bool is_hex64(std::string_view value) noexcept {
    if (value.size() != 64U) {
        return false;
    }
    return std::all_of(value.begin(), value.end(), [](char character) {
        return (character >= '0' && character <= '9') || (character >= 'a' && character <= 'f');
    });
}

[[nodiscard]] bool is_identifier(std::string_view value) {
    static const std::regex pattern(R"(^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$)");
    return std::regex_match(value.begin(), value.end(), pattern);
}

[[nodiscard]] bool is_version(std::string_view value) {
    static const std::regex pattern(R"(^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$)");
    return std::regex_match(value.begin(), value.end(), pattern);
}

[[nodiscard]] bool string_field(const Json &object, const char *field, std::string_view path,
                                ProjectionValidationResult &result, bool identifier = false,
                                bool version = false) {
    if (!object.contains(field) || !object.at(field).is_string()) {
        add_issue(result, "projection.invalid_json_type", std::string(path) + "." + field,
                  "expected string");
        return false;
    }
    const auto value = object.at(field).get<std::string>();
    if (value.empty() || !is_ascii(value) || (identifier && !is_identifier(value)) ||
        (version && !is_version(value))) {
        add_issue(result,
                  identifier ? "projection.invalid_identifier"
                  : version  ? "projection.invalid_version"
                             : "projection.invalid_string_value",
                  std::string(path) + "." + field, "invalid string value");
        return false;
    }
    return true;
}

[[nodiscard]] bool string_array(const Json &object, const char *field, std::string_view path,
                                ProjectionValidationResult &result) {
    if (!object.contains(field) || !object.at(field).is_array()) {
        add_issue(result, "projection.invalid_json_type", std::string(path) + "." + field,
                  "expected string array");
        return false;
    }
    std::set<std::string> seen;
    bool valid = true;
    const auto &values = object.at(field);
    for (std::size_t index = 0U; index < values.size(); ++index) {
        const auto item_path = std::string(path) + "." + field + "[" + std::to_string(index) + "]";
        if (!values[index].is_string()) {
            add_issue(result, "projection.invalid_json_type", item_path, "expected string");
            valid = false;
            continue;
        }
        const auto value = values[index].get<std::string>();
        if (value.empty() || !is_ascii(value)) {
            add_issue(result, "projection.invalid_string_value", item_path,
                      "expected non-empty ASCII NFC string");
            valid = false;
        }
        if (!seen.insert(value).second) {
            add_issue(result, "projection.duplicate_value", std::string(path) + "." + field,
                      "values must be unique");
            valid = false;
        }
    }
    return valid;
}

void add_issue(ProjectionValidationResult &result, std::string_view code, std::string path,
               std::string detail) {
    result.issues.push_back({std::string(code), std::move(path), std::move(detail)});
}

[[nodiscard]] bool exact_object(const Json &value, std::string_view path,
                                std::initializer_list<std::string_view> fields,
                                ProjectionValidationResult &result) {
    if (!value.is_object()) {
        add_issue(result, "projection.invalid_json_type", std::string(path), "expected object");
        return false;
    }
    std::vector<std::string> expected;
    bool valid = true;
    expected.reserve(fields.size());
    for (const auto field : fields) {
        expected.emplace_back(field);
    }
    for (const auto &[key, _] : value.items()) {
        if (std::find(expected.begin(), expected.end(), key) == expected.end()) {
            add_issue(result, "projection.unexpected_field", std::string(path) + "." + key,
                      "field is not in v1 contract");
            valid = false;
        }
    }
    for (const auto &field : expected) {
        if (!value.contains(field)) {
            add_issue(result, "projection.missing_field", std::string(path) + "." + field,
                      "required field is missing");
            valid = false;
        }
    }
    return valid;
}

[[nodiscard]] bool canonical_value(const Json &value, std::string_view path,
                                   ProjectionValidationResult &result, std::size_t depth = 0U) {
    if (depth > 64U) {
        add_issue(result, "projection.configuration_depth_exceeded", std::string(path),
                  "maximum depth is 64");
        return false;
    }
    if (value.is_string()) {
        if (!is_ascii(value.get_ref<const std::string &>())) {
            add_issue(result, "projection.invalid_string_value", std::string(path),
                      "configuration strings must be ASCII");
            return false;
        }
        return true;
    }
    if (value.is_number_float()) {
        add_issue(result, "projection.noncanonical_configuration", std::string(path),
                  "floating-point values are forbidden");
        return false;
    }
    if (value.is_number_unsigned() &&
        value.get<std::uint64_t>() >
            static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max())) {
        add_issue(result, "projection.noncanonical_configuration", std::string(path),
                  "integer outside signed 64-bit range");
        return false;
    }
    if (value.is_array()) {
        bool valid = true;
        for (std::size_t index = 0U; index < value.size(); ++index) {
            valid =
                canonical_value(value[index], std::string(path) + "[" + std::to_string(index) + "]",
                                result, depth + 1U) &&
                valid;
        }
        return valid;
    }
    if (value.is_object()) {
        bool valid = true;
        for (const auto &[key, nested] : value.items()) {
            if (!is_ascii(key)) {
                add_issue(result, "projection.invalid_string_value", std::string(path) + "." + key,
                          "configuration keys must be ASCII");
                valid = false;
            }
            valid =
                canonical_value(nested, std::string(path) + "." + key, result, depth + 1U) && valid;
        }
        return valid;
    }
    return true;
}

[[nodiscard]] std::string sha256_hex(std::string_view input) {
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
    std::array<std::uint32_t, 8> state = {
        0x6a09e667U, 0xbb67ae85U, 0x3c6ef372U, 0xa54ff53aU,
        0x510e527fU, 0x9b05688cU, 0x1f83d9abU, 0x5be0cd19U,
    };
    const auto choose = [](std::uint32_t x, std::uint32_t y, std::uint32_t z) {
        return (x & y) ^ (~x & z);
    };
    const auto majority = [](std::uint32_t x, std::uint32_t y, std::uint32_t z) {
        return (x & y) ^ (x & z) ^ (y & z);
    };
    std::vector<std::uint8_t> bytes(input.begin(), input.end());
    const std::uint64_t bit_length = static_cast<std::uint64_t>(bytes.size()) * 8U;
    bytes.push_back(0x80U);
    while ((bytes.size() % 64U) != 56U) {
        bytes.push_back(0U);
    }
    for (int shift = 56; shift >= 0; shift -= 8) {
        bytes.push_back(static_cast<std::uint8_t>((bit_length >> shift) & 0xffU));
    }
    for (std::size_t offset = 0U; offset < bytes.size(); offset += 64U) {
        std::array<std::uint32_t, 64> words{};
        for (std::size_t index = 0U; index < 16U; ++index) {
            const auto base = offset + index * 4U;
            words[index] = (static_cast<std::uint32_t>(bytes[base]) << 24U) |
                           (static_cast<std::uint32_t>(bytes[base + 1U]) << 16U) |
                           (static_cast<std::uint32_t>(bytes[base + 2U]) << 8U) |
                           static_cast<std::uint32_t>(bytes[base + 3U]);
        }
        for (std::size_t index = 16U; index < words.size(); ++index) {
            const auto sigma0 = std::rotr(words[index - 15U], 7) ^
                                std::rotr(words[index - 15U], 18) ^ (words[index - 15U] >> 3U);
            const auto sigma1 = std::rotr(words[index - 2U], 17) ^
                                std::rotr(words[index - 2U], 19) ^ (words[index - 2U] >> 10U);
            words[index] = words[index - 16U] + sigma0 + words[index - 7U] + sigma1;
        }
        auto [a, b, c, d, e, f, g, h] = state;
        for (std::size_t index = 0U; index < words.size(); ++index) {
            const auto sum1 = std::rotr(e, 6) ^ std::rotr(e, 11) ^ std::rotr(e, 25);
            const auto temp1 = h + sum1 + choose(e, f, g) + constants[index] + words[index];
            const auto sum0 = std::rotr(a, 2) ^ std::rotr(a, 13) ^ std::rotr(a, 22);
            const auto temp2 = sum0 + majority(a, b, c);
            h = g;
            g = f;
            f = e;
            e = d + temp1;
            d = c;
            c = b;
            b = a;
            a = temp1 + temp2;
        }
        state[0] += a;
        state[1] += b;
        state[2] += c;
        state[3] += d;
        state[4] += e;
        state[5] += f;
        state[6] += g;
        state[7] += h;
    }
    std::ostringstream stream;
    stream << std::hex << std::setfill('0');
    for (const auto word : state) {
        stream << std::setw(8) << word;
    }
    return stream.str();
}

[[nodiscard]] std::string canonical_request(Json request) {
    auto sort_array = [&request](const char *field) {
        auto &values = request[field];
        std::sort(values.begin(), values.end(), [](const Json &left, const Json &right) {
            return left.get<std::string>() < right.get<std::string>();
        });
    };
    sort_array("required_capabilities");
    sort_array("required_policies");
    return request.dump();
}

[[nodiscard]] std::string canonical_authority(Json registry) {
    registry.erase("canonical_json");
    registry.erase("registry_sha256");
    return registry.dump();
}

void validate_request_value(const Json &request, ProjectionValidationResult &result) {
    if (request.at("schema_version") != "echelon_forge.runtime_composition_request.v1") {
        add_issue(result, "projection.unsupported_schema_version", "$.schema_version",
                  "request schema version mismatch");
    }
    string_field(request, "request_id", "$", result, true);
    string_field(request, "request_version", "$", result, false, true);
    if (request.contains("contract_versions") &&
        exact_object(request.at("contract_versions"), "$.contract_versions",
                     {"composition", "runtime", "content", "stage"}, result)) {
        for (const auto field : {"composition", "runtime", "content", "stage"}) {
            string_field(request.at("contract_versions"), field, "$.contract_versions", result,
                         false, true);
        }
    }
    if (request.contains("intent") &&
        exact_object(request.at("intent"), "$.intent",
                     {"simulation_id", "policy_id", "evaluation_id"}, result)) {
        for (const auto field : {"simulation_id", "policy_id", "evaluation_id"}) {
            string_field(request.at("intent"), field, "$.intent", result, true);
        }
    }
    if (request.contains("requested_profile") &&
        exact_object(request.at("requested_profile"), "$.requested_profile",
                     {"profile_id", "profile_version"}, result)) {
        string_field(request.at("requested_profile"), "profile_id", "$.requested_profile", result,
                     true);
        string_field(request.at("requested_profile"), "profile_version", "$.requested_profile",
                     result, false, true);
    }
    string_array(request, "required_capabilities", "$", result);
    string_array(request, "required_policies", "$", result);
}

[[nodiscard]] std::string expected_owner(std::string_view category) {
    if (category == kCategoryModel) return "owner.model";
    if (category == kCategorySystem) return "owner.scheduler";
    if (category == kCategoryBackend) return "owner.backend";
    if (category == kCategoryDomain) return "owner.domain";
    if (category == kCategoryEvidence) return "owner.evidence";
    if (category == kCategorySecurity) return "owner.security";
    return {};
}

void validate_authority_value(const Json &authority, ProjectionValidationResult &result) {
    string_field(authority, "registry_id", "$", result, true);
    string_field(authority, "registry_version", "$", result, false, true);
    if (authority.at("registry_id") != std::string(kOwnerAuthorityRegistryId) ||
        authority.at("registry_version") != "1.0.0") {
        add_issue(result, "projection.authority_registry_mismatch", "$",
                  "authority identity mismatch");
    }
    if (!authority.at("categories").is_array() ||
        authority.at("categories").size() != kCategories.size()) {
        add_issue(result, "projection.invalid_authority", "$.categories",
                  "authority must list every category exactly once");
        return;
    }
    for (std::size_t index = 0U; index < kCategories.size(); ++index) {
        const auto path = "$.categories[" + std::to_string(index) + "]";
        const auto &row = authority.at("categories")[index];
        if (!exact_object(row, path, {"category", "owner_id"}, result)) {
            continue;
        }
        if (!row.at("category").is_string() || !row.at("owner_id").is_string() ||
            row.at("category") != std::string(kCategories[index]) ||
            row.at("owner_id") != expected_owner(kCategories[index])) {
            add_issue(result, "projection.invalid_authority", path,
                      "category owner does not match repository authority");
        }
    }
}

[[nodiscard]] std::string canonical_lock(Json lock) {
    lock.erase("canonical_json");
    lock.erase("lock_sha256");
    auto &authorities = lock["category_authorities"];
    std::sort(authorities.begin(), authorities.end(), [](const Json &left, const Json &right) {
        return left.at("category").get<std::string>() < right.at("category").get<std::string>();
    });
    auto &entries = lock["entries"];
    for (auto &entry : entries) {
        auto &capabilities = entry["capabilities"];
        std::sort(capabilities.begin(), capabilities.end(),
                  [](const Json &left, const Json &right) {
                      return left.get<std::string>() < right.get<std::string>();
                  });
    }
    std::sort(entries.begin(), entries.end(), [](const Json &left, const Json &right) {
        return std::tie(left.at("category").get_ref<const std::string &>(),
                        left.at("descriptor_id").get_ref<const std::string &>()) <
               std::tie(right.at("category").get_ref<const std::string &>(),
                        right.at("descriptor_id").get_ref<const std::string &>());
    });
    return lock.dump();
}

} // namespace

std::string canonical_sha256_hex(std::string_view canonical_bytes) {
    return sha256_hex(canonical_bytes);
}

ProjectionValidationResult
validate_runtime_composition_projection_json(std::string_view request_json,
                                             std::string_view lock_json,
                                             std::string_view authority_registry_json) {
    ProjectionValidationResult result;
    Json request;
    Json lock;
    Json authority;
    try {
        request = Json::parse(request_json.begin(), request_json.end());
        lock = Json::parse(lock_json.begin(), lock_json.end());
        authority = Json::parse(authority_registry_json.begin(), authority_registry_json.end());
    } catch (const Json::exception &error) {
        add_issue(result, "projection.input_error", "$", error.what());
        return result;
    }
    try {
        if (!exact_object(request, "$",
                          {"schema_version", "request_id", "request_version", "contract_versions",
                           "intent", "requested_profile", "required_capabilities",
                           "required_policies", "configuration"},
                          result)) {
            return result;
        }
        if (!exact_object(lock, "$",
                          {"schema_version", "contract_version", "lock_id", "lock_version",
                           "request_schema_version", "request_sha256", "authority_registry_sha256",
                           "category_authorities", "entries", "canonicalization", "hash_algorithm",
                           "canonical_json", "lock_sha256"},
                          result)) {
            return result;
        }
        if (!exact_object(authority, "$",
                          {"schema_version", "registry_id", "registry_version", "categories",
                           "canonicalization", "hash_algorithm", "canonical_json",
                           "registry_sha256"},
                          result)) {
            return result;
        }
        validate_request_value(request, result);
        validate_authority_value(authority, result);
        string_field(lock, "lock_id", "$", result, true);
        string_field(lock, "lock_version", "$", result, false, true);
        if (!lock.at("contract_version").is_string() ||
            lock.at("contract_version") != std::string(kAdmittedCatalogLockContractVersion)) {
            add_issue(result, "projection.unsupported_contract_version", "$.contract_version",
                      "catalog-lock contract version mismatch");
        }
        if (request.at("schema_version") != "echelon_forge.runtime_composition_request.v1" ||
            lock.at("schema_version") != std::string(kAdmittedCatalogLockSchemaVersion) ||
            authority.at("schema_version") != std::string(kOwnerAuthorityRegistrySchemaVersion) ||
            lock.at("request_schema_version") != "echelon_forge.runtime_composition_request.v1") {
            add_issue(result, "projection.unsupported_schema_version", "$.schema_version",
                      "schema version mismatch");
        }
        if (authority.at("registry_id") != std::string(kOwnerAuthorityRegistryId) ||
            authority.at("canonicalization") != std::string(kCanonicalizationId) ||
            authority.at("hash_algorithm") != std::string(kHashAlgorithm) ||
            lock.at("canonicalization") != std::string(kCanonicalizationId) ||
            lock.at("hash_algorithm") != std::string(kHashAlgorithm)) {
            add_issue(result, "projection.invalid_identity", "$.canonicalization",
                      "identity algorithm or registry id mismatch");
        }
        if (!canonical_value(request.at("configuration"), "$.configuration", result)) {
            // Issues are already recorded; continue so cross-binding diagnostics remain visible.
        }
        const auto request_hash = sha256_hex(canonical_request(request));
        const auto authority_hash = sha256_hex(canonical_authority(authority));
        if (!authority.at("canonical_json").is_string() ||
            authority.at("canonical_json").get<std::string>() != canonical_authority(authority)) {
            add_issue(result, "projection.canonical_bytes_mismatch", "$.canonical_json",
                      "authority canonical bytes mismatch");
        }
        if (!authority.at("registry_sha256").is_string() ||
            authority.at("registry_sha256").get<std::string>() != authority_hash) {
            add_issue(result, "projection.identity_mismatch", "$.registry_sha256",
                      "authority identity mismatch");
        }
        if (!lock.at("request_sha256").is_string() ||
            lock.at("request_sha256").get<std::string>() != request_hash) {
            add_issue(result, "projection.request_identity_mismatch", "$.request_sha256",
                      "does not match request");
        }
        if (!lock.at("authority_registry_sha256").is_string() ||
            lock.at("authority_registry_sha256").get<std::string>() != authority_hash) {
            add_issue(result, "projection.authority_registry_mismatch",
                      "$.authority_registry_sha256", "does not match authority registry");
        }
        if (!lock.at("canonical_json").is_string() ||
            lock.at("canonical_json").get<std::string>() != canonical_lock(lock)) {
            add_issue(result, "projection.canonical_bytes_mismatch", "$.canonical_json",
                      "lock canonical bytes mismatch");
        }
        const auto lock_hash = sha256_hex(canonical_lock(lock));
        if (!lock.at("lock_sha256").is_string() ||
            lock.at("lock_sha256").get<std::string>() != lock_hash) {
            add_issue(result, "projection.identity_mismatch", "$.lock_sha256",
                      "lock identity mismatch");
        }
        if (!lock.at("category_authorities").is_array() || !lock.at("entries").is_array()) {
            add_issue(result, "projection.invalid_json_type", "$.entries", "expected arrays");
            result.valid = result.issues.empty();
            return result;
        }
        std::set<std::string> categories;
        std::set<std::string> authority_rows;
        std::set<std::string> entry_categories;
        std::set<std::string> entry_ids;
        std::set<std::string> capabilities;
        for (const auto &authority_row : lock.at("category_authorities")) {
            if (!exact_object(authority_row, "$.category_authorities", {"category", "owner_id"},
                              result) ||
                !authority_row.at("category").is_string() ||
                !authority_row.at("owner_id").is_string()) {
                add_issue(result, "projection.invalid_authority", "$.category_authorities",
                          "invalid authority row");
                continue;
            }
            const auto category = authority_row.at("category").get<std::string>();
            const auto owner = authority_row.at("owner_id").get<std::string>();
            if (expected_owner(category).empty() || owner != expected_owner(category)) {
                add_issue(result, "projection.owner_authority_mismatch", "$.category_authorities",
                          "owner does not match repository authority");
            }
            if (!authority_rows.insert(category).second) {
                add_issue(result, "projection.duplicate_value", "$.category_authorities",
                          "category has two owners");
            }
            categories.insert(category);
        }
        for (const auto category : kCategories) {
            if (!categories.contains(std::string(category))) {
                add_issue(result, "projection.missing_category", "$.category_authorities",
                          "authority category is missing");
            }
        }
        for (const auto &entry : lock.at("entries")) {
            if (!exact_object(entry, "$.entries",
                              {"category", "owner_id", "descriptor_id", "implementation_id",
                               "implementation_version", "capabilities", "provenance",
                               "trust_decision"},
                              result)) {
                add_issue(result, "projection.invalid_entry", "$.entries", "invalid entry shape");
                continue;
            }
            if (!entry.at("category").is_string() || !entry.at("owner_id").is_string() ||
                !entry.at("descriptor_id").is_string() ||
                !entry.at("implementation_id").is_string() ||
                !entry.at("implementation_version").is_string() ||
                !entry.at("trust_decision").is_string()) {
                add_issue(result, "projection.invalid_entry", "$.entries",
                          "entry scalar field has wrong type");
                continue;
            }
            const auto category = entry.at("category").get<std::string>();
            entry_categories.insert(category);
            const auto owner = entry.at("owner_id").get<std::string>();
            if (expected_owner(category).empty()) {
                add_issue(result, "projection.unknown_category", "$.entries.category",
                          "category is not admitted in v1");
            }
            if (expected_owner(category).empty() || owner != expected_owner(category) ||
                !is_identifier(owner) ||
                !is_identifier(entry.at("descriptor_id").get<std::string>()) ||
                !is_identifier(entry.at("implementation_id").get<std::string>()) ||
                !is_version(entry.at("implementation_version").get<std::string>())) {
                add_issue(result, "projection.owner_mismatch", "$.entries",
                          "entry owner does not match authority");
            }
            if (entry.at("trust_decision") != "admitted") {
                add_issue(result, "projection.unadmitted_implementation",
                          "$.entries.trust_decision", "only admitted entries may be locked");
            }
            const auto entry_key = category + "\x1f" + entry.at("descriptor_id").get<std::string>();
            if (!entry_ids.insert(entry_key).second) {
                add_issue(result, "projection.duplicate_entry", "$.entries",
                          "descriptor is repeated");
            }
            if (entry.at("capabilities").is_array()) {
                std::set<std::string> row_capabilities;
                for (const auto &capability : entry.at("capabilities")) {
                    if (!capability.is_string() || capability.get<std::string>().empty() ||
                        !is_ascii(capability.get<std::string>()) ||
                        !row_capabilities.insert(capability.get<std::string>()).second) {
                        add_issue(result, "projection.invalid_string_value",
                                  "$.entries.capabilities",
                                  "capabilities must be unique non-empty ASCII strings");
                    } else {
                        capabilities.insert(capability.get<std::string>());
                    }
                }
            } else {
                add_issue(result, "projection.invalid_json_type", "$.entries.capabilities",
                          "expected string array");
            }
            const auto &provenance = entry.at("provenance");
            if (!exact_object(provenance, "$.entries.provenance",
                              {"artifact_kind", "artifact_identity", "artifact_sha256"}, result) ||
                !provenance.at("artifact_kind").is_string() ||
                !provenance.at("artifact_identity").is_string()) {
                add_issue(result, "projection.invalid_provenance", "$.entries.provenance",
                          "invalid provenance shape");
            } else {
                const auto kind = provenance.at("artifact_kind").get<std::string>();
                const auto identity = provenance.at("artifact_identity").get<std::string>();
                const auto &digest = provenance.at("artifact_sha256");
                if (kind != "repository_builtin" && kind != "native_package" &&
                    kind != "cordis_package") {
                    add_issue(result, "projection.invalid_provenance",
                              "$.entries.provenance.artifact_kind", "unknown artifact kind");
                }
                if (identity.empty() || !is_ascii(identity)) {
                    add_issue(result, "projection.invalid_provenance",
                              "$.entries.provenance.artifact_identity",
                              "invalid artifact identity");
                }
                if (!digest.is_null() &&
                    (!digest.is_string() || !is_hex64(digest.get<std::string>()))) {
                    add_issue(result, "projection.invalid_provenance",
                              "$.entries.provenance.artifact_sha256", "expected SHA-256 or null");
                }
                if ((kind == "native_package" || kind == "cordis_package") &&
                    (!digest.is_string() || !is_hex64(digest.get<std::string>()))) {
                    add_issue(result, "projection.provenance_hash_required",
                              "$.entries.provenance.artifact_sha256",
                              "package provenance must carry a SHA-256");
                }
            }
        }
        for (const auto category : kCategories) {
            if (!entry_categories.contains(std::string(category))) {
                add_issue(result, "projection.missing_category", "$.entries",
                          "request-bound lock must admit every category");
            }
        }
        if (request.at("required_capabilities").is_array()) {
            for (const auto &required : request.at("required_capabilities")) {
                if (required.is_string() && !capabilities.contains(required.get<std::string>())) {
                    add_issue(result, "projection.unmet_capability", "$.entries",
                              "required capability is not covered");
                }
            }
        }
        result.valid = result.issues.empty();
        return result;
    } catch (const Json::exception &error) {
        add_issue(result, "projection.input_error", "$", error.what());
    } catch (const std::exception &error) {
        add_issue(result, "projection.input_error", "$", error.what());
    }
    result.valid = false;
    return result;
}

} // namespace runtime::projection_contracts
