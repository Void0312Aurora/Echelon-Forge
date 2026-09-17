# Atlantique 2

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/maritime_patrol/atlantique-2/atlantique-2/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-17`
Equipment ID: `eq-fr-air-atl2`
Content status: parameter table present with per-field source and confidence. Retrieval status is recorded per package in each manifest's `Retrieval:` block. This leaf previously carried no parameter table at all; the table below was built on 2026-09-17.

## Identity

- Family: Bréguet 1150 Atlantic
- Variant: Atlantique 2 (ATL2)
- Role: Long-range maritime patrol, anti-submarine and anti-surface warfare
- Manufacturer: Dassault-Breguet, now Dassault Aviation
- Configuration scope: the Atlantique 2 as operated by the French Navy. The ATL1 and the proposed ATL3 are separate configurations and no value is carried between them.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| French Navy | In service | `p5-fr-air-atl2` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Primary missions | Anti-submarine and anti-surface warfare, long-range maritime patrol | `p5-fr-air-atl2` | A |
| Length | 103 ft 9 in (31.62 m calculated) | `p5-fr-air-atl2-militaryfactory` | C |
| Wingspan | 37.42 m (122 ft 9 in), including wingtip pods | `p5-fr-air-atl2-encyclopedic` | C |
| Height | 10.89 m (35 ft 9 in) | `p5-fr-air-atl2-encyclopedic` | C |
| Wing area | 120.34 m² (1,295.3 sq ft) | `p5-fr-air-atl2-encyclopedic` | C |
| Empty weight | 25,700 kg (56,659 lb) | `p5-fr-air-atl2-seaforces` | C |
| Gross weight | 45,000 kg (99,208 lb) | `p5-fr-air-atl2-seaforces` | C |
| Maximum takeoff weight | 46,200 kg (101,854 lb) | `p5-fr-air-atl2-seaforces` | C |
| Powerplant | Two Rolls-Royce Tyne RTy.20 Mk 21 two-spool turboprops | `p5-fr-air-atl2-seaforces` | C |
| Engine power | 4,500 kW (6,100 shp) each, stated as equivalent | `p5-fr-air-atl2-seaforces` | C |
| Maximum speed | 648 km/h (403 mph, 350 kn) | `p5-fr-air-atl2-seaforces` | C |
| Patrol cruise speed | 315 km/h (196 mph, 170 kn) | `p5-fr-air-atl2-seaforces` | C |
| Endurance | 18 hours | `p5-fr-air-atl2-seaforces` | C |
| Service ceiling | 9,145 m (30,003 ft) | `p5-fr-air-atl2-seaforces` | C |
| Armament | Up to 3,500 kg (7,700 lb), including torpedoes, depth charges, mines, anti-ship missiles and bombs | `p5-fr-air-atl2-seaforces` | C |
| Crew | Twelve, including two pilots, a flight engineer, forward observer, communications specialist, ECM systems specialist, radar and IFF operator, and tactical coordinator | `p5-fr-air-atl2-militaryfactory` | C |

## Configuration Boundary

This leaf carried no parameter table before 2026-09-17. The official French source held for it states the operator and the mission set and no dimension, mass or performance figure, which is why every technical row is Tier C.

Four packages carry the rows and each was retrieved on 2026-09-17:
- `p5-fr-air-atl2-seaforces` is the source of record for the masses, the engine, the performance figures, the endurance and the armament.
- `p5-fr-air-atl2-encyclopedic` supplies the metric geometry readings, from a block the article itself heads `Specifications (Atlantique 2)`.
- `p5-fr-air-atl2-militaryfactory` supplies the length and the crew, and states the wingspan, height and wing area in imperial units that agree with the metric readings.
- `p5-fr-air-atl2-dassault` locates the manufacturer's own Atlantique 2 characteristics page, which is the correct artifact for these rows. It carries no value yet because the page fetch returned navigation only, and no row cites it.

The length is the one row with a single source. Military Factory gives 103 ft 9 in and no other package gives a length, so the metric value of 31.62 m beside it is this tree's arithmetic from the imperial figure rather than a published reading. It is labelled as calculated.

The empty weight carries two imperial readings, 56,659 lb on two packages and 56,660 lb on the third, which is a one-pound rounding difference on the same metric value of 25,700 kg. The row records the metric value and one imperial reading.

The ATL2 is not the ATL1 and not the proposed ATL3. The ATL3 figures published by a separate source, 46.5 t maximum take-off weight and a 10,000 m ceiling, are not carried here.

## Source References

- `p5-fr-air-atl2`: `raw/sources/ministere_des_armees/p5-fr-air-atl2/manifest.md` — operator and mission context
- `p5-fr-air-atl2-seaforces`: `raw/sources/seaforces/p5-fr-air-atl2-seaforces/manifest.md` — masses, engine, performance, endurance, armament
- `p5-fr-air-atl2-encyclopedic`: `raw/sources/wikipedia/p5-fr-air-atl2-encyclopedic/manifest.md` — metric geometry
- `p5-fr-air-atl2-militaryfactory`: `raw/sources/military_factory/p5-fr-air-atl2-militaryfactory/manifest.md` — length and crew
- `p5-fr-air-atl2-dassault`: `raw/sources/dassault_aviation/p5-fr-air-atl2-dassault/manifest.md` — manufacturer locator, no value yet
