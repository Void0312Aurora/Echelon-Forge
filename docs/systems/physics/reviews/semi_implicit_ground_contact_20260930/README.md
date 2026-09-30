# Semi-Implicit Ground Contact

Document kind: `review`
Lifecycle: `retained`
Canonical: `docs/systems/physics/reviews/semi_implicit_ground_contact_20260930/README.md`
Owner: `systems/physics`
Last verified: `2026-09-30`

Status: `2026-09-30` `implemented / validation green at bounded scope`. The gear
contact in `GroundContact` is now solved against the end-of-step state of the
downstream integrators instead of the start-of-step state. The spring-damper,
Coulomb friction, and gear attitude constraints no longer limit the step size.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Demand: [Carrier Strike Group Engagement](../../../../domains/naval/work/active/carrier_strike_group_engagement/README.md),
  `S0-D` residual (2)
- [Gradient Realism Principles](../../../standards/gradient_realism_principles.md)
- [Physics Engine Upgrade Roadmap](../../work/issues/physics_engine_roadmap.md)
  (draft), Phase 3 "ground contact as unilateral constraint"
- Code: `src/systems/physics/ground_contact_system.h`,
  `src/systems/physics/ground_contact_solver.h`,
  `src/systems/physics/leapfrog_system.h`,
  `src/systems/physics/rotational_system.h`

## Problem

`GroundContact` computed the gear force from the start-of-step state and handed
it to `RotationalIntegrate` and `LeapfrogIntegrate`, which advance it
explicitly. The normal spring (k = 2.0e6 N/m, c = 3.5e5 N s/m) has a natural
period of about 0.3–0.5 s for 7–25 t airframes, so the explicit step was stable
only below about 0.12–0.17 s. The naval scenarios step at 0.5 s. Measured on the
pre-change build at `bd64bef6`, with zero throttle and no command, placed at gear
height for 10 s:

| Airframe | dt 0.05 s | dt 0.2 s | dt 0.5 s |
| --- | --- | --- | --- |
| F/A-18E Block III | holds (z 1.49–1.59 m) | thrown to 149 m | thrown to 320 m |
| F-16C Block 50 | holds | thrown to 669 m | thrown to 713 m |
| MH-60R | holds | thrown to 163 m | diverges (z ~ 1e44 m) |
| E-2D | holds | thrown to 116 m | thrown to 253 m |

The friction was explicit too. Its tanh-smoothed Coulomb law (v_ref 0.5 m/s) and
the slip-angle tyre law are stiff at low speed, so braking to a stop oscillated
at large steps. Two patches covered for this at 0.05 s: a bounded hold force, and
writing `Velocity` to zero below 0.25 m/s.

## Decision

Owner decision (`2026-09-30`): replace the time discretisation, and replace the
smoothed friction with set-valued (exact) Coulomb friction. Delete both
low-speed patches.

## Mechanism

`GroundContact` is the last force producer before the integrators, so the
`ForceAccumulator` already holds every other force and torque of the step. The
solver reproduces the downstream updates `v1 = v + h a`,
`z1 = z + h v + h^2 a / 2`, and `w1 = w + h tau / I`, then finds the contact
force for which the contact law holds at the end of the step. The stage order,
the integrators, and the executable graph are unchanged.

| Channel | Law (unchanged coefficients) | Discretisation |
| --- | --- | --- |
| Normal | unilateral `F = max(0, k p - c v)` | closed form on end-of-step penetration and sink rate. It engages when the free motion would end in penetration, and it is capped so the contact alone cannot lift the body clear within the step |
| Rolling resistance | Coulomb segment `|f_x| <= mu_roll N` per wheel | set-valued; outside the friction ellipse, as before |
| Braking and lateral | friction ellipse `(f_x/mu_brake N)^2 + (f_y/mu_lat N)^2 <= 1` on the main gear | set-valued |
| Tyre slip | cornering stiffness `C_alpha = 18 N/rad per N` | lateral compliance `v_lat = -(|v_long| / C_alpha) f_y`; this reduces to exact sticking at rest |
| Wheels | nose at +4 m (steerable, unbraked), main at -2 m, 20/80 load split | per-wheel convex QP over its force set (a capsule in scaled coordinates), with block Gauss-Seidel over the two wheels on the planar body (forward, left, yaw) |
| Pitch and roll gear constraint | spring beyond 10 deg pitch or 2 deg roll, damping outside a 0.01 rad/s deadband | scalar monotone solve per axis on the end-of-step angle and rate, with the Euler kinematics of `RotationalIntegrate` |

The tangential solve is maximum dissipation. Each wheel force minimises
`0.5 f'(h J M^-1 J' + R) f + (J u_free)' f` over its admissible set. That is the
discrete condition that the end-of-step slip lies in the normal cone of the
friction set.

## Validation

Local Windows MSVC Release (`build-independent-win`) and HEI Linux gcc 13
(`build-hei`), both at the change:

| Check | Before (`bd64bef6`) | After |
| --- | --- | --- |
| `ef_test` | 191 cases | 202 / 202 cases; 11 new in `ground_contact_solver`, `ground_contact_system` |
| `ef_composition_evidence_test` | pass | pass (graph hash unchanged) |
| parked probe (table above), dt 0.05/0.2/0.5 | thrown or diverges at 0.2 and 0.5 | every airframe holds at every step; z within 0.1 m of gear height; zero drift |
| HEI `tests/runtime tests/content tests/scenario tests/world_batch tests/architecture/composition` | 1361 passed, 1 failed | 1361 passed, 1 failed (same environment-only `runtime_bootstrap_import_plan_cache` red) |
| local architecture guards, naval, content, scenario | — | 356 passed, 2 failed (the WP22 binding-count reds, identical on `bd64bef6`) |

New native tests (expected values from closed forms or the continuous law):

- static spring equilibrium `m g / k` reached at dt 0.05, 0.2, and 0.5 s for
  7, 15, and 25 t;
- a body dropped at 3 m/s is caught in the step it arrives and does not
  rebound;
- idle thrust against the parking brake produces zero creep over 30 s;
- full braking decelerates at `(0.8 * 0.8 + 0.02) g` and stops exactly, with no
  velocity zeroing;
- thrust above rolling resistance accelerates at `(T - mu_roll N) / m`;
- a steady nose-up torque settles at `10 deg + tau / K`. The peak stays below
  the continuous law's own overshoot (16.8 deg, RK4 reference; the pitch spring
  is lightly damped, zeta 0.18);
- the per-wheel minimiser is checked against a dense grid of the admissible set.

Kernel contracts (`tests/contracts/unit/kernel/`, run per file):

| Contract | Before | After |
| --- | --- | --- |
| `action_midpoint_ground_roll` | pass (IAS 7.48) | pass (IAS 6.63) |
| `crosswind_track_vs_heading`, `free_fall_idle`, `pilot_pitch_sign_response` | pass | pass |
| `manual_takeoff` | **fail** (never reaches 300 m / 150 m/s) | **pass** (660 steps) |
| `pitch_hold_speed_scan`, `pitch_hold_throttle_scan`, `stable_level_flight` | fail | fail, same values (airborne only) |
| `takeoff_then_stable_flight`, `repeatability_takeoff_then_stable_flight` | fail (stable phase 708 steps) | fail (stable-phase roll 29.4 deg) |

The two takeoff-then-stable contracts fail before and after for a cause outside
ground contact. Their controller sends a neutral stick with `PilotAction.active`
set, and `pilot_action_requests_manual_takeover` treats a stick inside the 0.05
deadband as no takeover. The mission autopilot therefore flies. The scenario
commands heading 0 deg and spawns at heading 90 deg, so the autopilot holds full
aileron through the whole ground roll: the aileron command is saturated from the
first step (traced). The roll-restoring gear torque holds the wings at 2 deg
until lift-off, then the aircraft rolls into the commanded turn. Only the
failure message moves, because the implicit roll constraint pins the wings at
the band edge where the explicit one oscillated. This belongs to the Air
owner's control-source arbitration; see Residuals.

## Behaviour Changes

- Low-speed ground dynamics are exact Coulomb instead of smoothed. A braked or
  parked airframe sticks, and it breaks away when the applied force leaves the
  friction set. The midpoint ground-roll IAS moves from 7.48 to 6.63 m/s: the
  smoothed law under-applied rolling resistance below 1 m/s.
- The first touchdown step engages on the predicted, not current, penetration,
  so no step ends inside the gear with no force applied.
- Implicit damping is first order. Peak gear loads at dt 0.05 s touchdown are
  lower than the continuous law's (15 t at 3 m/s sink: 4.3 g against a 9.2 g
  reference). `GroundState` crash classification reads sink rate and speed, not
  load, so the lifecycle outcomes are unchanged.
- `GroundContact` no longer writes `Velocity`. The exact-stage inventory now
  lists `Inertia` and `ControlLawState` as reads and drops `Velocity`/`truth.vz`
  from its writes.

## Residuals

| Residual | Owner | Entry condition |
| --- | --- | --- |
| Deck contact surface: contact reads only terrain elevation, so an aircraft cannot rest on a flight deck | `systems/physics` with naval (deck geometry) | `CSG-S2` deck cycle |
| Takeoff-then-stable contracts: neutral-stick `PilotAction` does not take over from the mission autopilot, and scenario heading 0 deg against spawn 90 deg saturates the aileron on the roll | Air owner (control-source arbitration) | Air control-source review; independent of contact |
| Gear coefficients (k, c, pitch/roll K and D, `C_alpha`, 20/80 split, contact points) are fixed proxies, not per-airframe | Air owner, with platform content | per-airframe gear content in the unit schema |
| Longitudinal tyre slip (brake force from slip ratio, anti-skid) is not modelled; braking is Coulomb at `0.8 * brake` | `systems/physics` | a landing-rollout realism package |
| Contact is a single effective point per gear leg with a fixed load split; no per-leg normal forces or pitch-load transfer | `systems/physics` | a multi-point contact package (Phase 3/4 of the roadmap) |
