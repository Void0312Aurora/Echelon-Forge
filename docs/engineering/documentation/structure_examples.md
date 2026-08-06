# Documentation Structure Examples

Language: English canonical; [Chinese companion](structure_examples.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/engineering/documentation/structure_examples.md`
Owner: `engineering/documentation-governance`
Last verified: `2026-08-07`

These examples define reusable document shape. They do not supply technical
facts, acceptance, or normative authority for a content owner. Replace every
placeholder with verified content and remove optional sections that do not
apply; never invent evidence to complete a skeleton.

## Owner Directory Shape

Create a child directory only when it contains maintained material:

```text
<owner>/
  README.md
  README.zh.md
  standards/                 # normative rules accepted by this owner
  reference/                 # verified current facts
  work/
    active/<work-package>/   # authorized implementation and acceptance state
    issues/                  # unaccepted problems, roadmaps, and proposals
  reviews/                   # bounded judgments and review snapshots
```

Nested owners use the same shape. For example,
`systems/physics/work/issues/physics_engine_roadmap.md` is a draft plan owned by
the physics system; its location does not make the roadmap an accepted task.

## 1. Owner README

```markdown
# <Owner Name>

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/<owner>/README.md`
Owner: `<owner>`
Last verified: `<YYYY-MM-DD>`

<One paragraph defining what this owner owns and explicitly excludes.>

## Current Authority

- [<standard or reference>](<path>): <authority boundary>.

## Active Work

- [<work package>](<path>): <current state and acceptance boundary>.

## Open Issues

- [<issue>](<path>): <why it is not yet authorized or accepted>.
```

Do not append completed work history to this README. Retain only current routes
and one-line maturity boundaries.

## 2. Standard

```markdown
# <Topic> Standard

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/<owner>/standards/<topic>.md`
Owner: `<owner>`
Last verified: `<YYYY-MM-DD>`

## Scope
<Named producers, consumers, and excluded surfaces.>

## Normative Rules
- `<producer>` MUST <obligation>.
- `<consumer>` MUST NOT <prohibited behavior>.

## Verification
- `<test or review gate>` verifies <rule>.

## Exceptions And Change Triggers
<Allowed exceptions, conflict resolution, and events requiring re-review.>
```

A recommendation, roadmap, or collection of examples without normative rules
and verification remains a plan or reference, not a standard.

## 3. Reference

```markdown
# <Topic> Reference

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/<owner>/reference/<topic>.md`
Owner: `<owner>`
Last verified: `<YYYY-MM-DD>`

## Verification Boundary
<Revision, code/config sources, platform, and commands checked.>

## Current State
<Verified facts only.>

## Limitations
<Unknowns, unsupported cases, and facts not checked.>

## Reverification Triggers
<Changes that make this page stale.>
```

## 4. Active Work Package

```markdown
# <Work Package>

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/<owner>/work/active/<package>/README.md`
Owner: `<owner>`
Last verified: `<YYYY-MM-DD>`

## Objective
<One bounded outcome.>

## Scope And Non-goals
<Included and explicitly excluded work.>

## Acceptance Evidence
- `<command, test, or review>`: `<required result>`.

## Current Status
<Planned, active, mergeable, blocked, or closed with evidence.>

## Residuals
<Unresolved items and their owners.>
```

## 5. Issue Or Roadmap

```markdown
# <Issue Or Roadmap>

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/<owner>/work/issues/<topic>.md`
Owner: `<owner>`
Last verified: `not established`
Content status: unverified draft; supply a dated evidence baseline before promotion.

## Problem And Evidence
<Observed gap and bounded evidence.>

## Proposed Direction
<Candidate approach; do not phrase it as implemented behavior.>

## Promotion Gate
<Decision, evidence, and owner approval needed before active work begins.>

## Non-goals
<Adjacent work not authorized by this issue.>
```

The migrated Phase-2 roadmaps use this structure. `work/issues` explicitly
means that directory placement does not authorize implementation.

## 6. Review Snapshot

```markdown
# <Scope> Review — <YYYY-MM-DD>

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/<owner>/reviews/<scope>_review_<YYYYMMDD>.md`
Owner: `<owner>/reviews`
Last verified: `<YYYY-MM-DD>`
Review basis: `<revision and date>`

## Scope And Independence
<Reviewed revision, evidence set, reviewer role, and limitations.>

## Findings
<Evidence-backed findings.>

## Verdict
<Accepted, rejected, advisory, or blocked within the review scope.>

## Follow-up Routes
<Owner-local issue or active-work links; the review does not implement them.>
```

A dated review remains a snapshot. Moving it to an owner-local `reviews/`
directory does not make its historical metrics current.
