# Long-Horizon Architecture Governance Dispatch Queue

Status: `2026-08-25` P0 queue. Final independent plan review passed after two
repair rounds. P0-A inventories remain partial, so no P1 implementation cluster
is dispatchable yet.

Parent subproject: [Long-Horizon Architecture Governance](README.md)

Authoritative cluster definitions:
[task clusters](long_horizon_architecture_governance_task_clusters_20260825.md).

## Queue Policy

- This queue orders work; it does not redefine cluster scope or acceptance.
- Only clusters marked `ready` may be dispatched.
- A shorter cleanup or near-term delivery plan is not an alternate completion
  route. It may be an intermediate cluster result only when it advances the
  accepted long-horizon dependency chain.
- Reviewers may replace mechanisms with evidence-backed alternatives that
  preserve immutable composition, one executable authority, physical facade
  containment, control retirement, and sustainable evidence.
- Architecture decisions, shared-contract edits, integration, and acceptance
  remain serial.

## Current Queue

| Order | Cluster | State | Dispatch owner | Dependency | Required return |
| ---: | --- | --- | --- | --- | --- |
| 1 | `P0-A` | partial | main thread | latest remote worktree | project packet and dated baseline exist; complete caller/control/target/artifact/document inventories remain |
| 2 | `P0-B initial review` | repair-required | independent diagnostics reviewer | complete P0 draft | six P1 and four P2 findings; no P0 finding; no short-term substitution detected |
| 3 | `P0-C initial repair` | completed | main thread | initial P0-B findings | persisted review, finding disposition, revised synchronized packet, validation |
| 4 | `P0-B first repair review` | repair-required | same independent reviewer | initial P0-C repair | original findings closed; one new P1 and four P2 findings returned |
| 5 | `P0-C second repair` | completed | main thread | first repair-review findings | unique production cutover, P6/P7 ownership, executable validation, reproducible audit count, bilingual renewal bound |
| 6 | `P0-B final repair review` | pass | same independent reviewer | frozen second repair | all original and new findings closed at plan level; no new finding or short-term substitution |
| 7 | `P1-A` | blocked by P0 | future architecture worker | P0 accepted | immutable-kernel/host replacement decision and compatibility map |
| 8 | `P1-B` | blocked by P0 | future architecture worker | P0 accepted | contract derivation and durable-authority decision |

## Later Dependency Queue

| Wave | Clusters | Entry gate | Parallel rule | Exit product |
| --- | --- | --- | --- | --- |
| Architecture foundation | `P1-A`, `P1-B`, `P1-C` | P0 accepted | research may overlap; normative integration serial | reviewed lifecycle/episode, artifact authority, rollout, platform/topology, operations, and security decisions |
| Governance foundation | `P2-A`, `P2-B` | P1 terminology stable | parallel-safe with disjoint inventory/measurement files | classified controls and repeatable sustainability baseline |
| Contract/public foundation | `P3-A`, `P3-B`, `P3-C` | P1 accepted | public DTO target, plan shell, and rollout writers serial | final public types and mixed-version contract before host publication |
| Runtime candidate lifecycle | `P4-A`, `P4-B`, `P4-C` | P3 foundation stable | dark/shadow host before transfer authority; transfer before internal candidate seam | fenced candidate host, unique episode authority, immutable candidate kernel, no production cutover |
| Consolidation and production rollout | `P5-A`, `P5-B`, `P5-C`, `P5-D` | P4 dark/shadow candidate gates | plan/receipt/package gates precede the unique P5-D production cutover | one plan, complete RunReceipt, facade-only package, caller migration, rebuild retirement, and rollback evidence |
| Control migration | `P6-A`, `P6-B` | P2 classes and P5 boundaries available | excludes archive-retention policy/gate/suite paths owned by P7-A | purpose-specific tests and CI lanes |
| Evidence lifecycle | `P7-A`, `P7-B` | P2 classifications and P5 evidence ownership | P7-A decides retention before any archive-specific gate/suite/path change; routing precedes deletion | singular maintained authorities and retired migration residue |
| Acceptance | `P8-A`, `P8-B` | P3-P7 mergeable | strictly serial | validated long-horizon result, independent verdict, standard promotion |

## P0-B Review Packet

The independent reviewer must inspect:

- `README.md` and `README.zh.md`;
- task clusters, current status, dispatch queue, and acceptance contract;
- current `SimulationKernel` rebuild and lease/mutation barriers;
- runtime composition baseline and accepted Cordis program;
- current request/lock/projection/manifest/evidence/closure chain;
- runtime facade target, bindings, package, and escape-hatch governance;
- test suite manifests, runner meta-tests, and CI workflow;
- documentation, bilingual, evidence, and archive policies.

Required questions:

1. Does the plan reach a coherent long-term runtime architecture, or merely
   schedule cleanup?
2. Are host replacement, state transfer, identity, shutdown, failure,
   concurrency, fencing, leases, episode authority, replay, and rollback
   obligations complete?
3. Can the proposed contract consolidation preserve Cordis/native admission,
   reproducibility, compatibility, and security?
4. Can physical target/package boundaries replace source scans without
   disabling diagnostics or breaking the wheel?
5. Does the control lifecycle avoid creating another permanent
   registry-generator-fixture-meta-test chain?
6. Are CI, evidence, and documentation transitions operationally sustainable
   across years of new profiles, backends, domains, and bindings?
7. Which missing compatibility, migration, or acceptance gates could force a
   later rewrite?
8. Do phase dependencies prevent host publication before final public DTO,
   plan-version, rollout, and state-transfer contracts exist?
9. Are RunReceipt, supported platform/topology, operational SLO/owner,
   multi-process security, test ownership, and external-evidence durability
   complete?

The reviewer must not treat `reduce scope`, `do only P0-P2`, or `focus on quick
wins` as a valid resolution of a long-horizon omission. If the proposed
mechanism is flawed, the finding must supply or require an alternative that
preserves the strategic outcome.

## Dispatch Packet Template

```md
cluster:
goal:
write set:
non-goals:
long-horizon outcomes preserved:
capability tier / model ID / reasoning:
dependencies:
validation:
closure gate:
round cap:
required return packet:
```

## Queue Advancement Rules

- `pass` advances only the named cluster.
- `partial` never unlocks a dependent implementation cluster.
- `blocked` must identify the blocker, owner, replacement path, and forced
  review trigger.
- Exceeding a round cap triggers architecture re-baselining; it does not allow
  silent contraction of the final target.
- P8-B is the only queue item that may authorize program closure, and only
  after P8-A implementation evidence is complete.
