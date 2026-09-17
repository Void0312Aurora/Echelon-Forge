# M1127 Reconnaissance Vehicle

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/stryker/m1127-rv/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-stryker-m1127-rv` |
| Family / variant | Stryker / M1127 RV |
| Hull context | Legacy reconnaissance vehicle configuration |
| Role | Reconnaissance, surveillance, and target acquisition |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Listed configuration mass | 16.5 t | `p5-us-ground-stryker-usace-dims` | A | Source table configuration; not a universal combat mass |
| Length × width × height | 7.32 × 2.87 × 2.69 m | `p5-us-ground-stryker-usace-dims` | A | Configuration and sensor fit affect envelope |
| Powerplant | Caterpillar 350 hp diesel; Allison transmission | `p5-us-ground-m1127-armor-army` | A | Variant-specific public description |
| Engine designation | Caterpillar 3126, six-cylinder four-cycle inline turbocharged diesel, 350 hp at 2,500 rpm | `p5-us-ground-stryker-m1127rv-afvdatabase` | C | Secondary-sourced designation; matches the Army power figure without merging the later A1 rating |
| Transmission | Allison MD 3066P, six forward and one reverse | `p5-us-ground-stryker-m1127rv-afvdatabase` | C | Names the Allison unit the Army row above describes generically |
| Fuel capacity | 53 gal (200 L) | `p5-us-ground-stryker-m1127rv-afvdatabase` | C | Secondary source; usable reserve fraction not stated |
| Road speed | Up to 60 mph | `p5-us-ground-m1127-armor-army` | A | Terrain-specific speed unknown |
| Maximum level road speed | 60 mph (96 km/h) | `p5-us-ground-stryker-m1127rv-afvdatabase` | C | Corroborates the Army figure; off-road speed not published |
| Cruising range | 330 mi | `p5-us-ground-m1127-armor-army` | A | Public cruising figure; fuel-load context not established |
| Road range | approximately 330 mi (530 km) on roads | `p5-us-ground-stryker-m1127rv-afvdatabase` | C | Explicitly a road figure; cross-country range not published |
| Combat weight | 39,568 lb (17,948 kg) | `p5-us-ground-stryker-m1127rv-afvdatabase` | C | Secondary combat-mass figure. Distinct from the 16.5 t listed configuration mass above; neither is a GVW or GVWR value |
| Trench / vertical obstacle | 78 in (200 cm) / 23 in (58 cm) | `p5-us-ground-stryker-m1127rv-afvdatabase` | C | Cross-country obstacle envelope; configuration-dependent |
| Fording depth | 51 in (130 cm) | `p5-us-ground-stryker-m1127rv-afvdatabase` | C | Fording, not swimming; preparation requirements not stated |
| Grade / sideslope | 60% / 30% | `p5-us-ground-stryker-m1127rv-afvdatabase` | C | Slope limits as published; load-dependent in practice |
| Minimum turning diameter | 52 ft (17 m) | `p5-us-ground-stryker-m1127rv-afvdatabase` | C | Four-wheel steering geometry; measurement convention not stated |
| Crew / reconnaissance load | 2 vehicle crew + 4 scouts + 1 augmentee | `p5-us-ground-m1127-armor-army` | A | Seven-person stated configuration |
| Crew (total) | 7 (commander, driver, five passengers) | `p5-us-ground-stryker-m1127rv-afvdatabase` | C | Same seating arrangement as the row above, stated as a total |
| Armament | M2 .50 cal or Mk 19 automatic grenade launcher; M6 countermeasure grenade launcher | `p5-us-ground-m1127-armor-army` | A | Weapon fit is configuration-dependent |
| Armament (mount and store loads) | .50 cal M2HB or 40 mm Mk 19 MOD3 on the commander's cupola, 2,000 or 480 rounds; 7.62 mm M240B on a rear hull swing mount with 3,200 rounds | `p5-us-ground-stryker-m1127rv-afvdatabase` | C | Mount types and store loads; cupola traverse is manual on this variant |
| Mission systems | C4ISR suite; LRAS3 reconnaissance sensor context | `p5-us-ground-m1127-armor-army` | A | Sensor performance/range not established |
| Mobility hardware | 8 wheels; run-flat tires; central tire inflation | `p5-us-ground-m1127-armor-army` | A | Tire model and suspension data unknown |
| Public protection | Armored Stryker hull; exact thickness/level unknown | `p5-us-ground-m1127-armor-army` | A | No armor thickness inference |
| Hull armor maximum | welded high-hard steel structure, maximum 0.5 in (1.3 cm) | `p5-us-ground-stryker-m1127rv-afvdatabase` | C | Single maximum plate figure from a secondary source. It is not a protection rating, not an all-round value, and not an RHAe equivalence |

Field confidence follows the evidence tier and context column: direct variant statements are high confidence; configuration-sensitive statements are medium confidence; `unknown` remains unestimated.

## Configuration Boundary

Rows carried from `p5-us-ground-stryker-m1127rv-afvdatabase` describe the legacy reconnaissance variant. That source states the M1127 was not given the double-V hull and records the separate Stryker A1 upgrade (450 hp, 60,000 lb suspension, 910 A alternator, in-vehicle network) as a distinct configuration. Neither is merged into this record.

## Source References

- `p5-us-ground-m1127-armor-army`
- `p5-us-ground-stryker-usace-dims`
- `p5-us-ground-stryker-m1127rv-afvdatabase`
