# J-11B / J-11BS

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/j-11/j-11b-bs/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-23`
Equipment ID: `eq-cn-air-j11b-bs`
Content status: parameter-complete research record with per-field source and confidence. The single-seat and twin-seat airframes are not separated by any source held here, and that boundary remains explicit rather than papered over.

## Identity

- Family: Shenyang J-11
- Variant: J-11B and J-11BS
- Role: Heavy air-superiority fighter; the J-11BS is the twin-seat derivative
- Manufacturer: Shenyang Aircraft Corporation
- Configuration scope: the Chinese Flanker derivative. The J-11B is the single-seat mark and the J-11BS the twin-seat one; the J-11BG, J-11BH, J-11BSH and J-11D are further marks. The original J-11A with the Russian engine fit is a separate configuration.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| PLA Air Force | In service | `p5-cn-air-j11b-mnd` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Service use confirmed | Official PLA material confirms J-11B service use | `p5-cn-air-j11b-mnd` | A |
| NATO reporting name | Flanker-L | `p5-cn-air-j11b-mitchell` | C |
| Type | Air superiority fighter | `p5-cn-air-j11b-mitchell` | C |
| Contractor | Shenyang Aircraft Corporation | `p5-cn-air-j11b-mitchell` | C |
| Initial operational capability | 2000 | `p5-cn-air-j11b-mitchell` | C |
| Active variants | J-11, J-11B, J-11BS, J-11BG, J-11BH, J-11BSH, J-11D | `p5-cn-air-j11b-mitchell` | C |
| Length (family reading) | 21.9 m (71 ft 10 in) | `p5-cn-air-j11b-encyclopedic` | C |
| Wingspan (family reading) | 14.7 m (48 ft 3 in) | `p5-cn-air-j11b-encyclopedic` | C |
| Height (family reading) | 5.92 m (19 ft 5 in) | `p5-cn-air-j11b-encyclopedic` | C |
| Wing area | 52.84 m² (568.8 sq ft) | `p5-cn-air-j11b-encyclopedic` | C |
| Empty weight (family reading) | 36,112 lb (16,380 kg calculated) | `p5-cn-air-j11b-mitchell` | C |
| Gross weight | 23,926 kg (52,748 lb) | `p5-cn-air-j11b-encyclopedic` | C |
| Maximum takeoff weight | 33,000 kg (72,753 lb) | `p5-cn-air-j11b-encyclopedic` | C |
| Internal fuel capacity | 9,400 kg (20,700 lb) | `p5-cn-air-j11b-encyclopedic` | C |
| Powerplant | Two Shenyang WS-10A "Taihang" afterburning turbofans | `p5-cn-air-j11b-encyclopedic` | C |
| Thrust | 132 kN (30,000 lbf, or about 29,700 lbf) each with afterburner | `p5-cn-air-j11b-encyclopedic` | C |
| Engine note on the BG mark | The J-11BG uses the WS-10B at 13.2 tonnes thrust | `p5-cn-air-j11b-dvids` | C |
| Maximum speed | Mach 2.35 (approximately 2,500 km/h) at altitude | `p5-cn-air-j11b-dvids` | C |
| Combat range | Approximately 1,500 km (930 mi, 810 nmi) | `p5-cn-air-j11b-dvids` | C |
| Range | 3,530 km (2,190 mi, 1,910 nmi) | `p5-cn-air-j11b-dvids` | C |
| Service ceiling | 19,000 m (62,000 ft) | `p5-cn-air-j11b-dvids` | C |
| Rate of climb | 300 m/s | `p5-cn-air-j11b-dvids` | C |
| Load limits | +9 g | `p5-cn-air-j11b-dvids` | C |
| Crew | J-11B single-seat; J-11BS twin-seat derivative | `p5-cn-air-j11b-encyclopedic` | C |
| Armament | 30 mm GSh-30-1 cannon; ten hardpoints; reported PL-8B/PL-12 air-to-air stores and later-mark PL-10/PL-15 distinction | `p5-cn-air-j11b-encyclopedic` | C |
| Mission system | Type 1493 radar, digital flight control, glass cockpit, OEPS-27 electro-optical system, helmet-mounted sight and ECM-pod context | `p5-cn-air-j11b-encyclopedic` | C |

## Configuration Boundary

This leaf carried no parameter table before 2026-09-17. The official PLA source held for it confirms J-11B service use and states that variant-level dimensions and performance are not officially disclosed, which is why every technical row is Tier C.

The single-seat and twin-seat airframes are not separated. This leaf is named for the J-11B and the J-11BS together, and no package held here states a J-11BS dimension or mass figure. The encyclopedic specifications block gives crew 1 for the single-seat B; the BS is recorded only as the separate twin-seat derivative, not assigned the B dimensions. The Mitchell entry gives one set of figures for the whole family with no per-mark split. Every geometry and mass row above is therefore a family or single-seat reading, labelled as such, and none is asserted as the twin-seat airframe's own.

The measurements agree across publishers: the Mitchell entry's imperial dimensions convert to the encyclopedic metric ones, and the two maximum take-off weight figures, 72,753 lb and 33,000 kg, are the same number in different units. The engine thrust carries 132 kN with a parenthetical 29,700 lbf against the encyclopedic 30,000 lbf, which are two roundings of one rating.

The empty weight is the Mitchell entry's 36,112 lb. The metric value of 16,380 kg beside it is this tree's arithmetic, calculated at 0.45359237 kg per pound, because the Mitchell entry publishes no metric figure.

The performance block rests on a single package. No other package held here states a speed, range, ceiling or climb rate for this family, so those six rows are single-source and are labelled accordingly.

The J-11BG's WS-10B engine is recorded as a note on a separate mark and is not merged into the B or BS engine row.

## Source References

- `p5-cn-air-j11b-mnd`: `raw/sources/prc_ministry_of_national_defense/p5-cn-air-j11b-mnd/manifest.md` — official confirmation of service use, no technical values
- `p5-cn-air-j11b-mitchell`: `raw/sources/mitchell_institute/p5-cn-air-j11b-mitchell/manifest.md` — family context, variant list, dimensions and empty weight in imperial
- `p5-cn-air-j11b-encyclopedic`: `raw/sources/wikipedia/p5-cn-air-j11b-encyclopedic/manifest.md` — metric geometry, masses, fuel, powerplant, single-seat crew, armament and avionics context
- `p5-cn-air-j11b-dvids`: `raw/sources/dvids/p5-cn-air-j11b-dvids/manifest.md` — performance block and engine thrust
