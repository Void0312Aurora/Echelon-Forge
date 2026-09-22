# A400M Atlas C1

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/transport/strategic/a400m/a400m-c1/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-22`
Equipment ID: `eq-uk-air-a400m-c1`
Content status: parameter table complete for RAF Atlas C.1 research use; empty-weight readings remain an explicit unresolved secondary conflict, while the declared geometry, mass, propulsion, flight, crew, payload and mission-system fields are now covered by RAF/Airbus sources.

## Identity

- Family: A400M
- Variant: Atlas C.1
- Role: Tactical airlift and strategic oversize lift
- Manufacturer: Airbus Defence and Space
- Configuration scope: A400M as operated by the Royal Air Force as Atlas C.1. Airframe and performance figures are the common A400M values; no Atlas-specific modification is claimed.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| Royal Air Force | In service | `p5-uk-air-a400m-c1-raf` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Role | Tactical airlift and strategic oversize lift | `p5-uk-air-a400m-c1-raf` | A |
| Powerplant | Four EPI TP400-D6 turboprops, 8,200 kW each | `p5-uk-air-a400m-c1-raf`; `p5-uk-air-a400m-airbus-official` | A/B |
| Powerplant (manufacturer block) | Four Europrop International TP400-D6, 11,000 shp / 8,200 kW each | `p5-uk-air-a400m-airbus-official` | B |
| Thrust / power (RAF block) | 11,600 shp each | `p5-uk-air-a400m-c1-raf` | A |
| Cargo capacity | 37,000 kg (81,600 lb), stated as a representative load by the RAF source | `p5-uk-air-a400m-c1-raf` | A |
| Crew | Two pilots and one weapons systems operator | `p5-uk-air-a400m-c1-raf` | A |
| Length | 45.1 m (148 ft 0 in) | `p5-uk-air-a400m-airbus-official` | B |
| Length (RAF Atlas C.1 reading) | 42.2 m | `p5-uk-air-a400m-c1-raf` | A |
| Wingspan | 42.4 m (139 ft 1 in) | `p5-uk-air-a400m-airbus-official` | B |
| Height | 14.7 m (48 ft 3 in) | `p5-uk-air-a400m-airbus-official` | B |
| Wing area | 225.1 m² | `p5-uk-air-a400m-airbus-ukdefenceforum` | C |
| Empty weight | 76,500 kg per one source, described as an operating weight; 78,600 kg per two others | `p5-uk-air-a400m-airbus-ukdefenceforum` | C |
| Gross weight | 120,000 kg | `p5-uk-air-a400m-airbus-ukdefenceforum` | C |
| Maximum takeoff weight | 141,000 kg (310,850 lb) | `p5-uk-air-a400m-airbus-official` | B |
| Maximum landing weight | 123,000 kg | `p5-uk-air-a400m-airbus-official` | B |
| Fuel capacity | 50,500 kg internal | `p5-uk-air-a400m-airbus-ukdefenceforum` | C |
| Fuel capacity (manufacturer block) | 50,800 kg internal | `p5-uk-air-a400m-airbus-official` | B |
| Maximum cruise speed | 433 kt TAS; cruise Mach 0.68–0.72 | `p5-uk-air-a400m-airbus-official` | B |
| Range with maximum payload | 1,780 nmi (3,300 km) | `p5-uk-air-a400m-airbus-official` | B (conditioned) |
| Range with 30-tonne payload | 2,400 nmi (4,450 km) | `p5-uk-air-a400m-c1-raf`; `p5-uk-air-a400m-airbus-official` | A/B (conditioned) |
| Range with 20-tonne payload | 3,400 nmi (6,300 km) | `p5-uk-air-a400m-airbus-official` | B (conditioned) |
| Ferry range | 4,800 nmi (8,900 km) | `p5-uk-air-a400m-airbus-official` | B (conditioned) |
| Sensor / mission system | Civil weather radar with military ground mapping; defensive-aids suite; tactical airlift, airdrop and air-to-air refuelling capability | `p5-uk-air-a400m-c1-raf`; `p5-uk-air-a400m-airbus-official` | A/B |
| Troop and medical capacity | 116 fully equipped troops or paratroopers; up to 66 stretchers with 25 medical personnel | `p5-uk-air-a400m-c1-raf` | A |
| Cargo compartment | 4.00 m wide, 3.85 m high, 17.71 m long, with a further 5.40 m without the ramp | `p5-uk-air-a400m-airbus-official` | B |

## Configuration Boundary

The RAF source supplies the Atlas C.1 role, engine/thrust, RAF-specific length, speed, crew, payload configurations, radar and defensive-aids context. The Airbus brochure supplies common A400M dimensions, weights, fuel, propulsion, altitude, speed and conditioned ranges. The older forum compilation remains only as a named secondary cross-check for the empty-weight conflict and earlier geometry block.

Empty weight carries two readings, 76,500 kg and 78,600 kg, a spread larger than rounding. The first is described as an operating weight rather than a bare empty weight, which may account for the difference, but no source states that, so both are recorded and neither is preferred.

The Atlas C.1 and the A400M designation are the same airframe under a national service name. No value is carried from any other leaf.

## Source References

- `p5-uk-air-a400m-c1-raf`: `raw/sources/royal_air_force/p5-uk-air-a400m-c1-raf/manifest.md`
- `p5-uk-air-a400m-airbus-official`: `raw/sources/airbus/p5-uk-air-a400m-airbus-official/manifest.md` — manufacturer common A400M dimensions, weights, fuel, performance and ranges
- `p5-uk-air-a400m-airbus-ukdefenceforum`: `raw/sources/uk_defence_forum/p5-uk-air-a400m-airbus-ukdefenceforum/manifest.md`
