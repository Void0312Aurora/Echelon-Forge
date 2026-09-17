# T-90M Proryv

Language: English canonical. Chinese companion: not provided.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/t-90/t-90m/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-ru-ground-t90m` |
| Family / variant | T-90 / T-90M Proryv |
| Role | Main battle tank |
| Configuration scope | T-90M export/product description; do not merge with T-90A or T-90MS |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Combat mass | 46.5 t | `p5-ru-ground-t90m-armyrecognition` | C | Army Recognition specification; applique, fuel and ammunition fit can shift mass by roughly +/-1.5 t (simulation bound) |
| Length (hull; gun-forward bound) | 6.68 m hull; 9.63 m gun-forward bound | `p5-ru-ground-t90m-armyrecognition` | C | Page lists hull length; gun-forward value is a bounded geometry estimate retained for stowage/clearance calculations |
| Width | 3.78 m | `p5-ru-ground-t90m-armyrecognition` | C | Army Recognition specification with side equipment |
| Height | 2.23 m | `p5-ru-ground-t90m-armyrecognition` | C | Army Recognition specification; antenna state excluded |
| Engine | V-92S2 diesel, 1,000 hp; bounded 1,000-1,130 hp package range | `p5-ru-ground-t90m-armyrecognition` | C | 1,000 hp is page mobility value; 1,130 hp is retained only as alternate Proryv package bound, not blended |
| Transmission | Manual, 7 forward + 1 reverse gears | `p5-ru-ground-t90m-armyrecognition` | C | Page mobility section; gear ratios and torque curve are outside the public data |
| Road speed | 60 km/h | `p5-ru-ground-t90m-armyrecognition` | C | Maximum road speed; cross-country model uses a bounded 20-45 km/h tactical range |
| Operational range | 550 km | `p5-ru-ground-t90m-armyrecognition` | C | Maximum cruising range at stated load; fuel reserve modeled as 10-20% of nominal |
| Crew | 3 | `p5-ru-ground-t90m-armyrecognition` | C | Driver, gunner, commander arrangement |
| Main-gun ammunition payload | 43 x 125 mm rounds, including 22 carousel-ready | `p5-ru-ground-t90m-armyrecognition` | C | Page ammunition statement; remaining rounds are hull/turret stowage |
| Coaxial ammunition payload | 1,250 x 7.62 mm PKT rounds | `p5-ru-ground-t90m-armyrecognition` | C | Page ammunition statement |
| RWS ammunition payload | 300 x 12.7 mm NSVT rounds | `p5-ru-ground-t90m-armyrecognition` | C | Page ammunition statement |
| Main armament | 125 mm 2A46M-4 smoothbore gun; Refleks ATGM compatible | `p5-ru-ground-t90m-armyrecognition` | C | Page names 2A46M-4; earlier 2A46M-5 references are treated as a separate gun-package claim |
| Secondary armament | 7.62 mm PKT coaxial; 12.7 mm NSVT remote weapon station | `p5-ru-ground-t90m-armyrecognition` | C | Mount and ammunition quantities are represented explicitly above |
| Mission systems | Stabilized fire-control, hunter-killer automatic target tracker, day target detection to 5,000 m, fire detection/suppression, NBC and GLONASS/navigation context | `p5-ru-ground-t90m-armyrecognition` | C | Detection value is a page claim; weather/thermal performance is modeled as a 3-5 km bounded envelope |
| Protection | Relikt ERA, modular hull ERA, RPG net and bar-slat armour; soft/hard-kill APS stated | `p5-ru-ground-t90m-armyrecognition` | C | Simulation uses categorical frontal/side/rear protection; equivalent thickness is not inferred |
| Amphibious capability | Not amphibious; deep-fording kit fitted, with a 1.2-5 m water-crossing bound | `p5-ru-ground-t90m-armyrecognition` | C | 1.2-5 m is a bounded engineering estimate for kit-equipped Russian MBT fording, not a measured T-90M depth |

All target fields now contain a direct value or an explicitly bounded simulation estimate; no T-90 family value is silently substituted.

## Source References

- `p5-ru-ground-t90m-armyrecognition`
- `p5-ru-ground-t90m-roe` (historical pointer retained in the source registry)
