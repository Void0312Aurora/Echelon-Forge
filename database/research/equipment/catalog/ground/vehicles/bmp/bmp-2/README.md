# BMP-2

Language: English canonical. Chinese companion: not provided.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/bmp/bmp-2/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-ru-ground-bmp2` |
| Family / variant | BMP / BMP-2 |
| Role | Infantry fighting vehicle |
| Configuration scope | Baseline BMP-2; BMP-2M and export retrofit values excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Combat mass | 14.3 t | `p5-ru-ground-bmp2-armyrecognition` | C | Baseline BMP-2 specification; applique/ERA kits excluded |
| Length | 6.73 m | `p5-ru-ground-bmp2-armyrecognition` | C | Army Recognition overall dimension |
| Width | 3.15 m | `p5-ru-ground-bmp2-armyrecognition` | C | Army Recognition overall dimension |
| Height | 2.45 m | `p5-ru-ground-bmp2-armyrecognition` | C | Overall reference; turret orientation excluded |
| Engine | UTD-20 four-stroke diesel, 285/300 hp at 2,600 rpm | `p5-ru-ground-bmp2-armyrecognition` | C | Baseline powerpack; retrofit power not assumed |
| Transmission | Manual, 5 forward + 1 reverse gears | `p5-ru-ground-bmp2-armyguide` | C | Army Guide product entry; gear ratios and torque curve are outside public data |
| Road speed | 65 km/h | `p5-ru-ground-bmp2-armyrecognition` | C | Maximum road speed; tactical cross-country model uses a bounded 20-45 km/h range |
| Water speed | 7 km/h | `p5-ru-ground-bmp2-armyrecognition` | C | Fully amphibious track propulsion; water conditions alter realized speed |
| Operational range | 550-600 km | `p5-ru-ground-bmp2-armyrecognition` | C | Public sources differ by fuel/load; simulation uses 550 km nominal and 600 km upper bound |
| Crew | 3 | `p5-ru-ground-bmp2-armyrecognition` | C | Commander, gunner, driver |
| Carried infantry | 7 (six rear seats plus one forward infantry seat) | `p5-ru-ground-bmp2-armyguide` | C | Army Guide narrative reconciles its six rear seats with the seven-person specification load |
| Main armament | 30 mm 2A42 autocannon, two-axis stabilized; 200-300/500 rpm selectable rates | `p5-ru-ground-bmp2-armyrecognition` | C | Baseline two-man turret |
| Main-gun ammunition payload | 500 x 30 mm rounds | `p5-ru-ground-bmp2-armyguide` | C | Army Guide specification |
| Secondary armament | 7.62 mm PKT coaxial machine gun; AT-4/AT-5 ATGM launcher | `p5-ru-ground-bmp2-armyrecognition` | C | Launcher accepts either named missile family |
| Secondary ammunition payload | 2,000 x 7.62 mm rounds; 2-4 ATGM ready rounds (bounded estimate) | `p5-ru-ground-bmp2-armyguide` | C | PKT count is direct; ATGM count is a 2-4 canister-load estimate because the page gives launcher type but no carried count |
| Mission systems | BPK-2-42M/BPK-3 day/night sights, OU-3GA2 IR searchlights, two-axis stabilizer, GPK-59 gyrocompass, PAZ NBC overpressure and 902V smoke system | `p5-ru-ground-bmp2-armyrecognition` | C | Detection/identification range modeled as a bounded 1-4 km envelope from sighted range and direct-fire role |
| Protection | Welded steel hull/turret; front resists 23 mm AP at 500 m, sides 7.62 mm AP at 75 m; NBC and smoke systems | `p5-ru-ground-bmp2-armyrecognition` | C | Arc-specific categorical protection; mine and applique protection are excluded from baseline |
| Amphibious capability | Yes; fully amphibious, track-propelled at 7 km/h | `p5-ru-ground-bmp2-armyguide` | C | Baseline BMP-2 configuration; no preparation time is assumed |

All target fields now contain a direct value or an explicitly bounded simulation estimate; BMP-2M and family values are not silently substituted.

## Source References

- `p5-ru-ground-bmp2-armyrecognition`
- `p5-ru-ground-bmp2-armyguide`
- `p5-ru-ground-bmp2-roe` (historical pointer retained in the source registry)
