#pragma once

#include <algorithm>
#include <cstdint>
#include <string>
#include <vector>

struct RewardTerm {
#define EF_REWARD_TERM_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/reward_term.inc"
};

struct RewardReport {
#define EF_REWARD_REPORT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/reward_report.inc"
};

struct TerminationSpec {
#define EF_TERMINATION_SPEC_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/termination_spec.inc"
};

struct ObservationViewSpec {
#define EF_OBSERVATION_VIEW_SPEC_FIELD(type, name, default_value) type name = default_value;
#include "runtime/contracts/detail/observation_view_spec.inc"
};

struct ObservationViewCompatibilityReport {
#define EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD(type, name, default_value) \
    type name = default_value;
#include "runtime/contracts/detail/observation_view_compatibility_report.inc"
};

struct ObservationSchemaVersionParts {
    bool valid = false;
    int major = 0;
    int minor = 0;
};

inline ObservationSchemaVersionParts parse_observation_schema_version(const std::string& version) {
    ObservationSchemaVersionParts parts{};
    const std::size_t dot = version.find('.');
    if (dot == std::string::npos || dot == 0 || dot + 1 >= version.size()) {
        return parts;
    }

    try {
        const std::string major_text = version.substr(0, dot);
        const std::string minor_text = version.substr(dot + 1);
        std::size_t major_consumed = 0;
        std::size_t minor_consumed = 0;
        const int major = std::stoi(major_text, &major_consumed);
        const int minor = std::stoi(minor_text, &minor_consumed);
        if (major_consumed != major_text.size() || minor_consumed != minor_text.size()) {
            return parts;
        }
        parts.valid = true;
        parts.major = major;
        parts.minor = minor;
        return parts;
    } catch (...) {
        return parts;
    }
}

inline bool observation_view_has_field(
    const std::vector<std::string>& fields,
    const std::string& name
) {
    return std::find(fields.begin(), fields.end(), name) != fields.end();
}

inline ObservationViewCompatibilityReport evaluate_observation_view_checkpoint_compatibility(
    const ObservationViewSpec& checkpoint,
    const ObservationViewSpec& provider
) {
    ObservationViewCompatibilityReport report{};
    const ObservationSchemaVersionParts checkpoint_version =
        parse_observation_schema_version(checkpoint.schema_version);
    const ObservationSchemaVersionParts provider_version =
        parse_observation_schema_version(provider.schema_version);

    report.major_compatible = checkpoint_version.valid &&
        provider_version.valid &&
        checkpoint_version.major == provider_version.major;

    for (const auto& field : checkpoint.required_fields) {
        if (!observation_view_has_field(provider.required_fields, field)) {
            report.missing_required_fields.push_back(field);
        }
    }
    report.required_fields_satisfied = report.missing_required_fields.empty();

    for (const auto& field : provider.optional_fields) {
        if (!observation_view_has_field(checkpoint.optional_fields, field)) {
            report.unknown_optional_fields.push_back(field);
        }
    }
    for (const auto& field : checkpoint.optional_fields) {
        if (!observation_view_has_field(provider.optional_fields, field) &&
            !observation_view_has_field(provider.required_fields, field)) {
            report.missing_optional_fields.push_back(field);
        }
    }

    report.optional_field_drift_allowed =
        checkpoint.allow_minor_version_drift &&
        checkpoint.allow_unknown_optional_fields &&
        checkpoint.allow_missing_optional_fields &&
        (report.unknown_optional_fields.empty() || checkpoint.allow_unknown_optional_fields) &&
        (report.missing_optional_fields.empty() || checkpoint.allow_missing_optional_fields);

    report.compatible = report.major_compatible &&
        report.required_fields_satisfied &&
        report.optional_field_drift_allowed;
    return report;
}
