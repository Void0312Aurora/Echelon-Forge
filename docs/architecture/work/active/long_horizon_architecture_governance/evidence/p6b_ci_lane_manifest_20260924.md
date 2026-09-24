# P6-B CI Lane Manifest Baseline

Date: `2026-09-24`

This packet records the first executable P6-B slice. The maintained source is
`tests/suites/ci_lane_manifest.json`; the checker is
`tools/runners/audit_ci_lanes.py`. The checker does not create a second test
registry and does not change the P7 archive-retention policy.

## Lane declaration

| Lane | Workflow job | Runner | Timeout | Build/test parallelism | Native selector |
| --- | --- | --- | ---: | ---: | --- |
| `fast` | `ci-smoke.yml / fast` | `ubuntu-latest` | 15 min | 2 / 1 | `fast` |
| `qualification` | `ci-smoke.yml / p5b-windows-qualification` | `windows-latest` | 30 min | 2 / 1 | `qualification`, `p5b` |
| `nightly` | `coverage-baseline.yml / coverage-baseline` | `ubuntu-latest` | 45 min | 2 / 1 | `nightly` |
| `release` | `ci-smoke.yml / build-and-test` | `ubuntu-latest` | 30 min | 2 / 1 | `release` |
| `research` | `ci-cuda-compile.yml / cuda-compile` | `ubuntu-latest` | 45 min | 2 / 1 | `research` |

The workflow jobs retain their existing build/package boundaries. The new fast
job exercises the low-cost native labels and lane/authority audits. The
Windows qualification job selects the three P5-B native tests through the
secondary `p5b` label. The release job selects the release-labelled native
surface and then runs the existing broad `ef_test_all` smoke target. The
nightly job selects the nightly-labelled native surface while retaining its
coverage artifact publication. The research job remains compile/link-only;
runtime CUDA execution still requires a GPU host.

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
three workflows; the focused lane/CTest subset passed `6` tests and the
combined lane/authority/manifest set passed `18` tests. Ruff and the diff
check passed. The configured Windows build
was re-generated and the CTest inventory exposed the `p5b` and `fast` labels;
the local native binaries were not rebuilt to completion because that existing
MSVC build is a large dependency graph, so this packet does not claim a full
native lane run.

## Boundary

This is a P6-B implementation baseline, not P6 acceptance. Repeated CI runs,
duration/resource/flake measurements, failure-routing drills, and branch
protection confirmation remain open. P6-A source-scan replacement/retirement
evidence and P7 archive-specific policy work are also unchanged.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p6b_ci_lane_manifest_20260924.md`
Owner: `release-engineering`
