# M2 Causal-Transformer HMoE Proposal

Language: English canonical; [Chinese companion and detailed proposal](README.zh.md).

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/learning/work/issues/causal_transformer_hmoe/README.md`
Owner: `learning/policy-architecture`
Last verified: `not established`
Content status: held proposal; implementation is not authorized.

## Problem And Evidence

The maintained PPO/HMoE path does not preserve sequence semantics through
random per-step minibatches. A sequence-native buffer, causal extractor,
temporal HMoE policy, and masked PPO loss may address that gap, but the current
M1 temporal-window evidence has not justified the implementation cost.

## Proposed Direction

Retain the candidate architecture described in the
[detailed proposal](README.zh.md), with causal masking, contiguous rollout
sampling, explicit reset masks, and comparable Stage-0/Stage-1 probes.

## Promotion Gate

M1 must first demonstrate a useful temporal-history effect under comparable
scenarios, seeds, action interfaces, and C2/ROE constraints. A separate owner
decision must then open an active work package.

## Non-goals

This issue does not authorize runtime, physics, reward, self-play, or `2v2`
changes and does not make M2 the maintained policy architecture.
