# M1129 Mortar Carrier

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/stryker/m1129-mc/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-stryker-m1129-mc` |
| Family / variant | Stryker / M1129 MC |
| Hull context | Legacy mortar-carrier configuration |
| Role | Mounted indirect fire and obscuration |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Listed configuration mass | 16.9 t | `p5-us-ground-stryker-usace-dims` | A | Source table configuration; not a universal combat mass |
| Length × width × height | 7.29 × 2.72 × 2.69 m | `p5-us-ground-stryker-usace-dims` | A | Mortar and stowage configuration context |
| Crew | 5 | `p5-us-ground-mortar-atp-3-21-90` | A | Mortar-section configuration; exact vehicle seating not further normalized |
| Mortar system | RMS6-L 120 mm mortar | `p5-us-ground-mortar-atp-3-21-90` | A | System designation retained as cited |
| Ammunition / fire mission | HE, illumination, smoke and precision-guided mortar mission types | `p5-us-ground-mortar-atp-3-21-90` | A | Exact carried round count unknown |
| Mortar ammunition load | 48 or 60 × 120 mm rounds depending on sub-configuration; battalion platoon vehicles added a dismountable 81 mm M252 and company platoon vehicles a dismountable 60 mm M224 | `p5-us-ground-stryker-m1129mc-afvdatabase` | C | Resolves the round count left unknown above. The load stated here is the MC-B configuration |
| Engine designation | Caterpillar 3126, six-cylinder four-cycle inline turbocharged diesel, 350 hp at 2,500 rpm | `p5-us-ground-stryker-m1129mc-afvdatabase` | C | Secondary-sourced designation; the A1 450 hp rating is not merged |
| Transmission | Allison MD 3066P, six forward and one reverse | `p5-us-ground-stryker-m1129mc-afvdatabase` | C | Secondary source; shift schedule and torque curve not public |
| Fuel capacity | 53 gal (200 L) | `p5-us-ground-stryker-m1129mc-afvdatabase` | C | Secondary source; usable reserve fraction not stated |
| Combat weight | 41,367 lb (18,764 kg) for MC-B; 39,990 lb (18,140 kg) loaded for MC-A | `p5-us-ground-stryker-m1129mc-afvdatabase` | C | Both sub-variants retained separately. Neither is the 16.9 t listed configuration mass above |
| Dimensions (combat, MC-B) | 297 × 153 × 125 in (7.54 × 3.89 × 3.18 m) | `p5-us-ground-stryker-family-gdlsbrochure` | B | GDLS manufacturer combat envelope for the mortar carrier, which agrees with the Tier C compilation on all three axes. The brochure does not separate MC-A from MC-B |
| Dimensions (shipping, MC-B) | 287 × 107 × 106 in (7.29 × 2.72 × 2.69 m) | `p5-us-ground-stryker-family-gdlsbrochure` | B | GDLS shipping envelope. The length coincides with the USACE listed-configuration length above, which is a configuration coincidence and not the same measurement |
| Maximum level road speed | 60 mph (96 km/h) | `p5-us-ground-stryker-m1129mc-afvdatabase` | C | Variant-level road figure; off-road speed not published |
| Road range | approximately 330 mi (530 km) on roads | `p5-us-ground-stryker-m1129mc-afvdatabase` | C | Explicitly a road figure; cross-country range not published |
| Trench / vertical obstacle | 78 in (200 cm) / 23 in (58 cm) | `p5-us-ground-stryker-m1129mc-afvdatabase` | C | Cross-country obstacle envelope; configuration-dependent |
| Fording depth | 51 in (130 cm) | `p5-us-ground-stryker-m1129mc-afvdatabase` | C | Fording, not swimming; preparation requirements not stated |
| Grade / sideslope | 60% / 30% | `p5-us-ground-stryker-m1129mc-afvdatabase` | C | Slope limits as published; load-dependent in practice |
| Minimum turning diameter | 52 ft (16 m) | `p5-us-ground-stryker-m1129mc-afvdatabase` | C | Four-wheel steering geometry; measurement convention not stated. 16 m is the correct rounding of 52 ft (15.85 m) |
| Secondary armament | 7.62 mm M240B on the commander's cupola with 2,000 rounds | `p5-us-ground-stryker-m1129mc-afvdatabase` | C | MC-B fit; the source notes the MC-B lacked the remote weapon system and used a skate mount |
| Mission systems | Mortar fire-control and communications context | `p5-us-ground-mortar-atp-3-21-90` | A | Sensor, FCS and network performance unknown |
| Mission systems (M95 FCS) | M95 mortar fire-control system connected to digital battlefield networks, computing fire missions on the move | `p5-us-ground-stryker-m1129mc-afvdatabase` | C | Names the fire-control system; computation latency not published |
| Public protection | Armored Stryker hull; exact thickness/level unknown | `p5-us-ground-stryker-army-wsh-2020` | A | Qualitative only |
| Hull armor maximum | welded high-hard steel structure, maximum 0.5 in (1.3 cm) | `p5-us-ground-stryker-m1129mc-afvdatabase` | C | Single maximum plate figure from a secondary source. It is not a protection rating, not an all-round value, and not an RHAe equivalence |

Field confidence follows the evidence tier and context column: direct mortar-system statements are high confidence; configuration-sensitive statements are medium confidence; `unknown` fields remain unestimated.

## Configuration Boundary

The page distinguishes MC-A, the ICV-like carrier that could not fire mounted, from MC-B, fielded late 2005 with the recoiling RMS6-L. The mass figures for both are retained above as separate values. The source records the 2010 double-V hull and the separate Stryker A1 upgrade (450 hp, 60,000 lb suspension, 910 A alternator, in-vehicle network) as distinct configurations; neither is merged into this record.

## Source References

- `p5-us-ground-stryker-usace-dims`
- `p5-us-ground-mortar-atp-3-21-90`
- `p5-us-ground-stryker-army-wsh-2020`
- `p5-us-ground-stryker-m1129mc-afvdatabase`
- `p5-us-ground-stryker-family-gdlsbrochure`
