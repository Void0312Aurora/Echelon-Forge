# Carrier Strike Group Engagement Dispatch Queue

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/work/active/carrier_strike_group_engagement/carrier_strike_group_engagement_dispatch_queue_20260928.md`
Owner: `domains/naval`
Last verified: `2026-09-30`

Status: `2026-09-30`; `P0-A` and `S0-A`..`S0-X` accepted. S0-X closes with
full-duration runtime, native replay artifacts, and agent-free visualization
profiles. S1/U1 are unblocked by the S0-X dependency gate.

Parent project: [Carrier Strike Group Engagement](README.md)

## Queue Rules

- Dispatch only clusters listed in
  [carrier_strike_group_engagement_task_clusters_20260928.md](carrier_strike_group_engagement_task_clusters_20260928.md).
- One packet maps to one cluster.
- Do not edit the README, current status, or acceptance documents in parallel
  with implementation workers.
- Shared-runtime clusters run serially.

## Ready Packets

| Packet | Cluster | Status | Write set | Validation |
| --- | --- | --- | --- | --- |
| `CSG-P0-A-boundary` | `P0-A` | accepted `2026-09-28` | this directory; naval owner README index | doc link and bilingual audits |
| `CSG-S0-A-oob-blue` | `S0-A` | accepted `2026-09-28` ([Ford OOB](../../../reviews/csg_order_of_battle_20260928/csg_order_of_battle_ford_20260928.md)) | research scratch; main thread integrates into `docs/domains/naval/reviews/csg_order_of_battle_20260928/` | provenance completeness |
| `CSG-S0-A-oob-red` | `S0-A` | accepted `2026-09-28` ([Fujian OOB](../../../reviews/csg_order_of_battle_20260928/csg_order_of_battle_fujian_20260928.md)) | research scratch; main thread integrates into `docs/domains/naval/reviews/csg_order_of_battle_20260928/` | provenance completeness |
| `CSG-S0-B-geodesy-integration` | `S0-B` | accepted `2026-09-30`, `087c1928`; current full-duration scenario checks pass | `scenarios/naval/csg/`; naval scenario tests; stateless geodesy bindings | scenario anchor tests |
| `CSG-S0-X-stage-checkpoint` | `S0-X` | accepted `2026-09-30`; [runtime checkpoint](carrier_strike_group_engagement_acceptance_20260928.md#csg-s0-runtime-checkpoint-2026-09-30); main thread, serial | stage acceptance record; full-duration scenario tests; replay contracts and profiles | new simulation mechanisms |

## No-Dispatch Conditions

Do not dispatch an implementation worker while:

- the cluster would need to change an Air or Joint owner surface without that
  owner's seam being agreed;
- the cluster would need a parameter that has neither a source nor a recorded
  engineering estimate;
- the cluster consumes a system-owner deliverable whose owner package has not
  reached the named phase.
