# Model Tasks

Status: active planning line for temporal policy work. On `2026-05-25`, the
line selected "Path A first, Path C after evidence" as the maintained direction.

This area tracks model-side changes that cut across domains. The current
maintained task slice is temporal policy work, not a general replacement for
learning-model issue plans under `docs/learning/work/issues/` or the
`python/world_model/` implementation surface. The immediate driver is the
`1v1` air-combat weapon-employment line:
repeated missile launch behavior should be solved by policy temporal context
and observable physical state, not by growing tactical memory boards inside
simulation systems.

Current route:

- Standards baseline: model-architecture vocabulary and implementation ownership
  live under [Model Architecture Standards](../../../../learning/README.md);
  active tasks should cite that layer before adding or reinterpreting model
  branches, adapters, losses, buffers, or probes.
- Target architecture: Path C, sequence-native causal Transformer HMoE/PPO.
- First validation package: Path A, observation-window temporal HMoE.
- Action interface: on `2026-06-02`, the M1 air-combat action-interface split
  accepted the `air_combat_hybrid_v1` training surface; this releases only the
  action interface, not learned-policy acceptance or M2.
- Model-selection pause: on `2026-06-05`, A7 first-event timing evidence was
  re-scoped into M3 as a domain-neutral one-shot timing / optimal-stopping
  model-selection problem; M3-S1 is now the planning contract for architecture
  separation, data/censoring, and grouped stopping objectives before code opens.
- Learnability audit: M3-S2 is now a sealed evidence package. It found that
  legal release and terminal wins are reachable in the oracle surface, localized
  several event-timing and calibration breakpoints, and finally closed the
  bounded learned-policy firing gate on `2026-06-08` after the A5 weapon-arm
  action-frame fix. The accepted claim is deliberately narrow: the active model
  can request and execute one authorized release without rejected requests,
  violations, or repeat-before-assessment releases for the active Stage-1 C2/ROE
  scenario/config pair. Timing quality, cross-config robustness, effects
  quality, damage, and kill-chain behavior remain held and should reopen only as
  follow-on work.
- Release rule: Path C implementation starts only after Path A shows useful
  improvement on stage-0 / stage-1 air-combat curricula.
- Path B recurrent HMoE remains a comparison/fallback, not the mainline.

Start here:

- [Temporal HMoE Policy Plan](../../../../learning/work/issues/temporal_policy_roadmap.md)
- [M1 Temporal Window HMoE](../../../../learning/work/active/temporal_window_hmoe/README.zh.md)
- [M1 Air-Combat Action Interface Split](../../../../learning/reviews/air_combat_action_interface_split_20260602/README.md)
- [M2 Causal Transformer HMoE](../../../../learning/work/issues/causal_transformer_hmoe/README.zh.md)
- [M3 Optimal-Stopping Model Selection](../../../../learning/reviews/optimal_stopping_model_selection_20260605/README.md)
- [M3-S1 Censored Optimal-Stopping Timing Contract](../../../../learning/reviews/grouped_stopping_contract_20260605/README.md)
- [M3-S2 Fire-Timing Learnability Audit](../m3_s2_fire_timing_learnability_audit/README.md)
  archived pointer; full package:
  [archive/m3_s2_fire_timing_learnability_audit](../m3_s2_fire_timing_learnability_audit/README.md)
- Chinese companion:
  [Temporal HMoE Policy Plan.zh](../../../../learning/work/issues/temporal_policy_roadmap.zh.md)
