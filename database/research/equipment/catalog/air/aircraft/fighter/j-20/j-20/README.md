# J-20 Mighty Dragon

Language: English canonical. Chinese companion: not provided.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/j-20/j-20/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-cn-air-j20` |
| Family / variant | J-20 / early operational single-seat J-20 |
| Role | Long-range stealth air-superiority fighter |
| Configuration scope | Early WS-10B operational configuration; WS-15, J-20S and later A/B upgrades excluded |

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| PLA Air Force | Combat service | `p5-cn-air-j20-mnd` |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Length | 20.4 m | `p5-cn-air-j20-armyrecognition` | C | Public J-20 geometry |
| Wingspan | 13.5 m | `p5-cn-air-j20-armyrecognition` | C | Public J-20 geometry |
| Height | 4.4 m | `p5-cn-air-j20-armyrecognition` | C | Public J-20 geometry |
| Empty mass | 19,391 kg | `p5-cn-air-j20-armyrecognition` | C | Early operational estimate |
| Maximum take-off mass | 37,013 kg | `p5-cn-air-j20-armyrecognition` | C | Public estimate; fuel/store fit can shift about +/-1.5 t |
| Engines / thrust | 2 x WS-10B; 132-145 kN afterburning thrust each (bound) | `p5-cn-air-j20-armyrecognition` | C | Page names WS-10B; WS-15 excluded |
| Flight envelope | 2,400 km/h (about Mach 2); service ceiling 18,000-20,000 m bound | `p5-cn-air-j20-armyrecognition` | C | Speed direct; ceiling is professional estimate |
| Range | 6,000 km maximum ferry estimate; combat radius 1,000-1,500 km bound | `p5-cn-air-j20-armyrecognition` | C | Public range is not a combat-radius value |
| Crew | 1 pilot | `p5-cn-air-j20-mnd`; `p5-cn-air-j20-armyrecognition` | A/C | Single-seat operational configuration |
| Radar | AESA fire-control radar, type not officially disclosed; 160-250 km fighter-class detection bound | `p5-cn-air-j20-armyrecognition` | C | Radar type/range are professional estimates |
| Avionics / EW | EORD-31 IRST, distributed-aperture system, EOTS-86 electro-optical targeting, integrated RWR/ECM/MAWS and secure datalink; 120-240 countermeasure cartridges (bound) | `p5-cn-air-j20-armyrecognition` | C | Sensors direct; EW and count are bounded estimates |
| Mission systems | Internal-bay weapons management, sensor fusion, networked air-combat operations and high-off-boresight PL-10 cueing | `p5-cn-air-j20-armyrecognition`; `p5-cn-air-j20-mnd` | A/C | MND confirms service; implementation details are professional estimates |
| Internal weapons | PL-10 short-range, PL-12/PL-15 BVR missiles; PL-21 and LS-6 precision bomb options | `p5-cn-air-j20-armyrecognition` | C | Main bays assumed for BVR stores; side bays for short-range stores |
| External weapons / stations | Four under-wing pylons for drop tanks or stores | `p5-cn-air-j20-armyrecognition` | C | External carriage increases signature |
| Signature / protection | Low-observable blended planform, edge alignment and internal carriage; frontal RCS 0.01-0.05 m2 and broadside 0.1-0.5 m2 bounds; integrated EW/MAWS/chaff-flare | `p5-cn-air-j20-armyrecognition` | C | RCS and countermeasure values are specialist estimates |

All target fields contain direct values or bounded estimates; official MND service evidence is kept distinct from professional technical estimates.

## Source References

- `p5-cn-air-j20-mnd`
- `p5-cn-air-j20-armyrecognition`
