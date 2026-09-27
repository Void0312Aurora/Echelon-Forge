# P5-D Owner Acceptance and Rebuild Retirement

Status: `2026-09-27` — accepted by the project owner for continuation of the
main plan; the legacy in-place rebuild has lost production authority.

## Decision

The project owner explicitly accepts the current P5-D result and authorizes
retirement of the old production rebuild path. This packet is the governing
decision for this branch; it does not invent production telemetry that is not
present in the repository.

The retirement scope is production authority only:

- `SimulationKernel::rebuild_world_composition` is no longer public;
- the only remaining caller is the test-only
  `SimulationKernelCompositionTestAccess` accessor;
- the native test/fault-injection capability remains available for regression
  and rollback coverage;
- the executable inventory records
  `retired_production_authority_test_seam_retained` and `retired: true`.

## Verification

- `ef_test --test-suite=simulation_kernel_smoke`: **41 test cases, 889
  assertions passed**;
- `runtime_rebuild_unreachability.py validate`: passed;
- P5-D retirement/reachability Python gates: **12 passed**;
- `git diff --check`: passed.

## Boundary

The repository now treats the old rebuild route as retired production
authority. The test seam is intentionally retained; this is not a deletion of
native fault-injection coverage. Subsequent P6/P7/P8 work proceeds without
waiting for a separate production-observation packet.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p5d_owner_acceptance_and_rebuild_retirement_20260927.md`
Owner: `project owner / release-runtime integration`
Last verified: `2026-09-27`
