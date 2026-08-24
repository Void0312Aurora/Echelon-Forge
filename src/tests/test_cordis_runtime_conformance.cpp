#include "core/engine/simulation_kernel.h"
#include "runtime/composition/composition_json.h"
#include "runtime/contracts/runtime_composition_projection_contract.h"
#include "systems/system_contribution_registry.h"

#include <nlohmann/json.hpp>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

namespace {

using Json = nlohmann::json;

std::string read_file(const char *path) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) {
        throw std::runtime_error(std::string("cannot open ") + path);
    }
    std::ostringstream contents;
    contents << stream.rdbuf();
    return contents.str();
}

bool exact_lock_entry(const Json &lock, std::string_view category, std::string_view descriptor_id,
                      std::string_view owner_id, const Json &capabilities) {
    const auto same_capabilities = [](const Json &actual, const Json &expected) {
        if (!actual.is_array() || !expected.is_array() || actual.size() != expected.size()) {
            return false;
        }
        std::vector<std::string> actual_values;
        std::vector<std::string> expected_values;
        for (const auto &value : actual) {
            if (!value.is_string()) return false;
            actual_values.push_back(value.get<std::string>());
        }
        for (const auto &value : expected) {
            if (!value.is_string()) return false;
            expected_values.push_back(value.get<std::string>());
        }
        std::sort(actual_values.begin(), actual_values.end());
        std::sort(expected_values.begin(), expected_values.end());
        return actual_values == expected_values;
    };
    for (const auto &entry : lock.at("entries")) {
        if (entry.at("category") == std::string(category) &&
            entry.at("descriptor_id") == std::string(descriptor_id) &&
            entry.at("owner_id") == std::string(owner_id) &&
            entry.at("implementation_id") == "echelon_forge.native_builtin" &&
            entry.at("implementation_version") == "1.0.0" &&
            entry.at("trust_decision") == "admitted" &&
            same_capabilities(entry.at("capabilities"), capabilities) &&
            entry.at("provenance") == Json({
                                          {"artifact_identity", "echelon-forge-source-tree"},
                                          {"artifact_kind", "repository_builtin"},
                                          {"artifact_sha256", nullptr},
                                      })) {
            return true;
        }
    }
    return false;
}

bool registry_matches_resolved(const auto &resolved, std::string *error) {
    if (!runtime::systems::validate_default_contribution_graph(error)) {
        return false;
    }
    const auto components = runtime::systems::default_component_contributions();
    if (components.size() != resolved.manifest.component_contributions.size()) {
        if (error != nullptr) *error = "component registry/resolved count mismatch";
        return false;
    }
    for (const auto &row : resolved.manifest.component_contributions) {
        const auto it =
            std::find_if(components.begin(), components.end(), [&](const auto &candidate) {
                return candidate.component_id == row.component_id &&
                       candidate.registration_id == row.registration_id;
            });
        if (it == components.end()) {
            if (error != nullptr) *error = "component registry/resolved identity mismatch";
            return false;
        }
    }
    const auto systems = runtime::systems::default_system_contributions();
    if (systems.size() != resolved.system_registration_order.size()) {
        if (error != nullptr) *error = "system registry/resolved count mismatch";
        return false;
    }
    for (std::size_t index = 0; index < systems.size(); ++index) {
        if (systems[index].contribution_id != resolved.system_registration_order[index]) {
            if (error != nullptr) *error = "system registry/resolved order mismatch";
            return false;
        }
        const auto it =
            std::find_if(resolved.manifest.system_contributions.begin(),
                         resolved.manifest.system_contributions.end(), [&](const auto &row) {
                             return row.contribution_id == systems[index].contribution_id;
                         });
        if (it == resolved.manifest.system_contributions.end() ||
            it->registration_factory_id != systems[index].registration_factory_id ||
            it->domain != systems[index].domain ||
            (!systems[index].after_contribution_id.empty() &&
             (it->after.size() != 1 ||
              it->after.front() != systems[index].after_contribution_id))) {
            if (error != nullptr) *error = "system registry/resolved metadata mismatch";
            return false;
        }
    }
    return true;
}

bool profile_projection_matches_artifacts(const Json &projection, const Json &request,
                                          const Json &lock, const auto &resolved,
                                          std::string *error) {
    const auto string_field = [](const Json &object, const char *key) {
        return object.contains(key) && object.at(key).is_string()
                   ? object.at(key).get<std::string>()
                   : std::string{};
    };
    const auto fail = [error](std::string message) {
        if (error != nullptr) *error = std::move(message);
        return false;
    };
    static constexpr std::array<std::string_view, 17> fields = {
        "schema_version",
        "projection_id",
        "projection_version",
        "requested_profile",
        "request_sha256",
        "lock_sha256",
        "authority_registry_sha256",
        "required_capabilities",
        "required_policies",
        "catalog_entries",
        "component_contributions",
        "system_contributions",
        "compatibility_claims",
        "canonicalization",
        "hash_algorithm",
        "canonical_json",
        "projection_sha256",
    };
    if (!projection.is_object() || projection.size() != fields.size() ||
        std::any_of(fields.begin(), fields.end(),
                    [&projection](std::string_view field) {
                        return !projection.contains(std::string(field));
                    }) ||
        !request.at("requested_profile").is_object() ||
        string_field(request.at("requested_profile"), "profile_id") !=
            "builtin.default_compatibility" ||
        string_field(request.at("requested_profile"), "profile_version") != "1.0.0" ||
        string_field(projection, "schema_version") !=
            "echelon_forge.runtime_profile_projection.v1" ||
        string_field(projection, "projection_id") != "builtin.default_compatibility.projection" ||
        string_field(projection, "projection_version") != "1.0.0" ||
        projection.at("requested_profile") != request.at("requested_profile") ||
        string_field(projection, "request_sha256") != string_field(lock, "request_sha256") ||
        string_field(projection, "lock_sha256") != string_field(lock, "lock_sha256") ||
        string_field(projection, "authority_registry_sha256") !=
            string_field(lock, "authority_registry_sha256") ||
        string_field(projection, "canonicalization") !=
            std::string(runtime::projection_contracts::kCanonicalizationId) ||
        string_field(projection, "hash_algorithm") !=
            std::string(runtime::projection_contracts::kHashAlgorithm)) {
        return fail("profile projection request/lock identity mismatch");
    }

    const auto sorted_string_array = [](const Json &values) {
        std::vector<std::string> sorted;
        sorted.reserve(values.size());
        for (const auto &value : values)
            sorted.push_back(value.get<std::string>());
        std::sort(sorted.begin(), sorted.end());
        return Json(sorted);
    };
    const auto expected_capabilities = sorted_string_array(request.at("required_capabilities"));
    const auto expected_policies = sorted_string_array(request.at("required_policies"));
    if (projection.at("required_capabilities") != expected_capabilities ||
        projection.at("required_policies") != expected_policies) {
        return fail("profile projection capability/policy mismatch");
    }

    Json expected_catalog = Json::array();
    for (const auto &entry : lock.at("entries")) {
        expected_catalog.push_back({
            {"category", entry.at("category")},
            {"owner_id", entry.at("owner_id")},
            {"descriptor_id", entry.at("descriptor_id")},
            {"capabilities", sorted_string_array(entry.at("capabilities"))},
        });
    }
    std::sort(expected_catalog.begin(), expected_catalog.end(),
              [](const Json &left, const Json &right) {
                  return std::tie(left.at("category").get_ref<const std::string &>(),
                                  left.at("descriptor_id").get_ref<const std::string &>()) <
                         std::tie(right.at("category").get_ref<const std::string &>(),
                                  right.at("descriptor_id").get_ref<const std::string &>());
              });
    if (projection.at("catalog_entries") != expected_catalog) {
        return fail("profile projection catalog admission mismatch");
    }

    const auto &components = resolved.manifest.component_contributions;
    Json expected_components = Json::array();
    for (const auto &row : components) {
        expected_components.push_back({
            {"component_id", row.component_id},
            {"registration_id", row.registration_id},
        });
    }
    std::sort(expected_components.begin(), expected_components.end(),
              [](const Json &left, const Json &right) {
                  return left.at("component_id").get<std::string>() <
                         right.at("component_id").get<std::string>();
              });
    if (projection.at("component_contributions") != expected_components) {
        return fail("profile projection component identity mismatch");
    }

    Json expected_systems = Json::array();
    for (std::size_t index = 0; index < resolved.system_registration_order.size(); ++index) {
        expected_systems.push_back({
            {"contribution_id", resolved.system_registration_order[index]},
            {"stage_order", index},
        });
    }
    if (projection.at("system_contributions") != expected_systems) {
        return fail("profile projection system order mismatch");
    }

    auto expected_claim_values = resolved.manifest.compatibility_claims;
    std::sort(expected_claim_values.begin(), expected_claim_values.end());
    const Json expected_claims = expected_claim_values;
    if (projection.at("compatibility_claims") != expected_claims) {
        return fail("profile projection compatibility claims mismatch");
    }

    const Json identity_payload = {
        {"schema_version", "echelon_forge.runtime_profile_projection.v1"},
        {"projection_id", "builtin.default_compatibility.projection"},
        {"projection_version", "1.0.0"},
        {"requested_profile", request.at("requested_profile")},
        {"request_sha256", lock.at("request_sha256")},
        {"lock_sha256", lock.at("lock_sha256")},
        {"authority_registry_sha256", lock.at("authority_registry_sha256")},
        {"required_capabilities", expected_capabilities},
        {"required_policies", expected_policies},
        {"catalog_entries", expected_catalog},
        {"component_contributions", expected_components},
        {"system_contributions", expected_systems},
        {"compatibility_claims", expected_claims},
        {"canonicalization", std::string(runtime::projection_contracts::kCanonicalizationId)},
        {"hash_algorithm", std::string(runtime::projection_contracts::kHashAlgorithm)},
    };
    const auto canonical_json = identity_payload.dump();
    if (!projection.at("canonical_json").is_string() ||
        projection.at("canonical_json").get<std::string>() != canonical_json) {
        return fail("profile projection canonical bytes mismatch");
    }
    if (!projection.at("projection_sha256").is_string() ||
        projection.at("projection_sha256").get<std::string>() !=
            runtime::projection_contracts::canonical_sha256_hex(canonical_json)) {
        return fail("profile projection identity mismatch");
    }
    return true;
}

} // namespace

int main(int argc, char **argv) {
    if (argc != 6 && argc != 7) {
        std::cerr << "usage: ef_cordis_runtime_conformance_test <request> <lock> <authority> "
                     "<requested_manifest> <resolved_manifest> [profile_projection]\n";
        return 2;
    }
    try {
        const auto request = read_file(argv[1]);
        const auto lock = read_file(argv[2]);
        const auto authority = read_file(argv[3]);
        const auto requested_manifest = read_file(argv[4]);
        const auto resolved_manifest = read_file(argv[5]);
        const auto request_doc = Json::parse(request);
        const auto lock_doc = Json::parse(lock);
        const auto requested_doc = Json::parse(requested_manifest);
        const auto profile_projection = argc == 7 ? Json::parse(read_file(argv[6])) : Json{};

        const auto projection =
            runtime::projection_contracts::validate_runtime_composition_projection_json(
                request, lock, authority);
        if (!projection.valid) {
            for (const auto &issue : projection.issues) {
                std::cerr << issue.code << '@' << issue.path << ": " << issue.detail << '\n';
            }
            return 1;
        }
        const auto requested =
            runtime::composition::parse_simulation_composition_manifest_json(requested_manifest);
        if (!requested.ok()) {
            std::cerr << requested.error().code << '@' << requested.error().subject << ": "
                      << requested.error().detail << '\n';
            return 1;
        }
        const auto resolved =
            runtime::composition::parse_resolved_composition_json(resolved_manifest);
        if (!resolved.ok()) {
            std::cerr << resolved.error().code << '@' << resolved.error().subject << ": "
                      << resolved.error().detail << '\n';
            return 1;
        }
        if (requested.value().requested_profile.profile_id != "builtin.default_compatibility" ||
            requested.value().requested_profile.profile_version != "1.0.0" ||
            resolved.value().manifest.requested_profile.profile_id !=
                "builtin.default_compatibility" ||
            resolved.value().manifest.requested_profile.profile_version != "1.0.0") {
            std::cerr << "native profile identity mismatch\n";
            return 1;
        }
        if (!(requested.value() == resolved.value().manifest)) {
            std::cerr << "requested and resolved manifest payloads differ\n";
            return 1;
        }
        std::string registry_error;
        if (!registry_matches_resolved(resolved.value(), &registry_error)) {
            std::cerr << "native contribution registry does not match resolved artifact: "
                      << registry_error << '\n';
            return 1;
        }
        if (argc == 7 &&
            !profile_projection_matches_artifacts(profile_projection, request_doc, lock_doc,
                                                  resolved.value(), &registry_error)) {
            std::cerr << "native profile projection does not match admitted artifacts: "
                      << registry_error << '\n';
            return 1;
        }
        if (request_doc.at("requested_profile") != requested_doc.at("requested_profile") ||
            request_doc.at("contract_versions") != requested_doc.at("contract_versions") ||
            request_doc.at("intent") != Json({
                                            {"evaluation_id", "default.evaluation"},
                                            {"policy_id", "default.policy"},
                                            {"simulation_id", "default.simulation"},
                                        }) ||
            request_doc.at("required_capabilities") != Json({
                                                           "deterministic.step",
                                                           "runtime.world_batch.cpu",
                                                       }) ||
            request_doc.at("required_policies") != Json({
                                                       "native_step_authority",
                                                       "no_mid_episode_truth_reconfiguration",
                                                   })) {
            std::cerr
                << "default request projection does not match the low-level manifest contract\n";
            return 1;
        }
        const auto &configuration = request_doc.at("configuration");
        if (!configuration.is_object() || !configuration.at("seed").is_number_integer() ||
            !configuration.at("time_step_ns").is_number_integer() || configuration.at("seed") < 0 ||
            configuration.at("time_step_ns") <= 0 || lock_doc.at("entries").size() != 6 ||
            !exact_lock_entry(lock_doc, "backend", "builtin.backend.flecs_cpu", "owner.backend",
                              Json({"runtime.world_batch.cpu"})) ||
            !exact_lock_entry(lock_doc, "domain", "builtin.domain.combined", "owner.domain",
                              Json({"domain.combined"})) ||
            !exact_lock_entry(lock_doc, "evidence", "builtin.composition.evidence",
                              "owner.evidence", Json({"runtime.composition.evidence"})) ||
            !exact_lock_entry(lock_doc, "model", "builtin.default.models", "owner.model",
                              Json({"simulation.model.default"})) ||
            !exact_lock_entry(lock_doc, "security", "builtin.repository.admission",
                              "owner.security", Json({"runtime.repository_builtin"})) ||
            !exact_lock_entry(lock_doc, "system", "builtin.default.system_graph", "owner.scheduler",
                              Json({"deterministic.step", "simulation.system.default"}))) {
            std::cerr << "default request configuration or lock-to-manifest admission failed\n";
            return 1;
        }
        const auto seed = configuration.at("seed").get<std::uint64_t>();
        const auto time_step_ns = configuration.at("time_step_ns").get<std::uint64_t>();
        if (seed != 42 || time_step_ns != 16'666'667 ||
            seed > static_cast<std::uint64_t>(std::numeric_limits<unsigned int>::max())) {
            std::cerr << "default request seed exceeds native range\n";
            return 1;
        }
        SimulationKernel kernel(resolved_manifest);
        kernel.set_time_step(static_cast<double>(time_step_ns) / 1'000'000'000.0);
        kernel.reset(static_cast<unsigned int>(seed));
        if (std::abs(kernel.get_time_step() - static_cast<double>(time_step_ns) / 1'000'000'000.0) >
            1e-12) {
            std::cerr << "native kernel did not apply requested time step\n";
            return 1;
        }
        if (kernel.world_composition_generation() != 1 ||
            kernel.requested_composition_sha256().empty() ||
            kernel.resolved_composition_sha256().empty()) {
            std::cerr << "native default production composition did not initialize\n";
            return 1;
        }
        if (kernel.requested_composition_sha256() != resolved.value().requested_manifest_sha256 ||
            kernel.resolved_composition_sha256() != resolved.value().resolved_manifest_sha256) {
            std::cerr << "native realized identity differs from supplied resolved artifact\n";
            return 1;
        }
        kernel.step();
        std::cout << "native projection and low-level manifest conformance passed; providers="
                  << resolved.value().manifest.providers.size()
                  << "; production_generation=" << kernel.world_composition_generation()
                  << "; request_sha256=" << lock_doc.at("request_sha256").get<std::string>()
                  << "; lock_sha256=" << lock_doc.at("lock_sha256").get<std::string>() << '\n';
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
