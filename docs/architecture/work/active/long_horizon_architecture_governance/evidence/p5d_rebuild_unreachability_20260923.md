# P5-D Rebuild Unreachability Evidence

Status: `2026-09-27` — the in-kernel composition rebuild has no maintained
production caller or Python binding in the live tree. The production authority
is retired by the owner decision recorded in the [owner acceptance packet](p5d_owner_acceptance_and_rebuild_retirement_20260927.md); the native test seam remains.

## Executable boundary

`tools/maintenance/runtime_rebuild_unreachability.py` inventories the live
source paths and validates the facade-only package boundary. The current
inventory contains only:

- the private native declaration at `src/core/engine/simulation_kernel.h:331`;
- the native implementation at
  `src/core/engine/simulation_kernel.cpp:352-354`; and
- the test-only accessor in `src/core/engine/testing/` and eight test-only
  fault-injection calls in `src/tests/test_simulation_kernel_smoke.cpp`.

The inventory reports zero production callable references and zero references
from `src/interfaces/python`. The production package guard also confirms that
the wheel selects `EF_PRODUCTION_FACADE_ONLY=ON`, keeps diagnostics bindings
opt-in/off, excludes raw core bindings from the production source list, and
does not export `SimulationKernel` from the facade-only binding.

## Verification

Executed in the isolated
`codex/long-horizon-governance-architecture` worktree:

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5d-wheel'
python tools/maintenance/runtime_rebuild_unreachability.py validate
python -m pytest -q --confcutdir tests/architecture `
  tests/architecture/runtime_host/test_runtime_rebuild_unreachability.py
python -m ruff check `
  tools/maintenance/runtime_rebuild_unreachability.py `
  tests/architecture/runtime_host/test_runtime_rebuild_unreachability.py
git diff --check
```

Results: the inventory validated; the focused guard passed **3 tests**; Ruff
and the diff check passed. The fixture digest is
`c757c10a3e2004acff0276b47887be172e572c2c90603ce434eda61543acdc7e`.

## Boundary and next gate

The native method remains available only through the test-only composition
accessor. Production rebuild authority is retired by the owner acceptance
decision; no native test/fault-injection capability is deleted.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p5d_rebuild_unreachability_20260923.md`
Owner: `release/runtime integration`
Last verified: `2026-09-23`
