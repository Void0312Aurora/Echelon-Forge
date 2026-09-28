# Carrier Strike Group Engagement Dispatch Queue

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/work/active/carrier_strike_group_engagement/carrier_strike_group_engagement_dispatch_queue_20260928.md`
Owner: `domains/naval`
Last verified: `2026-09-28`

Status: `2026-09-28`; only `P0-A` is active. No implementation packet is ready
until `P0-A` is approved.

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
| `CSG-P0-A-boundary` | `P0-A` | active, main thread | this directory; naval owner README index | doc link and bilingual audits |
| `CSG-S0-A-oob` | `S0-A` | waiting on `P0-A` | `docs/domains/naval/reference/csg_order_of_battle_*.md` | provenance completeness |
| `CSG-S0-B-geodesy-integration` | `S0-B` | waiting on [Geodetic Frame](../../../../../systems/physics/work/active/geodetic_frame/README.md) `P3-B` | `scenarios/naval/csg/`; naval scenario tests | scenario anchor tests |

## No-Dispatch Conditions

Do not dispatch an implementation worker while:

- `P0-A` is unapproved;
- the cluster would need to change an Air or Joint owner surface without that
  owner's seam being agreed;
- the cluster would need a parameter that has neither a source nor a recorded
  engineering estimate;
- the cluster consumes a system-owner deliverable whose owner package has not
  reached the named phase.
