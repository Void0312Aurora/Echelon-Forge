# Tu-160M

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/bomber/tu-160/tu-160m/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-18`
Equipment ID: `eq-ru-air-tu160m`
Content status: parameter table present with per-field source and confidence. Status is `cataloged`, not `parameter_complete`, because every parameter row is Tier C secondary and the geometry rows describe the Tu-160 airframe rather than a stated Tu-160M change.

## Identity

- Family: Tu-160
- Variant: Tu-160M
- Role: Strategic missile-carrier bomber
- Manufacturer: Tupolev, Kazan Aircraft Factory
- Configuration scope: the Tu-160M is a modernization of the Tu-160 covering avionics, systems and the engine fit, reported by the manufacturer's press office to include serially produced NK-32-02 engines. The airframe outer mould line is not reported as changed, so the geometry rows below are airframe values.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| Russian Aerospace Forces | In service | `p5-ru-air-tu160m-mod` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Length | 54.1 m | `p5-ru-air-tu160m-19f45` | C |
| Height | 13.1 m | `p5-ru-air-tu160m-19f45` | C |
| Wingspan | Variable geometry: 35.6 m swept, 55.7 m unswept | `p5-ru-air-tu160m-19f45` | C |
| Empty weight | 110,000 kg | `p5-ru-air-tu160m-19f45` | C |
| Powerplant | Four Kuznetsov NK-32 afterburning turbofans; the Tu-160M is reported with serially produced NK-32-02 engines | `p5-ru-air-tu160m-19f45` | C |
| Maximum speed | Mach 2.05 (2,220 km/h) | `p5-ru-air-tu160m-19f45` | C |
| Range | 12,300 km (7,640 mi) | `p5-ru-air-tu160m-19f45` | C |
| Service ceiling | 16,000 m (52,493 ft) | `p5-ru-air-tu160m-19f45` | C |
| Armament capacity | Up to 88,185 lb (approximately 40,000 kg) of ordnance, including nuclear and conventional bombs and cruise missiles | `p5-ru-air-tu160m-19f45` | C |
| Crew | Four, on K-36LM ejection seats | `p5-ru-air-tu160m-19f45` | C |
| Structure | Titanium at 30 percent of the structure; fly-by-wire control; blended wing profile; full-span leading-edge slats; double-slotted trailing-edge flaps; cruciform tail | `p5-ru-air-tu160m-19f45` | C |
| Refuelling | Probe-and-drogue in-flight refuelling system, rarely used | `p5-ru-air-tu160m-19f45` | C |
| Procurement | Official material confirms Tu-160M procurement | `p5-ru-air-tu160m-mod` | A |

## Configuration Boundary

The official source held here is a Russian Ministry of Defence news statement confirming procurement. It discloses no dimensions, mass or performance, so every parameter row is Tier C secondary.

The geometry, mass and performance rows describe the Tu-160 airframe and engine installation. The cited sources do not report that the Tu-160M modernization changed the outer mould line, and they do not state that it did not either. The rows are therefore recorded as airframe values and are not asserted as Tu-160M-unique.

The Tu-160 and Tu-160M are treated as one family with the M as a modernization. No separate Tu-160 leaf exists in this tree, so no value is being carried between two records.

## Source References

- `p5-ru-air-tu160m-19f45`: `raw/sources/19fortyfive/p5-ru-air-tu160m-19f45/manifest.md`
- `p5-ru-air-tu160m-mod`: `raw/sources/russian_ministry_of_defence/p5-ru-air-tu160m-mod/manifest.md` — procurement confirmation only
