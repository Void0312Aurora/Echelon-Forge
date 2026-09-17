# YY-20A

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/tanker/yy-20/yy-20a/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-18`
Equipment ID: `eq-cn-air-yy20a`
Content status: parameter table present with per-field source and confidence. Status is `cataloged`, not `parameter_complete`, because every parameter row is Tier C secondary and the powerplant differs between sources.

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
| Height | 49.2 ft (approximately 15 m) | `p5-cn-air-yy20a-mitchell` | C |
| Empty weight | 220,462 lb (approximately 100,000 kg) | `p5-cn-air-yy20a-mitchell` | C |
| Maximum takeoff weight | 485,017 lb (approximately 220,000 kg) | `p5-cn-air-yy20a-mitchell` | C |
| Powerplant | Four D-30KP-2 per one source; the Y-20B is associated with four Shenyang WS-20 turbofans | `p5-cn-air-yy20a-mitchell` | C |
| Cruise speed | 430 kt | `p5-cn-air-yy20a-mitchell` | C |
| Range | 2,000 nm | `p5-cn-air-yy20a-mitchell` | C |
| Service ceiling | 42,660 ft | `p5-cn-air-yy20a-mitchell` | C |
| Internal fuel | 18,500 kg, with up to 75,000 kg of transportable fuel | `p5-cn-air-yy20a-mitchell` | C |
| Landing gear | Modified sponsons for the tanker fit | `p5-cn-air-yy20a-mitchell` | C |

## Configuration Boundary

The official source held here identifies the type as part of the Y-20 aircraft family and discloses no dimensions, mass or performance. Every parameter row is Tier C secondary.

The tanker-specific fuel pair, 18,500 kg internal and up to 75,000 kg transportable, is the figure the general Y-20 entries do not carry and is the reason this row set is variant-specific rather than inherited. It originates from a secondary source specific to the YY-20A and is recorded in the Mitchell package with that provenance noted.

The powerplant differs across sources: four D-30KP-2 on this variant's entry, against four Shenyang WS-20 turbofans on the Y-20B. Both are retained and neither is substituted for the other.

The Y-20, Y-20A, Y-20B, YY-20A and YY-20B are separate configurations. No value is carried between them, and the transport and tanker roles share airframe geometry but not fuel or payload figures.

## Source References

- `p5-cn-air-yy20a-mitchell`: `raw/sources/mitchell_institute/p5-cn-air-yy20a-mitchell/manifest.md`
- `p5-cn-air-yy20a-mnd`: `raw/sources/prc_ministry_of_national_defense/p5-cn-air-yy20a-mnd/manifest.md` — family context only
