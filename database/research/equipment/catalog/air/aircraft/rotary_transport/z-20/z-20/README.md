# Z-20

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/rotary_transport/z-20/z-20/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-17`
Equipment ID: `eq-cn-air-z20`
Content status: parameter table present with per-field source and confidence. Retrieval status is recorded per package in each manifest's `Retrieval:` block rather than asserted here. The seven fields withdrawn in the previous revision now rest on two named packages, and the length and rotor readings carry recorded conflicts.

## Identity

- Family: Z-20 (Zhi-20)
- Variant: Z-20
- Role: Medium-lift utility helicopter for transport, assault, medical evacuation, search and rescue and reconnaissance
- Manufacturer: AVICOPTER and Harbin Aviation Industry
- Configuration scope: the base utility variant. Transport, naval, air force and armed-police marks are separate configurations and are not merged.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| PLA Ground Force Aviation | In service | `p5-cn-air-z20-mnd` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| First flight | 23 December 2013 | `p5-cn-air-z20-gs` | C |
| Initial operational capability | November 2018 | `p5-cn-air-z20-gs` | C |
| Overall length | 20 m (65.6 ft) | `p5-cn-air-z20-globalmilitary` | C |
| Overall length (alternative reading) | 19.5 m | `p5-cn-air-z20-gs` | C |
| Rotor span (width) | 16 m (52.5 ft) | `p5-cn-air-z20-globalmilitary` | C |
| Rotor diameter | 16 m (52 ft 6 in) | `p5-cn-air-z20-encyclopedic` | C |
| Rotor diameter (alternative reading) | 16.2 to 16.5 m, given as a range | `p5-cn-air-z20-gs` | C |
| Fuselage length | 15 m (49.2 ft) | `p5-cn-air-z20-gs` | C |
| Fuselage height | 3.5 m (11.5 ft) | `p5-cn-air-z20-gs` | C |
| Height (alternative reading) | 5.0 m | `p5-cn-air-z20-gs` | C |
| Height | 5.3 m (17.4 ft) | `p5-cn-air-z20-globalmilitary` | C |
| Empty weight | 5,000 kg (11,023 lb) | `p5-cn-air-z20-globalmilitary` | C |
| Empty weight (alternative reading) | 4,850 to 5,000 kg (10,700 to 11,000 lb) | `p5-cn-air-z20-gs` | C |
| Maximum takeoff weight | 10,000 kg (22,046 lb) | `p5-cn-air-z20-globalmilitary` | C |
| Maximum takeoff weight (alternative reading) | 9,800 to 10,000 kg (20,000 to 22,000 lb) | `p5-cn-air-z20-gs` | C |
| Internal payload | 1,500 kg (3,300 lb) | `p5-cn-air-z20-gs` | C |
| External cargo capacity | 4,000 kg (8,800 lb) | `p5-cn-air-z20-encyclopedic` | C |
| External cargo capacity (alternative reading) | 5,000 kg | `p5-cn-air-z20-gs` | C |
| Powerplant | Two WZ-10 turboshafts, Zhuzhou Aeroengine Factory | `p5-cn-air-z20-globalmilitary` | C |
| Powerplant (power band) | 1,600 to 2,000 kW each | `p5-cn-air-z20-encyclopedic` | C |
| Maximum power at takeoff | 3,200 kW (4,290 hp) | `p5-cn-air-z20-gs` | C |
| Maximum speed | 360 km/h (224 mph) | `p5-cn-air-z20-globalmilitary` | C |
| Maximum speed (alternative reading) | 320 km/h | `p5-cn-air-z20-gs` | C |
| Cruise speed | 290 km/h (180 kn) | `p5-cn-air-z20-encyclopedic` | C |
| Cruise speed (alternative reading) | 275 km/h (170 mph, 150 kn) | `p5-cn-air-z20-gs` | C |
| Range | 560 km (348 mi) | `p5-cn-air-z20-globalmilitary` | C |
| Range (alternative reading) | 560 to 600 km (350 to 400 mi) | `p5-cn-air-z20-gs` | C |
| Maximum flight distance | 1,200 km | `p5-cn-air-z20-gs` | C |
| Ferry range | 2,200 km | `p5-cn-air-z20-gs` | C |
| Service ceiling | 6,000 m (19,685 ft) | `p5-cn-air-z20-globalmilitary` | C |
| Service ceiling (alternative reading) | 5,400 to 5,500 m (17,000 to 18,000 ft) | `p5-cn-air-z20-gs` | C |
| Climb rate | 7.1 m/s (1,400 ft/min) | `p5-cn-air-z20-globalmilitary` | C |
| Main rotor blades | 5 | `p5-cn-air-z20-gs` | C |
| Tail rotor blades | 4 | `p5-cn-air-z20-gs` | C |
| Engine development | The official source notes high-altitude engine and rotor anti-icing development | `p5-cn-air-z20-mnd` | A |

## Configuration Boundary

The official source held here confirms the programme and notes high-altitude engine and rotor anti-icing development, and discloses no dimensions, mass or performance. It is the only Tier A row set on this leaf and it carries the engine development note only.

Seven fields that the previous revision removed are now restored, each against a named package. Height, empty weight, maximum takeoff weight, maximum speed, range and service ceiling rest on `p5-cn-air-z20-globalmilitary`, and external cargo capacity rests on `p5-cn-air-z20-encyclopedic`. A third package, `p5-cn-air-z20-gs`, turned out to carry a full specification table as well, with its own readings for the same fields printed as bands; the previous revision's claim that the page stated only the programme dates, the length and the rotor diameter was wrong, and the manifest now records the correction. All three packages were retrieved on 2026-09-17.

The conflicts are recorded as separate rows and none is averaged:
- Overall height: 5.3 m from two packages against 5.0 m from the GlobalSecurity table.
- External payload: 4,000 kg from the encyclopedic block against 5,000 kg from the GlobalSecurity table, with a separate 1,500 kg internal payload row.
- Maximum speed: 360 km/h from two packages against 320 km/h from the GlobalSecurity table. The two cruise readings, 290 km/h and 275 km/h, track the same split.
- Service ceiling: 6,000 m against the band 5,400 to 5,500 m.
- Range: 560 km against the band 560 to 600 km, with the same page also giving a 1,200 km maximum flight distance and a 2,200 km ferry range, which are different quantities and are recorded as their own rows.
- Length and rotor: 20 m / 16 m from the compilation and encyclopedic packages against 19.5 m / 16.2 to 16.5 m from the GlobalSecurity table.

The powerplant is recorded as three readings: two WZ-10 turboshafts, a power band of 1,600 to 2,000 kW each, and a 3,200 kW maximum power at takeoff which is the pair combined rather than a per-engine figure. The leaf does not collapse these into one number.

Z-20, Z-20T, Z-20F, Z-20J, Z-20S and Z-20K are separate configurations serving different services and roles. None is merged into this record and no value is shared between them.

## Source References

- `p5-cn-air-z20-globalmilitary`: `raw/sources/globalmilitary/p5-cn-air-z20-globalmilitary/manifest.md` — dimensions, masses, powerplant, speed, range, ceiling, climb rate
- `p5-cn-air-z20-encyclopedic`: `raw/sources/wikipedia/p5-cn-air-z20-encyclopedic/manifest.md` — external cargo, rotor diameter, cruise speed, power band
- `p5-cn-air-z20-gs`: `raw/sources/globalsecurity/p5-cn-air-z20-gs/manifest.md` — programme dates, alternative length and rotor readings
- `p5-cn-air-z20-mnd`: `raw/sources/prc_ministry_of_national_defense/p5-cn-air-z20-mnd/manifest.md` — programme context only
