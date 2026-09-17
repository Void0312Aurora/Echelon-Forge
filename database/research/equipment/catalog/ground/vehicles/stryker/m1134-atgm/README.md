# M1134 Anti-Tank Guided Missile Vehicle

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/stryker/m1134-atgm/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-stryker-m1134-atgm` |
| Family / variant | Stryker / M1134 ATGM |
| Hull context | Legacy anti-tank guided missile configuration |
| Role | Long-range anti-armor fires |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Listed configuration mass | 17.7 t | `p5-us-ground-stryker-usace-dims` | A | Source table configuration |
| Length × width × height | 6.86 × 2.84 × 2.67 m | `p5-us-ground-stryker-usace-dims` | A | Launcher stowage/erected geometry must be separated later |
| Crew | 4 | `p5-us-ground-stryker-pm-atlss` | A | Draft mission configuration |
| Main armament | Elevated TOW launcher, twin tube, 12 missiles (two loaded, ten stowed) | `p5-us-ground-stryker-m1134atgm-afvdatabase` | C | Secondary source. Supplies the ready and stowed counts the row above leaves open; the launcher is compatible with all TOW variants and the missile subtype is not narrowed further |
| Launcher elevation system | Elevated TOW System with MITAS, mast raised 0.5 m (20 in) above the hull roof, 360 deg electric traverse at 40 deg/s, elevation +29 to -20 deg | `p5-us-ground-stryker-m1134atgm-afvdatabase` | C | Resolves the launcher stowage/erected geometry question in the row above; reload requires elevating to +40 deg and takes under two minutes |
| Mission systems | Anti-armor engagement and launcher sighting | `p5-us-ground-stryker-pm-atlss` | A | Sensor and missile performance not extracted here |
| Engine designation | Caterpillar 3126, six-cylinder four-cycle inline turbocharged diesel, 350 hp at 2,500 rpm | `p5-us-ground-stryker-m1134atgm-afvdatabase` | C | Secondary-sourced designation; the A1 450 hp rating is not merged |
| Transmission | Allison MD 3066P, six forward and one reverse | `p5-us-ground-stryker-m1134atgm-afvdatabase` | C | Secondary source; shift schedule and torque curve not public |
| Fuel capacity | 53 gal (200 L) | `p5-us-ground-stryker-m1134atgm-afvdatabase` | C | Secondary source; usable reserve fraction not stated |
| Combat weight | 40,904 lb (18,554 kg) | `p5-us-ground-stryker-m1134atgm-afvdatabase` | C | Secondary combat-mass figure. Distinct from the 17.7 t listed configuration mass above |
| Dimensions (combat) | 287.0 × 149.8 × 119.3 in (7.289 × 3.805 × 3.031 m) | `p5-us-ground-stryker-m1134atgm-afvdatabase` | C | Differs from the USACE row above; the two are different configurations and both are retained |
| Maximum level road speed | 60 mph (96 km/h) | `p5-us-ground-stryker-m1134atgm-afvdatabase` | C | Variant-level road figure; off-road speed not published |
| Road range | approximately 330 mi (530 km) on roads | `p5-us-ground-stryker-m1134atgm-afvdatabase` | C | Explicitly a road figure; cross-country range not published |
| Trench / vertical obstacle | 78 in (200 cm) / 23 in (58 cm) | `p5-us-ground-stryker-m1134atgm-afvdatabase` | C | Cross-country obstacle envelope; configuration-dependent |
| Fording depth | 51 in (130 cm) | `p5-us-ground-stryker-m1134atgm-afvdatabase` | C | Fording, not swimming; preparation requirements not stated |
| Grade / sideslope | 60% / 30% | `p5-us-ground-stryker-m1134atgm-afvdatabase` | C | Slope limits as published; load-dependent in practice |
| Minimum turning diameter | 52 ft (16 m) | `p5-us-ground-stryker-m1134atgm-afvdatabase` | C | Four-wheel steering geometry; measurement convention not stated |
| Secondary armament | 7.62 mm M240B on the commander's cupola with 2,000 rounds; must be folded down before the launcher fires | `p5-us-ground-stryker-m1134atgm-afvdatabase` | C | Supply load and the firing interlock the rows above do not state |
| Crew (detailed) | 4 (commander, driver, gunner, loader) | `p5-us-ground-stryker-m1134atgm-afvdatabase` | C | Names the seats behind the draft crew figure above |
| Public protection | Armored Stryker hull; exact thickness/level unknown | `p5-us-ground-stryker-army-wsh-2020` | A | Qualitative only |
| Hull armor maximum | welded high-hard steel structure, maximum 0.5 in (1.3 cm) | `p5-us-ground-stryker-m1134atgm-afvdatabase` | C | Single maximum plate figure from a secondary source. It is not a protection rating, not an all-round value, and not an RHAe equivalence |

Field confidence follows the evidence tier and context column: direct variant statements are high confidence; launcher/loadout context is medium confidence; `unknown` fields remain unestimated.

## Configuration Boundary

Rows carried from `p5-us-ground-stryker-m1134atgm-afvdatabase` describe the legacy anti-tank guided missile configuration. The source records the 2010 double-V hull and the separate Stryker A1 upgrade (450 hp, 60,000 lb suspension, 910 A alternator, in-vehicle network) as distinct configurations; neither is merged into this record.

## Source References

- `p5-us-ground-stryker-usace-dims`
- `p5-us-ground-stryker-pm-atlss`
- `p5-us-ground-stryker-army-wsh-2020`
- `p5-us-ground-stryker-m1134atgm-afvdatabase`
