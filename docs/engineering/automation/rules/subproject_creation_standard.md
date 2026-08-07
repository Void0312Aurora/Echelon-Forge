# Subproject Creation Standard For Agents

Language:
- English canonical: `subproject_creation_standard.md`
- Chinese companion: [subproject_creation_standard.zh.md](subproject_creation_standard.zh.md)

Status: `2026-06-01` maintained rule for creating new task subprojects and
subproject documentation.

Scope: new or revived subprojects under `docs/task/**`, plus the task-cluster
documents that agents use to plan, dispatch, implement, validate, and close a
bounded work slice.

This standard abstracts recurring structure from maintained task slices without
promoting any historical subproject as current authority. For delegated work,
use [Subagent Usage Policy](../standards/subagent_usage_policy.md).

## When To Create A Subproject

Create a subproject directory only when the work needs a durable execution
surface. Use a single assessment note or an existing README section when the work is
small.

Create a subproject when at least one is true:

- the work spans multiple files, phases, or owners;
- implementation must be split into finite task clusters;
- the work changes domain maturity, public capability claims, runtime contracts,
  scenarios, configs, or tests;
- the work needs explicit current status, acceptance, residuals, or archive
  handling;
- future agents must be able to resume without relying on chat history.

Do not create a subproject merely to restate an existing plan, to park an
unclear idea, or to avoid updating the nearest maintained README.

## Location And Naming

Use this location pattern:

```text
docs/task/<domain>/<subproject_slug>/
```

Rules:

- `<domain>` must already exist or be added to `docs/task/README*`.
- `<subproject_slug>` should be short, lowercase, and stable.
- Prefer a prefix when the parent domain already uses a phase sequence, such as
  `<phase>_<short_scope>` or `<domain_phase>_<short_scope>`.
- Avoid names that imply a higher maturity level than the scoped work proves.
  If a legacy name is misleading, add a local warning banner before expanding
  the directory.
- New top-level task domains require updates to `docs/task/README*` and the
  affected standards or manual entry points.

## Required Minimal File Set

Every maintained subproject must contain:

```text
README.md
<subproject_slug>_task_clusters_<YYYYMMDD>.md
```

Add these files when the slice is long-running or high-risk:

```text
<subproject_slug>_current_status_<YYYYMMDD>.md
<subproject_slug>_dispatch_queue_<YYYYMMDD>.md
<subproject_slug>_acceptance_<YYYYMMDD>.md
archive/README.md
```

Use Chinese companions for maintained public entry surfaces or stable
governance/status documents. High-churn implementation slices may be
English-canonical only when the parent README says so.

## README Required Sections

`README.md` is the current navigation and scope authority for the subproject.
It must include these sections, in this order unless a strong local reason
exists:

1. Title
2. `Status:` line
3. `Language:` block
4. `Inputs:` or `Related authority:` links
5. `Purpose`
6. `Current state`
7. `Scope`
8. `Phase plan`
9. `Task clusters`
10. `Outputs and evidence`
11. `Acceptance gate`
12. `Residuals and next steps`
13. `Archive`

Minimum README template:

```md
# <Subproject Title>

Status: `<YYYY-MM-DD>` <proposed | planning | active | accepted | held | closed | archived> <short status>.

Language:

- English canonical: `README.md`
- Chinese companion: <link or "not required yet; high-churn task slice">

Inputs:

- <parent task README>
- <relevant standard>
- <relevant code/test/scenario entry>

## Purpose

<One or two paragraphs describing the work content and why this subproject exists.>

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| <area> | <accepted/active/held> | <code/test/doc link> | <what this does not prove> |

## Scope

In scope:

- <specific work item>

Out of scope:

- <explicit non-goal and forbidden capability claim>

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze scope and authority. | <input> | <gate> | <status> |
| `P1 Evidence` | Collect source/code/test facts. | <input> | <gate> | <status> |
| `P2 Implementation` | Implement the scoped behavior. | <input> | <gate> | <status> |
| `P3 Integration` | Wire maintained runtime/config/test surfaces. | <input> | <gate> | <status> |
| `P4 Validation` | Run acceptance and record residuals. | <input> | <gate> | <status> |
| `P5 Closure` | Sync docs/index/archive. | <input> | <gate> | <status> |

## Task Clusters

- Task cluster plan: `<subproject_slug>_task_clusters_<YYYYMMDD>.md`

## Outputs And Evidence

- <code/config/scenario/test/doc output>

## Acceptance Gate

This subproject can be marked accepted only when:

- <testable condition>
- <documentation condition>
- <forbidden overclaim remains refused>

## Residuals And Next Steps

- <held item>
- <next credible expansion>

## Archive

Superseded or historical records move to `archive/README.md` when the
subproject has a replacement current-status or closeout surface.
```

## Task-Cluster Document Required Sections

The task-cluster document is the finite execution plan. It prevents a subproject
from turning into an open-ended sequence of follow-up waves.

Required sections:

1. Title
2. `Status:` line
3. Parent subproject link
4. Boundary or decision statement
5. Finite task cluster list
6. Dispatch rules
7. Worker packet requirements
8. Validation plan
9. Acceptance criteria
10. Residual map

Required cluster table columns:

| Column | Meaning |
| --- | --- |
| `Cluster` | Stable cluster id, such as `P1-A`, `D2-B`, or `INT-C`. |
| `Owner` | Main thread, named worker, future worker, integration worker, or read-only diagnostics worker. |
| `Capability tier / model ID / reasoning` | Record the tier and available reasoning control; include an exact model ID only when the current execution environment explicitly exposes it, otherwise use `n/a`. |
| `Goal` | One bounded result. |
| `Write set` | Exact files or file families the cluster may modify. |
| `Non-goals` | Explicit exclusions and forbidden capability claims. |
| `Validation` | Commands, link checks, contract runners, or inspection checks. |
| `Closure gate` | Condition that changes the cluster status. |
| `Dependency / parallel` | What must happen first and whether parallel work is safe. |
| `Round cap` | Maximum implementation/repair rounds before re-scoping. |
| `Status` | `planned`, `active`, `pass`, `partial`, `blocked`, `failed`, `accepted`, or `closed`. |

Minimum task-cluster template:

```md
# <Subproject> Task Clusters

Status: `<YYYY-MM-DD>` finite task-cluster plan for `<Subproject README.md>`.

## Boundary Decision

<What this subproject is allowed to change, and what it must not imply.>

## Finite Task Cluster List

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<ID>` | <owner> | <tier / explicit available model ID or n/a / reasoning> | <goal> | <files> | <excluded work> | <commands> | <gate> | <dependency/parallel rule> | <round cap> | <status> |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not allow two workers to edit the same normative table, scenario contract,
  public API, or status line concurrently.
- Keep acceptance/closure clusters serial.
- If a cluster exceeds its round cap, stop and re-scope before adding a follow-up
  wave.
- Follow [Subagent Usage Policy](../standards/subagent_usage_policy.md).

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan

```bash
<repo-root command>
```

## Acceptance Criteria

- <condition>

## Residual Map

Immediate:

- <residual>

Follow-on:

- <next scoped package>

Deferred:

- <explicitly held surface>
```

## Current-Status Document

Long-running domains or multi-slice subprojects should keep a current-status
document. It should not replace the local README; it records dated state.

Recommended filename:

```text
<domain_or_subproject>_current_status_<YYYYMMDD>.md
```

Required content:

- status line and date;
- what changed since the prior checkpoint;
- maturity matrix: accepted, active, held, blocked, deferred;
- evidence links to code, scenarios, configs, tests, retained artifacts, or
  cluster records;
- residual register or residual map;
- next recommended action order;
- explicit overclaim refusals.

## Acceptance And Closeout Documents

Add an acceptance or closeout document when the subproject changes capability
status, closes a high-risk residual, or promotes a scenario/config/test as
maintained evidence.

Acceptance documents must name:

- accepted scope;
- validation commands and outcomes;
- evidence artifacts;
- residuals that remain open;
- capability claims that are still forbidden;
- indexes that were synchronized.

Do not mark a subproject `closed` while current README, parent README, tests,
reference artifacts, or standards links still point to superseded status.

## Archive Rules

Use `archive/` for superseded local records only after there is a current README,
current status, or acceptance surface that tells readers where to start.

Archive rules:

- keep `archive/README.md` if the archive contains more than one file;
- never use archived records as default authority in new Agent prompts;
- do not delete historical evidence merely because it is stale;
- if an archived file contains a still-relevant fact, promote the fact into the
  current README or status doc and cite the archive as provenance.

## Status Vocabulary

Use these status words consistently:

| Status | Meaning |
| --- | --- |
| `proposed` | Idea exists, not accepted as a work surface. |
| `planning` | Scope is being bounded; implementation should not start yet. |
| `active` | Work is open and current. |
| `pass` | Assigned cluster passed its scoped gate. |
| `partial` | Evidence exists, but the gate is not unlocked. |
| `blocked` | Named blocker prevents honest progress without re-scope or owner input. |
| `accepted` | Scoped acceptance gate passed; residuals may remain. |
| `held` | Explicitly deferred and should not be implemented or claimed in this slice. |
| `closed` | Accepted work plus index/archive/doc synchronization is complete. |
| `archived` | Historical; not current authority by default. |

## Anti-Patterns

Avoid these:

- creating a subproject without a parent README link;
- creating a cluster plan with no finite cluster list;
- omitting non-goals and then over-claiming maturity;
- allowing repeated "one more repair round" without re-scoping;
- treating a dispatch queue as implementation evidence;
- marking a scenario-only asset as active training/runtime acceptance;
- marking a docs-only pass as runtime pass;
- leaving important findings only in chat;
- letting retained or signoff artifacts define broader project maturity.

## Agent Checklist

Before creating or updating a subproject, an Agent must verify:

- the parent domain README exists and will link the subproject;
- the relevant standards owner is linked;
- the README includes purpose, current state, scope, phase plan, task clusters,
  acceptance gate, and residuals;
- the task-cluster document has finite clusters and round caps;
- validation commands are repo-root runnable or explicitly marked docs-only;
- status words are scoped and do not imply broader maturity;
- archive/current boundaries are explicit;
- links pass local Markdown checks.
