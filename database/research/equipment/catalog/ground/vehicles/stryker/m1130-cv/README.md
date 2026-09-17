# M1130 Command Vehicle

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/stryker/m1130-cv/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-stryker-m1130-cv` |
| Family / variant | Stryker / M1130 CV |
| Hull context | Command-vehicle configuration |
| Role | Command, control, communications, and mission planning |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Listed configuration mass | 16.6 t | `p5-us-ground-stryker-usace-dims` | A | Source table configuration; communications fit can change mass |
| Length × width × height | 7.49 × 2.84 × 2.69 m | `p5-us-ground-stryker-usace-dims` | A | Command antenna/power fit context |
| Crew | 5 | `p5-us-ground-stryker-pm-atlss` | A | Draft mission configuration; exact seat allocation unknown |
| Armament | Remote weapon station | `p5-us-ground-stryker-pm-atlss` | A | Weapon fit not further specified |
| Mission systems | C2 communications, data, planning, and aircraft antenna/power interface | `p5-us-ground-stryker-pm-atlss` | A | Radio suite and network performance unknown |
| Engine designation | Caterpillar 3126, six-cylinder four-cycle inline turbocharged diesel, 350 hp at 2,500 rpm | `p5-us-ground-stryker-m1130cv-afvdatabase` | C | Secondary-sourced designation; the A1 450 hp rating is not merged |
| Transmission | Allison MD 3066P, six forward and one reverse | `p5-us-ground-stryker-m1130cv-afvdatabase` | C | Secondary source; shift schedule and torque curve not public |
| Fuel capacity | 53 gal (200 L) | `p5-us-ground-stryker-m1130cv-afvdatabase` | C | Secondary source; usable reserve fraction not stated |
| Combat dimensions | 290 × 116.43 × 122.88 in (7.366 × 2.957 × 3.121 m) | `p5-us-ground-stryker-family-gdlsbrochure` | B | GDLS manufacturer combat envelope, which agrees with the Tier C compilation on all three axes for this variant |
| Shipping dimensions | 290 × 112.8 × 103.65 in (7.366 × 2.865 × 2.633 m) | `p5-us-ground-stryker-family-gdlsbrochure` | B | GDLS shipping envelope; length is unchanged between configurations on this variant while width and height are not |
| Combat weight | 42,000 lb (19,051 kg) | `p5-us-ground-stryker-m1130cv-afvdatabase` | C | Secondary combat-mass figure. Distinct from the 16.6 t listed configuration mass above, which excludes the communications fit |
| Dimensions (combat) | 290 × 116.43 × 122.88 in (7.40 × 2.957 × 3.121 m) | `p5-us-ground-stryker-m1130cv-afvdatabase` | C | Differs from the USACE row above; the two are different configurations and both are retained |
| Maximum level road speed | 60 mph (96 km/h) | `p5-us-ground-stryker-m1130cv-afvdatabase` | C | Variant-level road figure; off-road speed not published |
| Road range | approximately 330 mi (530 km) on roads | `p5-us-ground-stryker-m1130cv-afvdatabase` | C | Explicitly a road figure; cross-country range not published |
| Trench / vertical obstacle | 78 in (200 cm) / 23 in (58 cm) | `p5-us-ground-stryker-m1130cv-afvdatabase` | C | Cross-country obstacle envelope; configuration-dependent |
| Fording depth | 51 in (130 cm) | `p5-us-ground-stryker-m1130cv-afvdatabase` | C | Fording, not swimming; preparation requirements not stated |
| Grade / sideslope | 60% / 30% | `p5-us-ground-stryker-m1130cv-afvdatabase` | C | Slope limits as published; load-dependent in practice |
| Minimum turning diameter | 52 ft (16 m) | `p5-us-ground-stryker-m1130cv-afvdatabase` | C | Four-wheel steering geometry; measurement convention not stated |
| Crew (detailed) | 5-6 (commander, driver, three to four staff) | `p5-us-ground-stryker-m1130cv-afvdatabase` | C | Widens the draft crew figure above to the staff range the source states |
| Armament (detailed) | .50 cal M2HB or 40 mm Mk 19 MOD3 on the M151E2 remote weapon system; 2,000 or 480 rounds; 60 deg/s electric traverse | `p5-us-ground-stryker-m1130cv-afvdatabase` | C | Names the station and store loads the row above leaves unspecified |
| Public protection | Armored Stryker hull; exact thickness/level unknown | `p5-us-ground-stryker-army-wsh-2020` | A | Qualitative only |
| Hull armor maximum | welded high-hard steel structure, maximum 0.5 in (1.3 cm) | `p5-us-ground-stryker-m1130cv-afvdatabase` | C | Single maximum plate figure from a secondary source. It is not a protection rating, not an all-round value, and not an RHAe equivalence |

Field confidence follows the evidence tier and context column: direct variant statements are high confidence; mission/configuration context is medium confidence; `unknown` fields remain unestimated.

## Configuration Boundary

Rows carried from `p5-us-ground-stryker-m1130cv-afvdatabase` describe the command-vehicle configuration. The source records the 2010 double-V hull and the separate Stryker A1 upgrade (450 hp, 60,000 lb suspension, 910 A alternator, in-vehicle network) as distinct configurations; neither is merged into this record.

## Source References

- `p5-us-ground-stryker-usace-dims`
- `p5-us-ground-stryker-pm-atlss`
- `p5-us-ground-stryker-army-wsh-2020`
- `p5-us-ground-stryker-m1130cv-afvdatabase`
- `p5-us-ground-stryker-family-gdlsbrochure`
