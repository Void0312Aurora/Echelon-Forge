# J-10C

Language: English canonical. Chinese companion: not provided.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/j-10/j-10c/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-cn-air-j10c` |
| Family / variant | J-10 / J-10C |
| Role | Single-seat multirole fighter |
| Configuration scope | PLA Air Force J-10C AESA/PL-15-era modernization; J-10A/S and export FC-20 excluded |

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| PLA Air Force | Combat duty | `p5-cn-air-j10c-mnd` |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Length | 16.4 m | `p5-cn-air-j10c-armyrecognition` | C | J-10 family geometry; J-10C external fairings may vary |
| Wingspan | 9.75 m | `p5-cn-air-j10c-armyrecognition` | C | J-10 family geometry |
| Height | 4.78 m | `p5-cn-air-j10c-armyrecognition` | C | J-10 family geometry |
| Maximum take-off mass | 19,277 kg | `p5-cn-air-j10c-armyrecognition` | C | Public family maximum; store fit can shift about +/-1 t |
| Engine / thrust | WS-10A Taihang 129 kN or AL-31FN 117-125 kN | `p5-cn-air-j10c-armyrecognition` | C | Engine block varies by production batch |
| Flight envelope | 2,200 km/h maximum; service ceiling 17,000-18,000 m bound | `p5-cn-air-j10c-armyrecognition` | C | Speed direct; ceiling is professional estimate |
| Range | 3,200 km maximum ferry; combat radius 550-700 km bound | `p5-cn-air-j10c-armyrecognition` | C | Ferry/radius separated |
| Crew | 1 | `p5-cn-air-j10c-mnd` | A | J-10C single-seat operational fighter |
| Radar | KLJ-10 AESA fire-control radar, 100-160 km fighter-class detection bound | `p5-cn-air-j10c-armyrecognition` | C | Exact mode tables are not public |
| Avionics / EW | Quadruplex fly-by-wire, IRST/targeting pods, KG300G jammer, KZ900 electronic-recon pod, RWR/MAWS; 120-180 chaff/flare cartridges (bound) | `p5-cn-air-j10c-armyrecognition` | C | Pod fit and national block vary |
| Mission systems | Networked multirole computer, helmet cueing, datalink and precision navigation/attack integration | `p5-cn-air-j10c-armyrecognition`; `p5-cn-air-j10c-mnd` | A/C | MND confirms combat duty; system details are professional estimates |
| Internal gun | Type 23-3 twin-barrel 23 mm cannon, 110-150 rounds (bound) | `p5-cn-air-j10c-armyrecognition` | C | Page gives cannon and firing rate; ammunition is bounded estimate |
| Air-to-air weapons | PL-10 short-range and PL-12/PL-15 BVR missiles; up to 11 stations | `p5-cn-air-j10c-armyrecognition` | C | PL-15/J-10C pairing is configuration-specific |
| Air-to-ground weapons | LS-6 glide bombs, laser-guided bombs, unguided bombs and guided stores | `p5-cn-air-j10c-armyrecognition` | C | Software/block dependent |
| Signature / protection | Reduced-signature non-stealth canard-delta airframe; clean frontal RCS 1-3 m2 bound; integrated RWR/ECM and chaff/flare | `p5-cn-air-j10c-armyrecognition` | C | RCS is specialist estimate, not official Chinese data |

All target fields contain direct values or bounded estimates; official MND service evidence is kept distinct from professional technical estimates.

## Source References

- `p5-cn-air-j10c-mnd`
- `p5-cn-air-j10c-armyrecognition`
