# T-72B3

Language: English canonical. Chinese companion: not provided.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/t-72/t-72b3/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-ru-ground-t72b3` |
| Family / variant | T-72 / T-72B3 |
| Role | Main battle tank |
| Configuration scope | Standard T-72B3 modernization described by Army Recognition; Model 2016/B3M packages excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Combat mass | 46.0 t | `p5-ru-ground-t72b3-armyrecognition` | C | Army Recognition B3 specification; fuel, ERA and ammunition fit can shift mass by roughly +/-1.5 t (simulation bound) |
| Length (gun forward) | 9.53 m | `p5-ru-ground-t72b3-armyrecognition` | C | Army Recognition overall dimension |
| Width | 3.59 m | `p5-ru-ground-t72b3-armyrecognition` | C | Army Recognition overall dimension |
| Height | 2.22 m | `p5-ru-ground-t72b3-armyrecognition` | C | Overall reference; antenna/stowed equipment excluded |
| Engine | V-84-1 diesel, 840 hp | `p5-ru-ground-t72b3-armyrecognition` | C | Army Recognition B3 mobility value; later B3M powerpack is excluded |
| Transmission | Hydraulically assisted manual transmission, 7 forward + 1 reverse gears | `p5-ru-ground-t72b3-armyrecognition` | C | Page mobility section; ratios and torque curve are outside public data |
| Road speed | 70 km/h | `p5-ru-ground-t72b3-armyrecognition` | C | Maximum road speed; cross-country model uses a bounded 20-50 km/h tactical range |
| Operational range | 500 km | `p5-ru-ground-t72b3-armyrecognition` | C | Maximum cruising range; fuel reserve modeled as 10-20% of nominal |
| Crew | 3 | `p5-ru-ground-t72b3-armyrecognition` | C | Driver, gunner, commander arrangement |
| Main-gun ammunition payload | 38 x 125 mm rounds, including 22 carousel-ready | `p5-ru-ground-t72b3-armyrecognition` | C | Army Recognition ammunition statement |
| Coaxial ammunition payload | 2,000 x 7.62 mm PKTM rounds (simulation estimate) | `p5-ru-ground-t72b3-armyrecognition` | C | 2,000-round bound follows Soviet MBT belt-load convention; not a counted B3 inventory |
| Cupola ammunition payload | 300 x 12.7 mm NSV rounds (simulation estimate) | `p5-ru-ground-t72b3-armyrecognition` | C | 300-round bound follows comparable vehicle load convention; not a counted B3 inventory |
| Main armament | 125 mm 2A46M-5 smoothbore gun; 9M119/Refleks ATGM compatible | `p5-ru-ground-t72b3-armyrecognition` | C | B3 configuration statement |
| Secondary armament | 7.62 mm PKTM coaxial; 12.7 mm NSV cupola machine gun | `p5-ru-ground-t72b3-armyrecognition` | C | Mount and ammunition quantities are represented explicitly above |
| Mission systems | Sosna-U second-generation optical/thermal sight, digital ballistic computer, weather sensors, automatic target tracker, laser-warning/jamming suite and GLONASS | `p5-ru-ground-t72b3-armyrecognition` | C | Thermal/identification performance modeled as a 3-5 km bounded envelope |
| Protection | Kontakt-5 ERA, 20 mm glacis applique, turret-roof applique, laser warning/jamming; Arena-E APS option | `p5-ru-ground-t72b3-armyrecognition` | C | Categorical arc protection; base armour equivalence is bounded at 120-600 mm RHAe by arc for simulation and is not a measured B3 value |
| Amphibious capability | Limited fording, not swimming: 1.2 m hard-bottom crossing without kit; up to 5 m with deep-fording kit; 20 min preparation | `p5-ru-ground-t72b3-armyrecognition` | C | Direct page values; snorkel preparation and recovery time are configuration-dependent |

All target fields now contain a direct value or an explicitly bounded simulation estimate; no T-72 family value is silently substituted.

## Source References

- `p5-ru-ground-t72b3-armyrecognition`
- `p5-ru-ground-t72b3-roe` (historical pointer retained in the source registry)
