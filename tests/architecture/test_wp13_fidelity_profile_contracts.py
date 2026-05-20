from __future__ import annotations

import subprocess
import tempfile
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HEADER = REPO_ROOT / "src" / "runtime" / "contracts" / "fidelity_profile_contracts.h"


def _compile_and_run(source: str) -> subprocess.CompletedProcess[str]:
    binary = Path(tempfile.gettempdir()) / "wp13_fidelity_profile_contracts_test_bin"
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


def test_wp13_fidelity_profile_contract_header_exists_in_runtime_contracts() -> None:
    assert HEADER.is_file()


def test_wp13_fidelity_profile_header_declares_request_labels_and_rejections() -> None:
    header = HEADER.read_text(encoding="utf-8")

    for token in (
        "exact_evaluation",
        "fast_training",
        "sensor_heavy",
        "fidelity_profile_requires_maintained_backend_profile",
        "fidelity_profile_requires_accepted_budget",
        "adaptive_fidelity_scheduling_not_implemented",
        "learned_model_provider_not_implemented",
        "exact_gpu_fidelity_requires_maintained_backend_profile",
        "resident_state_fidelity_requires_maintained_backend_profile",
        "shadow_fidelity_requires_maintained_backend_profile",
    ):
        assert token in header


def test_wp13_exact_evaluation_cpu_baseline_request_is_admitted() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/fidelity_profile_contracts.h"

        int main() {
            using namespace runtime::fidelity;

            const auto request = make_exact_evaluation_cpu_reference_request();
            const auto result = admit_fidelity_profile_request(request);

            if (!result.admitted || !result.baseline_exact_evaluation) {
                std::cerr << "baseline exact_evaluation request was rejected: "
                          << result.rejection_reason << "\n";
                return 1;
            }
            if (result.backend_profile_id != "cpu_exact.reference" ||
                result.parity_budget_ref != "parity_budget.cpu_exact.reference.v1") {
                std::cerr << "baseline binding drifted\n";
                return 1;
            }
            if (result.evidence_refs.empty()) {
                std::cerr << "baseline request lost facade evidence refs\n";
                return 1;
            }
            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp13_missing_required_fidelity_fields_fail_closed() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/fidelity_profile_contracts.h"

        int main() {
            using namespace runtime::fidelity;

            auto missing_backend = make_exact_evaluation_cpu_reference_request();
            missing_backend.backend_profile_id.clear();
            if (admit_fidelity_profile_request(missing_backend).rejection_reason !=
                kFidelityProfileRejectionMissingBackendProfile) {
                std::cerr << "missing backend profile did not fail closed\n";
                return 1;
            }

            auto missing_budget = make_exact_evaluation_cpu_reference_request();
            missing_budget.parity_budget_ref.clear();
            if (admit_fidelity_profile_request(missing_budget).rejection_reason !=
                kFidelityProfileRejectionMissingBudget) {
                std::cerr << "missing parity budget did not fail closed\n";
                return 1;
            }

            auto missing_scope = make_exact_evaluation_cpu_reference_request();
            missing_scope.model_family_scope.clear();
            if (admit_fidelity_profile_request(missing_scope).rejection_reason !=
                kFidelityProfileRejectionMissingModelScope) {
                std::cerr << "missing model scope did not fail closed\n";
                return 1;
            }

            auto blank_scope = make_exact_evaluation_cpu_reference_request();
            blank_scope.model_family_scope.push_back("   ");
            if (admit_fidelity_profile_request(blank_scope).rejection_reason !=
                kFidelityProfileRejectionMissingModelScope) {
                std::cerr << "blank model scope did not fail closed\n";
                return 1;
            }

            auto missing_gate = make_exact_evaluation_cpu_reference_request();
            missing_gate.validation_gate.clear();
            if (admit_fidelity_profile_request(missing_gate).rejection_reason !=
                kFidelityProfileRejectionMissingValidationGate) {
                std::cerr << "missing validation gate did not fail closed\n";
                return 1;
            }

            auto missing_evidence = make_exact_evaluation_cpu_reference_request();
            missing_evidence.facade_evidence_refs.clear();
            if (admit_fidelity_profile_request(missing_evidence).rejection_reason !=
                kFidelityProfileRejectionMissingFacadeEvidence) {
                std::cerr << "missing facade evidence did not fail closed\n";
                return 1;
            }

            auto blank_evidence = make_exact_evaluation_cpu_reference_request();
            blank_evidence.facade_evidence_refs.push_back("");
            if (admit_fidelity_profile_request(blank_evidence).rejection_reason !=
                kFidelityProfileRejectionMissingFacadeEvidence) {
                std::cerr << "blank facade evidence did not fail closed\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp13_nonbaseline_fidelity_labels_do_not_imply_maintained_support() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string_view>
        #include <vector>
        #include "runtime/contracts/fidelity_profile_contracts.h"

        int main() {
            using namespace runtime::fidelity;

            const std::vector<std::string_view> labels = {
                kFidelityProfileLabelFastTraining,
                kFidelityProfileLabelSensorHeavy,
                kFidelityProfileLabelWeaponEffectsHeavy,
                kFidelityProfileLabelLargeScaleSwarm,
                kFidelityProfileLabelSinglePlatformPhysics,
            };

            for (const auto label : labels) {
                auto request = make_exact_evaluation_cpu_reference_request();
                request.request_label = std::string(label);
                const auto result = admit_fidelity_profile_request(request);
                if (result.admitted ||
                    result.rejection_reason != kFidelityProfileRejectionUnsupportedLabel) {
                    std::cerr << "nonbaseline label admitted or rejected unclearly: "
                              << request.request_label << "\n";
                    return 1;
                }
            }
            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp13_unsupported_runtime_modes_reject_with_stable_reasons() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/fidelity_profile_contracts.h"

        int main() {
            using namespace runtime::fidelity;

            auto adaptive = make_exact_evaluation_cpu_reference_request();
            adaptive.requests_adaptive_scheduling = true;
            if (admit_fidelity_profile_request(adaptive).rejection_reason !=
                kFidelityProfileRejectionAdaptiveScheduling) {
                std::cerr << "adaptive scheduling rejection drifted\n";
                return 1;
            }

            auto learned = make_exact_evaluation_cpu_reference_request();
            learned.requests_learned_model_provider = true;
            if (admit_fidelity_profile_request(learned).rejection_reason !=
                kFidelityProfileRejectionLearnedProvider) {
                std::cerr << "learned provider rejection drifted\n";
                return 1;
            }

            auto approximate = make_exact_evaluation_cpu_reference_request();
            approximate.requests_approximate_execution = true;
            if (admit_fidelity_profile_request(approximate).rejection_reason !=
                kFidelityProfileRejectionApproximateExecution) {
                std::cerr << "approximate execution rejection drifted\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp13_backend_candidate_fidelity_claims_fail_closed() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/fidelity_profile_contracts.h"

        int main() {
            using namespace runtime::fidelity;

            auto exact_gpu = make_exact_evaluation_cpu_reference_request();
            exact_gpu.backend_profile_id = "gpu_exact.unmaintained_candidate";
            exact_gpu.parity_budget_ref = "parity_budget.gpu_exact.unmaintained_candidate.v1";
            exact_gpu.requests_exact_gpu_backend = true;
            if (admit_fidelity_profile_request(exact_gpu).rejection_reason !=
                kFidelityProfileRejectionExactGpu) {
                std::cerr << "exact GPU fidelity claim did not fail closed\n";
                return 1;
            }

            auto resident = make_exact_evaluation_cpu_reference_request();
            resident.backend_profile_id = "resident_state.unmaintained_candidate";
            resident.parity_budget_ref =
                "parity_budget.resident_state.unmaintained_candidate.v1";
            resident.requests_resident_state = true;
            if (admit_fidelity_profile_request(resident).rejection_reason !=
                kFidelityProfileRejectionResidentState) {
                std::cerr << "resident-state fidelity claim did not fail closed\n";
                return 1;
            }

            auto shadow = make_exact_evaluation_cpu_reference_request();
            shadow.backend_profile_id = "shadow_compare.unmaintained_candidate";
            shadow.parity_budget_ref =
                "parity_budget.shadow_compare.unmaintained_candidate.v1";
            shadow.requests_shadow_compare = true;
            if (admit_fidelity_profile_request(shadow).rejection_reason !=
                kFidelityProfileRejectionShadowCompare) {
                std::cerr << "shadow fidelity claim did not fail closed\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp13_unknown_or_unmaintained_profile_and_budget_reject() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/fidelity_profile_contracts.h"

        int main() {
            using namespace runtime::fidelity;

            auto unknown_profile = make_exact_evaluation_cpu_reference_request();
            unknown_profile.backend_profile_id = "missing.profile";
            if (admit_fidelity_profile_request(unknown_profile).rejection_reason !=
                kFidelityProfileRejectionRequiresMaintainedBackendProfile) {
                std::cerr << "unknown profile rejection drifted\n";
                return 1;
            }

            auto diagnostics_profile = make_exact_evaluation_cpu_reference_request();
            diagnostics_profile.backend_profile_id = "gpu_helpers.diagnostics_only";
            diagnostics_profile.parity_budget_ref =
                "parity_budget.gpu_helpers.diagnostics_only.v1";
            if (admit_fidelity_profile_request(diagnostics_profile).rejection_reason !=
                kFidelityProfileRejectionRequiresMaintainedBackendProfile) {
                std::cerr << "diagnostics profile rejection drifted\n";
                return 1;
            }

            auto unknown_budget = make_exact_evaluation_cpu_reference_request();
            unknown_budget.parity_budget_ref = "missing.budget";
            if (admit_fidelity_profile_request(unknown_budget).rejection_reason !=
                kFidelityProfileRejectionRequiresAcceptedBudget) {
                std::cerr << "unknown budget rejection drifted\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout
