# A-50U

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/aewc/a-50/a-50u/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-24`
Equipment ID: `eq-ru-air-a50u`
Content status: parameter-complete research record for the Russian A-50U; A-50 family baselines and A-50U-specific public performance are kept as separate rows.

## Identity

- Family: A-50
- Variant: A-50U
- Role: Airborne early warning and control aircraft
- Configuration scope: Russian A-50U modernisation. A-50 baseline, A-50M and export A-50EI are not merged into the variant-specific rows.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| Russian Aerospace Forces | In service / modernised | `p5-ru-air-a50u-xinhua`; `p5-ru-air-a50u-airforcetechnology` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Crew | 5 flight crew + 10 mission crew | `p5-ru-air-a50u-airforcetechnology` | C |
| Length | 46.59 m, A-50 family carrier baseline | `p5-ru-air-a50u-redstar` | C |
| Wingspan | 50.50 m, A-50 family carrier baseline | `p5-ru-air-a50u-redstar` | C |
| Height | 14.80 m, A-50 family carrier baseline | `p5-ru-air-a50u-redstar` | C |
| Wing area | 300 m², A-50 family carrier baseline | `p5-ru-air-a50u-redstar` | C |
| Radar antenna diameter | 10.20 m, A-50 family baseline | `p5-ru-air-a50u-redstar` | C |
| Powerplant | Four PS-90A turbofans, family baseline | `p5-ru-air-a50u-redstar` | C |
| Engine thrust | 16,000 kgf each, family baseline | `p5-ru-air-a50u-redstar` | C |
| Maximum takeoff mass, family table | 190,000 kg | `p5-ru-air-a50u-redstar` | C |
| Maximum takeoff mass, A-50U public performance | 210,000 kg | `p5-ru-air-a50u-xinhua` | A |
| Normal takeoff mass, family table | 180,000 kg | `p5-ru-air-a50u-redstar` | C |
| Cruise speed, family table | 800 km/h | `p5-ru-air-a50u-redstar` | C |
| Maximum level speed, A-50U public performance | 850 km/h | `p5-ru-air-a50u-xinhua` | A |
| Service ceiling, family table | 12,000 m | `p5-ru-air-a50u-redstar` | C |
| A-50U public altitude statement | 9,000 m climb/operating reference | `p5-ru-air-a50u-xinhua` | A |
| Range, family table | 7,500 km | `p5-ru-air-a50u-redstar` | C |
| Effective operational range, A-50U | 7,500 km | `p5-ru-air-a50u-xinhua` | A |
| Continuous reconnaissance endurance | 6 h | `p5-ru-air-a50u-xinhua` | A |
| Aerial refuelling | Yes | `p5-ru-air-a50u-xinhua` | A |
| A-50U mission system | Upgraded airborne radar-warning and guidance complex; improved low-speed/low-observable target detection | `p5-ru-air-a50u-xinhua`; `p5-ru-air-a50u-airforcetechnology` | A/C |
| Radar and control capacity | Family public reference: 50–60 targets tracked and 10–12 fighters guided; no universal A-50U detection curve asserted | `p5-ru-air-a50u-airforcetechnology` | C |
| Defensive systems | Electronic countermeasures/self-defence system | `p5-ru-air-a50u-airforcetechnology` | C |

## Configuration Boundary

The Xinhua article supplies the A-50U-specific public performance claims. RedStar supplies common A-50/Il-76-derived geometry and engine baselines, which are labelled as family values rather than A-50U certification. Airforce Technology supplies the upgrade, crew and mission-system context but explicitly mixes family and U variants. The two 190/210 tonne maximum-takeoff readings and 800/850 km/h speed readings remain separate, preserving source conditions instead of forcing a single value.

## Source References

- `p5-ru-air-a50u-xinhua`: `raw/sources/xinhuanet/p5-ru-air-a50u-xinhua/manifest.md` — A-50U-specific public performance
- `p5-ru-air-a50u-airforcetechnology`: `raw/sources/airforce_technology/p5-ru-air-a50u-airforcetechnology/manifest.md` — upgrade, crew and mission-system context
- `p5-ru-air-a50u-redstar`: `raw/sources/redstar/p5-ru-air-a50u-redstar/manifest.md` — labelled family baseline
