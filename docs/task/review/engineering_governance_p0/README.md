# Engineering Governance P0

Status: `2026-06-03` local-pass remediation slice for the P0 engineering-discipline findings; remote CI execution remains pending.

Language:

- English canonical: `README.md`
- Chinese companion: `README.zh.md`

Inputs:

- [Review task area](../README.md)
- [Engineering discipline review](../../../engineering/reviews/engineering_discipline_review_20260603.zh.md)
- [Engineering discipline claim verification](../../../evaluation/archive/engineering_discipline_claim_verification_20260603.zh.md)
- [Agent subproject standard](../../../engineering/automation/rules/subproject_creation_standard.md)
- [Subagent usage policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

This subproject implements the first remediation slice from the engineering
discipline review: CI lint gates, reproducible smoke dependency installation,
C++ warning policy, and version-number alignment.

It is intentionally narrow. It does not expand lint rules beyond the current
Ruff baseline, does not make C++ warnings fatal, and does not claim release
readiness.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| CI lint gate | local-pass | `.github/workflows/ci-smoke.yml`; `ruff check .` passed | Gate uses current Ruff rules and changed-file clang-format only. |
| Dependency constraints | local-pass | `requirements/constraints-smoke.txt`; pip dry-run resolved | Smoke/lint constraints are not a full training lockfile. |
| C++ warning policy | local-pass | `CMakeLists.txt`; CMake build passed with warnings visible | Warnings are non-fatal and do not apply to third-party FetchContent targets directly. |
| Version alignment | local-pass | `CMakeLists.txt`, `pyproject.toml` both `0.2.0` | This slice aligns values; it does not introduce a full version-generation system. |

## Scope

In scope:

- Install smoke and lint Python dependencies through `requirements/constraints-smoke.txt`.
- Add CI lint gates for `ruff check` and changed-file `clang-format --dry-run -Werror`.
- Add non-fatal project warning flags for maintained C/C++ targets.
- Align CMake project version with `pyproject.toml`.
- Record verification evidence and residual risks.

Out of scope:

- Expanding Ruff rule selection beyond the current `E9` / `F821-F823` baseline.
- Making C++ warnings fatal.
- Adding clang-tidy as a CI gate.
- Introducing a full release lockfile, package version generator, or multi-platform CI matrix.
- Refactoring source files solely to satisfy future stricter lint policies.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze this narrow toolchain slice. | Engineering review is verified. | Task clusters and non-goals are recorded. | pass |
| `P1 Implementation` | Apply CI, constraints, CMake, and version changes. | Boundary is recorded. | Files are edited and inspectable. | pass |
| `P2 Validation` | Run focused local checks. | Implementation is present. | CI-equivalent checks pass locally; remote CI pending. | pass |
| `P3 Closure` | Sync status and residuals. | Validation is complete. | README/task cluster status reflects evidence. | pass |

## Task Clusters

- Task cluster plan: `engineering_governance_p0_task_clusters_20260603.md`

## Outputs And Evidence

- `.github/workflows/ci-smoke.yml`
- `CMakeLists.txt`
- `requirements/constraints-smoke.txt`
- `requirements/README.md`
- This task subproject and parent review index entries.

Validation evidence:

- `./.venv/bin/python -m ruff check .` passed.
- Changed-file clang-format gate had no C/C++ files in this P0 diff.
- `pip install --dry-run -c requirements/constraints-smoke.txt pytest numpy ruff` resolved.
- `cmake -S . -B build-workshop -DCMAKE_BUILD_TYPE=Release` passed.
- `cmake --build build-workshop --target ef_core ef_py ef_test -j2` passed.
- `ctest --test-dir build-workshop -R ef_test_all --output-on-failure` passed.
- `git diff --check` passed for the touched P0 files.

## Acceptance Gate

This subproject can be marked accepted only when:

- CI installs smoke/lint dependencies through the constraints file.
- CI contains explicit Ruff and clang-format gates.
- Maintained C/C++ targets receive warning flags without applying them to third-party dependency targets.
- `CMakeLists.txt` and `pyproject.toml` agree on the project version.
- Focused local validation commands and any blockers are recorded.

## Residuals And Next Steps

- Expand Ruff rules in a later slice after current-baseline lint is stable.
- Add clang-tidy and sanitizer lanes in later slices.
- Consider a version single-source mechanism after the simple alignment is accepted.
- Clean up the non-fatal C++ warnings now made visible by the warning policy.
- Decide whether to migrate whole-repo Python/C++ formatting or keep changed-file gates.

## Archive

Historical or superseded remediation records should move to `archive/README.md`
only after a replacement current-status surface exists.
