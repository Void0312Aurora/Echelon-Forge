from __future__ import annotations

import subprocess
import tempfile
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HEADER = (
    REPO_ROOT
    / "src"
    / "runtime"
    / "contracts"
    / "counterfactual_replay_contracts.h"
)


def _compile_and_run(source: str) -> subprocess.CompletedProcess[str]:
    binary = Path(tempfile.gettempdir()) / "wp15_replay_envelope_contracts_test_bin"
    compile_result = subprocess.run(
        [
            "g++",
            "-std=c++20",
            "-I",
            str(REPO_ROOT / "src"),
            "-x",
            "c++",
            "-",
            "-o",
            str(binary),
        ],
        input=source,
        text=True,
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
    )
    assert compile_result.returncode == 0, compile_result.stderr
    return subprocess.run(
        [str(binary)],
        text=True,
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
    )


def test_wp15_replay_contract_header_exists_under_runtime_contracts() -> None:
    assert HEADER.is_file()


def test_wp15_replay_contract_header_declares_required_surface_and_restore_boundary() -> None:
    text = HEADER.read_text(encoding="utf-8")

    for symbol in (
        "struct ReplayEnvelope",
        "struct BranchPoint",
        "struct ReplaySnapshotRef",
        "struct ReplayBarrierRef",
        "struct ReplayEventOrderRef",
        "struct ReplayFacadeProvenanceRef",
        "validate_replay_envelope",
        "validate_branch_point_against_replay_envelope",
        "make_branch_point_identity",
        "ordered_replay_envelope_evidence_refs",
        "validate_replay_envelope_for_snapshot_restore",
        "snapshot_restore_supported = false",
        "restore_unsupported_until_snapshot_restore_proof",
    ):
        assert symbol in text

    assert "RuntimeCapabilities" not in text
    assert "platform_capability_contracts.h" not in text
    assert "runtime::platform_capabilities" not in text
    assert "platform_capabilities::CapabilityBundle" not in text


def test_wp15_valid_replay_envelope_and_branch_point_fixture_validate_cleanly() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <vector>
        #include "runtime/contracts/counterfactual_replay_contracts.h"

        int main() {
            using namespace runtime::counterfactual;

            ReplayEnvelope envelope{};
            envelope.replay_envelope_id = "replay:baseline:0001";
            envelope.run_id = "run:alpha";
            envelope.episode_id = "episode:42";
            envelope.has_deterministic_seed = true;
            envelope.deterministic_seed = 424242;
            envelope.has_source_time = true;
            envelope.source_time_s = 12.5;
            envelope.snapshot_ref.snapshot_version_ref = "global:128";
            envelope.barrier_ref.barrier_id = "window_commit";
            envelope.barrier_ref.barrier_sequence = 9;
            envelope.barrier_ref.barrier_detail = "maintained_facade_export";
            envelope.event_order_ref.event_id = "event:0009";
            envelope.event_order_ref.producer_node_id = "p10.observation_export.v1";
            envelope.facade_provenance_ref.packet_ref = "obs:128";
            envelope.facade_provenance_ref.packet_kind = "ObservationBatchPacket";

            const auto envelope_result = validate_replay_envelope(envelope);
            if (!envelope_result.valid) {
                std::cerr << "valid envelope rejected\n";
                for (const auto& error : envelope_result.errors) {
                    std::cerr << error << "\n";
                }
                return 1;
            }

            BranchPoint branch_point{};
            branch_point.branch_point_id = make_branch_point_identity(envelope);
            branch_point.replay_envelope_id = envelope.replay_envelope_id;
            branch_point.snapshot_version_ref = envelope.snapshot_ref.snapshot_version_ref;
            branch_point.barrier_id = envelope.barrier_ref.barrier_id;
            branch_point.event_order_ref = envelope.event_order_ref.event_id;
            branch_point.facade_packet_ref = envelope.facade_provenance_ref.packet_ref;

            const auto branch_result =
                validate_branch_point_against_replay_envelope(branch_point, envelope);
            if (!branch_result.valid) {
                std::cerr << "valid branch point rejected\n";
                for (const auto& error : branch_result.errors) {
                    std::cerr << error << "\n";
                }
                return 1;
            }

            const std::vector<std::string> refs =
                ordered_replay_envelope_evidence_refs(envelope);
            const std::vector<std::string> expected = {
                "snapshot_version_ref=global:128",
                "barrier_id=window_commit",
                "event_order_ref=event:0009",
                "facade_provenance_ref=obs:128",
            };
            if (refs != expected) {
                std::cerr << "evidence ref ordering drifted\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp15_branch_point_identity_is_stable_and_tied_to_replay_boundary_refs() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string>
        #include "runtime/contracts/counterfactual_replay_contracts.h"

        int main() {
            using namespace runtime::counterfactual;

            ReplayEnvelope envelope{};
            envelope.replay_envelope_id = "replay:stable";
            envelope.run_id = "run:stable";
            envelope.episode_id = "episode:stable";
            envelope.has_deterministic_seed = true;
            envelope.deterministic_seed = 7;
            envelope.has_source_time = true;
            envelope.source_time_s = 1.0;
            envelope.snapshot_ref.snapshot_version_ref = "global:7";
            envelope.barrier_ref.barrier_id = "window_commit";
            envelope.barrier_ref.barrier_detail = "maintained_facade_export";
            envelope.event_order_ref.event_id = "event:7";
            envelope.event_order_ref.producer_node_id = "p10.observation_export.v1";
            envelope.facade_provenance_ref.packet_ref = "obs:7";

            const std::string expected =
                "branch_point:replay:stable:global:7:window_commit:event:7";
            if (make_branch_point_identity(envelope) != expected) {
                std::cerr << "branch point identity unexpected\n";
                return 1;
            }

            BranchPoint branch_point{};
            branch_point.branch_point_id = expected;
            branch_point.replay_envelope_id = envelope.replay_envelope_id;
            branch_point.snapshot_version_ref = envelope.snapshot_ref.snapshot_version_ref;
            branch_point.barrier_id = envelope.barrier_ref.barrier_id;
            branch_point.event_order_ref = "event:drift";
            branch_point.facade_packet_ref = envelope.facade_provenance_ref.packet_ref;

            const auto result =
                validate_branch_point_against_replay_envelope(branch_point, envelope);
            if (result.valid ||
                result.rejection_reason != kBranchPointRejectionIdentityMismatch) {
                std::cerr << "identity drift did not fail closed\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp15_restore_support_is_explicitly_unsupported_even_for_valid_envelope() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/counterfactual_replay_contracts.h"

        int main() {
            using namespace runtime::counterfactual;

            ReplayEnvelope envelope{};
            envelope.replay_envelope_id = "replay:no-restore";
            envelope.run_id = "run:no-restore";
            envelope.episode_id = "episode:no-restore";
            envelope.has_deterministic_seed = true;
            envelope.deterministic_seed = 11;
            envelope.has_source_time = true;
            envelope.source_time_s = 2.0;
            envelope.snapshot_ref.snapshot_version_ref = "global:11";
            envelope.barrier_ref.barrier_id = "window_commit";
            envelope.barrier_ref.barrier_detail = "maintained_facade_export";
            envelope.event_order_ref.event_id = "event:11";
            envelope.event_order_ref.producer_node_id = "p10.observation_export.v1";
            envelope.facade_provenance_ref.packet_ref = "obs:11";

            const auto support = validate_replay_envelope_for_snapshot_restore(envelope);
            if (support.supported ||
                support.rejection_reason !=
                    kReplayEnvelopeRejectionRestoreUnsupportedBoundary) {
                std::cerr << "restore boundary drifted\n";
                return 1;
            }

            envelope.snapshot_restore_supported = true;
            const auto invalid = validate_replay_envelope(envelope);
            if (invalid.valid ||
                invalid.rejection_reason !=
                    kReplayEnvelopeRejectionRestoreClaimUnsupported) {
                std::cerr << "restore support claim did not fail closed\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp15_missing_required_replay_fields_fail_closed_with_stable_reasons() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string>
        #include "runtime/contracts/counterfactual_replay_contracts.h"

        int main() {
            using namespace runtime::counterfactual;

            ReplayEnvelope envelope{};
            const auto result = validate_replay_envelope(envelope);
            if (result.valid ||
                result.rejection_reason != kReplayEnvelopeRejectionMissingEnvelopeId) {
                std::cerr << "missing envelope id did not fail first\n";
                return 1;
            }

            bool saw_seed = false;
            bool saw_snapshot = false;
            bool saw_barrier = false;
            bool saw_event_order = false;
            bool saw_provenance = false;
            for (const auto& error : result.errors) {
                saw_seed = saw_seed ||
                    error.find("deterministic_seed") != std::string::npos;
                saw_snapshot = saw_snapshot ||
                    error.find("snapshot_ref.snapshot_version_ref") != std::string::npos;
                saw_barrier = saw_barrier ||
                    error.find("barrier_ref.barrier_id") != std::string::npos;
                saw_event_order = saw_event_order ||
                    error.find("event_order_ref.event_id") != std::string::npos;
                saw_provenance = saw_provenance ||
                    error.find("facade_provenance_ref.packet_ref") != std::string::npos;
            }

            if (!saw_seed || !saw_snapshot || !saw_barrier ||
                !saw_event_order || !saw_provenance) {
                std::cerr << "missing-field fail-closed coverage incomplete\n";
                return 1;
            }

            BranchPoint branch_point{};
            const auto branch_result = validate_branch_point(branch_point);
            if (branch_result.valid ||
                branch_result.rejection_reason !=
                    kBranchPointRejectionMissingBranchPointId) {
                std::cerr << "missing branch point id did not fail closed\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp15_invalid_facade_provenance_label_and_missing_event_order_are_rejected() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string>
        #include "runtime/contracts/counterfactual_replay_contracts.h"

        int main() {
            using namespace runtime::counterfactual;

            ReplayEnvelope envelope{};
            envelope.replay_envelope_id = "replay:bad-provenance";
            envelope.run_id = "run:bad-provenance";
            envelope.episode_id = "episode:bad-provenance";
            envelope.has_deterministic_seed = true;
            envelope.deterministic_seed = 101;
            envelope.has_source_time = true;
            envelope.source_time_s = 4.0;
            envelope.snapshot_ref.snapshot_version_ref = "global:101";
            envelope.barrier_ref.barrier_id = "window_commit";
            envelope.barrier_ref.barrier_detail = "maintained_facade_export";
            envelope.event_order_ref.producer_node_id = "p10.observation_export.v1";
            envelope.facade_provenance_ref.packet_ref = "obs:101";
            envelope.facade_provenance_ref.information_state_source.source_label =
                "not_a_wp11_label";

            const auto result = validate_replay_envelope(envelope);
            if (result.valid ||
                result.rejection_reason !=
                    kReplayEnvelopeRejectionMissingEventOrderRef) {
                std::cerr << "missing event order should fail first\n";
                return 1;
            }

            bool saw_invalid_provenance = false;
            for (const auto& error : result.errors) {
                saw_invalid_provenance =
                    saw_invalid_provenance ||
                    error.find("valid WP11 label") != std::string::npos;
            }
            if (!saw_invalid_provenance) {
                std::cerr << "invalid provenance label was not reported\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout
