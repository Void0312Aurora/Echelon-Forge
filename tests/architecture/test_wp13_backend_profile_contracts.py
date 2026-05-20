from __future__ import annotations

import subprocess
import tempfile
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HEADER = REPO_ROOT / "src" / "runtime" / "contracts" / "backend_profile_contracts.h"


def _compile_and_run(source: str) -> subprocess.CompletedProcess[str]:
    binary = Path(tempfile.gettempdir()) / "wp13_backend_profile_contracts_test_bin"
    command = [
        "g++",
        "-std=c++20",
        "-I",
        str(REPO_ROOT / "src"),
        "-x",
        "c++",
        "-",
        "-o",
        str(binary),
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

    return subprocess.run(
        [str(binary)],
        text=True,
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
    )


def test_wp13_backend_profile_contract_header_exists_in_runtime_contracts() -> None:
    assert HEADER.is_file()


def test_wp13_backend_profile_registry_seed_contains_accepted_ids_and_classes() -> None:
    source = textwrap.dedent(
        r"""
        #include <algorithm>
        #include <iostream>
        #include <string>
        #include <vector>
        #include "runtime/contracts/backend_profile_contracts.h"

        int main() {
            using namespace runtime::backend_profiles;

            const auto& registry = backend_profile_registry_seed();
            if (registry.size() != 5) {
                std::cerr << "unexpected seed size: " << registry.size() << "\n";
                return 1;
            }

            struct ExpectedRow {
                std::string id;
                std::string profile_class;
            };

            const std::vector<ExpectedRow> expected = {
                {std::string(kBackendProfileIdCpuExactReference), std::string(kBackendProfileClassReference)},
                {std::string(kBackendProfileIdGpuHelpersDiagnosticsOnly), std::string(kBackendProfileClassDiagnosticsOnly)},
                {std::string(kBackendProfileIdGpuExactUnmaintainedCandidate), std::string(kBackendProfileClassAcceleratedExact)},
                {std::string(kBackendProfileIdResidentStateUnmaintainedCandidate), std::string(kBackendProfileClassResidentState)},
                {std::string(kBackendProfileIdShadowCompareUnmaintainedCandidate), std::string(kBackendProfileClassDiagnosticsOnly)},
            };

            for (const auto& row : expected) {
                const auto* profile = find_backend_profile_contract(row.id);
                if (profile == nullptr) {
                    std::cerr << "missing profile: " << row.id << "\n";
                    return 1;
                }
                if (profile->profile_class != row.profile_class) {
                    std::cerr << "unexpected class for " << row.id << ": "
                              << profile->profile_class << "\n";
                    return 1;
                }
            }

            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp13_backend_profile_registry_marks_only_cpu_exact_reference_as_maintained() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string>
        #include "runtime/contracts/backend_profile_contracts.h"

        int main() {
            using namespace runtime::backend_profiles;

            const auto maintained = enumerate_maintained_backend_profile_contracts();
            if (maintained.size() != 1) {
                std::cerr << "unexpected maintained count: " << maintained.size() << "\n";
                return 1;
            }
            if (maintained.front()->backend_profile_id != kBackendProfileIdCpuExactReference) {
                std::cerr << "wrong maintained profile: "
                          << maintained.front()->backend_profile_id << "\n";
                return 1;
            }

            for (const auto& profile : backend_profile_registry_seed()) {
                const bool expected = profile.backend_profile_id == kBackendProfileIdCpuExactReference;
                if (is_maintained_backend_profile(profile) != expected) {
                    std::cerr << "maintained drift for " << profile.backend_profile_id << "\n";
                    return 1;
                }
            }

            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp13_backend_profile_registry_seed_validates_and_rejects_unsupported_claims() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string>
        #include <utility>
        #include <vector>
        #include "runtime/contracts/backend_profile_contracts.h"

        int main() {
            using namespace runtime::backend_profiles;

            const auto registry_result = validate_backend_profile_registry_seed();
            if (registry_result.has_value()) {
                std::cerr << "registry should validate cleanly\n";
                for (const auto& error : registry_result->errors) {
                    std::cerr << error << "\n";
                }
                return 1;
            }

            const auto cpu_exact_gpu =
                validate_backend_profile_for_exact_gpu_support(kBackendProfileIdCpuExactReference);
            if (cpu_exact_gpu.allowed ||
                cpu_exact_gpu.rejection_reason !=
                    kBackendProfileRejectionReasonMaintainedBaselineExactGpu) {
                std::cerr << "cpu profile exact-gpu gate drifted\n";
                return 1;
            }

            const auto gpu_helpers_exact_gpu =
                validate_backend_profile_for_exact_gpu_support(
                    kBackendProfileIdGpuHelpersDiagnosticsOnly
                );
            if (gpu_helpers_exact_gpu.allowed ||
                gpu_helpers_exact_gpu.rejection_reason !=
                    kBackendProfileRejectionReasonDiagnosticsOnlyExactGpu) {
                std::cerr << "gpu helpers exact-gpu rejection drifted\n";
                return 1;
            }

            const auto gpu_candidate_exact_gpu =
                validate_backend_profile_for_exact_gpu_support(
                    kBackendProfileIdGpuExactUnmaintainedCandidate
                );
            if (gpu_candidate_exact_gpu.allowed ||
                gpu_candidate_exact_gpu.rejection_reason !=
                    kBackendProfileRejectionReasonUnmaintainedCandidateExactGpu) {
                std::cerr << "gpu candidate exact-gpu rejection drifted\n";
                return 1;
            }

            const auto resident_candidate_resident =
                validate_backend_profile_for_resident_state_support(
                    kBackendProfileIdResidentStateUnmaintainedCandidate
                );
            if (resident_candidate_resident.allowed ||
                resident_candidate_resident.rejection_reason !=
                    kBackendProfileRejectionReasonUnmaintainedCandidateResidentState) {
                std::cerr << "resident-state candidate rejection drifted\n";
                return 1;
            }

            const auto shadow_candidate_shadow =
                validate_backend_profile_for_shadow_compare_support(
                    kBackendProfileIdShadowCompareUnmaintainedCandidate
                );
            if (shadow_candidate_shadow.allowed ||
                shadow_candidate_shadow.rejection_reason !=
                    kBackendProfileRejectionReasonUnmaintainedCandidateShadowCompare) {
                std::cerr << "shadow candidate rejection drifted\n";
                return 1;
            }

            const auto missing =
                validate_backend_profile_for_device_observation_view_support("missing.profile");
            if (missing.allowed ||
                missing.rejection_reason !=
                    kBackendProfileRejectionReasonProfileIdNotFound) {
                std::cerr << "missing profile rejection drifted\n";
                return 1;
            }

            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp13_diagnostics_and_candidate_rows_do_not_authorize_gpu_resident_shadow_or_device_observation() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string>
        #include <utility>
        #include <vector>
        #include "runtime/contracts/backend_profile_contracts.h"

        int main() {
            using namespace runtime::backend_profiles;

            const std::vector<std::string> blocked_ids = {
                std::string(kBackendProfileIdGpuHelpersDiagnosticsOnly),
                std::string(kBackendProfileIdGpuExactUnmaintainedCandidate),
                std::string(kBackendProfileIdResidentStateUnmaintainedCandidate),
                std::string(kBackendProfileIdShadowCompareUnmaintainedCandidate),
            };

            for (const auto& profile_id : blocked_ids) {
                const auto exact_gpu = validate_backend_profile_for_exact_gpu_support(profile_id);
                const auto resident = validate_backend_profile_for_resident_state_support(profile_id);
                const auto shadow = validate_backend_profile_for_shadow_compare_support(profile_id);
                const auto device = validate_backend_profile_for_device_observation_view_support(profile_id);
                if (exact_gpu.allowed || resident.allowed || shadow.allowed || device.allowed) {
                    std::cerr << "unsupported claim unexpectedly authorized for "
                              << profile_id << "\n";
                    return 1;
                }
            }

            const auto gpu_helpers_device =
                validate_backend_profile_for_device_observation_view_support(
                    kBackendProfileIdGpuHelpersDiagnosticsOnly
                );
            if (gpu_helpers_device.rejection_reason !=
                kBackendProfileRejectionReasonDiagnosticsOnlyDeviceObservationView) {
                std::cerr << "gpu helpers device-observation rejection drifted\n";
                return 1;
            }

            const auto resident_shadow =
                validate_backend_profile_for_shadow_compare_support(
                    kBackendProfileIdResidentStateUnmaintainedCandidate
                );
            if (resident_shadow.rejection_reason !=
                kBackendProfileRejectionReasonUnmaintainedCandidateShadowCompare) {
                std::cerr << "resident-state candidate shadow rejection drifted\n";
                return 1;
            }

            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp13_maintained_backend_profile_validation_fails_closed_on_missing_required_field() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/backend_profile_contracts.h"

        int main() {
            using namespace runtime::backend_profiles;

            BackendProfileContract profile = backend_profile_registry_seed().front();
            profile.validation_gate.clear();

            const auto result = validate_maintained_backend_profile_contract(profile);
            if (result.valid) {
                std::cerr << "maintained profile unexpectedly passed validation\n";
                return 1;
            }

            bool saw_validation_gate = false;
            for (const auto& error : result.errors) {
                if (error.find("validation_gate") != std::string::npos) {
                    saw_validation_gate = true;
                }
            }

            if (!saw_validation_gate) {
                std::cerr << "missing validation_gate failure\n";
                return 1;
            }

            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout
