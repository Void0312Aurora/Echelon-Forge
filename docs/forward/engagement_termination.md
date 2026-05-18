# Engagement Termination and Behavior Logic Roadmap

This document records the planning direction for engagement termination
conditions and behavior logic so we avoid prolonged mirror chases or pointless
maneuvering.

## Current Runtime Coverage
- Core safety and fail-fast termination currently lives in
  `src/core/mission/runtime/termination_runtime.*`.
- The runtime currently covers:
  - invalid finite-state / NaN guard termination
  - health-based crash termination
  - deep-stall, inverted-low-altitude, and extreme-pitch fail-fast cases
  - gear-collapse and off-runway termination logic
  - final `success` / `failure` / `timeout` reason normalization
- Scenario loading and mission-command normalization now live in the
  `gym_envs/scenario_loader/` package, primarily `core.py` and `loading.py`.

## Recommended Engagement-Level Termination Extensions
The items below are planning targets, not shipped runtime knobs today.

1) Disengagement range
- Add scenario-facing thresholds such as `disengage_range_m` +
  `disengage_hold_s`.
- If separation exceeds the threshold for a sustained period, terminate or
  switch to return-to-base behavior.

2) Ammunition depletion
- Add a rule such as `ammo_depletion_ends`, optionally gated on "no missiles
  remain in flight".
- If both sides are out of ammunition and no missiles remain in flight,
  terminate.
- If only one side is depleted, it can switch to a defensive or retreat
  policy.

3) Low energy
- Add scenario-facing thresholds such as `min_specific_energy_j_kg` +
  `energy_hold_s`.
- Evaluate with specific energy (J/kg) or a speed threshold.
- Track the condition duration to avoid triggering on momentary noise.

4) Loss of awareness
- If the target is lost for an extended period (no detection / no track),
  trigger disengagement.

5) Mission objective complete
- Terminate when kill, hit, or mission-kill objectives have been achieved.

## Recommended Behavior Logic
- "Engaged" and "disengaged" should be two explicit states with clear
  transition conditions.
- After disengaging, possible behaviors include:
  - escape on a fixed heading
  - energy recovery (build speed / altitude)
  - return-to-base or loiter

## Further Implementation Suggestions
- Keep engagement-level termination separate from the existing safety runtime
  so each rule set remains easy to reason about.
- Support per-side and per-entity termination rules in scenarios.
- Log the termination reason and trigger time to make replay analysis easier.
