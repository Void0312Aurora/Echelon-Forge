from __future__ import annotations

import textwrap

from tests.architecture.helpers import REPO_ROOT, compile_cpp_snippet

VALIDATOR_HEADER = (
    REPO_ROOT / "src" / "core" / "engine" / "same_window_edge_validation.h"
)


def _compile_and_run(source: str):
    return compile_cpp_snippet(source, binary_prefix="causal_same_window_edge")


def test_same_window_validator_header_exists() -> None:
    assert VALIDATOR_HEADER.is_file()


def test_same_window_edge_validation_passes_for_declared_stage_family_edge() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <vector>
        #include "core/engine/same_window_edge_validation.h"

        int main() {
            using namespace runtime::scheduler;
            const std::vector<StageNodeManifest> registry = {
                StageNodeManifest{
                    .node_id = "p7.same_window_launch.v1",
                    .semantic_stage = {"P7 FireControlLaunch"},
                    .owner_module = "tests",
                    .input_packets = {"LaunchRequest"},
                    .output_packets = {"LaunchEvent"},
                    .read_state_shards = {"track"},
                    .write_state_shards = {"engagement"},
                    .read_snapshot_policy = std::string(kReadSnapshotPolicyPostInjection),
                    .write_commit_policy = std::string(kWriteCommitPolicyStagePublish),
                    .clock_domain = "event_driven",
                    .latency_policy = "same_window_publish",
                    .sync_policy = "host_owned",
                    .allowed_same_window_edges = {"p10"},
                    .required_barriers = {"input_injection", "stage_publish"},
                    .event_families_emitted = {"fire_control_and_launch"},
                    .diagnostic_trace_obligations = {"launch_event_id"},
                    .facade_visibility = std::string(kFacadeVisibilityInternal),
                    .compatibility_adapter_allowed = false,
                },
                StageNodeManifest{
                    .node_id = "p10.same_window_export.v1",
                    .semantic_stage = {"P10 ObservationExport"},
                    .owner_module = "tests",
                    .input_packets = {"LaunchEvent"},
                    .output_packets = {"ObservationBatchPacket"},
                    .read_state_shards = {"engagement"},
                    .write_state_shards = {"observation"},
                    .read_snapshot_policy = std::string(kReadSnapshotPolicySameWindow),
                    .write_commit_policy = std::string(kWriteCommitPolicyExportOnly),
                    .clock_domain = "window_export",
                    .latency_policy = "same_window_read",
                    .sync_policy = "explicit_export",
                    .allowed_same_window_edges = {},
                    .required_barriers = {"stage_publish", "export"},
                    .event_families_emitted = {"observation_and_export"},
                    .diagnostic_trace_obligations = {"source_snapshot_version"},
                    .facade_visibility = std::string(kFacadeVisibilityMaintainedExport),
                    .compatibility_adapter_allowed = false,
                },
            };

            const SameWindowValidationResult result =
                validate_schedule_construction_same_window_edges(
                    registry,
                    {SameWindowEdge{
                        .producer_node_id = "p7.same_window_launch.v1",
                        .consumer_node_id = "p10.same_window_export.v1",
                    }}
                );

            if (!result.valid) {
                std::cerr << "expected pass fixture to validate\n";
                for (const auto& issue : result.issues) {
                    std::cerr << same_window_edge_error_code_name(issue.code)
                              << ": " << issue.message << "\n";
                }
                return 1;
            }
            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_same_window_edge_validation_fails_when_producer_does_not_name_consumer() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "core/engine/same_window_edge_validation.h"

        int main() {
            using namespace runtime::scheduler;
            const std::vector<StageNodeManifest> registry = {
                StageNodeManifest{
                    .node_id = "producer.v1",
                    .semantic_stage = {"P7 FireControlLaunch"},
                    .owner_module = "tests",
                    .input_packets = {"LaunchRequest"},
                    .output_packets = {"LaunchEvent"},
                    .read_state_shards = {"track"},
                    .write_state_shards = {"engagement"},
                    .read_snapshot_policy = std::string(kReadSnapshotPolicyPostInjection),
                    .write_commit_policy = std::string(kWriteCommitPolicyStagePublish),
                    .clock_domain = "event_driven",
                    .latency_policy = "same_window_publish",
                    .sync_policy = "host_owned",
                    .allowed_same_window_edges = {"p9"},
                    .required_barriers = {"input_injection", "stage_publish"},
                    .event_families_emitted = {"fire_control_and_launch"},
                    .diagnostic_trace_obligations = {"launch_event_id"},
                    .facade_visibility = std::string(kFacadeVisibilityInternal),
                    .compatibility_adapter_allowed = false,
                },
                StageNodeManifest{
                    .node_id = "consumer.v1",
                    .semantic_stage = {"P10 ObservationExport"},
                    .owner_module = "tests",
                    .input_packets = {"LaunchEvent"},
                    .output_packets = {"ObservationBatchPacket"},
                    .read_state_shards = {"engagement"},
                    .write_state_shards = {"observation"},
                    .read_snapshot_policy = std::string(kReadSnapshotPolicySameWindow),
                    .write_commit_policy = std::string(kWriteCommitPolicyExportOnly),
                    .clock_domain = "window_export",
                    .latency_policy = "same_window_read",
                    .sync_policy = "explicit_export",
                    .allowed_same_window_edges = {},
                    .required_barriers = {"stage_publish", "export"},
                    .event_families_emitted = {"observation_and_export"},
                    .diagnostic_trace_obligations = {"source_snapshot_version"},
                    .facade_visibility = std::string(kFacadeVisibilityMaintainedExport),
                    .compatibility_adapter_allowed = false,
                },
            };

            const SameWindowValidationResult result =
                validate_schedule_construction_same_window_edges(
                    registry,
                    {SameWindowEdge{
                        .producer_node_id = "producer.v1",
                        .consumer_node_id = "consumer.v1",
                    }}
                );

            if (result.valid || result.issues.size() != 1) {
                std::cerr << "expected single allowlist failure\n";
                return 1;
            }
            const auto& issue = result.issues.front();
            if (issue.code != SameWindowEdgeErrorCode::producer_does_not_allow_consumer) {
                std::cerr << "unexpected code: "
                          << same_window_edge_error_code_name(issue.code) << "\n";
                return 1;
            }
            if (issue.message.find("allowed_same_window_edges") == std::string::npos) {
                std::cerr << "missing stable allowlist message\n";
                return 1;
            }
            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_same_window_edge_validation_fails_when_read_write_sets_do_not_intersect() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "core/engine/same_window_edge_validation.h"

        int main() {
            using namespace runtime::scheduler;
            const std::vector<StageNodeManifest> registry = {
                StageNodeManifest{
                    .node_id = "producer.v1",
                    .semantic_stage = {"P7 FireControlLaunch"},
                    .owner_module = "tests",
                    .input_packets = {"LaunchRequest"},
                    .output_packets = {"LaunchEvent"},
                    .read_state_shards = {"track"},
                    .write_state_shards = {"engagement"},
                    .read_snapshot_policy = std::string(kReadSnapshotPolicyPostInjection),
                    .write_commit_policy = std::string(kWriteCommitPolicyStagePublish),
                    .clock_domain = "event_driven",
                    .latency_policy = "same_window_publish",
                    .sync_policy = "host_owned",
                    .allowed_same_window_edges = {"consumer.v1"},
                    .required_barriers = {"input_injection", "stage_publish"},
                    .event_families_emitted = {"fire_control_and_launch"},
                    .diagnostic_trace_obligations = {"launch_event_id"},
                    .facade_visibility = std::string(kFacadeVisibilityInternal),
                    .compatibility_adapter_allowed = false,
                },
                StageNodeManifest{
                    .node_id = "consumer.v1",
                    .semantic_stage = {"P10 ObservationExport"},
                    .owner_module = "tests",
                    .input_packets = {"DamageReport"},
                    .output_packets = {"ObservationBatchPacket"},
                    .read_state_shards = {"damage"},
                    .write_state_shards = {"observation"},
                    .read_snapshot_policy = std::string(kReadSnapshotPolicySameWindow),
                    .write_commit_policy = std::string(kWriteCommitPolicyExportOnly),
                    .clock_domain = "window_export",
                    .latency_policy = "same_window_read",
                    .sync_policy = "explicit_export",
                    .allowed_same_window_edges = {},
                    .required_barriers = {"stage_publish", "export"},
                    .event_families_emitted = {"observation_and_export"},
                    .diagnostic_trace_obligations = {"source_snapshot_version"},
                    .facade_visibility = std::string(kFacadeVisibilityMaintainedExport),
                    .compatibility_adapter_allowed = false,
                },
            };

            const SameWindowValidationResult result =
                validate_schedule_construction_same_window_edges(
                    registry,
                    {SameWindowEdge{
                        .producer_node_id = "producer.v1",
                        .consumer_node_id = "consumer.v1",
                    }}
                );

            if (result.valid || result.issues.size() != 1) {
                std::cerr << "expected single no-shared-contract failure\n";
                return 1;
            }
            if (result.issues.front().code != SameWindowEdgeErrorCode::no_shared_contract) {
                std::cerr << "unexpected code\n";
                return 1;
            }
            if (result.issues.front().message.find("share at least one output packet") ==
                std::string::npos) {
                std::cerr << "missing shared-contract message\n";
                return 1;
            }
            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_same_window_edge_validation_fails_when_consumer_omits_stage_publish_barrier() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "core/engine/same_window_edge_validation.h"

        int main() {
            using namespace runtime::scheduler;
            const std::vector<StageNodeManifest> registry = {
                StageNodeManifest{
                    .node_id = "producer.v1",
                    .semantic_stage = {"P7 FireControlLaunch"},
                    .owner_module = "tests",
                    .input_packets = {"LaunchRequest"},
                    .output_packets = {"LaunchEvent"},
                    .read_state_shards = {"track"},
                    .write_state_shards = {"engagement"},
                    .read_snapshot_policy = std::string(kReadSnapshotPolicyPostInjection),
                    .write_commit_policy = std::string(kWriteCommitPolicyStagePublish),
                    .clock_domain = "event_driven",
                    .latency_policy = "same_window_publish",
                    .sync_policy = "host_owned",
                    .allowed_same_window_edges = {"consumer.v1"},
                    .required_barriers = {"input_injection", "stage_publish"},
                    .event_families_emitted = {"fire_control_and_launch"},
                    .diagnostic_trace_obligations = {"launch_event_id"},
                    .facade_visibility = std::string(kFacadeVisibilityInternal),
                    .compatibility_adapter_allowed = false,
                },
                StageNodeManifest{
                    .node_id = "consumer.v1",
                    .semantic_stage = {"P10 ObservationExport"},
                    .owner_module = "tests",
                    .input_packets = {"LaunchEvent"},
                    .output_packets = {"ObservationBatchPacket"},
                    .read_state_shards = {"engagement"},
                    .write_state_shards = {"observation"},
                    .read_snapshot_policy = std::string(kReadSnapshotPolicySameWindow),
                    .write_commit_policy = std::string(kWriteCommitPolicyExportOnly),
                    .clock_domain = "window_export",
                    .latency_policy = "same_window_read",
                    .sync_policy = "explicit_export",
                    .allowed_same_window_edges = {},
                    .required_barriers = {"export"},
                    .event_families_emitted = {"observation_and_export"},
                    .diagnostic_trace_obligations = {"source_snapshot_version"},
                    .facade_visibility = std::string(kFacadeVisibilityMaintainedExport),
                    .compatibility_adapter_allowed = false,
                },
            };

            const SameWindowValidationResult result =
                validate_schedule_construction_same_window_edges(
                    registry,
                    {SameWindowEdge{
                        .producer_node_id = "producer.v1",
                        .consumer_node_id = "consumer.v1",
                    }}
                );

            if (result.valid || result.issues.size() != 1) {
                std::cerr << "expected single barrier failure\n";
                return 1;
            }
            if (result.issues.front().code !=
                SameWindowEdgeErrorCode::consumer_missing_stage_publish_barrier) {
                std::cerr << "unexpected code\n";
                return 1;
            }
            if (result.issues.front().message.find("required_barriers") == std::string::npos) {
                std::cerr << "missing barrier message\n";
                return 1;
            }
            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_same_window_edge_validation_fails_on_cycle() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "core/engine/same_window_edge_validation.h"

        int main() {
            using namespace runtime::scheduler;
            const std::vector<StageNodeManifest> registry = {
                StageNodeManifest{
                    .node_id = "producer_a.v1",
                    .semantic_stage = {"P7 FireControlLaunch"},
                    .owner_module = "tests",
                    .input_packets = {"DamageReport"},
                    .output_packets = {"LaunchEvent"},
                    .read_state_shards = {"damage"},
                    .write_state_shards = {"engagement"},
                    .read_snapshot_policy = std::string(kReadSnapshotPolicySameWindow),
                    .write_commit_policy = std::string(kWriteCommitPolicyStagePublish),
                    .clock_domain = "event_driven",
                    .latency_policy = "same_window_publish",
                    .sync_policy = "host_owned",
                    .allowed_same_window_edges = {"producer_b.v1"},
                    .required_barriers = {"stage_publish"},
                    .event_families_emitted = {"fire_control_and_launch"},
                    .diagnostic_trace_obligations = {"launch_event_id"},
                    .facade_visibility = std::string(kFacadeVisibilityInternal),
                    .compatibility_adapter_allowed = false,
                },
                StageNodeManifest{
                    .node_id = "producer_b.v1",
                    .semantic_stage = {"P9 EffectsDamage"},
                    .owner_module = "tests",
                    .input_packets = {"LaunchEvent"},
                    .output_packets = {"DamageReport"},
                    .read_state_shards = {"engagement"},
                    .write_state_shards = {"damage"},
                    .read_snapshot_policy = std::string(kReadSnapshotPolicySameWindow),
                    .write_commit_policy = std::string(kWriteCommitPolicyStagePublish),
                    .clock_domain = "event_driven",
                    .latency_policy = "same_window_publish",
                    .sync_policy = "host_owned",
                    .allowed_same_window_edges = {"producer_a.v1"},
                    .required_barriers = {"stage_publish"},
                    .event_families_emitted = {"effects_and_damage"},
                    .diagnostic_trace_obligations = {"damage_report_id"},
                    .facade_visibility = std::string(kFacadeVisibilityInternal),
                    .compatibility_adapter_allowed = false,
                },
            };

            const SameWindowValidationResult result =
                validate_schedule_construction_same_window_edges(
                    registry,
                    {
                        SameWindowEdge{
                            .producer_node_id = "producer_a.v1",
                            .consumer_node_id = "producer_b.v1",
                        },
                        SameWindowEdge{
                            .producer_node_id = "producer_b.v1",
                            .consumer_node_id = "producer_a.v1",
                        },
                    }
                );

            if (result.valid || result.issues.size() != 1) {
                std::cerr << "expected single cycle failure\n";
                return 1;
            }
            if (result.issues.front().code != SameWindowEdgeErrorCode::cycle_detected) {
                std::cerr << "unexpected code\n";
                return 1;
            }
            if (result.issues.front().message.find("introduces a cycle") ==
                std::string::npos) {
                std::cerr << "missing cycle message\n";
                return 1;
            }
            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_same_window_edge_validation_fails_for_window_commit_only_producer() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "core/engine/same_window_edge_validation.h"

        int main() {
            using namespace runtime::scheduler;
            const std::vector<StageNodeManifest> registry = {
                StageNodeManifest{
                    .node_id = "producer.v1",
                    .semantic_stage = {"P7 FireControlLaunch"},
                    .owner_module = "tests",
                    .input_packets = {"LaunchRequest"},
                    .output_packets = {"LaunchEvent"},
                    .read_state_shards = {"track"},
                    .write_state_shards = {"engagement"},
                    .read_snapshot_policy = std::string(kReadSnapshotPolicyPostInjection),
                    .write_commit_policy = std::string(kWriteCommitPolicyWindowCommit),
                    .clock_domain = "event_driven",
                    .latency_policy = "window_commit_only",
                    .sync_policy = "host_owned",
                    .allowed_same_window_edges = {"consumer.v1"},
                    .required_barriers = {"input_injection", "window_commit"},
                    .event_families_emitted = {"fire_control_and_launch"},
                    .diagnostic_trace_obligations = {"launch_event_id"},
                    .facade_visibility = std::string(kFacadeVisibilityInternal),
                    .compatibility_adapter_allowed = false,
                },
                StageNodeManifest{
                    .node_id = "consumer.v1",
                    .semantic_stage = {"P10 ObservationExport"},
                    .owner_module = "tests",
                    .input_packets = {"LaunchEvent"},
                    .output_packets = {"ObservationBatchPacket"},
                    .read_state_shards = {"engagement"},
                    .write_state_shards = {"observation"},
                    .read_snapshot_policy = std::string(kReadSnapshotPolicySameWindow),
                    .write_commit_policy = std::string(kWriteCommitPolicyExportOnly),
                    .clock_domain = "window_export",
                    .latency_policy = "same_window_read",
                    .sync_policy = "explicit_export",
                    .allowed_same_window_edges = {},
                    .required_barriers = {"stage_publish", "export"},
                    .event_families_emitted = {"observation_and_export"},
                    .diagnostic_trace_obligations = {"source_snapshot_version"},
                    .facade_visibility = std::string(kFacadeVisibilityMaintainedExport),
                    .compatibility_adapter_allowed = false,
                },
            };

            const SameWindowValidationResult result =
                validate_schedule_construction_same_window_edges(
                    registry,
                    {SameWindowEdge{
                        .producer_node_id = "producer.v1",
                        .consumer_node_id = "consumer.v1",
                    }}
                );

            if (result.valid || result.issues.size() != 1) {
                std::cerr << "expected single stage_publish failure\n";
                return 1;
            }
            if (result.issues.front().code !=
                SameWindowEdgeErrorCode::producer_not_stage_publish) {
                std::cerr << "unexpected code\n";
                return 1;
            }
            if (result.issues.front().message.find("write_commit_policy stage_publish") ==
                std::string::npos) {
                std::cerr << "missing stage_publish message\n";
                return 1;
            }
            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout
