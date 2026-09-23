# P5-D Supported Row Measurement Evidence

Status: `2026-09-23` — three-cycle local measurement passed the initial
P1-C operations targets; this is evidence for the supported row and not a
production cutover or P5-D acceptance.

This packet records repeated observations through the same local process and
package path used by the rollback drill. Each cycle starts a real Windows
CPython 3.12 child process, imports the selected `ef_py` build, constructs a
`RuntimeFacade`, stops it through the process control path, starts the rollback
build in a new process, and records artifact retrieval and caller adoption.
The report is a non-authoritative telemetry projection; the SQLite rollout
controller remains the release and admission authority.

## Measurement command

Executed in the isolated `codex/long-horizon-governance-architecture`
worktree:

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5d-wheel'
python tools/maintenance/p5d_measure_supported_row.py `
  --current-build build-long-horizon-p5d-wheel `
  --rollback-build build-long-horizon-p5c-wheel-final3 `
  --cycles 3 `
  --state-dir <unique-temporary-state-directory> `
  --release-id local-supported-row-cli `
  --plan-sha256 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

The direct script entry point was exercised after adding its repository-root
bootstrap; the focused unit test and Ruff check cover the imported path and
the CLI helper uses the same implementation.

## Observed results

| Metric | Observed result | Initial target | Result |
| --- | ---: | ---: | --- |
| Cycles | 3 | 3 requested | pass |
| Replacement success | 3/3 (1.0) | >= 0.999 | pass |
| Maximum replacement startup | 1.0988426 s | observation only | recorded |
| Drain completion | 3/3 (1.0) | >= 0.99 | pass |
| Maximum backout recovery | 1.1253792 s | <= 300 s | pass |
| Crash receipt deadline breaches | 0/3 | 0 | pass |
| Artifact availability | 3/3 (1.0) | >= 0.999 | pass |
| Caller adoption | 3/3 (1.0) | measured and owned | recorded |
| Child-process resource observation | 6/6 samples available; peak working set 46,186,496 bytes; peak handles 128 | observation only; no approved long-term budget | recorded |
| Safety events | 0 stale refs, 0 wrong epochs, 0 duplicate publications, 0 security denials | zero tolerance | pass |

The report snapshot contains three admission attempts, three replacement
successes, three completed drains, three backout recoveries, three crash
receipts, three artifact retrievals, and three adopted callers. The current
and rollback native binding SHA-256 values were stable across the three
cycles:

- current `ef_py`: `d699fbccfebc8d51ab22bbb4e50504f744a4836c8b99c707482dfaca24909e37`;
- rollback `ef_py`: `46ef11afe9687a865bd3e0a02e51ba7fa03b0c2d42215b8aff7e70f2e8db96cf`.

The SLO evaluator returned `passed: true` with an empty reason list.

The same three-cycle process sample now records a Windows working-set and
handle snapshot for each current/rollback child. Current and rollback samples
were all available; peak working-set observations ranged from 46,018,560 to
46,186,496 bytes and the peak handle count was 128. These are operational
observations only. P2-B still needs an owner-approved long-term resource
budget over representative release changes.

## Verification

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5d-wheel'
python -m pytest -q tests/architecture/runtime_host/test_p5d_supported_row_measurement.py
python -m ruff check `
  tools/maintenance/p5d_measure_supported_row.py `
  tests/architecture/runtime_host/test_p5d_supported_row_measurement.py
```

Results: **1 test passed**; Ruff passed. The CLI run above also completed all
six child-process starts/stops (three current and three rollback) and returned
the passing SLO projection.

## Boundary and remaining work

This is a repeated local Windows CPU-canonical supported-row observation. It
does not establish representative production traffic, full maintained-caller
parity, Linux or remote topology support, long-term rollback-window retention,
or the sole production-canary decision. P2-B still owns the broader cadence,
sample-size, control-yield and sustainability baseline; P5-D still requires
caller cutover, retention through the rollback window, and retirement of
production rebuild authority after those gates.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p5d_supported_row_measurement_20260923.md`
Owner: `release/runtime integration`
Last verified: `2026-09-23`
