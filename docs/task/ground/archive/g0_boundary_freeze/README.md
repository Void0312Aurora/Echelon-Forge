# G0 Boundary Freeze

Status: `2026-05-21` accepted by main-thread G0-D; G1 may start as
`preflight-only`.

Language:

- English canonical: `README.md`
- Chinese companion: not required yet; this is a high-churn task slice.

Inputs:

- [Ground domain bootstrap plan](../ground_domain_bootstrap_plan_20260521.md)
- [Ground standards overview](../../../standards/ground/README.md)
- [Ground minimal task structure](../../../standards/ground/minimal_task_structure.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Freeze the third-domain naming, layer ownership, minimum task vocabulary, and
G0 architecture commitments before G1 begins. This stage is documentation and
standards work only.

## Output

- [G0 standards alignment cluster](g0_standards_alignment_cluster_20260521.md)
- [G0 subagent dispatch packets](g0_subagent_dispatch_packets_20260521.md)

## Accepted Worker Returns

- `G0-A`: pass. The standards overview preserves frozen defaults, clarifies
  `army` and `land` alias normalization to `ground`, and keeps
  `spawn_unit(type_name)` as a compatibility wrapper only.
- `G0-B`: pass. The minimal task structure preserves `TASK_MOVE`,
  `TASK_OCCUPY`, and `TASK_SUPPORT` as the only starter task shapes while
  keeping movement, sensing, fires, logistics, damage, and terrain realism
  deferred.
- `G0-C`: pass. Navigation, dispatch docs, and the bilingual registry are
  synchronized after the normative standards are stable.
- `G0-D`: accepted. Main-thread review found no G0 standards blocker and keeps
  G1 limited to `preflight-only` until resolver/profile scope is confirmed.

## Scope

In scope:

- standards landing point under `docs/standards/ground/`
- minimum task vocabulary and architecture commitments
- standards/tree navigation updates
- subagent-dispatch structure for later stages

Out of scope:

- Python profile implementation
- C++ DTO changes
- scenario fixtures
- runtime behavior

## Gate

G0 is accepted because standards, task navigation, and dispatch docs all agree
on:

- maintained name: `ground`
- accepted aliases: `army`, `ground`, `land`
- first tight-loop unit: `platoon`
- first tasks: `TASK_MOVE`, `TASK_OCCUPY`, `TASK_SUPPORT`
- no private ground runtime path
- release order: G0-A and G0-B may run in parallel, G0-C runs serially after
  both return, and G0-D remains main-thread acceptance
- G1 release: `preflight-only`; no remaining G0 standards blocker is known, but
  implementation is not released by G0-D
