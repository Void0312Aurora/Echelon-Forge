# Typhoon FGR4

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/typhoon/typhoon-fgr4/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-18`
Equipment ID: `eq-uk-air-typhoon-fgr4`
Content status: parameter table present with per-field source and confidence. The RAF page supplies the full technical specification block and is the authoritative source for every dimension, mass and performance row.

## Identity

- Family: Typhoon
- Variant: FGR Mk4
- Role: Multirole combat aircraft
- Manufacturer: Eurofighter consortium
- Configuration scope: Typhoon FGR Mk4 as operated by the Royal Air Force.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| Royal Air Force | In service | `p5-uk-air-typhoon-fgr4-raf` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Powerplant | Two Eurojet EJ200 turbojets | `p5-uk-air-typhoon-fgr4-raf` | A |
| Thrust | 20,000 lb each | `p5-uk-air-typhoon-fgr4-raf` | A |
| Length | 15.96 m | `p5-uk-air-typhoon-fgr4-raf` | A |
| Height | 5.29 m | `p5-uk-air-typhoon-fgr4-raf` | A |
| Wingspan | 11.09 m | `p5-uk-air-typhoon-fgr4-raf` | A |
| Wing area | 50 m² | `p5-uk-air-typhoon-fgr4-raf` | A |
| Maximum speed | Mach 1.6 | `p5-uk-air-typhoon-fgr4-raf` | A |
| Maximum altitude | 55,000 ft | `p5-uk-air-typhoon-fgr4-raf` | A |
| Air-to-air refuelling | Probe and drogue | `p5-uk-air-typhoon-fgr4-raf` | A |
| Aircrew | One pilot | `p5-uk-air-typhoon-fgr4-raf` | A |
| Defensive aids | Electronic counter and surveillance measures, missile approach warner, expendables, towed radar decoy | `p5-uk-air-typhoon-fgr4-raf` | A |
| Air-to-air weapons | Meteor, AMRAAM, ASRAAM | `p5-uk-air-typhoon-fgr4-raf` | A |
| Air-to-surface weapons | Paveway IV, Brimstone 2, Storm Shadow | `p5-uk-air-typhoon-fgr4-raf` | A |
| Gun | 27 mm Mauser | `p5-uk-air-typhoon-fgr4-raf` | A |
| Sensors | ECR 90 radar; PIRATE infrared search and track; Litening V targeting and reconnaissance pod | `p5-uk-air-typhoon-fgr4-raf` | A |
| Empty weight | 11,000 kg (24,251 lb) | `p5-uk-air-typhoon-fgr4-encyclopedic` | C |
| Maximum takeoff weight | 23,500 kg (51,809 lb) | `p5-uk-air-typhoon-fgr4-encyclopedic` | C |
| Internal fuel | Approximately 4,500 kg, or 7,600 kg including external stores | `p5-uk-air-typhoon-fgr4-encyclopedic` | C |
| Ejection seat | Martin-Baker Mk 16A | `p5-uk-air-typhoon-fgr4-compiled` | C |

## Configuration Boundary

The RAF page is the authoritative source for this leaf and supplies powerplant, thrust, both dimensions, wing area, maximum speed, maximum altitude, refuelling method, aircrew, defensive aids, weapons and sensors. Those rows are Tier A and are not qualified.

Three fields remain on a Tier C source because the RAF page does not state them: empty weight, maximum takeoff weight and internal fuel. They rest on the general-type block held as `p5-uk-air-typhoon-fgr4-encyclopedic`, which describes the Typhoon type rather than the FGR Mk 4, so those rows are labelled C and carry the type-versus-variant gap rather than closing it.

The ejection seat row rests on the GlobalMilitary FGR.4 block, which is the only source held here that states a seat for the FGR.4. The general-type block gives a different designation for the seat on the same aircraft family; that reading is not adopted, because the FGR.4 block is variant-specific and the general block is not.

Conflicts with the Tier C readings, all resolved in favour of the RAF page and all retained as recorded alternatives rather than deleted:
- Wingspan: RAF 11.09 m against 11.0 m on the GlobalMilitary FGR.4 block and 10.95 m on the general block and on Forces News.
- Height: RAF 5.29 m against 5.3 m and 5.28 m.
- Wing area: RAF 50 m² against 51.2 m².
- Maximum speed: RAF Mach 1.6 against Mach 2.0 on Forces News.

The Mach 2.0 reading comes from `p5-uk-air-typhoon-fgr4-forcesnews` and is retained there as the recorded alternative. The 19.4 m length that an earlier revision of this leaf recorded against the RAF's 15.96 m is withdrawn, because it came from an artifact that was neither named nor located.

## Source References

- `p5-uk-air-typhoon-fgr4-raf`: `raw/sources/royal_air_force/p5-uk-air-typhoon-fgr4-raf/manifest.md` — authoritative technical, weapons and sensors block
- `p5-uk-air-typhoon-fgr4-encyclopedic`: `raw/sources/wikipedia/p5-uk-air-typhoon-fgr4-encyclopedic/manifest.md` — general type block, masses and internal fuel
- `p5-uk-air-typhoon-fgr4-compiled`: `raw/sources/compiled_secondary/p5-uk-air-typhoon-fgr4-compiled/manifest.md` — GlobalMilitary FGR.4 block, recorded alternative
- `p5-uk-air-typhoon-fgr4-forcesnews`: `raw/sources/forces_news/p5-uk-air-typhoon-fgr4-forcesnews/manifest.md` — Forces News readings, recorded alternative
