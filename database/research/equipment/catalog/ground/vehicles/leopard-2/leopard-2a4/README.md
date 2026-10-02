# Leopard 2A4

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/leopard-2/leopard-2a4/README.md`
Owner: `database/equipment-data`
Content status: cold-war configuration parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-de-ground-leopard2a4` |
| Family / variant | Leopard 2 / 2A4 |
| Service state | Cold-War production standard; later national upgrades excluded |
| Role | Main battle tank |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Geometry | 9.67 m length × 3.70 m width × 2.79 m height | `p5-de-ground-leopard2a4-weaponspecs` | C | Named A4 public-data geometry; antenna, skirt and gun orientation states not specified |
| Combat mass | 55,150 kg combat weight | `p5-de-ground-leopard2a4-weaponspecs` | C | Public compilation's combat-weight convention; national package and fuel state are not itemized |
| Powerplant | MTU MB 873 Ka-501 diesel, 1,500 hp | `p5-de-ground-leopard2a4-knds` | C | Variant powerpack figure; service-life modifications not normalized |
| Transmission | Renk HSWL 354 | `p5-de-ground-leopard2a4-knds` | C | Model-level public specification; control-law details are not itemized |
| Road speed / range | Up to 68 km/h; approximately 550 km public range | `p5-de-ground-leopard2a4-weaponspecs` | C | Maximum road speed and public range estimate; terrain/fuel effects are not modeled |
| Crew | 4 | `p5-de-ground-leopard2a4-bundeswehr` | A | Standard turret crew context; station ergonomics are not itemized |
| Main armament | 120 mm Rh-120 L44 smoothbore cannon | `p5-de-ground-leopard2a4-weaponspecs` | C | Public technical summary; ammunition family and ready/stowed split are not itemized |
| Main-gun ammunition | 42 × 120 mm rounds | `p5-de-ground-leopard2a4-weaponspecs` | C | Public compilation; national ammunition mix may differ |
| Secondary armament | 2 × 7.62 mm MG3 machine guns | `p5-de-ground-leopard2a4-weaponspecs` | C | Public A4 baseline; national fit and ammunition load are not itemized |
| Mission systems | EMES 15 computerized fire-control and thermal sighting | `p5-de-ground-leopard2a4-weaponspecs` | C | Sensor generation named; tracking/network performance is not itemized |
| Public protection | Composite armour with spaced turret modules and NBC-protected crew compartment | `p5-de-ground-leopard2a4-weaponspecs` | C | Qualitative public description; no thickness, array layout or calibrated protection value |

## Source References

- `p5-de-ground-leopard2a4-bundeswehr`
- `p5-de-ground-leopard2a4-knds`
- `p5-de-ground-leopard2a4-weaponspecs`
