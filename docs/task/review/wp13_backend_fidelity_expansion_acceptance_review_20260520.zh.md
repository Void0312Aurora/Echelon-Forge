# WP13 Backend Fidelity Expansion 验收审查

状态：`2026-05-21` accepted / implementation mergeable。

语言版本：

- 英文主文：
  [wp13_backend_fidelity_expansion_acceptance_review_20260520.md](wp13_backend_fidelity_expansion_acceptance_review_20260520.md)
- 中文辅文：`wp13_backend_fidelity_expansion_acceptance_review_20260520.zh.md`

输入：

- [WP13 Backend Fidelity Expansion](../simulation_architecture/wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.zh.md)
- [WP13-A Runtime Capability Query And Rejection Surface](../simulation_architecture/wp13_backend_fidelity_expansion/wp13_runtime_capability_query_cluster_20260520.zh.md)
- [WP13-B Backend Profile Registry Runtime Gate](../simulation_architecture/wp13_backend_fidelity_expansion/wp13_backend_profile_registry_gate_cluster_20260520.zh.md)
- [WP13-C Parity Budget Evidence Gate](../simulation_architecture/wp13_backend_fidelity_expansion/wp13_parity_budget_evidence_gate_cluster_20260520.zh.md)
- [WP13-D Fidelity Profile Request Gate](../simulation_architecture/wp13_backend_fidelity_expansion/wp13_fidelity_profile_request_gate_cluster_20260520.zh.md)
- [WP13-E Facade And Binding Proof](../simulation_architecture/wp13_backend_fidelity_expansion/wp13_facade_binding_proof_cluster_20260520.zh.md)
- [WP13-F Integration And Acceptance Handoff](../simulation_architecture/wp13_backend_fidelity_expansion/wp13_integration_acceptance_cluster_20260520.zh.md)
- [WP12 验收审查](wp12_information_agency_enforcement_acceptance_review_20260520.zh.md)

## 1. 结论

WP13 验收通过，可作为 Phase 4 backend/fidelity expansion increment 合入。它把
backend 与 fidelity claim 转成可查询、可拒绝、有证据支撑的 runtime facts，并通过
维护中的 facade 与 Python binding surfaces 暴露。

边界需要保留：

- 维护中 baseline 仍是 `cpu_exact.reference` 与
  `parity_budget.cpu_exact.reference.v1`。
- Exact GPU、resident-state ownership、device observation views、shadow
  compare、adaptive fidelity scheduling、learned `ModelProvider` runtime 与
  maintained multi-fidelity execution 仍不受支持。
- Fidelity labels 被作为 request/admission vocabulary 接受，而不是 support
  claims。
- Windows portability 修复只移除 architecture tests 中的硬编码临时路径和仓库相对路径
  漂移，不晋级任何 runtime capability。

## 2. Gate 结论

| Gate | 结论 | 证据 |
|------|------|------|
| `WP13-A Runtime Capability Query And Rejection Surface` | pass | `src/runtime/facade/runtime_facade_types.h`、`src/runtime/facade/runtime_facade.cpp`、`src/interfaces/python/bindings_runtime.cpp`、`tests/runtime/facade/test_runtime_facade.py` 与 `tests/runtime/bindings/test_bindings_runtime_dto_surface.py` 暴露保守 profile、budget、evidence 与 rejection metadata，同时保持 exact GPU、resident-state、shadow 与 multi-fidelity support 为 false。 |
| `WP13-B Backend Profile Registry Runtime Gate` | pass | `src/runtime/contracts/backend_profile_contracts.h` 与 `tests/architecture/test_wp13_backend_profile_contracts.py` 定义 code-owned backend profile records、validators、maintained/candidate/diagnostics-only status boundaries 与 fail-closed capability gate helpers。 |
| `WP13-C Parity Budget Evidence Gate` | pass | `src/runtime/contracts/parity_budget_contracts.h` 与 `tests/architecture/test_wp13_parity_budget_contracts.py` 定义 profile-owned parity budget records、comparison domains、mismatch policy、acceptance gate metadata，以及 missing、incompatible、candidate 或 diagnostics-only budgets 的拒绝行为。 |
| `WP13-D Fidelity Profile Request Gate` | pass | `src/runtime/contracts/fidelity_profile_contracts.h` 与 `tests/architecture/test_wp13_fidelity_profile_contracts.py` 定义 `FidelityProfileRequest`、`FidelityProfileAdmissionResult`、CPU exact baseline request helper，并对 unsupported fidelity labels 和 backend claims fail closed。 |
| `WP13-E Facade And Binding Proof` | pass | `src/interfaces/python/bindings_runtime.cpp`、`tests/runtime/bindings/test_bindings_runtime_dto_surface.py`、`tests/runtime/bindings/test_bindings_policy_surface.py`、`tests/runtime/facade/test_runtime_facade.py` 与 `tests/test_gpu_runtime_bindings.py` 证明 profile、budget、capability 与 fidelity admission data 可通过 maintained surfaces 查看，不依赖 raw backend access。 |
| `WP13-F Integration And Acceptance Handoff` | pass | 本审查记录 A-E 状态、validation commands、residuals、route/index updates、Windows-local validation commands 与保守 support boundary。 |

## 3. 验证命令

已在 Windows 本地 checkout 通过：

```powershell
cmake --build build-local-win -j4
python -m pytest -q tests\architecture\test_wp13_fidelity_profile_contracts.py
python -m pytest -q tests\architecture\test_wp13_backend_profile_contracts.py tests\architecture\test_wp13_parity_budget_contracts.py tests\architecture\test_wp13_fidelity_profile_contracts.py
python -m pytest -q tests\architecture\test_runtime_facade_layering.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\bindings\test_bindings_runtime_dto_surface.py tests\runtime\bindings\test_bindings_policy_surface.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py tests\test_gpu_runtime_bindings.py
git diff --check
```

本审查前观察结果：

- Build：通过。
- Focused fidelity request architecture gate：`8 passed`。
- WP13 backend profile、parity budget 与 fidelity contract batch：
  `21 passed`。
- Runtime facade layering guard：`13 passed`。
- Runtime binding 与 policy binding batch：`24 passed`。
- Runtime facade 与 GPU binding batch：`19 passed, 2 skipped`。
- `git diff --check`：通过，仅有 line-ending warnings。

添加本审查后，最终 closure validation 还应运行：

```powershell
python tools\maintenance\wp_doc_closure_audit.py --wp WP13
```

## 4. Runtime Surface 摘要

- `RuntimeCapabilities` 暴露维护中的 CPU exact baseline metadata、candidate
  profile ids、candidate parity budget refs、rejection reasons 与
  multi-fidelity rejection text，同时保持 false support defaults。
- Backend profile records 与 parity budget records 是 code-owned contract data，
  并带 validators 与 negative capability-gate helpers。
- `FidelityProfileRequest` 与 `FidelityProfileAdmissionResult` 暴露 fidelity
  request labels、backend profile id、parity budget ref、model-family scope、
  validation gate、facade evidence refs、unsupported request flags、admission
  status、rejection reason 与 evidence refs。
- Python bindings 暴露 fidelity request/result DTOs，以及
  `make_exact_evaluation_cpu_reference_fidelity_request()` 和
  `admit_fidelity_profile_request()`。

## 5. 保守 Support 声明

唯一被 admission 的 fidelity request 是 CPU exact reference baseline：
`exact_evaluation` with `cpu_exact.reference` and
`parity_budget.cpu_exact.reference.v1`。

下列 claims 仍明确不受支持，不得被 WP13 描述为 maintained：

- `fast_training`、`sensor_heavy`、`weapon_effects_heavy`、
  `large_scale_swarm` 与 `single_platform_physics` fidelity labels。
- Adaptive fidelity scheduling。
- Learned `ModelProvider` runtime admission。
- Approximate execution。
- Exact GPU backend execution。
- Resident-state ownership。
- Device observation views。
- Shadow-backed fidelity 或 shadow compare。
- Maintained multi-fidelity support。

## 6. 剩余工作与下一步

有意后移的 residuals：

- Exact GPU 晋级需要维护中的 backend profile revision、parity budget、
  synchronization/ownership policy、facade evidence 与 validation review。
- Resident-state support 需要显式 ownership、synchronization、state visibility 与
  parity evidence，才能离开 unmaintained-candidate 状态。
- Shadow compare 需要 non-interference rules、diagnostics separation、parity
  scope 与 validation evidence，才能进入 maintained。
- Adaptive fidelity scheduling 与 learned provider runtime 仍属于未来
  architecture/runtime 工作。
- Capability composition 只有在本 backend/fidelity query 与 rejection surface
  保持稳定后才应开启。

建议下一 WP：开启 post-WP9 route 的 capability-composition phase，并保留 WP13 规则：
backend/fidelity capability claims 必须 profile-backed、budget-backed 且 fail
closed。
