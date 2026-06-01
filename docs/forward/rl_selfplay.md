# Reinforcement Learning and Self-Play Roadmap

This document defines the design path for reinforcement learning and self-play
so the training loop remains controllable and reproducible.

## Minimal Training Loop (Implemented)
- Single-step observation -> action -> environment update -> reward ->
  termination.
- Action space: rate-based commands (turn, accelerate, climb, fire).
- Opponent policy: self-play (symmetric policy), or scripted chase / random.

## Observation Design Suggestions
- Relative position / velocity, relative bearing, and distance.
- Own speed / altitude / heading, target speed / altitude.
- Sensor information: detected / locked state and most recent detection range.

## Reward Design Suggestions
- Primary: reward for kills, penalty for being killed.
- Shaping: close distance, maintain detection, hold advantageous aspect.
- Constraints: penalize excessive maneuvering and low-energy states.

## Recommended Termination Conditions
- Kill / mission kill.
- Disengagement range remains above threshold for a sustained period.
- Ammunition depleted and no missiles remain in flight.
- Low energy remains below threshold for a sustained period.

## Self-Play Strategy
- Synchronous updates: both sides use the same training algorithm.
- Historical policy pool: sample older policies at random to avoid
  overfitting.
- Elo / win-rate evaluation: track policy evolution over time.

## Infrastructure Suggestions
- Unified logging: record state, action, and reward.
- Reproducibility: fix random seeds and record configurations.
- Training metrics: win rate, average engagement length, hit rate.

## Next Steps
- Introduce a policy pool and evaluation loop.
- Make reward and termination conditions configurable by scenario.
- Integrate deep networks (PyTorch) and GPU execution.

## Current Repository State
- This is still a forward-looking roadmap, not the maintained self-play entry
  point.
- There is no `examples/training/train_self_play.py` or
  `examples/training/selfplay_config.json` in the current repository.
- Maintained training entry points and configs live under `train.py`,
  `python/training/`, and `examples/config/training/`.
- Air-combat training configs and scripted-opponent fixtures exist, but a
  standalone historical policy pool and self-play evaluation loop still need to
  be promoted through `plan/` or `task/` before this document can claim them as
  implemented.
