# P5-D Maintained Caller Parity Evidence

Status: `2026-09-25` — the bounded default CPU-exact maintained caller set is
migrated and now has a dedicated executable parity gate. This packet does not
claim production publication or a production cutover.

## Scope

The gate covers maintained Python runtime paths under `python/rl/runtime`,
`python/testing/contracts`, `python/tasking_contracts`, `gym_envs`,
`examples/viz/web_viz`, and `tools/maintenance`, plus the standalone native
caller in `src/main.cpp`. It reuses the P8-A closure's AST inventory, which
rejects direct, aliased, wildcard, and recognized literal-dynamic
`ef_py.SimulationKernel` or `ef_py.WorldBatchRuntime` calls. Non-literal
dynamic loaders remain outside this lexical gate and require the separate
closure/compatibility classification. The native check reuses the closure C++
inventory and additionally requires the real facade include, construction, and
setup/step calls.

Diagnostic and compatibility paths are not silently reclassified as maintained
callers. They remain inventoried by the P8-A composition closure and retain
their explicit compatibility disposition.

The bounded gate intentionally excludes `tools/diagnostics/**`,
`tools/geometry/**`, archived material, copied `artifacts/**`, and test-only
sources. Those surfaces are not unowned: the closure inventory classifies
diagnostic Python callers as `simulation_kernel.default_compatibility`, the
native P4-C candidate as `simulation_kernel.build_tree_candidate`, and test
fault injection as `simulation_kernel.test_fault_injection`. The native scan
also keeps the build-tree candidate out of the production default-caller
inventory by design; its separate P4-C gate remains authoritative.

## Verification

Executed in the isolated `codex/long-horizon-governance-architecture`
worktree:

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5c-shared'
powershell -NoProfile -ExecutionPolicy Bypass -File tools/maintenance/cmo_env.ps1 `
  python -m pytest -q tests/architecture/runtime_host/test_p5d_maintained_caller_parity.py
python tools/maintenance/runtime_composition_migration_closure.py validate
```

Results: **4 parity tests passed** and the composition closure validator passed.
The gate therefore records the caller-migration boundary as complete for the
maintained local topology. It does not authorize the compatibility bindings,
unsupported platforms, production release publication, or rebuild retirement.

## Remaining P5-D operational gates

- an authorized production-canary RolloutDecision and caller-cutover
  attestation;
- representative release-cadence evidence (owned by P2-B);
- an actual production rollback-window observation; and
- activation of the fail-closed rebuild-retirement proof after those inputs.

These are operational inputs, not missing maintained-caller code in this
branch.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p5d_maintained_caller_parity_20260925.md`
Owner: `release/runtime integration`
Last verified: `2026-09-25`
