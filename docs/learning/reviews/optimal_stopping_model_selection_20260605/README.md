# M3 Optimal-Stopping Model Selection

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/learning/reviews/optimal_stopping_model_selection_20260605/README.md`
Owner: `learning/reviews`
Last verified: `2026-08-08`
Review basis: `2026-06-05` problem definition, research packets, and synthesis.

Status: `2026-06-05` model-selection synthesis complete; follow-on planning
contract opened as M3-S1, while training code remains held.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent model task index: [Model Tasks](../../../learning/README.md)
- A7 current evidence:
  [A7 Current Status](../../../task/air_combat/archive/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_current_status_20260604.md)
- A7 execution breakpoint:
  [A7 Execution Breakpoint Analysis](../../../task/air_combat/archive/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_execution_breakpoint_analysis_20260605.md)
- A7 event-policy margin repair:
  [A7 Event-Policy Margin Repair](../../../task/air_combat/archive/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_event_policy_margin_repair_20260605.md)
- Subproject standard:
  [Subproject Creation Standard](../../../engineering/automation/rules/subproject_creation_standard.md)
- Distributed-work rule:
  [Subagent Usage Policy](../../../engineering/automation/standards/subagent_usage_policy.md)

## Purpose

M3 turns the blocked A7 first-event timing line into a model-selection problem.
The immediate goal is not another coefficient sweep or another local A7 patch.
The goal is to define the abstract mathematical object behind the failure and
compare model families that could solve that object with lower structural risk.

The military scenario is treated only as one instance of a generic one-shot
timing problem: an agent observes a sequence, must choose at most one event
time, should avoid early events, should choose inside a desirable window, and
receives censored on-policy data because an early event changes the rest of the
trajectory.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| A7 local repairs | held | A7 has labels, credit-head capacity, direct event-policy margin, and one-shot legality, but deterministic probing still records `0` releases and active event-credit rows collapse late in training. | Does not justify another A7 coefficient sweep as the default next step. |
| Mathematical abstraction | pass | [Formal problem statement](m3_formal_problem_statement_20260605.md) defines a censored constrained one-shot timing problem. | Does not implement the selected model. |
| Distributed research | pass | R1/R2/R3 research packets are complete and separately documented. | Dispatch results are evidence inputs, not runtime changes. |
| Model-selection synthesis | pass | [Model-selection synthesis](m3_model_selection_synthesis_20260605.md) recommends a censored optimal-stopping timing contract with survival/event-time calibration and wait-preserving data. | Does not open or accept an implementation contract. |
| Follow-on planning | superseded by retained review evidence | [M3-S1 Censored Optimal-Stopping Timing Contract](../grouped_stopping_contract_20260605/README.md) records the implemented boundary and P5 evidence. | This dated decision does not reopen code or claim learned-policy acceptance. |

## Scope

In scope:

- Define a domain-neutral mathematical object for one-shot event timing under
  partial observability, legality masks, and post-event censoring.
- Compare model families by identifiability, deterministic decision boundary,
  cumulative early-event hazard, compatibility with on-policy data, and
  implementation risk.
- Produce separate research documents for self-designed algorithms, academic
  literature, and suitable existing model families.
- Produce a later synthesis that recommends whether M1/M2/A7 should continue or
  whether a new model contract is required.

Out of scope:

- New training code, new runtime behavior, or missile/domain physics changes.
- Declaring A7 accepted or rejected as an implementation.
- Starting M2 merely because A7 is blocked.
- Reusing military-specific terms as the core mathematical definition.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Problem` | Freeze the abstract mathematical object and model-selection criteria. | A7 safe-bias follow-up remains held. | Formal problem statement and README exist. | pass |
| `P1 Parallel Research` | Gather three independent model-selection views. | P0 draft exists. | Each worker writes one assigned research document. | pass |
| `P2 Synthesis` | Compare research outputs and name candidate model contracts. | P1 documents returned. | Synthesis separates recommended, fallback, and rejected paths. | pass |
| `P3 Decision` | Decide whether to open a follow-on implementation contract. | P2 synthesis accepted by main thread. | Parent model README and A7 residuals are updated without overclaim. | pass; spawned M3-S1 planning |

## Task Clusters

- Task cluster plan:
  [m3_optimal_stopping_model_selection_task_clusters_20260605.md](m3_optimal_stopping_model_selection_task_clusters_20260605.md)
- Dispatch queue:
  [m3_optimal_stopping_model_selection_dispatch_queue_20260605.md](m3_optimal_stopping_model_selection_dispatch_queue_20260605.md)

## Outputs And Evidence

- Formal problem statement:
  [m3_formal_problem_statement_20260605.md](m3_formal_problem_statement_20260605.md)
- Self-designed algorithm packet:
  [m3_self_designed_algorithm_probe_20260605.md](m3_self_designed_algorithm_probe_20260605.md)
- Academic literature packet:
  [m3_academic_literature_model_survey_20260605.md](m3_academic_literature_model_survey_20260605.md)
- Existing model-family packet:
  [m3_existing_model_family_fit_survey_20260605.md](m3_existing_model_family_fit_survey_20260605.md)
- Synthesis:
  [m3_model_selection_synthesis_20260605.md](m3_model_selection_synthesis_20260605.md)
- Follow-on planning contract:
  [M3-S1 Censored Optimal-Stopping Timing Contract](../grouped_stopping_contract_20260605/README.md)

## Acceptance Gate

This subproject can be marked accepted only when:

- the formal mathematical problem is stable enough for future implementation
  agents to reuse without reading this chat;
- each research packet names assumptions, candidate model class, expected
  failure modes, and concrete fit to the current blocked evidence;
- synthesis recommends a bounded next model contract and rejects at least one
  tempting but structurally weak alternative;
- parent model docs are synchronized without claiming learned-policy success.

## Residuals And Next Steps

- M3-S1 is opened as a planning contract; start with architecture boundaries
  and data/censoring before training-loop edits.
- Keep M2 as a candidate model family, not as an assumed cure.
- Keep A7 evidence as the empirical failure case, not as the mathematical
  problem definition itself.

## Archive

No archive records exist yet. Historical research packets may move to
`archive/` only after a synthesis document supersedes them.
