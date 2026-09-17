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
| Maximum takeoff weight | 16.5 t per the manufacturer; 17,000 kg per reference works | `p5-fr-air-mirage2000d-rmv-dassault` | B/C |
| External stores capacity | 5.7 t | `p5-fr-air-mirage2000d-rmv-dassault` | B |
| Length (two-seat airframe, reference-works value) | 14.55 m against 14.36 m for the single-seat airframe | `p5-fr-air-mirage2000d-rmv-dassault` | C |
| Powerplant | Not established from the held sources | — | — |
| Performance (speed, ceiling, range) | Not established from the held sources | — | — |

## Configuration Boundary

The manufacturer states rounded figures in a corporate report: 9.1 m, 14.3 m, 8 t, 16.5 t. Reference works give a two-seat length of 14.55 m and a maximum takeoff weight of 17,000 kg. The two sets are recorded side by side rather than reconciled, because the manufacturer's rounding and the reference works' weight definition may not describe the same quantity. The manufacturer values are not treated as a more precise version of the reference values.

A configuration note carried from the Tiger leaf experience: the 2000D is a two-seat airframe and its length differs from the single-seat 2000C and 2000-5F. Values must not be carried between those leaves.

The French Ministry of the Armed Forces source held for this leaf is a news article about a Djibouti deployment and carries no specification table. It is retained for operator context only.

## Source References

- `p5-fr-air-mirage2000d-rmv-dassault`: `raw/sources/dassault_aviation/p5-fr-air-mirage2000d-rmv-dassault/manifest.md`
- `p5-fr-air-mirage2000d-rmv`: `raw/sources/ministere_des_armees/p5-fr-air-mirage2000d-rmv/manifest.md` — operator context only, no parameter rows
