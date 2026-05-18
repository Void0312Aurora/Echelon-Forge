<!-- Machine-translated draft generated on 2026-05-18 from docs/task/naval/naval_realism_layering_and_next_step_plan_20260516.zh.md. Review before treating this file as authoritative. -->

# Naval Realism Layered Checklist and Next Steps Plan for Current Scenario

Status: `2026-05-16` Frozen Analysis Version.

Related files:

- [DDG-51 Screen T-AKE Minimum Scenario](../../../scenarios/naval/ddg51_take1_screen_contact_report_v1.json)
- [Ship Public Parameter Source Description](../../standards/naval/ship_unit_references.md)
- [Naval Mission Minimum Structure Description](../../standards/naval/minimal_task_structure.md)
- [Naval Runtime Test](../../../tests/runtime/naval/test_naval_screen_scenario.py)
- [Naval Geometry Contracts](../../../tests/contracts/unit/naval/naval_screen_contact_report_geometry.json)

Document positioning:

- This document is used to freeze the realism boundary of the current minimal naval example.
- This document first answers "what is already real and what are honest simplifications," then freezes "the next step plan for the current scenario."
- This document currently does not authorize further expansion into weapons, damage, complete escort control, enemy real formation, or larger-scale naval combat.

## 1. Current Scenario Conclusion

The current naval mainline is not a "real engagement scenario" but an already executable and verifiable "minimal realistic maritime screen contact scenario."

The core semantics of the current scenario are:

1. Blue main combatant `DDG-51` as the screening ship.
2. Blue `T-AKE-1` as the protected high-value auxiliary ship.
3. Red side as a hostile surface contact target.
4. The current main verification is the "detection - sharing - reporting" chain, not weapon engagement.

The value of this line is that it has already established a minimal but not fictitious maritime tactical example starting from real ship types, real public parameters, and reasonable contact geometry.

## 2. Realism Layered Checklist

### 2.1 Trusted Realism Baseline

The following parts can be regarded as the "trusted realism baseline" in the current mainline:

1. **Ship type selection is real**
   - Blue screening ship uses `USS Arleigh Burke (DDG-51)`.
   - Blue protected ship uses `USNS Lewis and Clark (T-AKE-1)`.
   - Both come from real, publicly traceable ship types and platform data.

2. **Public parameters have been stored**
   - Length, beam, draft, displacement, maximum speed, economic speed, range, crew complement, etc. have been entered into `ShipPlatform`.
   - Parameter conversion and sources have been explained in [ship_unit_references.md](../../standards/naval/ship_unit_references.md).

3. **Mission relationship is real and restrained**
   - The current approach is not to invent a "maritime dogfight" but to start from the realistic and semantically clear escort relationship of "destroyer screening a supply ship."
   - The minimum naval mission mapping for `TASK_SCREEN` / `TASK_SUPPORT` has been established.

4. **Contact geometry is reasonable**
   - `DDG-51` is positioned about `8 nmi` ahead of `T-AKE-1`.
   - The red contact is located where `DDG` can detect it first, but the `HVU`’s local radar cannot initially detect it.
   - This makes the outcome "screening ship detects enemy first, HVU learns about contact through shared situational awareness" a natural result, not a hard-coded test.

5. **Sensor ranges use conservative real-world constraints**
   - The current detection ranges for `AN/SPS-67(V)` and the auxiliary ship’s navigation radar are not arbitrarily high values but are based on a conservative upper limit using radar horizon/line-of-sight approximations.
   - This is more credible than writing a large default detection range for a surface radar without source.

6. **Shared situational awareness link is established**
   - The current runtime can already verify: `DDG` own-ship detection -> `HVU` shared track -> `HVU` contact report.
   - Both runtime tests and contract tests have passed.

### 2.2 Acceptable Honest Simplifications

The following parts are not yet high-fidelity, but they are acceptable honest simplifications at this stage:

1. **Ship motion is planar kinematics**
   - Current ships move translationally on the water surface, obey speed limits, and automatically update course.
   - There are no considerations of sea state, inertial turns, acceleration/deceleration response, or propulsion system time lags.
   - This is sufficient to support the "minimum contact scenario" but not to support real ship maneuvering combat.

2. **Radar detection is a simplified probabilistic model**
   - Current detection accounts for factors such as range, field of view, noise, and scan period.
   - However, more complete real-world factors such as ship-level RCS, sea clutter, sea state, mode switching, and identification chains have not been established.

3. **Data link is a minimal sharing model**
   - Current sharing mechanisms consider same side, same network, distance, and LOS constraints.
   - However, network organization is a side-level approximation, not a realistic fleet C2 / Link management model.

4. **Hitboxes and system compartments are structural placeholders**
   - Current ships have partitioned hitboxes and system lists.
   - This leaves room for future survivability/damage refinement, but at this stage it cannot represent real ship survivability.

### 2.3 Known Distortion Points

The following are the distortion points that should be most clearly labeled in the current scenario:

1. **Red ship type has not been realistically selected**
   - The current red side is a hostile contact in semantics, but the runtime still reuses `T-AKE-1` hull configuration as a placeholder.
   - This means the red side is currently not a real enemy ship model.

2. **Ship health model has no real explanatory power**
   - `health` is currently approximated as "about 1 HP per ton."
   - This only avoids a completely blank value and cannot explain real survivability, damage propagation, mission incapacitation, or sinking process.

3. **Weapon systems have not entered a credible stage**
   - `VLS`, naval guns, `CIWS`, anti-ship missiles, and air defense missiles have not yet entered the runtime combat chain in a credible manner.
   - Equipment recorded in current metadata should not be misinterpreted as "already implemented."

4. **Data link configuration is inconsistent with real formation**
   - The current factory automatically assigns data link network numbers by side.
   - This is suitable for minimal shared situational awareness, but it is not equivalent to real formation, frequency bands, node roles, or link reliability modeling.

5. **Mission semantics precede escort control**
   - The `TASK_SCREEN` semantics exist, but a mature dynamic screen-keeping control logic is not yet available.
   - In other words, it is more like a "geometric example with an escort relationship attached" rather than a "real, operable escort tactical controller."

### 2.4 Parts That Should Not Be Mistakenly Called "Real Naval Combat"

To avoid semantic drift later, the following statements should be clearly avoided in the current context:

1. Do not refer to the current scenario as a "real naval engagement scenario."
2. Do not refer to the red placeholder hull as a "completed enemy ship model."
3. Do not refer to the current `health`, generic damage, or metadata weapon records as "ship-level damage/weapon simulation."
4. Do not directly state the current data link sharing as "the real fleet tactical data link system has been completed."

A more accurate description should be:

- **Minimum realistic maritime screen contact scenario**
- **Baseline for escort/detection/shared situational awareness**
- **A naval starting example before entering weapon and damage modeling**

## 3. Next Step Plan for the Current Scenario

### 3.1 General Principle

At the current stage, we will not continue expanding implementation but instead freeze the direction of convergence.

The goal of the next step should NOT be:

1. Directly entering ship weapon engagement.
2. Directly building a complete escort controller.
3. Directly introducing a real red formation, electronic warfare, damage, or multi-ship coordination.

The next step should stay within the range of "a natural small extension of the current scenario."

### 3.2 Suggested Next Step

The suggested next step is frozen as:

**On the existing `DDG-51` screen `T-AKE-1` scenario, create a variant with "red contact approach / closest point of approach" and add a corresponding contract.**

Rationale:

1. This step still stays at the "contact management" and "screen geometry" level, without falsely jumping into not-yet-credible weapon operations.
2. It can directly test whether the current minimum scenario is only a "static snapshot" or can already sustain basic maritime situation evolution.
3. It provides a clear judgment basis for whether dynamic screen-keeping control is needed later.
4. It does not require solving larger problems like real red ship selection, weapon chain, or damage chain at this point.

### 3.3 Frozen Work Packages for the Next Step

The next step only freezes two very narrow work packages:

1. **WP-N1: Approach scenario variant**
   - Based on the existing scenario, let the red side (as a hostile surface contact) approach the blue support ship.
   - Keep the real baseline of blue `DDG` and `HVU` unchanged.
   - Do not introduce weapon and engagement logic yet.

2. **WP-N2: Closest point of approach contract**
   - Add a focused contract for this scenario.
   - Core check items:
     - `DDG` should still obtain its own-ship contact first.
     - `HVU` should learn about the contact through shared situational awareness.
     - The closest point of approach between `HVU` and the red side should meet a preset threshold.
     - If there is currently no dynamic control, the contract should honestly reflect that "the current situation is just initial geometry persistence, not active escort maneuvering."

### 3.4 Items Explicitly Deferred for Now

In the next step plan, the following items are explicitly deferred:

1. Real red ship type library expansion
2. Ship weapons, VLS, naval guns, `CIWS` launch chains
3. Ship damage, incapacitation, sinking, and mission failure chains
4. Dynamic screen-keeping controller
5. Multi-ship formation escort or more complex naval tactics

The reason is not that these are unimportant, but that the current priority is to first confirm:

**Whether the existing minimum scenario can stably support the "contact approach + geometry constraint + shared situational awareness" layer.**

## 4. Execution Command

If this line is reopened later, it is recommended that the default verification command includes at least:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/naval/test_naval_ship_database.py tests/runtime/naval/test_naval_screen_scenario.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_contact_report_geometry.json
```

If the next step enters the "approach scenario variant," then corresponding runtime tests or contract tests should be added on top, not replace the current minimum baseline.

## 5. Current Freeze Conclusion

The correct positioning of the current naval mainline is:

1. It is no longer an empty shell, but a verifiable minimum realistic maritime screen example.
2. It has established real ship types, reasonable contact geometry, and a shared situational awareness chain.
3. It has not yet entered a credible maritime weapon engagement layer.
4. Its next step should not jump into full naval combat, but first perform convergence verification of "approach contact / closest point of approach."

This conclusion is frozen until the next explicit restart of naval advancement.
