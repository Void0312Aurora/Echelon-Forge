# Y-20

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/transport/strategic/y-20/y-20/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-25`
Equipment ID: `eq-cn-air-y20`
Content status: `parameter-complete` research record; public values remain Tier C and are not a runtime configuration.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| PLA Air Force | In service | `p5-cn-air-y20-mnd` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Role | Large military transport aircraft | `p5-cn-air-y20-mnd` | A |
| Public characteristics | Long range, heavy payload capacity and high speed | `p5-cn-air-y20-mnd` | A |
| Length | 47 m (154 ft 2 in) | `p5-cn-air-y20-compiled` | C |
| Wingspan | 50 m (164 ft 1 in) | `p5-cn-air-y20-compiled` | C |
| Height | 15 m (49 ft 3 in) | `p5-cn-air-y20-compiled` | C |
| Empty weight | 100,000 kg (220,462 lb) | `p5-cn-air-y20-compiled` | C |
| Maximum takeoff weight | 220,000 kg (485,017 lb) | `p5-cn-air-y20-compiled` | C |
| Maximum payload | 66 t for the Y-20A | `p5-cn-air-y20-compiled` | C |
| Public payload reading | Up to 66 t for generic Y-20 | `p5-cn-air-y20-snl` | C |
| Powerplant | Four Shenyang WS-20 turbofans on the Y-20B; four D-30KP-2 on the earlier airframes | `p5-cn-air-y20-compiled` | C |
| Engine thrust reading | 122.0 kN each | `p5-cn-air-y20-snl` | C |
| Crew | 3 (pilot, co-pilot and loadmaster) | `p5-cn-air-y20-militaryfactory` | C |
| Cruise speed | 690 km/h | `p5-cn-air-y20-militaryfactory` | C |
| Maximum speed | 920 km/h | `p5-cn-air-y20-snl`; `p5-cn-air-y20-militaryfactory` | C |
| Service ceiling | 13,000 m | `p5-cn-air-y20-militaryfactory` | C |
| Conditioned range | 10,000 km unladen; 7,800 km with 40 t payload; 4,500 km with maximum payload | `p5-cn-air-y20-snl` | C |
| In-service inventory | 55 Y-20 transports, 30 YY-20A and 10 YY-20B recorded as of 2026 | `p5-cn-air-y20-compiled` | C |

## Configuration Boundary

The official source held here supplies the role and the public characteristics at Tier A. It does not publish a complete technical table. The SNL and Military Factory packages are generic Y-20 secondary readings and close the public speed, range, crew and ceiling fields without being treated as official certification.

That package previously described itself as a compilation of several entries while naming one URL. Its publisher and title now name the single article, so each row above is traceable to that article rather than to a group of unnamed carriers, and the 66 t payload is recorded as that article's statement rather than as a shared figure.

The powerplant differs across the family and is not merged: four Shenyang WS-20 turbofans in the B configuration against four D-30KP-2 in the earlier configuration. The 122.0 kN thrust row is retained as a generic public reading; it does not decide which engine fit belongs to a particular airframe.

The SNL package reports a 45 m wingspan while the compiled package and Military Factory report 50 m. Both readings remain visible; neither is silently promoted to a certified dimension.

The Y-20, Y-20A, Y-20B, YY-20A and YY-20B are separate configurations. The tanker variants are recorded on their own leaf and their fuel and payload figures are not carried here.

## Source References

- `p5-cn-air-y20-mnd`: `raw/sources/prc_ministry_of_national_defense/p5-cn-air-y20-mnd/manifest.md` — programme and role context
- `p5-cn-air-y20-compiled`: `raw/sources/compiled_secondary/p5-cn-air-y20-compiled/manifest.md` — dimensions, masses, payload, powerplant split and inventory
- `p5-cn-air-y20-snl`: `raw/sources/store_norske_leksikon/p5-cn-air-y20-snl/manifest.md` — generic Y-20 public performance and payload-conditioned range
- `p5-cn-air-y20-militaryfactory`: `raw/sources/military_factory/p5-cn-air-y20-militaryfactory/manifest.md` — generic Y-20 crew and flight-envelope cross-check
