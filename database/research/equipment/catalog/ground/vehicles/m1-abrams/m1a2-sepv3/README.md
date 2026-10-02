# M1A2 Abrams SEP v3

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/m1-abrams/m1a2-sepv3/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-m1a2sepv3` |
| Family / variant | M1 Abrams / M1A2 SEP v3 |
| Hull / configuration context | SEP v3; classified armour array and kit state are not itemized |
| Role | Main battle tank |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Powerplant | Honeywell AGT1500 gas turbine, 1,500 hp | `p5-us-ground-m1a2sepv3-armytechnology` | C | Trade-publication profile; fuel use and engine overhaul state are not itemized |
| Main armament | 120 mm M256 smoothbore cannon | `p5-us-ground-m1a2sepv3-armytechnology` | C | Trade-publication profile; ammunition mix listed separately |
| Protection | New hull/turret armour package, optional reactive/slat armour, CREW Duke V3 counter-IED EW and Trophy APS context | `p5-us-ground-m1a2sepv3-armytechnology` | C | Qualitative public description; classified array/thickness and kit state are not represented |
| Electrical / mission systems | Third-generation FLIR, commander independent thermal viewer, under-armour APU, ammunition datalink, digital diagnostics/networking | `p5-us-ground-m1a2sepv3-armytechnology` | C | Trade-publication system summary; interfaces and performance are not itemized |
| Geometry | 9.7 m length × 3.7 m width × 2.4 m height | `p5-us-ground-m1a2sepv3-armytechnology` | C | Named SEPv3 public-data geometry; gun orientation and fittings are not itemized |
| Mass | 66,800 kg combat weight | `p5-us-ground-m1a2sepv3-weaponspecs` | C | Public compilation's combat-weight convention; kit/fuel state can vary |
| Crew / payload | 4 crew; 42 × 120 mm rounds | `p5-us-ground-m1a2sepv3-armytechnology` / `p5-us-ground-m1a2sepv3-weaponspecs` | C | Crew from Army Technology; ammunition capacity from independent compilation; exact mix is not itemized |
| Mobility | Up to 67 km/h; approximately 426 km public range | `p5-us-ground-m1a2sepv3-weaponspecs` | C | Public maximum/nominal figures; terrain, fuel and load effects are not modeled |
| Transmission | Allison X-1100-3B automatic, Abrams-family configuration | `p5-us-ground-m1a2sepv3-weaponspecs` | C | Family transmission identity retained; SEPv3 control software is not itemized |

## Source References

- `p5-us-ground-m1a2sepv3-gdls`
- `p5-us-ground-m1a2sepv3-army-peogcs`
- `p5-us-ground-m1a2sepv3-weaponspecs`
