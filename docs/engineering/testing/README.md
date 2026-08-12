# Testing Engineering

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/engineering/testing/README.md`
Owner: `engineering/testing`
Last verified: `2026-08-08`

This owner covers repository-wide test organization, collection and coverage
governance, test infrastructure, and cross-owner validation conventions. It
does not own a domain's behavioral contract, and a dated review does not
override current tests or the relevant technical standard.

## Current Authority

- [Tests index](../../../tests/README.md)
- [Known test-infrastructure residuals](reference/known_test_infrastructure_residuals.md)
- [Test-system residual governance issue](work/issues/test_system_residual_governance/README.md)
- [Test-system governance acceptance packet](reviews/test_system_governance_20260621/README.md)

Other files under `reviews/` are dated supporting records. Treat their measured
counts and implementation observations as snapshots until reverified.

## Routing Boundary

- Domain and runtime owners define what behavior must hold.
- Testing engineering defines how repository-wide gates, collection,
  categorization, and infrastructure residuals are represented.
- Coverage data proves only the measured source set and command recorded by the
  evidence packet.
- Completed task and plan packets under legacy archive paths are provenance,
  not current testing authority.

## Reverification Triggers

Update this index when test roots, CI lanes, coverage ownership, strict-xfail
policy, or the owner-local issue/review routes change.
