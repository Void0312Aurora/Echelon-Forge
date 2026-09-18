# Long-Horizon Architecture Governance Dispatch Queue

Status: `2026-09-19` P0 and P1 architecture decisions plus the complete
P3-A/P3-B/P3-C contract, authority-envelope, ledger and compatibility
foundations and P4-A dark/shadow host lifecycle are accepted. Independent P3
and P4-A reviews closed every Critical/High/Medium finding without short-term
substitution. P4-B dark/shadow candidate review has now passed; the first P4-C
build-tree/internal seam has passed candidate-scope independent review.
P2-A/P2-B, maintained parity/stress, rollback, and P5-P8 remain dependency-gated.
The active P4-B implementation route is the subordinate [remediation route](p4b_remediation_route_20260830.md);
this dispatch queue remains authoritative for ordering and review cadence.

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
| 1 | `P0-A` | accepted | main thread | latest remote worktree | project packet plus reproducible caller/control/target/artifact/CI/document inventory accepted |
| 2 | `P0-B initial review` | repair-required | independent diagnostics reviewer | complete P0 draft | six P1 and four P2 findings; no P0 finding; no short-term substitution detected |
| 3 | `P0-C initial repair` | completed | main thread | initial P0-B findings | persisted review, finding disposition, revised synchronized packet, validation |
| 4 | `P0-B first repair review` | repair-required | same independent reviewer | initial P0-C repair | original findings closed; one new P1 and four P2 findings returned |
| 5 | `P0-C second repair` | completed | main thread | first repair-review findings | unique production cutover, P6/P7 ownership, executable validation, reproducible audit count, bilingual renewal bound |
| 6 | `P0-B final repair review` | pass | same independent reviewer | frozen second repair | all original and new findings closed at plan level; no new finding or short-term substitution |
| 7 | `P1 integrated initial review` | repair-required | independent `gpt-5.6-sol` max reviewer | frozen P1 decisions | zero critical, eight high, four medium and two low findings; no short-term substitution |
| 8 | `P1-A/B/C repair` | completed candidate | main thread | initial findings | quiescence/fault lifecycle, release/state authority, canonical wire/journal/storage, single canary cutover, rollback split and exact crosswalk repairs |
| 9 | `P1 integrated first repair review` | repair-required | same independent reviewer | frozen first repair | original high findings closed; two new high lifecycle gaps found for bootstrap/recovery and normal shutdown |
| 10 | `P1 second repair` | completed candidate | main thread | first repair-review findings | one-CAS initial/replacement/recovery transactions, terminal shutdown, exact per-path caller classes and singular checkpoint aggregation |
| 11 | `P1 integrated second repair review` | pass | same independent reviewer | frozen second repair | no unresolved critical/high; P1-A/B/C pass; one medium clarification requested |
| 12 | `P1 final medium confirmation` | pass | same independent reviewer | checkpoint-source clarification | healthy source may create checkpoint; faulted/quarantined source cannot; integrated verdict remains pass |
| 13 | `P2-A` | ready | future governance worker | P1 accepted | classified live controls with attached lifecycle/expiry/renewal/removal metadata |
| 14 | `P2-B` | ready | future diagnostics/operations worker | P1 accepted | repeatable sustainability, lifecycle, skew, retrieval and resource baselines |
| 15 | `P3-A` | accepted | main thread + independent `gpt-5.6-sol` max reviewer | P1 accepted | `ef_runtime_contracts`, v1 identity/schema ownership, actual target/install graph gates, and final review pass |
| 16 | `P3-B` | accepted | main thread + independent `gpt-5.6-sol` max reviewer | P3-A accepted | canonical JSON authority envelopes, versioned plan/release/rollout/checkpoint shells, provenance binding, exact vectors and native/Cordis conformance |
| 17 | `P3-C` | accepted | main thread + independent `gpt-5.6-sol` max reviewer | P3-B accepted | non-production ArtifactLedger, exact N/N-1 readers, fenced journals/checkpoints, durable kill/backout recovery and final review pass |
| 18 | `P4-A` | accepted | main thread + independent `gpt-5.6-sol` max reviewer | P3 foundation accepted | dark/shadow one-CAS host lifecycle with quiescence, leases, fences, termination, quarantine, timeout retry and no production publication |
| 19 | `P4-B` | dark/shadow candidate independently passed; no production publication | main thread + independent `gpt-5.6-sol` max reviewer | P4-A accepted | twelve-row versioned native episode/state-transfer candidate, strict decoding, N/N-1 WAL evidence and host replacement; no production publication |
| 20 | `P4-C` | candidate-scope review passed; no production publication | main thread + independent `gpt-5.6-sol` max reviewer | P4-B handoff ready | build-tree-only kernel/world-batch seam, epoch-bearing native/Python shadow adapters, focused teardown/stale-reference gates, and explicit residuals; no maintained caller cutover |

## Later Dependency Queue

| Wave | Clusters | Entry gate | Parallel rule | Exit product |
| --- | --- | --- | --- | --- |
| Architecture foundation | `P1-A`, `P1-B`, `P1-C` | P0 accepted | research may overlap; normative integration serial | reviewed lifecycle/episode, artifact authority, rollout, platform/topology, operations, and security decisions |
| Governance foundation | `P2-A`, `P2-B` | P1 terminology stable | parallel-safe with disjoint inventory/measurement files | classified controls and repeatable sustainability baseline |
| Contract/public foundation | `P3-A`, `P3-B`, `P3-C` | accepted | public DTO, canonical plan/release/state envelopes and rollout/ledger writers serial | final public types, authority shells and non-production conditional storage before host publication |
| Runtime candidate lifecycle | `P4-A`, `P4-B`, `P4-C` | P3 foundation accepted | dark/shadow host before transfer authority; transfer before internal candidate seam | fenced candidate host, unique episode authority, immutable candidate kernel, no production cutover |
| Consolidation and production rollout | `P5-A`, `P5-B`, `P5-C`, `P5-D` | P4 dark/shadow candidate gates | plan, qualified ledger/journal/checkpoint/receipt and package gates precede the unique P5-D production-canary decision | one plan, durable complete RunReceipt, facade-only package, caller migration, process-aware rollback and rebuild retirement |
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
