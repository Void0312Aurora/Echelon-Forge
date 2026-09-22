# Long-Horizon Architecture Governance P5-C Independent Review

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/architecture/reviews/long_horizon_architecture_governance_p5c_review_20260922.md`
Review scope: P5-C production facade-only package and diagnostics boundary
Review basis: independent source, build, link-map, wheel, and runtime recheck
Review date: `2026-09-22`

## Verdict

`pass_with_repairs` for the supported Windows/MSVC, CPython 3.12,
local single-process CPU-canonical topology.

The reviewed package does not expose raw engine/GPU bindings. The raw engine
and world implementation is retained behind the private shared
`ef_facade_backend.dll` and is not exported to the Python extension. This
follows the P1-A rule that the maintained CPU backend may remain private behind
the facade host while never becoming a caller-visible ownership surface.

This verdict does not authorize P5-D caller cutover, production canary
publication, rollback authority changes, CUDA promotion, cross-platform
qualification, or P8 closure.

## Rechecked Gates

- Production `ef_py` build completed with `EF_PRODUCTION_FACADE_ONLY=ON`.
- `dumpbin /exports ef_facade_backend.dll` showed `RuntimeFacade` methods and
  no `SimulationKernel`, `WorldBatchRuntime`, or GPU-helper exports.
- The production pyd import table contained `ef_facade_backend.dll` and no
  direct `ef_core` or `ef_gpu_experiments` dependency.
- The fresh wheel
  `artifacts/p5c-wheel-final3/cmo-0.2.0-cp312-cp312-win_amd64.whl` was
  verified with SHA-256
  `4BC32143E2CC9D2EE880A30A4B534F96D8DB6C3186252C5DA98FAF8928D81D67`.
- The wheel contained `ef_py.pyd` and `ef_facade_backend.dll`, no diagnostics
  module, and no candidate adapter.
- A new venv imported the wheel from its own `site-packages`, completed
  `RuntimeFacade` construction, `WorldBatchVecEnv` reset/step, and visual
  reset/step with `(1, 24, 48, 10)` tensors.
- The explicit diagnostics build/import passed with
  `EF_BUILD_DIAGNOSTICS_BINDINGS=ON` and exposed the intended raw diagnostic
  names only in `ef_py_diagnostics`.
- Architecture/facade gates: **20 passed**; visual VecEnv gates: **2 passed**;
  `git diff --check`: passed.

## Findings And Residuals

1. The earlier static-backend direct-link concern is closed by the shared
   private backend and explicit `RuntimeFacade` export/import boundary.
2. Maintained mission/geometry and visual/execution observation helpers remain
   compiled into the production extension. They are contract/helper
   implementation sources, not world-step owners; raw engine ownership remains
   in the private backend.
3. The export class currently exposes a wider C++ facade ABI than strictly
   necessary, including a few private facade methods. This is low-risk ABI
   hygiene and does not expose raw engine/GPU owners.
4. Qualification is limited to the Windows/MSVC row tested here. P6-P8 own
   broader CI/platform/topology and final acceptance matrices.
