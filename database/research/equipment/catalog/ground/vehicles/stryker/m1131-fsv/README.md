# M1131 Fire Support Vehicle

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/stryker/m1131-fsv/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-stryker-m1131-fsv` |
| Family / variant | Stryker / M1131 FSV |
| Hull context | Fire-support configuration |
| Role | Target acquisition, fire support, and secure communications |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Listed configuration mass | 16.5 t | `p5-us-ground-stryker-usace-dims` | A | Source table configuration |
| Length × width × height | 7.32 × 2.84 × 2.62 m | `p5-us-ground-stryker-usace-dims` | A | Configuration context retained |
| Crew | 4 | `p5-us-ground-stryker-pm-atlss` | A | Draft mission configuration |
| Armament | Commander's cupola with .50 cal M2HB or 40 mm Mk 19 MOD3 (2,000 or 480 rounds), plus 7.62 mm M240B on a rear hull swing mount with 3,200 rounds | `p5-us-ground-stryker-m1131fsv-afvdatabase` | C | Secondary-sourced mount and store loads. This resolves the earlier not-established state; the cupola traverse is manual on this variant |
| Mission systems | Target acquisition, identification, tracking; four secure combat radio nets; automatic designation to firing units | `p5-us-ground-stryker-pm-atlss` | A | Sensor accuracy, range, and network latency unknown |
| Engine designation | Caterpillar 3126, six-cylinder four-cycle inline turbocharged diesel, 350 hp at 2,500 rpm | `p5-us-ground-stryker-m1131fsv-afvdatabase` | C | Secondary-sourced designation; the A1 450 hp rating is not merged |
| Transmission | Allison MD 3066P, six forward and one reverse | `p5-us-ground-stryker-m1131fsv-afvdatabase` | C | Secondary source; shift schedule and torque curve not public |
| Fuel capacity | 53 gal (200 L) | `p5-us-ground-stryker-m1131fsv-afvdatabase` | C | Secondary source; usable reserve fraction not stated |
| Combat weight | 38,186 lb (17,321 kg) | `p5-us-ground-stryker-m1131fsv-afvdatabase` | C | Secondary combat-mass figure. Distinct from the 16.5 t listed configuration mass above |
| Dimensions (combat) | 287.9 × 153.6 × 128.4 in (7.313 × 3.901 × 3.261 m) | `p5-us-ground-stryker-m1131fsv-afvdatabase` | C | Differs from the USACE row above; the two are different configurations and both are retained |
| Maximum level road speed | 60 mph (96 km/h) | `p5-us-ground-stryker-m1131fsv-afvdatabase` | C | Variant-level road figure; off-road speed not published |
| Road range | approximately 330 mi (530 km) on roads | `p5-us-ground-stryker-m1131fsv-afvdatabase` | C | Explicitly a road figure; cross-country range not published |
| Trench / vertical obstacle | 78 in (200 cm) / 23 in (58 cm) | `p5-us-ground-stryker-m1131fsv-afvdatabase` | C | Cross-country obstacle envelope; configuration-dependent |
| Fording depth | 51 in (130 cm) | `p5-us-ground-stryker-m1131fsv-afvdatabase` | C | Fording, not swimming; preparation requirements not stated |
| Grade / sideslope | 60% / 30% | `p5-us-ground-stryker-m1131fsv-afvdatabase` | C | Slope limits as published; load-dependent in practice |
| Minimum turning diameter | 52 ft (17 m) | `p5-us-ground-stryker-m1131fsv-afvdatabase` | C | Four-wheel steering geometry; measurement convention not stated |
| Crew (detailed) | 4 (commander, driver, fire support officer, radio telephone operator) | `p5-us-ground-stryker-m1131fsv-afvdatabase` | C | Names the seats behind the draft crew figure above |
| Public protection | Armored Stryker hull; exact thickness/level unknown | `p5-us-ground-stryker-army-wsh-2020` | A | Qualitative only |
| Hull armor maximum | welded high-hard steel structure, maximum 0.5 in (1.3 cm) | `p5-us-ground-stryker-m1131fsv-afvdatabase` | C | Single maximum plate figure from a secondary source. It is not a protection rating, not an all-round value, and not an RHAe equivalence |

Field confidence follows the evidence tier and context column: direct variant statements are high confidence; mission/configuration context is medium confidence; `unknown` fields remain unestimated.

## Configuration Boundary

Rows carried from `p5-us-ground-stryker-m1131fsv-afvdatabase` describe the fire-support configuration. The source records the 2010 double-V hull and the separate Stryker A1 upgrade (450 hp, 60,000 lb suspension, 910 A alternator, in-vehicle network) as distinct configurations; neither is merged into this record.

## Source References

- `p5-us-ground-stryker-usace-dims`
- `p5-us-ground-stryker-pm-atlss`
- `p5-us-ground-stryker-army-wsh-2020`
- `p5-us-ground-stryker-m1131fsv-afvdatabase`
