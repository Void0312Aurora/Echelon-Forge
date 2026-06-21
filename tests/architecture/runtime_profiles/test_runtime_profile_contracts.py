from __future__ import annotations

import textwrap

from tests.architecture.helpers import REPO_ROOT, compile_cpp_snippet

BACKEND_PROFILE_HEADER = (
  REPO_ROOT / "src" / "runtime" / "contracts" / "backend_profile_contracts.h"
)
PARITY_BUDGET_HEADER = (
  REPO_ROOT / "src" / "runtime" / "contracts" / "parity_budget_contracts.h"
)
FIDELITY_PROFILE_HEADER = (
  REPO_ROOT / "src" / "runtime" / "contracts" / "fidelity_profile_contracts.h"
)


def _compile_runtime_profile_snippet(source: str, *, binary_prefix: str):
  return compile_cpp_snippet(
    source,
    binary_prefix=f"runtime_profiles_{binary_prefix}",
  )


# Backend profile contracts

def test_backend_profile_contract_header_exists_in_runtime_contracts() -> None:
  assert BACKEND_PROFILE_HEADER.is_file()


def test_backend_profile_registry_seed_contains_accepted_ids_and_classes() -> None:
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
  result = _compile_runtime_profile_snippet(source, binary_prefix="backend")
  assert result.returncode == 0, result.stderr + result.stdout


def test_backend_profile_registry_marks_only_cpu_exact_reference_as_maintained() -> None:
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
  result = _compile_runtime_profile_snippet(source, binary_prefix="backend")
  assert result.returncode == 0, result.stderr + result.stdout


def test_backend_profile_registry_seed_validates_and_rejects_unsupported_claims() -> None:
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
  result = _compile_runtime_profile_snippet(source, binary_prefix="backend")
  assert result.returncode == 0, result.stderr + result.stdout


def test_diagnostics_and_candidate_rows_do_not_authorize_gpu_resident_shadow_or_device_observation() -> None:
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
  result = _compile_runtime_profile_snippet(source, binary_prefix="backend")
  assert result.returncode == 0, result.stderr + result.stdout


def test_maintained_backend_profile_validation_fails_closed_on_missing_required_field() -> None:
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
  result = _compile_runtime_profile_snippet(source, binary_prefix="backend")
  assert result.returncode == 0, result.stderr + result.stdout


# Parity budget contracts

def test_parity_budget_contract_header_exists_in_runtime_contracts() -> None:
  assert PARITY_BUDGET_HEADER.is_file()


def test_header_encodes_required_budget_ids_and_rejection_reasons() -> None:
  header = PARITY_BUDGET_HEADER.read_text(encoding="utf-8")

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


def test_header_carries_required_comparison_domain_metadata_fields() -> None:
  header = PARITY_BUDGET_HEADER.read_text(encoding="utf-8")

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


def test_registry_seed_validates_cleanly_and_keeps_single_maintained_budget() -> None:
  source = textwrap.dedent(
    r"""
    #include <iostream>
    #include "runtime/contracts/parity_budget_contracts.h"

    int main() {
      using namespace runtime::parity;
      const auto result = validate_parity_budget_registry_seed();
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

  result = _compile_runtime_profile_snippet(source, binary_prefix="parity_budget")
  assert result.returncode == 0, result.stderr + result.stdout


def test_candidate_and_diagnostics_budgets_reject_maintained_promotion() -> None:
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

  result = _compile_runtime_profile_snippet(source, binary_prefix="parity_budget")
  assert result.returncode == 0, result.stderr + result.stdout


def test_missing_budget_ref_and_incompatible_profile_class_fail_closed() -> None:
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

  result = _compile_runtime_profile_snippet(source, binary_prefix="parity_budget")
  assert result.returncode == 0, result.stderr + result.stdout


def test_missing_acceptance_gate_and_required_metadata_rejects() -> None:
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

  result = _compile_runtime_profile_snippet(source, binary_prefix="parity_budget")
  assert result.returncode == 0, result.stderr + result.stdout


# Fidelity profile contracts

def test_fidelity_profile_contract_header_exists_in_runtime_contracts() -> None:
  assert FIDELITY_PROFILE_HEADER.is_file()


def test_fidelity_profile_header_declares_request_labels_and_rejections() -> None:
  header = FIDELITY_PROFILE_HEADER.read_text(encoding="utf-8")

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


def test_exact_evaluation_cpu_baseline_request_is_admitted() -> None:
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

  result = _compile_runtime_profile_snippet(source, binary_prefix="fidelity")
  assert result.returncode == 0, result.stderr + result.stdout


def test_missing_required_fidelity_fields_fail_closed() -> None:
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
      blank_scope.model_family_scope.push_back("  ");
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

  result = _compile_runtime_profile_snippet(source, binary_prefix="fidelity")
  assert result.returncode == 0, result.stderr + result.stdout


def test_nonbaseline_fidelity_labels_do_not_imply_maintained_support() -> None:
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

  result = _compile_runtime_profile_snippet(source, binary_prefix="fidelity")
  assert result.returncode == 0, result.stderr + result.stdout


def test_unsupported_runtime_modes_reject_with_stable_reasons() -> None:
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

  result = _compile_runtime_profile_snippet(source, binary_prefix="fidelity")
  assert result.returncode == 0, result.stderr + result.stdout


def test_backend_candidate_fidelity_claims_fail_closed() -> None:
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

  result = _compile_runtime_profile_snippet(source, binary_prefix="fidelity")
  assert result.returncode == 0, result.stderr + result.stdout


def test_unknown_or_unmaintained_profile_and_budget_reject() -> None:
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

  result = _compile_runtime_profile_snippet(source, binary_prefix="fidelity")
  assert result.returncode == 0, result.stderr + result.stdout
