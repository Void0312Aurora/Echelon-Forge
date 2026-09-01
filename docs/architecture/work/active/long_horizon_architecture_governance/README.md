# Long-Horizon Architecture Governance

Status: `2026-08-31` active long-horizon architecture-governance program; P0
authority and baseline, P1 target-architecture decisions, the complete
P3-A/P3-B/P3-C contract, authority-envelope, ledger, and compatibility
foundations, and P4-A dark/shadow host lifecycle are accepted after independent
review. P4-B candidate implementation is complete on the isolated branch;
independent integrated review is pending and production acceptance is not
granted. P2-A/P2-B, P4-C and P5-P8 remain open; no production truth
publication, runtime caller migration, or production cutover is accepted yet.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/README.md`
Owner: `cross-domain architecture`
Last verified: `2026-08-31`

Related authority:

- [Architecture owner](../../../README.md)
- [Simulation system architecture design](../../../standards/simulation_system_architecture_design.md)
- [Runtime workflow and contract baseline](../../../standards/runtime_workflow_and_contract_baseline.md)
- [Runtime composition baseline](../../../standards/runtime_composition_baseline.md)
- [Archived Cordis composition program](../../archive/cordis_simulation_composition_kernel/README.md)
- [Document lifecycle policy](../../../../engineering/documentation/standards/document_lifecycle_policy.md)
- [Subproject creation standard](../../../../engineering/automation/rules/subproject_creation_standard.md)
- [Subagent usage policy](../../../../engineering/automation/standards/subagent_usage_policy.md)
- [Independent P0-B plan review](../../../reviews/long_horizon_architecture_governance_plan_review_20260825.md)
- [P1-A host lifecycle and episode authority decision](decisions/p1a_host_lifecycle_and_episode_authority_decision_20260825.md)
- [P1-B plan and RunReceipt authority decision](decisions/p1b_plan_and_run_receipt_authority_decision_20260825.md)
- [P1-C rollout, operations and security decision](decisions/p1c_rollout_operations_and_security_decision_20260825.md)
- [Independent P1 architecture review](../../../reviews/long_horizon_architecture_governance_p1_review_20260825.md)

## Purpose

This program changes how Echelon Forge evolves its runtime architecture and how
architecture controls are created, promoted, renewed, and retired. It is not a
repository-cleanup wave and must not be redefined as a short-term test, CI, or
documentation reduction project.

The long-horizon outcome is an immutable admitted kernel constructed from one
closed executable plan, replacement owned by a host-level lifecycle boundary,
production bindings physically restricted to facade contracts, and governance
controls that expire or renew instead of accumulating after every migration.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Runtime composition | accepted bounded default CPU-exact baseline | [runtime composition standard](../../../standards/runtime_composition_baseline.md) and [`SimulationKernel`](../../../../../src/core/engine/simulation_kernel.cpp) | accepted construction and evidence do not prove that in-kernel rebuild has a production consumer |
| Composition replacement | implemented but strategically unresolved | `rebuild_world_composition`, mutation barriers, raw-world quarantine, scope generations, and handover machinery | no maintained non-test caller or binding currently requires in-place kernel rebuild |
| Runtime boundary | facade direction accepted; compatibility surfaces remain | [runtime facade guards](../../../../../tests/architecture/runtime_facade/test_runtime_escape_hatches.py) | source scans describe the boundary but do not make it physically unrepresentable |
| Contract and evidence chain | complete for the accepted default profile | request, catalog lock, projection, requested/resolved manifests, provenance, parity, and closure artifacts | intermediate migration artifacts remain permanent governance inputs |
| Public/runtime authority boundary | P3-A/P3-B/P3-C and P4-A accepted; P4-B implementation complete, independent review pending | [`ef_runtime_contracts`](../../../../../include/echelon_forge/runtime_contracts/runtime_identity.h), [`RuntimeHostCandidate`](../../../../../src/runtime/host/runtime_host_candidate.h), [P4-B candidate](p4b_state_transfer_candidate_20260830.md), twelve-row owner adapters, exact vectors, non-production ArtifactLedger simulator, fresh Windows/MSVC native gates and [P4-A independent review](../../../reviews/long_horizon_architecture_governance_p4a_review_20260827.md) | P4-A/B remain dark/shadow only; independent P4-B review, P4-C integration, and P5-B/P5-D production durability, authenticity, activation and cutover remain gated |
| Test and CI governance | verified CI smoke was green; full governance audit is not | [CI smoke suite](../../../../../tests/smoke/ci_smoke_suite.json), [governance audit suite](../../../../../tests/suites/governance_audit_suite.json), and `test_archive_retirement.py` | the remote baseline tracks 20 owner-archive documents that fail the retirement gate |
| Documentation lifecycle | policy, gate, and repository route conflict | [document lifecycle policy](../../../../engineering/documentation/standards/document_lifecycle_policy.md), subproject standard, and current architecture archive | standards admit owner-local archives while the maintained gate prohibits every `docs/**/archive/**` path |

## Scope

In scope:

- choose and implement the long-term immutable-kernel and host-owned replacement architecture;
- define the host lifecycle state machine, publication linearization point, epoch/fencing/lease model, unique episode-barrier authority, drain/reclamation rules, and complete state-transfer census;
- consolidate runtime composition interchange and run evidence into the minimum durable contract chain;
- support mixed-version producer/native/wheel rollout with single-writer, bounded dual-reader, canary/shadow, rollback-window, and backout semantics;
- replace source-text boundary governance with CMake target, header visibility,
  package, type, runtime-contract, and behavior boundaries;
- establish a lifecycle for architecture controls, including ownership, detection purpose, renewal, expiration, replacement, and retirement;
- redesign test and CI lanes around feedback purpose without weakening native, facade, wheel, replay, parity, or CPU-canonical correctness;
- move historical acceptance and evidence out of permanent execution authority while retaining reproducible provenance;
- migrate existing callers, compatibility paths, documentation, and evidence without creating a second runtime truth;
- define supported platform/process topologies, operational owners, lifecycle SLOs, adoption telemetry, and fail-closed multi-process/external-host activation gates.

Out of scope:

- weakening deterministic CPU-exact execution or treating CUDA as canonical without its own promotion evidence;
- accepting external plugins, remote catalogs, or live reload without authenticity, compatibility, state-transfer, and failure-containment rules;
- deleting behavior, packaging, or native admission evidence merely to improve repository ratios;
- claiming that a documentation, inventory, or source-scan pass implements the target architecture;
- replacing the long-horizon target with a cleanup-only or short-term delivery plan because the core migration is difficult.

## Architecture Decision

The target direction is:

1. `SimulationKernel` is constructed from an immutable `ResolvedCompositionPlan` and does not change truth-affecting composition in place during its lifetime.
2. A host-level composition owner has an explicit lifecycle state machine,
   one-CAS initial/replacement/checkpoint-recovery publication, terminal
   shutdown, pre-publication quiescence and final-state transfer fence,
   monotonic generations, fenced world/entity/request/result references,
   jointly linearized instance leases, drain/quarantine budgets and
   deterministic reclamation. Native simulation owns the authoritative episode
   barrier; Python mirrors participate through a versioned handshake.
3. The versioned resolved-plan shell and engine-independent public-contracts target exist before truth-changing host cutover; dark/shadow work cannot publish a seam based on transitional JSON or engine-owned DTOs.
4. Durable execution artifacts converge on an experiment request, one closed
   resolved executable plan, and native per-run receipt. Orthogonal
   ReleaseManifest, RolloutDecision and StateCheckpoint authorities have one
   writer/validator each. Catalog, projection, generated diagnostics/metadata
   and migration artifacts have explicit derived/transitional/history routes.
5. A canonical JSON/detached-digest contract and versioned rollout authority
   govern N/N-1 producer/native/stored-plan/wheel combinations through one
   writer, bounded readers, non-authoritative shadow, one production-canary
   cutover decision, rollback checkpoints, kill switches, and backout triggers.
6. Per-run `RunReceipt` binds exact plan bytes/hash, executable/module/wheel
   digests, build/toolchain/ABI/platform, scenario/content/config/seed,
   world/episode/run identity, lifecycle receipts, determinism profile,
   result hashes, and completion state. Durable journal admission precedes truth
   mutation; recovery/finalization is fenced and rollback artifacts are
   restorable before production cutover.
7. Maintained Python, RL, visualization, and host paths link only through
   runtime contracts and facade targets. Raw engine access is isolated in a
   diagnostics-only build and package surface.
8. Stable invariants prefer compiler, target, type, runtime-contract, and
   behavior enforcement. Source scans are temporary migration instruments with
   metadata attached to their existing gate declarations. An expired migration
   control cannot silently renew: one bounded renewal is allowed with an
   independent sponsor and forced removal date; otherwise it retires or is
   re-admitted as a permanent semantic control.
9. The accepted topology/platform matrix is explicit. Unsupported multi-process execution fails closed; activation requires leader fencing, persistent epochs, crash recovery, authentication/authorization, authenticity, quotas, and the same native owner.
10. Normative standards and current operator/developer entries remain maintained;
   closed review packets, dispatch records, and acceptance evidence move to an
   admitted review, git-ledger, release, or CI artifact retention surface.

Phasing may change implementation order, but it must preserve these outcomes.
An independent review may replace a mechanism only when the replacement reaches
the same long-term authority, compatibility, and lifecycle result.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Authority And Baseline` | Establish verified source, control, CI, evidence, and ownership baselines plus independent review. | user authorization and latest `origin/main` | project packet, measurements, review findings, and owner index are current | accepted |
| `P1 Target Architecture` | Freeze lifecycle, episode authority, versioning/rollout, platform/process topology, contract-chain, boundary, and control-lifecycle decisions. | P0 evidence accepted | decisions include compatibility, rollback, operations, storage and security activation paths and pass independent architecture review | accepted |
| `P2 Control Lifecycle` | Make every architecture control permanent, renewable, migratory, or evidentiary with explicit ownership and retirement. | P1 terminology frozen | existing controls are classified and migration controls have enforced exit criteria | P2-A/P2-B ready |
| `P3 Contract And Public Boundary Foundation` | Land canonical authority envelopes, resolved-plan/release/rollout/checkpoint shells, engine-independent public DTO target, ledger foundation and target visibility before host cutover. | P1 accepted | transitional adapters are single-owner and host work can use final public types/storage without publishing a second truth | P3-A/P3-B/P3-C accepted |
| `P4 Host Lifecycle And Immutable Kernel Candidate` | Implement fenced host replacement, unique episode authority, complete state-transfer semantics, and an immutable candidate path in dark/shadow mode. | P3 contract/boundary foundation stable | the candidate path is state-complete and fenced but cannot become production truth or retire production rebuild | P4-A accepted; P4-B implementation complete, independent review pending; P4-C planned |
| `P5 Plan, Evidence, Binding, And Production Cutover` | Close the executable plan, introduce complete RunReceipt, finish physical facade/diagnostics packaging, then execute the only production cutover/backout and retire rebuild. | P4 candidate proven in dark/shadow mode | Cordis/native/facade/wheel use one plan; supported callers cut over once with rollback evidence and rebuild loses production authority | planned |
| `P6 Test And CI Architecture` | Align fast, qualification, nightly, release, and research lanes with unique failure audiences. | P2 control classes and P5 boundaries available | permanent gates have named detection value and migration scans are absent or expiring | planned |
| `P7 Evidence And Documentation Lifecycle` | Retain reproducible proof without keeping closed work packages in permanent authority. | P2 classes and P5 evidence ownership stable | standards, current references, historical records, and generated evidence have singular owners and routes | planned |
| `P8 Long-Horizon Acceptance` | Prove migration compatibility, operational sustainability, and absence of duplicate truth. | P3-P7 complete | full acceptance contract and independent review pass; lasting rules are promoted and task history follows the admitted retirement route | planned |

## Task Clusters

- [Finite task-cluster plan](long_horizon_architecture_governance_task_clusters_20260825.md)
- [Current status and risk register](long_horizon_architecture_governance_current_status_20260825.md)
- [Dispatch queue](long_horizon_architecture_governance_dispatch_queue_20260825.md)
- [Acceptance contract](long_horizon_architecture_governance_acceptance_20260825.md)
- [P0 authority inventory](evidence/p0_authority_inventory_20260825.md)
- [P1-A lifecycle decision](decisions/p1a_host_lifecycle_and_episode_authority_decision_20260825.md)
- [P1-B authority decision](decisions/p1b_plan_and_run_receipt_authority_decision_20260825.md)
- [P1-C rollout decision](decisions/p1c_rollout_operations_and_security_decision_20260825.md)
- [P1 independent review](../../../reviews/long_horizon_architecture_governance_p1_review_20260825.md)
- [P3-A independent review](../../../reviews/long_horizon_architecture_governance_p3a_review_20260825.md)
- [P3-B independent review](../../../reviews/long_horizon_architecture_governance_p3b_review_20260825.md)
- [P3-C independent review](../../../reviews/long_horizon_architecture_governance_p3c_review_20260827.md)
- [P4-A independent review](../../../reviews/long_horizon_architecture_governance_p4a_review_20260827.md)
- [P4-B state-transfer candidate snapshot](p4b_state_transfer_candidate_20260830.md)
- [P4-B remediation route](p4b_remediation_route_20260830.md)

## Outputs And Evidence

Expected outputs include:

- reviewed architecture decisions and compatibility maps;
- a host-owned construction/replacement seam and immutable kernel contract;
- a consolidated composition-plan and run-evidence contract;
- epoch-bearing references, episode authority, lifecycle SLOs, runbooks, and adoption/rollback telemetry;
- CMake/package boundaries for facade-only production bindings and isolated raw
  diagnostics;
- a classified control inventory with renewal and retirement evidence;
- purpose-specific CI lanes and behavior-preserving test migration;
- owner-local standards, references, reviews, admitted history-retention routes, and externalized evidence with working retrieval paths;
- replay, parity, failure-injection, packaging, resource, and migration evidence
  sufficient to reject a second truth path.

## Acceptance Gate

This program can be accepted only when:

- maintained runtime composition is immutable within a kernel, or any approved exception proves unavoidable identity and complete state transfer;
- host replacement, facade ownership, raw diagnostics isolation, and compatibility migration are implemented and tested;
- request, resolved plan, and run evidence form the durable authority chain
  without a second Cordis, Python, native, or fixture-owned resolver;
- replacement publication, leases, fencing, state transfer, mixed-version
  rollout, canary/backout, complete RunReceipt, and supported topology/platform
  rules are implemented and tested;
- every permanent control names its invariant and unique detection path; every migration control retires or has one bounded independently reviewed renewal;
- CI and documentation evidence demonstrate sustainability across ordinary
  development, qualification, release, and long-running evolution;
- an independent architecture review reports no unresolved critical or
  high-severity finding against the long-horizon outcome.

Partial cleanup, a green documentation suite, or a narrower short-term program
cannot satisfy this gate.

## Residuals And Next Steps

- P1-A/P1-B/P1-C are accepted at decision level after independent initial and
  repair reviews. P3-A/P3-B/P3-C are separately accepted after independent
  repair reviews; this unlocks P2-A/P2-B and P4 dark/shadow candidate work, not
  runtime truth publication or production migration.
- Dynamic in-place replacement remains a candidate exception, not an assumed
  requirement; its admission requires a real consumer and state-transfer proof.
- The initial accepted topology is in-process unless P1 and P8 explicitly
  admit a fenced multi-process topology; unsupported topologies fail closed.
- External plugin distribution and CUDA promotion retain their existing owners
  and must integrate with, not bypass, this program.

## Archive

The active README and current-status file remain the entry points while the
program is open. Accepted decisions move to architecture standards or reviews.
P7 must reconcile the current owner-archive policy with the gate that prohibits
all `docs/**/archive/**` paths before selecting a retirement route. Until then,
no new archive tree is an accepted closure mechanism, and the active directory
must not become an append-only evidence store.
