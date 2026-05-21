from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HEADER = REPO_ROOT / "src" / "runtime" / "contracts" / "stage_node_manifest_registry.h"


def _compile_and_run(source: str) -> subprocess.CompletedProcess[str]:
    command = [
        "g++",
        "-std=c++20",
        "-I",
        str(REPO_ROOT / "src"),
        "-x",
        "c++",
        "-",
        "-o",
        "/tmp/wp10_manifest_registry_test_bin",
    ]
    compile_result = subprocess.run(
        command,
        input=source,
        text=True,
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
    )
    assert compile_result.returncode == 0, compile_result.stderr

    run_result = subprocess.run(
        ["/tmp/wp10_manifest_registry_test_bin"],
        text=True,
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
    )
    return run_result


def test_wp10_stage_node_manifest_registry_header_exists_in_runtime_contracts() -> None:
    assert HEADER.is_file()


def test_wp10_registry_seed_spells_out_required_fields_for_each_maintained_node() -> None:
    header_text = HEADER.read_text(encoding="utf-8")
    required_fields = [
        ".semantic_stage =",
        ".owner_module =",
        ".input_packets =",
        ".output_packets =",
        ".read_state_shards =",
        ".write_state_shards =",
        ".read_snapshot_policy =",
        ".write_commit_policy =",
        ".clock_domain =",
        ".latency_policy =",
        ".sync_policy =",
        ".required_barriers =",
        ".event_families_emitted =",
        ".diagnostic_trace_obligations =",
        ".facade_visibility =",
        ".compatibility_adapter_allowed =",
    ]
    for node_id in (
        "p7.fire_control_launch.v1",
        "p9.effects_damage.v1",
        "p10.observation_export.v1",
    ):
        marker = f'.node_id = "{node_id}"'
        assert marker in header_text, f"missing registry seed for {node_id}"
        block = header_text.split(marker, 1)[1].split("StageNodeManifest{", 1)[0]
        for field in required_fields:
            assert field in block, f"{node_id} missing {field}"


def test_wp10_registry_seed_enumerates_required_maintained_node_ids() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <vector>
        #include "runtime/contracts/stage_node_manifest_registry.h"

        int main() {
            using namespace runtime::scheduler;
            const auto manifests = enumerate_wp10_maintained_stage_node_manifests();
            std::vector<std::string> ids;
            for (const auto* manifest : manifests) {
                ids.push_back(manifest->node_id);
            }

            for (const auto& expected : {
                     std::string("p7.fire_control_launch.v1"),
                     std::string("p9.effects_damage.v1"),
                     std::string("p10.observation_export.v1"),
                 }) {
                if (std::find(ids.begin(), ids.end(), expected) == ids.end()) {
                    std::cerr << "missing maintained node: " << expected << "\n";
                    return 1;
                }
            }

            if (manifests.size() != 3) {
                std::cerr << "unexpected maintained node count: " << manifests.size() << "\n";
                return 1;
            }

            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp10_registry_seed_validates_cleanly_and_keeps_clock_domain_advisory() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/stage_node_manifest_registry.h"

        int main() {
            using namespace runtime::scheduler;
            if (!kWp10ClockDomainAdvisoryOnly) {
                std::cerr << "clock domain flag drifted\n";
                return 1;
            }

            const auto result = validate_wp10_stage_node_manifest_registry_seed();
            if (result.has_value()) {
                std::cerr << "registry should validate cleanly\n";
                for (const auto& error : result->errors) {
                    std::cerr << error << "\n";
                }
                return 1;
            }
            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_missing_required_fields_fail_closed() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/stage_node_manifest_registry.h"

        int main() {
            using namespace runtime::scheduler;
            StageNodeManifest manifest{};
            manifest.node_id = "broken.node";
            manifest.semantic_stage = {"P7 FireControlLaunch"};

            const auto result = validate_stage_node_manifest(manifest);
            if (result.valid) {
                std::cerr << "manifest unexpectedly passed validation\n";
                return 1;
            }

            bool saw_owner = false;
            bool saw_inputs = false;
            bool saw_facade = false;
            for (const auto& error : result.errors) {
                saw_owner = saw_owner || error.find("owner_module") != std::string::npos;
                saw_inputs = saw_inputs || error.find("input_packets") != std::string::npos;
                saw_facade = saw_facade || error.find("facade_visibility") != std::string::npos;
            }

            if (!saw_owner || !saw_inputs || !saw_facade) {
                std::cerr << "missing expected fail-closed errors\n";
                return 1;
            }
            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_same_window_publish_claim_requires_allowed_same_window_edges() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/stage_node_manifest_registry.h"

        int main() {
            using namespace runtime::scheduler;
            StageNodeManifest manifest{
                .node_id = "same.window.publisher",
                .semantic_stage = {"P7 FireControlLaunch"},
                .owner_module = "tests",
                .input_packets = {"LaunchRequest"},
                .output_packets = {"LaunchEvent"},
                .read_state_shards = {"engagement"},
                .write_state_shards = {"engagement"},
                .read_snapshot_policy = std::string(kReadSnapshotPolicyPostInjection),
                .write_commit_policy = std::string(kWriteCommitPolicyStagePublish),
                .clock_domain = "event_driven",
                .latency_policy = "same_window_after_request_barrier",
                .sync_policy = "host_owned",
                .allowed_same_window_edges = {},
                .required_barriers = {"input_injection", "stage_publish"},
                .event_families_emitted = {"fire_control_and_launch"},
                .diagnostic_trace_obligations = {"launch_event_id"},
                .facade_visibility = std::string(kFacadeVisibilityInternal),
                .compatibility_adapter_allowed = false,
            };

            const auto result = validate_stage_node_manifest(manifest);
            if (result.valid) {
                std::cerr << "same-window publish unexpectedly passed\n";
                return 1;
            }

            for (const auto& error : result.errors) {
                if (error.find("allowed_same_window_edges") != std::string::npos) {
                    return 0;
                }
            }

            std::cerr << "missing allowed_same_window_edges error\n";
            return 1;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_compatibility_and_diagnostics_nodes_are_not_maintained_scheduler_truth() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <vector>
        #include "runtime/contracts/stage_node_manifest_registry.h"

        int main() {
            using namespace runtime::scheduler;
            const auto* compatibility =
                find_stage_node_manifest("p7.launch_request_adapter_compat.v1");
            const auto* diagnostics =
                find_stage_node_manifest("p10.observation_trace_diagnostics.v1");

            if (compatibility == nullptr || diagnostics == nullptr) {
                std::cerr << "missing non-maintained registry entries\n";
                return 1;
            }
            if (is_maintained_scheduler_truth(*compatibility)) {
                std::cerr << "compatibility node drifted into maintained truth\n";
                return 1;
            }
            if (is_maintained_scheduler_truth(*diagnostics)) {
                std::cerr << "diagnostics node drifted into maintained truth\n";
                return 1;
            }

            const auto manifests = enumerate_wp10_maintained_stage_node_manifests();
            for (const auto* manifest : manifests) {
                if (manifest->node_id == compatibility->node_id ||
                    manifest->node_id == diagnostics->node_id) {
                    std::cerr << "non-maintained node leaked into maintained list\n";
                    return 1;
                }
            }
            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp17_selected_slice_strict_helper_does_not_change_wp10_maintained_count() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <vector>
        #include "runtime/contracts/stage_node_manifest_registry.h"

        int main() {
            using namespace runtime::scheduler;
            const auto maintained = enumerate_wp10_maintained_stage_node_manifests();
            const auto selected = enumerate_wp17_selected_slice_strict_clock_domain_manifests();

            if (maintained.size() != 3) {
                std::cerr << "wp10 maintained count drifted\n";
                return 1;
            }
            if (selected.size() != 3) {
                std::cerr << "wp17 selected-slice strict helper should expose exactly three nodes\n";
                return 1;
            }
            for (const auto* manifest : selected) {
                if (manifest == nullptr) {
                    std::cerr << "null selected-slice manifest\n";
                    return 1;
                }
                if (!is_wp17_selected_slice_strict_clock_domain_node(*manifest)) {
                    std::cerr << "helper returned a non-selected node\n";
                    return 1;
                }
            }
            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_event_emitting_nodes_declare_event_family_and_diagnostics_obligations() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/stage_node_manifest_registry.h"

        int main() {
            using namespace runtime::scheduler;
            for (const auto* manifest : enumerate_wp10_maintained_stage_node_manifests()) {
                if (!declares_event_like_outputs(*manifest)) {
                    continue;
                }
                if (manifest->event_families_emitted.empty()) {
                    std::cerr << manifest->node_id << " missing event family\n";
                    return 1;
                }
                if (manifest->diagnostic_trace_obligations.empty()) {
                    std::cerr << manifest->node_id << " missing diagnostics obligations\n";
                    return 1;
                }
            }
            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout
