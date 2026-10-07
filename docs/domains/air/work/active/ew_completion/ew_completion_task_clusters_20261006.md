# Air EW Ordered Task Clusters

Document kind: task
Lifecycle: active
Canonical: docs/domains/air/work/active/ew_completion/ew_completion_task_clusters_20261006.md
Owner: domains/air
Last verified: 2026-10-07

Status: `2026-10-07` E1/E2 local gates passed; finite execution plan for
[Air EW Completion](README.md). PR #103-#105 normal checks pass; their reviews
remain open, and #104's CUDA toolchain setup timed out. E3 local gates pass;
PRs #106/#107 checks pass and review is pending. E4-A/E4-B local delivery and
formation gates pass; E4-B is PR #108 with checks passed and review pending.
E5 is PR #109 with local admission and remote checks passed, review pending.
E6's named surrogate terminal/replay gate passes locally; causal EW effects,
non-surrogate objectives and stack review remain open.

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
| E3 | main thread | high policy integration / n/a / n/a | Integrate opt-in EW history and maintained temporal policy extraction. | Python Air observation/history, policy extractors, reset/replay and compatibility tests | world-truth inference; training-success claim | absent-key compatibility, first-frame masks, reset, same-seed replay, built-policy consumption | real supported policy path consumes declared history | after E1/E2; serial | 1 + 2 repair | local-pass / PR #106 CI and review pending |
| E4-A | main thread | high shared delivery / n/a / n/a | Add seeded opaque command delivery with delay, loss, expiry, bounded receipts, and node availability; preserve the Joint adapter. | `python/tasking_contracts/common/command_link.py`, Joint adapter/consumer and focused tests | Air role interpretation or native effects | deterministic loss/replay, expiry boundary, unavailable-node cancellation, delayed ordering, Joint inbox TTL, native-link regression | shared transport and existing Joint consumer gates pass | after E3; serial | 1 + 2 repair | local-pass / PR #107 checks pass, review pending |
| E4-B | main thread | high cooperative Air / n/a / n/a | Integrate formation EW role orders over the shared transport. | Air command/tasking/formation adapters, maintained cooperative environment and fixtures | bypass of command transport; broader fleet doctrine; automatic native link/truth mapping | delayed/dropped/expired roles, declared leader loss/reassignment, per-slot isolation, replay and resource isolation | supported formation path preserves bounded self-protection roles/resources under failure cases | after E4-A; serial | 1 + 2 repair | local-pass / PR #108 checks pass, review pending |
| E5 | main thread | high public admission / n/a / n/a | Admit a versioned EW action mode through the supported environment. | action-mode registry, environment/config/space mappings, action/native state tests and standards | shifting existing indices; unsupported consumer promotion | factory/space/action/native-state roundtrip; old modes stable; unsupported config rejection | maintained consumer and compatibility gates pass | after E3/E4; serial | 1 + 2 repair | local-pass / PR #109 checks pass, review pending |
| E6 | main thread | high terminal acceptance / n/a / n/a | Publish named EW scenario acceptance and residual verdict. | named scenario/contracts, evaluation/replay receipts, capability roster, Air docs | unmeasured playability or learned-policy claim | success/failure/timeout rejection, fixed seeds, measured resources/transmission, roster and replay | scoped named acceptance passes with explicit residual owners; causal EW-effect gate stays open | after E1-E5; serial final | 1 + 2 repair | scoped local-pass / CI and review pending |

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

Immediate: complete review for PRs #103-#109 and CI/review for the E6 slice; close
PR #104's CUDA toolchain setup check, which timed out before source compilation.

Follow-on: E5 admission and the named surrogate E6 gate pass locally. Connect
EW effect mechanisms to non-surrogate mission objectives and validate their
causal contribution. Resolve the three reproduced cooperative baseline test failures in a
separate bounded C2/fixture follow-up before claiming general cooperative
closure. Automatic native link/aircraft-loss mapping and support jamming are
not part of E4-B's self-protection permission gate.

Deferred: real-platform RF calibration, emitter libraries, antenna sidelobes,
pulse processing, calibrated J/S and independent ghost-track lifecycle.

## E6 Scoped Acceptance Receipt

Status: `pass` for named engineering-surrogate terminal/resource/transmit/replay
acceptance; `partial` for wider EW effectiveness/playability. Implementation
commit: `ef1073886b5e73749cc7b05aca782d3be1777edb`. The
[machine-readable receipt](artifacts/ew_named_terminal_acceptance_20261007.json)
was produced from that clean tree and the unchanged E2 native build, with the
actual extension hash. E3-E6 change no native source.

| Scenario | Seed | Terminal step | Outcome | Chaff / flare consumed | Native jammer transmit frames | Same-seed replay |
| --- | --- | --- | --- | --- | --- | --- |
| `air_combat_1v1_c2_roe_ew_terminal_v1` | 20260516 | 201 | combat_win | 4 / 4 | 38 | equal |
| same | 20261007 | 204 | combat_win | 5 / 5 | 41 | equal |
| `cooperative_air_2v2_scripted_c2_roe_ew_terminal_v1` | 20260516 | 212 | both combat_win | Lead 5 / 5; Wing 3 / 3 | Lead 44; Wing 48 | equal |
| same | 20261007 | 263 | both combat_win | Lead 3 / 3; Wing 8 / 8 | Lead 24; Wing 80 | equal |

Each slot emits one accepted/native release, maps launch warnings to
countermeasure requests, and preserves roster-owned `Red_A`/`Red_B` targets with
opponent owner counts `[2,0]`. Some request frames have no native transmit
receipt; the trace records those states separately and does not attribute the
difference to a specific cause. Inventory consumption is the measured
pre-terminal lower bound, excluding the auto-reset terminal frame.

```powershell
$env:CMO_BUILD_DIR = 'D:\workshop\Research\Echelon-Forge\build-ew-next'
$env:OMP_NUM_THREADS = '1'
python tools/diagnostics/air_ew_terminal_acceptance.py --json_out docs/domains/air/work/active/ew_completion/artifacts/ew_named_terminal_acceptance_20261007.json
python -m pytest -q tests/runtime/air_combat/test_air_ew_terminal_acceptance.py tests/runtime/air_combat/test_air_combat_ew_scripted_demo.py tests/runtime/air_combat/test_air_cooperative_combat_ew_scripted_demo.py
```

The selection passed 36 tests. Native single-aircraft and cooperative scenarios
with a two-step environment budget both emitted timeout reports and were rejected
by their acceptance validators. Other negative tests mutate real reports to
reject loss, unfinished members, exhausted acceptance budgets, missing inventory
change, missing transmit state, post-reset samples, missing baseline, incorrect
roster ownership, missing slot arrays and replay drift. Full combat-loss dynamics
remain unverified. CLI replay cannot be skipped.

### Residual Owners

| Residual | Owner / next evidence | Closure boundary |
| --- | --- | --- |
| Non-surrogate EW mission and causal effect | Air EW/scenario validation: connect native decoy capture or radar denial to declared objective, with mechanism-off negative controls | surrogate wins and inventory/transmit receipts cannot close this gate |
| Real-platform RF, J/S, seeker and vulnerability calibration | Air content/physics validation: traceable platform data and calibrated cross-seed effects | no numerical performance claim from authored proxy defaults |
| Native link/loss mapping and escort/support jamming | Air tasking/runtime: declared native communication inputs and support-effect ownership | E4-B only grants self-protection permission |
| Independent DRFM ghost tracks | Air sensing/EW: track identity, association, expiry/reset and deception negatives | same-target range offset is insufficient |
| Three cooperative baseline failures and command-queue saturation | Air C2/runtime: separate bounded fixture/queue investigation; earlier direct probes emitted pending-queue-full warnings, while the frozen E6 matrix log had none | terminal success does not establish full cooperative/C2 closure; saturation was not stress-tested |
| PR review, #104 CUDA provisioning and visualization/playable gate | Maintainer/CI and Air acceptance: final checks/review, toolchain run and render/process evidence | keep stack open and Air label `playable_candidate` / EW review `entry_surface_incomplete` |

The package remains active. These are role owners and required evidence,
not newly dispatched implementation work or a promotion decision.

## E1 stack

1. RF data/content/schema/reflection and passive DTO contracts, with independent
   native tests.
2. ESM runtime/observation/projection and Python adapter regressions, based on PR 1.

Document budget: README, Chinese overview, this task file, and one small E1
contract note if required by the split. Update receipts in place; do not create
additional queues or status ledgers. No cluster is accepted from a script exit
alone; final compiled revision and acceptance scope must be recorded.
