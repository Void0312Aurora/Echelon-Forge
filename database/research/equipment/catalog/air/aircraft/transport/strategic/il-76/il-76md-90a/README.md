# Il-76MD-90A

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/transport/strategic/il-76/il-76md-90a/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-23`
Equipment ID: `eq-ru-air-il76md90a`
Content status: parameter-complete research record. Official UAC technical data now supplies the core Il-76MD-90A platform block; secondary rows remain explicitly labelled where the official page is silent.

## Identity

- Family: Ilyushin Il-76
- Variant: Il-76MD-90A
- Role: Strategic and heavy military transport
- Manufacturer: Ilyushin, within the United Aircraft Corporation group
- Configuration scope: the re-engined modernized military transport. The Il-76MD, the Il-76TD-90 and the stretched Il-76MF are separate configurations and no value is carried between them.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| Russian Aerospace Forces | In service | `p5-ru-air-il76md90a-roe` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Role and modernized avionics | Modernized military transport with a new-generation integrated flight, sighting and navigation system | `p5-ru-air-il76md90a-roe` | A |
| Length | 46.6 m (152 ft 11 in) | `p5-ru-air-il76md90a-encyclopedic` | C |
| Wingspan | 50.5 m (165 ft 8 in) | `p5-ru-air-il76md90a-encyclopedic` | C |
| Height | 14.42 m (47 ft 4 in) | `p5-ru-air-il76md90a-encyclopedic` | C |
| Wing area | 300 m² (3,200 sq ft) | `p5-ru-air-il76md90a-encyclopedic` | C |
| Empty weight (family reading) | 92,500 kg (203,928 lb), stated against the Il-76TD-90 | `p5-ru-air-il76md90a-encyclopedic` | C |
| Maximum takeoff weight | 210,000 kg (462,971 lb), or 210 t | `p5-ru-air-il76md90a-ruaviation` | C |
| Maximum payload | 60,000 kg (130,000 lb), or 60 t | `p5-ru-air-il76md90a-ruaviation` | C |
| Range with 60 t payload | 4,000 km | `p5-ru-air-il76md90a-ruaviation` | C |
| Range with 52 t payload | 5,000 km | `p5-ru-air-il76md90a-ruaviation` | C |
| Range with 40 t payload | 6,500 km | `p5-ru-air-il76md90a-ruaviation` | C |
| Range unladen | 9,700 km | `p5-ru-air-il76md90a-ruaviation` | C |
| Cruising speed | 750 to 780 km/h | `p5-ru-air-il76md90a-ruaviation` | C |
| Powerplant | Four Aviadvigatel PS-90A-76 turbofans | `p5-ru-air-il76md90a-ruaviation` | C |
| Thrust as published in kilogrammes | 16,000 kg each | `p5-ru-air-il76md90a-ruaviation` | C |
| Thrust as published in kilonewtons | 156.9 kN (35,300 lbf) each | `p5-ru-air-il76md90a-encyclopedic` | C |
| Official UAC dimensions | 46.6 m length; 14.42 m height; 50.5 m wingspan | `p5-ru-air-il76md90a-uac` | B |
| Official UAC propulsion | 4 × PS-90A-76; 16,000 kgf each | `p5-ru-air-il76md90a-uac` | B |
| Official UAC cruise speed | 750–780 km/h | `p5-ru-air-il76md90a-uac` | B |
| Official UAC flight altitude / ceiling reading | 12,200 m | `p5-ru-air-il76md90a-uac` | B |
| Official UAC cargo compartment | 20 × 3.45 × 3.4 m without ramp | `p5-ru-air-il76md90a-uac` | B |
| Official UAC mission fit | Reinforced wing/landing gear, digital avionics, medical/fire-fighting module conversion | `p5-ru-air-il76md90a-uac` | B |

## Configuration Boundary

This leaf carried no parameter table before 2026-09-17. The Rosoboronexport entry held for it is a Tier A export catalogue page and states the role and the modernized system fit without a specification table, which is why no technical row existed.

The UAC package is the source of record for the modernized platform's dimensions, PS-90A-76 fit, thrust, cruise speed, altitude, cargo compartment, maximum takeoff weight, payload and a conditioned range point. `p5-ru-air-il76md90a-ruaviation` retains the broader payload/range table and `p5-ru-air-il76md90a-encyclopedic` retains the family empty-weight caveat and unit cross-check.

The thrust carries two readings in different units for the same engine: 16,000 kg each on the Russian Aviation table and 156.9 kN (35,300 lbf) each on the encyclopedic block. 16,000 kgf is about 156.9 kN, so the two describe the same rating in different units and both are recorded as published rather than one being converted into the other.

The empty weight is the one row with a caveat rather than a clean reading. The encyclopedic page labels its 92,500 kg against the Il-76TD-90, a different mark, so the leaf records it as a family reading and does not present it as the Il-76MD-90A's empty weight. No package held here states the MD-90A's own empty weight.

The range table is payload-dependent and is recorded as four rows rather than as a single range, because one figure would discard the load condition each is stated against.

The UAC page supplies a 12,200 m flight-altitude reading, retained as the public operational ceiling/altitude field. It is not treated as a combat-profile guarantee.

## Source References

- `p5-ru-air-il76md90a-roe`: `raw/sources/rosoboronexport/p5-ru-air-il76md90a-roe/manifest.md` — operator, role and system-fit context
- `p5-ru-air-il76md90a-ruaviation`: `raw/sources/russian_aviation/p5-ru-air-il76md90a-ruaviation/manifest.md` — masses, payload, range table, cruising speed, engine
- `p5-ru-air-il76md90a-encyclopedic`: `raw/sources/wikipedia/p5-ru-air-il76md90a-encyclopedic/manifest.md` — dimensions, per-engine thrust, family empty weight
- `p5-ru-air-il76md90a-uac`: `raw/sources/uac/p5-ru-air-il76md90a-uac/manifest.md` — official modernized platform dimensions, propulsion, cargo, speed, altitude and mass/payload block
