#pragma once

#include <algorithm>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

#include "runtime/contracts/parity_budget_profiles.h"

namespace runtime::parity {

inline const std::vector<ParityBudgetRecord> &parity_budget_registry_seed() {
    static const std::vector<ParityBudgetRecord> registry = {
        make_cpu_exact_reference_budget(),
        make_gpu_helpers_diagnostics_only_budget(),
        make_gpu_exact_unmaintained_candidate_budget(),
        make_resident_state_unmaintained_candidate_budget(),
        make_shadow_compare_unmaintained_candidate_budget(),
    };
    return registry;
}

inline const ParityBudgetRecord *find_parity_budget_record(std::string_view budget_id) {
    const auto &registry = parity_budget_registry_seed();
    const auto it = std::find_if(
        registry.begin(), registry.end(),
        [budget_id](const ParityBudgetRecord &record) { return record.budget_id == budget_id; });
    return it == registry.end() ? nullptr : &(*it);
}

inline ParityBudgetValidationResult
validate_profile_owned_parity_budget(std::string_view backend_profile_id,
                                     std::string_view profile_class, std::string_view budget_ref) {
    ParityBudgetValidationResult result{};

    if (is_blank(budget_ref)) {
        result.reject(std::string(kParityBudgetRejectionMissingBudgetRef));
        result.add_error("budget_ref is required");
        return result;
    }

    const ParityBudgetRecord *record = find_parity_budget_record(budget_ref);
    if (record == nullptr) {
        result.reject(std::string(kParityBudgetRejectionUnknownBudgetRef));
        result.add_error("budget_ref was not found in the registry seed");
        return result;
    }

    result = validate_parity_budget_record_contract(*record);
    if (!result.valid) {
        return result;
    }

    if (!is_blank(backend_profile_id) && record->backend_profile_id != backend_profile_id) {
        result.reject(std::string(kParityBudgetRejectionMetadataIncomplete));
        result.add_error("backend_profile_id does not own the referenced budget");
        return result;
    }

    if (!profile_class_compatible_with_parity_budget(profile_class, record->profile_class)) {
        result.reject(std::string(kParityBudgetRejectionProfileClassIncompatible));
        result.add_error("profile_class is not compatible with the referenced budget");
        return result;
    }

    return result;
}

inline std::optional<ParityBudgetValidationResult> validate_parity_budget_registry_seed() {
    const auto &registry = parity_budget_registry_seed();
    if (registry.empty()) {
        ParityBudgetValidationResult result{};
        result.reject(std::string(kParityBudgetRejectionMetadataIncomplete));
        result.add_error("registry seed must not be empty");
        return result;
    }

    std::vector<std::string> seen_budget_ids;
    seen_budget_ids.reserve(registry.size());
    std::vector<std::string> maintained_budget_ids;

    for (const auto &record : registry) {
        if (contains_value(seen_budget_ids, record.budget_id)) {
            ParityBudgetValidationResult result{};
            result.reject(std::string(kParityBudgetRejectionMetadataIncomplete));
            result.add_error("duplicate budget_id: " + record.budget_id);
            return result;
        }
        seen_budget_ids.push_back(record.budget_id);

        const ParityBudgetValidationResult record_result =
            validate_parity_budget_record_contract(record);
        if (!record_result.valid) {
            return record_result;
        }

        if (record_result.accepted_for_maintained_use) {
            maintained_budget_ids.push_back(record.budget_id);
        }
    }

    if (maintained_budget_ids.size() != 1 ||
        maintained_budget_ids.front() != kParityBudgetCpuExactReferenceV1) {
        ParityBudgetValidationResult result{};
        result.reject(std::string(kParityBudgetRejectionMetadataIncomplete));
        result.add_error(
            "registry seed must keep only parity_budget.cpu_exact.reference.v1 as maintained");
        return result;
    }

    return std::nullopt;
}

} // namespace runtime::parity
