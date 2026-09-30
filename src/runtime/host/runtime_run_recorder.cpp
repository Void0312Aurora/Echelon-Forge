#include "runtime_run_recorder.h"

#include "runtime/contracts/authority/runtime_authority_contract.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <chrono>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <initializer_list>
#include <map>
#include <optional>
#include <random>
#include <set>
#include <sstream>
#include <string>
#include <string_view>

#include <nlohmann/json.hpp>

#if defined(_WIN32)
#define NOMINMAX
#include <Windows.h>
#include <TlHelp32.h>
#elif defined(__linux__)
#include <unistd.h>
#endif

namespace runtime::host {
namespace {

using Json = nlohmann::json;

std::string native_build_mode() {
#if defined(NDEBUG)
    return "Release";
#else
    return "Debug";
#endif
}

bool native_compiler_facts_match(const RuntimeExecutionOwnerFacts &facts) {
    if (facts.build_mode != native_build_mode()) return false;
#if defined(_MSC_VER)
    return facts.linker == "link.exe" && facts.cxx_abi == "msvc-native";
#else
    return true;
#endif
}

RuntimeRunRecorderStatus failure(std::string code, std::string detail) {
    return RuntimeRunRecorderStatus{false, std::move(code), std::move(detail)};
}

bool exact_run_id(std::string_view expected, const Json &value) {
    const Json *candidate = &value;
    if (value.is_object() && value.contains("payload")) candidate = &value.at("payload");
    return candidate->is_object() && candidate->contains("run_id") &&
           candidate->at("run_id").is_string() &&
           candidate->at("run_id").get<std::string>() == expected;
}

bool sha256_string(const Json &value) {
    if (!value.is_string() || value.get<std::string>().size() != 64U) return false;
    for (const char character : value.get<std::string>()) {
        if (!((character >= '0' && character <= '9') || (character >= 'a' && character <= 'f')))
            return false;
    }
    return true;
}

bool nonempty_string(const Json &value) {
    return value.is_string() && !value.get_ref<const std::string &>().empty();
}

bool identifier_string(const Json &value) {
    if (!value.is_string()) return false;
    const auto &text = value.get_ref<const std::string &>();
    const auto ascii_alpha = [](const char character) {
        return (character >= 'A' && character <= 'Z') || (character >= 'a' && character <= 'z');
    };
    const auto ascii_alnum = [ascii_alpha](const char character) {
        return ascii_alpha(character) || (character >= '0' && character <= '9');
    };
    if (text.empty() || text.size() > 128U || !ascii_alpha(text.front())) {
        return false;
    }
    return std::all_of(text.begin() + 1, text.end(), [ascii_alnum](const char character) {
        return ascii_alnum(character) || character == '.' || character == '_' || character == ':' ||
               character == '-';
    });
}

bool safe_unsigned(const Json &value) {
    return value.is_number_unsigned() && value.get<std::uint64_t>() <= 9007199254740991ULL;
}

bool safe_size(const Json &value) {
    return safe_unsigned(value);
}

bool generation_string(const Json &value) {
    if (!value.is_string()) return false;
    const auto &text = value.get_ref<const std::string &>();
    if (text.empty() || (text.size() > 1U && text.front() == '0')) return false;
    return std::all_of(text.begin(), text.end(),
                       [](const char character) { return character >= '0' && character <= '9'; });
}

bool generation_less_equal(const Json &left, const Json &right) {
    if (!generation_string(left) || !generation_string(right)) return false;
    const auto &lhs = left.get_ref<const std::string &>();
    const auto &rhs = right.get_ref<const std::string &>();
    return lhs.size() < rhs.size() || (lhs.size() == rhs.size() && lhs <= rhs);
}

bool exact_fields(const Json &value, std::initializer_list<std::string_view> fields) {
    if (!value.is_object() || value.size() != fields.size()) return false;
    return std::all_of(fields.begin(), fields.end(), [&value](const std::string_view field) {
        return value.contains(std::string(field));
    });
}

bool digest_map(const Json &value, const bool allow_empty = false) {
    if (!value.is_object() || (!allow_empty && value.empty())) return false;
    for (auto row = value.begin(); row != value.end(); ++row) {
        if (!identifier_string(Json(row.key())) || !sha256_string(row.value())) return false;
    }
    return true;
}

bool sorted_identifiers(const Json &value, const bool allow_empty = false) {
    if (!value.is_array() || (!allow_empty && value.empty())) return false;
    std::string previous;
    for (std::size_t index = 0; index < value.size(); ++index) {
        if (!identifier_string(value.at(index))) return false;
        const auto &current = value.at(index).get_ref<const std::string &>();
        if (index != 0U && previous >= current) return false;
        previous = current;
    }
    return true;
}

bool admitted_value(const Json &value, std::initializer_list<std::string_view> admitted) {
    if (!value.is_string()) return false;
    const auto &text = value.get_ref<const std::string &>();
    return std::any_of(admitted.begin(), admitted.end(),
                       [&text](const std::string_view item) { return text == item; });
}

bool signatures_valid(const Json &value) {
    if (!value.is_array()) return false;
    for (const auto &signature : value) {
        if (!exact_fields(signature, {"algorithm", "key_id", "signature", "signer_context"}))
            return false;
        for (const auto field : {"algorithm", "key_id", "signature", "signer_context"}) {
            if (!nonempty_string(signature.at(field))) return false;
        }
    }
    return true;
}

std::string utc_timestamp() {
    const auto now = std::chrono::system_clock::now();
    const std::time_t time = std::chrono::system_clock::to_time_t(now);
    std::tm utc{};
#ifdef _WIN32
    gmtime_s(&utc, &time);
#else
    gmtime_r(&time, &utc);
#endif
    std::ostringstream output;
    output << std::put_time(&utc, "%Y-%m-%dT%H:%M:%SZ");
    return output.str();
}

std::optional<std::size_t> lifecycle_rank(std::string_view event) {
    static constexpr std::array<std::string_view, 10> order = {
        "journal_admitted", "construction", "validation",  "publication", "episode", "drain",
        "rollback",         "shutdown",     "reclamation", "terminal",
    };
    const auto found = std::find(order.begin(), order.end(), event);
    if (found == order.end()) return std::nullopt;
    return static_cast<std::size_t>(std::distance(order.begin(), found));
}

bool run_receipt_payload_valid(const Json &payload) {
    if (!exact_fields(payload, {"authority_kind",
                                "schema_version",
                                "contract_version",
                                "writer_role",
                                "receipt_id",
                                "run_id",
                                "attempt_id",
                                "host_boot_id",
                                "incarnation_epoch",
                                "writer_generation",
                                "reader_generation_min",
                                "reader_generation_max",
                                "admission_binding_sha256",
                                "plan_binding",
                                "release_binding",
                                "executable",
                                "package",
                                "build",
                                "platform",
                                "inputs",
                                "backend",
                                "execution_scope",
                                "lifecycle",
                                "results",
                                "checkpoints",
                                "qualification_refs",
                                "side_effect_receipts",
                                "completion",
                                "terminal_state",
                                "terminal_reason",
                                "journal_id",
                                "journal_last_sequence",
                                "journal_last_record_sha256",
                                "retention_class",
                                "hash_algorithm",
                                "authenticity"})) {
        return false;
    }
    if (payload.value("authority_kind", "") != "run_receipt" ||
        payload.value("schema_version", "") != "echelon_forge.run_receipt.v1" ||
        payload.value("contract_version", "") != "echelon_forge.run_receipt_contract.v1" ||
        payload.value("writer_role", "") != "runtime_host" ||
        payload.value("hash_algorithm", "") != "sha256") {
        return false;
    }
    for (const auto field : {"receipt_id", "run_id", "attempt_id", "host_boot_id", "journal_id"}) {
        if (!identifier_string(payload.at(field))) return false;
    }
    for (const auto field : {"incarnation_epoch", "writer_generation", "reader_generation_min",
                             "reader_generation_max"}) {
        if (!generation_string(payload.at(field))) return false;
    }
    if (!generation_less_equal(payload.at("reader_generation_min"),
                               payload.at("reader_generation_max")))
        return false;
    if (!sha256_string(payload.at("admission_binding_sha256"))) return false;

    const auto &plan = payload.at("plan_binding");
    if (!exact_fields(plan, {"plan_id", "plan_sha256", "request_sha256", "plan_generation",
                             "plan_canonical_sha256", "plan_location", "request_canonical_sha256",
                             "request_location", "compiler_identity", "compiler_version"}) ||
        !identifier_string(plan.at("plan_id")) || !generation_string(plan.at("plan_generation"))) {
        return false;
    }
    for (const auto field :
         {"plan_sha256", "request_sha256", "plan_canonical_sha256", "request_canonical_sha256"}) {
        if (!sha256_string(plan.at(field))) return false;
    }
    for (const auto field :
         {"plan_location", "request_location", "compiler_identity", "compiler_version"}) {
        if (!nonempty_string(plan.at(field))) return false;
    }

    const auto &release = payload.at("release_binding");
    if (!exact_fields(release, {"release_id", "release_manifest_sha256", "rollout_decision_id",
                                "rollout_decision_sha256", "provenance_sha256", "sbom_sha256",
                                "attestation_sha256"}) ||
        !identifier_string(release.at("release_id")) ||
        !identifier_string(release.at("rollout_decision_id"))) {
        return false;
    }
    for (const auto field : {"release_manifest_sha256", "rollout_decision_sha256",
                             "provenance_sha256", "sbom_sha256", "attestation_sha256"}) {
        if (!sha256_string(release.at(field))) return false;
    }

    const auto &executable = payload.at("executable");
    if (!exact_fields(executable, {"identity", "version", "digest", "native_module_digests",
                                   "plugin_digests"}) ||
        !identifier_string(executable.at("identity")) ||
        !nonempty_string(executable.at("version")) || !sha256_string(executable.at("digest")) ||
        !digest_map(executable.at("native_module_digests")) ||
        !digest_map(executable.at("plugin_digests"), true)) {
        return false;
    }

    const auto &package = payload.at("package");
    if (!exact_fields(package, {"identity", "version", "digest", "wheel_digest",
                                "dependency_graph_sha256"}) ||
        !identifier_string(package.at("identity")) || !nonempty_string(package.at("version")) ||
        !sha256_string(package.at("digest")) || !sha256_string(package.at("wheel_digest")) ||
        !sha256_string(package.at("dependency_graph_sha256"))) {
        return false;
    }

    const auto &build = payload.at("build");
    if (!exact_fields(build, {"source_revision", "dirty", "build_mode", "linker", "toolchain",
                              "cxx_abi", "python_abi", "node_abi"}) ||
        !build.at("dirty").is_boolean()) {
        return false;
    }
    for (const auto field : {"source_revision", "build_mode", "linker", "toolchain", "cxx_abi",
                             "python_abi", "node_abi"}) {
        if (!nonempty_string(build.at(field))) return false;
    }

    const auto &platform = payload.at("platform");
    if (!exact_fields(platform, {"os", "architecture", "compiler", "standard_library", "cpu", "gpu",
                                 "driver", "runtime_dependency_digests"}) ||
        !digest_map(platform.at("runtime_dependency_digests"))) {
        return false;
    }
    for (const auto field :
         {"os", "architecture", "compiler", "standard_library", "cpu", "gpu", "driver"}) {
        if (!nonempty_string(platform.at(field))) return false;
    }

    const auto &inputs = payload.at("inputs");
    if (!exact_fields(inputs, {"scenario_id", "content_id", "database_id", "configuration_id",
                               "seed_policy", "seed_value", "seed_stream_id", "artifacts"}) ||
        !digest_map(inputs.at("artifacts"))) {
        return false;
    }
    for (const auto field : {"scenario_id", "content_id", "database_id", "configuration_id",
                             "seed_policy", "seed_value", "seed_stream_id"}) {
        if (!nonempty_string(inputs.at(field))) return false;
    }

    const auto &backend = payload.at("backend");
    if (!exact_fields(backend,
                      {"profile_id", "backend_provider_id", "backend_implementation_version",
                       "determinism_profile", "system_graph_sha256", "stage_contract_sha256"}) ||
        !sha256_string(backend.at("system_graph_sha256")) ||
        !sha256_string(backend.at("stage_contract_sha256"))) {
        return false;
    }
    for (const auto field : {"profile_id", "backend_provider_id", "backend_implementation_version",
                             "determinism_profile"}) {
        if (!nonempty_string(backend.at(field))) return false;
    }

    const auto &scope = payload.at("execution_scope");
    if (!exact_fields(scope, {"world_ids", "entity_ids", "episode_ids", "request_ids", "epochs"}))
        return false;
    for (const auto field : {"world_ids", "episode_ids", "request_ids"}) {
        if (!sorted_identifiers(scope.at(field))) return false;
    }
    if (!sorted_identifiers(scope.at("entity_ids"), true)) return false;
    const auto &epochs = scope.at("epochs");
    if (!exact_fields(epochs, {"world", "entity", "episode", "request"})) return false;
    for (const auto field : {"world", "entity", "episode", "request"}) {
        if (!generation_string(epochs.at(field))) return false;
    }

    const auto &lifecycle = payload.at("lifecycle");
    static constexpr std::array<std::string_view, 10> lifecycle_order = {
        "journal_admitted", "construction", "validation",  "publication", "episode", "drain",
        "rollback",         "shutdown",     "reclamation", "terminal",
    };
    if (!lifecycle.is_array() || lifecycle.empty()) return false;
    std::size_t previous_rank = 0U;
    std::uint64_t previous_durable_sequence = 0U;
    bool first_event = true;
    for (std::size_t index = 0; index < lifecycle.size(); ++index) {
        const auto &event = lifecycle.at(index);
        if (!exact_fields(event, {"sequence", "event", "timestamp", "epoch", "durable_sequence"}) ||
            !safe_unsigned(event.at("sequence")) ||
            event.at("sequence").get<std::uint64_t>() != index ||
            !safe_unsigned(event.at("durable_sequence")) ||
            !nonempty_string(event.at("timestamp")) || !generation_string(event.at("epoch")) ||
            !event.at("event").is_string()) {
            return false;
        }
        const auto name = event.at("event").get<std::string>();
        const auto position = std::find(lifecycle_order.begin(), lifecycle_order.end(), name);
        if (position == lifecycle_order.end()) return false;
        const auto rank =
            static_cast<std::size_t>(std::distance(lifecycle_order.begin(), position));
        if (!first_event && rank < previous_rank) return false;
        if (!first_event &&
            event.at("durable_sequence").get<std::uint64_t>() < previous_durable_sequence)
            return false;
        previous_rank = rank;
        previous_durable_sequence = event.at("durable_sequence").get<std::uint64_t>();
        first_event = false;
    }
    if (lifecycle.front().at("event") != "journal_admitted" ||
        lifecycle.back().at("event") != "terminal")
        return false;

    const auto &results = payload.at("results");
    if (!exact_fields(results, {"result_digest", "output_artifacts", "native_validation"}) ||
        !(results.at("result_digest") == "" || sha256_string(results.at("result_digest"))) ||
        !results.at("output_artifacts").is_array()) {
        return false;
    }
    std::string previous_output;
    for (std::size_t index = 0; index < results.at("output_artifacts").size(); ++index) {
        const auto &output = results.at("output_artifacts").at(index);
        if (!exact_fields(output, {"name", "digest", "media_type", "size", "availability",
                                   "retention_class", "retrieval_location"}) ||
            !identifier_string(output.at("name")) || !sha256_string(output.at("digest")) ||
            !safe_size(output.at("size")) ||
            !admitted_value(output.at("retention_class"), {"active-release", "rollback-window",
                                                           "run-retained", "evidence-short"})) {
            return false;
        }
        for (const auto field : {"media_type", "availability", "retrieval_location"}) {
            if (!nonempty_string(output.at(field))) return false;
        }
        const auto &name = output.at("name").get_ref<const std::string &>();
        if (index != 0U && previous_output >= name) return false;
        previous_output = name;
    }
    const auto &native_validation = results.at("native_validation");
    if (!exact_fields(native_validation, {"accepted", "validator_id", "evidence_sha256"}) ||
        !native_validation.at("accepted").is_boolean() ||
        !identifier_string(native_validation.at("validator_id")) ||
        !sha256_string(native_validation.at("evidence_sha256"))) {
        return false;
    }

    const auto &checkpoints = payload.at("checkpoints");
    if (!exact_fields(checkpoints, {"source_refs", "created_refs"})) return false;
    for (const auto collection_name : {"source_refs", "created_refs"}) {
        const auto &refs = checkpoints.at(collection_name);
        if (!refs.is_array()) return false;
        std::string previous_checkpoint;
        for (const auto &ref : refs) {
            if (!exact_fields(ref, {"checkpoint_id", "checkpoint_sha256", "validation_sha256",
                                    "state_schema_generation", "retrieval_location"}) ||
                !identifier_string(ref.at("checkpoint_id")) ||
                !sha256_string(ref.at("checkpoint_sha256")) ||
                !sha256_string(ref.at("validation_sha256")) ||
                !generation_string(ref.at("state_schema_generation")) ||
                !nonempty_string(ref.at("retrieval_location"))) {
                return false;
            }
            const auto &checkpoint_id = ref.at("checkpoint_id").get_ref<const std::string &>();
            if (!previous_checkpoint.empty() && previous_checkpoint >= checkpoint_id) return false;
            previous_checkpoint = checkpoint_id;
        }
    }
    for (const auto collection_name : {"qualification_refs", "side_effect_receipts"}) {
        const auto &collection = payload.at(collection_name);
        if (!collection.is_array()) return false;
        std::string previous_identity;
        for (std::size_t index = 0; index < collection.size(); ++index) {
            const auto &row = collection.at(index);
            const bool side_effect = std::string_view(collection_name) == "side_effect_receipts";
            if (!(side_effect ? exact_fields(
                                    row, {"identity", "digest", "media_type", "retrieval_location"})
                              : exact_fields(row, {"identity", "digest"})) ||
                !identifier_string(row.at("identity")) || !sha256_string(row.at("digest"))) {
                return false;
            }
            if (side_effect && (!nonempty_string(row.at("media_type")) ||
                                !nonempty_string(row.at("retrieval_location")))) {
                return false;
            }
            const auto &identity = row.at("identity").get_ref<const std::string &>();
            if (index != 0U && previous_identity >= identity) return false;
            previous_identity = identity;
        }
    }

    const auto &completion = payload.at("completion");
    if (!exact_fields(completion, {"created_at", "finalized_at", "durable_ack"}) ||
        !nonempty_string(completion.at("created_at")) ||
        !nonempty_string(completion.at("finalized_at")) || completion.at("durable_ack") != true) {
        return false;
    }
    if (!admitted_value(payload.at("terminal_state"), {"completed", "failed", "cancelled",
                                                       "rejected", "crashed", "incomplete"}) ||
        !nonempty_string(payload.at("terminal_reason")) ||
        !safe_unsigned(payload.at("journal_last_sequence")) ||
        !sha256_string(payload.at("journal_last_record_sha256")) ||
        !admitted_value(payload.at("retention_class"),
                        {"active-release", "rollback-window", "run-retained", "evidence-short"})) {
        return false;
    }
    if (payload.at("terminal_state") == "completed") {
        if (results.at("result_digest") == "" || native_validation.at("accepted") != true)
            return false;
        if (results.at("output_artifacts").empty()) return false;
        for (const auto required : {"journal_admitted", "construction", "validation", "publication",
                                    "episode", "drain", "shutdown", "reclamation", "terminal"}) {
            const bool present =
                std::any_of(lifecycle.begin(), lifecycle.end(), [required](const Json &event) {
                    return event.at("event") == required;
                });
            if (!present) return false;
        }
    }

    const auto journal_tail = payload.at("journal_last_sequence").get<std::uint64_t>();
    for (const auto &event : lifecycle) {
        if (event.at("durable_sequence").get<std::uint64_t>() > journal_tail) return false;
    }
    if (lifecycle.back().at("durable_sequence").get<std::uint64_t>() != journal_tail) return false;

    const auto &authenticity = payload.at("authenticity");
    return exact_fields(authenticity, {"attestation_sha256", "signatures"}) &&
           sha256_string(authenticity.at("attestation_sha256")) &&
           signatures_valid(authenticity.at("signatures"));
}

} // namespace

std::optional<std::string> execution_measurement_sha256(const Json &bindings);

bool validate_runtime_run_receipt_json(std::string_view receipt_json, std::string &detail) {
    try {
        const auto receipt = Json::parse(receipt_json.begin(), receipt_json.end());
        if (!receipt.is_object() || receipt.size() != 7U ||
            receipt.value("canonicalization", "") != "echelon_forge.canonical_json.v2" ||
            receipt.value("domain", "") != "runtime.run-receipt" ||
            receipt.value("envelope_version", "") != "echelon_forge.authority_envelope.v1" ||
            receipt.value("media_type", "") !=
                "application/vnd.echelon-forge.run-receipt.v1+json" ||
            !receipt.contains("payload") || !receipt.contains("payload_sha256") ||
            !receipt.contains("signatures") || !signatures_valid(receipt.at("signatures"))) {
            detail = "receipt envelope profile is invalid";
            return false;
        }
        const auto canonical_payload =
            runtime::authority_contracts::canonical_authority_json(receipt.at("payload").dump());
        if (!canonical_payload.has_value() || receipt.dump() != receipt_json ||
            receipt.at("payload").dump() != *canonical_payload ||
            runtime::authority_contracts::authority_digest_sha256_hex(
                "runtime.run-receipt", "application/vnd.echelon-forge.run-receipt.v1+json",
                *canonical_payload) != receipt.at("payload_sha256").get<std::string>() ||
            !run_receipt_payload_valid(receipt.at("payload"))) {
            detail = "receipt payload or detached digest is invalid";
            return false;
        }
    } catch (const Json::exception &error) {
        detail = error.what();
        return false;
    }
    return true;
}

Json admission_binding_material(const Json &bindings) {
    auto material = bindings;
    material.erase("release_manifest_envelope_json");
    material.erase("rollout_decision_envelope_json");
    return material;
}

bool validate_embedded_authorities(const Json &bindings, std::string &detail) {
    if (!bindings.contains("release_manifest_envelope_json") ||
        !bindings.contains("rollout_decision_envelope_json") ||
        !bindings.at("release_manifest_envelope_json").is_string() ||
        !bindings.at("rollout_decision_envelope_json").is_string()) {
        detail = "release and rollout authority envelopes are required";
        return false;
    }
    Json release;
    Json decision;
    try {
        release = Json::parse(bindings.at("release_manifest_envelope_json").get<std::string>());
        decision = Json::parse(bindings.at("rollout_decision_envelope_json").get<std::string>());
    } catch (const Json::exception &error) {
        detail = std::string("embedded authority envelope is invalid: ") + error.what();
        return false;
    }
    const auto validate = [](const Json &envelope, std::string_view expected_kind) {
        if (!envelope.is_object() || !envelope.contains("payload") ||
            !envelope.at("payload").is_object())
            return false;
        const auto result = runtime::authority_contracts::validate_authority_envelope_json(
            envelope.dump(), envelope.at("payload").dump());
        return result.valid && envelope.at("payload").value("authority_kind", "") == expected_kind;
    };
    if (!validate(release, "release_manifest") || !validate(decision, "rollout_decision")) {
        detail = "embedded release or rollout authority envelope is not valid";
        return false;
    }
    const auto &release_payload = release.at("payload");
    const auto &decision_payload = decision.at("payload");
    const auto &release_binding = bindings.at("release_binding");
    const auto &plan_binding = bindings.at("plan_binding");
    if (release_binding.at("release_id") != release_payload.at("release_id") ||
        release_binding.at("release_manifest_sha256") != release.at("payload_sha256") ||
        release_binding.at("provenance_sha256") != release_payload.at("provenance_sha256") ||
        release_binding.at("sbom_sha256") != release_payload.at("sbom_sha256") ||
        release_binding.at("rollout_decision_id") != decision_payload.at("decision_id") ||
        release_binding.at("rollout_decision_sha256") != decision.at("payload_sha256") ||
        decision_payload.at("release_id") != release_payload.at("release_id") ||
        decision_payload.at("manifest_sha256") != release.at("payload_sha256") ||
        decision_payload.at("plan_sha256") != plan_binding.at("plan_sha256") ||
        !generation_less_equal(release_payload.at("reader_generation_min"),
                               bindings.at("reader_generation_min")) ||
        !generation_less_equal(bindings.at("reader_generation_max"),
                               release_payload.at("reader_generation_max")) ||
        !generation_less_equal(decision_payload.at("plan_reader_generation_min"),
                               bindings.at("reader_generation_min")) ||
        !generation_less_equal(bindings.at("reader_generation_max"),
                               decision_payload.at("plan_reader_generation_max"))) {
        detail = "release, rollout, plan, and reader-generation bindings differ";
        return false;
    }
    const auto &package = bindings.at("package");
    bool package_matched = false;
    for (const auto &entry : release_payload.at("package_set")) {
        if (entry.at("name") == package.at("identity") &&
            entry.at("sha256") == package.at("digest") &&
            entry.at("sha256") == package.at("wheel_digest")) {
            package_matched = true;
            break;
        }
    }
    const auto supported_row = bindings.at("platform").at("os").get<std::string>() + "-" +
                               bindings.at("platform").at("architecture").get<std::string>() + "-" +
                               bindings.at("platform").at("compiler").get<std::string>();
    if (!package_matched ||
        std::find(release_payload.at("supported_rows").begin(),
                  release_payload.at("supported_rows").end(),
                  supported_row) == release_payload.at("supported_rows").end() ||
        bindings.at("build").at("source_revision") != release_payload.at("source_revision") ||
        bindings.at("build").at("toolchain") != release_payload.at("toolchain_identity")) {
        detail = "measured package, build, or platform is not admitted by ReleaseManifest";
        return false;
    }
    return true;
}

std::optional<std::string> digest_path(const std::filesystem::path &path, std::string &detail) {
    std::error_code error;
    if (!std::filesystem::exists(path, error) || error) {
        detail = "execution provenance path is absent: " + path.string();
        return std::nullopt;
    }
    if (std::filesystem::is_regular_file(path, error) && !error) {
        std::ifstream input(path, std::ios::binary);
        if (!input) {
            detail = "execution provenance file cannot be opened: " + path.string();
            return std::nullopt;
        }
        std::ostringstream bytes;
        bytes << input.rdbuf();
        return runtime::authority_contracts::sha256_hex(bytes.str());
    }
    if (!std::filesystem::is_directory(path, error) || error) {
        detail = "execution provenance path is not a regular file or directory: " + path.string();
        return std::nullopt;
    }
    Json entries = Json::array();
    for (std::filesystem::recursive_directory_iterator
             it(path, std::filesystem::directory_options::skip_permission_denied, error),
         end;
         it != end && !error; it.increment(error)) {
        if (!it->is_regular_file(error) || error) continue;
        std::ifstream input(it->path(), std::ios::binary);
        if (!input) {
            detail = "execution provenance file cannot be opened: " + it->path().string();
            return std::nullopt;
        }
        std::ostringstream bytes;
        bytes << input.rdbuf();
        entries.push_back(Json{{"path", it->path().lexically_relative(path).generic_string()},
                               {"sha256", runtime::authority_contracts::sha256_hex(bytes.str())}});
    }
    if (error || entries.empty()) {
        detail = "execution provenance directory is empty or unreadable: " + path.string();
        return std::nullopt;
    }
    std::sort(entries.begin(), entries.end(), [](const Json &left, const Json &right) {
        return left.at("path").get<std::string>() < right.at("path").get<std::string>();
    });
    const auto canonical = runtime::authority_contracts::canonical_authority_json(entries.dump());
    return canonical.has_value()
               ? std::optional<std::string>(runtime::authority_contracts::sha256_hex(*canonical))
               : std::nullopt;
}

std::string module_identity(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(), [](const unsigned char character) {
        return static_cast<char>(std::tolower(character));
    });
    for (auto &character : value) {
        if (!((character >= 'a' && character <= 'z') || (character >= '0' && character <= '9') ||
              character == '.' || character == '_' || character == ':' || character == '-')) {
            character = '_';
        }
    }
    if (value.empty() || !(value.front() >= 'a' && value.front() <= 'z')) {
        value = "module_" + value;
    }
    if (value.size() > 128U) value.resize(128U);
    return value;
}

std::optional<std::filesystem::path> current_process_executable_path(std::string &detail) {
#if defined(_WIN32)
    std::wstring buffer(32768U, L'\0');
    const DWORD length =
        GetModuleFileNameW(nullptr, buffer.data(), static_cast<DWORD>(buffer.size()));
    if (length == 0U || length >= buffer.size()) {
        detail = "current process executable path cannot be observed";
        return std::nullopt;
    }
    buffer.resize(length);
    return std::filesystem::path(buffer);
#elif defined(__linux__)
    std::error_code error;
    auto path = std::filesystem::read_symlink("/proc/self/exe", error);
    if (error || path.empty()) {
        detail = "current process executable path cannot be observed";
        return std::nullopt;
    }
    return path;
#else
    detail = "current process executable discovery is unsupported on this platform";
    return std::nullopt;
#endif
}

bool collect_loaded_module_digests(Json &modules, std::string &detail) {
    std::map<std::string, std::filesystem::path> observed_paths;
#if defined(_WIN32)
    const HANDLE snapshot =
        CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, GetCurrentProcessId());
    if (snapshot == INVALID_HANDLE_VALUE) {
        detail = "loaded native modules cannot be enumerated";
        return false;
    }
    MODULEENTRY32W entry{};
    entry.dwSize = sizeof(entry);
    if (Module32FirstW(snapshot, &entry) == FALSE) {
        CloseHandle(snapshot);
        detail = "loaded native module inventory is empty";
        return false;
    }
    do {
        const std::filesystem::path path(entry.szExePath);
        const auto identity = module_identity(path.filename().string());
        const auto [_, inserted] = observed_paths.emplace(identity, path);
        if (!inserted && observed_paths.at(identity) != path) {
            CloseHandle(snapshot);
            detail = "loaded native module basenames are ambiguous";
            return false;
        }
    } while (Module32NextW(snapshot, &entry) != FALSE);
    CloseHandle(snapshot);
#elif defined(__linux__)
    std::ifstream maps("/proc/self/maps");
    std::string line;
    while (std::getline(maps, line)) {
        const auto path_start = line.find('/');
        if (path_start == std::string::npos) continue;
        const std::filesystem::path path(line.substr(path_start));
        std::error_code error;
        if (!std::filesystem::is_regular_file(path, error) || error) continue;
        const auto identity = module_identity(path.filename().string());
        const auto [_, inserted] = observed_paths.emplace(identity, path);
        if (!inserted && observed_paths.at(identity) != path) {
            detail = "loaded native module basenames are ambiguous";
            return false;
        }
    }
#else
    detail = "loaded native module discovery is unsupported on this platform";
    return false;
#endif
    modules = Json::object();
    for (const auto &[identity, path] : observed_paths) {
        const auto digest = digest_path(path, detail);
        if (!digest.has_value()) return false;
        modules[identity] = *digest;
    }
    if (modules.empty()) {
        detail = "loaded native module inventory is empty";
        return false;
    }
    return true;
}

std::optional<std::string> read_file_bytes(const std::filesystem::path &path, std::string &detail) {
    std::ifstream input(path, std::ios::binary);
    if (!input) {
        detail = "runtime authority file cannot be opened: " + path.string();
        return std::nullopt;
    }
    std::ostringstream bytes;
    bytes << input.rdbuf();
    return bytes.str();
}

bool validate_execution_plan_source(const RuntimeExecutionProvenanceSources &sources,
                                    const Json &bindings, std::string &plan_json,
                                    std::string &detail) {
    if (sources.resolved_execution_plan_path.empty()) {
        detail = "P5-A resolved execution plan source is required";
        return false;
    }
    const auto bytes = read_file_bytes(sources.resolved_execution_plan_path, detail);
    if (!bytes.has_value()) return false;
    const auto validation =
        runtime::authority_contracts::validate_resolved_execution_plan_json(*bytes);
    if (!validation.valid) {
        detail = "P5-A resolved execution plan is invalid: " + validation.detail;
        return false;
    }
    const auto plan = Json::parse(*bytes);
    const auto &plan_binding = bindings.at("plan_binding");
    const auto &input_bindings = plan.at("input_bindings");
    const auto &inputs = bindings.at("inputs").at("artifacts");
    const auto plan_blob_sha256 = runtime::authority_contracts::sha256_hex(*bytes);
    const auto request_sha256 = input_bindings.at("request_sha256").get<std::string>();
    if (plan.at("plan_id") != plan_binding.at("plan_id") ||
        plan.at("plan_sha256") != plan_binding.at("plan_sha256") ||
        plan.at("writer_generation") != plan_binding.at("plan_generation") ||
        input_bindings.at("request_sha256") != plan_binding.at("request_sha256") ||
        input_bindings.at("request_sha256") != plan_binding.at("request_canonical_sha256") ||
        plan_binding.at("plan_location") != "ledger://blob-" + plan_blob_sha256 ||
        plan_binding.at("request_location") != "ledger://blob-" + request_sha256 ||
        !inputs.contains("resolved_execution_plan") || !inputs.contains("request") ||
        inputs.at("resolved_execution_plan") != plan_blob_sha256 ||
        inputs.at("request") != request_sha256 ||
        !generation_less_equal(plan.at("reader_generation_min"),
                               bindings.at("reader_generation_min")) ||
        !generation_less_equal(bindings.at("reader_generation_max"),
                               plan.at("reader_generation_max"))) {
        detail = "admitted plan/request content addresses differ from the P5-A plan source";
        return false;
    }
    plan_json = *bytes;
    return true;
}

bool collect_runtime_execution_bindings_json(const RuntimeExecutionProvenanceSources &sources,
                                             std::string_view binding_template_json,
                                             std::string &observed_bindings_json,
                                             std::string &detail,
                                             std::string *verified_request_json) {
    try {
        auto observed = Json::parse(binding_template_json.begin(), binding_template_json.end());
        if (!observed.is_object() || !observed.contains("executable") ||
            !observed.contains("package") || !observed.contains("platform") ||
            !observed.contains("inputs") || !observed.contains("backend")) {
            detail = "execution provenance binding template is incomplete";
            return false;
        }
        const auto &backend = observed.at("backend");
        if (backend.value("profile_id", "") != "cpu_exact.reference" ||
            backend.value("backend_provider_id", "") != "builtin.backend.flecs_cpu" ||
            backend.value("determinism_profile", "") != "exact") {
            detail = "accelerator execution provenance has no native hardware collector";
            return false;
        }
        if (sources.package_path.empty() || sources.wheel_path.empty()) {
            detail = "package and wheel provenance paths are required";
            return false;
        }
        const auto &facts = sources.owner_facts;
        const auto owner_fact = [](const std::string &value) { return !value.empty(); };
        if (!owner_fact(facts.build_mode) || !owner_fact(facts.linker) ||
            !owner_fact(facts.cxx_abi) || !owner_fact(facts.python_abi) ||
            !owner_fact(facts.node_abi)) {
            detail = "execution provenance owner facts are incomplete";
            return false;
        }
        if (!native_compiler_facts_match(facts)) {
            detail = "execution provenance compiler/build facts differ from the running binary";
            return false;
        }
        std::string plan_json;
        if (!validate_execution_plan_source(sources, observed, plan_json, detail)) return false;
        const auto plan = Json::parse(plan_json);
        const auto executable_path = current_process_executable_path(detail);
        if (!executable_path.has_value()) return false;
        auto executable_digest = digest_path(*executable_path, detail);
        auto package_digest = digest_path(sources.package_path, detail);
        auto wheel_digest = digest_path(sources.wheel_path, detail);
        if (!executable_digest.has_value() || !package_digest.has_value() ||
            !wheel_digest.has_value())
            return false;
        const auto executable_identity = module_identity(executable_path->stem().string());
        const auto executable_version = "sha256-" + executable_digest->substr(0, 16U);
        const auto plan_envelope =
            Json::parse(plan.at("authority_envelope_json").get<std::string>());
        const auto &plan_payload = plan_envelope.at("payload");
        const auto &release_envelope =
            Json::parse(observed.at("release_manifest_envelope_json").get<std::string>());
        const auto &release_payload = release_envelope.at("payload");
        std::string package_identity;
        for (const auto &entry : release_payload.at("package_set")) {
            if (entry.at("sha256") == *package_digest) {
                package_identity = entry.at("name").get<std::string>();
                break;
            }
        }
        if (package_identity.empty()) {
            detail = "measured package is not present in the closed ReleaseManifest";
            return false;
        }
        const auto plan_blob_sha256 = runtime::authority_contracts::sha256_hex(plan_json);
        const auto request_sha = plan.at("input_bindings").at("request_sha256").get<std::string>();
        const auto request_bytes = read_file_bytes(sources.request_path, detail);
        if (!request_bytes.has_value()) return false;
        const auto request = Json::parse(*request_bytes);
        const auto canonical_request =
            runtime::authority_contracts::canonical_authority_json(request.dump());
        if (!canonical_request.has_value() ||
            runtime::authority_contracts::sha256_hex(*canonical_request) != request_sha ||
            !request.contains("intent") || !request.contains("configuration") ||
            request.at("intent").value("simulation_id", "").empty() ||
            request.value("request_id", "").empty() ||
            !request.at("configuration").contains("seed") ||
            !request.at("configuration").at("seed").is_number_unsigned() ||
            request.at("configuration").at("seed").get<std::uint64_t>() >
                std::numeric_limits<std::uint32_t>::max() ||
            !request.at("configuration").contains("time_step_ns") ||
            !request.at("configuration").at("time_step_ns").is_number_unsigned() ||
            request.at("configuration").at("time_step_ns").get<std::uint64_t>() == 0U) {
            detail = "runtime input facts differ from the P5-A request authority";
            return false;
        }
        if (verified_request_json != nullptr) *verified_request_json = *canonical_request;
        const auto resolved_sha =
            plan.at("input_bindings").at("resolved_manifest_sha256").get<std::string>();
        const auto catalog_sha =
            plan.at("input_bindings").at("catalog_lock_sha256").get<std::string>();
        const auto canonical_hash = [&](const Json &value) -> std::optional<std::string> {
            const auto canonical =
                runtime::authority_contracts::canonical_authority_json(value.dump());
            return canonical.has_value() ? std::optional<std::string>(
                                               runtime::authority_contracts::sha256_hex(*canonical))
                                         : std::nullopt;
        };
        const auto &resolved_manifest = plan_payload.at("resolved_manifest").at("manifest");
        const auto system_graph_sha = canonical_hash(resolved_manifest.at("system_contributions"));
        const auto stage_contract_sha = canonical_hash(resolved_manifest.at("contract_versions"));
        if (!system_graph_sha.has_value() || !stage_contract_sha.has_value()) {
            detail = "closed execution plan lacks canonical backend graph facts";
            return false;
        }
        observed["executable"]["identity"] = executable_identity;
        observed["executable"]["version"] = executable_version;
        observed["package"]["identity"] = package_identity;
        observed["package"]["version"] = "sha256-" + package_digest->substr(0, 16U);
        observed["build"] = {
            {"source_revision", release_payload.at("source_revision")},
            {"dirty", facts.build_dirty},
            {"build_mode", facts.build_mode},
            {"linker", facts.linker},
            {"toolchain", release_payload.at("toolchain_identity")},
            {"cxx_abi", facts.cxx_abi},
            {"python_abi", facts.python_abi},
            {"node_abi", facts.node_abi},
        };
        observed["inputs"] = {
            {"scenario_id", request.at("intent").at("simulation_id")},
            {"content_id", "resolved-manifest-" + resolved_sha},
            {"database_id", "catalog-lock-" + catalog_sha},
            {"configuration_id", request.at("request_id")},
            {"seed_policy", "fixed"},
            {"seed_value",
             std::to_string(request.at("configuration").at("seed").get<std::uint64_t>())},
            {"seed_stream_id", request.at("request_id").get<std::string>() + ".seed"},
            {"artifacts",
             Json{{"request", request_sha}, {"resolved_execution_plan", plan_blob_sha256}}},
        };
        observed["backend"] = {
            {"profile_id", plan_payload.at("backend").at("profile_id")},
            {"backend_provider_id", plan_payload.at("backend").at("provider_id")},
            {"backend_implementation_version",
             plan_payload.at("backend").at("implementation_version")},
            {"determinism_profile", "exact"},
            {"system_graph_sha256", *system_graph_sha},
            {"stage_contract_sha256", *stage_contract_sha},
        };
        Json native_modules;
        if (!collect_loaded_module_digests(native_modules, detail)) return false;
        observed.at("executable")["digest"] = *executable_digest;
        observed.at("executable")["native_module_digests"] = native_modules;
        observed.at("executable")["plugin_digests"] = Json::object();
        observed.at("package")["digest"] = *package_digest;
        observed.at("package")["wheel_digest"] = *wheel_digest;
        const auto dependency_canonical =
            runtime::authority_contracts::canonical_authority_json(native_modules.dump());
        if (!dependency_canonical.has_value()) {
            detail = "runtime dependency observation is not canonicalizable";
            return false;
        }
        observed.at("package")["dependency_graph_sha256"] =
            runtime::authority_contracts::sha256_hex(*dependency_canonical);
#if defined(_WIN32)
        observed.at("platform")["os"] = "windows";
#elif defined(__APPLE__)
        observed.at("platform")["os"] = "macos";
#elif defined(__linux__)
        observed.at("platform")["os"] = "linux";
#else
        detail = "host operating system cannot be measured";
        return false;
#endif
#if defined(_M_X64) || defined(__x86_64__)
        observed.at("platform")["architecture"] = "amd64";
        observed.at("platform")["cpu"] = "x64";
#elif defined(_M_ARM64) || defined(__aarch64__)
        observed.at("platform")["architecture"] = "arm64";
        observed.at("platform")["cpu"] = "arm64";
#else
        detail = "host CPU architecture cannot be measured";
        return false;
#endif
#if defined(_MSC_VER)
        observed.at("platform")["compiler"] = "msvc";
        observed.at("platform")["standard_library"] = "msvc";
#elif defined(__clang__)
        observed.at("platform")["compiler"] = "clang";
        observed.at("platform")["standard_library"] = "libc++";
#elif defined(__GNUC__)
        observed.at("platform")["compiler"] = "gcc";
        observed.at("platform")["standard_library"] = "libstdc++";
#else
        detail = "host compiler cannot be measured";
        return false;
#endif
        observed.at("platform")["gpu"] = "none";
        observed.at("platform")["driver"] = "none";
        observed.at("platform")["runtime_dependency_digests"] = native_modules;
        const auto canonical =
            runtime::authority_contracts::canonical_authority_json(observed.dump());
        if (!canonical.has_value()) {
            detail = "execution provenance observation is not canonicalizable";
            return false;
        }
        observed_bindings_json = *canonical;
        return true;
    } catch (const Json::exception &error) {
        detail = error.what();
        return false;
    }
}

bool load_runtime_execution_plan_json(const RuntimeExecutionProvenanceSources &sources,
                                      std::string_view receipt_bindings_json,
                                      std::string &execution_plan_json, std::string &detail) {
    try {
        const auto bindings =
            Json::parse(receipt_bindings_json.begin(), receipt_bindings_json.end());
        if (!bindings.is_object() || !bindings.contains("plan_binding") ||
            !bindings.contains("inputs")) {
            detail = "receipt bindings lack plan/input authority";
            return false;
        }
        return validate_execution_plan_source(sources, bindings, execution_plan_json, detail);
    } catch (const Json::exception &error) {
        detail = error.what();
        return false;
    }
}

bool validate_runtime_run_header_json(std::string_view run_id, std::string_view header_json,
                                      std::string &detail) {
    try {
        const auto header = Json::parse(header_json.begin(), header_json.end());
        if (!header.is_object() || header.dump() != header_json ||
            header.value("run_id", "") != run_id ||
            !exact_fields(header, {"run_id", "receipt_bindings", "admission_binding_sha256",
                                   "observed_measurement_sha256"}) ||
            !sha256_string(header.at("admission_binding_sha256")) ||
            !sha256_string(header.at("observed_measurement_sha256"))) {
            detail = "run admission header is not canonical or run-bound";
            return false;
        }
        const auto &bindings = header.at("receipt_bindings");
        if (!exact_fields(bindings,
                          {"receipt_id", "attempt_id", "plan_binding", "release_binding",
                           "executable", "package", "build", "platform", "inputs", "backend",
                           "reader_generation_min", "reader_generation_max",
                           "release_manifest_envelope_json", "rollout_decision_envelope_json"}) ||
            !identifier_string(bindings.at("receipt_id")) ||
            !identifier_string(bindings.at("attempt_id")) ||
            !generation_string(bindings.at("reader_generation_min")) ||
            !generation_string(bindings.at("reader_generation_max")) ||
            !generation_less_equal(bindings.at("reader_generation_min"),
                                   bindings.at("reader_generation_max"))) {
            detail = "run admission bindings are incomplete";
            return false;
        }
        if (!validate_embedded_authorities(bindings, detail)) return false;
        const auto measured = execution_measurement_sha256(bindings);
        const auto canonical_bindings = runtime::authority_contracts::canonical_authority_json(
            admission_binding_material(bindings).dump());
        if (!measured.has_value() || !canonical_bindings.has_value() ||
            runtime::authority_contracts::sha256_hex(*canonical_bindings) !=
                header.at("admission_binding_sha256").get<std::string>() ||
            *measured != header.at("observed_measurement_sha256").get<std::string>()) {
            detail = "run admission measurement digest differs";
            return false;
        }
    } catch (const Json::exception &error) {
        detail = error.what();
        return false;
    }
    return true;
}

std::optional<std::string> execution_measurement_sha256(const Json &bindings) {
    if (!bindings.is_object() || !bindings.contains("executable") ||
        !bindings.contains("package") || !bindings.contains("platform") ||
        !bindings.contains("inputs"))
        return std::nullopt;
    const Json material = {{"executable", bindings.at("executable")},
                           {"inputs", bindings.at("inputs")},
                           {"package", bindings.at("package")},
                           {"platform", bindings.at("platform")}};
    const auto canonical = runtime::authority_contracts::canonical_authority_json(material.dump());
    return canonical.has_value()
               ? std::optional<std::string>(runtime::authority_contracts::sha256_hex(*canonical))
               : std::nullopt;
}

RuntimeRunRecorder::RuntimeRunRecorder(RuntimeRunRecorderStore &store, std::string run_id,
                                       std::string writer_id)
    : store_(store), run_id_(std::move(run_id)), writer_id_(std::move(writer_id)),
      admission_capability_(make_admission_capability(run_id_, writer_id_)) {}

RuntimeRunAdmissionCapability
RuntimeRunRecorder::make_admission_capability(std::string_view run_id, std::string_view writer_id) {
    std::random_device random;
    const auto now = std::chrono::steady_clock::now().time_since_epoch().count();
    const auto seed = std::string(run_id) + "\0" + std::string(writer_id) + "\0" +
                      std::to_string(now) + "\0" + std::to_string(random()) + "\0" +
                      std::to_string(reinterpret_cast<std::uintptr_t>(&random));
    return RuntimeRunAdmissionCapability(runtime::authority_contracts::sha256_hex(seed));
}

RuntimeRunRecorderStatus RuntimeRunRecorder::reject(std::string code, std::string detail) {
    state_ = RuntimeRunRecorderState::Rejected;
    return failure(std::move(code), std::move(detail));
}

RuntimeRunRecorderStatus RuntimeRunRecorder::reject_after_admission(std::string code,
                                                                    std::string detail) {
    terminalizable_ = true;
    return reject(std::move(code), std::move(detail));
}

RuntimeRunRecorderStatus RuntimeRunRecorder::admit(std::string_view header_json) {
    if (state_ != RuntimeRunRecorderState::New)
        return reject("recorder.state", "run recorder is not new");
    if (run_id_.empty() || writer_id_.empty() || header_json.empty()) {
        return reject("recorder.input", "run, writer, and header identities are required");
    }
    try {
        const auto header = Json::parse(header_json.begin(), header_json.end());
        if (!exact_run_id(run_id_, header) || !header.is_object() || header.dump() != header_json)
            return reject("recorder.header", "header run identity differs");
        if (header.contains("receipt_bindings")) {
            if (!exact_fields(header, {"run_id", "receipt_bindings", "admission_binding_sha256",
                                       "observed_measurement_sha256"}) ||
                !sha256_string(header.at("admission_binding_sha256")) ||
                !sha256_string(header.at("observed_measurement_sha256")))
                return reject("recorder.header", "admission bindings are not canonical");
            const auto &bindings = header.at("receipt_bindings");
            if (!exact_fields(bindings, {"receipt_id", "attempt_id", "plan_binding",
                                         "release_binding", "executable", "package", "build",
                                         "platform", "inputs", "backend", "reader_generation_min",
                                         "reader_generation_max", "release_manifest_envelope_json",
                                         "rollout_decision_envelope_json"}) ||
                !identifier_string(bindings.at("receipt_id")) ||
                !identifier_string(bindings.at("attempt_id")) ||
                !generation_string(bindings.at("reader_generation_min")) ||
                !generation_string(bindings.at("reader_generation_max")) ||
                !generation_less_equal(bindings.at("reader_generation_min"),
                                       bindings.at("reader_generation_max")))
                return reject("recorder.header", "admission binding fields are incomplete");
            std::string authority_detail;
            if (!validate_embedded_authorities(bindings, authority_detail))
                return reject("recorder.header", authority_detail);
            const auto measured = execution_measurement_sha256(bindings);
            const auto canonical_bindings = runtime::authority_contracts::canonical_authority_json(
                admission_binding_material(bindings).dump());
            if (!measured.has_value() || !canonical_bindings.has_value() ||
                runtime::authority_contracts::sha256_hex(*canonical_bindings) !=
                    header.at("admission_binding_sha256").get<std::string>() ||
                *measured != header.at("observed_measurement_sha256").get<std::string>())
                return reject("recorder.header", "admission measurement digest differs");
            admission_bindings_json_ = bindings.dump();
            admission_binding_sha256_ = header.at("admission_binding_sha256");
            admission_measurement_sha256_ = header.at("observed_measurement_sha256");
            receipt_id_ = bindings.at("receipt_id").get<std::string>();
            attempt_id_ = bindings.at("attempt_id").get<std::string>();
            execution_scope_json_ =
                Json{{"world_ids", Json::array({"world-unpublished"})},
                     {"entity_ids", Json::array()},
                     {"episode_ids", Json::array({"episode-unpublished"})},
                     {"request_ids", Json::array({"request-" + run_id_})},
                     {"epochs",
                      Json{{"world", "0"}, {"entity", "0"}, {"episode", "0"}, {"request", "0"}}}}
                    .dump();
        }
    } catch (const Json::exception &error) {
        return reject("recorder.header", error.what());
    }
    std::string detail;
    if (!store_.acquire_fence("journal:" + run_id_, writer_id_, fence_generation_, detail)) {
        return reject("recorder.fence", detail);
    }
    if (!store_.commit_header_authorized(run_id_, fence_generation_, writer_id_, header_json,
                                         admission_capability_, detail)) {
        std::uint64_t recovered_next = 0;
        std::string recovered_tail;
        std::string recovery_detail;
        if (!store_.resume_journal_authorized(run_id_, fence_generation_, writer_id_, header_json,
                                              admission_capability_, recovered_next, recovered_tail,
                                              recovery_detail)) {
            return reject("recorder.admission", detail + "; resume failed: " + recovery_detail);
        }
        next_sequence_ = recovered_next;
        last_record_sha256_ = std::move(recovered_tail);
    }
    RuntimeRunRecorderRecoveryState recovered;
    if (!store_.rehydrate_state_authorized(run_id_, admission_capability_, recovered, detail)) {
        return reject("recorder.admission", detail);
    }
    committed_checkpoints_ = std::move(recovered.committed_checkpoints);
    lifecycle_events_ = std::move(recovered.lifecycle_events);
    if (!recovered.host_boot_id.empty()) host_boot_id_ = std::move(recovered.host_boot_id);
    if (!recovered.incarnation_epoch.empty())
        incarnation_epoch_ = std::move(recovered.incarnation_epoch);
    if (!recovered.execution_scope_json.empty())
        execution_scope_json_ = std::move(recovered.execution_scope_json);
    if (!recovered.existing_receipt_json.empty())
        pending_receipt_json_ = std::move(recovered.existing_receipt_json);
    state_ = RuntimeRunRecorderState::Admitted;
    terminalizable_ = true;
    admitted_at_ =
        recovered.admitted_at.empty() ? utc_timestamp() : std::move(recovered.admitted_at);
    if (!admission_bindings_json_.empty()) {
        if (next_sequence_ == 0U) {
            const auto lifecycle = note_lifecycle("journal_admitted");
            if (!lifecycle) return lifecycle;
        } else if (lifecycle_events_.empty()) {
            // A resumed strict journal already contains the original durable
            // admission frame. Reconstruct the receipt projection without
            // appending a second admission event under the recovery fence.
            lifecycle_events_.push_back(Json{
                {"sequence", 0U},
                {"event", "journal_admitted"},
                {"timestamp", admitted_at_},
                {"epoch", incarnation_epoch_},
                {"durable_sequence", 0U}}.dump());
        }
    }
    return {true, {}, {}};
}

RuntimeRunRecorderStatus RuntimeRunRecorder::note_lifecycle(std::string_view event) {
    if (state_ != RuntimeRunRecorderState::Admitted)
        return failure("recorder.state", "lifecycle event requires an admitted journal");
    const auto rank = lifecycle_rank(event);
    if (!rank.has_value())
        return reject_after_admission("recorder.lifecycle", "lifecycle event is not admitted");
    if (!lifecycle_events_.empty()) {
        const auto previous = Json::parse(lifecycle_events_.back());
        const auto previous_event = previous.at("event").get<std::string>();
        const bool recovery_terminal =
            previous_event == "terminal" && event == "terminal" && next_sequence_ > 0U &&
            previous.at("durable_sequence").get<std::uint64_t>() < next_sequence_ - 1U;
        if (previous_event == event && !recovery_terminal) return {true, {}, {}};
        const auto previous_rank = lifecycle_rank(previous_event);
        if (!previous_rank.has_value() || *rank < *previous_rank)
            return reject_after_admission("recorder.lifecycle", "lifecycle event order regressed");
        if (previous_event == "terminal" && !recovery_terminal)
            return reject_after_admission("recorder.lifecycle", "lifecycle is already terminal");
    }
    const auto timestamp = utc_timestamp();
    const auto durable_sequence = next_sequence_;
    const auto record =
        Json{{"event", "runtime_lifecycle"}, {"lifecycle_event", event}, {"timestamp", timestamp}}
            .dump();
    const auto appended = append(durable_sequence, record);
    if (!appended) return appended;
    lifecycle_events_.push_back(Json{
        {"sequence", lifecycle_events_.size()},
        {"event", event},
        {"timestamp", timestamp},
        {"epoch", incarnation_epoch_},
        {"durable_sequence",
         durable_sequence}}.dump());
    return {true, {}, {}};
}

RuntimeRunRecorderStatus RuntimeRunRecorder::bind_runtime_identity(
    std::string_view host_boot_id, std::string_view incarnation_epoch, std::string_view world_id,
    std::string_view world_epoch, std::string_view episode_id, std::string_view episode_epoch,
    std::string_view request_id) {
    if (state_ != RuntimeRunRecorderState::Admitted)
        return failure("recorder.state", "runtime identity requires an admitted journal");
    const Json candidate = {
        {"world_ids", Json::array({world_id})},
        {"entity_ids", Json::array()},
        {"episode_ids", Json::array({episode_id})},
        {"request_ids", Json::array({request_id})},
        {"epochs", Json{{"world", world_epoch},
                        {"entity", "0"},
                        {"episode", episode_epoch},
                        {"request", incarnation_epoch}}},
    };
    if (!identifier_string(Json(host_boot_id)) || !generation_string(Json(incarnation_epoch)) ||
        !identifier_string(Json(world_id)) || !generation_string(Json(world_epoch)) ||
        !identifier_string(Json(episode_id)) || !generation_string(Json(episode_epoch)) ||
        !identifier_string(Json(request_id))) {
        return reject_after_admission("recorder.identity", "runtime identity is not canonical");
    }
    if (incarnation_epoch_ != "0") {
        if (host_boot_id_ == host_boot_id && incarnation_epoch_ == incarnation_epoch &&
            execution_scope_json_ == candidate.dump())
            return {true, {}, {}};
        return reject_after_admission("recorder.identity", "runtime identity is already bound");
    }
    const auto appended = append(next_sequence_, Json{{"event", "runtime_identity_bound"},
                                                      {"host_boot_id", host_boot_id},
                                                      {"incarnation_epoch", incarnation_epoch},
                                                      {"execution_scope", candidate}}
                                                     .dump());
    if (!appended) return appended;
    host_boot_id_ = host_boot_id;
    incarnation_epoch_ = incarnation_epoch;
    execution_scope_json_ = candidate.dump();
    return {true, {}, {}};
}

RuntimeRunRecorderStatus RuntimeRunRecorder::observe_entity(std::string_view entity_id,
                                                            std::string_view entity_epoch) {
    if (state_ != RuntimeRunRecorderState::Admitted)
        return failure("recorder.state", "entity observation requires an admitted journal");
    if (!identifier_string(Json(entity_id)) || !generation_string(Json(entity_epoch)))
        return reject_after_admission("recorder.identity", "entity identity is not canonical");
    auto scope = Json::parse(execution_scope_json_);
    auto &entities = scope.at("entity_ids");
    if (std::find(entities.begin(), entities.end(), Json(std::string(entity_id))) != entities.end())
        return {true, {}, {}};
    const auto appended = append(next_sequence_, Json{{"event", "runtime_entity_observed"},
                                                      {"entity_id", entity_id},
                                                      {"entity_epoch", entity_epoch}}
                                                     .dump());
    if (!appended) return appended;
    entities.push_back(entity_id);
    std::sort(entities.begin(), entities.end());
    scope.at("epochs")["entity"] = entity_epoch;
    execution_scope_json_ = scope.dump();
    return {true, {}, {}};
}

RuntimeRunRecorderStatus RuntimeRunRecorder::append(std::uint64_t sequence,
                                                    std::string_view payload) {
    if (state_ != RuntimeRunRecorderState::Admitted)
        return failure("recorder.state", "journal is not admitted");
    if (payload.empty()) return failure("recorder.payload", "journal payload is empty");
    if (sequence != next_sequence_)
        return failure("recorder.sequence", "journal sequence is not monotonic");
    std::string detail;
    RuntimeRunRecorderAppendAck ack;
    if (!store_.append_record_authorized(run_id_, fence_generation_, writer_id_, sequence, payload,
                                         admission_capability_, ack, detail)) {
        return reject_after_admission("recorder.append", detail);
    }
    if (!ack.durable || ack.sequence != sequence || !sha256_string(Json(ack.payload_sha256)) ||
        !sha256_string(Json(ack.record_sha256)) ||
        ack.payload_sha256 != runtime::authority_contracts::sha256_hex(payload)) {
        return reject_after_admission("recorder.append",
                                      "store returned an invalid durable append acknowledgement");
    }
    last_record_sha256_ = ack.record_sha256;
    ++next_sequence_;
    return {true, {}, {}};
}

RuntimeRunRecorderStatus RuntimeRunRecorder::persist_checkpoint(std::string_view checkpoint_json,
                                                                std::string_view validation_json) {
    if (state_ != RuntimeRunRecorderState::Admitted)
        return failure("recorder.state", "checkpoint requires an admitted journal");
    if (checkpoint_json.empty() || validation_json.empty())
        return reject("recorder.checkpoint", "checkpoint and validation evidence are required");
    try {
        auto checkpoint = Json::parse(checkpoint_json.begin(), checkpoint_json.end());
        if (!checkpoint.is_object() || checkpoint.dump() != checkpoint_json ||
            !checkpoint.contains("payload") || !checkpoint.at("payload").is_object() ||
            checkpoint.at("payload").value("authority_kind", "") != "state_checkpoint" ||
            checkpoint.at("payload").value("run_id", "") != run_id_ ||
            !checkpoint.at("payload").contains("state_schema_generation") ||
            !generation_string(checkpoint.at("payload").at("state_schema_generation"))) {
            return reject("recorder.checkpoint",
                          "checkpoint authority is not canonical or run-bound");
        }
        auto &checkpoint_payload = checkpoint.at("payload");
        if (next_sequence_ == 0U || !checkpoint_payload.contains("world_fragments") ||
            !checkpoint_payload.at("world_fragments").is_array())
            return reject("recorder.checkpoint", "checkpoint requires a durable transfer scope");
        checkpoint_payload["checkpoint_id"] =
            "checkpoint-" + run_id_ + "-" + std::to_string(next_sequence_);
        checkpoint_payload["transfer_fence_sequence"] = std::to_string(next_sequence_);
        if (!admission_bindings_json_.empty()) {
            const auto scope = Json::parse(execution_scope_json_);
            std::set<std::string> expected_worlds;
            std::set<std::string> expected_episodes;
            for (const auto &world : scope.at("world_ids"))
                expected_worlds.insert(world.get<std::string>());
            for (const auto &episode : scope.at("episode_ids"))
                expected_episodes.insert(episode.get<std::string>());
            std::set<std::string> actual_worlds;
            std::set<std::string> actual_episodes;
            for (const auto &fragment : checkpoint_payload.at("world_fragments")) {
                actual_worlds.insert(fragment.at("world_id").get<std::string>());
                for (const auto &episode : fragment.at("episode_ids"))
                    actual_episodes.insert(episode.get<std::string>());
            }
            if (actual_worlds != expected_worlds || actual_episodes != expected_episodes)
                return reject("recorder.checkpoint",
                              "checkpoint fragments do not exactly cover the execution scope");
        }
        const auto canonical_payload =
            runtime::authority_contracts::canonical_authority_json(checkpoint_payload.dump());
        if (!canonical_payload.has_value())
            return reject("recorder.checkpoint", "checkpoint payload is not canonical");
        auto validation = Json::parse(validation_json.begin(), validation_json.end());
        validation["checkpoint_id"] = checkpoint_payload.at("checkpoint_id");
        const auto replay_sha256 = runtime::authority_contracts::checkpoint_replay_aggregate_sha256(
            checkpoint_payload.dump());
        if (replay_sha256.has_value() && validation.contains("aggregate_replay_sha256"))
            validation["aggregate_replay_sha256"] = *replay_sha256;
        if (!validation.is_object() || validation.value("accepted", false) != true ||
            validation.value("checkpoint_id", "") !=
                checkpoint_payload.value("checkpoint_id", "") ||
            validation.value("state_sha256", "").empty() ||
            validation.value("state_sha256", "") !=
                checkpoint_payload.value("aggregate_state_sha256", ""))
            return reject("recorder.checkpoint", "validation evidence is not canonical JSON");
        if (checkpoint.at("payload").at("writer_generation") != std::to_string(fence_generation_))
            return reject("recorder.checkpoint", "checkpoint writer generation differs from fence");
        if (!admission_bindings_json_.empty()) {
            const auto bindings =
                Json::parse(admission_bindings_json_.begin(), admission_bindings_json_.end());
            const auto release =
                Json::parse(bindings.at("release_manifest_envelope_json").get<std::string>());
            if (checkpoint.at("payload").at("state_schema_generation") !=
                release.at("payload").at("state_schema_generation"))
                return reject("recorder.checkpoint",
                              "checkpoint state schema differs from the admitted release");
            const auto &payload = checkpoint.at("payload");
            if (payload.value("release_id", "") !=
                    bindings.at("release_binding").at("release_id").get<std::string>() ||
                payload.value("decision_id", "") !=
                    bindings.at("release_binding").at("rollout_decision_id").get<std::string>() ||
                payload.value("plan_sha256", "") !=
                    bindings.at("plan_binding").at("plan_sha256").get<std::string>())
                return reject("recorder.checkpoint",
                              "checkpoint release/decision differs from admitted run");
        }
        checkpoint["payload_sha256"] = runtime::authority_contracts::authority_digest_sha256_hex(
            "runtime.state-checkpoint", "application/vnd.echelon-forge.state-checkpoint.v1+json",
            *canonical_payload);
        const auto canonical_checkpoint =
            runtime::authority_contracts::canonical_authority_json(checkpoint.dump());
        if (!canonical_checkpoint.has_value())
            return reject("recorder.checkpoint", "checkpoint envelope is not canonicalizable");
        const auto validation_result =
            runtime::authority_contracts::validate_authority_envelope_json(*canonical_checkpoint,
                                                                           *canonical_payload);
        if (!validation_result.valid)
            return reject("recorder.checkpoint", validation_result.detail);
        const auto checkpoint_sha256 =
            runtime::authority_contracts::sha256_hex(*canonical_checkpoint);
        const auto validation_canonical =
            runtime::authority_contracts::canonical_authority_json(validation.dump());
        if (!validation_canonical.has_value())
            return reject("recorder.checkpoint", "validation evidence is not canonicalizable");
        const auto validation_sha256 =
            runtime::authority_contracts::sha256_hex(*validation_canonical);
        const auto intent = append(
            next_sequence_,
            Json{{"checkpoint_id", checkpoint_payload.at("checkpoint_id")},
                 {"checkpoint_sha256", checkpoint_sha256},
                 {"event", "checkpoint_commit"},
                 {"transfer_fence_sequence", checkpoint_payload.at("transfer_fence_sequence")},
                 {"validation_sha256", validation_sha256}}
                .dump());
        if (!intent) return intent;
        std::string detail;
        RuntimeRunRecorderCheckpointAck ack;
        if (!store_.commit_checkpoint_authorized(run_id_, fence_generation_, writer_id_,
                                                 *canonical_checkpoint, *validation_canonical,
                                                 admission_capability_, ack, detail)) {
            return reject("recorder.checkpoint", detail);
        }
        if (!ack.durable || !sha256_string(Json(ack.checkpoint_sha256)) ||
            !sha256_string(Json(ack.validation_sha256)) ||
            ack.checkpoint_sha256 !=
                runtime::authority_contracts::sha256_hex(*canonical_checkpoint) ||
            ack.validation_sha256 !=
                runtime::authority_contracts::sha256_hex(*validation_canonical) ||
            ack.state_schema_generation !=
                checkpoint.at("payload").at("state_schema_generation").get<std::string>()) {
            return reject("recorder.checkpoint",
                          "store returned an invalid durable checkpoint acknowledgement");
        }
        committed_checkpoints_.push_back({checkpoint_payload.at("checkpoint_id"),
                                          ack.checkpoint_sha256, ack.validation_sha256,
                                          ack.state_schema_generation});
    } catch (const Json::exception &error) {
        return reject("recorder.checkpoint", error.what());
    }
    return {true, {}, {}};
}

RuntimeRunRecorderStatus
RuntimeRunRecorder::put_artifact(std::string_view name, std::string_view bytes,
                                 std::string_view media_type, std::string_view retention_class,
                                 std::string &digest, std::string &retrieval_location) {
    if (state_ != RuntimeRunRecorderState::Admitted)
        return failure("recorder.state", "artifact requires an admitted journal");
    if (!identifier_string(Json(std::string(name))) || bytes.empty() || media_type.empty() ||
        retention_class.empty())
        return reject_after_admission("recorder.artifact", "artifact content metadata is required");
    if (std::any_of(committed_artifacts_.begin(), committed_artifacts_.end(),
                    [name](const auto &artifact) { return artifact.name == name; }))
        return reject_after_admission("recorder.artifact", "artifact name is already committed");
    std::string detail;
    if (!store_.put_artifact(bytes, media_type, retention_class, digest, retrieval_location,
                             detail)) {
        return reject_after_admission("recorder.artifact", detail);
    }
    if (!sha256_string(Json(digest)) || retrieval_location != "ledger://blob-" + digest) {
        return reject_after_admission("recorder.artifact",
                                      "store returned an invalid durable artifact acknowledgement");
    }
    committed_artifacts_.push_back({std::string(name), digest, std::string(media_type),
                                    static_cast<std::uint64_t>(bytes.size()),
                                    std::string(retention_class), retrieval_location});
    return {true, {}, {}};
}

RuntimeRunRecorderStatus
RuntimeRunRecorder::record_native_result(std::string_view result_digest,
                                         std::string_view validation_evidence_sha256) {
    if (state_ != RuntimeRunRecorderState::Admitted)
        return failure("recorder.state", "native result requires an admitted journal");
    if (!sha256_string(Json(std::string(result_digest))) ||
        !sha256_string(Json(std::string(validation_evidence_sha256))))
        return reject_after_admission("recorder.result", "native result digest is invalid");
    if (!native_result_digest_.empty() &&
        (native_result_digest_ != result_digest ||
         native_validation_evidence_sha256_ != validation_evidence_sha256))
        return reject_after_admission("recorder.result", "native result is already bound");
    native_result_digest_ = result_digest;
    native_validation_evidence_sha256_ = validation_evidence_sha256;
    return {true, {}, {}};
}

RuntimeRunRecorderStatus RuntimeRunRecorder::finalize(std::string_view receipt_json) {
    if (state_ != RuntimeRunRecorderState::Admitted)
        return failure("recorder.state", "journal is not admitted");
    if (receipt_json.empty()) return reject("recorder.receipt", "receipt is empty");
    if (!admission_bindings_json_.empty() && receipt_json != owner_projected_receipt_json_ &&
        receipt_json != pending_receipt_json_) {
        return reject("recorder.receipt",
                      "strict run receipt was not projected by the admitted recorder owner");
    }
    std::string contract_detail;
    if (!validate_runtime_run_receipt_json(receipt_json, contract_detail))
        return reject("recorder.receipt", contract_detail);
    try {
        const auto receipt = Json::parse(receipt_json.begin(), receipt_json.end());
        if (!receipt.is_object() || receipt.size() != 7U ||
            receipt.value("canonicalization", "") != "echelon_forge.canonical_json.v2" ||
            receipt.value("domain", "") != "runtime.run-receipt" ||
            receipt.value("envelope_version", "") != "echelon_forge.authority_envelope.v1" ||
            receipt.value("media_type", "") !=
                "application/vnd.echelon-forge.run-receipt.v1+json" ||
            !receipt.contains("payload") || !receipt.contains("payload_sha256") ||
            !receipt.contains("signatures") || !signatures_valid(receipt.at("signatures"))) {
            return reject("recorder.receipt", "receipt envelope profile is invalid");
        }
        const auto canonical_payload =
            runtime::authority_contracts::canonical_authority_json(receipt.at("payload").dump());
        if (!canonical_payload.has_value() || receipt.dump() != receipt_json ||
            receipt.at("payload").dump() != *canonical_payload ||
            runtime::authority_contracts::authority_digest_sha256_hex(
                "runtime.run-receipt", "application/vnd.echelon-forge.run-receipt.v1+json",
                *canonical_payload) != receipt.at("payload_sha256").get<std::string>()) {
            return reject("recorder.receipt",
                          "receipt envelope profile or detached digest is invalid");
        }
        if (!exact_run_id(run_id_, receipt))
            return reject("recorder.receipt", "receipt run identity differs");
        const auto &payload = receipt.at("payload");
        if (!admission_bindings_json_.empty()) {
            const auto bindings =
                Json::parse(admission_bindings_json_.begin(), admission_bindings_json_.end());
            const auto measured = execution_measurement_sha256(payload);
            if (!measured.has_value() || *measured != admission_measurement_sha256_ ||
                payload.at("admission_binding_sha256") != admission_binding_sha256_ ||
                payload.at("plan_binding") != bindings.at("plan_binding") ||
                payload.at("release_binding") != bindings.at("release_binding") ||
                payload.at("executable") != bindings.at("executable") ||
                payload.at("package") != bindings.at("package") ||
                payload.at("build") != bindings.at("build") ||
                payload.at("platform") != bindings.at("platform") ||
                payload.at("inputs") != bindings.at("inputs") ||
                payload.at("backend") != bindings.at("backend") ||
                payload.at("receipt_id") != bindings.at("receipt_id") ||
                payload.at("attempt_id") != bindings.at("attempt_id") ||
                payload.at("reader_generation_min") != bindings.at("reader_generation_min") ||
                payload.at("reader_generation_max") != bindings.at("reader_generation_max"))
                return reject("recorder.receipt", "receipt actual execution measurement differs");
        }
        if (!run_receipt_payload_valid(payload)) {
            return reject("recorder.receipt", "receipt payload contract is invalid");
        }
        if (payload.at("journal_id") != run_id_) {
            return reject("recorder.receipt", "receipt journal identity differs");
        }
        const auto exact_pending_retry =
            !pending_receipt_json_.empty() && receipt_json == pending_receipt_json_;
        if (payload.at("writer_generation") != std::to_string(fence_generation_) &&
            (!exact_pending_retry ||
             !generation_less_equal(payload.at("writer_generation"),
                                    Json(std::to_string(fence_generation_))))) {
            return reject("recorder.receipt",
                          "receipt writer generation differs from the active fence");
        }
        if (!receipt.contains("payload_sha256") || !sha256_string(receipt.at("payload_sha256"))) {
            return reject("recorder.receipt", "receipt digest is missing or invalid");
        }
        if (!payload.contains("journal_last_sequence") ||
            !safe_unsigned(payload.at("journal_last_sequence")) ||
            payload.at("journal_last_sequence").get<std::uint64_t>() !=
                (next_sequence_ == 0 ? 0 : next_sequence_ - 1) ||
            !payload.contains("journal_last_record_sha256") ||
            payload.at("journal_last_record_sha256") != last_record_sha256_) {
            return reject("recorder.receipt",
                          "receipt does not bind the last durable journal record");
        }
        for (const auto &committed : committed_checkpoints_) {
            bool bound = false;
            for (const auto collection_name : {"source_refs", "created_refs"}) {
                for (const auto &reference : payload.at("checkpoints").at(collection_name)) {
                    if (reference.at("checkpoint_id") == committed.checkpoint_id &&
                        reference.at("checkpoint_sha256") == committed.checkpoint_sha256 &&
                        reference.at("validation_sha256") == committed.validation_sha256 &&
                        reference.at("state_schema_generation") ==
                            committed.state_schema_generation) {
                        bound = true;
                    }
                }
            }
            if (!bound)
                return reject("recorder.receipt", "receipt omits a committed checkpoint reference");
        }
    } catch (const Json::exception &error) {
        return reject("recorder.receipt", error.what());
    }
    std::string detail;
    RuntimeRunRecorderFinalizeAck ack;
    const std::string receipt_bytes(receipt_json);
    pending_receipt_json_ = receipt_bytes;
    if (!store_.finalize_receipt_authorized(run_id_, fence_generation_, writer_id_, receipt_bytes,
                                            admission_capability_, ack, detail)) {
        return reject("recorder.finalize", detail);
    }
    const auto receipt = Json::parse(receipt_bytes.begin(), receipt_bytes.end());
    if (!ack.durable || !sha256_string(Json(ack.receipt_sha256)) ||
        receipt.at("payload_sha256").get<std::string>() != ack.receipt_sha256) {
        return reject("recorder.finalize",
                      "store returned an invalid durable receipt acknowledgement");
    }
    pending_receipt_json_.clear();
    owner_projected_receipt_json_.clear();
    state_ = RuntimeRunRecorderState::Finalized;
    terminalizable_ = false;
    return {true, {}, {}};
}

std::string RuntimeRunRecorder::admission_bindings_json() const {
    return admission_bindings_json_;
}

RuntimeRunRecorderStatus
RuntimeRunRecorder::finalize_observed(std::string_view receipt_template_json,
                                      std::string_view terminal_state,
                                      std::string_view terminal_reason) {
    bool recovered_after_rejection = false;
    if (state_ == RuntimeRunRecorderState::Rejected && terminalizable_) {
        std::uint64_t recovered_next = 0;
        std::string recovered_tail;
        std::string detail;
        if (!store_.resume_journal_authorized(run_id_, fence_generation_, writer_id_, {},
                                              admission_capability_, recovered_next, recovered_tail,
                                              detail)) {
            return failure("recorder.recovery", detail);
        }
        next_sequence_ = recovered_next;
        last_record_sha256_ = std::move(recovered_tail);
        state_ = RuntimeRunRecorderState::Admitted;
        recovered_after_rejection = true;
    }
    if (state_ != RuntimeRunRecorderState::Admitted)
        return failure("recorder.state", "journal is not admitted");
    if (!pending_receipt_json_.empty()) return finalize(pending_receipt_json_);
    if (!admission_bindings_json_.empty()) {
        const auto terminal = note_lifecycle("terminal");
        if (!terminal) return terminal;
    } else if (next_sequence_ == 0U || recovered_after_rejection) {
        const auto terminal_record = Json{
            {"event", "terminal"},
            {"reason", terminal_reason},
            {"state", terminal_state}}.dump();
        const auto appended = append(next_sequence_, terminal_record);
        if (!appended) return appended;
    }
    if (last_record_sha256_.empty())
        return failure("recorder.receipt", "terminal receipt requires a durable journal record");
    try {
        auto receipt = Json::parse(receipt_template_json.begin(), receipt_template_json.end());
        auto &payload = receipt.at("payload");
        payload["run_id"] = run_id_;
        payload["journal_id"] = run_id_;
        if (!receipt_id_.empty()) payload["receipt_id"] = receipt_id_;
        if (!attempt_id_.empty()) payload["attempt_id"] = attempt_id_;
        payload["host_boot_id"] = host_boot_id_;
        payload["incarnation_epoch"] = incarnation_epoch_;
        if (!execution_scope_json_.empty())
            payload["execution_scope"] = Json::parse(execution_scope_json_);
        payload["writer_generation"] = std::to_string(fence_generation_);
        if (!admission_binding_sha256_.empty())
            payload["admission_binding_sha256"] = admission_binding_sha256_;
        payload["journal_last_sequence"] = next_sequence_ - 1U;
        payload["journal_last_record_sha256"] = last_record_sha256_;
        payload["terminal_state"] = terminal_state;
        payload["terminal_reason"] = terminal_reason;
        payload.at("completion")["created_at"] =
            admitted_at_.empty() ? payload.at("completion").at("created_at") : Json(admitted_at_);
        payload.at("completion")["finalized_at"] = utc_timestamp();
        payload.at("completion")["durable_ack"] = true;

        const auto epoch = payload.at("incarnation_epoch");
        const bool completed = terminal_state == "completed";
        if (completed && (native_result_digest_.empty() || committed_artifacts_.empty()))
            return reject("recorder.result", "completed receipt lacks recorder-owned results");
        Json output_artifacts = Json::array();
        if (completed) {
            std::sort(committed_artifacts_.begin(), committed_artifacts_.end(),
                      [](const auto &left, const auto &right) { return left.name < right.name; });
            for (const auto &artifact : committed_artifacts_) {
                output_artifacts.push_back(
                    Json{{"name", artifact.name},
                         {"digest", artifact.digest},
                         {"media_type", artifact.media_type},
                         {"size", artifact.size},
                         {"availability", "durable"},
                         {"retention_class", artifact.retention_class},
                         {"retrieval_location", artifact.retrieval_location}});
            }
        }
        const auto failure_evidence = runtime::authority_contracts::sha256_hex(
            "runtime.native-validation:" + std::string(terminal_state) + ":" +
            std::string(terminal_reason));
        payload["results"] =
            Json{{"result_digest", completed ? native_result_digest_ : std::string{}},
                 {"output_artifacts", output_artifacts},
                 {"native_validation",
                  Json{{"accepted", completed},
                       {"validator_id", "native-run-validator"},
                       {"evidence_sha256",
                        completed ? native_validation_evidence_sha256_ : failure_evidence}}}};
        if (!admission_bindings_json_.empty()) {
            payload["lifecycle"] = Json::array();
            for (const auto &event_json : lifecycle_events_) {
                payload.at("lifecycle").push_back(Json::parse(event_json));
            }
        } else if (terminal_state != "completed") {
            const auto timestamp = utc_timestamp();
            payload["lifecycle"] =
                Json::array({Json{{"sequence", 0U},
                                  {"event", "journal_admitted"},
                                  {"timestamp", payload.at("completion").at("created_at")},
                                  {"epoch", epoch},
                                  {"durable_sequence", 0U}},
                             Json{{"sequence", 1U},
                                  {"event", "terminal"},
                                  {"timestamp", timestamp},
                                  {"epoch", epoch},
                                  {"durable_sequence", next_sequence_ - 1U}}});
        } else {
            auto &lifecycle = payload.at("lifecycle");
            for (auto &event : lifecycle) {
                const auto claimed = event.value("durable_sequence", 0ULL);
                event["durable_sequence"] = std::min<std::uint64_t>(claimed, next_sequence_ - 1U);
            }
            lifecycle.back()["durable_sequence"] = next_sequence_ - 1U;
            lifecycle.back()["timestamp"] = utc_timestamp();
        }

        payload["checkpoints"] =
            Json{{"source_refs", Json::array()}, {"created_refs", Json::array()}};
        auto &created_refs = payload.at("checkpoints").at("created_refs");
        for (const auto &committed : committed_checkpoints_) {
            const auto existing = std::find_if(
                created_refs.begin(), created_refs.end(), [&committed](const Json &reference) {
                    return reference.value("checkpoint_id", "") == committed.checkpoint_id;
                });
            if (existing == created_refs.end()) {
                created_refs.push_back(
                    Json{{"checkpoint_id", committed.checkpoint_id},
                         {"checkpoint_sha256", committed.checkpoint_sha256},
                         {"validation_sha256", committed.validation_sha256},
                         {"state_schema_generation", committed.state_schema_generation},
                         {"retrieval_location", "ledger://checkpoint-" + committed.checkpoint_id}});
            }
        }
        std::sort(created_refs.begin(), created_refs.end(),
                  [](const Json &left, const Json &right) {
                      return left.at("checkpoint_id").get<std::string>() <
                             right.at("checkpoint_id").get<std::string>();
                  });
        payload["qualification_refs"] = Json::array();
        payload["side_effect_receipts"] = Json::array();
        const auto attestation_material =
            Json{{"admission_binding_sha256", admission_binding_sha256_},
                 {"journal_last_record_sha256", last_record_sha256_},
                 {"journal_last_sequence", next_sequence_ - 1U},
                 {"result_digest", completed ? native_result_digest_ : std::string{}},
                 {"terminal_reason", terminal_reason},
                 {"terminal_state", terminal_state}};
        const auto canonical_attestation =
            runtime::authority_contracts::canonical_authority_json(attestation_material.dump());
        if (!canonical_attestation.has_value())
            return reject("recorder.receipt", "owner attestation is not canonicalizable");
        payload["authenticity"] =
            Json{{"attestation_sha256",
                  runtime::authority_contracts::sha256_hex(*canonical_attestation)},
                 {"signatures", Json::array()}};
        const auto canonical_payload =
            runtime::authority_contracts::canonical_authority_json(payload.dump());
        if (!canonical_payload.has_value())
            return reject("recorder.receipt", "observed receipt payload is not canonicalizable");
        receipt["payload_sha256"] = runtime::authority_contracts::authority_digest_sha256_hex(
            "runtime.run-receipt", "application/vnd.echelon-forge.run-receipt.v1+json",
            *canonical_payload);
        const auto canonical_receipt =
            runtime::authority_contracts::canonical_authority_json(receipt.dump());
        if (!canonical_receipt.has_value())
            return reject("recorder.receipt", "observed receipt envelope is not canonicalizable");
        owner_projected_receipt_json_ = *canonical_receipt;
        return finalize(owner_projected_receipt_json_);
    } catch (const Json::exception &error) {
        return reject("recorder.receipt", error.what());
    }
}

} // namespace runtime::host
