# Naval Ship Unit References

Language:
- English canonical: `ship_unit_references.md`
- Chinese companion: [ship_unit_references.zh.md](ship_unit_references.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/reference/ship_unit_references.md`
Owner: `domains/naval`
Last verified: `2026-08-08`

Status: maintained ship-unit reference baseline for the naval specialization.

This document records the first publicly traceable ship-unit baselines selected
for the maintained naval specialization.

It is not a doctrine document and not the primary place to define naval task
semantics. Its purpose is narrower:

- provide a reality-anchored reference pair for the first naval standards work
- keep public ship data traceable to official or manufacturer sources
- separate public facts from runtime estimates and temporary modeling rules

Semantic ownership remains in:

- [US Navy Profile](../../joint/service_profiles/standards/navy_profile.md)
- [Naval owner entrypoint](../README.md)
- [Naval Minimal Task Structure](../standards/minimal_task_structure.md)

The Navy service profile owns service-level organization and authority
interpretation. This Naval reference supplies unit/configuration evidence for
maritime execution; it does not transfer execution ownership to the profile.

## Reference Pairing

The current canonical first-batch naval reference pair is:

- escort/screen unit: USS Arleigh Burke (`DDG-51`), Arleigh Burke-class Flight
  I guided-missile destroyer
- supported high-value unit: USNS Lewis and Clark (`T-AKE-1`), Lewis and
  Clark-class dry cargo/ammunition ship

This pair is useful because it maps cleanly onto the maintained naval tasking
baseline without overextending the current runtime:

- `DDG-51`: `TASK_SCREEN`, `ScreenCommander`, `Screen`
- `T-AKE-1`: `TASK_SUPPORT`, `LogisticsCoordinator`, `Support`

The value of this page is not that these are the only valid naval units. The
value is that they form a traceable and reusable first reference baseline.

## Public Source Baseline

### DDG-51 Flight I / USS Arleigh Burke

Primary public sources:

- [USS Arleigh Burke characteristics page](https://www.surflant.usff.navy.mil/Organization/Operational-Forces/Destroyers/USS-Arleigh-Burke-DDG-51/About-Us/Characteristics/)
- [Destroyer ship-class page](https://www.surflant.usff.navy.mil/Organization/Operational-Forces/Destroyers/Destroyer-Ship-Class-DDG-Info-Page/)

Recorded public values:

- dimensions: `153.8 m x 20.4 m x 9.3 m`
- Flight I full-load displacement: `8,230 long tons`
- speed: `30+ knots` on the ship page and `30 knots` on the class page
- range: `4,400 nautical miles at 20 knots`
- crew: `300+` on the ship page and `303` on the class page
- publicly listed systems include Aegis Combat System, `AN/SPY-1D`,
  `AN/SPS-67(V)`, `Mk 41 VLS`, `5-inch/54 gun`, Harpoon launchers, and CIWS on
  early-flight ships

Runtime conversions in
[examples/config/database/ships/units/ddg51_flight_i_uss_arleigh_burke.json](../../../../examples/config/database/ships/units/ddg51_flight_i_uss_arleigh_burke.json):

- full-load displacement: `8,230 long tons -> 8,362,000 kg`
- light displacement: `6,711 long tons -> 6,819,000 kg`
- length: `153.8 m`
- beam: `20.4 m`
- draft: `9.3 m`
- maximum speed: `30 kt -> 15.43 m/s`
- range speed: `20 kt -> 10.29 m/s`

### T-AKE-1 / USNS Lewis and Clark

Primary public sources:

- [U.S. Navy T-AKE fact file](https://www.navy.mil/Resources/Fact-Files/Display-FactFiles/Article/2211797/dry-cargoammunition-ships-t-ake/)
- [General Dynamics NASSCO T-AKE fact sheet](https://www.nassco.com/pdfs/T-AKE_FactSheet_Jan_2007.pdf)

Recorded public values:

- length: `689 ft`
- beam: `106 ft`
- draft: `30 ft`
- displacement: `41,000 tons` on the Navy fact file and `41,000 metric tons`
  at design draft on the NASSCO sheet
- speed: `20 knots`
- range: `14,000 nautical miles` at design speed and draft on the NASSCO sheet
- listed crewing: `53 civilian`

Runtime conversions in
[examples/config/database/ships/units/take1_usns_lewis_and_clark.json](../../../../examples/config/database/ships/units/take1_usns_lewis_and_clark.json):

- full-load displacement: `41,000 metric tons -> 41,000,000 kg`
- length: `689 ft -> 210.0 m`
- beam: `106 ft -> 32.31 m`
- draft: `30 ft -> 9.14 m`
- maximum speed: `20 kt -> 10.29 m/s`

## Modeling Boundaries

The `ShipPlatform` data recorded for these units should be interpreted as public
parameter baselines, not as convenience placeholders.

They currently anchor:

- displacement
- dimensions
- speed
- range
- crewing

The following remain explicit runtime estimates or temporary modeling rules:

- `height_above_waterline_m` is still an estimate used for line-of-sight and
  future radar-horizon work because public fact sheets usually list draft, not
  precise sensor or mast height
- surface-search radar runtime range is currently bounded by radar-horizon
  reasoning rather than by any claimed classified or unsourced maximum range
- ship `health` is currently scaled at one HP per metric tonne of full-load
  displacement until naval damage and lethality calibration is standardized
- `DDG-51` now carries an MVP `naval_weapon_system` mount inventory consumed by
  the naval runtime. Ready counts, engagement ranges, hit probabilities,
  cooldowns, and damage values remain engineering calibrations or
  community-derived approximations rather than public performance authority;
  the generic `Ammo` component still exists elsewhere but is not the sole naval
  inventory surface

Current horizon-based runtime examples:

- `DDG-51` surface search:
  `3.57 * (sqrt(25 m owner antenna) + sqrt(5 m target)) = 25.8 nmi = 46.3 km`
- `T-AKE-1` navigation/surface search:
  `3.57 * (sqrt(15 m owner antenna) + sqrt(5 m target)) = 19.6 nmi = 36.3 km`

These should be read as maintained modeling assumptions, not as doctrine claims.

Current implementation evidence:

- [Naval weapon-system component](../../../../src/components/domains/naval/combat/weapon_naval.h)
- [Weapon-release runtime service](../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp)

## Reference Usage

The first intended use of this baseline is a low-complexity naval screen
scenario:

1. a supported logistics HVU
2. a single escort or screen ship
3. one or more surface contacts
4. scoring based on screen geometry, reporting, and supported-unit protection

That usage example is included here only to explain why these two units were
selected first. The actual scenario workflow and evaluation design should remain
in scenario/task documents rather than migrating into this reference page.

## Related Documents

- [Naval owner entrypoint](../README.md)
- [Naval Minimal Task Structure](../standards/minimal_task_structure.md)
- [Naval Observation Contract](../standards/observation_contract.md)
- [US Navy Profile](../../joint/service_profiles/standards/navy_profile.md)
- [Document Alignment Map](../../../engineering/documentation/reference/document_alignment_map.md)
