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
- Learnability audit: on `2026-06-05`, M3-S2 found that legal release and
  terminal wins are reachable in the oracle surface, but reward ordering favors
  late close-range wins and the current labels-to-credit-to-policy contract
  does not train a calibrated signed event-logit discriminator. The follow-up
  M3-S2 direct event-window probe reached the executable event logits but still
  held with deterministic `0` releases. The sharper 2026-06-06 diagnosis is
  cumulative prewindow hazard: `p ~= 0.0055` over `800` prewindow steps implies
  `0.988` early-sample risk, so the sampled policy can erase its own
  quality-window supervision. The support-preserving collection repair keeps
  M3-S2 active groups alive through the 8k run, but deterministic probing still
  records `0` releases. A structural toy probe then cleared the pure grouped
  M3-S2 loss object: both free logits and a small MLP learn the `800 + 1080`
  one-shot window boundary. The real update path probe then showed the current
  Stage-1 M3-S2 auxiliary update lowers both prewindow and quality logits,
  reducing loss through global hazard suppression instead of boundary
  formation. A log-domain cumulative-hazard repair restores long-prewindow
  survival gradients and drops M3 stop probability from about `0.47` to `0.145`
  in 8k short training, but deterministic release remains `0` and stochastic
  still samples early. Further work should prototype a scale-separated real-row
  discriminator, repair the event-to-pulse adapter, signed event-logit actor
  targets, or reward contract before treating M2 memory as the primary fix.
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
- Chinese companion:
  [Temporal HMoE Policy Plan.zh](temporal_hmoe_policy_plan_20260525.zh.md)
