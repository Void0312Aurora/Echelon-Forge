# AH-64E Apache Guardian

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/attack/ah-64/ah-64e/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-23`
Equipment ID: `eq-uk-air-apache-ah64e`
Content status: parameter table complete for the shared AH-64E research record. British Army E-variant capability, Boeing family/E values and a versioned community empty-weight cross-check remain separately labelled.

## Identity

- Family: Boeing AH-64 Apache
- Variant: AH-64E Apache Guardian
- Role: Attack helicopter
- Manufacturer: Boeing, with the United Kingdom aircraft assembled and supported by AgustaWestland, now Leonardo Helicopters
- Configuration scope: the AH-64E, the upgraded mark with T700-GE-701D engines and composite rotor blades. The AH-64A, AH-64D and the British AH.1 are separate configurations.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| United States Army | In service | `p5-us-air-apache-ah64e-boeing` |
| United Kingdom | In service | `p5-us-air-apache-ah64e-boeing` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Crew | 2, pilot and co-pilot or gunner | `p5-us-air-apache-ah64e-boeing` | B |
| Length (fuselage) | 14.7 m (48.2 ft) | `p5-us-air-apache-ah64e-boeing` | B |
| Length (overall, rotors turning) | 17.73 m (58 ft 2 in) | `p5-us-air-ah64e-encyclopedic` | C |
| Height | 4.7 m (15.5 ft) | `p5-us-air-apache-ah64e-boeing` | B |
| Height (alternative reading) | 4.95 m | `p5-us-air-ah64e-armyrecognition` | C |
| Main rotor diameter | 14.6 m (48 ft) | `p5-us-air-apache-ah64e-boeing` | B |
| Primary mission gross weight | 6,838 kg (15,075 lb) | `p5-us-air-apache-ah64e-boeing` | B |
| Maximum operating weight | 10,433 kg (23,000 lb) | `p5-us-air-apache-ah64e-boeing` | B |
| Maximum rate of climb | 853+ m (2,800+ ft) per minute | `p5-us-air-apache-ah64e-boeing` | B |
| Powerplant | Two General Electric T700-GE-701D turboshafts | `p5-us-air-ah64e-armyrecognition` | C |
| Speed | Approximately 300 km/h | `p5-us-air-ah64e-armyrecognition` | C |
| Combat radius | Approximately 476 km | `p5-us-air-ah64e-armyrecognition` | C |
| Empty weight (A and D reading) | 5,165 kg (11,387 lb) | `p5-us-air-ah64e-migflug` | C |
| Internal fuel | Approximately 1,420 litres in two crashworthy self-sealing cells | `p5-us-air-ah64e-migflug` | C |
| UK Army maximum speed | 330 km/h | `p5-uk-air-apache-ah64e-army` | A |
| UK Army engine | Two General Electric T700-GE-701D turboshafts | `p5-uk-air-apache-ah64e-army` | A |
| UK Army maximum-weight reading | 7,746 kg | `p5-uk-air-apache-ah64e-army` | A |
| UK Army armament | 30 mm chain gun, 70 mm rockets and Hellfire missiles | `p5-uk-air-apache-ah64e-army` | A |
| UK Army mission sensors | Longbow radar; optical and thermal imaging sights; integrated defensive-aid suite | `p5-uk-air-apache-ah64e-army` | A |
| E-variant empty-weight community reading | 5,360 kg (2024/V6 database record) | `p5-us-air-ah64e-cmano` | C |

## Configuration Boundary

Its queue identity is the United Kingdom row, but the record is shared at the AH-64E variant level and is not a measurement of every UK aircraft configuration. The British Army page now supplies direct UK E-variant capability and headline values; the Boeing and specialist packages retain family/E readings.

The Boeing page is the source of record for the crew, the fuselage length, the height, the rotor diameter, both mission weights, the climb rate and the fleet totals. Its stated length of 48.2 ft is a fuselage figure, and it is recorded as such beside the overall length of 17.73 m with rotors turning that the encyclopedic block gives. The two are not alternative readings of one quantity and the leaf does not treat them as such.

The height carries two readings: 4.7 m from the manufacturer and 4.95 m from a defence reference page. Both are retained and neither is preferred.

The maximum operating weight and the maximum take-off weight are the same quantity under two names and both publishers give 23,000 lb, so the row is not a single-source figure.

The empty-weight block now carries three boundaries: 5,165 kg explicitly for the A/D marks from MiGFlug, the Army Recognition page's unqualified approximate figure, and a 5,360 kg E-variant reading from the versioned CMANO database. The latter is Tier C and community-derived, so it is a cross-check rather than an official certification value.

The British Army page independently names the T700-GE-701D, 330 km/h speed, 7,746 kg maximum-weight reading, weapon set and sensor suite. Army Recognition remains the source of the approximately 300 km/h and 476 km combat-radius readings; both are retained rather than averaged.

## Source References

- `p5-us-air-apache-ah64e-boeing`: `raw/sources/boeing/p5-us-air-apache-ah64e-boeing/manifest.md` — manufacturer crew, dimensions, weights, climb rate
- `p5-us-air-ah64e-encyclopedic`: `raw/sources/wikipedia/p5-us-air-ah64e-encyclopedic/manifest.md` — overall length reading
- `p5-us-air-ah64e-armyrecognition`: `raw/sources/army_recognition/p5-us-air-ah64e-armyrecognition/manifest.md` — engine, speed, combat radius
- `p5-us-air-ah64e-migflug`: `raw/sources/migflug/p5-us-air-ah64e-migflug/manifest.md` — empty weight, internal fuel
- `p5-uk-air-apache-ah64e-army`: `raw/sources/british_army/p5-uk-air-apache-ah64e-army/manifest.md` — UK E-variant capability, speed, engine, weight, weapons and sensors
- `p5-us-air-ah64e-cmano`: `raw/sources/cmano_db/p5-us-air-ah64e-cmano/manifest.md` — versioned community E-variant empty-weight cross-check
