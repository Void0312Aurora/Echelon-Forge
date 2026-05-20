from __future__ import annotations

import subprocess
import tempfile
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HEADER = REPO_ROOT / "src" / "runtime" / "contracts" / "parity_budget_contracts.h"


def _compile_and_run(source: str) -> subprocess.CompletedProcess[str]:
    binary = Path(tempfile.gettempdir()) / "wp13_parity_budget_contracts_test_bin"
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


def test_wp13_parity_budget_contract_header_exists_in_runtime_contracts() -> None:
    assert HEADER.is_file()


def test_wp13_header_encodes_required_budget_ids_and_rejection_reasons() -> None:
    header = HEADER.read_text(encoding="utf-8")

    for token in (
        "parity_budget.cpu_exact.reference.v1",
        "parity_budget.gpu_helpers.diagnostics_only.v1",
        "parity_budget.gpu_exact.unmaintained_candidate.v1",
        "parity_budget.resident_state.unmaintained_candidate.v1",
        "parity_budget.shadow_compare.unmaintained_candidate.v1",
        "missing_parity_budget_ref",
        "parity_budget_profile_class_incompatible",
        "parity_budget_acceptance_gate_missing",
        "parity_budget_candidate_is_not_accepted_for_maintained_use",
        "parity_budget_diagnostics_only_is_not_accepted_for_maintained_use",
    ):
        assert token in header


def test_wp13_header_carries_required_comparison_domain_metadata_fields() -> None:
    header = HEADER.read_text(encoding="utf-8")

    for token in (
        "event_order",
        "snapshot_versions",
        "observation_export",
        "diagnostics_trace",
        "sync_barriers",
        "mismatch_policy",
        "acceptance_gate",
        "schema_version",
        "source_snapshot_version",
        "resulting_snapshot_version",
        "mismatch_code",
        "shadow_report_export",
        "partial_sync_commit",
    ):
        assert token in header


def test_wp13_registry_seed_validates_cleanly_and_keeps_single_maintained_budget() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/parity_budget_contracts.h"

        int main() {
            using namespace runtime::parity;
            const auto result = validate_wp13_parity_budget_registry_seed();
            if (result.has_value()) {
                std::cerr << "registry seed should validate cleanly\n";
                for (const auto& error : result->errors) {
                    std::cerr << error << "\n";
                }
                return 1;
            }

            const auto* baseline =
                find_parity_budget_record(kParityBudgetCpuExactReferenceV1);
            if (baseline == nullptr) {
                std::cerr << "missing cpu exact baseline budget\n";
                return 1;
            }
            const auto baseline_result = validate_profile_owned_parity_budget(
                "cpu_exact.reference",
                kParityBudgetProfileClassReference,
                kParityBudgetCpuExactReferenceV1
            );
            if (!baseline_result.valid || !baseline_result.accepted_for_maintained_use) {
                std::cerr << "cpu exact baseline should be accepted\n";
                return 1;
            }
            if (baseline->event_order.mode != "exact_identity" ||
                baseline->snapshot_versions.mode != "exact_identity" ||
                baseline->observation_export.payload_policy != "inherit_numeric_state" ||
                baseline->diagnostics_trace.prose_policy != "diagnostics_only") {
                std::cerr << "baseline comparison metadata drifted\n";
                return 1;
            }
            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp13_candidate_and_diagnostics_budgets_reject_maintained_promotion() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string_view>
        #include <vector>
        #include "runtime/contracts/parity_budget_contracts.h"

        int main() {
            using namespace runtime::parity;

            const std::vector<std::pair<std::string_view, std::string_view>> expectations = {
                {
                    kParityBudgetGpuHelpersDiagnosticsOnlyV1,
                    kParityBudgetRejectionDiagnosticsOnlyNotMaintained,
                },
                {
                    kParityBudgetGpuExactUnmaintainedCandidateV1,
                    kParityBudgetRejectionCandidateNotMaintained,
                },
                {
                    kParityBudgetResidentStateUnmaintainedCandidateV1,
                    kParityBudgetRejectionCandidateNotMaintained,
                },
                {
                    kParityBudgetShadowCompareUnmaintainedCandidateV1,
                    kParityBudgetRejectionDiagnosticsOnlyNotMaintained,
                },
            };

            for (const auto& [budget_id, expected_reason] : expectations) {
                const auto* record = find_parity_budget_record(budget_id);
                if (record == nullptr) {
                    std::cerr << "missing budget: " << budget_id << "\n";
                    return 1;
                }

                const auto result = validate_profile_owned_parity_budget(
                    record->backend_profile_id,
                    record->profile_class,
                    budget_id
                );
                if (!result.valid) {
                    std::cerr << "registry record failed structural validation: "
                              << budget_id << "\n";
                    return 1;
                }
                if (result.accepted_for_maintained_use) {
                    std::cerr << "candidate or diagnostics budget drifted into maintained use: "
                              << budget_id << "\n";
                    return 1;
                }
                if (result.rejection_reason != expected_reason) {
                    std::cerr << "unexpected rejection reason for " << budget_id << ": "
                              << result.rejection_reason << "\n";
                    return 1;
                }
            }
            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp13_missing_budget_ref_and_incompatible_profile_class_fail_closed() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/parity_budget_contracts.h"

        int main() {
            using namespace runtime::parity;

            const auto missing = validate_profile_owned_parity_budget(
                "cpu_exact.reference",
                kParityBudgetProfileClassReference,
                ""
            );
            if (missing.rejection_reason != kParityBudgetRejectionMissingBudgetRef) {
                std::cerr << "missing budget ref did not fail closed\n";
                return 1;
            }

            const auto incompatible = validate_profile_owned_parity_budget(
                "cpu_exact.reference",
                kParityBudgetProfileClassApproximate,
                kParityBudgetCpuExactReferenceV1
            );
            if (incompatible.valid) {
                std::cerr << "incompatible profile class unexpectedly validated\n";
                return 1;
            }
            if (incompatible.rejection_reason !=
                kParityBudgetRejectionProfileClassIncompatible) {
                std::cerr << "incompatible class rejection reason drifted\n";
                return 1;
            }
            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp13_missing_acceptance_gate_and_required_metadata_rejects() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/parity_budget_contracts.h"

        int main() {
            using namespace runtime::parity;

            ParityBudgetRecord missing_gate = make_cpu_exact_reference_budget();
            missing_gate.acceptance_gate.clear();
            const auto missing_gate_result =
                validate_parity_budget_record_contract(missing_gate);
            if (missing_gate_result.valid) {
                std::cerr << "missing acceptance gate unexpectedly validated\n";
                return 1;
            }
            if (missing_gate_result.rejection_reason !=
                kParityBudgetRejectionAcceptanceGateMissing) {
                std::cerr << "missing acceptance gate did not report stable rejection\n";
                return 1;
            }

            ParityBudgetRecord missing_metadata = make_cpu_exact_reference_budget();
            missing_metadata.sync_barriers.clear();
            const auto missing_metadata_result =
                validate_parity_budget_record_contract(missing_metadata);
            if (missing_metadata_result.valid) {
                std::cerr << "missing comparison metadata unexpectedly validated\n";
                return 1;
            }
            if (missing_metadata_result.rejection_reason !=
                kParityBudgetRejectionMetadataIncomplete) {
                std::cerr << "missing metadata did not report stable rejection\n";
                return 1;
            }
            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout
