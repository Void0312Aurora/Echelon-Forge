# Kill-chain guidance mechanism ablation conclusions — 2026-07-15

## Scope

This packet diagnoses the current engineering runtime. It does not tune a
real-weapon model and does not grant AIM-120C, F-16C, fuze, lethality, or Pk
authority. The baseline remains fixed at the repository AIM-120-like proxy,
including `N=4`, `35 g`, and `APN=0.5`.

The experiment ran `200` deterministic simulations: `20` mirrored
constant-velocity cases by `10` guidance-mechanism variants. Epsilon gains are
used only as mechanism gates; they are not optimized parameter candidates.
Retained artifacts are the [JSON report](kill_chain_guidance_mechanism_ablation_20260715.json),
[run rows](kill_chain_guidance_mechanism_ablation_20260715_rows.csv),
[conditional effects](kill_chain_guidance_mechanism_ablation_20260715_effects.csv),
and [generated summary](kill_chain_guidance_mechanism_ablation_20260715_summary.md).
The run used `/home/void0312/Workshop/CMO/build/ef_py.cpython-313-x86_64-linux-gnu.so`.
The current worktree also contains a pre-existing uncommitted guidance-cadence /
held-command refactor; these cases set `guidance_update_period_s=0`, so the
cadence branch is not the tested mechanism, but the build context must remain
visible when reproducing the numbers.

## Main results

| Current full chain | 4 km | 6 km | 8 km |
|---|---:|---:|---:|
| `30 deg` nearest distance | `9.461 m` | `10.267 m` | `10.963 m` |
| `45 deg` nearest distance | `22.438 m` | `22.101 m` | `24.448 m` |

All mirrored `30 deg` cells enter `R_fuze=15 m`; all mirrored `45 deg` cells
remain outside it. Left/right symmetry is stable: the maximum paired nearest
distance difference over all `100` pairs is below `0.000051 m`.

The nested ablation identifies the following conditional effects over the
`4/6/8 km` core cells:

- Lead is the dominant necessary mechanism. Adding lead to `capture + PN`
  reduces nearest distance by `40.8..49.0 m` at `30 deg` and
  `78.4..96.4 m` at `45 deg`.
- PN is also necessary. Adding PN with lead present reduces nearest distance by
  `5.8..10.3 m` at `30 deg` and `6.0..45.2 m` at `45 deg`.
- The direct APN acceleration term is not the close-range residual owner.
  Adding APN to `capture + PN + lead` changes the `30 deg` cells by only
  `0.19..0.29 m` and the `45 deg` cells by `0.01..1.53 m`.

The `45 deg` miss is a systematic terminal tail overshoot, not random noise.
For `4/6/8 km`, the nearest point is approximately `-19.2..-21.6 m` in target
local forward and `11.0..11.4 m` laterally, with `tail` aspect. Terminal mean
command is about `29 g`. Saturation fraction falls from `0.477` at `4 km` to
`0.111` at `8 km` while miss distance remains near `22..24 m`; therefore the
`35 g` clamp alone does not explain the residual.

## Structural controls

| Variant | 4 km / 45 deg | 6 km / 45 deg | 8 km / 45 deg | 16 km / 30 deg O control |
|---|---:|---:|---:|---:|
| Full baseline | `22.438` | `22.101` | `24.448` | `17.010` |
| No track filter | `19.120` | `18.206` | `19.400` | `12.703` |
| Near-instant scalar autopilot | `20.078` | `21.520` | `23.735` | `16.148` |
| Second-order autopilot | `25.279` | `22.843` | `25.024` | `17.331` |
| Third-order autopilot | `35.878` | `24.537` | `25.767` | `18.690` |

Removing track filtering improves the `45 deg` cells by `3.3..5.0 m`, but it
also moves the sensitive `16 km / 30 deg` O-class negative control inside the
`15 m` fuze radius. It broadens the launch window and is not a safe closure.

A near-instant scalar autopilot improves the core `45 deg` cells by only
`0.6..2.4 m`; none enters `R_fuze`. Second- and third-order scalar autopilots
degrade the result. Scalar magnitude lag is therefore secondary, and changing
autopilot order does not address the remaining guidance geometry.

## Mechanism findings that remain open

The trace exposes two high-priority structural inconsistencies, but this
first-stage gate-based ablation cannot isolate them exactly:

1. The missile transform heading remains near its launch attitude while the
   velocity heading turns by roughly `47..52 deg` in the `30 deg` cases and
   `75..80 deg` in the `45 deg` cases. Capture uses the velocity direction,
   while PN/APN rate terms are transformed through the missile `Transform`.
   Because relative-bearing differentiation and frame transformation are
   coupled, the next experiment must use a world-vector LOS-rate PN formulation
   rather than forcing the entity attitude externally.
2. The constant-velocity target produces peak estimated target acceleration of
   about `22..29 g`. Direct APN is limited to roughly `5.4..6.1 g`, but the same
   estimated acceleration also enters the quadratic lead prediction without
   that APN limit. A velocity-only lead versus velocity-plus-acceleration lead
   ablation is required before assigning the remaining overshoot to this term.

## Decision

The current `45 deg -> M` launch-window classification remains a faithful
description of the present runtime, but it is not mechanism closure. “No
nominal guidance residual” in the expectation audit means the classification
matches observed behavior; it does not mean the guidance mechanism is
calibrated.

Do not increase `N`, `g`, or widen the N class on this evidence. The next exact
mechanism batch should keep all scalar values frozen and add:

1. independent capture, PN, lead-velocity, lead-acceleration, and APN switches;
2. capture/PN/APN vectors, pre-clamp total command, post-clamp command, and
   achieved acceleration vector diagnostics;
3. current-frame versus world-vector LOS-rate PN;
4. velocity-only lead, quadratic lead, and a constant-velocity truth-kinematics
   oracle;
5. mandatory preservation of `4/6/8 km / 30 deg` positives and
   `12 km / 45 deg`, `16 km / 30 deg` negative controls.
