# Document Lifecycle Policy

Language:
- English canonical: `document_lifecycle_policy.md`
- Chinese companion: [document_lifecycle_policy.zh.md](document_lifecycle_policy.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/engineering/documentation/standards/document_lifecycle_policy.md`
Owner: `engineering/documentation-governance`
Last verified: `2026-08-07`

Status: `2026-08-07` authoritative policy for classifying, maintaining,
reviewing, generating, and archiving repository documentation.

## Purpose

This policy gives every maintained document one content kind and one lifecycle
state. It prevents current authority, historical records, generated output,
configuration inputs, and retained evidence from being mixed in the same
navigation surface without an explicit boundary.

`maintained` and `archived` are lifecycle states, not peer directory types.
A reference page can therefore be `kind: reference` and
`lifecycle: maintained`, then later become `lifecycle: archived` without being
misclassified as a different kind of document.

This policy governs tracked repository documentation. Ignored, private, or
local-only workspaces are outside its publication scope unless they are
deliberately admitted into the tracked tree.

## Classification Model

### Document Kinds

| Kind | Purpose | Normal location | Authority boundary |
| --- | --- | --- | --- |
| `standard` | Stable terminology, ownership, governance, and mandatory constraints | the content owner's `standards/` subtree | Normative within its declared scope; it cannot overrule current code or executable evidence about implemented behavior. |
| `plan` | Bounded architecture direction, sequencing, migration, and acceptance design | the content owner's `work/issues/` subtree, or `docs/project/` for a project-wide program | Authorizes only the frozen or explicitly active scope it names. |
| `task` | Current implementation work, status, residuals, and acceptance packages | the content owner's `work/active/` subtree | Owns scoped execution status; it does not redefine cross-project terminology owned by the applicable standards owner. |
| `reference` | Verified description of current structure, API, capability, or inventory | an owner's `reference/` subtree or component README | Descriptive authority only for the last-verified state. |
| `howto` | Reproducible operator or maintainer procedure | `docs/operations/howto/` or an owner-local how-to surface | Valid only for the named platform, prerequisites, and verified command path. |
| `review` | Independent findings, risk assessment, acceptance decision, or rejection | the content owner's `reviews/` subtree | Records a judgment. Action items must move to `work/active/` or `work/issues/`; a review does not itself implement a change. |
| `evidence` | Immutable retained inputs, measurements, manifests, figures, or acceptance proof | an `evidence/` package beside the owner-local active work or review | Supports a bounded claim only; it is not current behavior or policy authority. |
| `generated` | Reproducible output produced from named tracked inputs | an owner-local `generated/` directory | Never manually normative. The producer and inputs are authoritative. |
| `config-index` | Human-readable index of canonical scenarios or configuration inputs | the owning reference or configuration surface | Points to configuration truth; it must not duplicate the payload. |

`docs/standards/`, `docs/plan/`, `docs/task/`, and `docs/task/review/` remain
migration-era legacy surfaces while their maintained documents are assigned to
content owners. Their temporary location does not change document kind or
authority, and new work must not expand them when an owner-local route exists.

### Lifecycle States

| Lifecycle | Meaning | Allowed use |
| --- | --- | --- |
| `draft` | Scope or content is not accepted. | Discussion and review only; not implementation authority. |
| `maintained` | Current and intentionally updated with its owner. | Default current entry for the declared scope. |
| `accepted` | A bounded result or review decision has passed its gate. | Stable evidence or closure record; new scope requires a new task or plan. |
| `superseded` | Replaced by a named current document. | Transitional history until physically archived. |
| `archived` | Historical and not current authority by default. | Provenance and route history only. |

Do not use directory presence as a lifecycle claim. A local README must name
the current entry, and every superseded document must name its replacement.

## Required Metadata

New documents and substantially rewritten maintained documents must place this
block immediately after the title and language block:

```text
Document kind: `<kind>`
Lifecycle: `<lifecycle>`
Canonical: `<repo-relative path or self>`
Owner: `<component, domain, or governance surface>`
Last verified: `<YYYY-MM-DD>` or `not established`
```

Additional requirements:

- `not established` is allowed only for migrated legacy material or draft work
  whose factual baseline was not reverified. It must include a visible content
  status, and it cannot be promoted to `accepted`, `reference`, or `standard`
  until an owner supplies a dated verification boundary;

- `plan` and `task`: scope, non-goals, acceptance evidence, and residuals;
- `reference`: implementation sources and the verification boundary;
- `howto`: prerequisites, platform assumptions, commands, and expected result;
- `review`: reviewed revision, reviewer independence, findings, and verdict;
- `evidence`: claim boundary, manifest, provenance, and retention reason;
- `generated`: producer command, tracked inputs, and a do-not-edit marker;
- `config-index`: canonical config/scenario paths and lifecycle category.

Legacy documents do not need a repository-wide metadata rewrite in one commit.
When a legacy document is promoted, moved, or substantially edited, it must be
brought into compliance in that same change.

## Minimum Content Contracts

Metadata alone is not a compliant document. Each maintained surface must make
the following content explicit; headings may vary, but the information may not
be omitted or replaced by a link to an unrelated ledger.

| Surface | Required content |
| --- | --- |
| Owner README | What the owner owns; what it does not own; current authoritative entries; temporary legacy routes; maintenance trigger. |
| Standard | Normative scope; defined terms; mandatory and prohibited behavior; compliance evidence; change procedure. |
| Plan or `work/issues` page | Objective; evidence baseline; scope and non-goals; proposed decisions or sequence; acceptance evidence; residuals or next review trigger. |
| Task or `work/active` page | Authorized outcome; current status; owned surfaces; validation commands/evidence; blockers; closure condition. |
| Reference | Implementation/configuration sources of truth; last verification boundary; current supported behavior; known limitations; update trigger. |
| How-to | Intended outcome; prerequisites; exact procedure; observable success result; rollback or recovery path when applicable. |
| Review | Reviewed revision/date; evidence inspected; findings and severity; verdict or decision state; authority boundary; follow-up owner. |

The [documentation authoring examples](../structure_examples.md)
show compliant shapes without creating a second normative policy.

## README Boundary

A maintained README is an index, not an append-only project ledger. It should
contain only:

1. current purpose and lifecycle;
2. current authoritative entry points;
3. current status and accepted capability boundary;
4. open residuals or explicitly held work;
5. links to review, evidence, and archive indexes.

Completed work-package narratives belong in a local `archive/README.md` or a
bounded acceptance record. New or substantially rewritten maintained READMEs
should remain at or below 200 lines. A README above 300 lines requires a
documented `Size exception` explaining why an index split would be harmful.

Do not copy the same status narrative into the root README, `docs/README`, a
domain README, and a task packet. The narrowest maintained owner holds the
detail; higher-level indexes provide one-line routing and maturity boundaries.

Promoting or extracting task material into standards must not broaden the
task's scope, acceptance state, schedule, or authority. The current task owner
remains authoritative for task-specific state.

## Naming And Placement

- Stable maintained documents use `lower_snake_case.md` without a date.
- Dated snapshots use `<topic>_<YYYYMMDD>.md`.
- Reviews use `<scope>_review_<YYYYMMDD>.md` unless a stable local README owns
  the review series.
- Evidence packages use `evidence/<topic>_<YYYYMMDD>/` with `README.md` and
  `manifest.json`.
- `README.md` is reserved for directory navigation.
- New archive directories use lowercase `archive/`.
- Do not create `Archive/`, `archive/archive/`, or repeated lifecycle directory
  components. Existing legacy paths are migrated only through a reviewed,
  link-safe iteration.

## Bilingual Rules

English `.md` files are canonical and Chinese `.zh.md` files are companions.
The detailed translation workflow remains in the
[Bilingual Documentation Policy](bilingual_documentation_policy.md).

Chinese companions are mandatory for:

- root and major directory navigation READMEs;
- standards and governance authority;
- stable plan authority;
- maintained reference and operator how-to pages;
- task/domain README pages promoted as current entry surfaces.

High-churn dated tasks, reviews, evidence notes, and generated output may remain
English-only unless the local README promotes them into the strict bilingual
surface. A required pair must be updated in the same iteration. If the pair
diverges, English remains canonical, but the iteration cannot claim bilingual
closure until the companion is reconciled.

Registry hashes must be refreshed only for pairs reconciled in the current
review scope. A whole-registry rewrite is not evidence that unrelated legacy
divergence was reviewed. The current registry is rooted at `docs/`; changes to
the repository-root README pair therefore require direct bilingual review until
that pair is admitted to a machine-readable registry.

## Link Rules

- Use relative Markdown links for tracked repository targets.
- Link to an explicit `README.md` when a documentation directory is the target.
- Do not publish workstation paths such as drive-letter paths or `/home/...`.
- A maintained document must not link to an ignored, private, or absent file as
  though it were a tracked artifact.
- If an artifact is intentionally external or no longer retained, write its
  path as code and state the retention boundary instead of creating a broken
  Markdown link.
- English pages link to canonical English targets by default. Chinese entry
  pages should link to a maintained Chinese companion when one exists.
- Broken links in maintained entry surfaces are release-blocking. Archived
  link defects are warnings unless they obscure the current replacement or an
  evidence manifest.

## Evidence Rules

Evidence is retained only when it supports a named claim, acceptance gate,
reproducibility boundary, or rights/provenance obligation. An evidence package
must include:

- a short README naming the supported claim and non-claims;
- a machine-readable manifest;
- creation date and producer;
- input identities and hashes where practical;
- output identities and hashes where practical;
- retention reason and license/rights boundary;
- the task, review, or standard that consumes it.

Evidence is immutable after acceptance. Corrections create a new package and
mark the old package superseded or archived. Do not delete evidence merely
because it is old, and do not retain whole experiment directories when a small
manifest and selected outputs prove the same bounded claim.

## Generated-Document Rules

Generated documents must begin with a visible notice containing:

```text
Generated by: <repo-relative tool and command>
Inputs: <tracked paths or manifest>
Do not edit manually.
```

Generated output must be reproducible in a clean workspace. If a result cannot
be reproduced and is retained for a claim, classify it as evidence instead.
Generated summaries may support navigation but cannot replace a maintained
README, standard, review verdict, or acceptance decision.

## Configuration Rules

Canonical configuration payloads do not live under `docs/`:

- scenarios remain under `scenarios/`;
- training and runtime configuration remains under `examples/config/` or the
  owning maintained config surface;
- frozen and archived inputs retain their declared lifecycle where the config
  system owns it.

Machine-readable documentation-maintenance registries may live beside their
owner's reference material when documentation tooling is their only consumer;
they are governance indexes, not runtime configuration payloads.

Documentation may contain a `config-index` that links to those files and states
their purpose, lifecycle, compatibility boundary, and validation command. Do
not paste full JSON payloads into Markdown or keep a second editable config copy
inside a review or task packet.

## Review And Archive Lifecycle

A review must identify the exact revision or diff it inspected, remain
independent from the implementation author for that iteration, and classify
findings by behavior risk rather than prose preference. Once its actions are
transferred or closed, the review becomes `accepted` or `archived` and must not
remain presented as an active implementation queue.

A document may enter `archive/` only when:

1. a maintained replacement or parent README exists;
2. current facts needed by maintainers have been promoted to that replacement;
3. incoming maintained links have been updated;
4. provenance and evidence consumers have been checked;
5. the archive index records the reason and date.

Archived files are immutable except for link repair, license/rights correction,
or an explicit erratum. New work must not be appended to an archived packet.

## Enforcement And Migration

Every documentation iteration must run, at minimum:

```bash
git diff --check
python tools/maintenance/translate_docs_batch.py audit --root docs \
  --registry docs/engineering/documentation/reference/bilingual_document_clusters.json
```

It must also run the maintained link/document audit once that gate exists.
Migration is incremental: first establish a compliant entry and replacement,
then repair links, then move or remove redundant material. A large path move,
archive collapse, evidence deletion, or bilingual rewrite requires its own
reviewed iteration.

Repository-wide consolidation sequencing is still tracked in the migration-era
[Repository Consolidation Plan](../../../plan/repository_consolidation/README.md).

## Related Documents

- [Agent Document Authority Map](../../automation/rules/document_authority_map.md)
- [Bilingual Documentation Policy](bilingual_documentation_policy.md)
- [Standards Maintenance Policy](standards_maintenance_policy.md)
- [Subproject Creation Standard](../../automation/rules/subproject_creation_standard.md)
- [Repository Consolidation Plan](../../../plan/repository_consolidation/README.md)
