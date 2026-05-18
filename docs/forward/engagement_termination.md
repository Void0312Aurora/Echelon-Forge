# Engagement Termination and Behavior Logic Roadmap

This document records the planning direction for engagement termination
conditions and behavior logic so we avoid prolonged mirror chases or pointless
maneuvering.

## Already Implemented (Runtime / Scenario Layer)
- Disengagement by distance threshold: `disengage_range_m` +
  `disengage_hold_s`.
- Disengagement by low energy: `min_specific_energy_j_kg` + `energy_hold_s`.
- Termination on ammunition depletion: `ammo_depletion_ends` plus in-flight
  missile checks.
- Main implementation locations: `src/core/mission/termination_runtime.*`,
  `gym_envs/scenario_loader.py`.

## Recommended Termination Conditions
1) Disengagement range
- If separation exceeds the threshold for a sustained period, terminate or
  switch to return-to-base behavior.

2) Ammunition depletion
- If both sides are out of ammunition and no missiles remain in flight,
  terminate.
- If only one side is depleted, it can switch to a defensive or retreat
  policy.

3) Low energy
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
- Move termination conditions into core systems (C++) to ensure consistency.
- Support per-side and per-entity termination rules in scenarios.
- Log the termination reason and trigger time to make replay analysis easier.
