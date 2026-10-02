# Type 052D Luyang III

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/naval/ships/surface-combatant/type-052/type-052d/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-cn-naval-type052d` |
| Family / variant | Type 052 / Type 052D Luyang III guided-missile destroyer |
| Role | Area air-defence, anti-ship, anti-submarine and land-attack surface combatant |
| Configuration scope | Baseline Type 052D hull (approximately 155-157 m) and PLAN combat-system fit; stretched Type 052DL (162 m), export Type 052DE, and ship-specific later upgrades are excluded |
| Service context | PLAN in-service presence is officially confirmed by China Military Online's 2025 report on Cangzhou (hull 125); technical values below are professional secondary/public estimates because PLAN does not publish a complete class data sheet |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Length overall | 156 m (public range 155-157 m) | `p5-cn-naval-type052d-navaltechnology`; `p5-cn-naval-type052d-armyrecognition` | C | Baseline Type 052D; the 162 m Type 052DL flight-deck stretch is excluded |
| Beam | 18 m | `p5-cn-naval-type052d-navaltechnology`; `p5-cn-naval-type052d-armyrecognition` | C | Public values span roughly 17-18 m; use 18 m for the baseline geometry and retain the narrower value as a cross-check |
| Draft | 6.5 m | `p5-cn-naval-type052d-navaltechnology`; `p5-cn-naval-type052d-armyrecognition` | C | Draft/load condition is not published by PLAN; source pages converge on 6.5 m |
| Standard displacement | Estimated 6,000-6,500 t; simulation midpoint 6,250 t | `p5-cn-naval-type052d-navaltechnology`; `p5-cn-naval-type052d-wikipedia` | C | No official normal-displacement figure was found. Bound is derived from the direct 7,500 t full-load value and public normal-displacement summaries (about 6,000-6,500 t); do not present midpoint as an official specification |
| Full-load displacement | 7,500 t | `p5-cn-naval-type052d-navaltechnology`; `p5-cn-naval-type052d-armyrecognition` | C | Full-load semantics are explicit on both professional reference pages |
| Propulsion | CODOG, two QC-280 gas turbines plus two MTU 20V 956TB92 diesel engines, twin shafts | `p5-cn-naval-type052d-navaltechnology`; `p5-cn-naval-type052d-armyrecognition` | C | Baseline public fit; later domestic diesel substitutions and export packages are excluded |
| Propulsion power | 2 x 28 MW gas turbines + 2 x 6 MW diesels = 68 MW installed mechanical power (about 91,000 hp) | `p5-cn-naval-type052d-navaltechnology` | C | Engine ratings are page values; total is arithmetic sum, not a claim that all four engines run simultaneously in CODOG high-speed mode |
| Maximum speed | 30 kt (public Army Recognition wording: 30+ kt) | `p5-cn-naval-type052d-navaltechnology`; `p5-cn-naval-type052d-armyrecognition` | C | Use 30 kt as the conservative class value; 30+ kt is retained as an upper-bound wording, not a separate tested value |
| Range | 4,500 nmi at 15 kt | `p5-cn-naval-type052d-navaltechnology` | C | Baseline public endurance point; another professional page gives 5,000 nmi at 18 kt, requiring cross-check before changing the model value |
| Crew | 280 | `p5-cn-naval-type052d-navaltechnology`; `p5-cn-naval-type052d-armyrecognition` | C | Public class complement; ship-specific embarked detachment is not included |
| Aviation payload | One light/medium helicopter, Z-9C or Ka-28; flight deck and enclosed hangar | `p5-cn-naval-type052d-navaltechnology`; `p5-cn-naval-type052d-armyrecognition` | C | Baseline Type 052D aviation fit; Type 052DL's larger flight deck and Z-20 operation are excluded |
| Sensors and combat systems | Four Type 346A multifunction AESA arrays; Type 364 altitude/surface search; Type 366 surface-search/targeting; Type 517H air search; Type 760 navigation; Type 349A gun fire control; Type 754 helicopter control; MGK-335MS-E hull sonar; towed-array and variable-depth sonar; IR-17 optronics; jammers and JSIDLS data link | `p5-cn-naval-type052d-navaltechnology`; `p5-cn-naval-type052d-armyrecognition` | C | Public equipment identification; exact radar modes, ranges, electronic-order-of-battle and software baselines are not disclosed |
| Main weapon | 1 x H/PJ-38 130 mm multipurpose naval gun | `p5-cn-naval-type052d-navaltechnology`; `p5-cn-naval-type052d-armyrecognition` | C | Gun designation is stable across the professional references; ammunition outfit is not public |
| Vertical-launch weapons | 64-cell GJB 5860 universal VLS for mission-dependent HHQ-9/HHQ-9B SAMs, HQ-16/DK-10A medium-range SAMs, YJ-18/YJ-83 anti-ship missiles, CJ-10 land-attack missiles and CY-5 ASW rockets | `p5-cn-naval-type052d-navaltechnology`; `p5-cn-naval-type052d-armyrecognition` | C | Cell count is direct; missile mix is loadout-dependent and must not be interpreted as simultaneous full inventory |
| Close-in and torpedo weapons | 1 x H/PJ-12 30 mm CIWS (later ships may use Type 730/1130); 24-cell HQ-10 launcher; 2 x triple 324 mm torpedo tubes for Yu-7-class ASW torpedoes | `p5-cn-naval-type052d-navaltechnology`; `p5-cn-naval-type052d-armyrecognition` | C | CIWS and decoy fit varies by batch; baseline record keeps the common gun/missile self-defence suite and flags later substitutions |
| Protection / survivability | Inward-sloped superstructure and reduced-signature layout; layered AESA/EO/sensor coverage, EW jammers and decoy launchers; no public armour thickness or damage-tolerance data | `p5-cn-naval-type052d-navaltechnology`; `p5-cn-naval-type052d-armyrecognition` | C | Stealth-layout and countermeasure features are directly reported. For simulation, use a bounded categorical `medium-high modern destroyer survivability` envelope with no armour-equivalent inference; damage-control and signature measurements remain cross-check items |

All target fields contain a direct value or an explicitly bounded estimate. Official service presence is kept separate from the Tier C technical estimates, and Type 052DL/052DE values are not silently merged into this baseline.

## Source References

- `p5-cn-naval-type052d-mnd`
- `p5-cn-naval-type052d-navaltechnology`
- `p5-cn-naval-type052d-armyrecognition`
- `p5-cn-naval-type052d-wikipedia`
