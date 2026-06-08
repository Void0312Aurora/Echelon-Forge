# Model Tasks

Status: active planning line for temporal policy work. On `2026-05-25`, the
line selected "Path A first, Path C after evidence" as the maintained direction.

This area tracks model-side changes that cut across domains. The current
maintained task slice is temporal policy work, not a general replacement for
the `forward/models/` idea backlog or the `python/world_model/` implementation
surface. The immediate driver is the `1v1` air-combat weapon-employment line:
repeated missile launch behavior should be solved by policy temporal context
and observable physical state, not by growing tactical memory boards inside
simulation systems.

Current route:

- Standards baseline: model-architecture vocabulary and implementation ownership
  live under [Model Architecture Standards](../../standards/model/README.md);
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

- [Temporal HMoE Policy Plan](temporal_hmoe_policy_plan_20260525.md)
- [M1 Temporal Window HMoE](m1_temporal_window_hmoe/README.zh.md)
- [M1 Air-Combat Action Interface Split](m1_action_interface_split/README.md)
- [M2 Causal Transformer HMoE](m2_causal_transformer_hmoe/README.zh.md)
- [M3 Optimal-Stopping Model Selection](m3_optimal_stopping_model_selection/README.md)
- [M3-S1 Censored Optimal-Stopping Timing Contract](m3_s1_censored_optimal_stopping_timing_contract/README.md)
- [M3-S2 Fire-Timing Learnability Audit](m3_s2_fire_timing_learnability_audit/README.md)
  archived pointer; full package:
  [archive/m3_s2_fire_timing_learnability_audit](archive/m3_s2_fire_timing_learnability_audit/README.md)
- Chinese companion:
  [Temporal HMoE Policy Plan.zh](temporal_hmoe_policy_plan_20260525.zh.md)
