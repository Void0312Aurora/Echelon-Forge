# M142 HIMARS

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/himars/m142/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-m142-himars` |
| Family / variant | HIMARS / M142 |
| Hull / configuration context | Wheeled launcher on an FMTV 5-ton truck chassis |
| Role | Mobile precision rocket and missile launcher |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Launcher payload | Six 227 mm GMLRS/ER-GMLRS rockets; one ATACMS missile; or two PrSM missiles | `p5-us-ground-m142-armyrecognition` | C | Mutually exclusive pod/loadout configurations; missile reach depends on munition block |
| Chassis | FMTV M1140 6×6 5-ton truck | `p5-us-ground-m142-armyrecognition` | C | Professional reference identifies the carrier; exact production lot is not itemized |
| Mission system | MLRS-family launcher-loader module, computerized fire-control, GPS/INS navigation, secure data link and autonomous reload crane | `p5-us-ground-m142-armytechnology` | C | Trade-publication system summary; fire-control interfaces and network latency are not itemized |
| Geometry | 7.0 m length × 2.4 m width × 3.2 m height | `p5-us-ground-m142-armytechnology` | C | Named M142 public-data overall geometry; launcher elevation state excluded |
| Mass | 10,886 kg vehicle-only; 16,257 kg public loaded/combat estimate | `p5-us-ground-m142-armytechnology` / `p5-us-ground-m142-weaponspecs` | C | Army Technology labels 10,886 kg as vehicle mass; WeaponSpecs publishes a separate combat-weight convention |
| Crew / payload | 3 crew (driver, gunner, section chief); one launcher pod loadout as listed above | `p5-us-ground-m142-armytechnology` | C | Support vehicle and reload crew are not counted |
| Propulsion / mobility | Caterpillar C7 diesel; Allison 3700SP 7-speed automatic; 6×6 chassis; up to 85 km/h; approximately 480 km range | `p5-us-ground-m142-armyrecognition` | C | Professional reference figures; engine horsepower and terrain/fuel effects are not itemized |
| Protection | Armoured cab/crew compartment against small-arms fire and shell splinters | `p5-us-ground-m142-armytechnology` | C | Qualitative public protection boundary; no thickness or calibrated level inferred |

## Source References

- `p5-us-ground-m142-himars-lockheedmartin`
- `p5-us-ground-m142-weaponspecs`
- `p5-us-ground-m142-armyrecognition`
- `p5-us-ground-m142-armytechnology`
