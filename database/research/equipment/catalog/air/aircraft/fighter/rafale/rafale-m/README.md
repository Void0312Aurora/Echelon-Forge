# Rafale M

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/rafale/rafale-m/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-22`
Equipment ID: `eq-fr-air-rafale-m`
Content status: parameter table complete for the single-seat carrier Rafale M; common Rafale performance values and M-specific naval mass/crew context retain their scopes.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| France | In service | `p5-fr-air-rafale-m-dassault` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Variant | Single-seat carrier-capable Rafale | `p5-fr-air-rafale-m-dassault` | A |
| Wingspan | 10.9 m | `p5-fr-air-rafale-m-dassault` | A |
| Length | 15.3 m | `p5-fr-air-rafale-m-dassault` | A |
| Height | 5.3 m | `p5-fr-air-rafale-m-dassault` | A |
| Empty weight | Approximately 10.5 t | `p5-fr-air-rafale-m-dassault` | A |
| Maximum takeoff weight | 24.5 t | `p5-fr-air-rafale-m-dassault` | A |
| External stores capacity | 9.5 t | `p5-fr-air-rafale-m-dassault` | A |
| Length (variant table) | 15.27 m (50 ft 1 in) | `p5-fr-air-rafale-aviationist` | C |
| Wingspan (variant table) | 10.90 m (35 ft 9 in) | `p5-fr-air-rafale-aviationist` | C |
| Height (variant table) | 5.34 m (17 ft 6 in) | `p5-fr-air-rafale-aviationist` | C |
| Empty weight (variant reading) | 10,600 kg (23,400 lb) for the Rafale M | `p5-fr-air-rafale-aviationist` | C |
| Gross weight | 15,000 kg (33,069 lb) | `p5-fr-air-rafale-aviationist` | C |
| Powerplant | Two Snecma M88-4e turbofans, 50.04 kN dry each | `p5-fr-air-rafale-aviationist` | C |
| Maximum thrust | 2 x 7.5 t | `p5-fr-air-rafale-m-dassault` | A (family-level) |
| Internal fuel | 4.7 t (10,300 lb), common family block | `p5-fr-air-rafale-m-dassault` | A (family-level) |
| External fuel | Up to 6.7 t (14,700 lb) | `p5-fr-air-rafale-m-dassault` | A (family-level) |
| Maximum speed | Mach 1.8 / 750 kt | `p5-fr-air-rafale-m-dassault` | A (family-level) |
| Service ceiling | 50,000 ft | `p5-fr-air-rafale-m-dassault` | A (family-level) |
| Limit load factor | -3.2g / +9g | `p5-fr-air-rafale-m-dassault` | A (family-level) |
| Crew | One | `p5-fr-air-rafale-aviationist` | C |
| Store stations | 13 on the Rafale M | `p5-fr-air-rafale-adapt-dassault` | A (variant-specific) |
| Armament | One 30 mm Nexter 30M791 cannon; cleared stores include METEOR, MICA, HAMMER, SCALP, AM39 Exocet and guided/unguided bombs | `p5-fr-air-rafale-adapt-dassault`; `p5-fr-air-rafale-aviationist` | A/C |

## Configuration Boundary

The Dassault Marine block identifies the single-seat carrier-capable mark and publishes approximately 10.5 t empty weight, rounded dimensions, maximum takeoff weight and external stores. The Aviationist table supplies the M-specific 10,600 kg empty-weight and one-crew readings, plus the common engine context. The official adaptation page's 13-store-station count is retained for the M rather than copying the 14-station Air count.

The common performance rows are labelled family-level because the retained manufacturer specification page does not publish a separate M-only speed, ceiling or thrust. Carrier operation is a configuration boundary, not a reason to replace the common family figures with Air B/C values.

## Source References

- `p5-fr-air-rafale-m-dassault`: `raw/sources/dassault_aviation/p5-fr-air-rafale-m-dassault/manifest.md` — official Marine and common performance blocks
- `p5-fr-air-rafale-adapt-dassault`: `raw/sources/dassault_aviation/p5-fr-air-rafale-adapt-dassault/manifest.md` — hard points, weapon-system and armament context
- `p5-fr-air-rafale-aviationist`: `raw/sources/the_aviationist/p5-fr-air-rafale-aviationist/manifest.md` — per-mark M readings and engine/armament context
