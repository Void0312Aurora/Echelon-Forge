# M1A1 Abrams

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/m1-abrams/m1a1/README.md`
Owner: `database/equipment-data`
Content status: variant-specific cold-war parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-m1a1` |
| Family / variant | M1 Abrams / M1A1 |
| Service state | Cold-War configuration; later upgrade kits are not merged |
| Role | Main battle tank |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Geometry | 9.83 m length × 3.65 m width × 2.89 m height | `p5-us-ground-m1a1-armyrecognition` | C | Named baseline M1A1 overall geometry; public tables disagree on height convention, so gun/stowage state is retained as uncertainty |
| Mass semantics | 62,000 kg listed weight (alternate public combat estimate 63,100 kg) | `p5-us-ground-m1a1-armyrecognition` / `p5-us-ground-m1a1-weaponspecs` | C | Secondary tables use different loaded/ combat conventions; no transport or kit-state mass inferred |
| Powerplant | 1,500 hp AGT1500 gas-turbine engine | `p5-us-ground-m1a1-armyrecognition` | C | Professional reference; fuel consumption and engine block details are not itemized |
| Transmission | Allison X-1100-3B automatic, 4 forward / 2 reverse | `p5-us-ground-m1a1-armyrecognition` | C | Public technical summary; exact overhaul/block state not itemized |
| Road speed / range | Up to 68 km/h; approximately 426 km public range | `p5-us-ground-m1a1-armyrecognition` | C | Maximum road speed and public range estimate; another public table lists 67 km/h/465 km, reflecting convention differences |
| Crew | 4 | `p5-us-ground-m1a1-armyrecognition` | C | Professional reference identifies driver, gunner, loader and commander; station interfaces are not itemized |
| Main armament | 120 mm M256 smoothbore cannon | `p5-us-ground-m1a1-armyrecognition` | C | Professional reference; ammunition family and ready/stowed split are not itemized |
| Secondary armament | 12.7 mm commander machine gun and 7.62 mm coaxial machine gun | `p5-us-ground-m1a1-armyrecognition` | C | Professional reference; exact mount and ammunition loadout are not itemized |
| Main-gun ammunition | 40 × 120 mm rounds | `p5-us-ground-m1a1-armyrecognition` | C | Public compilation; 34 turret-bustle + 6 hull-box arrangement is a reference configuration |
| Mission systems | Laser rangefinder, digital fire-control computer, stabilized day/thermal sight, NBC detector/protection | `p5-us-ground-m1a1-armyrecognition` | C | Public system summary; sensor performance and network interfaces are not itemized |
| Public protection | Chobham/composite armour with depleted-uranium plate and NBC-protected crew compartment context | `p5-us-ground-m1a1-armyrecognition` | C | Professional reference; no armour thickness or calibrated protection value inferred |

## Source References

- `p5-us-ground-m1a1-army-tm`
- `p5-us-ground-m1a1-weaponspecs`
- `p5-us-ground-m1a1-armyrecognition`
