# P6-B CI Lane Manifest Baseline

Date: `2026-09-27`

This packet records the first executable P6-B slice. The maintained source is
`tests/suites/ci_lane_manifest.json`; the checker is
`tools/runners/audit_ci_lanes.py`. The checker does not create a second test
registry and does not change the P7 archive-retention policy.

## Lane declaration

| Lane | Workflow job | Runner | Timeout | Build/test parallelism | Declared labels / workflow selector |
| --- | --- | --- | ---: | ---: | --- |
| `fast` | `ci-smoke.yml / fast` | `ubuntu-latest` | 15 min | 2 / 1 | `fast` / `fast` |
| `qualification` | `ci-smoke.yml / p5b-windows-qualification` | `windows-latest` | 30 min | 2 / 1 | `qualification`, `p5b` / `p5b` |
| `nightly` | `coverage-baseline.yml / coverage-baseline` | `ubuntu-latest` | 45 min | 2 / 1 | `nightly` / `nightly` |
| `release` | `ci-smoke.yml / build-and-test` | `ubuntu-latest` | 30 min | 2 / 1 | `release` / `release` |
| `research` | `ci-cuda-compile.yml / cuda-compile` | `ubuntu-latest` | 45 min | 2 / 1 | `research` / none (compile/link only) |

The workflow jobs retain their existing build/package boundaries. The manifest
now distinguishes labels declared as available from labels actually selected
by each workflow. The new fast job selects the low-cost `fast` label and runs
the lane/authority audits. The Windows qualification job selects the four
P5-B native tests through the secondary `p5b` label. The release job selects
the release-labelled native surface and then runs the existing broad
`ef_test_all` smoke target. The nightly job selects the nightly-labelled
native surface while retaining its coverage artifact publication. The research
job declares its compile-only audience but selects no CTest label; runtime CUDA
execution still requires a GPU host.

## Verification

```powershell
python tools/runners/audit_ci_lanes.py --format markdown
$env:CMO_BUILD_DIR='build-long-horizon-p5c-shared'
$env:PYTHONPATH="$PWD\build-long-horizon-p5c-shared\Debug;$PWD"
python -m pytest -q `
  tests/runners/test_ci_lane_manifest.py `
  tests/architecture/build_system/test_ctest_lane_labels.py `
  tests/runners/test_pytest_suite_manifests.py
python -m ruff check tools/runners/audit_ci_lanes.py tests/runners/test_ci_lane_manifest.py
git diff --check
```

Observed result: the lane audit reports five lanes, five workflow jobs, and
three workflows; the focused lane/CTest subset passed `7` tests and the
combined lane/authority/manifest set passed `19` tests. Ruff and the diff
check passed. The configured Windows build
was re-generated and the CTest inventory exposed the `p5b` and `fast` labels;
the local native binaries were not rebuilt to completion because that existing
MSVC build is a large dependency graph, so this packet does not claim a full
native lane run.

## Local repeat probe

While hosted CI is unstable, the maintained lane declaration and selector
checks were repeated locally three times. Each repetition ran
`audit_ci_lanes.py --format json` followed by the 16-test lane/CTest/manifest
subset:

| Repeat | Audit exit | Test exit | Elapsed |
| ---: | ---: | ---: | ---: |
| 1 | 0 | 0 | 35.850 s |
| 2 | 0 | 0 | 35.592 s |
| 3 | 0 | 0 | 35.561 s |

This establishes repeatable local declaration and workflow-selector behavior
only. It
does not claim hosted-runner resource/flake evidence, branch-protection
enforcement, or a completed native build. The refreshed run used the current
`codex/long-horizon-governance-architecture` checkout after the P7-B control
retirement and document-census commits. The selector subset itself passed
**16 tests** on the same configured build.

## Hosted control-plane check

A read-only GitHub API check on `2026-09-25` found no protected `main` branch
(`GET /branches/main/protection` returned `404 Branch not protected`) and no
repository rulesets (`GET /rulesets` returned an empty list). The repository's
recent workflow runs therefore cannot be treated as branch-protection evidence;
hosted resource/flake and failure-routing evidence remain open.

## Boundary

This is a P6-B implementation baseline, not P6 acceptance. Hosted repeated
CI runs, duration/resource/flake measurements, failure-routing drills, and
branch protection confirmation remain open; the local repeat probe above is
not a substitute. P6-A source-scan replacement/retirement evidence and P7
archive-specific policy work are also unchanged.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p6b_ci_lane_manifest_20260924.md`
Owner: `release-engineering`
