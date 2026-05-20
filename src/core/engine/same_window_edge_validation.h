#pragma once

#include <algorithm>
#include <cctype>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

#include "runtime/contracts/stage_node_manifest_registry.h"

namespace runtime::scheduler {

struct SameWindowEdge {
    std::string producer_node_id;
    std::string consumer_node_id;
};

enum class SameWindowEdgeErrorCode {
    unknown_producer,
    unknown_consumer,
    producer_not_stage_publish,
    producer_does_not_allow_consumer,
    consumer_not_same_window,
    consumer_missing_stage_publish_barrier,
    no_shared_contract,
    cycle_detected,
};

struct SameWindowValidationIssue {
    SameWindowEdge edge;
    SameWindowEdgeErrorCode code = SameWindowEdgeErrorCode::unknown_producer;
    std::string message;
};

struct SameWindowValidationResult {
    bool valid = true;
    std::vector<SameWindowValidationIssue> issues;

    void add_issue(
        SameWindowEdge edge,
        SameWindowEdgeErrorCode code,
        std::string message
    ) {
        valid = false;
        issues.push_back(SameWindowValidationIssue{
            .edge = std::move(edge),
            .code = code,
            .message = std::move(message),
        });
    }
};

inline std::string same_window_edge_error_code_name(
    SameWindowEdgeErrorCode code
) {
    switch (code) {
    case SameWindowEdgeErrorCode::unknown_producer:
        return "unknown_producer";
    case SameWindowEdgeErrorCode::unknown_consumer:
        return "unknown_consumer";
    case SameWindowEdgeErrorCode::producer_not_stage_publish:
        return "producer_not_stage_publish";
    case SameWindowEdgeErrorCode::producer_does_not_allow_consumer:
        return "producer_does_not_allow_consumer";
    case SameWindowEdgeErrorCode::consumer_not_same_window:
        return "consumer_not_same_window";
    case SameWindowEdgeErrorCode::consumer_missing_stage_publish_barrier:
        return "consumer_missing_stage_publish_barrier";
    case SameWindowEdgeErrorCode::no_shared_contract:
        return "no_shared_contract";
    case SameWindowEdgeErrorCode::cycle_detected:
        return "cycle_detected";
    }

    return "unknown_same_window_edge_error";
}

inline std::string normalize_stage_family_token(std::string_view semantic_stage) {
    std::string token;
    for (const char c : semantic_stage) {
        if (std::isspace(static_cast<unsigned char>(c)) != 0) {
            break;
        }
        token.push_back(static_cast<char>(
            std::tolower(static_cast<unsigned char>(c))
        ));
    }
    return token;
}

inline std::vector<std::string> stage_family_tokens(
    const StageNodeManifest& manifest
) {
    std::vector<std::string> tokens;
    tokens.reserve(manifest.semantic_stage.size());
    for (const auto& semantic_stage : manifest.semantic_stage) {
        std::string token = normalize_stage_family_token(semantic_stage);
        if (!token.empty() && !contains_value(tokens, token)) {
            tokens.push_back(std::move(token));
        }
    }
    return tokens;
}

inline const StageNodeManifest* find_stage_node_manifest(
    const std::vector<StageNodeManifest>& registry,
    std::string_view node_id
) {
    const auto it = std::find_if(
        registry.begin(),
        registry.end(),
        [node_id](const StageNodeManifest& manifest) {
            return manifest.node_id == node_id;
        }
    );
    if (it == registry.end()) {
        return nullptr;
    }
    return &(*it);
}

inline bool producer_allows_same_window_consumer(
    const StageNodeManifest& producer,
    const StageNodeManifest& consumer
) {
    if (contains_value(producer.allowed_same_window_edges, consumer.node_id)) {
        return true;
    }

    for (const auto& token : stage_family_tokens(consumer)) {
        if (contains_value(producer.allowed_same_window_edges, token)) {
            return true;
        }
    }

    return false;
}

inline bool manifests_share_same_window_contract(
    const StageNodeManifest& producer,
    const StageNodeManifest& consumer
) {
    for (const auto& packet : producer.output_packets) {
        if (contains_value(consumer.input_packets, packet) ||
            contains_value(consumer.read_state_shards, packet)) {
            return true;
        }
    }

    for (const auto& shard : producer.write_state_shards) {
        if (contains_value(consumer.input_packets, shard) ||
            contains_value(consumer.read_state_shards, shard)) {
            return true;
        }
    }

    return false;
}

inline bool has_path_between_nodes(
    const std::unordered_map<std::string, std::vector<std::string>>& adjacency,
    std::string_view start,
    std::string_view target
) {
    if (start == target) {
        return true;
    }

    std::vector<std::string> stack = {std::string(start)};
    std::vector<std::string> visited;

    while (!stack.empty()) {
        const std::string node = stack.back();
        stack.pop_back();

        if (contains_value(visited, node)) {
            continue;
        }
        visited.push_back(node);

        const auto it = adjacency.find(node);
        if (it == adjacency.end()) {
            continue;
        }

        for (const auto& next : it->second) {
            if (next == target) {
                return true;
            }
            if (!contains_value(visited, next)) {
                stack.push_back(next);
            }
        }
    }

    return false;
}

inline SameWindowValidationResult validate_schedule_construction_same_window_edges(
    const std::vector<StageNodeManifest>& registry,
    const std::vector<SameWindowEdge>& declared_edges
) {
    SameWindowValidationResult result{};
    std::unordered_map<std::string, std::vector<std::string>> adjacency;

    for (const auto& edge : declared_edges) {
        const StageNodeManifest* producer =
            find_stage_node_manifest(registry, edge.producer_node_id);
        if (producer == nullptr) {
            result.add_issue(
                edge,
                SameWindowEdgeErrorCode::unknown_producer,
                "producer node_id '" + edge.producer_node_id +
                    "' was not found in the stage manifest registry"
            );
            continue;
        }

        const StageNodeManifest* consumer =
            find_stage_node_manifest(registry, edge.consumer_node_id);
        if (consumer == nullptr) {
            result.add_issue(
                edge,
                SameWindowEdgeErrorCode::unknown_consumer,
                "consumer node_id '" + edge.consumer_node_id +
                    "' was not found in the stage manifest registry"
            );
            continue;
        }

        bool edge_valid = true;

        if (producer->write_commit_policy != kWriteCommitPolicyStagePublish) {
            result.add_issue(
                edge,
                SameWindowEdgeErrorCode::producer_not_stage_publish,
                "producer node_id '" + producer->node_id +
                    "' must declare write_commit_policy stage_publish for "
                    "same-window edges"
            );
            edge_valid = false;
        }

        if (!producer_allows_same_window_consumer(*producer, *consumer)) {
            result.add_issue(
                edge,
                SameWindowEdgeErrorCode::producer_does_not_allow_consumer,
                "producer node_id '" + producer->node_id +
                    "' must name consumer node_id '" + consumer->node_id +
                    "' or one of its stage family tokens in "
                    "allowed_same_window_edges"
            );
            edge_valid = false;
        }

        if (consumer->read_snapshot_policy != kReadSnapshotPolicySameWindow) {
            result.add_issue(
                edge,
                SameWindowEdgeErrorCode::consumer_not_same_window,
                "consumer node_id '" + consumer->node_id +
                    "' must declare read_snapshot_policy same_window"
            );
            edge_valid = false;
        }

        if (!contains_value(consumer->required_barriers, "stage_publish")) {
            result.add_issue(
                edge,
                SameWindowEdgeErrorCode::consumer_missing_stage_publish_barrier,
                "consumer node_id '" + consumer->node_id +
                    "' must include stage_publish in required_barriers"
            );
            edge_valid = false;
        }

        if (!manifests_share_same_window_contract(*producer, *consumer)) {
            result.add_issue(
                edge,
                SameWindowEdgeErrorCode::no_shared_contract,
                "producer node_id '" + producer->node_id +
                    "' must share at least one output packet or written shard "
                    "with consumer node_id '" + consumer->node_id + "'"
            );
            edge_valid = false;
        }

        if (!edge_valid) {
            continue;
        }

        if (has_path_between_nodes(
                adjacency,
                edge.consumer_node_id,
                edge.producer_node_id
            )) {
            result.add_issue(
                edge,
                SameWindowEdgeErrorCode::cycle_detected,
                "declared same-window edge '" + edge.producer_node_id + " -> " +
                    edge.consumer_node_id +
                    "' introduces a cycle in the window graph"
            );
            continue;
        }

        adjacency[edge.producer_node_id].push_back(edge.consumer_node_id);
    }

    return result;
}

}  // namespace runtime::scheduler
