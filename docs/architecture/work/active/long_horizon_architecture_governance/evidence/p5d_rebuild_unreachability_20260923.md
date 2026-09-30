# P5-D Rebuild Unreachability Evidence

Status: `2026-09-23` — the in-kernel composition rebuild has no maintained
production caller or Python binding in the live tree. This is a pre-cutover
quarantine record; it does not retire the native capability or authorize the
production canary.

## Executable boundary

`tools/maintenance/runtime_rebuild_unreachability.py` inventories the live
source paths and validates the facade-only package boundary. The current
inventory contains only:

- the native declaration at `src/core/engine/simulation_kernel.h:187`;
- the native implementation at
  `src/core/engine/simulation_kernel.cpp:352-354`; and
- eight test-only fault-injection calls in
  `src/tests/test_simulation_kernel_smoke.cpp` at lines 79, 86, 97, 103, 140,
  191, 201, and 243.

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
`6474dbcd144b2769ce81fa74df8bff05990d0581db027b3c49a094db63557022`.

## Boundary and next gate

The native method remains available to the existing test-only composition
smoke coverage. Retirement requires the single P5-D production cutover, a
durable rollback-window retention check, and the accepted rebuild-retirement
gate after that window. No production truth publication or rebuild retirement
is claimed by this packet.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p5d_rebuild_unreachability_20260923.md`
Owner: `release/runtime integration`
Last verified: `2026-09-23`
