# Domain Separation Split Dispatch Queue

Status: `2026-06-10` dispatch queue and progress log for [Domain Separation Split](README.md).

## Queue Policy

- Do not create new Codex conversation sessions or threads.
- In-thread subagent-style work is allowed only when write sets are isolated and
  the worker packet maps to one task cluster.
- Prefer serial integration for public headers, registration files, and status
  documents.
- The queue is finite for this round. Additions require updating the task
  cluster table instead of appending open-ended follow-up waves.

## Round 0: Boundary And Inventory

| Queue Item | Cluster | Owner | Write set | Dispatch condition | Required return |
| --- | --- | --- | --- | --- | --- |
| `Q0-A` | DS-P0-A | main thread | `docs/task/review/domain_separation_split/**`, `docs/task/review/README*` | Now | Subproject files, parent index links, `git diff --check` result |
| `Q0-B` | DS-P0-B | diagnostics worker | `*current_status*` only | After Q0-A | Include/type inventory for damage, weapon, systems, effects, sensor |

## Round 1: Component Ownership

| Queue Item | Cluster | Owner | Write set | Dispatch condition | Required return |
| --- | --- | --- | --- | --- | --- |
| `Q1-A` | DS-C1-A | implementation worker | damage component headers and direct include users | Q0-B complete | Split result, include migration, build/test evidence, residual wrapper list |
| `Q1-B` | DS-C1-B | implementation worker | weapon component headers and direct include users | Q0-B complete; avoid overlapping files with Q1-A | Split result, include migration, build/test evidence, residual wrapper list |

## Round 2: System Ownership

| Queue Item | Cluster | Owner | Write set | Dispatch condition | Required return |
| --- | --- | --- | --- | --- | --- |
| `Q2-A` | DS-S1-A | implementation worker | combat damage systems and registration | Q1-A pass | Common/air/naval/ground system split, focused runtime evidence |
| `Q2-B` | DS-S1-B | implementation worker | air systems/tuning wrappers and indexes | Q0-A complete | Air ownership candidate validation, wrapper policy, focused guards |
| `Q2-C` | DS-S1-C | implementation worker | naval logistics systems and registration | Q0-B complete; no registration overlap with Q2-A | Naval logistics extraction and focused naval evidence |

## Round 3: Model Ownership

| Queue Item | Cluster | Owner | Write set | Dispatch condition | Required return |
| --- | --- | --- | --- | --- | --- |
| `Q3-A` | DS-M1-A | implementation worker | effects model routing and domain model files | Q1-A and Q2-A pass | Effects routing split, focused effects/damage tests |
| `Q3-B` | DS-M1-B | implementation worker | sensor model routing and naval sensor adapter files | Q0-B complete; avoid interface overlap with Q3-A | Sensor adapter split and naval sensor tests |

## Round 4: Guards And Closure

| Queue Item | Cluster | Owner | Write set | Dispatch condition | Required return |
| --- | --- | --- | --- | --- | --- |
| `Q4-A` | DS-T1-A | test/architecture worker | architecture/runtime guards | Relevant implementation surfaces stable | Guard tests and failure targets |
| `Q4-B` | DS-D1-A | integration worker | docs/manual/source README and acceptance docs | Implementation and guard evidence exists | Acceptance update, residual list, index sync |

## Required Worker Packet

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Dispatch Log

| Time | Queue Item | Cluster | Assignee | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| `2026-06-09` | `Q0-A` | DS-P0-A | main thread | pass | Subproject files and parent review links created; docs diff check passed. |
| `2026-06-09` | `Q0-B` | DS-P0-B | worker `Meitner` | pass | Inventory added to current-status files; docs diff check passed. |
| `2026-06-09` | `Q1-A` | DS-C1-A | worker `Dirac` | pass | Damage component split landed with umbrella-header compatibility; combined `ef_py` build and diff checks passed. |
| `2026-06-09` | `Q1-B` | DS-C1-B | worker `Cicero` | pass | Weapon component split landed with umbrella-header compatibility; combined `ef_py` build and diff checks passed. |
| `2026-06-09` | `Q2-A` | DS-S1-A | worker `Popper` | pass | Combat damage system split landed; combined `ef_py`, include search, and diff checks passed. |
| `2026-06-09` | `Q2-B` | DS-S1-B | worker `Galileo` | pass | Air runtime ownership validation landed; old physics/tuning wrappers remain include-only. |
| `2026-06-10` | `Q2-C` | DS-S1-C | main thread | pass | Naval underway resupply extracted to `systems/naval`; `build-local-win` `ef_py`, focused naval underway tests, and diff checks passed. |
| `2026-06-10` | `Q3-A` | DS-M1-A | worker `Nash` (`gpt-5.4`/high) | pass | Effects model now routes through common domain router with Air owner helper and Naval/Ground placeholder paths; focused effects tests passed. |
| `2026-06-10` | `Q3-B` | DS-M1-B | worker `Kierkegaard` (`gpt-5.4`/high) | pass | Generic sensor model now routes ship-specific maritime reads through `models/naval` adapter; focused naval sensor tests passed. |
| `2026-06-10` | `Q4-A` | DS-T1-A | main thread | partial | Focused domain split guard added and passes; broader architecture files still fail on unrelated/direct-sim and Windows linker baselines. |
| `2026-06-10` | `Q4-B` | DS-D1-A | main thread | partial | Source/task docs synced for implemented surfaces; final subproject acceptance held on residual Air helper dependency and broader architecture failures. |
