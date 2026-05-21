# G0 Standards Alignment Cluster

Status: `2026-05-21` accepted by main-thread G0-D; G1 release is
`preflight-only`.

Inputs:

- [Ground domain bootstrap plan](../ground_domain_bootstrap_plan_20260521.md)
- [Ground domain bootstrap review](../../review/ground_domain_bootstrap_plan_review_20260521.md)
- [G0 subagent dispatch packets](g0_subagent_dispatch_packets_20260521.md)
- [Ground standards overview](../../../standards/ground/README.md)
- [Ground minimal task structure](../../../standards/ground/minimal_task_structure.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Make G0 a real standards constraint before implementation starts. This cluster
turns the reviewed bootstrap plan into maintained standards documents and task
indexes.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `G0-A1` | Standards entry | `docs/standards/ground/README.md` declares layer model, G0 defaults, stage coverage, capability path, agency, and information-state rules. |
| `G0-A2` | Minimal task structure | `docs/standards/ground/minimal_task_structure.md` freezes `TASK_MOVE`, `TASK_OCCUPY`, and `TASK_SUPPORT`. |
| `G0-A3` | Standards navigation | `docs/standards/README.md` and `docs/standards/overview/document_alignment_map.md` route ground concepts to `services/army` and `ground/`. |
| `G0-A4` | Task navigation | `docs/task/ground/README.md` points to G0-G4 stages and the dispatch queue. |
| `G0-A5` | Bilingual surface | Tier A standards files have Chinese companions and the cluster registry is refreshed. |
| `G0-A6` | Dispatch readiness | G0 worker packets split standards overview, task vocabulary, and integration work into serializable write scopes. |

## Accepted Return Integration

- `G0-A` returned `pass`: frozen defaults remain `ground`, `platoon`,
  `move / occupy / support`, and `1 Hz`; `army` and `land` aliases normalize to
  `ground`; capability composition stays canonical.
- `G0-B` returned `pass`: `TASK_MOVE`, `TASK_OCCUPY`, and `TASK_SUPPORT`
  remain the only starter shapes; platoon remains the first tight-loop owner;
  movement, sensing, fires, logistics, damage, and terrain realism remain
  deferred.
- `G0-C` returned `pass`: navigation, registry, and dispatch synchronization
  are complete. It did not release G1 implementation.
- `G0-D` accepted G0 and released only G1 preflight.

## Release Recommendation

Accepted next state: `G1 preflight-only`.

No G0 standards blocker is known after the accepted G0-A and G0-B returns, but
G1 implementation should wait until a preflight confirms the resolver/profile
write scope and whether DTO shells are actually required.

## Write Scope

Allowed:

- `docs/standards/ground/**`
- `docs/standards/README*.md`
- `docs/standards/overview/document_alignment_map*.md`
- `docs/standards/bilingual_document_clusters.json`
- `docs/task/ground/**`

Do not edit:

- runtime code
- Python profile code
- `docs/standards/joint/**` unless a shared concept truly must move there
- unrelated task directories

Release order:

- `G0-A` and `G0-B` may run in parallel because their normative write scopes are
  disjoint.
- `G0-C` runs after both accepted returns and only updates navigation,
  registry, and dispatch surfaces.
- `G0-D` remains the main-thread acceptance step.

## Suggested Validation

```bash
git diff --check
python tools/maintenance/translate_docs_batch.py clusters --write
python tools/maintenance/translate_docs_batch.py audit --show-missing none
```

## Handoff

Return:

- touched files
- standards decisions made
- unresolved G1 inputs
- commands run
- any suspected naming/layering conflict
- recommendation for G1 release: `preflight-only`, `implementation-ready`, or
  `blocked`
