#pragma once

#include <string>
#include <string_view>

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

} // namespace runtime::authority_contracts
