# BMP-1

Language: English canonical. Chinese companion: not provided.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/bmp/bmp-1/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-ru-ground-bmp1` |
| Family / variant | BMP / BMP-1 (Object 765 Sp2-Sp4 baseline) |
| Role | Amphibious infantry fighting vehicle |
| Configuration scope | Soviet BMP-1 baseline with 2A28 Grom turret; BMP-1P, BVP-1 licensed builds, and later 30/40 mm retrofit turrets are excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Geometry | 6.735 m length x 2.940 m width x 2.068 m height; 0.370 m ground clearance | `p5-ru-ground-bmp1-valka` | C | Valka Object 765 dimensions; early short-bow and Czechoslovak long-bow hulls differ slightly |
| Combat mass | 13,000 kg nominal; 13,200 kg for 1973-1979 Sp3 production | `p5-ru-ground-bmp1-valka` | C | Variant-series range retained; armor kits and fuel state can add approximately 0-0.8 t |
| Powerplant | UTD-20 six-cylinder V diesel, liquid cooled, 220 kW (about 295 hp) at 2,600 rpm; 980 Nm nominal torque | `p5-ru-ground-bmp1-valka` | C | Baseline engine; 300 hp figures in other references are rounding, while 360 hp retrofit claims are excluded |
| Transmission | Mechanical synchromesh gearbox, 5 forward + 1 reverse; planetary steering units | `p5-ru-ground-bmp1-valka` | C | Gear ratios and clutch-control law are not published |
| Road / cross-country speed | 65 km/h road; 40-45 km/h cross-country; approximately 7 km/h afloat | `p5-ru-ground-bmp1-valka` | C | Dry-road and average unpaved-road values; water speed depends on trim, loading and current |
| Operational range | 550-600 km road nominal; 460-500 km cross-country planning bound | `p5-ru-ground-bmp1-valka` | C | Public sources differ by fuel/load and subseries; 460-600 km retained rather than collapsed |
| Crew / payload | 3 crew (commander, gunner, driver) + 8 infantry; 460 L fuel | `p5-ru-ground-bmp1-valka` | C | Valka seating capacity is eight; some export/medical layouts reduce seats |
| Main armament / ammunition | 73 mm 2A28 Grom low-pressure smoothbore, 40 PG-15V rounds; 9S428 rail for 4 x 9M14M Malyutka ATGM | `p5-ru-ground-bmp1-valka` | C | Sp2-Sp3 baseline; BMP-1P replaces Malyutka with Fagot/Konkurs and is excluded |
| Secondary armament / ammunition | 7.62 mm PKT coaxial machine gun, 2,000 rounds | `p5-ru-ground-bmp1-valka` | C | Direct Valka load figure; no bow machine guns in baseline turret |
| Mission systems | 1PN22M2 day/night gunner sight, commander/driver TNPO periscopes, 2E15/2E28M gun stabilization context, PAZ NBC filtration/overpressure, TDA exhaust smoke and 902-series smoke launchers on later subseries | `p5-ru-ground-bmp1-valka` | C | Sight/system nomenclature is the standard Object 765 fit; exact subseries and passive/IR channel require manual cross-check |
| Protection | Welded rolled-steel hull/turret: upper front 7 mm at 80 deg, lower front 19 mm at 57 deg, sides 16-18 mm, rear 16 mm, roof 6 mm, belly 5-7 mm; turret 13-23 mm; PAZ NBC and smoke systems | `p5-ru-ground-bmp1-valka` | C | Arc/thickness values are direct; no RHAe equivalence inferred, and applique/ERA retrofits are excluded |
| Water crossing | Fully amphibious, track-propelled; approximately 7 km/h forward and 2 km/h reverse afloat, no special preparation in baseline | `p5-ru-ground-bmp1-valka` | C | Requires trim-vane and bilge-pump serviceability; river current/wave state can reduce speed |

All target fields contain a direct value or an explicitly bounded estimate. Source conflicts (13.0 versus 13.2 t, 550-600 km versus 460-500 km range, and early/late turret smoke equipment) remain visible and are not silently normalized.

## Source References

- `p5-ru-ground-bmp1-valka`
- `p5-ru-ground-bmp1-mcia` (historical U.S. Marine Corps/MCIA handbook pointer; used for independent amphibious and crew cross-check)
