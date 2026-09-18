#pragma once

#include <string>
#include <string_view>
#include <optional>

namespace runtime::authority_contracts {

struct ValidationResult {
    bool valid = false;
    std::string code;
    std::string detail;
};

inline constexpr std::string_view kCanonicalization = "echelon_forge.canonical_json.v2";
inline constexpr std::string_view kEnvelopeVersion = "echelon_forge.authority_envelope.v1";

[[nodiscard]] std::string authority_digest_sha256_hex(std::string_view domain,
                                                      std::string_view media_type,
                                                      std::string_view payload_bytes);

// Native consumes canonical bytes produced by the shared schema/vector owner;
// it never reserializes an admitted payload or creates a second authority.
[[nodiscard]] ValidationResult
validate_authority_envelope_json(std::string_view envelope_json,
                                 std::string_view canonical_payload_bytes);

// Validate the P5-A closed execution-plan wrapper.  The wrapper is a derived
// admission artifact: its embedded authority envelope remains the sole plan
// authority, while input bindings prevent a consumer from silently joining a
// different request, lock, projection, backend, or manifest.
[[nodiscard]] ValidationResult validate_resolved_execution_plan_json(std::string_view plan_json);

[[nodiscard]] std::string resolved_execution_plan_sha256_hex(std::string_view canonical_payload_bytes);

[[nodiscard]] std::optional<std::string>
resolved_manifest_from_execution_plan_json(std::string_view plan_json);

} // namespace runtime::authority_contracts
