# Model Architecture Standards Overview

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Status: `2026-06-08` authoritative entrypoint for maintained model and policy
architecture standards.

This directory owns repository-wide model-architecture vocabulary for
reinforcement-learning policies, auxiliary heads, rollout labels, losses,
rewards, probes, and runtime action adapters. It is a standards surface, not a
task tracker. Active model tasks under `docs/task/model/` should cite this
directory when they add, split, or reinterpret model components.

## Scope

The model standards layer defines:

- the difference between executable policy components, auxiliary learning heads,
  runtime legality constraints, reward surfaces, and diagnostics;
- the current policy execution graph used by maintained PPO/HMoE training
  entries;
- ownership boundaries for stopping, window-prior, event-action, and credit
  mechanisms;
- the learned-firing evidence boundary for air-combat policies, where legal
  executable release behavior is separated from timing quality and downstream
  weapon effects;
- required documentation when a future task adds a model branch, adapter, loss,
  buffer, or probe.

It does not own:

- air, naval, or ground mission semantics;
- C2/ROE doctrine, tasking authority, or service-profile vocabulary;
- low-level physics, weapon effects, or damage-model parameters;
- the acceptance status of active training experiments.

Those belong to the relevant `joint/`, `services/`, domain-specialization,
`bridge/`, task, or runtime documents.

For active air-combat training, this means "the model learned to fire" is a
model-side behavioral claim about the executable event path producing legal
accepted `fire_once` releases under the existing A3/A5 gates. It is not a
claim about missile probability of kill, effects-chain realism, health deltas,
or damage/kill acceptance.

## Maintained Documents

Read these files in order:

1. [Policy Execution Architecture Baseline](policy_execution_architecture.md)

The first document is intentionally concrete: it maps the current implementation
surfaces and establishes the vocabulary that future M2/M3 work should use before
adding more mechanisms.

## Current Code Alignment

The maintained model standard currently maps to these implementation surfaces:

- feature extractors:
  [python/models/transformer.py](../../../python/models/transformer.py)
- HMoE policy, event distribution, and auxiliary heads:
  [python/rl/policy_algo/policies.py](../../../python/rl/policy_algo/policies.py)
  - includes executable `hybrid_event_head`, auxiliary
    `hybrid_event_credit_head`, `m3_stopping_head`, and
    `m3_window_classifier_head` adapter paths.
- HMoE route selection:
  [python/rl/policy_algo/hmoe_routing.py](../../../python/rl/policy_algo/hmoe_routing.py)
- PPO rollout/update loop and auxiliary-loss integration:
  [python/rl/policy_algo/ppo_adaptive_kl.py](../../../python/rl/policy_algo/ppo_adaptive_kl.py)
  - owns rollout-time label construction, A6/A7 weighting, M3-S2 event-window
    updates, support-preserving collection, replay/calibration population, and
    diagnostics.
- first-event labels and event-credit helpers:
  [python/rl/policy_algo/first_event_hazard.py](../../../python/rl/policy_algo/first_event_hazard.py)
- first-event rollout storage:
  [python/rl/policy_algo/first_event_rollout_buffer.py](../../../python/rl/policy_algo/first_event_rollout_buffer.py)
- grouped stopping objective:
  [python/rl/policy_algo/m3s1_grouped_stopping.py](../../../python/rl/policy_algo/m3s1_grouped_stopping.py)
- air-combat event-action runtime support:
  [gym_envs/universal_env_parts/air_combat_event_action.py](../../../gym_envs/universal_env_parts/air_combat_event_action.py)
  - owns the final A5 runtime gate after policy-visible support has shaped the
    event distribution.

## Standardization Rules

- Name each component by role before naming it by experiment code. For example,
  "window-prior classifier" is a model role; `m3_window_classifier_head` is the
  current implementation name.
- A model branch must declare whether it is executable, auxiliary-only,
  diagnostic-only, or an adapter into an executable action path.
- Runtime masks and state machines define legal support. They do not by
  themselves define the learned stopping objective.
- Rewards can value behavior but must not be the only place where action
  legality, one-shot suppression, or model-branch ownership is defined.
- Any normalization or replay buffer that changes model logits at evaluation time
  is part of the model contract and must be documented with its support
  population.
- Deterministic and stochastic probes are evaluation surfaces. They can validate
  a model contract, but they are not model components.
- Learned-firing evidence must report request, acceptance, rejection, release,
  authority, repeat-suppression, and timing fields before it can be compared to
  timing-quality or downstream-effects evidence.

## Relationship To Task Work

`docs/task/model/` owns active experiments, dispatch plans, held/pass status, and
evidence packets. This directory owns the durable vocabulary those tasks must use
when they discuss model structure.

If a task needs a new model mechanism, the task should either cite an existing
standard here or explicitly request a standards update before treating the new
mechanism as part of the maintained architecture.
