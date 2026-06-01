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

- Target architecture: Path C, sequence-native causal Transformer HMoE/PPO.
- First validation package: Path A, observation-window temporal HMoE.
- Release rule: Path C implementation starts only after Path A shows useful
  improvement on stage-0 / stage-1 air-combat curricula.
- Path B recurrent HMoE remains a comparison/fallback, not the mainline.

Start here:

- [Temporal HMoE Policy Plan](temporal_hmoe_policy_plan_20260525.md)
- [M1 Temporal Window HMoE](m1_temporal_window_hmoe/README.zh.md)
- [M2 Causal Transformer HMoE](m2_causal_transformer_hmoe/README.zh.md)
- Chinese companion:
  [Temporal HMoE Policy Plan.zh](temporal_hmoe_policy_plan_20260525.zh.md)
