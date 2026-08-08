# Air Platform Specialization Overview

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/domains/air/README.md`
Owner: `domains/air`
Last verified: `2026-08-08`

Status: maintained owner entrypoint for current air-specialization interfaces.

This directory defines the maintained air-specific standards for the current
repository. Its purpose is not to describe every cockpit concept that a real
pilot might use. Its purpose is to describe the air-specialization contracts
that the current runtime, tests, and tasking bridge actually rely on.

## Scope

This directory owns four maintained interface standards and two draft issue
surfaces:

- mission/task observation semantics exposed to air agents
- pilot action semantics exposed by the environment and `PilotAction`
- air-specialized command/tasking semantics layered on top of common core
- air-specific pilot reporting extensions
- air-to-air kill-chain expectation-envelope review vocabulary, currently as a
  draft plan rather than a runtime contract
- the broader Air improvement backlog, which records candidates rather than
  authorized implementation

It does not own:

- joint/common command relationships
- service-level organization doctrine
- low-level physics or reward implementation details

Those belong in:

- [Simulation Conventions](../../architecture/standards/simulation_conventions.md)
- [Joint Command and Modeling Baseline](../joint/standards/command_and_modeling_baseline.md)
- [Joint Command-Link and Reporting Baseline](../joint/standards/command_link_and_reporting_baseline.md)
- [USAF Profile](../joint/service_profiles/standards/air_force_profile.md)
- [Runtime Workflow and Contract Baseline](../../architecture/standards/runtime_workflow_and_contract_baseline.md)

## How To Read This Directory

Read these files in order:

1. [Pilot Observation Contract](standards/pilot_observation_contract.md)
2. [Pilot Action Contract](standards/pilot_action_contract.md)
3. [Air Mission Command and Tasking Contract](standards/mission_command_and_tasking_contract.md)
4. [Pilot Reporting Contract](standards/pilot_reporting_contract.md)
5. [Air-To-Air Kill-Chain Expectation Envelope](work/issues/kill_chain_expectation_envelope.md)
6. [Air Improvement Backlog](work/issues/improvement_backlog.md)

The first four documents define the maintained air interface between:

- tasking/leader logic
- mission command and mission observation runtime
- pilot action input
- pilot report output

The kill-chain expectation envelope is a draft issue plan. It proposes review
labels and owner attribution for air-to-air diagnostic distributions, but it is
not a calibration result or a maintained runtime/test contract and does not
authorize implementation or runtime retuning.

The Air improvement backlog is likewise a draft issue surface. Its entries are
candidates until a separately authorized work package promotes them.

## Current Code Alignment

The maintained air-specialization contract is split across several layers in the
code base:

- air tasking extensions:
  [src/components/domains/air/tasking/README.md](../../../src/components/domains/air/tasking/README.md)
- shared command core plus air command extension:
  [src/components/command/common/README.md](../../../src/components/command/common/README.md)
- action surface:
  [src/components/command/pilot_action.h](../../../src/components/command/pilot_action.h)
- mission observation taxonomy:
  [python/mission_obs_taxonomy.py](../../../python/mission_obs_taxonomy.py)
- scenario-loader mission observation assembly:
  [gym_envs/scenario_loader/mission_observation.py](../../../gym_envs/scenario_loader/mission_observation.py)

That layering matters:

- `TaskOrderAir`, `LeaderIntentAir`, and `PilotReportAir` are tasking-side air
  extensions.
- `MissionCommand` and `PilotAction` are command/action-side runtime carriers.
- mission observation is a mode-based vector contract, not a free-form list of
  pilot sensations.

## Standardization Rules

- Keep common-core terms under `domains/joint/standards/` and service
  interpretation under `domains/joint/service_profiles/`.
- Keep air terms such as runway, takeoff, approach, formation, slot, and
  recovery in this directory.
- Document the current implemented contract first; note future extensions
  separately if needed.
- Do not describe the action or observation surface as broader than the current
  runtime/test contract.
- Draft issue plans must label held runtime behavior explicitly, cite the task
  evidence that stabilizes the vocabulary, and avoid implying implementation
  authority.

## Related Documents

- [Scenario Configuration Guide](../../operations/howto/scenario_configuration_guide.md)
- [Runtime Workflow and Contract Baseline](../../architecture/standards/runtime_workflow_and_contract_baseline.md)
- [USAF Profile](../joint/service_profiles/standards/air_force_profile.md)
- [Air-To-Air Kill-Chain Expectation Envelope](work/issues/kill_chain_expectation_envelope.md)
