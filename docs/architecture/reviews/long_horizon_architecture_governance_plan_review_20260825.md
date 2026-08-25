# Long-Horizon Architecture Governance Plan Review — 2026-08-25

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/architecture/reviews/long_horizon_architecture_governance_plan_review_20260825.md`
Owner: `cross-domain architecture/reviews`
Last verified: `2026-08-25`
Review basis: `82d5b6e893c442950e334eb3e9ec92f8174eeb35` plus the
P0-A project draft on branch `codex/long-horizon-governance-architecture`.

## Scope And Independence

An independent read-only `gpt-5.6-sol` reviewer inspected the full
[long-horizon project packet](../work/active/long_horizon_architecture_governance/README.md)
and its cited runtime, composition, facade, binding, test/CI, and
documentation/evidence sources. The reviewer did not author or edit the plan.

The review was explicitly required to preserve the long-horizon outcome. It
could reject mechanisms or sequencing, but could not close a finding by
substituting repository cleanup, a narrower program, or short-term delivery.

## Initial Verdict

Verdict: `repair-required`.

- P0 findings: none.
- P1 findings: six.
- P2 findings: four.
- Short-term substitution detected: no.

The reviewer found the strategic target coherent, but concluded that lifecycle
publication, phase order, rollout, run evidence, control renewal, and
operational/security gates were incomplete.

## P1 Findings And Disposition

| Finding | Evidence-backed defect | Required repair | Plan disposition |
| --- | --- | --- | --- |
| `P1-01 Host fencing and episode authority` | current facade/backend ownership has no host slot, incarnation-bearing public references, lease/fencing protocol, or singular Python/native episode handshake | freeze lifecycle state machine, linearization, epochs, leases, drain/reclamation, complete state census, and native episode authority; make transfer semantics precede cutover | accepted into `P1-A` and `P4-A/P4-B/P4-C`; P4-A is dark/shadow, P4-B precedes the P4-C candidate, and both precede P5-D production cutover |
| `P1-02 Phase order stabilizes a transitional seam` | host implementation was scheduled before the final resolved-plan shell and engine-independent public-contract target | land final contract shell and initial physical boundary before truth-changing host publication | phases reordered: `P3-A/P3-B/P3-C` establish public DTO, plan, and rollout foundation before `P4` host publication |
| `P1-03 No mixed-version rollout/backout` | strict version pins can fail closed when producer, native binary, stored artifacts, and wheel upgrade out of order | add N/N-1 matrix, one writer, bounded readers, canary/shadow, cutover receipt, rollback checkpoint/window, kill switch, and backout trigger | accepted into `P1-C`, `P3-C`, `P5-D`, and P1/P3/P5/P8 acceptance gates |
| `P1-04 Existing evidence is not a complete run receipt` | composition evidence omits exact executable/package/platform, scenario/content/config/seed, lifecycle transition, result, and completion identity | define versioned `RunReceipt` covering actual inputs, binary/package, platform, lifecycle, outputs, and completion | accepted into `P1-B`, `P5-B`, strategic outcome, and P5/P8 acceptance gates |
| `P1-05 Renewal can preserve migration controls forever` | expiration had no renewal cap, forced successor, or default failure/retirement policy | attach lifecycle metadata to existing gate declarations; permit at most one sponsored bounded renewal before retirement or permanent re-admission | accepted into `P2-A` and P2/P6/failure gates; no new registry-generator-fixture chain is authorized |
| `P1-06 Missing operations, adoption, topology, and security gates` | plan lacked host owner/runbook/SLO/adoption telemetry and multi-process fencing/security activation | define supported topology/platform, fail closed elsewhere, add operational owner/SLO/telemetry and multi-process leader/fencing/recovery/authenticity/quota gate | accepted into `P1-C`, `P2-B`, `P5-D`, and P8 acceptance |

## P2 Findings And Disposition

| Finding | Disposition |
| --- | --- |
| P0 inventories are still partial | P0 remains `partial/repair-required`; P1 implementation stays blocked until caller/control/target/artifact/document inventories and repair review pass |
| Supported platform matrix was undefined | P1-C now owns explicit platform/process support; final acceptance requires supported-platform build/wheel/runtime evidence and fails closed for unsupported topology |
| Manifest simplification could orphan maintained tests | P6-A now preserves the invariant that every maintained test has one owner and execution strategy through runner-native metadata or a derived non-authoritative orphan report |
| External evidence durability lacked SLOs | P7-A/P7 acceptance now require minimum retention, availability, backup/restore, access control, provider migration, retrieval, and periodic restore drills |

## Repair Verification

Main-thread repair must:

- update every affected README, phase, cluster, queue, status, and acceptance
  surface;
- keep P0 `not accepted` until inventories and independent repair review pass;
- rerun diff, link, bilingual, and documentation governance checks;
- return the revised packet to the same independent reviewer for
  finding-by-finding confirmation.

## First Repair Review

Verdict: `repair-required`.

The same independent reviewer confirmed all six original P1 findings and four
original P2 dispositions closed at plan level, with P0 inventories still open
as intended. It found no P0 overclaim and no short-term substitution, but found
one new P1 and four new P2 defects:

| Finding | Defect | Required disposition |
| --- | --- | --- |
| `N-P1-01 Production cutover ordering` | P4 both migrated maintained callers/retired rebuild while P5 later closed the plan, RunReceipt, facade-only package, and performed another rollout | make P4 candidate-only and P5-D the unique production cutover, or move every P5 hard prerequisite before a single P4 cutover |
| `N-P2-01 P6/P7 ownership` | archive-retirement gate/suite write sets overlapped and P7 entry conditions disagreed | give P7-A sole archive-retention authority and synchronize its P2/P5 dependency |
| `N-P2-02 P0 pytest bootstrap` | the documented command loaded repository `tests/conftest.py` and exited when a clean source worktree lacked `ef_py` | use a docs-only `--confcutdir tests/architecture` command or declare a native prerequisite |
| `N-P2-03 Audit selection` | the recorded 41-pass subset was not reproducible from the packet | record the exact governance-manifest expansion and its 53-pass/1-fail result |
| `N-P2-04 Chinese renewal summary` | the Chinese acceptance summary omitted the one-renewal bound and forced removal date | synchronize the canonical bounded-renewal rule |

## Second Repair Disposition

- P4 now publishes only an internal dark/shadow candidate; it cannot change
  production truth, migrate maintained production callers, or retire rebuild.
- P5-A/B/C close the executable plan, complete RunReceipt, and facade-only
  package before P5-D performs the single production cutover, caller migration,
  rollback window, and rebuild retirement.
- P7-A exclusively owns archive-retention policy, gate, suite node, paths, and
  retrieval route; P6 excludes those surfaces and P7 consistently depends on
  P2 classifications plus P5 evidence ownership.
- P0 uses docs-only pytest isolation. The exact governance-manifest command and
  its `53 passed, 1 failed` remote-baseline result are recorded.
- The Chinese acceptance summary now requires at most one bounded independently
  reviewed renewal with a forced removal date.

## Final Follow-Up Verdict

Verdict: `pass`.

The same independent reviewer re-read the frozen packet and confirmed:

- `N-P1-01` and `N-P2-01` through `N-P2-04` are closed;
- all original P1 and P2 dispositions remain closed at plan level;
- clean-source P0 docs pytest passes 25 tests, while the reproducible governance
  manifest remains 53 passed/1 known archive-baseline failure;
- no new P0, P1, or P2 finding and no short-term substitution was detected.

This closes P0-B plan review only. P0 overall remains partial until its live
caller, control, target, artifact, and document inventories are complete. P1-P8
remain unimplemented and unaccepted.

## Authority Boundary

This review validates plan completeness only. It does not implement or accept
the runtime, contract, build, binding, test/CI, evidence, or operations phases.
