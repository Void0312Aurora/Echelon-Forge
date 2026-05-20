#pragma once

#include <algorithm>
#include <cstdint>
#include <string>
#include <vector>

struct RewardTerm {
    std::string name;
    double value = 0.0;
    std::string term_owner = "simulation";
};

struct RewardReport {
    std::vector<RewardTerm> fact_terms;
    std::vector<RewardTerm> shaping_terms;
    std::uint64_t fact_snapshot_version = 0;
    std::string term_owner = "split";
};

struct TerminationSpec {
    std::string reason = "running";
    std::string reason_source = "simulation";
    std::uint64_t snapshot_version = 0;
};

struct ObservationViewSpec {
    std::string schema_version = "1.0";
    std::vector<std::string> required_fields;
    std::vector<std::string> optional_fields;
    bool reject_major_mismatch = true;
    bool allow_minor_version_drift = true;
    bool allow_unknown_optional_fields = true;
    bool allow_missing_optional_fields = true;
};

struct ObservationViewCompatibilityReport {
    bool compatible = false;
    bool major_compatible = false;
    bool required_fields_satisfied = false;
    bool optional_field_drift_allowed = false;
    std::vector<std::string> missing_required_fields;
    std::vector<std::string> unknown_optional_fields;
    std::vector<std::string> missing_optional_fields;
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
