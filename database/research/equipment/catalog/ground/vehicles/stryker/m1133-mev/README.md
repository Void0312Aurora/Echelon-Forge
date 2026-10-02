# M1133 Medical Evacuation Vehicle

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/stryker/m1133-mev/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-stryker-m1133-mev` |
| Family / variant | Stryker / M1133 MEV |
| Hull context | Medical evacuation configuration |
| Role | Battalion aid station and protected medical evacuation |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Listed configuration mass | 17.0 t | `p5-us-ground-stryker-usace-dims` | A | Medical fit configuration; not a universal combat mass |
| Length × width × height | 7.34 × 2.72 × 2.67 m | `p5-us-ground-stryker-usace-dims` | A | Medical interior and litter fit context |
| Crew | 3 | `p5-us-ground-stryker-pm-atlss` | A | Crew figure; patient capacity not established here |
| Payload | Medical treatment and evacuation equipment | `p5-us-ground-stryker-pm-atlss` | A | Litter/ambulatory capacity unknown |
| Armament | No primary gun; six four-barrel M6 66 mm smoke grenade launchers on a hinged platform forward of the commander's station for self-protection | `p5-us-ground-stryker-m1133mev-afvdatabase` | C | Confirms the MEV is unarmed as the handbook indicates and supplies the self-defense fit the row above leaves unestablished. Do not add an RWS |
| Mission systems | Battalion aid-station and advanced-trauma equipment | `p5-us-ground-stryker-pm-atlss` | A | Medical equipment inventory/performance unknown |
| Patient capacity | Four litters, or six seated, or a mixed load; rear compartment enlarged with vertical walls and a 25 cm (10 in) higher roof | `p5-us-ground-stryker-m1133mev-afvdatabase` | C | Resolves the litter/ambulatory capacity left unknown above |
| Engine designation | Caterpillar 3126, six-cylinder four-cycle inline turbocharged diesel, 350 hp at 2,500 rpm | `p5-us-ground-stryker-m1133mev-afvdatabase` | C | Secondary-sourced designation; the A1 450 hp rating is not merged |
| Transmission | Allison MD 3066P, six forward and one reverse | `p5-us-ground-stryker-m1133mev-afvdatabase` | C | Secondary source; shift schedule and torque curve not public |
| Fuel capacity | 53 gal (200 L) | `p5-us-ground-stryker-m1133mev-afvdatabase` | C | Secondary source; usable reserve fraction not stated |
| Combat dimensions | 275.83 × 114.39 × 101.65 in (7.006 × 2.906 × 2.582 m) | `p5-us-ground-stryker-family-gdlsbrochure` | B | GDLS manufacturer combat envelope, which agrees with the Tier C compilation on all three axes for this variant |
| Shipping dimensions | 275.83 × 106.39 × 93.78 in (7.006 × 2.702 × 2.382 m) | `p5-us-ground-stryker-family-gdlsbrochure` | B | GDLS shipping envelope; length is unchanged between configurations on this variant while width and height are not |
| Combat weight | 37,341 lb (16,938 kg) | `p5-us-ground-stryker-m1133mev-afvdatabase` | C | Secondary combat-mass figure. Lowest of the family set; distinct from the 17.0 t listed configuration mass above |
| Dimensions (combat) | 275.83 × 114.39 × 101.65 in (7.006 × 2.906 × 2.582 m) | `p5-us-ground-stryker-m1133mev-afvdatabase` | C | Differs from the USACE row above; the two are different configurations and both are retained |
| Maximum level road speed | 60 mph (96 km/h) | `p5-us-ground-stryker-m1133mev-afvdatabase` | C | Variant-level road figure; off-road speed not published |
| Road range | approximately 330 mi (530 km) on roads | `p5-us-ground-stryker-m1133mev-afvdatabase` | C | Explicitly a road figure; cross-country range not published |
| Trench / vertical obstacle | 78 in (200 cm) / 23 in (58 cm) | `p5-us-ground-stryker-m1133mev-afvdatabase` | C | Cross-country obstacle envelope; configuration-dependent |
| Fording depth | 51 in (130 cm) | `p5-us-ground-stryker-m1133mev-afvdatabase` | C | Fording, not swimming; preparation requirements not stated |
| Grade / sideslope | 60% / 30% | `p5-us-ground-stryker-m1133mev-afvdatabase` | C | Slope limits as published; load-dependent in practice |
| Minimum turning diameter | 52 ft (16 m) | `p5-us-ground-stryker-m1133mev-afvdatabase` | C | Four-wheel steering geometry; measurement convention not stated |
| Public protection | Armored Stryker hull; exact thickness/level unknown | `p5-us-ground-stryker-army-wsh-2020` | A | Qualitative only |
| Hull armor maximum | welded high-hard steel structure, maximum 0.5 in (1.3 cm) | `p5-us-ground-stryker-m1133mev-afvdatabase` | C | Single maximum plate figure from a secondary source. It is not a protection rating, not an all-round value, and not an RHAe equivalence |

Field confidence follows the evidence tier and context column: direct variant statements are high confidence; payload-sensitive statements are medium confidence; `unknown` fields remain unestimated.

## Configuration Boundary

Rows carried from `p5-us-ground-stryker-m1133mev-afvdatabase` describe the medical evacuation configuration. The source records the 2010 double-V hull and the separate Stryker A1 upgrade (450 hp, 60,000 lb suspension, 910 A alternator, in-vehicle network) as distinct configurations; neither is merged into this record.

## Source References

- `p5-us-ground-stryker-usace-dims`
- `p5-us-ground-stryker-pm-atlss`
- `p5-us-ground-stryker-army-wsh-2020`
- `p5-us-ground-stryker-m1133mev-afvdatabase`
- `p5-us-ground-stryker-family-gdlsbrochure`
- `p5-us-ground-stryker-family-gao03671`
