# Air Platform Specialization Overview

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Status: `2026-05-18` specialization entrypoint for maintained air interfaces.

This directory defines the maintained air-specific standards for the current
repository. Its purpose is not to describe every cockpit concept that a real
pilot might use. Its purpose is to describe the air-specialization contracts
that the current runtime, tests, and tasking bridge actually rely on.

## Scope

This directory owns four maintained interface slices and one planning
supplement:

- mission/task observation semantics exposed to air agents
- pilot action semantics exposed by the environment and `PilotAction`
- air-specialized command/tasking semantics layered on top of common core
- air-specific pilot reporting extensions
- air-to-air kill-chain expectation-envelope review vocabulary, currently as a
  planning supplement rather than a runtime contract

It does not own:

- joint/common command relationships
- service-level organization doctrine
- low-level physics or reward implementation details

Those belong in:

- [Standards Documentation Overview](../README.md)
- [Joint Command and Modeling Baseline](../joint/command_and_modeling_baseline.md)
- [Joint Command-Link and Reporting Baseline](../joint/command_link_and_reporting_baseline.md)
- [USAF Profile](../services/air_force.md)
- [Runtime Workflow and Contract Baseline](../bridge/runtime_workflow_and_contract_baseline.md)

## How To Read This Directory

Read these files in order:

1. [Pilot Observation Contract](obs.md)
2. [Pilot Action Contract](act.md)
3. [Air Mission Command and Tasking Contract](aim.md)
4. [Pilot Reporting Contract](rep.md)
5. [Air-To-Air Kill-Chain Expectation Envelope](kill_chain_expectation_envelope.md)

The first four documents define the maintained air interface between:

- tasking/leader logic
- mission command and mission observation runtime
- pilot action input
- pilot report output

The kill-chain expectation envelope is a planning supplement. It standardizes
review labels and owner attribution for air-to-air diagnostic distributions, but
it is not a calibration result and is not yet a maintained runtime/test
contract.

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

- Keep common-core terms in `joint/` and `services/`.
- Keep air terms such as runway, takeoff, approach, formation, slot, and
  recovery in this directory.
- Document the current implemented contract first; note future extensions
  separately if needed.
- Do not describe the action or observation surface as broader than the current
  runtime/test contract.
- Planning supplements must label held runtime behavior explicitly and cite the
  task evidence that stabilizes the vocabulary.

## Related Documents

- [Scenario Configuration Guide](../bridge/scenario_guide.md)
- [Runtime Workflow and Contract Baseline](../bridge/runtime_workflow_and_contract_baseline.md)
- [USAF Profile](../services/air_force.md)
- [Air-To-Air Kill-Chain Expectation Envelope](kill_chain_expectation_envelope.md)
