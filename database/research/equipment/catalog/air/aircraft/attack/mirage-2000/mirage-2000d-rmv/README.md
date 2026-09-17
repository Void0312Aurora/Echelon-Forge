# Mirage 2000D RMV

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/attack/mirage-2000/mirage-2000d-rmv/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-18`
Equipment ID: `eq-fr-air-mirage2000d-rmv`
Content status: parameter table present with per-field source and confidence. Status is `cataloged`, not `parameter_complete`, because powerplant and performance figures are not established from the held sources.

## Identity

- Family: Mirage 2000
- Variant: 2000D Rmv
- Role: Two-seat ground-attack aircraft
- Manufacturer: Dassault Aviation
- Configuration scope: the Rmv mid-life renovation changes mission systems, sensors and weapons integration rather than the airframe, so the geometry and mass rows below are airframe values that apply across the 2000D standard.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| French Air and Space Force | In service | `p5-fr-air-mirage2000d-rmv` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Wingspan | 9.1 m | `p5-fr-air-mirage2000d-rmv-dassault` | B |
| Length | 14.3 m | `p5-fr-air-mirage2000d-rmv-dassault` | B |
| Height | 5.4 m | `p5-fr-air-mirage2000d-rmv-dassault` | B |
| Empty weight | 8 t | `p5-fr-air-mirage2000d-rmv-dassault` | B |
| Maximum takeoff weight | 16.5 t per the manufacturer; 17,000 kg (37,500 lb) per the Tier C specification compilation | `p5-fr-air-mirage2000d-rmv-dassault`; `p5-fr-air-mirage2000-gs` | B/C | Two readings retained, not reconciled: the manufacturer states a rounded 16.5 t while the compilation states 17,000 kg against the single-seat baseline. The two may use different weight definitions |
| External stores capacity | 5.7 t per the manufacturer; 6,300 kg per the Tier C compilation | `p5-fr-air-mirage2000d-rmv-dassault`; `p5-fr-air-mirage2000-gs` | B/C | Two readings retained; the difference is not resolved |
| Length (two-seat airframe) | 14.55 m against 14.36 m for the single-seat airframe | `p5-fr-air-mirage2000-gs` | C | The applicable value for the 2000D. The compilation states that two-seat and strike variants differ marginally in dimensions |
| Internal fuel capacity (single-seat baseline) | 3,080 kg (6,790 lb) | `p5-fr-air-mirage2000-gs` | C | Stated for the single-seat 2000C baseline; the compilation warns that the two-seat and strike variants differ in fuel capacity, so this is not asserted as a 2000D value |
| Powerplant | One SNECMA M53-P2 single-spool afterburning turbofan; 54 kN (12,000 lbf) dry and 95 kN (21,400 lbf) with afterburner | `p5-fr-air-mirage2000-gs` | C | The M53-P2 is fitted across the single-seat and two-seat Mirage 2000 family, and the compiling source lists the B, D and N variants together as the two-seat airframes. No 2000D-specific engine variant is claimed |
| Powerplant (independent reading) | Same SNECMA M53-P2; 64.3 kN (14,455 lbf) dry and 95.1 kN (21,379 lbf) with afterburner | `p5-fr-air-mirage2000d-flugzeuginfo` | C | A second package states the same engine model and the same variant split, giving the 2000D as the two-seat fighter-bomber variant. Its dry figure is 10.3 kN above the compilation's 54 kN and its afterburner figure is 0.1 kN above the compilation's 95 kN. Both readings are retained and the dry-thrust conflict is not resolved |
| Maximum speed | Mach 2.2 (2,340 km/h) at altitude; 1,350 km/h at sea level | `p5-fr-air-mirage2000-gs` | C | Family performance value stated for the single-seat 2000C with combat load |
| Maximum speed (independent reading) | 2,334 km/h | `p5-fr-air-mirage2000d-flugzeuginfo` | C | Single-seat baseline reading, 6 km/h below the compilation's 2,340 km/h. Both are retained |
| Service ceiling (independent reading) | 17,983 m (59,000 ft) | `p5-fr-air-mirage2000d-flugzeuginfo` | C | Single-seat baseline reading, 923 m above the compilation's 17,060 m. Both are retained |
| Service ceiling | 17,060 m (56,000 ft) | `p5-fr-air-mirage2000-gs` | C | Family performance value |
| Combat radius | 1,550 km (960 mi) | `p5-fr-air-mirage2000-gs` | C | Family performance value |
| Ferry range | 3,335 km (2,070 mi) with auxiliary fuel | `p5-fr-air-mirage2000-gs` | C | Family performance value |
| Rate of climb | 285 m/s at sea level | `p5-fr-air-mirage2000-gs` | C | Family performance value |
| Load limits | +9.0 / −4.5 g | `p5-fr-air-mirage2000-gs` | C | Family performance value; represents the airframe limit rather than a mission profile |
| Hardpoints | 9, five fuselage and four wing | `p5-fr-air-mirage2000-gs` | C | Family structural value, applicable to the two-seat airframe |

For every row where two sources are named, both are recorded and neither is treated as a more precise version of the other, because the manufacturer's rounding and the compilation's weight definitions may not describe the same quantity.

## Configuration Boundary

The manufacturer states rounded figures in a corporate report: 9.1 m, 14.3 m, 8 t, 16.5 t, 5.7 t. The Tier C specification compilation gives a two-seat length of 14.55 m, a maximum takeoff weight of 17,000 kg and an external stores capacity of 6,300 kg. The two sets are recorded side by side rather than reconciled.

The compilation is written for the single-seat 2000C baseline and states its own caveat that two-seat and strike variants differ marginally in dimensions and fuel capacity. Its performance and armament blocks are therefore recorded as family values on the single-seat baseline and are not asserted as 2000D measurements.

A second package, `p5-fr-air-mirage2000d-flugzeuginfo`, states the same engine model and names the 2000D explicitly as the two-seat fighter-bomber variant. It supplies an independent powerplant reading and two further family performance readings, so the engine fit and the performance envelope now rest on two publishers rather than one. The dry-thrust split is the widest disagreement this opened: 54 kN against 64.3 kN for the same engine. It is recorded and not resolved, because the two packages may be describing different ratings and neither states which.

The performance rows remain single-seat-baseline values from both packages. The 2000D is a two-seat airframe with its own stores and mission fit, and no package held here states a 2000D-measured speed, ceiling or radius, so the leaf does not present these as such.

The Mirage 2000D is a two-seat airframe whose length differs from the single-seat 2000C and 2000-5F. Values must not be carried between those leaves.

The French Ministry of the Armed Forces source held for this leaf is a news article about a Djibouti deployment and carries no specification table. It is retained for operator context only.

## Source References

- `p5-fr-air-mirage2000d-rmv-dassault`: `raw/sources/dassault_aviation/p5-fr-air-mirage2000d-rmv-dassault/manifest.md`
- `p5-fr-air-mirage2000-gs`: `raw/sources/globalsecurity/p5-fr-air-mirage2000-gs/manifest.md`
- `p5-fr-air-mirage2000d-flugzeuginfo`: `raw/sources/flugzeuginfo/p5-fr-air-mirage2000d-flugzeuginfo/manifest.md` — independent powerplant and performance readings
- `p5-fr-air-mirage2000d-rmv`: `raw/sources/ministere_des_armees/p5-fr-air-mirage2000d-rmv/manifest.md` — operator context only, no parameter rows
