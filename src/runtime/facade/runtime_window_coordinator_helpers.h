#pragma once

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <initializer_list>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

// Internal helper split for runtime_window_coordinator.h.
// Include this companion after the barrier and cadence constants are declared.

inline bool runtime_window_is_blank(std::string_view value) {
    return value.empty() || std::all_of(value.begin(), value.end(), [](unsigned char c) {
        return std::isspace(c) != 0;
    });
}

inline bool runtime_window_is_supported_merge_policy(std::string_view policy) {
    return policy == "last_write_wins" || policy == "reject_on_conflict";
}

inline bool runtime_window_has_payload(const RuntimeWindowActionRequest& request) {
    return request.action_intent.has_pilot_action ||
        request.action_intent.has_mission_command;
}

inline bool runtime_window_has_finite_time(double value) {
    return std::isfinite(value) != 0;
}

inline bool runtime_window_is_supported_clock_merge_policy(std::string_view policy) {
    return policy == "nested_slot" || policy == "hold_last" ||
        policy == "interpolate" || policy == "enqueue_event" ||
        policy == "defer_to_next_window" ||
        policy == "reject_on_ambiguous_order";
}

inline bool runtime_window_is_independent_clock_domain_relation(
    std::string_view relation
) {
    return relation == "independent";
}

inline bool runtime_window_has_selected_barrier_order(
    const std::vector<std::string>& barrier_order
) {
    if (barrier_order.empty()) {
        return false;
    }

    const std::array<std::string_view, 3> selected_barriers = {
        kRuntimeWindowBarrierInputInjection,
        kRuntimeWindowBarrierWindowCommit,
        kRuntimeWindowBarrierExport,
    };
    std::size_t next_index = 0;
    for (const auto& barrier_id : barrier_order) {
        const auto it = std::find(
            selected_barriers.begin() + static_cast<std::ptrdiff_t>(next_index),
            selected_barriers.end(),
            barrier_id
        );
        if (it == selected_barriers.end()) {
            return false;
        }
        next_index = static_cast<std::size_t>(
            std::distance(selected_barriers.begin(), it) + 1
        );
    }
    return true;
}

inline std::vector<std::string> runtime_window_selected_barrier_order() {
    return {
        std::string(kRuntimeWindowBarrierInputInjection),
        std::string(kRuntimeWindowBarrierWindowCommit),
        std::string(kRuntimeWindowBarrierExport),
    };
}

inline std::vector<std::string> runtime_window_partial_barrier_order(
    std::initializer_list<std::string_view> barrier_ids
) {
    std::vector<std::string> barrier_order;
    barrier_order.reserve(barrier_ids.size());
    for (const auto barrier_id : barrier_ids) {
        barrier_order.emplace_back(barrier_id);
    }
    return barrier_order;
}

inline std::string runtime_window_input_source_snapshot_version(
    const RuntimeWindowActionRequest& request
) {
    if (!runtime_window_is_blank(
            request.clock_domain_metadata.source_snapshot_version)) {
        return request.clock_domain_metadata.source_snapshot_version;
    }
    return request.input_snapshot_version;
}

inline double runtime_window_input_source_time_s(
    const RuntimeWindowActionRequest& request,
    double fallback_source_time_s
) {
    if (request.clock_domain_metadata.has_source_time &&
        runtime_window_has_finite_time(
            request.clock_domain_metadata.source_time_s)) {
        return request.clock_domain_metadata.source_time_s;
    }
    if (runtime_window_has_finite_time(request.action_intent.effective_time_s)) {
        return request.action_intent.effective_time_s;
    }
    return fallback_source_time_s;
}

inline std::string runtime_window_input_target_window_id(
    const RuntimeWindowActionRequest& request,
    const RuntimeWindowSchedulingContext& context
) {
    if (!runtime_window_is_blank(request.clock_domain_metadata.target_window_id)) {
        return request.clock_domain_metadata.target_window_id;
    }
    return context.window_id;
}

inline std::vector<std::string> runtime_window_input_barrier_order(
    const RuntimeWindowActionRequest& request,
    std::initializer_list<std::string_view> fallback_barriers
) {
    if (!request.clock_domain_metadata.barrier_order.empty()) {
        return request.clock_domain_metadata.barrier_order;
    }
    return runtime_window_partial_barrier_order(fallback_barriers);
}

inline std::string runtime_window_input_clock_merge_policy(
    const RuntimeWindowActionRequest& request,
    std::string_view fallback_policy
) {
    if (!runtime_window_is_blank(request.clock_domain_metadata.clock_merge_policy)) {
        return request.clock_domain_metadata.clock_merge_policy;
    }
    if (request.cadence_control.enabled) {
        const ActionHoldPolicy hold_policy =
            normalize_action_hold_policy(request.cadence_control.hold_policy);
        if (hold_policy.hold_mode == kActionHoldModeHoldLast) {
            return "hold_last";
        }
        if (hold_policy.hold_mode == kActionHoldModeInterpolate) {
            return "interpolate";
        }
    }
    return std::string(fallback_policy);
}

inline RuntimeWindowCadence runtime_window_make_cadence(
    std::string_view domain,
    std::uint32_t tick_count,
    double interval_s,
    std::string_view merge_policy,
    std::string_view barrier_id
) {
    return RuntimeWindowCadence{
        .domain = std::string(domain),
        .tick_count = tick_count,
        .interval_s = interval_s,
        .merge_policy = std::string(merge_policy),
        .barrier_id = std::string(barrier_id),
    };
}

inline RuntimeWindowCadenceConfig
runtime_window_default_wp17_selected_slice_cadence_config() {
    RuntimeWindowCadenceConfig config{};
    config.window_duration_s = 0.1;
    config.domains = {
        runtime_window_make_cadence(
            kRuntimeWindowCadenceDomainPolicy,
            1U,
            0.1,
            "nested_slot",
            kRuntimeWindowBarrierInputInjection
        ),
        runtime_window_make_cadence(
            kRuntimeWindowCadenceDomainControl,
            2U,
            0.05,
            "hold_last",
            kRuntimeWindowBarrierInputInjection
        ),
        runtime_window_make_cadence(
            kRuntimeWindowCadenceDomainPhysics,
            6U,
            1.0 / 60.0,
            "enqueue_event",
            kRuntimeWindowBarrierWindowCommit
        ),
        runtime_window_make_cadence(
            kRuntimeWindowCadenceDomainExport,
            1U,
            0.1,
            "nested_slot",
            kRuntimeWindowBarrierExport
        ),
    };
    return config;
}

inline std::size_t runtime_window_find_cadence_domain_index(
    const RuntimeWindowCadenceConfig& config,
    std::string_view domain
) {
    const auto it = std::find_if(
        config.domains.begin(),
        config.domains.end(),
        [domain](const RuntimeWindowCadence& cadence) {
            return cadence.domain == domain;
        }
    );
    if (it == config.domains.end()) {
        return config.domains.size();
    }
    return static_cast<std::size_t>(
        std::distance(config.domains.begin(), it)
    );
}

inline const RuntimeWindowCadence* runtime_window_find_cadence_domain(
    const RuntimeWindowCadenceConfig& config,
    std::string_view domain
) {
    const std::size_t index =
        runtime_window_find_cadence_domain_index(config, domain);
    if (index >= config.domains.size()) {
        return nullptr;
    }
    return &config.domains[index];
}

inline void runtime_window_append_default_cadence_domain_if_missing(
    RuntimeWindowCadenceConfig* config,
    const RuntimeWindowCadence& default_cadence
) {
    if (config == nullptr) {
        return;
    }
    if (runtime_window_find_cadence_domain_index(*config, default_cadence.domain) >=
        config->domains.size()) {
        config->domains.push_back(default_cadence);
    }
}

inline RuntimeWindowCadenceConfig normalize_runtime_window_cadence_config(
    const RuntimeWindowRequest& request
) {
    RuntimeWindowCadenceConfig config = request.cadence_config;
    const RuntimeWindowCadenceConfig defaults =
        runtime_window_default_wp17_selected_slice_cadence_config();

    if (!runtime_window_has_finite_time(config.window_duration_s) ||
        config.window_duration_s <= 0.0) {
        config.window_duration_s = defaults.window_duration_s;
    }

    if (config.domains.empty()) {
        return defaults;
    }

    runtime_window_append_default_cadence_domain_if_missing(
        &config,
        defaults.domains[0]
    );
    runtime_window_append_default_cadence_domain_if_missing(
        &config,
        defaults.domains[1]
    );
    runtime_window_append_default_cadence_domain_if_missing(
        &config,
        defaults.domains[2]
    );
    runtime_window_append_default_cadence_domain_if_missing(
        &config,
        defaults.domains[3]
    );

    for (auto& cadence : config.domains) {
        const RuntimeWindowCadence* default_cadence =
            runtime_window_find_cadence_domain(defaults, cadence.domain);
        if (cadence.tick_count == 0U) {
            cadence.tick_count =
                default_cadence != nullptr ? default_cadence->tick_count : 1U;
        }
        if (!runtime_window_has_finite_time(cadence.interval_s) ||
            cadence.interval_s <= 0.0) {
            cadence.interval_s = config.window_duration_s /
                static_cast<double>(cadence.tick_count);
        }
        if (runtime_window_is_blank(cadence.merge_policy) &&
            default_cadence != nullptr) {
            cadence.merge_policy = default_cadence->merge_policy;
        }
        if (runtime_window_is_blank(cadence.barrier_id) &&
            default_cadence != nullptr) {
            cadence.barrier_id = default_cadence->barrier_id;
        }
    }
    return config;
}

inline ActionHoldPolicy runtime_window_normalized_hold_policy(
    const RuntimeWindowActionRequest& request
) {
    return normalize_action_hold_policy(request.cadence_control.hold_policy);
}

inline double runtime_window_resolve_hold_expiry_time_s(
    const RuntimeWindowActionRequest& request,
    double fallback_source_time_s
) {
    if (request.cadence_control.has_expiry_time &&
        runtime_window_has_finite_time(request.cadence_control.expiry_time_s)) {
        return request.cadence_control.expiry_time_s;
    }
    if (request.action_intent.valid_until_s != 0.0 &&
        runtime_window_has_finite_time(request.action_intent.valid_until_s)) {
        return request.action_intent.valid_until_s;
    }
    const ActionHoldPolicy hold_policy =
        runtime_window_normalized_hold_policy(request);
    if (hold_policy.validity_duration_s > 0.0) {
        return runtime_window_input_source_time_s(request, fallback_source_time_s) +
            hold_policy.validity_duration_s;
    }
    return 0.0;
}

inline bool runtime_window_hold_candidate_expired_at_tick(
    const RuntimeWindowActionRequest& request,
    double fallback_source_time_s,
    double tick_time_s
) {
    const double expiry_time_s =
        runtime_window_resolve_hold_expiry_time_s(request, fallback_source_time_s);
    return expiry_time_s != 0.0 && expiry_time_s < tick_time_s;
}

inline bool runtime_window_has_requested_export(
    const RuntimeWindowRequest& request
) {
    return request.export_observation || request.export_engagement ||
        request.export_diagnostics;
}

inline std::string runtime_window_default_id(const RuntimeWindowRequest& request) {
    if (!runtime_window_is_blank(request.window_id)) {
        return request.window_id;
    }
    return "window:" + std::to_string(request.world_id) + ":" +
        std::to_string(request.source_time_s);
}
