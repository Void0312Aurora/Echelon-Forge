# Exact kill-chain guidance mechanism ablation conclusions — 2026-07-15

## Summary

This pass does not retune `N`, the lateral-acceleration limit, or APN gain. It
freezes `N=4`, `35 g`, and `APN gain=0.5`, then applies exact discrete controls
to capture, PN, velocity lead, acceleration lead, target-kinematics source, and
APN. The matrix contains `20` mirrored constant-velocity cases and `16`
mechanism profiles, for `320` deterministic runs. A second-seed audit of `16`
key runs reproduced every nearest distance exactly.

The main conclusion is that the current `45 deg -> M` boundary is not purely a
parameter-calibration result. It also contains legacy PN frame coupling, target
kinematics estimation error, and implicit launch-window shaping by capture.
World-frame PN is a substantive mechanism-fix candidate, but it cannot be made
the production default while retaining the old N/M/O labels unchanged: it
improves `45 deg` while moving the `16 km / 30 deg` O control inside the fuze
radius. Because that control was itself derived under the legacy mechanism,
the breach alone does not prove world-frame PN is unreasonable. The sound
sequence is to correct the mechanism and then recalibrate window shaping and
classification, rather than using legacy PN attenuation as an implicit gate.

## Evidence and boundary

Retained artifacts are:

- [JSON report](kill_chain_guidance_exact_mechanism_ablation_20260715.json)
- [run rows](kill_chain_guidance_exact_mechanism_ablation_20260715_rows.csv)
- [mirrored pair means](kill_chain_guidance_exact_mechanism_ablation_20260715_pairs.csv)
- [matched conditional effects](kill_chain_guidance_exact_mechanism_ablation_20260715_effects.csv)
- [generated summary](kill_chain_guidance_exact_mechanism_ablation_20260715_summary.md)

The profile is attached only to an individual missile after launch and before
its first guidance update. Normal missiles do not carry the component; the
weapon database, release service, and production defaults are unchanged. Lead
retains its current semantics: it changes the capture aimpoint and is not an
independent acceleration command.

## Implementation and measurement acceptance

| Check | Result |
| --- | ---: |
| Unprofiled baseline vs all-enabled legacy profile maximum nearest-distance difference | `0.0 m` |
| Maximum mirrored difference in the full matrix | `0.00005075 m` |
| Maximum disabled capture / PN / APN component | `0.0 g` |
| Maximum `preclamp = capture + PN + APN` vector closure error | `4.55e-12 m/s^2` |
| Maximum post-clamp total command | `35.00000000000001 g` |
| Truth-CV velocity/quadratic-lead difference | `0.0 m` |
| Truth-CV APN off/on difference | `0.0 m` |
| Lead off/on difference with capture disabled | `0.0 m` |

These invariants show that this pass measures discrete mechanism differences,
not the approximate epsilon-gain gates used in the first ablation.

## Current baseline

| Cell | `4 km` | `6 km` | `8 km` |
| --- | ---: | ---: | ---: |
| `30 deg` nearest distance | `9.461 m` | `10.267 m` | `10.963 m` |
| `45 deg` nearest distance | `22.438 m` | `22.101 m` | `24.448 m` |

The `12 km / 45 deg` result is `48.462 m`, and `16 km / 30 deg` is
`17.010 m`. The baseline therefore keeps every N30 positive inside
`R_fuze=15 m` and both O controls outside.

## Mechanism attribution

### 1. Lead is owned by the capture-lead composite path

Removing lead from the current chain worsens N30 by `39.955..47.998 m` and
M45 by `77.932..93.167 m`. Lead remains the dominant necessary mechanism, but
the exact invariant is decisive: with capture disabled, lead off/on changes
every case by `0.0 m`. Lead is therefore not an independent control force; it
acts only through the capture aimpoint.

Capture itself is not monotonically beneficial:

- removing it improves N30 by `9.058..10.959 m`;
- it worsens M45 by `5.786..83.495 m`;
- at `16 km / 30 deg`, removing capture moves the nearest distance from
  `17.010 m` to `0.024 m`.

Capture therefore owns both terminal convergence and part of the launch-window
shaping. Part of the current O boundary comes from nonlinear capture/PN
interaction rather than pure kinematic infeasibility.

### 2. PN is necessary, but the legacy frame attenuates it under attitude-velocity separation

Removing PN worsens N30 by `5.718..9.753 m` and M45 by
`6.110..32.644 m`; PN cannot be deleted.

Replacing only the legacy `body angle-rate + Transform` PN with world-frame
LOS-history PN, while retaining the same filtered LOS and closing speed, gives:

| Cell | Legacy PN | World LOS-history PN | Improvement |
| --- | ---: | ---: | ---: |
| `4 km / 45 deg` | `22.438 m` | `16.736 m` | `5.702 m` |
| `6 km / 45 deg` | `22.101 m` | `16.472 m` | `5.629 m` |
| `8 km / 45 deg` | `24.448 m` | `17.034 m` | `7.414 m` |
| `12 km / 45 deg` | `48.462 m` | `21.752 m` | `26.710 m` |
| `16 km / 30 deg` | `17.010 m` | `12.030 m` | `4.980 m` |

This confirms that the previously observed Transform-heading versus velocity-
heading separation is a mechanism issue: it weakens the effective PN command
through projection. World PN materially improves M45, but also moves O-far
inside `R_fuze`; it is not a local 45-degree-only patch.

### 3. Track kinematics account for residual error, but truth-CV is an oracle

Under analytic world PN, replacing track kinematics with truth-CV gives:

| Cell | Track analytic | Truth-CV analytic | Improvement |
| --- | ---: | ---: | ---: |
| `4 km / 45 deg` | `18.760 m` | `15.639 m` | `3.121 m` |
| `6 km / 45 deg` | `18.678 m` | `14.708 m` | `3.970 m` |
| `8 km / 45 deg` | `19.257 m` | `14.843 m` | `4.414 m` |
| `12 km / 45 deg` | `27.819 m` | `16.528 m` | `11.291 m` |
| `16 km / 30 deg` | `13.883 m` | `9.503 m` | `4.380 m` |

The track velocity chain therefore explains about `3.1..4.4 m` of the core
M45 residual. Truth-CV moves the `6/8 km / 45 deg` cells inside `15 m`, but it
also broadens the old window further and is not a production input.

Using current track velocity for analytic PN is not better than LOS-history PN;
it is about `1.040 m` worse on average in M45. A formula-only analytic-PN edit
is therefore insufficient without first fixing track-velocity quality and the
coordinate contract.

### 4. Acceleration lead and direct APN are not the primary 45-degree owners

- Quadratic versus velocity-only lead improves legacy M45 by only
  `1.395..1.699 m`; the world-frame versions improve by about `1.0..1.2 m`.
- Direct APN improves core M45 by only `0.012..1.531 m` and N30 by
  `0.192..0.294 m`.
- With truth-CV acceleration fixed at zero, quadratic/velocity lead and APN
  off/on are exactly identical case by case.

The 45-degree residual should not be attributed to insufficient APN gain or an
underpowered quadratic-lead term.

## Calibration verdict

1. **The current `45 deg -> M` boundary is reproducible as a description of the
   existing runtime.** The exact all-enabled profile is identical to the
   unprofiled baseline and reproduces the N30/O controls.
2. **It is not mechanism closure.** The window incorporates legacy PN-frame
   attenuation, track-estimation error, and capture window shaping; it is not
   only the result of `N=4` and `35 g`.
3. **World-frame PN is the cleaner coordinate mechanism, but the old labels
   cannot be its acceptance oracle.** If a mechanism correction changes the
   reachable set, the N/M/O envelope must be regenerated.
4. **Production defaults remain unchanged for now.** Retaining the legacy
   runtime until capture shaping and the envelope are recalibrated is a
   compatibility decision, not physical endorsement of the legacy mechanism.

## Next work

1. Implement world LOS-history PN as a production candidate and add a coordinate
   invariant: changing Transform heading while holding world position and
   velocity fixed must not change PN output.
2. Run the next exact ablation on capture terminal weighting, range scaling, and
   lead blend; capture is now the main owner of N/M/O window shaping.
3. Add track-versus-truth position, velocity, and LOS-rate error time series to
   identify why current analytic PN is worse than LOS-history PN.
4. Regenerate the `4..16 km x 0..90 deg` envelope on the corrected PN/capture
   combination before deciding the `45 deg` and `16 km / 30 deg` classes. Do
   not constrain the corrected mechanism with labels derived from the legacy
   mechanism.

## Authority boundary

This conclusion diagnoses the current engineering runtime only. It grants no
real AIM-120 guidance-law, launch-envelope, Pk, deterministic-fuze, or stock
weapon/target lethality authority.
