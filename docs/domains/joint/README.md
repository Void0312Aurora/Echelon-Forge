# Joint Mission Domain

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/domains/joint/README.md`
Owner: `domains/joint`
Last verified: `2026-08-07`

The Joint owner defines cross-domain authority relationships, task-organization
vocabulary, and intent/order/report interfaces that must retain the same meaning
across air, naval, and ground work. It does not own service doctrine or any
domain's execution geometry, timing, control, sensing, or weapon semantics.

## Current Authority

- [Joint Command and Modeling Baseline](standards/command_and_modeling_baseline.md):
  defines the common-core naming, authority, and modeling boundary.
- [Joint Command-Link and Reporting Baseline](standards/command_link_and_reporting_baseline.md):
  defines the minimum command-delivery, reporting, data-link, and ROE loop.

## Owner Boundary

- Joint owns relationships and common contract shapes that survive across
  services.
- Service profiles interpret those common objects for a military service.
- Air, naval, and ground owners define their own platform and mission execution
  semantics.
- Terms such as `wingman`, `runway`, `destroyer screen`, and `platoon wedge`
  must not be promoted into the Joint common core.

## Pending Owner Migration

Service profiles and domain-specific standards remain on their maintained
legacy routes until their separate migration slices land:

- [Service profiles](../../standards/services/README.md)
- [Air specialization](../../standards/air/README.md)
- [Naval specialization](../../standards/naval/README.md)
- [Ground specialization](../../standards/ground/README.md)

These links are transitional routes, not a claim that Joint owns the linked
execution semantics.

## Reference Basis

- [Joint Chiefs service publications](https://www.jcs.mil/Doctrine/Service-Publications/)
- [CJCSM 3150.13C, Joint Reporting Structure](https://www.jcs.mil/Portals/36/Documents/Library/Manuals/m315013.pdf)
