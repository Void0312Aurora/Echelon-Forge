# Repository Consolidation Plan

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `plan`
Lifecycle: `maintained`
Canonical: `docs/plan/repository_consolidation/README.md`
Owner: `repository consolidation workline`
Last verified: `2026-07-18`

Status: active consolidation plan on branch `codex/redundancy-consolidation`.

## Objective

Reduce redundant code, duplicated authority, compatibility residue, oversized
navigation surfaces, and documentation drift across the repository. The work
may adjust architecture when the evidence supports it, but it must preserve
maintained behavior, explicit compatibility commitments, tests, provenance,
and bounded capability claims.

All consolidation iterations remain on the same branch. Each iteration produces
one independently reviewable commit and must be accepted before the next
iteration changes the same surface.

## Iteration Protocol

Every iteration follows this sequence:

1. **Analyze**
   - inspect the current worktree and callers;
   - identify the duplicated owner or obsolete path;
   - define the behavior and evidence that must survive;
   - freeze the write set and non-goals.
2. **Implement**
   - make the smallest coherent architectural change that moves toward one
     maintained owner;
   - migrate callers before removing compatibility or history;
   - do not mix unrelated cleanup into the iteration.
3. **Validate**
   - run focused tests for every touched behavior;
   - run structural, link, lint, build, or smoke gates appropriate to the risk;
   - record commands and outcomes before review.
4. **Independent review**
   - dispatch a separate subagent that did not author the change;
   - review the frozen diff for behavior loss, removed functionality, caller
     survival, compatibility, documentation authority, and test adequacy;
   - the reviewer is read-only and returns blocking findings, non-blocking
     findings, and a verdict.
5. **Repair and re-review**
   - fix blocking findings and rerun affected validation;
   - material fixes require a final independent re-check.
6. **Commit**
   - commit only after the final diff has no unresolved blocking review finding;
   - use one commit for the iteration and record its evidence in the iteration
     register below;
   - do not amend an earlier accepted iteration to hide later repairs.

No implementation change made after the final review may be included in the
commit without another review pass.

## Required Acceptance Evidence

An iteration is accepted only when its handoff identifies:

- exact write set and non-goals;
- caller or consumer inventory for removed/moved surfaces;
- focused validation commands and results;
- broader maintained smoke/build result when production behavior changed;
- line/file delta and remaining duplicate owner, if any;
- independent reviewer identity, reviewed revision/diff, findings, and verdict;
- explicit statement of preserved behavior and retained residuals;
- commit hash after commit creation.

Documentation-only iterations must additionally prove local links for the
touched entry surface, bilingual companion consistency where required, and
`git diff --check`.

## Candidate Priority

The list is a routing order, not pre-authorization. Every candidate requires a
fresh source and caller audit when its iteration begins.

| Priority | Candidate | Intended result | Main risk |
| --- | --- | --- | --- |
| P0 | Correctness defects exposed by duplicate representations | Fix incorrect behavior before mechanical deletion. | A compatibility-preserving patch can still change default semantics. |
| P1 | Unreachable implementations and exact helper duplication | Remove dead bodies and establish one runtime/test helper owner. | Hidden construction or import patterns may bypass normal callers. |
| P2 | Documentation lifecycle and consolidation governance | Establish executable classification, review, archive, and evidence rules. | A policy-only change can add another unused authority unless indexed and enforced. |
| P3 | Maintained navigation and compatibility shims | Repair entry links, migrate internal callers from shims, and leave bounded external compatibility facades. | Moving or deleting a shim before caller migration breaks users not visible in tests. |
| P4 | Repeated Python taxonomy, geometry, objective, C2/ROE, and bootstrap helpers | Create one semantic owner with scalar/tensor or runtime/compiler parity tests. | Similar-looking helpers may contain intentional semantic differences. |
| P5 | World-batch, step-evaluation, effects-event, and configuration schema duplication | Replace field-by-field synchronization with shared payloads or explicit adapters. | Public bindings, ABI shape, serialization, and report schemas may change. |
| P6 | Python package cycles and C++ target/layer boundaries | Enforce dependency direction and smaller build/runtime ownership units. | Broad import, linker, initialization-order, and performance regressions. |
| P7 | Documentation compaction, archive normalization, and evidence manifests | Make maintained navigation small; collapse duplicate archive layers only after provenance mapping. | Path moves can break tools, tests, historical references, and rights evidence. |
| P8 | Final repository-wide residual audit | Classify every surviving duplicate as intentional, held, or not cost-effective. | A scan can miss behavioral duplication or overstate textual similarity. |

## Iteration Register

| Iteration | Status | Commit / branch evidence | Scope and result | Validation / review evidence |
| --- | --- | --- | --- | --- |
| I1 Runtime and test infrastructure consolidation | `accepted` | `aaec45882173d57c679e3e7233a81980ee9d8fdc` on `codex/redundancy-consolidation` | Fixed sparse missile-tuning override semantics, removed the unreachable `UniversalEnv` body, centralized `ef_py` runtime bootstrap and suite-manifest parsing, and consolidated repeated test helpers. Net change: 1,413 insertions and 2,390 deletions. | Focused regressions and the maintained smoke suite passed (`361 passed`, `41 subtests passed` in the final iteration closeout). An independent review reported no unresolved blocking finding before commit. |
| I2 Documentation lifecycle and consolidation governance | `accepted` | iteration commit on `codex/redundancy-consolidation`; exact hash is reported in the commit handoff and next register update | Added lifecycle and consolidation authority, one shared maintained-document scope, a strict link audit, selective bilingual-registry refresh, and link-safe repairs without a baseline allowlist. The strict registry now covers 76 pairs. Final diff: 57 files, 1,960 insertions, 427 deletions. | Default audit: 155 documents, 2,592 internal links, zero issues. Focused governance tests: `15 passed`; maintained smoke: `371 passed`, `41 subtests passed`; Ruff and `git diff --check` passed. Registry: 70 synced, 6 preserved legacy divergences, 1 legacy missing English companion. `iteration2_independent_review` found two archive-authority blockers; both were repaired. Final `bilingual_registry_audit` re-review left no unresolved blocker. |

### I2 Retained Documentation Residuals

- The repository-root `README.md` / `README.zh.md` pair is reviewed directly
  but is not hash-tracked because the current registry is rooted at `docs/`.
- `docs/standards/foundation/realism_authority_boundary.zh.md` still lacks its
  English canonical peer.
- Six pre-existing pair divergences remain deliberately unrefreshed:
  `plan/cooperative/multi_agent_cooperative_training_foundation_and_performance_plan`,
  `standards/model/policy_execution_architecture`, `standards/naval/obs`,
  `task/air_combat/README`, `task/issues/README`, and `task/review/README`.
- Legacy archive normalization and evidence compaction remain P7 work and were
  not folded into this governance iteration.

## Surfaces That Must Not Be Deleted Without Additional Gates

The following are not deletion candidates merely because they are large, old,
or duplicated:

- public or compatibility APIs before internal and plausible external callers
  have a migration path and deprecation boundary;
- tests before their behavioral assertions are replaced by equal or stronger
  coverage and the relevant bug history is preserved;
- frozen configs, canonical scenarios, accepted evidence, source-rights
  records, third-party inputs, and provenance manifests;
- generated artifacts consumed by a maintained release or validation path until
  clean regeneration is proven;
- archive records solely because they are stale or verbose;
- ignored/private/local workspaces not admitted into the tracked scope;
- user-owned unrelated worktree changes;
- behavior that has no characterization test until that behavior is first
  measured and its intended boundary is decided.

Deletion of any evidence or archive package requires a consumer/reference scan,
rights and provenance review, and proof that a smaller retained set preserves
the same bounded claim.

## Commit And Review Discipline

- Keep every iteration on `codex/redundancy-consolidation` unless the user
  explicitly changes the branch strategy.
- One iteration equals one coherent commit.
- The independent reviewer must not edit the implementation under review.
- Review must ask whether functionality was removed, not only whether tests
  pass or code became shorter.
- Passing narrow tests does not prove repository-wide compatibility.
- If an iteration discovers a materially different problem, record it as a
  later candidate instead of expanding the current write set.
- Do not commit with unresolved blocking findings, failing required validation,
  or unexplained deletions.

## Stop Conditions

The consolidation program may be declared complete only after a final audit
proves all of the following:

1. maintained entry surfaces have one named owner and no known broken internal
   navigation;
2. no confirmed unreachable production body or unowned compatibility path
   remains in the active tree;
3. remaining duplicate schemas/helpers have either one shared owner or an
   explicit documented reason for separate representations;
4. remaining archive/evidence duplication is required for provenance, rights,
   reproducibility, or bounded acceptance;
5. remaining candidates are classified as intentional, held behind a named
   compatibility decision, or demonstrably higher-risk/cost than their benefit;
6. focused tests, maintained smoke/build gates, document gates, and final
   independent review pass;
7. the final residual report identifies what was deliberately retained and why.

Operationally, run at least two consecutive residual-audit passes after the
last material consolidation. The second pass must find no new high-confidence,
safe consolidation candidate. Absence of a textual duplicate alone is not
proof of completion; caller, behavior, documentation, and evidence ownership
must also be audited.

If progress requires an external compatibility decision, unavailable source
rights, or behavior that cannot be characterized from the repository, mark the
candidate `held` with the exact missing authority. Do not delete it to satisfy a
line-count target.

## Related Authority

- [Document Lifecycle Policy](../../standards/governance/document_lifecycle_policy.md)
- [Agent Document Authority Map](../../agent/rules/document_authority_map.md)
- [Standards Maintenance Policy](../../standards/governance/standards_maintenance_policy.md)
- [Subagent Usage Policy](../../standards/governance/subagent_usage_policy.md)
