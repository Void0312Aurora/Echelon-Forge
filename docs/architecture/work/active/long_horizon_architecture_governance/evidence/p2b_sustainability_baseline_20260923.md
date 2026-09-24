# P2-B Sustainability Baseline Evidence

Status: `2026-09-25` — three repeated local samples passed the current
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
| Declared controls | 7 total at the 2026-09-25 measurement: 5 permanent, 2 migratory | cross-domain architecture | manifest-level declarations; one zero-entry migratory control was retired by P7-B on 2026-09-24 |
| Migratory rows due at simulated `2027-04-01` | 2 | cross-domain architecture | disposition simulation, not a renewal |
| Healthy control check runs | 12/12 passed; 0 healthy-sample failures | cross-domain architecture | current checkout, four groups × three runs |
| Check execution cost | 281.8896640 s total; 23.4908053 s mean per group run | release engineering | local Windows CPython 3.12 process |
| Supported-row SLO runs | 3/3 passed; 3 total cycles | release/runtime integration | current and rollback local builds |
| Release cadence identity | 3 logical release IDs, 1 plan digest, 1 current/rollback package pair; `local_repeat_only` | release/runtime integration | three repetitions of the same local builds, not representative release changes |
| Replacement success | 1.0 | release/runtime integration | three observed starts |
| Drain completion | 1.0 | release/runtime integration | three observed stops |
| Maximum replacement startup | 1.4249537 s | release/runtime integration | observation, target remains 300 s backout only |
| Maximum backout recovery | 1.4229253 s | release/runtime integration | initial target <= 300 s |
| Caller adoption | 1.0 | release/runtime integration | drill caller path, not full maintained parity |
| Artifact availability | 1.0 | release/runtime integration | three local package reads |
| Child-process resource observation | 6/6 working-set/handle samples available; max peak working set 47,042,560 bytes; max peak handles 135 | release/runtime integration | three-cycle supported-row sample; observation only |
| Safety counters | 0 stale refs, 0 wrong epochs, 0 duplicate publications, 0 security denials | runtime composition/security | healthy path observation |
| Evidence retrieval | 3/3 packets, 13,706 bytes, 1.0 availability | documentation lifecycle | three checked-in evidence packets |

The four check groups and their mean/max durations were:

| Group | Runs | Passed | Mean | Max |
| --- | ---: | ---: | ---: | ---: |
| lifecycle and manifest | 3 | 3 | 30.7147732 s | 32.4234440 s |
| rollout and storage guards | 3 | 3 | 17.4418202 s | 26.5681502 s |
| plan and authority negative guards | 3 | 3 | 28.3013887 s | 30.5363935 s |
| candidate teardown and state-transfer guards | 3 | 3 | 17.5052392 s | 32.5198311 s |

The static audit in the same report observed 528 active test files, 314
`test_*.py` files, 2,762 static test items, 125 smoke entries, 61 contract
JSON files, and 208 risk-flagged Python files. These are size and cost
baselines, not quality scores.

The report now preserves each run's release ID, plan digest, observed package
digests, cycle count, and SLO outcome. In this three-run sample the IDs were
`p2b-baseline-1`, `p2b-baseline-2`, and `p2b-baseline-3`, but the plan digest
was `b` repeated 64 times and every cycle used the same package pair:

| Package | SHA-256 |
| --- | --- |
| Current Windows binding | `d699fbccfebc8d51ab22bbb4e50504f744a4836c8b99c707482dfaca24909e37` |
| Rollback Windows binding | `46ef11afe9687a865bd3e0a02e51ba7fa03b0c2d42215b8aff7e70f2e8db96cf` |

The classifier counts observed per-cycle pairs rather than combining
unrelated current and rollback digests. A changed pair across internally
consistent batches is reported as `distinct_package_batches_observed`; a
changed pair within one batch or an incomplete digest needs disposition.
Even a distinct-batch observation leaves `representative_release_cadence`
open until actual release changes, cadence, and owners are qualified. This
sample cannot close that gate.

## Interpretation and boundary

The zero healthy-sample failure count is the current false-positive
observation under the declared definition: a failure in an expected-good local
checkout. It is not a historical false-positive rate and does not prove that a
future control cannot reject a valid change. The negative guard group provides
repeatable rejection-path coverage; its passing result does not turn safety
counters into a claim that stale references or skew never occur.

Resource teardown and state-transfer behavior are sampled by the candidate
teardown/state-transfer guard group; a long-term memory/handle budget across
representative workloads remains open. The supported-row process sample now
also records six available Windows working-set/handle observations, with a
maximum peak working set of 46,186,496 bytes and 128 handles; those values are
not an approved budget or a leak verdict. Linux, remote, multi-process, and
production traffic are outside this local baseline. P2-B still requires a
release cadence, broader representative samples, an owner-approved resource
budget, and an owner review before its exit condition can be marked accepted.

## Verification

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5d-wheel'
python -m pytest -q tests/architecture/governance/test_p2b_sustainability_baseline.py
python -m pytest -q tests/architecture/runtime_host/test_p5d_supported_row_measurement.py
python -m ruff check `
  tools/maintenance/p2b_sustainability_baseline.py `
  tools/maintenance/p5d_measure_supported_row.py `
  tests/architecture/governance/test_p2b_sustainability_baseline.py
```

Result: **1 integration test passed**, the cadence classifier and
supported-row identity tests passed, and Ruff passed. The
integration test executes the same baseline builder with one repetition and
one process cycle; the dated values above come from the three-repetition
command.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p2b_sustainability_baseline_20260923.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-25`
