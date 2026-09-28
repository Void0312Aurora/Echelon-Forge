# Naval Mission Domain

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/README.md`
Owner: `domains/naval`
Last verified: `2026-09-23`

Status: maintained owner entrypoint for naval execution semantics.

This directory owns the current naval execution contract: maritime
screen/support behavior, station geometry, recovery behavior, naval command and
observation specialization, and the ship-unit references used to anchor that
work. It does not own the shared Joint schema or the Navy interpretation of
that schema.

## Maintained Authority

Read these owner-local documents together:

1. [Naval Minimal Task Structure](standards/minimal_task_structure.md)
2. [Naval Observation Contract](standards/observation_contract.md)
3. [Naval Ship Unit References](reference/ship_unit_references.md)

The first two are normative standards. The ship-unit page is a maintained
reference baseline and does not define task semantics.

## Ownership Boundary

The [Navy service profile](../joint/service_profiles/standards/navy_profile.md)
interprets Joint common-core fields for Navy organization and authority. It
owns the service-level meaning of:

- `task_group` and `task_unit`
- `warfare_role_code`
- `officer_in_tactical_command`
- Navy-specific task packaging and authority anchors

This Naval domain owns how maritime units execute that interpretation:

- `screen`, `support`, `station`, and `recover` behavior
- ship and formation control semantics
- screen/station observation geometry and reporting state
- naval command, tasking, and execution specialization

Joint common core retains the service-neutral carrier shapes, including
`service_profile`, `task_family`, `command_relationship`, `authority_scope`,
`coordination_mode`, `tactical_unit_type`, and shared identifiers. Naval may
constrain how those shapes are used for maritime execution, but it does not
redefine their cross-service schema.

## Current Implementation Boundary

The repository currently provides maintained, bounded naval surfaces rather
than a complete fleet simulation:

- naval tasking and command DTO extensions
- `naval_screen_station_v1`, a fixed 23-field mission-observation mode
- task/profile mappings for screen, support, patrol, and recover families
- contact, assignment, reporting, ROE, and station/screen execution inputs
- initial ship and naval weapon-system configuration baselines

These surfaces do not establish full fleet doctrine, complete maneuver and
station-keeping controllers, replenishment operations, or authoritative naval
weapon and damage calibration.

## Standardization Rules

- Keep shared contract definitions in
  [Joint standards](../joint/standards/command_and_modeling_baseline.md).
- Keep Navy service interpretation in the
  [Navy service profile](../joint/service_profiles/standards/navy_profile.md).
- Keep maritime execution and reporting semantics in this owner directory.
- Describe maintained code and test contracts before proposed extensions.
- Do not import air-specific sortie, runway, or lead/wingman semantics unless a
  naval interface explicitly consumes them.

## Active Work and Related Documents

- [Carrier strike group engagement](work/active/carrier_strike_group_engagement/README.md):
  forward naval combat program, in planning. A scenario ladder from static
  order of battle to a full Ford-class versus Fujian-class group engagement,
  with a parallel undersea track. It replaces the historical `N0`-`N8` ladder
  as the forward plan.
- [Naval domain-surface split](work/active/naval_domain_surface_split/README.md):
  current bounded package. `P2-B` landed the naval command projection and the
  split-branch native regression test now discharges the former projection hold;
  the [`P5-A` closure record](work/active/naval_domain_surface_split/naval_domain_surface_split_p5_closure_20260922.md)
  records acceptance for the bounded N4 surface while keeping N5/N6 out of scope.
- [Naval progress snapshot — 2026-05-27](reviews/naval_progress_snapshot_20260527.md):
  dated review evidence, not the latest status authority. Its `N0`-`N8` ladder
  is historical and is superseded as a forward plan by the carrier strike group
  engagement package.
- [Joint Command and Modeling Baseline](../joint/standards/command_and_modeling_baseline.md)
- [Joint Command-Link and Reporting Baseline](../joint/standards/command_link_and_reporting_baseline.md)
