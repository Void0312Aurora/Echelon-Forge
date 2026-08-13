# Standards Maintenance Policy

Language:
- English canonical: `standards_maintenance_policy.md`
- Chinese companion: [standards_maintenance_policy.zh.md](standards_maintenance_policy.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/engineering/documentation/standards/standards_maintenance_policy.md`
Owner: `engineering/documentation-governance`
Last verified: `2026-08-08`

Status: `2026-08-08` authoritative policy for keeping maintained standards aligned with implementation evidence.

This policy defines how maintained owner-local standards change after
implementation, active work, tests, scenarios, or governance move. It
complements the [Documentation Engineering Overview](../README.md), the
[Document Alignment Map](../reference/document_alignment_map.md),
and the [Bilingual Documentation Policy](bilingual_documentation_policy.md).

## Purpose

The standards subtrees owned by project, architecture, domain, system,
learning, operations, engineering, and research owners collectively define
naming, layering, service/domain semantics, public-source admission, and
governance rules. A standards subtree is not a task board, but it must stay
close enough to implementation that contributors can trust it when making
code, test, scenario, or planning changes.

Maintained standards now use owner-local routes. The retired
`docs/standards/` root must not be recreated as a shared ownership surface.

The maintenance policy prevents two failure modes:

- stale standards that lag behind accepted runtime/test contracts
- standards prose that overclaims implementation maturity or promotes a task
  experiment into project-wide authority

## Authority Rule

Use this order when standards and implementation appear to disagree:

1. Current code, tests, scenarios, configs, and contract runners decide factual
   implementation state.
2. The applicable content owner's maintained `standards/` entries decide
   naming, layering, ownership, public-source admission, and governance rules.
3. The applicable owner's `work/active/` entries decide scoped work status,
   residuals, and acceptance evidence.

The retired `docs/plan/` and `docs/task/` roots no longer exist; they are
recorded in the [Retired Documentation Ledger](../../../archive_ledger.md).
Current scoped work and residuals must be routed through the applicable owner's
`work/active/` or `work/issues/` surface.

If executable evidence and a standards page disagree, do not silently pick one.
Open or use a review/task governance lane, classify the drift, and close it
with an explicit standards update, implementation update, or held decision.

## Drift Classes

| Drift class | Meaning | Required handling |
| --- | --- | --- |
| Semantic mismatch | The standard and implementation encode contradictory meaning. | Pick the owner of truth, then update code or standard in the same remediation slice. |
| Implementation ahead of standard | Code, test, scenario, or accepted task evidence added a stable contract not yet registered in standards. | Add or update the standards owner before claiming the contract as maintained. |
| Standard ahead of implementation | A standards page describes target behavior that is not implemented. | Mark it as planning, held, or non-runtime until evidence exists. |
| Status/date stale | The page is still mostly right, but headers or status lines no longer tell readers what evidence it reflects. | Refresh the status line and authority note. |
| Bilingual/index drift | A maintained canonical page changed without its companion, registry, or nearest README index. | Update the peer, registry, and index before closing the slice. |

## Admission Gates

A new or expanded standards contract must name:

- the content owner and, where relevant, the owning layer such as `foundation`,
  `bridge`, `joint`, `services`, a domain specialization, `model`, or
  `governance`
- the implementation evidence, if the page describes current behavior
- the task or review evidence, if the contract was stabilized by a workstream
- the public-source basis, when realism or doctrine claims are involved
- the status category: authoritative, specialization, planning supplement,
  held, or archived
- the bilingual companion expectation for the touched surface

No empty owner rule:

- Do not create an owner-local `standards/` directory or
  `src/*/domains/<domain>` owner shell just to illustrate future structure.
- If a layer is not accepted yet, say it is held or planning instead of adding
  a production-looking placeholder.
- A domain may own components, systems, and models at different maturity
  levels. Absence of a layer must remain visible rather than being hidden by an
  empty directory or dummy interface.

## Required Update Triggers

Update a standards page, or create a review gap that names why the update is
held, whenever one of these changes lands:

- a new DTO field, enum value, mode, scenario contract, model contract, or
  runtime workflow stage becomes maintained
- an accepted task changes service/domain ownership or capability claims
- a runtime/test contract retires a compatibility path or replaces an older
  owner
- a planning supplement is no longer aligned with current source layout
- a maintained governance rule changes how contributors should dispatch,
  translate, accept, archive, or validate work

Do not rely on dated review files alone as current authority. The nearest
maintained owner README or standards entry must point to the current
interpretation.

## Status And Header Rules

Maintained standards pages should include a status line near the top:

```md
Status: `<YYYY-MM-DD>` <authority state> <short scope>.
```

Use precise authority states:

- `authoritative`
- `authoritative foundation`
- `authoritative bridge`
- `authoritative model architecture`
- `specialization`
- `active planning supplement, not a current runtime contract`
- `held pending <evidence>`
- `archived`

Do not use a fresh date to imply the page is accepted if the body still
contains unresolved or planning-only contracts. The date means the page was
reviewed or updated; the authority state names what the page can be used for.

## Review And Closure Lane

Standards drift found by audit or implementation work should be tracked under
the content owner's bounded `reviews/`, `work/issues/`, or `work/active/`
surface until it is closed, held, or archived. Legacy review/task routes remain
valid until migrated. The 2026-06-10 precedent is the archived accepted
Standards Documentation Governance (`git show 691f098b:docs/task/review/archive/standards_documentation_governance/README.md`)
subproject.

Retrieval address:
`git show 691f098b:docs/task/review/archive/standards_documentation_governance/README.md`.

A gap can close only when:

- the owner layer is named
- code/test/scenario evidence is cited when current implementation is claimed
- planning-only or held behavior is labeled honestly
- bilingual companions and nearest indexes are synchronized
- focused validation has pass/fail evidence

## Validation

Use these checks for standards governance slices:

```bash
python3 tools/maintenance/translate_docs_batch.py audit --root docs \
  --registry docs/engineering/documentation/reference/bilingual_document_clusters.json
python -m pytest -q tests/architecture/governance
git diff --check -- docs tools/maintenance tests/architecture/governance
```

Remediation slices that touch code or runtime contracts must add their affected
runtime, architecture, build, or contract tests.

## Related Documents

- [Documentation Engineering Overview](../README.md)
- [Document Alignment Map](../reference/document_alignment_map.md)
- [Bilingual Documentation Policy](bilingual_documentation_policy.md)
- [Bilingual Document Clusters](../reference/bilingual_document_clusters.md)
- [Subagent Usage Policy](../../automation/standards/subagent_usage_policy.md)
- Standards Documentation Governance (`git show 691f098b:docs/task/review/archive/standards_documentation_governance/README.md`)
