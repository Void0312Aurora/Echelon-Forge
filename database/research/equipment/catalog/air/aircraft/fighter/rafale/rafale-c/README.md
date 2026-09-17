# Rafale C

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/rafale/rafale-c/README.md`
Owner: `database/equipment-data`
Last verified: `not established`
Equipment ID: `eq-fr-air-rafale-c`
Content status: Model-level draft with first-party geometry and payload data.

## Identity

- Family: Rafale
- Variant: Rafale C
- Role: Multirole fighter
- Operator baseline: French Air and Space Force

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| France | In service | `p5-fr-air-rafale-dassault` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Wingspan | 10.9 m | `p5-fr-air-rafale-dassault` | A |
| Length | 15.3 m | `p5-fr-air-rafale-dassault` | A |
| Height | 5.3 m | `p5-fr-air-rafale-dassault` | A |
| Empty weight | Approximately 10 t | `p5-fr-air-rafale-dassault` | A |
| Maximum takeoff weight | 24.5 t | `p5-fr-air-rafale-dassault` | A |
| External stores capacity | 9.5 t | `p5-fr-air-rafale-dassault` | A |
| Length | 15.27 m (50 ft 1 in) | `p5-fr-air-rafale-aviationist` | C |
| Wingspan | 10.90 m (35 ft 9 in) | `p5-fr-air-rafale-aviationist` | C |
| Height | 5.34 m (17 ft 6 in) | `p5-fr-air-rafale-aviationist` | C |
| Empty weight | 9,850 kg (21,720 lb) for the Rafale C | `p5-fr-air-rafale-aviationist` | C |
| Gross weight | 15,000 kg (33,069 lb) | `p5-fr-air-rafale-aviationist` | C |
| Maximum takeoff weight | 24,500 kg (54,013 lb) | `p5-fr-air-rafale-aviationist` | C |
| Internal fuel | 4,700 kg (10,362 lb) for the Rafale C | `p5-fr-air-rafale-aviationist` | C |
| Powerplant | Two Snecma M88-4e turbofans, 50.04 kN dry each | `p5-fr-air-rafale-aviationist` | C |
| Armament | One 30 mm GIAT 30 autocannon and up to 9,500 kg of external stores | `p5-fr-air-rafale-aviationist` | C |
| Crew | One for the Rafale C | `p5-fr-air-rafale-aviationist` | C |

## Source References

- `p5-fr-air-rafale-dassault`: `raw/sources/dassault_aviation/p5-fr-air-rafale-dassault/manifest.md` — manufacturer geometry, masses and payload
- `p5-fr-air-rafale-aviationist`: `raw/sources/the_aviationist/p5-fr-air-rafale-aviationist/manifest.md` — variant table, per-mark empty weight, fuel and armament

## Configuration Boundary

The manufacturer page gives rounded corporate figures: 10.9 m, 15.3 m, 5.3 m, approximately 10 t, 24.5 t and 9.5 t. The variant table gives two decimal places on the same dimensions and a per-mark empty weight, so the two sets are recorded side by side rather than reconciled. Neither is preferred and the leaf does not average them.

The empty weight is the row where the two readings differ most: the manufacturer rounds to 10 t and the variant table separates the three marks and gives 9,850 kg for the C. The C value is recorded from the table because it is variant-specific, and the manufacturer's rounded figure is retained as the type-level reading.

A maximum speed of 1,912 km/h that an earlier revision of this leaf carried is withdrawn, because the figure came from a comparison that named no artifact and none could be re-located. No package held for this leaf states a maximum speed.

The Rafale B and Rafale M are separate marks with their own leaves. The B and M empty weights in the variant table are not carried here.
