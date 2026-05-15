# Shared Execution Model: Conditional Routing Note

## Background

The current execution-layer policy is a single shared model that is expected to
cover multiple functional regimes:

- takeoff and ground-run behavior
- initial climb and departure
- cruise and route keeping
- cooperative formation behavior
- later recovery / landing related behavior

This unified-pipeline design has clear engineering advantages, but it also
creates a modeling tension: at inference time, a given aircraft in a given phase
only needs part of the model capacity, while the current policy activates the
same end-to-end parameter path for every regime.

## Problem Statement

The core concern is not merely model size. The deeper issue is likely negative
transfer across heterogeneous behaviors:

- different flight phases prefer different action priors
- different roles may require different decision subspaces
- a single dense policy head may entangle incompatible control tendencies

In other words, the current shared execution model may be "too unified" at the
decision head even if a shared observation backbone is still desirable.

## Initial Judgment

### Dropout is not the main answer

Dropout may help regularization, but it does not directly solve the actual
problem here:

- it does not provide explicit conditional computation
- inference usually disables dropout
- in RL control, extra stochastic masking can also destabilize value / policy
  learning

Therefore dropout may remain a secondary regularization tool, but it should not
be treated as the primary architectural response to multi-function execution.

### MoE is directionally relevant, but full MoE is probably premature

Mixture-of-Experts is closer to the real need because it enables conditional
activation. However, a full sparse-MoE conversion would introduce additional
risks:

- router learning instability under PPO
- expert collapse / routing imbalance
- more fragmented batches and worse systems efficiency
- harder debugging while the current training line is still being stabilized

For the current project stage, a lighter conditional-routing design is more
appropriate than immediately adopting a fully sparse MoE trunk.

## Preferred Near-Term Direction

Keep a unified execution pipeline, but introduce conditional specialization near
the policy head.

Recommended structure:

1. shared observation encoder
2. shared latent backbone
3. conditionally selected actor/value heads or small expert heads

This yields a middle ground:

- preserve a unified observation and training pipeline
- reduce interference between incompatible behaviors
- avoid prematurely fragmenting the full execution stack into separate models

## Routing Signals

Routing should not depend on artificial training-only hints. It should be based
on information that is operationally meaningful and already justified by the
simulation/task structure.

Priority candidates:

- aircraft role identity (for example lead / wingman / other slot identity)
- current command or task family
- current flight phase
- clearance / authorization state when relevant
- cooperative task mode when relevant

The principle is that the route-selection signal must remain compatible with the
project's realism requirement, rather than being introduced only for training
convenience.

## Suggested Incremental Path

### Stage 1

Implement a shared-backbone, multi-head execution policy:

- shared feature extractor
- shared intermediate latent
- separate actor/value heads for a small number of behavior families

Routing can initially be explicit and rule-based from existing mission/phase
signals.

### Stage 2

If Stage 1 reduces interference, expand to a small mixture-of-heads design:

- 2 to 4 lightweight experts
- a small router over experts
- keep the encoder dense and shared

This is easier to stabilize than a full sparse-MoE backbone.

### Stage 3

Only after the above is stable should the project evaluate:

- deeper expert specialization
- sparse expert activation inside the trunk
- load-balancing losses or other MoE-specific mechanisms

## Why This Matters

This line of work is not just a model-architecture experiment. It may become a
key mechanism for scaling the execution layer from single-task control toward a
broader, still-unified, multi-role execution policy without forcing every
regime to fight for the exact same dense decision head.

## Status

This is a forward note only. No implementation commitment is implied yet.

