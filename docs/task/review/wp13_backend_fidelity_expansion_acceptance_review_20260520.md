# WP13 Backend Fidelity Expansion Acceptance Review

Status: `2026-05-21` accepted / implementation mergeable.

Language:

- English canonical:
  `wp13_backend_fidelity_expansion_acceptance_review_20260520.md`
- Chinese companion:
  [wp13_backend_fidelity_expansion_acceptance_review_20260520.zh.md](wp13_backend_fidelity_expansion_acceptance_review_20260520.zh.md)

Inputs:

- [WP13 Backend Fidelity Expansion](../simulation_architecture/wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.md)
- [WP13-A Runtime Capability Query And Rejection Surface](../simulation_architecture/wp13_backend_fidelity_expansion/wp13_runtime_capability_query_cluster_20260520.md)
- [WP13-B Backend Profile Registry Runtime Gate](../simulation_architecture/wp13_backend_fidelity_expansion/wp13_backend_profile_registry_gate_cluster_20260520.md)
- [WP13-C Parity Budget Evidence Gate](../simulation_architecture/wp13_backend_fidelity_expansion/wp13_parity_budget_evidence_gate_cluster_20260520.md)
- [WP13-D Fidelity Profile Request Gate](../simulation_architecture/wp13_backend_fidelity_expansion/wp13_fidelity_profile_request_gate_cluster_20260520.md)
- [WP13-E Facade And Binding Proof](../simulation_architecture/wp13_backend_fidelity_expansion/wp13_facade_binding_proof_cluster_20260520.md)
- [WP13-F Integration And Acceptance Handoff](../simulation_architecture/wp13_backend_fidelity_expansion/wp13_integration_acceptance_cluster_20260520.md)
- [WP12 acceptance review](wp12_information_agency_enforcement_acceptance_review_20260520.md)

## 1. Verdict

WP13 is accepted as the Phase 4 backend/fidelity expansion increment. It turns
backend and fidelity claims into queryable, rejectable, evidence-backed runtime
facts through maintained facade and Python binding surfaces.

Scope caveats are intentional:

- The maintained baseline remains `cpu_exact.reference` with
  `parity_budget.cpu_exact.reference.v1`.
- Exact GPU, resident-state ownership, device observation views, shadow
  compare, adaptive fidelity scheduling, learned `ModelProvider` runtime, and
  maintained multi-fidelity execution remain unsupported.
- Fidelity labels are admitted as request/admission vocabulary, not as support
  claims.
- Windows portability fixes in the architecture tests only remove hard-coded
  temporary paths and repository-relative path drift; they do not promote any
  runtime capability.

## 2. Gate Verdicts

| Gate | Verdict | Evidence |
|------|---------|----------|
| `WP13-A Runtime Capability Query And Rejection Surface` | pass | `src/runtime/facade/runtime_facade_types.h`, `src/runtime/facade/runtime_facade.cpp`, `src/interfaces/python/bindings_runtime.cpp`, `tests/runtime/facade/test_runtime_facade.py`, and `tests/runtime/bindings/test_bindings_runtime_dto_surface.py` expose conservative profile, budget, evidence, and rejection metadata while keeping exact GPU, resident-state, shadow, and multi-fidelity support false. |
| `WP13-B Backend Profile Registry Runtime Gate` | pass | `src/runtime/contracts/backend_profile_contracts.h` and `tests/architecture/test_wp13_backend_profile_contracts.py` define code-owned backend profile records, validators, maintained/candidate/diagnostics-only status boundaries, and fail-closed capability gate helpers. |
| `WP13-C Parity Budget Evidence Gate` | pass | `src/runtime/contracts/parity_budget_contracts.h` and `tests/architecture/test_wp13_parity_budget_contracts.py` define profile-owned parity budget records, comparison domains, mismatch policy, acceptance gate metadata, and rejection behavior for missing, incompatible, candidate, or diagnostics-only budgets. |
| `WP13-D Fidelity Profile Request Gate` | pass | `src/runtime/contracts/fidelity_profile_contracts.h` and `tests/architecture/test_wp13_fidelity_profile_contracts.py` define `FidelityProfileRequest`, `FidelityProfileAdmissionResult`, the CPU exact baseline request helper, and fail-closed admission for unsupported fidelity labels and backend claims. |
| `WP13-E Facade And Binding Proof` | pass | `src/interfaces/python/bindings_runtime.cpp`, `tests/runtime/bindings/test_bindings_runtime_dto_surface.py`, `tests/runtime/bindings/test_bindings_policy_surface.py`, `tests/runtime/facade/test_runtime_facade.py`, and `tests/test_gpu_runtime_bindings.py` prove profile, budget, capability, and fidelity admission data are visible through maintained surfaces without raw backend access. |
| `WP13-F Integration And Acceptance Handoff` | pass | This review records A-E status, validation commands, residuals, route/index updates, Windows-local validation commands, and the conservative support boundary. |

## 3. Validation Commands

Passed on the Windows local checkout:

```powershell
cmake --build build-local-win -j4
python -m pytest -q tests\architecture\test_wp13_fidelity_profile_contracts.py
python -m pytest -q tests\architecture\test_wp13_backend_profile_contracts.py tests\architecture\test_wp13_parity_budget_contracts.py tests\architecture\test_wp13_fidelity_profile_contracts.py
python -m pytest -q tests\architecture\test_runtime_facade_layering.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\bindings\test_bindings_runtime_dto_surface.py tests\runtime\bindings\test_bindings_policy_surface.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py tests\test_gpu_runtime_bindings.py
git diff --check
```

Observed outcomes before this review:

- Build: passed.
- Focused fidelity request architecture gate: `8 passed`.
- WP13 backend profile, parity budget, and fidelity contract batch:
  `21 passed`.
- Runtime facade layering guard: `13 passed`.
- Runtime binding and policy binding batch: `24 passed`.
- Runtime facade and GPU binding batch: `19 passed, 2 skipped`.
- `git diff --check`: passed with line-ending warnings only.

Final closure validation should additionally run after this review is added:

```powershell
python tools\maintenance\wp_doc_closure_audit.py --wp WP13
```

## 4. Runtime Surface Summary

- `RuntimeCapabilities` exposes maintained CPU exact baseline metadata,
  candidate profile ids, candidate parity budget refs, rejection reasons, and
  multi-fidelity rejection text while preserving false support defaults.
- Backend profile records and parity budget records are code-owned contract
  data with validators and negative capability-gate helpers.
- `FidelityProfileRequest` and `FidelityProfileAdmissionResult` expose fidelity
  request labels, backend profile id, parity budget ref, model-family scope,
  validation gate, facade evidence refs, unsupported request flags, admission
  status, rejection reason, and evidence refs.
- Python bindings expose the fidelity request/result DTOs plus
  `make_exact_evaluation_cpu_reference_fidelity_request()` and
  `admit_fidelity_profile_request()`.

## 5. Conservative Support Statement

The only admitted fidelity request is the CPU exact reference baseline:
`exact_evaluation` with `cpu_exact.reference` and
`parity_budget.cpu_exact.reference.v1`.

The following claims remain explicitly unsupported and must not be described as
maintained by WP13:

- `fast_training`, `sensor_heavy`, `weapon_effects_heavy`,
  `large_scale_swarm`, and `single_platform_physics` fidelity labels.
- Adaptive fidelity scheduling.
- Learned `ModelProvider` runtime admission.
- Approximate execution.
- Exact GPU backend execution.
- Resident-state ownership.
- Device observation views.
- Shadow-backed fidelity or shadow compare.
- Maintained multi-fidelity support.

## 6. Residuals And Next Plan

Residuals intentionally carried forward:

- Exact GPU promotion requires a maintained backend profile revision, parity
  budget, synchronization/ownership policy, facade evidence, and validation
  review.
- Resident-state support requires explicit ownership, synchronization, state
  visibility, and parity evidence before it can leave unmaintained-candidate
  status.
- Shadow compare needs non-interference rules, diagnostics separation, parity
  scope, and validation evidence before it can become maintained.
- Adaptive fidelity scheduling and learned provider runtime remain future
  architecture/runtime work.
- Capability composition should open only after this backend/fidelity query and
  rejection surface remains stable.

Recommended next WP: open the capability-composition phase from the post-WP9
route, preserving the WP13 rule that backend/fidelity capability claims must be
profile-backed, budget-backed, and fail closed.
