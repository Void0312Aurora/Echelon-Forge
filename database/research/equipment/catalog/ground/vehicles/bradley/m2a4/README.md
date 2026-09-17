# M2A4 Bradley

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/bradley/m2a4/README.md`
Owner: `database/equipment-data`
Content status: current variant parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-m2a4` |
| Family / variant | Bradley Fighting Vehicle / M2A4 |
| Service state | Current modernized Bradley standard; M2A3 and M2A4E1 are separate |
| Role | Infantry fighting vehicle |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Geometry | 6.55 m length × 3.60 m width × 2.98 m height | `p5-us-ground-m2a4-weaponspecs` | C | Named M2A4 public-data geometry; stowage/antenna convention not itemized |
| Combat mass | 36,287 kg | `p5-us-ground-m2a4-weaponspecs` | C | Public compilation's combat-weight convention; armour, fuel and stowage state may vary |
| Powerplant | Cummins VTA-903E-T675 diesel, 675 hp | `p5-us-ground-m2a4-defensivelines` | C | Secondary production summary; block-specific engine fit not independently resolved |
| Transmission | HMPT-800-3ECB improved automatic | `p5-us-ground-m2a4-defensivelines` | C | Secondary production summary; exact serial/block applicability is bounded to M2A4 |
| Road speed / range | Up to 66 km/h; approximately 402 km public range | `p5-us-ground-m2a4-weaponspecs` | C | Public compilation; terrain/load/fuel effects are not modeled |
| Crew / carried infantry | 3 crew + 6 Army infantry; public seat estimate 7 | `p5-us-ground-m2a4-cpe` | A/C | Army role page states six infantry; WeaponSpecs lists seven troop seats; retain both conventions |
| Main armament | 25 mm M242 Bushmaster chain gun | `p5-us-ground-m2a4-cpe` | A | Ammunition mix and ready-round count are not itemized |
| Anti-armour armament | TOW missile launcher | `p5-us-ground-m2a4-cpe` | A | Missile block, reloads and launcher elevation limits are not itemized |
| Main-gun ammunition | Approximately 900 × 25 mm rounds | `p5-us-ground-m2a4-weaponspecs` | C | Public compilation; exact AP/HE mix and stowage state not itemized |
| TOW ready missiles | 2 launcher tubes ready; reload quantity not itemized | `p5-us-ground-m2a4-weaponspecs` | C | Public M2A4 summary; missile block and reload stowage are configuration-sensitive |
| Secondary armament | 7.62 mm M240C coaxial machine gun plus dual TOW launcher | `p5-us-ground-m2a4-weaponspecs` | C | Public M2A4 summary; ready/reload missile count is configuration-sensitive |
| Mission systems | Digitized electronics, thermal sights, diagnostics, communications and improved electrical power | `p5-us-ground-m2a4-cpe` | A | Army modernization description; detailed sensor/radio performance not itemized |
| Public protection | Aluminium hull with spaced laminate and steel applique; NBC protection; reactive applique context | `p5-us-ground-m2a4-weaponspecs` | C | Qualitative public description; no thickness or calibrated protection level |

## Source References

- `p5-us-ground-m2a4-cpe`
- `p5-us-ground-m2a4-baesystems`
- `p5-us-ground-m2a4-weaponspecs`
- `p5-us-ground-m2a4-defensivelines`
