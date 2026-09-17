# M1126 Infantry Carrier Vehicle

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/stryker/m1126-icv/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-stryker-m1126-icv` |
| Family / variant | Stryker / M1126 ICV |
| Hull context | Legacy flat-bottom hull (FBH) baseline in the cited material |
| Role | Infantry carrier |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Listed configuration mass | 16.1 t | `p5-us-ground-stryker-usace-dims` | A | Source table configuration; not a universal combat or GVW value |
| Length × width × height | 7.32 × 2.84 × 2.69 m | `p5-us-ground-stryker-usace-dims` | A | Configuration and attachments must be retained when normalized |
| Powerplant | 350 hp diesel | `p5-us-ground-stryker-army-wsh-2020` | A | Baseline ICV context; do not copy to later DVH/DVHA1 leaves |
| Engine designation | Caterpillar 3126, six-cylinder four-cycle inline turbocharged diesel, 350 hp at 2,500 rpm | `p5-us-ground-stryker-m1126icv-afvdatabase` | C | Secondary-sourced designation. The Army handbook gives 350 hp without naming the engine, so the model designation and the A1 450 hp figure are not merged |
| Transmission | Allison MD 3066P, six forward and one reverse | `p5-us-ground-stryker-m1126icv-afvdatabase` | C | Secondary source; shift schedule and torque curve not public |
| Fuel capacity | 53 gal (200 L) | `p5-us-ground-stryker-m1126icv-afvdatabase` | C | Secondary source; usable reserve fraction not stated |
| Road speed | 60 mph | `p5-us-ground-stryker-army-wsh-2020` | A | Explicit public baseline figure; terrain-specific speed unknown |
| Maximum level road speed | 60 mph (96 km/h) | `p5-us-ground-stryker-m1126icv-afvdatabase` | C | Corroborates the handbook figure; off-road speed not published |
| Cruising range | 330 mi | `p5-us-ground-stryker-army-wsh-2020` | A | Explicit public baseline figure; fuel-load context not established |
| Road range | approximately 330 mi (530 km) on roads | `p5-us-ground-stryker-m1126icv-afvdatabase` | C | Explicitly a road figure; cross-country range not published |
| Combat dimensions | 286.3 × 116.43 × 122.88 in (7.272 × 2.957 × 3.121 m) | `p5-us-ground-stryker-family-gdlsbrochure` | B | GDLS manufacturer combat envelope, which agrees with the Tier C compilation on all three axes for this variant |
| Shipping dimensions | 286.5 × 112.8 × 103.6 in (7.277 × 2.865 × 2.631 m) | `p5-us-ground-stryker-family-gdlsbrochure` | B | GDLS shipping envelope; note the shipping length is marginally longer than the combat length on this variant, so the two columns must not be interchanged |
| Combat weight | approximately 38,000 lb (17,200 kg) | `p5-us-ground-stryker-m1126icv-afvdatabase` | C | Secondary combat-mass figure. Distinct from the 16.1 t listed configuration mass above; neither is a GVW or GVWR value |
| Trench / vertical obstacle | 78 in (200 cm) / 23 in (58 cm) | `p5-us-ground-stryker-m1126icv-afvdatabase` | C | Cross-country obstacle envelope; configuration-dependent |
| Fording depth | 51 in (130 cm) | `p5-us-ground-stryker-m1126icv-afvdatabase` | C | Fording, not swimming; preparation requirements not stated |
| Grade / sideslope | 60% / 30% | `p5-us-ground-stryker-m1126icv-afvdatabase` | C | Slope limits as published; load-dependent in practice |
| Minimum turning diameter | 52 ft (16 m) | `p5-us-ground-stryker-m1126icv-afvdatabase` | C | Four-wheel steering geometry; measurement convention not stated |
| Crew / carried infantry | 2 crew + 9 infantry | `p5-us-ground-stryker-army-wsh-2020` | A | Configuration-specific carrier load |
| Crew (total) | 11 (commander, driver, nine passengers) | `p5-us-ground-stryker-m1126icv-afvdatabase` | C | Same seating arrangement as the row above, stated as a total |
| Armament | M2 .50 cal or Mk 19 remote weapon station | `p5-us-ground-stryker-army-wsh-2020` | A | Station fit is configuration-dependent |
| Armament (detailed) | .50 cal M2HB or 40 mm Mk 19 MOD3 on the M151E2 remote weapon system; 2,000 .50 cal rounds or 480 40 mm rounds; 7.62 mm M240B with 3,200 rounds as an adapter option | `p5-us-ground-stryker-m1126icv-afvdatabase` | C | Mount, store loads and the M240B option. Smoke-grenade fit not resolved to a single configuration |
| Public protection | Armored Stryker hull; exact thickness/level unknown | `p5-us-ground-stryker-army-wsh-2020` | A | Do not infer armor thickness from family descriptions |
| Hull armor maximum | welded high-hard steel structure, maximum 0.5 in (1.3 cm) | `p5-us-ground-stryker-m1126icv-afvdatabase` | C | Single maximum plate figure from a secondary source. It is not a protection rating, not an all-round value, and not an RHAe equivalence |
| Mission systems | Infantry squad transport; C4ISR/RWS context | `p5-us-ground-stryker-pm-atlss` | A | Detailed sensor and radio performance not established |

Field confidence follows the evidence tier and context column: direct variant statements are high confidence; baseline or family-context statements are medium confidence; `unknown` remains unestimated.

## Configuration Boundary

Rows carried from `p5-us-ground-stryker-m1126icv-afvdatabase` describe the baseline flat-bottom ICV as that source states it. That source also documents the 2010 double-V hull and the separate Stryker A1 upgrade (450 hp, 60,000 lb suspension, 910 A alternator, in-vehicle network). Neither is merged into this record, and the 350 hp engine figure above must not be carried into a DVH or A1 leaf.

## Source References

- `p5-us-ground-stryker-army-wsh-2020`
- `p5-us-ground-stryker-usace-dims`
- `p5-us-ground-stryker-pm-atlss`
- `p5-us-ground-stryker-m1126icv-afvdatabase`
- `p5-us-ground-stryker-family-gdlsbrochure`
