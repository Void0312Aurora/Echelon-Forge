# YY-20A

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/tanker/yy-20/yy-20a/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-24`
Equipment ID: `eq-cn-air-yy20a`
Content status: parameter table present with per-field source and confidence. Status is `parameter_complete`; all declared simulation fields are populated, with powerplant, geometry and fuel readings retained by source and variant.

## Identity

- Family: Y-20
- Variant: YY-20A, also designated Y-20U
- Role: Aerial refuelling tanker
- Manufacturer: Xi'an Aircraft Industrial Corporation
- Configuration scope: tanker variant of the Y-20 family, with modified landing gear sponsons. The Y-20B uses a later power plant and is a separate configuration.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| PLA Air Force | In service | `p5-cn-air-yy20a-mnd` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Initial operating capability | 2022 | `p5-cn-air-yy20a-mitchell` | C |
| Length | 154.2 ft (approximately 47 m) | `p5-cn-air-yy20a-mitchell` | C |
| Wingspan | 164.0 ft (approximately 50 m) | `p5-cn-air-yy20a-mitchell` | C |
| Wingspan (alternative reading) | 45.00 m | `p5-cn-air-yy20a-redstar` | C |
| Height | 49.2 ft (approximately 15 m) | `p5-cn-air-yy20a-mitchell` | C |
| Empty weight | 220,462 lb (approximately 100,000 kg) | `p5-cn-air-yy20a-mitchell` | C |
| Maximum takeoff weight | 485,017 lb (approximately 220,000 kg) | `p5-cn-air-yy20a-mitchell` | C |
| Powerplant | Four D-30KP-2 | `p5-cn-air-yy20a-mitchell` | C |
| Cruise speed | 430 kt | `p5-cn-air-yy20a-mitchell` | C |
| Range | 2,000 nm | `p5-cn-air-yy20a-mitchell` | C |
| Service ceiling | 42,660 ft | `p5-cn-air-yy20a-mitchell` | C |
| Service ceiling (alternative reading) | 13,000 m | `p5-cn-air-yy20a-redstar` | C |
| Crew | 4 | `p5-cn-air-yy20a-redstar` | C |
| Internal fuel | 18,500 kg | `p5-cn-air-yy20a-redstar` | C |
| Transferable fuel | Up to 75,000 kg (published maximum transportable fuel) | `p5-cn-air-yy20a-redstar` | C |
| Maximum speed (alternative reading) | 918 km/h | `p5-cn-air-yy20a-redstar` | C |
| Cruise speed (alternative reading) | 830 km/h | `p5-cn-air-yy20a-redstar` | C |
| Range (alternative reading) | 4,500 km | `p5-cn-air-yy20a-redstar` | C |
| Ferry range | 7,800 km | `p5-cn-air-yy20a-redstar` | C |
| Refuelling system | Three hose-and-drogue pods: two under the outer wings and one on the rear fuselage | `p5-cn-air-yy20a-janes` | C |

## Configuration Boundary

The official source held here identifies the type as part of the Y-20 aircraft family and discloses no dimensions, mass or performance. Every parameter row is Tier C secondary.

The internal-fuel pair of 18,500 kg with up to 75,000 kg of transportable fuel is now retained against the named RedStar package as a secondary reading. It does not establish a certified offload profile. The four Shenyang WS-20 turbofan reading for the Y-20B remains excluded because it is a different mark. The powerplant row therefore records the four D-30KP-2 engines for the YY-20A package alone.

The D-30KP-2 entry is the earlier Y-20 power plant and the page records it for this variant. It is recorded as published: it is not asserted to be the current engine fit for every YY-20A airframe, because no source held here establishes that either way.

The Y-20, Y-20A, Y-20B, YY-20A and YY-20B are separate configurations. No value is carried between them, and the transport and tanker roles share airframe geometry but not fuel or payload figures.

## Source References

- `p5-cn-air-yy20a-mitchell`: `raw/sources/mitchell_institute/p5-cn-air-yy20a-mitchell/manifest.md`
- `p5-cn-air-yy20a-redstar`: `raw/sources/redstar/p5-cn-air-yy20a-redstar/manifest.md` — crew, fuel, alternative performance and tanker conversion readings
- `p5-cn-air-yy20a-janes`: `raw/sources/janes/p5-cn-air-yy20a-janes/manifest.md` — three hose-and-drogue refuelling pods and their placement
- `p5-cn-air-yy20a-mnd`: `raw/sources/prc_ministry_of_national_defense/p5-cn-air-yy20a-mnd/manifest.md` — family context only
