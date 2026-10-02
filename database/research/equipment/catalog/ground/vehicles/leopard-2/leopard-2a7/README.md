# Leopard 2A7

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/leopard-2/leopard-2a7/README.md`
Owner: `database/equipment-data`
Content status: current variant parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-de-ground-leopard2a7` |
| Family / variant | Leopard 2 / 2A7 |
| Service state | Current A7/A7V configuration context; export and national fits are not merged |
| Role | Main battle tank |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Geometry | 10.97 m length × 3.75 m width × 3.00 m height | `p5-de-ground-leopard2a7-weaponspecs` | C | Named A7 public-data geometry with gun-forward length; stowed/turret convention retained |
| Combat mass | 67,500 kg maximum public combat configuration | `p5-de-ground-leopard2a7-weaponspecs` | C | Kit- and customer-dependent maximum; not a universal curb mass |
| Powerplant | MTU MB 873 Ka-501 diesel, 1,500 hp | `p5-de-ground-leopard2a7-knds` | C | Public A7 powerpack figure; fuel use and service-life state are not itemized |
| Transmission | Renk HSWL 354 | `p5-de-ground-leopard2a7-knds` | C | Public model specification; control-law details are not itemized |
| Road speed / range | Up to 68 km/h; approximately 450 km public range | `p5-de-ground-leopard2a7-weaponspecs` | C | Maximum road speed and public range estimate; terrain/payload/fuel effects are not modeled |
| Crew | 4 | `p5-de-ground-leopard2a7-bundeswehr` | A | A7/A7V turret crew context; exact national fit is not itemized |
| Main armament | 120 mm Rheinmetall L/55 smoothbore cannon | `p5-de-ground-leopard2a7-weaponspecs` | C | Public A7 summary; customer gun and ammunition fit can vary |
| Main-gun ammunition | 42 × 120 mm rounds | `p5-de-ground-leopard2a7-weaponspecs` | C | Public compilation; national ammunition mix may differ |
| Secondary armament | 2 × 7.62 mm MG3 machine guns | `p5-de-ground-leopard2a7-weaponspecs` | C | Public A7 baseline; mount and ammunition load are not itemized |
| Mission systems | EMES 15 fire-control, commander panoramic sight, thermal imaging and digitized crew stations | `p5-de-ground-leopard2a7-weaponspecs` | C | Public system summary; networking/performance limits are not itemized |
| Public protection | Composite armour with modular add-on packages, mine/IED protection, NBC protection and Trophy option context | `p5-de-ground-leopard2a7-weaponspecs` | C | Qualitative public description; customer APS and armour arrays vary |

## Source References

- `p5-de-ground-leopard2a7-bundeswehr`
- `p5-de-ground-leopard2a7-knds`
- `p5-de-ground-leopard2a7-weaponspecs`
