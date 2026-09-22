# F-16C/D Fighting Falcon

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/f-16/f-16c/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-22`
Equipment ID: `eq-us-air-f16c-block50`
Content status: parameter table complete for the USAF F-16C Block 50 leaf; the radar row preserves the source's explicit FMS applicability boundary.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| United States Air Force | In service | `p5-us-air-f16cd-usaf` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Powerplant | One Pratt & Whitney F100-PW-200/220/229 or General Electric F110-GE-100/129; Block 50/52 text identifies F100-PW-229 and F110-GE-129 as the increased-performance options | `p5-us-air-f16c-shaw` | A |
| Thrust | 29,000 lb | `p5-us-air-f16c-shaw` | A |
| Wingspan | 32 ft 8 in (9.8 m) | `p5-us-air-f16c-shaw` | A |
| Length | 49 ft 5 in (14.8 m) | `p5-us-air-f16c-shaw` | A |
| Height | 16 ft (4.8 m) | `p5-us-air-f16c-shaw` | A |
| Empty weight | 19,700 lb without fuel (8,936 kg) | `p5-us-air-f16c-shaw` | A |
| Maximum takeoff weight | 39,000 lb (17,690 kg), stated as the Block 50/52 maximum gross takeoff weight | `p5-us-air-f16c-shaw` | A |
| Payload / representative load | Two 2,000-lb bombs, two AIM-9, two AIM-120 and two 2,400-lb external fuel tanks | `p5-us-air-f16c-shaw` | A |
| Maximum speed | 1,500 mph (Mach 2 at altitude) | `p5-us-air-f16c-shaw` | A |
| Ferry range | More than 2,002 mi (1,740 nm) | `p5-us-air-f16c-shaw` | A |
| Service ceiling | Above 50,000 ft (15 km) | `p5-us-air-f16c-shaw` | A |
| Armament | One M-61A1 20 mm multibarrel cannon with 500 rounds; external stations for up to six air-to-air missiles, targeting pods, conventional munitions and countermeasure pods | `p5-us-air-f16c-shaw` | A |
| Radar / mission-system context | APG-68 family is the stated Block 50/52 context; APG-68(V)9 is explicitly identified for current FMS aircraft, while this source does not establish the exact radar variant on every USAF Block 50 airframe | `p5-us-air-f16c-shaw` | A (bounded applicability) |
| Crew | One for the F-16C | `p5-us-air-f16c-shaw` | A |
| Initial operating capability | Block 50/52, 1994 | `p5-us-air-f16c-shaw` | A |

## Configuration Boundary

The Shaw fact sheet is specific to the USAF F-16C Block 50 and is the source of record for the rows above. The older generic F-16C/D fact sheet is retained only as family context; no generic C/D thrust or mass is substituted for the Block 50 readings. The radar row is deliberately bounded: the page names APG-68(V)9 for current foreign-sale aircraft, but does not claim that every USAF Block 50 carries that exact variant. The unsupported 42,300-lb secondary reading is removed rather than merged with the official 39,000-lb figure.

## Source References

- `p5-us-air-f16c-shaw`: `raw/sources/us_air_force/p5-us-air-f16c-shaw/manifest.md` — Block 50/52-specific parameters and radar applicability note
- `p5-us-air-f16cd-usaf`: `raw/sources/us_air_force/p5-us-air-f16cd-usaf/manifest.md` — F-16C/D family context
