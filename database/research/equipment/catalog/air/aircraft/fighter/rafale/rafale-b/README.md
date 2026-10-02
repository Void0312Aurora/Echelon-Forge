# Rafale B

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/rafale/rafale-b/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-22`
Equipment ID: `eq-fr-air-rafale-b`
Content status: parameter table complete for the twin-seat Rafale B; common Rafale performance values are marked family-level and B-specific values remain separately sourced.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| France | In service | `p5-fr-air-rafale-b-dassault` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Variant | Twin-seat land-based Rafale | `p5-fr-air-rafale-b-dassault` | A |
| Wingspan | 10.9 m | `p5-fr-air-rafale-b-dassault` | A |
| Length | 15.3 m | `p5-fr-air-rafale-b-dassault` | A |
| Height | 5.3 m | `p5-fr-air-rafale-b-dassault` | A |
| Empty weight | Approximately 10 t | `p5-fr-air-rafale-b-dassault` | A |
| Maximum takeoff weight | 24.5 t | `p5-fr-air-rafale-b-dassault` | A |
| External stores capacity | 9.5 t | `p5-fr-air-rafale-b-dassault` | A |
| Length (variant table) | 15.27 m (50 ft 1 in) | `p5-fr-air-rafale-aviationist` | C |
| Wingspan (variant table) | 10.90 m (35 ft 9 in) | `p5-fr-air-rafale-aviationist` | C |
| Height (variant table) | 5.34 m (17 ft 6 in) | `p5-fr-air-rafale-aviationist` | C |
| Empty weight (variant reading) | 10,300 kg (22,708 lb) for the Rafale B | `p5-fr-air-rafale-aviationist` | C |
| Gross weight | 15,000 kg (33,069 lb) | `p5-fr-air-rafale-aviationist` | C |
| Powerplant | Two Snecma M88-4e turbofans, 50.04 kN dry each | `p5-fr-air-rafale-aviationist` | C |
| Maximum thrust | 2 x 7.5 t | `p5-fr-air-rafale-b-dassault` | A (family-level) |
| Internal fuel | 4.4 t (9,700 lb) for the Rafale B | `p5-fr-air-rafale-aviationist` | C |
| External fuel | Up to 6.7 t (14,700 lb) | `p5-fr-air-rafale-b-dassault` | A (family-level) |
| Maximum speed | Mach 1.8 / 750 kt | `p5-fr-air-rafale-b-dassault` | A (family-level) |
| Service ceiling | 50,000 ft | `p5-fr-air-rafale-b-dassault` | A (family-level) |
| Limit load factor | -3.2g / +9g | `p5-fr-air-rafale-b-dassault` | A (family-level) |
| Crew | Two | `p5-fr-air-rafale-aviationist` | C |
| Store stations | 14 total, 5 heavy-wet | `p5-fr-air-rafale-b-dassault` | A (family-level) |
| Armament | One 30 mm Nexter 30M791 cannon; cleared stores include METEOR, MICA, HAMMER, SCALP, AM39 Exocet and guided/unguided bombs | `p5-fr-air-rafale-adapt-dassault`; `p5-fr-air-rafale-aviationist` | A/C |

## Configuration Boundary

The Dassault Air B block identifies the twin-seat land-based mark and publishes the rounded family geometry, mass, stores and performance values. The Aviationist table supplies the B-specific 10,300 kg empty-weight, 4,400 kg internal-fuel and two-crew readings, plus the common engine and cannon description. No Rafale C or M-only value is substituted for a B row.

The common performance rows are intentionally labelled family-level: Dassault does not publish a separate B-only speed, ceiling or thrust in the retained page. The B is a land-based training/operational mark; carrier-only configuration claims belong to the M leaf.

## Source References

- `p5-fr-air-rafale-b-dassault`: `raw/sources/dassault_aviation/p5-fr-air-rafale-b-dassault/manifest.md` — official Air B and common performance blocks
- `p5-fr-air-rafale-adapt-dassault`: `raw/sources/dassault_aviation/p5-fr-air-rafale-adapt-dassault/manifest.md` — hard points, weapon-system and armament context
- `p5-fr-air-rafale-aviationist`: `raw/sources/the_aviationist/p5-fr-air-rafale-aviationist/manifest.md` — per-mark B readings and engine/armament context
