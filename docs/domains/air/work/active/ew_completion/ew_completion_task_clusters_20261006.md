# Air EW Ordered Task Clusters

Document kind: task
Lifecycle: active
Canonical: docs/domains/air/work/active/ew_completion/ew_completion_task_clusters_20261006.md
Owner: domains/air
Last verified: 2026-10-07

Status: `2026-10-07` E1/E2 local gates passed; finite execution plan for
[Air EW Completion](README.md). PR #103-#105 normal checks pass; their reviews
remain open, and #104's CUDA toolchain setup timed out. E3 local gates pass; publication is pending.

## Boundary Decision

Implement E1 through E6 in dependency order. The package may change EW content,
runtime mechanisms, observations, command composition, explicit action modes,
and named acceptance scenarios. Each result needs scoped evidence before the
next cluster depends on it. Engineering mechanism acceptance does not imply
real-platform calibration, learned-policy success, or Air capability promotion.

## Finite Task Cluster List

Capability entries describe risk and ownership, not a model recommendation.
The exact model and reasoning controls are not exposed by this execution packet.

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E1-A | main thread | high shared contract / n/a / n/a | Complete optional RF groups, ESM configuration, transactional loader, schema and state reflection. | `src/components/systems/{sensor,ew,rf_signal}.h`, content loader, reflection/state adapters, database templates, native/content tests, this package and Air indexes | platform RF calibration; active sensing behavior | malformed/missing/nonpositive fields denied; defaults stable; current/legacy state tests | independently compiled contract PR and focused gates pass | first; serial | 1 + 2 repair | active |
| E1-B | main thread | high shared sensing / n/a / n/a | Apply ESM threshold/band/beam gates, age/confirmation, passive DTO and optional Python projection. | default sensor model, ESM reset, observation API/DTO/bindings, Python Air adapter, native/facade tests, this package | canonical action or RL admission; emitter range/position solution | sensitivity boundary, weak/out-of-band, legacy/strict, multi-mount, same-time dedup, weaker refresh, expiry/reset, classification masks | compiled stack head and EW/Python regressions pass | after E1-A; serial | 1 + 2 repair | active |
| E2 | main thread | high EW mechanism / n/a / n/a | Define bounded jammer band/effect/resource behavior and signed DRFM. | EW components, content/schema/reflection, action/sensing systems, observations and focused tests | calibrated J/S; independent ghost tracks without a separate lifecycle contract | inactive/off-band/off-beam/burn-through negatives, budget depletion/recovery, DRFM sign and source identity | authored defaults and effect/resource receipts agree with mechanism tests | after E1; serial | 1 + 2 repair | local-pass / PR #105 checks pass, review pending |
| E3 | main thread | high policy integration / n/a / n/a | Integrate opt-in EW history and maintained temporal policy extraction. | Python Air observation/history, policy extractors, reset/replay and compatibility tests | world-truth inference; training-success claim | absent-key compatibility, first-frame masks, reset, same-seed replay, built-policy consumption | real supported policy path consumes declared history | after E1/E2; serial | 1 + 2 repair | local-pass / publication pending |
| E4 | main thread | high cooperative command / n/a / n/a | Integrate formation EW roles with command loss/latency. | Air command/tasking/formation adapters, maintained transport, cooperative fixtures and tests | bypass of command transport; broader fleet doctrine | delayed/dropped/expired intents, leader loss/reassignment, per-slot isolation, replay | supported formation path preserves roles/resources under failure cases | after E2/E3; serial | 1 + 2 repair | planned |
| E5 | main thread | high public admission / n/a / n/a | Admit a versioned EW action mode through the supported environment. | action-mode registry, environment/config/space mappings, action/native state tests and standards | shifting existing indices; unsupported consumer promotion | factory/space/action/native-state roundtrip; old modes stable; unsupported config rejection | maintained consumer and compatibility gates pass | after E3/E4; serial | 1 + 2 repair | planned |
| E6 | main thread | high terminal acceptance / n/a / n/a | Publish named EW scenario acceptance and residual verdict. | named scenario/contracts, evaluation/replay receipts, capability roster, Air docs | unmeasured playability or learned-policy claim | success/failure/timeout, fixed seeds, measured effects/resources, roster and replay | named acceptance passes with explicit residual owners | after E1-E5; serial final | 1 + 2 repair | planned |

## Dispatch Rules

- Execute serially in the main thread; this packet does not authorize delegated
  agent work.
- Each change belongs to one cluster. Shared contracts, status and acceptance
  updates have one writer.
- Each cluster has one implementation pass and at most two evidence-driven
  repair passes. Re-scope explicitly if that cap is reached.
- Publish larger changes as stacked PRs with independently buildable bases.
- Keep acceptance and closure serial; a published PR is not a merged result.

## Worker Packet Requirements

The main-thread receipt uses the same bounded fields as a worker packet:

```text
status: pass | partial | blocked | failed
cluster:
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan

From the relevant branch checkout, set `CMO_BUILD_DIR` to its configured native
build directory, then use PowerShell:

```powershell
cmake --build $env:CMO_BUILD_DIR --target ef_test ef_py ef_runtime_host_candidate_test
& "$env:CMO_BUILD_DIR/ef_test.exe" --no-colors
& "$env:CMO_BUILD_DIR/ef_runtime_host_candidate_test.exe" --test-suite=simulation_kernel_state_owner_adapters
python -m pytest -q tests/content/test_ew_suite_schema.py tests/runtime/simulation/test_air_observation_adapter.py tests/runtime/simulation/test_facade_ew.py tests/runtime/simulation/test_facade_esm.py tests/runtime/air/test_air_scripted_ew.py tests/runtime/air_combat/test_air_ew_rl_surface.py tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/air_combat/test_air_ew_replay.py
python -m pytest -q tests/architecture/governance/test_docs_information_architecture.py tests/architecture/governance/test_document_link_audit.py
git diff --check
```

E1-A uses the RF-contract, state-owner and content subset before E1-B exists.
E3 acceptance is recorded by `tests/runtime/air_combat/test_air_ew_temporal.py`
plus the temporal extractor, WorldBatch history, Air EW observation and training
entry regression modules. Record later clusters' narrower command and
named-scenario commands in this packet when those surfaces are implemented.

E3 focused local receipts:

```powershell
$env:CMO_BUILD_DIR = 'D:\workshop\Research\Echelon-Forge\build-ew-next'
$env:OMP_NUM_THREADS = '1'
python -m pytest -q tests/runtime/air_combat/test_air_ew_temporal.py
python -m pytest -q tests/training/test_air_combat_training_entry_contracts.py
```

The E3 run passed 8 focused temporal tests, the Air training-entry suite passed
21 tests and 42 subtests, and the broader temporal/EW selection passed 22 tests.
The two known documentation-governance baseline failures are recorded in the
package README and were reproduced on this branch.

## Acceptance Criteria

- E1 passes RF/content/state negatives and compiled sensing/observation
  regressions, with legacy defaults and passive-data boundaries preserved.
- E2-E5 pass their effect/resource, history/policy, command and admission gates
  without changing earlier action indices or inferring hidden truth.
- E6 records named terminal evidence, measured resource/effect outcomes, replay
  and a scoped capability verdict.
- Each stacked PR has independent build evidence, final checks and review;
  merged status is verified before branch/worktree cleanup.

## Residual Map

Immediate: complete review for PRs #103-#105 and close PR #104's CUDA toolchain
setup check, which timed out before source compilation.

Follow-on: publish and validate the E3 PR, then implement E4 cooperative command,
E5 canonical admission, and E6 named terminal acceptance in order.

Deferred: real-platform RF calibration, emitter libraries, antenna sidelobes,
pulse processing, calibrated J/S and independent ghost-track lifecycle.

## E1 stack

1. RF data/content/schema/reflection and passive DTO contracts, with independent
   native tests.
2. ESM runtime/observation/projection and Python adapter regressions, based on PR 1.

Document budget: README, Chinese overview, this task file, and one small E1
contract note if required by the split. Update receipts in place; do not create
additional queues or status ledgers. No cluster is accepted from a script exit
alone; final compiled revision and acceptance scope must be recorded.
