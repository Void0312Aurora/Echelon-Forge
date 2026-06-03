# Engineering Governance P0 Task Clusters

Status: `2026-06-03` local-pass finite task-cluster record for `engineering_governance_p0`; remote CI execution remains pending.

## Boundary Decision

This remediation slice implements only the immediate P0 engineering gates from
the verified engineering-discipline review. The work is serial in this run
because CI, constraints, CMake, and task-status edits share the same acceptance
surface and the worktree already contains unrelated concurrent changes.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-A` | main thread | n/a | Record the narrow remediation boundary and task clusters. | `docs/task/review/engineering_governance_p0/**`, `docs/task/review/README*` | Broad roadmap rewrite, archive moves | Markdown inspection | Subproject has README and finite cluster plan. | First; serial | 1 | pass |
| `P0-B` | main thread | n/a | Wire CI dependency constraints and lint gates. | `.github/workflows/ci-smoke.yml`, `requirements/constraints-smoke.txt`, `requirements/README.md` | Ruff rule expansion, clang-tidy gate, CI matrix | `ruff check .`; pip dry-run; shell syntax inspection | CI installs through constraints and has Ruff + changed-file clang-format gates. | After P0-A; serial | 2 | pass |
| `P0-C` | main thread | n/a | Align version and add non-fatal C/C++ warning policy. | `CMakeLists.txt` | Warnings-as-errors, sanitizer lane, target split | CMake configure/build smoke | Version matches `pyproject.toml`; project targets have warning flags. | After P0-A; serial with P0-B in this run | 2 | pass |
| `P0-D` | main thread | n/a | Run focused validation and record blockers. | task status docs only if needed | Full test suite, unrelated source cleanup | `ruff`, `cmake`, `ctest`, changed-file clang-format local check | Pass/fail evidence is recorded honestly. | After P0-B/P0-C | 1 | pass |
| `P0-E` | main thread | n/a | Integrate status, residuals, and parent review index. | `docs/task/review/README*`, this subproject README | Claim release readiness | Markdown inspection, `git diff --check` | Status and residuals match validation evidence. | Last; serial | 1 | pass |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- This run keeps all clusters in the main thread because the modified files are
  tightly coupled and the current worktree has unrelated parallel edits.
- Do not allow separate workers to edit `.github/workflows/ci-smoke.yml`,
  `requirements/constraints-smoke.txt`, or the same status table concurrently.
- If any cluster exceeds its round cap, stop and re-scope before adding a
  follow-up wave.
- Follow [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md).

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan

```bash
./.venv/bin/python -m ruff check .
base_ref=HEAD
mapfile -d '' cpp_files < <(git diff --name-only -z --diff-filter=ACMR "${base_ref}" -- '*.cpp' '*.h' '*.hpp')
if (( ${#cpp_files[@]} > 0 )); then
  printf '%s\0' "${cpp_files[@]}" | xargs -0 clang-format --dry-run -Werror
fi
cmake -S . -B build-p0-governance -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build-p0-governance --target ef_core ef_py ef_test -j2
ctest --test-dir build-p0-governance -R ef_test_all --output-on-failure
git diff --check -- .github/workflows/ci-smoke.yml CMakeLists.txt requirements docs/task/review/engineering_governance_p0 docs/task/review/README.md docs/task/review/README.zh.md
```

## Acceptance Criteria

- P0-B and P0-C implementation files are updated.
- Focused validation has pass/fail evidence.
- Any remaining blocker is explicit and assigned to a follow-on slice.

## Validation Evidence

```text
ruff check .: pass
changed-file clang-format gate: pass, no C/C++ files in this P0 diff
pip install --dry-run -c requirements/constraints-smoke.txt pytest numpy ruff: pass
cmake configure build-workshop: pass
cmake build ef_core ef_py ef_test: pass, non-fatal warnings visible
ctest -R ef_test_all: pass
git diff --check for touched P0 files: pass
```

## Residual Map

Immediate:

- Remote GitHub Actions execution is still pending.
- Non-fatal C++ warnings are now visible and need a cleanup slice before any warnings-as-errors lane.
- Whole-repo Ruff formatting and clang-format still have large existing baseline debt; this P0 uses `ruff check` and changed-file clang-format only.

Follow-on:

- Ruff rule expansion.
- clang-tidy CI lane.
- sanitizer CI lane.
- version single-source mechanism.

Deferred:

- Full release lockfile and multi-platform CI matrix.
