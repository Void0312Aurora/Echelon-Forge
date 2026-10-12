# `src/systems/domains/naval` Boundary

`systems/domains/naval` contains the per-tick progression logic for ship,
submarine, and embarked aviation token-level runtime. It consumes
`components/domains/naval/platform`, `components/command`, and foundational
movement components, but does not own mission/tasking orchestration or facades.

This is an active naval runtime slice, not a placeholder. It is still bounded to
platform motion, embarked-air tokens, OTH relay, and naval weapon-release hooks;
tasking/contact evidence is surfaced through contracts/facade packets rather
than owned here as a full N4 mission runtime.

## Allowed

- Updates to ship/submarine motion, heading, speed, and depth.
- Per-frame mutation for naval platforms such as sea-state response, seakeeping, and station keeping.
- Token-level runtime scheduling for launch/recovery of embarked aircraft and OTH relay behavior.
- Naval mission-command weapon-release hooks that call the shared weapon release service.

## Forbidden

- Defining naval platform components or command/tasking DTOs.
- Mission rewards, termination, scenario compilation, or episode transitions.
- Python bindings, facades, training scripts, or multi-world owners.
- Expanding the embarked aviation MVP runtime into a large, unfrozen mission orchestration layer.
- Owning N4 contact evidence, tasking packets, or pre-fire diagnostics exports.

## Current Files

- [ship_motion_system.h](ship_motion_system.h)
  - Updates ship speed, heading, sea-state drag, and station keeping.
- [submarine_motion_system.h](submarine_motion_system.h)
  - Updates submarine speed, heading, and depth envelopes. An entity may
    attach `SubmarineBathymetryPolicy` to opt into the shared environment
    segment query. The policy requires an explicit Transform-to-keel distance
    and matching horizontal/vertical frame identifiers; it does not infer a
    hull reference from `draft_m`.
- [embarked_air_ops_system.h](embarked_air_ops_system.h)
  - Token-level runtime for launch/recovery of embarked helicopters and OTH relay behavior.
- [naval_mission_weapon_release_system.h](naval_mission_weapon_release_system.h)
  - Naval mission-command weapon-release bridge into the shared weapon release service.
- [naval_logistics_system.h](naval_logistics_system.h)
  - Naval underway replenishment progression for abstract stores transfer.

## Dependency Direction

This directory may consume `components/domains/naval/platform`,
`components/command`, `components/basic`, and the required pieces of
`core/interfaces`. It should not depend on `runtime/facade`,
`interfaces/python`, or training/scenario glue.

### Bathymetry admission boundary

Bathymetry-aware motion is an explicit profile. The environment owns
`IEnvironmentModel::get_bathymetry_along_segment`; the naval system does not
own a raster or infer water depth from generic terrain elevation. The provider
must return `Valid`, a finite minimum water depth for the complete horizontal
step, matching horizontal/vertical frame identifiers, a non-empty source, zero
water-surface elevation in the Transform datum, and an explicit
time-invariant-for-step declaration. `Unavailable`, `Dry`, `OutOfCoverage`,
`InvalidDatum`, and incomplete metadata reject the whole step and report an
observable policy status. An entity without the policy retains the legacy
open-water kinematic behavior.

`SubmarineBathymetryPolicy` is an admitted, reflected optional component. This
initial test slice attaches it through the native world lease; content loading
and Agent observations do not enable or expose it. Its addition changes the
sealed composition identity and is carried through the compatibility manifest,
resolved plan, Cordis provenance, and host/batch evidence. The policy and its
last status/source survive native state transfer. The default environment
returns `Unavailable`; no atlas or ocean-depth data is fabricated.

Clearance and hull-reference offset must both be finite and nonnegative.
Water too shallow to contain the hull even at surface zero rejects horizontal
movement. A segment already incompatible with the current depth also rejects
the horizontal sweep and permits only rate-limited vertical movement toward
the allowed depth. Unknown metadata holds depth and horizontal movement;
heading may still evolve within the existing turn limit. A conservative segment
minimum can reject trajectories that a future continuous solver could admit.

This slice limits commands and trajectories only. It does not model seabed
contact, collision response, damage, or hydrodynamics.

The native opt-in tests exercise two independently implemented synthetic
bathymetry queries: a full-segment interior shoal and a linear seabed slope.
They establish consumer interoperability, not availability of real bathymetry
data. Before promoting this slice after integration with other native changes,
recompute the state-transfer migration digest and run the default composition,
host state-owner roundtrip, and host/batch parity gates on the combined commit.
Per-PR green checks do not establish that combined evidence.
