# AH-64E Apache Guardian

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/attack/ah-64/ah-64e/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-17`
Equipment ID: `eq-uk-air-apache-ah64e`
Content status: parameter table present with per-field source and confidence. Retrieval status is recorded per package in each manifest's `Retrieval:` block. This leaf previously carried no parameter table; the table below was built on 2026-09-17, and every row is a family or E-variant reading rather than a separate UK measurement.

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

## Configuration Boundary

This leaf carried no parameter table before 2026-09-17, and every row is a family or E-variant reading rather than a measurement of the United Kingdom aircraft.

The Boeing page is the source of record for the crew, the fuselage length, the height, the rotor diameter, both mission weights, the climb rate and the fleet totals. Its stated length of 48.2 ft is a fuselage figure, and it is recorded as such beside the overall length of 17.73 m with rotors turning that the encyclopedic block gives. The two are not alternative readings of one quantity and the leaf does not treat them as such.

The height carries two readings: 4.7 m from the manufacturer and 4.95 m from a defence reference page. Both are retained and neither is preferred.

The maximum operating weight and the maximum take-off weight are the same quantity under two names and both publishers give 23,000 lb, so the row is not a single-source figure.

The empty weight is the A and D reading of 5,165 kg. A Tier C page notes that the E runs several hundred kilogrammes heavier once the -701D engines, the uprated transmission and the Guardian avionics are fitted, but publishes no figure for it, so no E empty weight is recorded.

The powerplant, speed and combat radius rest on the Army Recognition page alone. It is the only package held here that names the T700-GE-701D, which is the E mark's engine, rather than the T700-GE-701 and -701C of the earlier marks.

## Source References

- `p5-us-air-apache-ah64e-boeing`: `raw/sources/boeing/p5-us-air-apache-ah64e-boeing/manifest.md` — manufacturer crew, dimensions, weights, climb rate
- `p5-us-air-ah64e-encyclopedic`: `raw/sources/wikipedia/p5-us-air-ah64e-encyclopedic/manifest.md` — overall length reading
- `p5-us-air-ah64e-armyrecognition`: `raw/sources/army_recognition/p5-us-air-ah64e-armyrecognition/manifest.md` — engine, speed, combat radius
- `p5-us-air-ah64e-migflug`: `raw/sources/migflug/p5-us-air-ah64e-migflug/manifest.md` — empty weight, internal fuel
