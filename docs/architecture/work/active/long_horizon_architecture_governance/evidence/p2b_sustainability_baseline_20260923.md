# P2-B Sustainability Baseline Evidence

Status: `2026-09-23` — three repeated local samples passed the current
control, runtime, and retrieval checks; this is a dated baseline, not a
production SLO ratification or overall program acceptance.

The baseline runner combines the P2-A manifest declarations, existing
architecture checks, the real supported-row process/package path, and direct
evidence retrieval. It records durations and outcomes from the same commands
that can be rerun by release/runtime integration. The report is a diagnostic
projection; it does not author rollout or runtime truth.

## Measurement command

Executed in the isolated `codex/long-horizon-governance-architecture`
worktree:

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5d-wheel'
python tools/maintenance/p2b_sustainability_baseline.py `
  --current-build build-long-horizon-p5d-wheel `
  --rollback-build build-long-horizon-p5c-wheel-final3 `
  --runs 3 `
  --process-cycles 1 `
  --output <temporary-report-path>
```

Each of the four check groups ran three times. Each supported-row run started
one current child process and one rollback child process, so the runtime sample
contains three replacement and three backout cycles in addition to the earlier
three-cycle packet.

## Results

| Measurement | Observed result | Owner | Boundary |
| --- | ---: | --- | --- |
| Declared controls | 8 total: 5 permanent, 3 migratory | cross-domain architecture | manifest-level declarations |
| Migratory rows due at simulated `2027-04-01` | 3 | cross-domain architecture | disposition simulation, not a renewal |
| Healthy control check runs | 12/12 passed; 0 healthy-sample failures | cross-domain architecture | current checkout, four groups × three runs |
| Check execution cost | 81.2526470 s total; 6.7710539 s mean per group run | release engineering | local Windows CPython 3.12 process |
| Supported-row SLO runs | 3/3 passed; 3 total cycles | release/runtime integration | current and rollback local builds |
| Replacement success | 1.0 | release/runtime integration | three observed starts |
| Drain completion | 1.0 | release/runtime integration | three observed stops |
| Maximum replacement startup | 0.9332587 s | release/runtime integration | observation, target remains 300 s backout only |
| Maximum backout recovery | 0.8832237 s | release/runtime integration | initial target <= 300 s |
| Caller adoption | 1.0 | release/runtime integration | drill caller path, not full maintained parity |
| Artifact availability | 1.0 | release/runtime integration | three local package reads |
| Safety counters | 0 stale refs, 0 wrong epochs, 0 duplicate publications, 0 security denials | runtime composition/security | healthy path observation |
| Evidence retrieval | 3/3 packets, 10,729 bytes, 1.0 availability | documentation lifecycle | three checked-in evidence packets |

The four check groups and their mean/max durations were:

| Group | Runs | Passed | Mean | Max |
| --- | ---: | ---: | ---: | ---: |
| lifecycle and manifest | 3 | 3 | 10.2888604 s | 10.3574076 s |
| rollout and storage guards | 3 | 3 | 5.4873014 s | 5.8128637 s |
| plan and authority negative guards | 3 | 3 | 4.7051112 s | 4.8945188 s |
| candidate teardown and state-transfer guards | 3 | 3 | 6.6029426 s | 6.8433796 s |

The static audit in the same report observed 519 active test files, 306
`test_*.py` files, 2,733 static test items, 124 smoke entries, 61 contract
JSON files, and 208 risk-flagged Python files. These are size and cost
baselines, not quality scores.

## Interpretation and boundary

The zero healthy-sample failure count is the current false-positive
observation under the declared definition: a failure in an expected-good local
checkout. It is not a historical false-positive rate and does not prove that a
future control cannot reject a valid change. The negative guard group provides
repeatable rejection-path coverage; its passing result does not turn safety
counters into a claim that stale references or skew never occur.

Resource teardown and state-transfer behavior are sampled by the candidate
teardown/state-transfer guard group; a long-term memory/handle budget across
representative workloads remains open. Linux, remote, multi-process, and
production traffic are outside this local baseline. P2-B still requires a
release cadence, broader representative samples, resource-budget evidence,
and an owner review before its exit condition can be marked accepted.

## Verification

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5d-wheel'
python -m pytest -q tests/architecture/governance/test_p2b_sustainability_baseline.py
python -m ruff check `
  tools/maintenance/p2b_sustainability_baseline.py `
  tests/architecture/governance/test_p2b_sustainability_baseline.py
```

Result: **1 integration test passed** and Ruff passed. The integration test
executes the same baseline builder with one repetition and one process cycle;
the dated values above come from the three-repetition command.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p2b_sustainability_baseline_20260923.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-23`
