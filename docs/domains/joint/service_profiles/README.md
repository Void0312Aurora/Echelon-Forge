# Service Profiles

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/domains/joint/service_profiles/README.md`
Owner: `domains/joint/service-profiles`
Last verified: `2026-08-08`

This nested owner defines how U.S. military service profiles interpret the
shared Joint common-core vocabulary. A service profile selects admissible
organization, task-packaging, authority, and tactical-unit interpretations; it
does not own air, naval, or ground execution semantics.

## Current Authority

- [U.S. Air Force Profile](standards/air_force_profile.md)
- [U.S. Army Profile](standards/army_profile.md)
- [U.S. Navy Profile](standards/navy_profile.md)
- [U.S. Marine Corps Profile](standards/marine_corps_profile.md)

Read these profiles after the parent [Joint owner index](../README.md) and its
[command and modeling](../standards/command_and_modeling_baseline.md) and
[command-link and reporting](../standards/command_link_and_reporting_baseline.md)
standards.

## Owner Boundary

Service profiles own:

- service-specific interpretation of Joint common-core fields;
- which organizational layers remain scenario or force-packaging metadata;
- which tactical-unit forms may enter a domain runtime;
- the boundary where service terminology must hand off to a domain owner.

Service profiles do not own platform control, observation/action layouts,
movement, station geometry, sensing, weapon behavior, damage, or other domain
execution contracts. Those remain with the air, naval, and ground owners.

## Domain Handoffs

Use the current domain-owner routes for execution semantics:

- [Air specialization](../../air/README.md)
- [Ground specialization](../../ground/README.md)
- [Naval specialization](../../naval/README.md)

Directory placement under Joint is an information-architecture decision. It
does not collapse service-profile interpretation into the Joint common core or
grant Joint ownership over domain execution.

## Related Legacy Routes

- [Simulation Conventions](../../../architecture/standards/simulation_conventions.md)
- [Document Alignment Map](../../../engineering/documentation/reference/document_alignment_map.md)
- [Scenario Configuration Guide](../../../operations/howto/scenario_configuration_guide.md)
- [Runtime Workflow and Contract Baseline](../../../architecture/standards/runtime_workflow_and_contract_baseline.md)
