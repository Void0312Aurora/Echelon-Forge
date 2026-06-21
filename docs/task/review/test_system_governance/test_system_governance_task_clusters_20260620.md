# Test System Governance Task Clusters

Status: `2026-06-21` accepted finite task-cluster plan for
[README.md](README.md), with residuals retained in
[Test System Residual Governance](../../issues/test_system_residual_governance/README.md).

## Boundary Decision

This subproject may change test governance docs, audit runners, suite manifests,
and selected tests when the replacement preserves or clarifies maintained
coverage. It must not delete business coverage because a file is long, promote a
coverage percentage into a capability claim, or rewrite runtime/model behavior
inside a test-cleanup cluster.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-A` | Main thread | n/a | Create branch, parent review placement, and subproject shell. | `docs/task/review/test_system_governance/**`, `docs/task/review/README*` | No new top-level `docs/task` domain. | Link inspection; `git status --short`. | Standard file set exists and parent links point to it. | Must precede all clusters. | 1 | pass |
| `P1-A` | Main thread | n/a | Land repeatable active-test audit runner and runner tests. | `tools/runners/audit_test_system.py`, `tests/runners/test_audit_test_system.py`, `tests/README.md` | No full-suite execution requirement. | `cmo_python -m pytest -q tests/runners`; `cmo_python -m ruff check ...`; audit runner markdown output. | Runner reports active pytest, contract, smoke, and risk surfaces. | May run with P0-A after branch creation; now used as baseline. | 2 | pass |
| `P1-B` | Future diagnostics worker | n/a | Reconcile audit output, pytest collect count, local `.coverage`, and prior 2026-06-20 coverage review. | `docs/task/review/test_system_governance/*current_status*`, optional coverage note under `docs/task/review/` | No new coverage claim without measured source roots. | `cmo_python -m pytest --collect-only -q tests --ignore=tests/archive`; coverage report command if toolchain available. | Status doc separates static item count, pytest collection count, Python coverage, and C++ coverage. | After P1-A. | 2 | pass |
| `P2-A` | Future implementation worker | n/a | Convert `tests/tools` oversized geometry snapshot checks into smaller invariant or artifact-contract checks. | `tests/tools/test_airframe_geometry_manifest.py`, `tests/tools/test_airframe_geometry_review_cli.py`, shared fixtures if needed | Do not weaken geometry authority boundaries or optional dependency skips. | Focused pytest for touched tests; audit diff before/after. | Risk score and literal/assert concentration drop while behavior gates remain explicit. | After P1-A; serial with other edits to same files. | 3 | accepted with dependency-complete behavior residual |
| `P2-B` | Future implementation worker | n/a | Consolidate repeated damage-model candidate-bundle and closeout-gate test patterns. | `tests/architecture/damage_model/*.py`, `tests/architecture/damage_model/helpers.py` | Do not mark A2/MLF evidence accepted beyond existing acceptance docs. | Focused pytest for touched files; audit diff before/after. | Shared helper/data contract removes duplicated literal-heavy patterns without losing fail-closed checks. | After P1-B recommended; serial for damage-model files. | 3 | accepted oversized-item sweep; file-level residual retained |
| `P2-C` | Future implementation worker | n/a | Decide and document the `weapon_guidance_realism` mixin wrapper pattern. | `tests/runtime/air_combat/weapon_guidance_realism/*.py`, local README/status docs if needed | No behavior rewrite of weapon guidance runtime. | Pytest collect for the package; focused pytest for wrapper modules. | Hidden mixin tests are either justified by docs or converted to clearer semantic test modules. | Can run parallel with P2-A/P2-B if write sets do not overlap. | 2 | accepted documentation; behavior failure retained |
| `P3-A` | Integration worker | n/a | Align suite tiers with maintained smoke/focused/local/manual decisions. | `tests/smoke/*.json`, `tests/suites/README.md`, `tests/README.md`, optional suite manifests | Do not promote broad source scans into smoke wholesale. | `cmo_python -m pytest -q tests/runners/test_pytest_suite_manifests.py`; suite runner smoke command. | Suite manifests encode intentional gate membership and stale paths fail closed. | After at least one P2 cluster. | 2 | pass |
| `P4-A` | Main thread | n/a | Run acceptance validation and record deltas. | Status and acceptance docs; no broad code rewrite. | No overall test-health acceptance without scoped evidence. | Runner tests, focused touched tests, audit markdown, coverage command if available. | Acceptance doc names accepted slice and residuals. | After P2/P3 cluster completion. | 2 | pass |
| `P5-A` | Main thread | n/a | Close accepted slices and archive superseded records. | `README*`, `archive/README.md`, parent `README*`, archive registry if needed | Do not move active records into archive without current pointers. | Link inspection; relevant markdown checks if available. | Parent and local indexes point to current surfaces. | Serial after P4-A. | 1 | pass for current slice |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not allow two workers to edit the same test file, suite manifest, status
  line, or acceptance table concurrently.
- Keep acceptance and closeout clusters serial.
- If a cluster exceeds its round cap, stop and re-scope before adding a
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
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/audit_test_system.py --format markdown --limit 30
cmo_python -m pytest -q tests/runners
cmo_python -m ruff check tools/runners/audit_test_system.py tests/runners/test_audit_test_system.py
```

Focused implementation clusters must add the relevant touched-test pytest
commands before they can move to `pass`.

## Acceptance Criteria

- The audit runner and documentation remain in sync.
- At least one high-risk test cluster is reduced, re-tiered, or converted with
  before/after audit evidence.
- Suite manifest changes are intentional and covered by manifest tests.
- Coverage statements name their measured source roots.
- Residual hardcoded or source-scan tests are mapped to a follow-on tier.

## Residual Map

Retained follow-on issue:

- [Test System Residual Governance](../../issues/test_system_residual_governance/README.md)
  owns the remaining airframe dependency-complete behavior run, damage-model
  file-level literal/source-scan concentration, failing `weapon_guidance_realism`
  package run, and Python/C++ coverage boundary separation.

Deferred:

- Runtime/model algorithm refactors.
- Whole-project coverage enforcement threshold.
- Large-scale deletion of tests without replacement evidence.
