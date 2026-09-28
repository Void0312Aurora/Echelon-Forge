# Fujian Carrier Group Order Of Battle

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/reviews/csg_order_of_battle_20260928/csg_order_of_battle_fujian_20260928.md`
Owner: `domains/naval`
Last verified: `2026-09-28`

Language: English canonical only; no Chinese companion (dated research evidence).

Status: `2026-09-28` research-grade, non-authoritative order of battle for [Carrier Strike Group Engagement](../../work/active/carrier_strike_group_engagement/README.md) cluster `S0-A`. Values are public-source candidates; none is calibrated runtime authority. Sources are listed in the [CSG source ledger](csg_source_ledger_20260928.md).

## Scope And Conventions

- Scenario window is 2025-2026.
- Tiers: `A` official (PRC MND / Xinhua / CCTV, US DoD CMPR, CRS, ONI); `B` public-engineering / named-author analysis (USNI News, CSIS, IISS, Janes summaries, airshow manufacturer displays, Naval News); `C` sanity-check only (Wikipedia, GlobalSecurity, Military Watch, Army Recognition, forums).
- Rows marked `C-only` are supported only by Tier C sources.
- `engineering_estimate` marks a reasoned estimate, not a sourced figure; the reasoning is given inline.
- `not public` means no public value was found.
- Figures marked `export` are export-variant figures (brochure or airshow display) and are not assumed equal to the PLAN service variant.

## Order Of Battle

Context (A): CMPR 2025 lists the Southern Theater Command Navy as holding an aircraft carrier, two destroyer flotillas, three frigate flotillas, two submarine flotillas and a submarine base (`csg-cn-cmpr-2025`), so a Fujian group would draw its escorts from STC flotillas. The CMPR does not state CSG composition.

Doctrinal baseline for a Fujian (CV-18, Southern Theater, Sanya) group in 2025-2026: **1 x Type 055 + 2 x Type 052D/DL + 1 x Type 054A (or 054B) + 1 x SSN (Type 093B) + 1 x Type 901**, giving 6 escort/support units (plausible range 4-8). The PLAN has never officially disclosed a fixed CSG table of organisation. Counts below are derived from publicly tracked precedents (see Observed Precedents) and named-analyst commentary.

### Carrier And Air Wing

Status snapshot (2026-09-28):

- Commissioned 2025-11-05 at Sanya; home port Sanya (`csg-cn-fujian-mnd`, `csg-cn-fujian-plan-spokesperson`, A).
- Official sources confirm the air-wing **types** (J-35, J-15T, J-15D, KJ-600, Z-20 series) but give **no counts** and no date for embarking a full wing (`csg-cn-fujian-plan-spokesperson`, `csg-cn-airwing-dod-cmpr2025`, A).
- State media (Apr 2026) expect "full combat capability" before end-2026. Analysts doubt FOC within a year of commissioning (`csg-cn-fujian-aei-2026-04`, `csg-cn-fujian-reuters-commission`, B).
- All counts below describe a planning "full wing". They are `engineering_estimate` unless a row says otherwise.

| Class | Count (range) | Role | Justification / Source ID |
| --- | --- | --- | --- |
| Fujian (Type 003, CV-18) | 1 | CATOBAR carrier, CSG flagship | `csg-cn-fujian-mnd`, `csg-cn-fujian-xinhua` (A) |
| J-35 (carrier variant) | 12 (0-24) | Stealth fleet air defence / first-day strike | Type confirmed (A: `csg-cn-fujian-plan-spokesperson`, `csg-cn-airwing-dod-cmpr2025`). No public count. The upper value of 24 is a notional wing (`csg-cn-airwing-armyrec-2025`, C). zh-wiki gives 36-40 J-15T and J-35 combined (C). For a 2026 scenario date use 0-8, because carrier J-35 output is limited and carrier qualification is still under way (`csg-cn-fujian-aei-2026-04`). engineering_estimate |
| J-15T | 20 (12-28) | Heavy multirole, anti-ship strike, candidate buddy tanker | Type confirmed (A). 10 of the 12 "J-15" in the Oct 2024 flypast were J-15T (`csg-cn-j15t-aviationist`, B). Fills the fighter slots J-35 does not take, within a 32-40 fighter total (`csg-cn-fujian-wiki-zh`, C; `csg-cn-fujian-indsr-2025` models 34 J-15T/D). engineering_estimate |
| J-15D / J-15DT (EW) | 4 (2-6) | Escort jamming, SEAD | "J-15D" is named officially (A). Analysts designate the CATOBAR build J-15DT (`csg-cn-j15dt-twz`, `csg-cn-fujian-navalnews-commission`, B). Count of 4 from `csg-cn-fujian-wiki-zh` and `csg-cn-airwing-armyrec-2025` (both C) |
| KJ-600 | 4 (3-6) | Fixed-wing AEW&C | Type confirmed (A). At least 3 airframes in Sep 2025 footage (`csg-cn-fujian-janes-airwing`, B). 2 were on deck at commissioning (`csg-cn-fujian-aviationist-commission`, B). 4 per zh-wiki and Army Recognition (C). 6+ built fleet-wide by 2026 (`csg-cn-kj600-wiki`, C) |
| Z-20F (ASW) | 6 (4-8) | ASW (dipping sonar, lightweight torpedo), light anti-ship | "Z-20 series shipborne helicopters" (A). Z-20F on deck at commissioning carrying YJ-9-family anti-ship missiles (`csg-cn-fujian-aviationist-commission`, `csg-cn-fujian-navalnews-commission`, B). Count: zh-wiki gives about 6 Z-20; en-wiki gives about 12 helicopters in total (C). engineering_estimate |
| Z-20J / Z-20S (utility, SAR, plane guard) | 2 (2-4) | Utility, VERTREP, CSAR | Naval utility Z-20J (`csg-cn-z20f-flightglobal`, `csg-cn-z20-odin-weg`, B). "HZ-20 utility" (en-wiki, C). Which designation serves on Fujian is unconfirmed |
| Z-18F / Z-18J / Z-9S (legacy rotary) | 0 (0-4) | ASW / helicopter AEW / SAR, transitional | zh-wiki lists about 4 Z-18 and 2 Z-9S (C-only). MP-IDSA lists Z-18F (Chinese-forum sourced). Use only for scenario dates before full Z-20 fielding |
| GJ-21 (GJ-11J) UCAV | 0 (0-4) | Stealth strike / ISR loyal wingman (prospective) | CMPR says "various UAVs" without naming a type (A). GJ-21 flew with its hook down in Nov 2025 (`csg-cn-gj21-twz`, B). At-sea launch and recovery not confirmed as of 2026-05 (`csg-cn-gj21-dronewarfare`, C). Default is 0 for 2025-26 |
| **Total embarked** | ~40 fixed-wing + ~8 rotary (40-60 FW; 8-14 rotary) | - | CSIS: "Estimated 50~60 fixed-wing aircraft" (`csg-cn-fujian-csis-chinapower`, B). INDSR: about 60 in total including helicopters (B). en-wiki: 40+ fixed-wing plus 12 helicopters (C). Sina commentary: about 50 fixed-wing at full load (C). CSIS and INDSR **conflict**: CSIS counts fixed-wing only, INDSR counts all aircraft |

### Escorts, SSN, Replenishment

| Class | Count (range) | Hull examples | Role | Justification / Source ID |
| --- | --- | --- | --- | --- |
| Type 055 (Renhai CG/DDG) | 1 (1-2) | 106 Yan'an (confirmed Fujian escort, Nov 2025); Southern Theater: 105 Dalian, 107 Zunyi, 108 Xianyang | Air-defence commander, area AAW/BMD, long-range anti-ship/land strike, flag/C2 | Present in every publicly tracked PLAN CSG since 2021. PRC expert (Wang Yunfei): a carrier formation "typically requires one to two large destroyers as its main escort". Shandong sailed with two 055s in July 2024. Proceedings (May 2026) sketches 2 x 055 per group as a force-design end state. `csg-cn-fujian-mnd-20251118` (A); `csg-cn-type055-gt-20260308` (A-relay/C); `csg-cn-shandong-gt-202407` (A-relay); `csg-cn-proc-202605` (B) |
| Type 052D / 052DL (Luyang III) | 2 (1-3) | Southern Theater examples: 165 Zhanjiang (Shandong escort 2025), 164 Guilin, 162 Nanning, 173 Changsha, 174 Hefei, 175 Yinchuan (hull-to-theatre mapping is C) | Secondary AAW / radar picket, ASuW, ASW with Z-9/Z-20 | Precedents show 1-2 per group (Shandong 2023: 2; Liaoning 2022: 2; 2025-26: 1). Wikipedia's projected Fujian group has 3 x 052D + 1 x 052C (unsourced, C-only). Class of 35-37+ supports 2 per carrier. `csg-cn-shandong-wiki` (C); `csg-cn-liaoning-usni-20220503` (B); `csg-cn-054b-navalnews-202605` (B); `csg-cn-fujian-wiki` (C) |
| Type 054A (Jiangkai II) | 1 (0-2) | 554 Tongliao (confirmed Fujian escort Nov 2025; **Type 054A, not 054B**); Southern: 553 Dali, 552 Chenzhou | ASW screen (late units have VDS + towed array), point/local AAW (HHQ-16) | Present in most precedents (Shandong 2023: 2; 2025: 1). The PRC MND release names Tongliao. `csg-cn-fujian-mnd-20251118` (A); `csg-cn-fujian-idsa` (B); `csg-cn-054a-seaforces` (C) |
| Type 054B (Jiangkai III) | 0 (0-1); 1 in a late-2026 excursion | 555 Qinzhou (only Southern Theater 054B); 545 Luohe (Northern; Liaoning group May-June 2026) | Outer ASW screen with Z-20, local AAW | Naval News: the Liaoning May 2026 formation (055 + 052D + 054B + 901) is "the clearest picture to date of the PLAN's emerging carrier strike group template". PRC expert: 055/054B form a complementary pairing. Only 2 hulls exist, so the baseline keeps the 054A; in the excursion case, 555 Qinzhou replaces it. `csg-cn-054b-navalnews-202605` (B); `csg-cn-054b-usni-20260129` (B); `csg-cn-054b-sofx-202605` (C, relaying Global Times) |
| Type 052C (Luyang II) | 0 (0-1) | not verified this pass | Legacy area AAW (HHQ-9, 48-cell revolver VLS) | Only in Wikipedia's projected Fujian group (C-only). Older CSGs used 052C before 055/052D were available (Military Watch, C). Keep as a low-readiness substitute only |
| SSN: Type 093B (Shang III), or 093A | 1 (0-2) | Pennants not officially disclosed; 417+ (093B) and 413-416 (093A) per Seaforces (C-only) | Forward/independent ASW sweep, anti-surface (YJ-18 family from VLS), counter-SSN in the carrier's direct support | PRC media never reports SSN escort. Evidence is indirect: a CCTV Liaoning 10th-anniversary video (Sept 2022) showed a Type 093 and 094A alongside the Liaoning flotilla (`csg-cn-liaoning-cctv2022-eurasiantimes`, C-relay of state media). Type 093s reportedly shadowed the UK CSG in 2021 (C). ONI: 6-8 x 093B in service, "most capable operational attack submarine" (`csg-cn-ssn-usni-oni-20260305`, A via B). US CSG doctrine uses 1-2 SSNs (`csg-cn-19fortyfive-202606`, C). Baseline 1 x 093B is an analyst assumption, not an observed fact |
| SSN: Type 095 (09V) | 0 (2025-2026) | first hull launched Feb 2026 (Bohai) | Future quiet SSGN escort | In trials pipeline only. Not deployable in the scenario window. `csg-cn-095-navalnews-202602` (B) |
| Type 901 (Fuyu) AOE | 1 (0-1) | 901 Hulunhu; 905 Chaganhu | Underway replenishment (fuel, aviation fuel, ammunition, stores) at carrier speed (25 kt) | Present in most far-seas CSG deployments (Liaoning 2026: Hulunhu; Shandong 2025: Chaganhu). Only 2 hulls for 3 carriers, so a 903A substitution or none is plausible for short near-seas sorties. `csg-cn-054b-navalnews-202605` (B); `csg-cn-901-uscc-2020` (A); `csg-cn-19fortyfive-202607` (C, citing Naval News) |
| Type 903/903A (Fuchi) AOR | 0 (0-1) | not verified this pass | Substitute replenishment (19 kt max, about 18-20 kt sustained) | USCC/Jane's: 9 in service, 19 kt, 10,500 t fuel. It constrains group speed when substituted. `csg-cn-901-uscc-2020` (A) |
| New large AOE (Longxue, 271 m) | 0 (2025-2026) | unnamed, launched Jul 2026 | Future Type 004-era carrier support | Fitting out. `csg-cn-newaoe-janes-202607` (B) |

### Observed Precedents

| Date | Group | Observed composition (hull) | Reporter | Source ID |
| --- | --- | --- | --- | --- |
| 2025-11 (return 2025-11-18) | Fujian (18) first live-force training | Type 055 Yan'an (106); frigate Tongliao (554); "multiple vessels" (others unnamed) | PRC MND / China Military Online | `csg-cn-fujian-mnd-20251118` (A); `csg-cn-fujian-usni-20251119` (B) |
| 2025-06 | Shandong (17) Western Pacific, dual-carrier | Type 055 Yan'an (106); Type 052D Zhanjiang (165); Type 054A Yuncheng (571); replenishment Chaganhu (Type 901 reported; one outlet says Type 903A) | JMSDF JSO via Overt Defense / Wikipedia | `csg-cn-shandong-overtdefense-202506` (C); `csg-cn-shandong-wiki` (C) |
| 2025-06 | Liaoning (16) Western Pacific | Type 055 Nanchang (101); Type 052D Tangshan (122) (+ others reported) | JMSDF JSO via Overt Defense | `csg-cn-shandong-overtdefense-202506` (C) |
| 2023-04 | Shandong (17) Joint Sword / Philippine Sea | 1 x Type 055; 2 x Type 052D; 2 x Type 054A; 1 x Type 901 | Wikipedia (JMSDF-derived) | `csg-cn-shandong-wiki` (C) |
| 2022-05 | Liaoning (16) near Japan | Type 055 Nanchang (101); Type 052D Xining (117), Urumqi (118) (+ 054A, 901 reported) | USNI News (Japan MOD) | `csg-cn-liaoning-usni-20220503` (B) |
| 2026-05/06 | Liaoning (16) Western Pacific / SCS, 40 days | Type 055 Wuxi (104); Type 052D Kaifeng (124); Type 054B Luohe (545); Type 901 Hulunhu (901) | Japan JSO via Naval News (K. Takahashi); USNI News Western Pacific Pulse 2026-06-26 | `csg-cn-054b-navalnews-202605` (B); `csg-cn-wpacpulse-usni-20260626` (B) |

Observed pattern: 1 x Type 055 + 1-2 x Type 052D + 1-2 frigates (054A, now 054B) + 1 x Type 901 (or 903A) is the recurrent publicly-tracked surface screen. SSNs are never announced; their presence is an analyst inference.

## Platform Parameters

### Fujian (Type 003)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Designation / hull | Type 003 (OSD: Fujian class), hull 18 (CV-18) | - | `csg-cn-fujian-xinhua`; `csg-cn-airwing-dod-cmpr2025` | A | - |
| Launched | 2022-06-17 | date | `csg-cn-fujian-xinhua` (June 2022); `csg-cn-fujian-csis-chinapower` (exact day) | A/B | - |
| Commissioned | 2025-11-05, Sanya | date | `csg-cn-fujian-mnd`; `csg-cn-fujian-xinhua` | A | - |
| Home port | Sanya | - | `csg-cn-fujian-plan-spokesperson` | A | Southern Theatre assignment is a Naval News inference (B). Dec 2025 Taiwan Strait transit north for maintenance / Qingdao per wikis (C) |
| Full-load displacement | >80,000 | t | `csg-cn-fujian-mnd` | A | CSIS ~80,000 (B). en-wiki 80,000-85,000 (C). naval-encyclopedia 80,000-90,000 (C). Planning range 80,000-85,000 |
| Length overall (flight deck) | 316 | m | `csg-cn-fujian-csis-chinapower` | B | Estimated from imagery. TWZ ~1,040 ft / 317 m (B). Waterline ~300 m (zh-wiki, C-only) |
| Flight-deck width (max) | 76 | m | `csg-cn-fujian-csis-chinapower` | B | CSIS labels this "beam". TWZ ~250 ft (B). A Zhihu post gives 78 m (C) |
| Waterline beam | ~40 | m | `csg-cn-fujian-wiki-zh` | C | C-only, estimate |
| Draft | ~11 | m | `csg-cn-fujian-wiki-zh` | C | C-only. naval-encyclopedia gives 9 m (C). Range 9-11 |
| Flight-deck area | >=16,330 | m2 | `csg-cn-fujian-indsr-2025` | B | Computed from 316 x 76, not measured |
| Propulsion | Conventional steam turbines + diesel generators | - | `csg-cn-fujian-csis-chinapower` | B | 8 boilers / 4 turbines / 4 shafts is C-only (`csg-cn-fujian-wiki-en`, `csg-cn-fujian-wiki-zh`). Not nuclear (B). A 2024 Naval Technology guess of gas / IEP is superseded |
| EMALS power architecture | MVDC integrated power system | - | `csg-cn-fujian-wiki-en` | C | C-only; not officially described |
| Installed power | not public | MW | - | - | naval-encyclopedia 220,000 hp (C-only). Liaoning/Shandong ~147 MW (Eurasia Review, C). engineering_estimate 140-165 MW: steam plant inherited from Type 002 plus generator margin |
| Max speed | ~30-31 | kn | `csg-cn-fujian-csis-chinapower` | B | CSIS "Estimated ~30-31". zh-wiki 31 (C). en-wiki 30 (C) |
| Endurance | ~8,000-10,000 | nmi | `csg-cn-fujian-reuters-commission` | B | Reuters: "some analysts" estimate refuelling after ~10,000 nmi. en-wiki 8,000-10,000 (C). naval-encyclopedia ~6,000 (C). Speed basis not stated |
| Catapults | 3 electromagnetic (2 bow, 1 waist) | count | `csg-cn-fujian-mnd` (EM type); `csg-cn-fujian-usni-commission` (3); `csg-cn-fujian-indsr-2025` (layout) | A/B | EM type is A. Count and layout are B. An R&D team member quoted in `csg-cn-fujian-idsa` gives "three electromagnetic rails" |
| Arresting gear | Arrested recovery confirmed; 4 wires; reported electromagnetic | count | `csg-cn-fujian-xinhua-emals-2025-09` (arrested landing); `csg-cn-fujian-navaltech` (4 wires) | A/B | "Electromagnetic arresting gear" is C-only (en-wiki, Eurasia Review) |
| Angled-deck angle | ~6 | deg | `csg-cn-fujian-cnn-deck` | B | Former USN officers' estimate from imagery (USN ~9 deg). The landing area overlaps the waist catapult |
| Aircraft elevators | 2, starboard (one forward, one aft of island) | count | `csg-cn-fujian-navaltech`; `csg-cn-fujian-indsr-2025` | B | Elevator >21 m, able to lift two J-15 side by side (`csg-cn-fujian-sina-2022`, C-only) |
| Ammunition elevator | >=1, port side aft | count | `csg-cn-fujian-sina-2022` | C | C-only |
| Helicopter spots | 5 marked | count | `csg-cn-fujian-navaltech` | B | From 2024 imagery |
| Hangar size | not public | m | - | - | Sina: hangar holds >24 fighter-size aircraft plus several helicopters; gain over Shandong "limited" because the hull and machinery layout is inherited (C-only). engineering_estimate ~30 aircraft hangar, ~24-30 on deck |
| Aircraft capacity | 50-60 fixed-wing (est.); ~60 total incl. rotary | aircraft | `csg-cn-fujian-csis-chinapower`; `csg-cn-fujian-indsr-2025` | B | en-wiki 40+ FW + 12 helicopters (C). NSJ 40-60, "up to 70" (C). Planning range 40-70 total |
| Sortie / launch rate | not public | launches/day | - | - | "Up to 180 catapult launches/day" (Army Recognition, C-only). Air-ops rate ~60% of Nimitz (`csg-cn-fujian-cnn-deck`, B, opinion) |
| SAM | 4 x HHQ-10 launchers | mounts | `csg-cn-fujian-navaltech` (4 missile PDS); `csg-cn-fujian-csis-chinapower` ("4 x missile-based point defence") | B | Cells per launcher conflict: 24 (`csg-cn-fujian-idsa`, forum-sourced) vs 18 on Liaoning/Shandong (CSIS). HHQ-10 identification: `csg-cn-fujian-twz-2024` (B) |
| CIWS | 4 x Type 1130 (H/PJ-11) 30 mm | mounts | `csg-cn-fujian-navaltech`; `csg-cn-fujian-csis-chinapower` ("at least 4") | B | Type 1130 identification: `csg-cn-fujian-idsa` (B) and zh-wiki (C) |
| ASW / anti-torpedo | 6-tube 324 mm anti-torpedo launcher; 12-tube anti-swimmer launcher; 24/32-cell 122 mm multipurpose rocket launcher | - | `csg-cn-fujian-idsa` | B | IDSA's source for this list is Chinese forum material, so treat as C-quality. en-wiki cites SCMP 2026-07 for the anti-torpedo launcher (C). Mount count not public |
| Main radar | Island-integrated fixed-face AESA; designation not officially disclosed | - | `csg-cn-fujian-navaltech`; `csg-cn-fujian-twz-2024` | B | "Type 346B" is C-only (`csg-cn-fujian-eurasiareview`; `csg-cn-fujian-nsj` says "possibly"). zh-wiki gives 346A plus X-band (C). CSIS "TBD". Treat 346B as `estimate` |
| Radar bands / max detection | S/C + X dual band; 500-600 | km | `csg-cn-type346b-deagel` | C | C-only. Figure is for Type 346B on Type 055 and does not carry over to Fujian unless the fit is confirmed |
| Ship's company | ~2,000 | persons | `csg-cn-fujian-csis-chinapower` | B | Estimate |
| Air wing personnel | ~1,000 | persons | `csg-cn-fujian-csis-chinapower` | B | Estimate; total about 3,000 (en-wiki, C, agrees) |
| Readiness | Commissioned; trials, ship-aircraft integration and formation training continuing | - | `csg-cn-fujian-plan-spokesperson` | A | Global Times / CCTV (Apr 2026): full combat capability in 2026. AEI: FOC unlikely within a year. PLATracker: at least one more year (`csg-cn-fujian-reuters-commission`) |

### J-35 (carrier variant)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Carrier operation | EM catapult launch and arrested landing aboard Fujian | - | `csg-cn-fujian-xinhua-emals-2025-09` | A | - |
| Fujian air-wing membership | Named | - | `csg-cn-fujian-plan-spokesperson`; `csg-cn-airwing-dod-cmpr2025` | A | CMPR wording is "likely intends" |
| Configuration | Single-seat, twin-engine LO; folding wing, hook, launch bar | - | `csg-cn-j35-migflug` | C | Naval wing has larger chord and area than J-35A |
| Length | 17.3 | m | `csg-cn-j35-migflug` | C | AVIC figure (relayed) applied to FC-31, J-35 and J-35A alike |
| Wingspan (spread) | 11.5 | m | `csg-cn-j35-migflug` | C | Folded span not public |
| Height | 4.8 | m | `csg-cn-j35-migflug` | C | - |
| Empty weight | not public | kg | - | - | Western estimates 12,000-13,500 (C) |
| MTOW | 28,000-30,000 | kg | `csg-cn-j35-migflug` | C | 28,000 = Janes figure for FC-31 prototype 2 (relayed). 30,000 = Chinese-language sources for J-35 |
| Internal fuel | ~7,200 | kg | `csg-cn-j35-migflug` | C | C-only, estimate |
| Engines | 2 x WS-21 (interim, 87-93 kN AB each); WS-19 (~116 kN est.) intended | kN | `csg-cn-j35-aerocorner`; `csg-cn-j35-migflug` | C | No official engine statement. WS-19 thrust unpublished |
| Max speed | Mach 1.8 | Mach | `csg-cn-j35-migflug` | C | AVIC datasheet (relayed). Chinese-language sources give Mach 2.2 |
| Speed at sea level | Mach 1.14 (~1,400) | km/h | `csg-cn-j35-migflug` | C | - |
| Combat radius, internal fuel | ~1,250 | km | `csg-cn-j35-migflug`; `csg-cn-j35-wiki` | C | Brochure hi-lo-hi profile. 2015 FC-31 briefing ~1,200 km. china-arms 1,350 km (C) |
| Combat radius, one refuel / ext. tanks | ~1,900 / ~2,000 | km | `csg-cn-j35-migflug` | C | External tanks remove LO |
| Service ceiling | 16,000 | m | `csg-cn-j35-migflug`; `csg-cn-j35-wiki` | C | - |
| g limits | +9 / -3 | g | `csg-cn-j35-migflug` | C | - |
| Radar | AESA; type not public | - | `csg-cn-j35-migflug` | C | Export FC-31 was advertised with KLJ-7A. Nothing public for the naval J-35 |
| Other sensors | Chin EOTS, DAS | - | `csg-cn-j35-migflug`; `csg-cn-j35-aerocorner` | C | - |
| Stations | 6 internal (ventral bay) + 6 wing | count | `csg-cn-j35-migflug` | C | Some sources say 4 internal AAM (C) |
| Max weapon load | ~8,000 (about 2,000 internal + 6,000 external) | kg | `csg-cn-j35-migflug`; `csg-cn-j35-wiki` | C | - |
| Loadout: fleet air defence (LO) | 4 x PL-15 + 2 x PL-10, internal | - | `csg-cn-j35-migflug` | C | Analyst loadout, not officially shown |
| Loadout: maritime strike (LO) | 2 x KD-88 or YJ-91 internal + 2 x PL-10 | - | `csg-cn-j35-migflug` | C | YJ-83K and YJ-12 do not fit internally; carrying them is external and non-LO |
| Air refuelling | Retractable probe (receiver) | - | `csg-cn-j35-migflug`; `csg-cn-j35-wiki` | C | Buddy-tanker role not public |
| RCS | not public | m2 | - | - | Chinese claims of 0.007-0.01 are unverified |

### J-15T

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Carrier operation | EM catapult launch and arrested landing aboard Fujian; also STOBAR-capable | - | `csg-cn-fujian-xinhua-emals-2025-09`; `csg-cn-j15t-aviationist` | A/B | Early footage showed unarmed launches (`csg-cn-fujian-reuters-commission`, B) |
| Fujian air-wing membership | Named | - | `csg-cn-fujian-plan-spokesperson`; `csg-cn-airwing-dod-cmpr2025` | A | - |
| CATOBAR features | Reinforced twin-wheel nose gear with launch bar, hook, wing and stabilator fold, tail MAWS | - | `csg-cn-j15t-aviationist` | B | Zhuhai 2024, airframe 1518 |
| Length / span | 21.9 / 14.7 (7.4 folded) | m | `p5-cn-air-j15-tni`; `csg-cn-j15-wiki` | C | Baseline J-15 values; en-wiki gives 22.28 m length |
| Empty weight | 17,500-17,700 | kg | `p5-cn-air-j15-tni`; `p5-cn-air-j15-deagel` | C | Baseline. J-15T structural delta not public |
| MTOW | 32,500-33,000 | kg | `p5-cn-air-j15-tni`; `p5-cn-air-j15-deagel` | C | Reachable in practice only from a catapult (`csg-cn-j15-migflug`, C). Maximum catapult launch weight not public |
| Internal fuel | ~9,400-9,800 | kg | `csg-cn-j15-migflug`; `csg-cn-j15-wiki` | C | 9,400 is the Su-33 figure; 9,800 is quoted for J-15 |
| Engines | 2 x WS-10-series (at least some airframes) | - | `csg-cn-fujian-janes-airwing`; `csg-cn-j15t-aviationist` | B | Some J-15T may still fly AL-31F (forum, C) |
| Max speed | Mach 2.17-2.4 | Mach | `csg-cn-j15-migflug` (2.17); `p5-cn-air-j15-tni` (2.4) | C | Not demonstrated with stores |
| Combat radius | ~1,270 (baseline, internal fuel) | km | `p5-cn-air-j15-migflug` | C | CATOBAR radius not public. China SignPost (2011, named authors) gave ~700 km from a ski jump with buddy tanking. engineering_estimate for a catapult launch: 1,000-1,300 km, trading fuel against weapons |
| Ferry range | 3,500 | km | `p5-cn-air-j15-tni` | C | Some sources mislabel this as combat radius |
| Service ceiling | 18,000 | m | `csg-cn-j15-migflug` | C | Chinese sources give 20,000 |
| Radar | New AESA (canted, pitot-less radome); designation not public | - | `csg-cn-j15dt-twz`; `csg-cn-j15t-aviationist` | B | Baseline J-15 used the Type 1493 pulse-Doppler radar (C) |
| Hardpoints / max stores | 12 / 6,500 | count / kg | `p5-cn-air-j15-deagel`; `p5-cn-air-j15-migflug` | C | Baseline values. J-15T wingtip PL-10 rails are B |
| Air-to-air | PL-15 (BVR), PL-10 (WVR, wingtip), PL-12 (legacy) | - | `csg-cn-j15t-aviationist` (PL-10 rails); `csg-cn-j15-wiki` (PL-15) | B/C | PL-15 carriage on J-15T is C-only (wiki, forum photos) |
| Anti-ship, subsonic | 4 x YJ-83K observed off Fujian (Jul 2026) | - | `csg-cn-j15t-mwm-yj83k`; `csg-cn-j15-wiki` | C | C-only. YJ-83K ~700 kg, ~230 km (MWM, C) |
| Anti-ship, supersonic | 2 x YJ-15 observed (Feb 2026, likely test); YJ-12 per Chinese military media | - | `csg-cn-j15t-usni-yj15`; `csg-cn-j15t-aviationist-yj15` | B | YJ-15 ~500 km range is C-only (MWM) |
| Land attack | AKF-98A (KD-88 family) | - | `csg-cn-j15t-usni-yj15` | B | - |
| Buddy refuelling | Buddy refuelling with a pod demonstrated on J-15; J-15T tanker role aboard Fujian not public | - | `csg-cn-j15-buddy-globaltimes` | B | Pod type UPAZ-1(A) is C-only (wiki) |
| Receiver probe | Retractable IFR probe | - | `p5-cn-air-j15-migflug` | C | YU-20 to J-15 refuelling shown in 2023 (`csg-cn-j15-buddy-globaltimes`, B) |

### J-15D / J-15DT (EW)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Fujian air-wing membership | "J-15D" named | - | `csg-cn-fujian-plan-spokesperson`; `csg-cn-airwing-dod-cmpr2025` | A | Analysts call the CATOBAR build J-15DT and the STOBAR build J-15DH (`csg-cn-j15dt-twz`, B) |
| Crew | 2 | persons | `csg-cn-j15d-janes-2024` | B | - |
| Jamming pods | 2 underwing + 2 ventral (different bands; likely high, mid and low band) | count | `csg-cn-j15d-janes-2024` | B | Band coverage is a Janes inference |
| ESM | Wingtip tactical jamming receiver (TJR) pods | - | `csg-cn-j15d-janes-2024` | B | - |
| Radar | AESA, downward-canted radome (DT) | - | `csg-cn-j15dt-twz` | B | Cant direction comes from an X post (C) |
| IRST | Removed | - | `csg-cn-j15-wiki` | C | - |
| Anti-radiation weapon | YJ-91 | - | `csg-cn-airwing-armyrec-2025` | C | C-only |
| Performance | not public | - | - | - | engineering_estimate: J-15T airframe values, radius 10-20% lower with 4 pods plus tanks |

### KJ-600

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Carrier operation | EM catapult launch and arrested landing aboard Fujian; China's first carrier-based fixed-wing AEW | - | `csg-cn-fujian-xinhua-emals-2025-09` | A | Catapult-only because of size and weight (`csg-cn-fujian-janes-airwing`, B) |
| Configuration | Twin turboprop, high wing, folding wings, four-fin tail, dorsal radome | - | `csg-cn-kj600-casi` | B | - |
| Crew | 4-6 | persons | `csg-cn-kj600-twz`; `csg-cn-kj600-casi` | B | Deagel gives 6 (C) |
| Length / span / height | 18.1 / 25 / 5.7 | m | `csg-cn-kj600-deagel`; `csg-cn-kj600-wiki` | C | C-only; close to E-2D |
| Gross / max take-off weight | 25,000-30,500 | kg | `csg-cn-kj600-casi` (25-30 t); `csg-cn-kj600-deagel` (30,500) | B/C | GlobalSecurity ~20 t (C). Deagel's 25,400 kg empty weight against a 30,500 kg MTOW is internally implausible |
| Internal fuel | ~6,000 | kg | `csg-cn-kj600-wiki` | C | C-only |
| Engines | 2 x FWJ-6C (WoJiang-6C) turboprops, 6-blade propellers | - | `csg-cn-kj600-casi` | B | 3,805 kW each is C-only (wiki) |
| Max speed | 693 | km/h | `csg-cn-kj600-deagel` | C | Cruise ~500 km/h (`csg-cn-kj600-gs`, C) |
| Service ceiling | 15,000 (as published) | m | `csg-cn-kj600-deagel` | C | Implausible for a turboprop AEW (E-2D ~10,500 m). engineering_estimate 9,000-11,000 m |
| Ferry range | 2,800 | km | `csg-cn-kj600-deagel` | C | - |
| Radius of operation | 500 | nmi | `csg-cn-kj600-deagel` | C | - |
| Endurance / time on station | ~5 (on station) | h | `csg-cn-kj600-gs` | C | C-only, relays Chinese commentary. engineering_estimate 4-6 h unrefuelled, by E-2C/D analogy |
| Radar | AESA in dorsal radome (institute attribution unconfirmed); array layout not public | - | `csg-cn-kj600-casi` | B | Rotating radome with two AESA faces (wiki, C) vs three fixed faces (social media, C) |
| Detection range | not public | km | - | - | Chinese claims: >400 km vs fighter or surface ship, ~270 km vs cruise missile, stealth tracking at 320 km (`csg-cn-kj600-gs`, C, propaganda-grade). engineering_estimate: horizon from 9 km altitude to a sea-skimmer = 4.12 x (sqrt 9000 + sqrt 10) = ~400 km; practical 300-400 km vs a ~5 m2 fighter, less vs LO targets |
| Track capacity | >200 | tracks | `csg-cn-kj600-gs` | C | C-only |
| Fleet status | >=3 airframes in Fujian footage (2025); 6+ built by 2026 | aircraft | `csg-cn-fujian-janes-airwing`; `csg-cn-kj600-wiki` | B/C | The 6+ figure relays FlightGlobal Apr 2026 (paywalled) |

### Z-20F (ASW) And Z-20J / Z-20S (Naval Utility / SAR)

Base-airframe values are reused from the Z-20 catalog leaf (`p5-cn-air-z20-*`). Naval-variant deltas are not public.

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Fujian membership | "Z-20 series shipborne helicopters" | - | `csg-cn-fujian-plan-spokesperson`; `csg-cn-airwing-dod-cmpr2025` | A | - |
| Z-20F aboard at commissioning | 2 on deck, armed with light anti-ship missiles | - | `csg-cn-fujian-aviationist-commission`; `csg-cn-fujian-navalnews-commission` | B | Aviationist identifies the missiles as YJ-9 family |
| Z-20F sensors | Chin surface-search radar, nose EO/IR, stub wings | - | `csg-cn-z20f-flightglobal` | B | Dipping sonar (ALFS-like), MAD and left-side sonobuoy launcher are C-only (`csg-cn-z20f-armyrec`) |
| Z-20F weapons | Yu-7 324 mm LWT; YJ-9-family AShM; up to 8 x KD-10 | - | `csg-cn-z20f-armyrec`; `csg-cn-fujian-aviationist-commission` | C/B | YJ-9 is B. Yu-7 and KD-10 are C-only |
| Z-20J | Naval utility / assault; no radar or EO; stub-wing weapons possible | - | `csg-cn-z20f-flightglobal`; `csg-cn-z20-odin-weg` | B | The two sources disagree on stub wings |
| Z-20S | Naval multirole / SAR; tail gear aft of the cabin | - | `csg-cn-z20-odin-weg` | B | globalmilitary lists Z-20S as a PLAAF SAR variant (C) |
| Engines | 2 x WZ-10, ~1,790 kW (2,400 shp) each | kW | `csg-cn-z20f-flightglobal` | B | Catalog band 1,600-2,000 kW (C) |
| MTOW | ~10,000 (base Z-20) | kg | `p5-cn-air-z20-globalmilitary` | C | Naval MTOW not public. engineering_estimate 10,000-10,800 (MH-60R ~10,400 as analogue) |
| Max speed | 320-360 | km/h | `p5-cn-air-z20-gs`; `p5-cn-air-z20-globalmilitary` | C | Base airframe |
| Range | 560-600 | km | `p5-cn-air-z20-globalmilitary`; `p5-cn-air-z20-gs` | C | Base airframe. ASW time on station not public; engineering_estimate 1.5-2.5 h at 100-150 km radius |
| Service ceiling | 5,400-6,000 | m | `p5-cn-air-z20-gs`; `p5-cn-air-z20-globalmilitary` | C | Base airframe |
| Crew | 2 flight crew (base) | persons | `p5-cn-air-z20-globalmilitary` | C | ASW mission crew not public; engineering_estimate 3-4 |

### GJ-21 (Naval GJ-11 Derivative, Prospective)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Official UAV reference | "Various UAVs" in the future Fujian wing; no type named | - | `csg-cn-airwing-dod-cmpr2025` | A | - |
| Identity | Naval GJ-11 derivative (GJ-11J / GJ-11H / GJ-21, all unofficial names) | - | `csg-cn-gj21-twz` | B | - |
| Carrier features | Folding wings, hook, twin nose wheel with launch bar | - | `csg-cn-gj11-wiki` | C | Hook-down flight in Nov 2025 is B (`csg-cn-gj21-twz`) |
| Test status | Hook-down flight Nov 2025; mock-up on Type 076 Jan 2026; launch-bar prototype May 2026 | - | `csg-cn-gj21-twz`; `csg-cn-gj11-wiki` | B/C | At-sea launch and recovery not confirmed as of 2026-05 (`csg-cn-gj21-dronewarfare`, C) |
| Wingspan | 14 (land GJ-11) | m | `csg-cn-gj11-wiki` | C | Naval span not public |
| Endurance / radius | ~6 / >1,500 | h / km | `csg-cn-gj11-defensepost` | C | C-only estimate for the land GJ-11 |
| Weapons | 2 internal bays | - | `csg-cn-gj11-wiki` | C | Payload not public |

### Type 055 (Renhai-class cruiser / large destroyer)

Hulls: first batch 101 Nanchang, 102 Lhasa, 103 Anshan, 104 Wuxi, 105 Dalian, 106 Yan'an, 107 Zunyi, 108 Xianyang (all in service by end-2022); second batch 109 Dongguan and 110 Anqing made their official debut on CCTV Xinwen Lianbo on 2026-03-08, assigned to the Eastern Theater (`csg-cn-type055-gt-20260308`, A-relay). Proceedings says both were commissioned in May 2025 (`csg-cn-proc-202605`, B), which conflicts with the Wikipedia date of March 2026 (C). Proceedings also reports four more hulls launched in 2025, possibly combat-ready by 2027. Southern Theater (Fujian's home theatre, Sanya) holds 105/106/107/108.

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Full-load displacement | 12,000-13,000 | t | `csg-cn-type055-usni-proc-202303`; `csg-cn-type055-wiki` | B | "12,000-13,000 tons" (Wertheim, Combat Fleets). Wikipedia cites Janes 2018 for 12-13 kt full load and Janes 2019 for about 11,000 t standard. Use 12,500 t midpoint. PRC media use "10,000-ton class". |
| Standard displacement | about 11,000 | t | `csg-cn-type055-wiki` (cites Janes 2019) | C-only | Only the Wikipedia citation chain was seen; the Janes original was not read |
| Length overall | 180 (591 ft) | m | `csg-cn-type055-usni-proc-202303` | B | Consistent across all sources |
| Beam | 20 (66 ft) | m | `csg-cn-type055-usni-proc-202303` | B | — |
| Draft | 6.6 (22 ft) | m | `csg-cn-type055-usni-proc-202303` | B | Load condition not stated |
| Max speed | 30 | kt | `csg-cn-type055-usni-proc-202303` | B | Estimate; no PLAN figure. Wikipedia also says "estimated" |
| Range | 5,000 at 18 kt | nmi | `csg-cn-type055-usni-proc-202303` | B | Wikipedia gives 5,000 nmi at 12 kt (cites Janes 2017 Rahmat). Speed attached to the range figure conflicts |
| Propulsion | COGAG, 4 gas turbines, 2 shafts, controllable-pitch propellers | — | `csg-cn-type055-usni-proc-202303` | B | Turbine type QC-280 (about 28 MW each, about 112 MW total) comes from Wikipedia/Seaforces only (C-only). Six QD-50 turbine generators of 5 MW each is `C-only` and marked "citation needed" |
| VLS | 112 universal cells: 64 forward (8x8) + 48 aft (6x8) | cells | `csg-cn-dia-2019` (112 cells, mixed munitions); `csg-cn-type055-usni-proc-202303` (layout) | A / B | Confirmed. Believed to be the GJB 5860-2006 concentric-canister standard also used on 052D (Wikipedia, C). 9 m long-cell variant claimed by Seaforces (C-only) |
| Missile mix: area SAM | HHQ-9B (ER); "range in excess of 100 nmi" | nmi | `csg-cn-type055-usni-proc-202303` | B | The Janes 2020 CCTV report supports HHQ-9B carriage. Per-ship loadout is not public; model mixes as a scenario loadout |
| Missile mix: ASCM | YJ-18 (range stated as 290 nmi) | nmi | `csg-cn-dia-2019` (YJ-18 290 nmi, 052D context); `csg-cn-type055-usni-proc-202303` | A / B | Range is an analyst figure; the subsonic-cruise / supersonic-terminal profile is not addressed in this source |
| Missile mix: ASBM / hypersonic | YJ-20 hypersonic ASBM: type-approval launch from Wuxi (104), Dec 2025; Janes range 1,500-2,000 km. YJ-21: hypersonic launch from a Type 055 shown April 2022, range estimated 1,000-1,500 km | km | `csg-cn-type055-usni-20251229`; `csg-cn-type055-usni-20260311`; `csg-cn-yj21-scmp-2022` | B | Wikipedia suggests the 2022 launch may have been YJ-20 rather than YJ-21 (C). ISW (2026-07-31) reports CCTV footage of a Type 052D launching YJ-20, the first official confirmation for 052D. Model the 055 anti-ship long-range slot as YJ-20 or YJ-21 (scenario choice); the range is analyst/Janes, not PLAN |
| Missile mix: ASW / LACM | CY-5 (Yu-8) ASW missile; CJ-10 LACM; HHQ-16 (quad-pack) | — | `csg-cn-type055-wiki`; `csg-cn-type055-seaforces` | C-only | USNI says only "antisubmarine missiles or potentially land-attack cruise missiles" (B, generic). Designations are C-only |
| Gun | 1 x 130 mm (H/PJ-45 per Wikipedia/Seaforces; H/PJ-38 in the Wikipedia body text) | mm | `csg-cn-type055-usni-proc-202303` (calibre) | B | Calibre is B. Designation conflicts between PJ-38 and PJ-45 (C). Use "130 mm single" |
| CIWS | 1 x 30 mm gun CIWS (Type 1130 / H/PJ-11, 11-barrel) + 1 x 24-cell HHQ-10 | — | `csg-cn-type055-usni-proc-202303` | B | USNI says "30-mm CIWS" and "24-cell HHQ-10". The Type 1130 designation comes from Wikipedia (C). Seaforces lists Type 730 (C). Mount designation conflicts; count 1 of each |
| Torpedoes | 2 x triple 324 mm launchers (Yu-7) | — | `csg-cn-type055-usni-proc-202303` | B | Yu-7 designation is C |
| Primary radar | 4 x S-band Type 346B (H/LJG-346B) AESA faces, about 40% larger than 052D's 346A | — | `csg-cn-type055-janes-2020` (CCTV-derived); `csg-cn-type055-usni-proc-202303` | B | Janes: dual-band system with 4 large planar faces plus 4 smaller mast panels, confirmed by a CCTV report. CCTV claims LEO satellite tracking (A-adjacent claim, unverified) |
| Secondary radar | 4 x X-band multifunction panels on integrated mast (fire control / horizon search) | — | `csg-cn-type055-janes-2020` | B | Band is from Wikipedia (C); Janes confirms only the "four smaller panels" |
| Radar range, 346B | engineering_estimate: 400-600 km against large high-altitude targets; fighter-size RCS well under that | km | `csg-cn-type346-forum` | C-only | Only social-media/forum estimates exist (346 at about 300-350 km, 346A at about 400 km, 346B at about 500-600 km). No A/B figure. Reasoning: 40% larger aperture over 346A implies about 1.2x range at equal power density (R proportional to (A*P)^(1/4) for a search radar, so (1.4*1.4)^(1/4) is about 1.18 assuming power scales with area). Radar horizon caps low-flyers at about 30-45 km for a 30 m mast. Model as a parameter sweep |
| Sonar | Bow (bulbous-bow hull) sonar + variable-depth sonar + towed array | — | `csg-cn-type055-usni-proc-202303` | B | Designations, frequencies and detection ranges are not public |
| Helicopters | 2 maritime helicopters (Z-9 class or Z-20F); hangar for two | ea | `csg-cn-type055-usni-proc-202303` | B | Z-18 is also listed by Wikipedia (C) |
| Crew | 300+ | persons | `csg-cn-type055-usni-proc-202303` | B | "thought to carry more than 300" |
| EW / decoys | EW suite; 24-barrel decoy launchers; Type 726-4 | — | `csg-cn-type055-wiki` | C-only | — |
| Command role | Carrier-group air-defence and command escort; first carrier-group integration April 2021 (Nanchang with Liaoning) | — | `csg-cn-type055-wiki`; `csg-cn-054b-navalnews-202605` | B | Naval News frames 055 as the high-end AAW and strike layer |

### Type 052D / 052DL (Luyang III)

Baseline values (full load 7,500 t, 156 m, CODOG, 30 kt, crew 280, 64 VLS) are reused from the existing naval surface-combatant catalog (source IDs `p5-cn-naval-type052d-*`, all Tier C). This section adds B-tier corroboration, the 052DL fit (the fit most likely to escort a CATOBAR carrier with Z-20), and conflicts. Class size: 35 as of Mar 2026 (Wikipedia, C) or 37 (ISW 2026-07-31, B). Proceedings (May 2026, B) says eight of the latest **Type 052DM** variant were commissioned in 2025, with total output "approaching 40" and about ten more expected. The 052DM configuration delta is not public in this pass. Southern Theater examples: 165 Zhanjiang, 164 Guilin, 162 Nanning, 173 Changsha, 174 Hefei, 175 Yinchuan (hull-to-fleet mapping is C).

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Full-load displacement, 052D / 052DL | 7,500 / 7,700 | t | `csg-cn-052d-navalnews-202303` | B | Upgrades the catalog's C-only value to B for the 7,500 t figure |
| Length, 052D / 052DL | 157 / 162 | m | `csg-cn-052d-navalnews-202303` | B | Catalog uses 156 m (range 155-157). 052DL is about 4 m longer (hangar/deck) from hull 156 Zibo onward |
| Beam | 17.2 | m | `csg-cn-052d-navalnews-202303` | B | Conflict: catalog uses 18 m (C). Prefer 17.2 m (B) |
| Draft | 6.2 | m | `csg-cn-052d-navalnews-202303` | B | Conflict: catalog uses 6.5 m (C). Load condition unstated. Prefer 6.2 m, or bound 6.2-6.5 m |
| VLS | 64 cells, 8 modules (4 forward, 4 aft); GJB 5860-2006 canister universal VLS | cells | `csg-cn-052d-navalnews-202303` | B | Confirms catalog. Load: HHQ-9 (HHQ-9B on later ships), Yu-8 ASW rocket, YJ-18, CJ-10. YJ-20 launch from a 052D shown on CCTV 2026-07-29 (`csg-cn-yj20-052d-isw-20260731`, B, relaying an official source) |
| Gun | H/PJ-45A 130 mm | mm | `csg-cn-052d-navalnews-202303` | B | Catalog says H/PJ-38. Designation conflict; calibre agrees |
| CIWS | H/PJ-12 30 mm (first 8 ships H/PJ-11) + 24-cell HQ-10 | — | `csg-cn-052d-navalnews-202303` | B | Conflict with catalog, which says H/PJ-12 with later 730/1130. Naval News states the reverse batch order (early ships PJ-11). Treat as batch-dependent |
| Radars | Type 346A (4 faces), Type 364, Type 366, Type 517B (052D) / Type 518 L-band (052DL, "different air search radar aft"), Type 760 | — | `csg-cn-052d-navalnews-202303`; `csg-cn-052d-wiki` | B | The 052DL's Type 518 L-band assignment is C (globalmilitary/Wikipedia); Naval News only notes a different aft radar. No public range figures |
| Sonar | SJD-9 hull-mounted sonar + SJG-311 variable-depth sonar; linear towed array also reported | — | `csg-cn-052d-navalnews-202303` | B | Towed array is from Wikipedia/fandom (C-only). Catalog's "MGK-335MS-E hull sonar" conflicts with SJD-9 (B); prefer SJD-9 |
| Helicopter | 052D: 1 x Z-9C (Ka-28 possible); 052DL: 1 x Z-20F (stretched deck and hangar) | ea | `csg-cn-052d-navalnews-202303` | B | Single-helicopter hangar in both variants |
| Crew | 280 | persons | `csg-cn-052d-navalnews-202303` | B | Confirms catalog |
| Turning / manoeuvring data | not public | — | — | — | No public tactical diameter or acceleration data. engineering_estimate for modelling: tactical diameter about 4-5 ship lengths (about 650-800 m) at 30 kt, typical for twin-screw 150-160 m destroyers. Unvalidated |
| Speed | 30 (30+) | kt | catalog `p5-cn-naval-type052d-navaltechnology` | C-only | No B/A source found in this pass |

### Type 054A (Jiangkai II) Frigate

Hull examples: 554 Tongliao (Fujian escort, Nov 2025), 571 Yuncheng, 568 Hengyang (Shandong escorts). About 30 original-batch hulls (2008-2019) plus a resumed 2021+ batch; class total about 40-46 (USNI 2026-01 says "over 40"; Wikipedia says 46 active, C). Tongliao belongs to the resumed batch (commissioned about Nov 2023) and is therefore expected to have the late-build ASW fit.

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Full-load displacement | about 4,000 | t | `csg-cn-054a-usni-proc-202006` | B | Wikipedia gives 3,963 t, Seaforces 4,050 t (C). Standard displacement is about 3,600 t (C-only) |
| Length / beam / draft | 134 (440 ft) / 16 (52.5 ft) / about 4.9 (16 ft) | m | `csg-cn-054a-usni-proc-202006` | B | Draft varies by source: 4.5 m Seaforces, 5 m Wikipedia, 6 m blog (C) |
| Max speed | 27 | kt | `csg-cn-054a-usni-proc-202006` | B | Conflict: Seaforces 28 kt, GlobalSecurity "30 kn estimated" (C). Use 27 kt (B) |
| Range | up to 8,000 at economical speed | nmi | `csg-cn-054a-usni-proc-202006` | B | Seaforces gives 4,000 nmi at 18 kt (C). Speed-dependent; the difference is plausible from economical vs 18 kt cruise |
| Propulsion | CODAD, 4 x licence-built SEMT Pielstick 16PA6 STC diesels, 2 shafts | — | `csg-cn-054a-globalsecurity` | C-only | Per-engine rating conflicts: 5.7 MW (GlobalSecurity), 6.75 MW (Seaforces), 4.72 MW (blog) |
| Crew | 190 | persons | `csg-cn-054a-usni-proc-202006` | B | Naval-technology says 165; Seaforces 180 (C) |
| VLS | 32 cells (H/AKJ-16) forward of bridge: HHQ-16 SAM + Yu-8 ASW rockets | cells | `csg-cn-054a-usni-proc-202006` | B | Confirmed. The H/AKJ-16 designation is C |
| SAM range | HHQ-16 20-40 nmi | nmi | `csg-cn-dia-2019`; `csg-cn-054a-usni-proc-202006` | A / B | Newer HHQ-16 versions reportedly extended to 85 nmi (`csg-cn-054b-usni-proc-202503`, B, "reportedly") |
| ASCM | 8 x YJ-83 in 2 quad launchers; range about 100 nmi | nmi | `csg-cn-054a-usni-proc-202006` | B | 2025 article gives 100-135 nmi depending on variant |
| Gun | 1 x 76 mm (H/PJ-26) | mm | `csg-cn-054a-usni-proc-202006` | B | Designation is C. Type 054AG (543 Linfen, 580 Ordos) is stretched with a 100 mm gun (C-only) |
| CIWS | 2 x 30 mm (Type 730 / H/PJ-12 early batches; H/PJ-11 / Type 1130 later batches) | — | `csg-cn-054a-usni-proc-202006` | B | USNI says late units have an "improved 30-mm CIWS". Designations by flight are C (Seaforces) |
| ASW weapons | 2 x triple 324 mm torpedo tubes (Yu-7); 2 x 6-tube 240 mm ASW rocket launchers; Yu-8 from VLS | — | `csg-cn-054a-usni-proc-202006` | B | — |
| ASW sensors | Hull sonar (all); variable-depth + towed-array sonar on late-production units (from the 17th unit, Huanggang, onward) | — | `csg-cn-054a-usni-proc-202006`; `csg-cn-054a-wiki` | B | USNI: "thought to possess" VDS and towed array (14 later units). Sonar designations (MGK-335, SJD-9 etc.) are C. Tongliao (554), a resumed-batch hull, is assumed to have the VDS/TAS fit (inference) |
| Radars | Type 382 3D air search (Top Plate derivative), Type 366 / Mineral-ME surface/OTH, MR-90 derived SAM illuminators, 2 x Type 347G fire control | — | `csg-cn-054a-globalsecurity`; `csg-cn-054b-globalsecurity` | C-only | Fregat-MAE-5 "120 km aircraft / 50 km sea-skimmer" range comes from a blog only (C-only) |
| Helicopter | 1 x Z-9 (AS365 derivative) or Ka-28; hangar | ea | `csg-cn-054a-usni-proc-202006` | B | Z-20 does not fit the standard 054A hangar (inference from the 054B / 052DL stretch rationale) |

### Type 054B (Jiangkai III) Frigate

Hulls: 545 Luohe (Hudong, commissioned 2025-01-22, Northern Theater; operational capability announced 2026-01-22; first carrier-group deployment with Liaoning May-June 2026); 555 Qinzhou (Huangpu, commissioned May 2025, Southern Theater; `csg-cn-054b-gt-202505`). A third hull was reported building at Hudong-Changxingdao (Janes, Jan 2026). Qinzhou (555) is the only Southern Theater 054B and therefore the most plausible 054B for a Sanya-based Fujian group.

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Displacement | 5,000-6,000 | t | `csg-cn-054b-usni-proc-202503` | B | SCMP/Navy Recognition say about 6,000 t; Army Recognition about 5,000 t full load (C). Official figure not public. Use 5,500 t midpoint |
| Length / beam | about 147 (482 ft) / about 18 (59 ft) | m | `csg-cn-054b-usni-proc-202503`; `csg-cn-054b-janes-202601` | B | Janes (imagery + state media) gives 147 x 18 m against 134 x 16 m for 054A. Beam of 18.5 m in SeaWaves (C) |
| Draft | not public | m | — | — | engineering_estimate 5.0-5.5 m (054A draft scaled with displacement at similar L/B/T) |
| Propulsion | CODAD (combined diesel and diesel) | — | `csg-cn-054b-usni-proc-202503`; `csg-cn-054b-twz-202501` | B | Army Recognition says "full electric propulsion" with gas-turbine generators (C), which conflicts with USNI/TWZ (CODAD). Use CODAD. 4 x CS16V27 diesels at 7.28 MW each (Army Recognition) is C-only |
| Max speed | "reliable details have yet to surface" (USNI); 28 kt (Army Recognition) | kt | `csg-cn-054b-usni-proc-202503`; `csg-cn-054b-armyrecognition` | C-only | The 28 kt figure is C-only. engineering_estimate 27-29 kt |
| Range | not public (>5,000 nmi per Army Recognition) | nmi | `csg-cn-054b-armyrecognition` | C-only | Global Times experts say "longer range than 054A" (qualitative, state media) |
| Crew | about 240 | persons | `csg-cn-054b-usni-proc-202503` | B | Estimate |
| VLS | 32 cells forward of bridge, HHQ-16 + Yu-8 | cells | `csg-cn-054b-usni-proc-202503`; `csg-cn-054b-twz-202501` | B | A 48-cell VLS on future hulls is speculated (Defence Security Asia, C-only). Keep 32 |
| ASCM | 8 x YJ-83 (2 quad launchers); 100-135 nmi | nmi | `csg-cn-054b-usni-proc-202503` | B | — |
| Gun | 1 x 100 mm (H/PJ-87 derivative) | mm | `csg-cn-054b-usni-proc-202503`; `csg-cn-054b-twz-202501` | B | Designation per TWZ/Luck |
| Point defence | 1 x 24-tube HHQ-10 (hangar roof) + 1 x 11-barrel 30 mm (Type 1130) | — | `csg-cn-054b-usni-proc-202503`; `csg-cn-054b-twz-202501` | B | — |
| Radars | Dual-face (back-to-back) rotating AESA on foremast (S-band "mini-shield"); possible second rotating AESA aft; integrated RF mast | — | `csg-cn-054b-usni-proc-202503` | B | S-band attribution and the replacement of Type 382/366 are C (GlobalSecurity). No range figures |
| Sonar | Hull-mounted + variable-depth + towed-array sonar | — | `csg-cn-054b-usni-proc-202503` | B | Designations and ranges are not public. ASW is framed as the primary role by Naval News (2026) and The Drive (C) |
| Torpedoes | 2 x triple 324 mm in covered bays | — | `csg-cn-054b-usni-proc-202503` | B | — |
| Helicopter | 1 x Z-20 (flight deck + hangar) | ea | `csg-cn-cmpr-2025`; `csg-cn-054b-usni-proc-202503` | A / B | CMPR 2025: 054B "is larger than the Type 054A, has enhanced firepower, and can carry larger utility helicopters, such as the Z-20" |

### SSN — Type 093A (Shang II) And Type 093B (Shang III); Type 095 Status

Force (early 2026, ONI testimony to USCC, 2026-03-02): 6-8 Type 093B in service since 2022, each with 24 VLS cells, described by ONI as "the PLA Navy's most capable operational attack submarine"; plus 2 x Type 093 and 4 x Type 093A. Hull numbers are not officially published: pennants 407-409 (093), 413-416 (093A) and 417+ (093B) come from Seaforces (C-only). PRC state media never discloses SSN escort of carrier groups; SSN presence in a Fujian group is an analyst assumption (see Order Of Battle).

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| 093B in-service count | 6-8 | boats | `csg-cn-ssn-usni-oni-20260305` | A (ONI via B) | ONI commander RADM Brookes testimony as reported by USNI News. 7-9 launched since 2022 (IISS Feb 2026 via secondary reporting, B); 2 more launched H1 2026 (C) |
| 093B VLS | 24 cells | cells | `csg-cn-ssn-usni-oni-20260305` | A (ONI via B) | Conflict: Feb 2025 imagery (Shugart/CNAS) shows 12 open hatches (`csg-cn-093b-eurasiantimes-202502`, C-relay of B analyst); a CSSC model shows 18 cells (`csg-cn-093b-navalnews-202410`, B). Possible explanation: a 12-hatch view of a 24-cell arrangement, or a batch difference (unresolved). Use 24 (ONI) as baseline; sensitivity case 12 |
| 093B VLS weapons | Unspecified by ONI; likely YJ-18 family ASCM (YJ-18B sub-VLS variant), CJ-10 LACM, possibly new supersonic/hypersonic AShMs shown at the Sept 2025 parade | — | `csg-cn-ssn-usni-oni-20260305` | B | IISS (via 19FortyFive) assesses the cells will initially hold high-speed AShMs. YJ-18B designation is C-only |
| 093A VLS | None (the hump behind the sail is towed-array handling, not VLS) | — | `csg-cn-093-wiki` (citing Carlson & Wang 2023, CMSI CMR-30) | C (B-origin) | Conflict: Seaforces and older reporting claim "093G" has VLS (C). CMR-30 (B) could not be downloaded (Cloudflare); relayed by Wikipedia. Treat 093A as torpedo-tube-launched weapons only |
| Torpedo tubes | 6 x 533 mm bow tubes (4 upper, 2 lower) | tubes | `csg-cn-093-navaltechnology`; `csg-cn-093-wiki` | C-only | 533 vs 650 mm conflict noted by Seaforces/TNI (C). Use 533 mm |
| Weapons load (tubes) | 20 torpedoes or 36 mines (basic load) | ea | `csg-cn-093-navaltechnology` | C-only | Mixed load with tube-launched YJ-18 / YJ-82 ASCM possible |
| Heavyweight torpedo | Yu-6: 533 mm, wire + active/passive + wake homing, max about 65 kt, range about 45 km (at cruise speed) | kt / km | `csg-cn-yu6-globalsecurity`; `csg-cn-yu6-wiki` | C-only | Reputed Mk 48 derivative (Janes per forum, C). Speed and range combination is not simultaneous; model as two-speed (attack / transit). Yu-9 electric variant exists (C) |
| Submarine-launched ASCM | YJ-18: subsonic cruise about Mach 0.8, terminal sprint up to Mach 3 within about 20 nmi of target; DoD range 290 nmi (about 540 km) | nmi | `csg-cn-yj18-uscc-2015` | A (DoD figure via USCC) | USCC staff paper notes ONI/Carlson/Janes alternative estimate of about 120 nmi (B). Range conflict, factor of 2.4. Run both |
| Submerged displacement | 093/093A about 6,675 t; 093B 6,700-7,000 t | t | `csg-cn-093-wiki` | C-only | PLAN Navy Day 2025 posters (per Army Recognition, C) show Type 093 at about 120 m, 13 m, 5,000 t surfaced / 8,000 t submerged. That conflicts with Western estimates; the posters may be deliberately generic |
| Length / beam | 093: 108.5 m; 093B: about 110 m; beam about 11 m | m | `csg-cn-093-wiki`; `csg-cn-093-globalsecurity` | C-only | Poster values 120 x 13 m (C). 19FortyFive gives 093B at about 6,200 t (C) |
| Propulsion | 2 PWR (about 70-75 MW class, speculative), single shaft; 093B pump-jet | — | `csg-cn-093-wiki`; `csg-cn-ssn-kirchberger-uscc-2023` | C-only | Pump-jet on 093B is widely reported (B-tier Naval News and TWZ imagery analyses). Reactor count and ratings are speculative |
| Max submerged speed | 093: 28 kt; 093A/B: 30 kt (design) | kt | `csg-cn-093-wiki` | C-only | PLAN 2025 Navy Day poster: 28 kt for "Type 093" (A-adjacent official poster, relayed by Army Recognition, C). Use 30 kt for 093A/B, 28 kt as a conservative bound |
| Quiet (tactical) speed | not public | kt | — | — | engineering_estimate 8-12 kt for 093A, 12-16 kt for 093B, scaled from the Type 095 claim "silent speed not less than 18 kt" (Ma Hongwei via Kirchberger, B) and the generational gap |
| Test depth | about 400 | m | `csg-cn-ssn-armyrecognition-navyday2025` | C-only | The 2025 PLAN Navy Day poster value (official poster relayed by a C outlet; the primary was not seen). globalmilitary.net also gives 400 m (C). Type 095 claim: at least 600 m (Ma Hongwei via Kirchberger USCC 2023, B) |
| Crew | about 100 | persons | `csg-cn-093-wiki` | C-only | — |
| Sensors | Bow/hull sonar, flank arrays (H/SQC-207 reported), passive intercept, towed array (093A onward), Type 359 radar | — | `csg-cn-093-wiki`; `csg-cn-093-seaforces` | C-only | Detection ranges are not public |
| Acoustic signature (relative) | 093: about Victor I-III class; 093A: about Victor II (early) to Victor III (late pair); 093B: possibly Sierra I class | relative | `csg-cn-093-wiki` (citing Carlson & Wang CMR-30); ONI 2009 chart (093 noisier than Victor III) via `csg-cn-093-seaforces` | C (B-origin) | Conflicting claims: Chinese sources say 093 is at 110 dB, "on par with Akula" (C, not credible); GlobalSecurity says US places 093B between LA Flight I and Flight III (C). No absolute broadband source level is public. Model as relative noise classes, not dB |
| Type 095 (09V) status | First hull launched at Bohai Feb 2026 (about 110-115 m, beam 12-13 m, X-tail, likely pump-jet); two further new-design hulls launched late May / early June 2026 (Bohai and Jiangnan, per Luck via TWZ); not operational | — | `csg-cn-095-navalnews-202602`; `csg-cn-095-twz-202609` | B | Displacement of 9,000-11,000 t is C-only (GlobalSecurity). ONI calls 095 a guided-missile SSN. Years of trials remain, so it is **not** in the 2025-2026 OOB. Include only as a 2028+ excursion |

### Type 901 (Fuyu / Hulunhu-class) Fast Combat Support Ship (AOE)

Hulls: 901 Hulunhu (ex-965, commissioned 2017-09-01) and 905 Chaganhu (ex-967, commissioned Dec 2018). Wikipedia hull renumbering is C. Hulunhu supported Liaoning in May-June 2026 (B). Only two are in service at the start of 2026 (Naval News count via 19FortyFive, C-relay). With 3 carriers and 2 x Type 901, Fujian will often sail with a Type 903/903A (19 kt, about 23 kt t) instead, which is a speed-coupling constraint.

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Full-load displacement | 45,000 (USCC/Jane's table: 48,000) | t | `csg-cn-054b-navalnews-202605` (45 kt); `csg-cn-901-uscc-2020` (48 kt) | A / B | USCC 2020 (Tier A publisher, figures compiled from Jane's Fighting Ships) says 48,000. Naval News, TWZ and Wikipedia say 45,000. Bound 45-48 kt |
| Length / beam / draft | 240-241 / 31-31.5 / 10.8 | m | `csg-cn-901-uscc-2020` (241 m); `csg-cn-newaoe-twz-202607` (240 x 31 m) | A / B | Draft 10.8 m is C-only (Wikipedia) |
| Propulsion | 4 x QC-280 gas turbines (about 28 MW each, about 112 MW total), inferred from gas-turbine exhausts | — | `csg-cn-901-uscc-2020` (gas turbines, from photos); `csg-cn-901-wiki` (QC-280) | A / C | The turbine model and rating are C-only |
| Max speed | 25 | kt | `csg-cn-901-janes-2019`; `csg-cn-901-uscc-2020` | B / A | "Estimated". Design intent is carrier-group speed-matching (Type 903A sustains only about 18-20 kt, per NMF India, C) |
| Liquid transfer stations | 5 (3 port, 2 starboard): fuel oil + aviation fuel | stations | `csg-cn-901-janes-2019`; `csg-cn-901-uscc-2020` | B / A | Port-heavy layout matches carriers having starboard islands (USCC) |
| Solid transfer rigs | 2 (food, armament, general stores) | rigs | `csg-cn-901-janes-2019` | B | — |
| Fuel capacity | about 20,000 | t | `csg-cn-901-uscc-2020` | A (Jane's-derived) | Split between F-76-equivalent and JP-5-equivalent is not public |
| Total cargo capacity | about 25,000 | t | `csg-cn-901-uscc-2020` | A (Jane's-derived) | Implies about 5,000 t of dry cargo and ammunition (arithmetic). VLS reload at sea is not demonstrated publicly: model as not available |
| Helicopters | 2 x Z-8 / Z-18 (VERTREP), hangar | ea | `csg-cn-901-uscc-2020` | A (Jane's-derived) | — |
| Self-defence | 4 x 30 mm H/PJ-13 CIWS | — | `csg-cn-newaoe-twz-202607` | B | — |
| Transfer rate | not public | — | — | — | USCC notes a small-bore hose in the 903A Fuzhou UNREP photo, suggesting slow transfer; Type 901 rate unobserved. engineering_estimate for modelling: 2-3 kt/h (about 2,000-3,000 t/h) aggregate fuel transfer across stations, comparable to Western AOEs. Unvalidated |
| Crew | not public | persons | — | — | — |

### New Large Replenishment Ship (COMEC Longxue, Guangzhou) — 2026, Not In Service

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Existence / status | Hull under construction since at least Feb 2026; first identified by Janes in imagery from 25 Mar 2026; launched between 9 and 12 July 2026 (dock flooded, moved to fitting-out berth); CSSC released a ground photo in May 2026 | — | `csg-cn-newaoe-janes-202604`; `csg-cn-newaoe-janes-202607`; `csg-cn-newaoe-twz-202607` | B | No PRC government designation or confirmation. Type number is unknown |
| Length / beam | about 271 / about 37 | m | `csg-cn-newaoe-janes-202604` | B | Imagery scaling |
| Displacement | 60,000-65,000 (analyst estimate) | t | `csg-cn-newaoe-interestingengineering` | C-only | Not from Janes. Treat as engineering_estimate (scaling 45 kt by (271/240)(37/31) gives about 60.6 kt at equal draft/Cb, which is consistent) |
| Features | Forward bridge superstructure, aft superstructure with twin-door hangar and flight deck, multiple midships RAS pillars, slab-sided high-volume hull | — | `csg-cn-newaoe-twz-202607`; `csg-cn-newaoe-janes-202604` | B | Station count not yet countable |
| Intended role | Support for larger carriers (Type 004) and larger, more diverse air wings; simultaneous escort resupply | — | `csg-cn-newaoe-scmp-202607` (quoting Janes analyst Sean O'Connor) | B | Analyst assessment. Not available for a 2025-2026 Fujian group (fitting out; trials likely 2027+) |

## Weapons

US-side numbers (DoD/ONI/CRS/USCC) are *assessments*, often decade-old and rounded to nm; PRC official media (MND/CCTV/Xinhua) almost never publish range/speed for in-service PLAN weapons. Where a PRC official figure exists (e.g. Type 1130 rate of fire) it is cited as Tier A. Many popular "spec sheet" numbers trace back to export brochures (FL-3000N, LY-80N, PL-15E, C-802/C-803, YJ-12E) or to a single press report; those are flagged `export` or back-traced where possible. Designation hazard (2025-2026): the 2022 Type 055 hypersonic VLS launch was widely called "YJ-21"; after the 3 Sep 2025 Victory Day parade unveiled YJ-15/YJ-17/YJ-19/YJ-20, much analysis re-attributed the *ship-launched* round to YJ-20, with YJ-21 as the air-launched (H-6K/N; export YJ-21E) weapon.

### YJ-18 / YJ-18A (Ship/Submarine VLS Anti-Ship Cruise Missile)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
|---|---|---|---|---|---|
| Role | Anti-ship cruise missile (ASCM); land-attack variants reported | - | csg-cn-yj18-csis | B | US designation CH-SS-NX-13 |
| Launch platforms (surface) | Type 052D (Luyang III), Type 055 (Renhai) universal VLS | - | csg-cn-yj18-csis; csg-cn-oni-2015 | A/B | ONI 2015 confirmed deployment on ships and subs; exact 054B/055/052D load-out mix not public |
| Launch platforms (subsurface) | Type 039 Song / 039A-B Yuan (torpedo-tube encapsulated), Type 093 Shang | - | csg-cn-yj18-csis; csg-cn-crs-rl33153 | A/B | CRS/ONI: YJ-18 replacing YJ-82 on Song, Yuan, Shang. Sub variant is tube-launched (533 mm), not VLS, on Song/Yuan; 093B VLS reported (C-only, not verified here) |
| Max range | 290 (≈537) | nm (km) | csg-cn-yj18-uscc (citing DoD); csg-cn-yj20-usni-2026 | A/B | DoD figure; USNI (2026) gives "270-290 nm" for YJ-12/YJ-18 class |
| Range band | 220-540 | km | csg-cn-yj18-csis | B | Lower bound likely all-supersonic or anti-ship low-low profile; not decomposed publicly |
| Cruise speed | Mach 0.8 | Mach | csg-cn-yj18-csis; csg-cn-yj18-uscc | A/B | "~600 mph" (USCC) |
| Terminal speed | Mach 2.5-3.0 | Mach | csg-cn-yj18-csis; csg-cn-yj18-uscc | A/B | USCC: "reportedly up to Mach 3.0" (media-sourced) |
| Sprint onset distance | ~20 | nm | csg-cn-yj18-uscc | A | USCC attributes to media reports, not DoD; Wikipedia's "180 km cruise + 40 km sprint" split is C-only (Klub-analogy derived) |
| Flight profile | Sea-skimming cruise, supersonic terminal dash (separating terminal stage) | - | csg-cn-yj18-uscc; csg-cn-yj18-csis | A/B | USCC: "most likely" sea-skimming; radar horizon break ~16-18 nm |
| Guidance | INS + BeiDou satellite nav midcourse; active radar terminal seeker | - | csg-cn-yj18-csis | B | Seeker band / anti-jam features not public; anti-radiation variant mentioned by CSIS |
| Warhead | 150-300 (HE; anti-radiation option reported) | kg | csg-cn-yj18-csis | B | Wide band = unknown; Wikipedia 140-300 kg (C) |
| Launch weight | <1,579 | kg | csg-cn-yj18-csis | B | Upper bound (Klub-derived); C-sources repeat 1,579 kg |
| Length (with booster) | <8.2 | m | csg-cn-yj18-csis | B | Klub-derived |
| Cells per missile | 1 per universal VLS cell (one canister per cell) | - | engineering_estimate | - | Reasoning: ~8.2 m, ~0.5-0.53 m class missile vs PLAN universal VLS (~9 m cell, ~0.85 m CCL canister); multi-packing not reported |
| YJ-18A | Improved variant; 2019 parade display; 2025-26 CCTV footage of a black radar-absorbent-coated "new type" in VLS test | - | csg-cn-yj18-scmp-2026; csg-cn-yj18-csis | B | Performance deltas vs YJ-18 not public; SCMP identification is "specialists", not PLA |
| IOC | ~2014-2015 | year | csg-cn-yj18-csis; csg-cn-oni-2015 | A/B | ONI confirmed deployment April 2015 |

### YJ-21 (Hypersonic Anti-Ship Ballistic Missile; Air-Launched KD-21 / Export YJ-21E)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
|---|---|---|---|---|---|
| Role | Hypersonic anti-ship ballistic missile (ASBM), carrier-kill mission | - | csg-cn-dod-cmpr-2025; csg-cn-crs-rl33153 | A | DoD 2025 CMPR explicitly calls YJ-21 a "hypersonic anti-ship ballistic missile" |
| Launch platform: air | H-6K/N bomber (bomber-launched version revealed May 2024); export YJ-21E shown at Air Show China 2024 | - | csg-cn-dod-cmpr-2025 | A | J-10C photographed with YJ-21E Dec 2025 (C-only, defence-blog) — NOT a Fujian air-wing weapon on current evidence |
| Launch platform: ship | Type 055 VLS test-fire April 2022 "possibly designated the YJ-21" (DoD wording via CRS) | - | csg-cn-crs-rl33153 | A | CONFLICT: after the Sept 2025 parade, analysts re-attributed the ship-launched round to YJ-20 (see YJ-20 rows). Treat "ship-launched YJ-21" as unresolved; model the ship ASBM slot as YJ-20 for 2026 |
| Max range | ~1,500 (≈810) | km (nm) | csg-cn-crs-rl33153 | A | CRS quotes a press/secondary figure ("approximately 1,500 km"), not a DoD assessment; export YJ-21E described ">2,000 km combat range" by SCMP 2022 (B, likely includes carrier aircraft radius) |
| DoD air-launched system reach | 4,000-5,500 (H-6 + YJ-21/CJ-20, land attack row) | km | csg-cn-dod-cmpr-2025 | A | Total reach = missile + ~3,500 km H-6K/N combat radius; missile-only range not stated by DoD |
| Cruise / terminal speed | Mach 6 cruise / Mach 10 terminal | Mach | csg-cn-crs-rl33153 | A | CRS repeats a 2023 PLA Strategic Support Force article figure; treat as PRC-claimed, not US-assessed |
| Flight profile | Boost + quasi-ballistic / glide, manoeuvring terminal dive | - | csg-cn-dod-cmpr-2025 (ASBM class); csg-cn-yj21-wiki | A/C | Detailed trajectory (apogee, glide vs MaRV) not public |
| Guidance / seeker | Not public; radar seeker inferred | - | csg-cn-yj21-turdef | C-only | Seeker type (active/passive radar, IR) unconfirmed |
| Warhead | Conventional; mass not public | kg | csg-cn-yj21-wiki | C-only | not public |
| Length | ~8.3 | m | csg-cn-yj21-wiki | C-only | Fits ~9 m PLAN universal VLS cell if ship variant exists |
| Cells per missile | 1 (small enough to fit a surface combatant VLS cell — DoD) | - | csg-cn-crs-rl33153 | A | "small enough to fit into a surface combatant's VLS cell" (DoD via CRS) |

### YJ-20 (Ship-Launched Hypersonic ASBM; Likely The Type 055/052D Round)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
|---|---|---|---|---|---|
| Public debut | 3 Sep 2025 Victory Day parade (with YJ-15, YJ-17, YJ-19) | date | csg-cn-yj20-gt-2025; csg-cn-yj20-usni-2026 | A/B | Global Times reporting PLA footage |
| Ship launch | Type 055 Wuxi (104) "finalization test" released 28 Dec 2025 (China Military Bugle, PLA News Media Center); Type 052D launch footage released 29 Jul 2026 | - | csg-cn-yj20-gt-2025; csg-cn-yj20-usni-2026 | A/B | Finalization test = design-phase close-out before production; IOC status still not officially stated |
| Range | 1,500-2,000 (Janes, via USNI Mar 2026) / "600-900 miles" (Janes, via USNI Jul 2026) / 1,000-1,500 km (SCMP) | km | csg-cn-yj20-usni-2026; csg-cn-yj20-usni-2026-03; csg-cn-yj20-scmp | B | CONFLICT inside Janes-derived reporting (≈965-1,450 km vs 1,500-2,000 km). Suggest scenario band 1,000-1,500 km, sensitivity to 2,000 km |
| Speed | >Mach 6 cruise, up to ~Mach 9-10 terminal | Mach | csg-cn-yj20-twz | B | TWZ "generally considered"; no US official figure |
| Flight profile | Boost-glide, biconic glide body; near-vertical terminal attack claimed | - | csg-cn-yj20-gt-2025 | B | Named PRC expert (Zhang Junshe) description; not a PLA spec |
| Guidance | Satellite nav + mid-course updates, active radar and/or IR terminal ("believed") | - | csg-cn-yj20-twz | B | Speculative |
| Dimensions / cell | <9 m length, <850 mm diameter; 1 per HT-1 universal VLS cell (055, modified 052D) | m / mm | csg-cn-yj20-scmp | B | SCMP estimate from imagery |

### YJ-12 (Supersonic Ramjet Anti-Ship Missile; Air-Launched, Also J-15 Per PRC Media)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
|---|---|---|---|---|---|
| Role | Supersonic air-launched ASCM (ship-launched YJ-12A and coastal YJ-12B also exist) | - | csg-cn-yj12-csis-img; csg-cn-yj12-usni-2026 | B | |
| Launch platforms | H-6K/G/J bombers; J-15 (per Chinese military media via USNI); JH-7A reported | - | csg-cn-yj12-usni-2026; csg-cn-dod-cmpr-2025 | A/B | J-15 carriage from PRC media; whether J-15T/J-35 on Fujian carry it operationally: not public |
| Max range | 400-500 (CSIS); ~500 (Janes, via USNI 2026) | km | csg-cn-yj12-csis-img; csg-cn-yj12-usni-2026 | B | Wikipedia attributes "270 nm (500 km)" to US government (C, not traced to primary here). Range is profile-dependent: hi-lo shorter, hi-hi longer |
| DoD system reach (H-6 + YJ-12/YJ-83) | 3,100-4,000 | km | csg-cn-dod-cmpr-2025 | A | Combined bomber radius (~3,500 km) + missile; not missile-only |
| Export CM-302 range | ~290 | km | csg-cn-yj12-wiki | C-only, export | MTCR-driven export limit; NOT PLAN figure |
| Speed | Mach 2.5-4 reported (≈Mach 3 typical) | Mach | csg-cn-yj12-wiki; csg-cn-yj12-mda | C-only | No A/B source found giving a speed number; treat Mach 3 as mid-estimate |
| Flight profile | High-altitude supersonic cruise with terminal dive, or lo-lo sea-skim; terminal evasive manoeuvres reported | - | csg-cn-yj12-wsn | C-only | Terminal altitude 5-15 m (weaponsystems.net) C-only |
| Guidance | INS + BeiDou midcourse (datalink updates reported); active radar terminal | - | csg-cn-yj12-wiki | C-only | |
| Warhead | ~200 (CSIS); 205-500 reported range | kg | csg-cn-yj12-csis-img | B | Wide spread; 500 kg (MDAA) C-only and likely overstated |
| Propulsion | Integrated solid booster + liquid-fuel ramjet | - | csg-cn-yj12-mda; csg-cn-yj12-wsn | C-only | |
| Carriage per aircraft | H-6K: up to 4 ASCMs (ONI 2015 for upgraded H-6); J-15: not public (1-2 plausible) | missiles | csg-cn-oni-2015 | A | engineering_estimate for J-15: ~2.5 t-class missile ⇒ 1-2 per aircraft on centreline/inner stations |

### YJ-83K / YJ-83KH (Subsonic Air-Launched ASCM; Standard PLANAF Anti-Ship Weapon)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
|---|---|---|---|---|---|
| Role | Subsonic sea-skimming ASCM, air-launched variant of YJ-83 (CSS-N-8 family) | - | csg-cn-yj83-janes | B | |
| Launch platforms | JH-7/JH-7A, H-6G, J-15 (all PLANAF, per Janes); J-16 (PLAAF, CCTV Feb 2020); J-15T shown with 4× YJ-83K (2026 PLAN image, via Military Watch) | - | csg-cn-yj83-janes; csg-cn-yj83-mwm | B / C | J-15T 4-round load reported by Military Watch (C); image attributed to PLAN — verify |
| Max range (YJ-83K) | 180 | km | csg-cn-yj83-janes | B | ONI 2015: YJ-83 family ~65-120 nm (≈120-222 km) for ship variants (A); export C-802A/AK 180 km (export) |
| Max range (YJ-83KH) | 230 | km | csg-cn-yj83-janes | B | Janes: "stated maximum range 230 km" |
| Export range C-802 / C-802A | 65 / ~97 (≈120 / 180) | nm (km) | csg-cn-oni-2015; csg-cn-yj83-wiki | A / C, export | ONI: export ranges advertised 65 nm (C-802) and 100 nm (C-802A); domestic "likely much longer" |
| Speed | Mach 0.9 | Mach | csg-cn-yj83-wiki | C-only | Consistent with turbojet subsonic class |
| Flight profile | Sea-skimming cruise and terminal | - | csg-cn-yj83-wiki | C-only | Terminal pop-up not reported |
| Guidance | INS + active radar terminal (YJ-83K); imaging IR terminal + possible datalink (YJ-83KH) | - | csg-cn-yj83-janes | B | Janes: YJ-83K "radar-guided"; KH "imaging-infrared seeker" |
| Warhead | 165 (HE semi-armour-piercing) | kg | csg-cn-yj83-wiki | C-only | CSIS C-802: 165 kg (B, export variant) |
| Length / mass | 5.3 m (Janes) / ~700-800 kg | m / kg | csg-cn-yj83-janes; csg-cn-yj83-mwm | B / C | Mass C-only |

### YJ-15 (Ramjet Anti-Ship Missile Shown On J-15/J-15T)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
|---|---|---|---|---|---|
| Public debut | 3 Sep 2025 Victory Day parade | date | csg-cn-yj20-gt-2025 | B | Official media: YJ-15/17/19/20 can be carried by "carrier-based fighter jets, surface vessels and submarines" (collective statement, not per-missile) |
| Carrier-fighter carriage | J-15/J-15T photographed with 2× YJ-15 (Feb 2026, unofficial image) | missiles/aircraft | csg-cn-yj12-usni-2026; csg-cn-yj15-scmp | B | SCMP cannot verify image authenticity |
| Range | 1,200-1,800 (Janes analysis for "new air-launched anti-ship missiles", via USNI) / ">1,000" (USNI headline) / ~500 (Military Watch) | km | csg-cn-yj12-usni-2026; csg-cn-yj83-mwm | B / C | LARGE CONFLICT. Janes wording may refer to the class, not YJ-15 specifically. Physical-size sanity (compact fighter-carried ramjet) argues for the lower end; engineering_estimate 400-800 km pending better data |
| Speed | >Mach 5 (Janes via USNI) / Mach 4-5 | Mach | csg-cn-yj12-usni-2026 | B | PRC: not public |
| Propulsion | Ramjet (air-breathing) | - | csg-cn-yj15-scmp; csg-cn-yj12-usni-2026 | B | USNI headline says "supersonic" |
| Guidance / warhead | not public | - | - | - | |

### HHQ-9 / HHQ-9B (Long-Range Area SAM; Type 052D / Type 055)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
|---|---|---|---|---|---|
| Role | Long-range area air defence for the formation; anti-aircraft, anti-ASCM, limited anti-ballistic | - | csg-cn-hhq9-xinhua-2021; csg-cn-oni-2015 | A/B | Xinhua (2021 Nanchang live-fire, via deagel reprint): "medium-range area anti-missile and air defense for surface ship formations" |
| Launch platforms | Type 052C (HHQ-9/9A, revolver-type VLS), Type 052D (64 universal cells), Type 055 (112 universal cells) | - | csg-cn-oni-2015; csg-cn-yj20-janes-2026 | A/B | Fujian itself carries NO area SAM; relies on escorts |
| Range, HHQ-9 (052C) | ~55 | nm (≈100 km) | csg-cn-oni-2015 | A | ONI 2015, text + Figure 2-3 "Naval Surface-to-Air Missile Ranges" |
| Range, extended-range HHQ-9 (052D) | "extended-range variant"; ONI chart bar reaches ~80-90 nm | nm | csg-cn-oni-2015 | A | ONI gives no number in text; chart value read from axis (10-90 nm scale) ⇒ treat ~80 nm (≈150 km) as A-derived estimate. Best US-official anchor for "HHQ-9B" |
| Range, HQ-9B (land) | >250 / 300 (162 nm) | km | csg-cn-hhq9-armytech; csg-cn-hhq9-mitchell | B / C | Land-system figures; naval HHQ-9B equivalence NOT established. Wikipedia 260 km (C) |
| Export FD-2000 / FD-2000B range | 125 / 250 | km | csg-cn-hhq9-wiki | C-only, export | Export brochure figures (CPMIEC); not PLAN |
| Max altitude | HQ-9 ~20 km (65,616 ft); HQ-9B 50 km reported | km | csg-cn-hhq9-mitchell; csg-cn-hhq9-armytech | B / C | Naval-variant ceiling not public |
| Speed | Mach 4.2 | Mach | csg-cn-hhq9-mitchell | B | Original HQ-9; 9B speed not public |
| Guidance | Inertial + command midcourse; track-via-missile / semi-active radar terminal; HQ-9B adds IR / dual-mode seeker (reported); active-radar claims also exist | - | csg-cn-hhq9-armytech; csg-cn-hhq9-wiki | C-only | Sources disagree on SARH/TVM vs active radar for HHQ-9B. On 052D/055, Type 346-series AESA provides tracking/uplink (context, not a missile spec) |
| Warhead | 180 (HE-frag, HQ-9 baseline) | kg | csg-cn-hhq9-armytech | C-only | 9B value not public |
| Missile length / mass (HQ-9) | 6.8 m / ~2,000 kg; stage diameters 700 / 560 mm | m / kg / mm | csg-cn-hhq9-armytech | C-only | Traces to a 2001 Defence International article |
| Cells per missile (HHQ-9B) | 1 per universal VLS cell, cold-launched | - | csg-cn-hhq9-xinhua-2021; csg-cn-afcea-3tier | A/B | CCTV footage (2021) shows cold launch from 055 bow VLS; AFCEA: universal VLS can cold-launch HHQ-9 and hot-launch others |
| HHQ-9C (Sep 2025 parade) | Displayed; claimed quad-pack (4 per cell) on Type 055 | per cell | csg-cn-hhq9c-x | C-only | Social-media claim; no A/B confirmation found. Do NOT model 4/cell without further evidence |
| Live-fire evidence | Nanchang: 5 SAMs fired, 5 hits (CCTV, 2021) | - | csg-cn-hhq9-xinhua-2021 | A (PRC media via reprint) | Target types/conditions not public |

### HHQ-16 / HHQ-16B/C (Medium-Range SAM; Type 054A, 054B, Also 052D/055 VLS)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
|---|---|---|---|---|---|
| Role | Medium-range local-area SAM (Shtil-1 / 9M317ME lineage, vertically launched) | - | csg-cn-oni-2015; csg-cn-afcea-3tier | A/B | AFCEA: "essentially a vertically launched version of the SA-N-7B" with ~50 km range |
| Launch platforms | Type 054A: 32-cell VLS (hot-launch, Mk41-like hatches); Type 054B (first commissioned early 2025); 052D/055 universal VLS reported for HHQ-16B/C | - | csg-cn-oni-2015; csg-cn-dod-cmpr-2025; csg-cn-hhq16-quwa | A/B | 054B SAM type/cell count not in A sources |
| Range, HHQ-16 (054A) | ~20-40 | nm (≈37-74 km) | csg-cn-oni-2015 | A | ONI's spread likely spans baseline vs improved round |
| Range, HHQ-16 baseline | 40 | km | csg-cn-hhq16-quwa | B | Matches export LY-80 / LY-80N 40 km (export) |
| Range, HQ-16B/C / HHQ-16C | ~70 / 70+ | km | csg-cn-hhq16-quwa | B | Quwa named analysis; CCTV Jun 2025: new HQ-16-derived land system intercepts "at a range of 50 km" (via Janes) |
| Export LY-80 envelope | 3.5-40 km vs fighter; 3.5-12 km vs cruise missile (300 m/s, 50 m alt); target alt 15 m-18 km; SSPk 0.85 fighter / 0.60 cruise missile | km / m / - | csg-cn-hhq16-missilery | C-only, export | Useful min-range / low-altitude anchors; export-brochure derived |
| Export HQ-16FE | 160 km, active radar seeker, 27 km altitude | km | csg-cn-hhq16-quwa | B, export | Different missile generation; not PLAN-confirmed |
| Guidance | Inertial + command update, semi-active radar terminal; 4 × Type 345 (MR-90-like) illuminators on 054A | - | csg-cn-hhq16-wsn; csg-cn-afcea-3tier | C-only / B | AFCEA confirms MR-90-copy tracking radar |
| Missile length / diameter | 5.01 m / 340 mm | m / mm | csg-cn-hhq16-missilery | C-only, export | |
| Warhead | HE-frag; mass not public (~70 kg class by 9M317 analogy) | kg | engineering_estimate | - | 9M317 warhead ~70 kg; not confirmed for HQ-16 |
| Cells per missile | 1 per 054A cell (32 per ship); quad-pack NOT reported | - | csg-cn-hhq16-quwa | B | |

### HHQ-10 (Short-Range Point-Defence Missile; FL-3000N Export)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
|---|---|---|---|---|---|
| Role | Point defence vs ASCMs and aircraft (RAM-analogue, not a rolling airframe) | - | csg-cn-afcea-3tier; csg-cn-hhq10-wsn | B | |
| Launchers | 24-cell (trial ship 892; Type 055), 18-cell (Liaoning), 8-cell (Type 056) | cells | csg-cn-afcea-3tier | B | Type 052D stern 24-cell (C) |
| Fujian fit | "multiple HHQ-10 short-range missile launchers" | - | csg-cn-fujian-usnipro-2026 | B | Number of launchers/cells not public (4 × 18-cell commonly claimed, C-only) |
| Max range | 9 (vs subsonic) / 6 (vs supersonic) | km | csg-cn-afcea-3tier; csg-cn-hhq10-wiki | B, export | AFCEA cites FL-3000N advertised statistics (Zhuhai 2008) — export-derived |
| Min range | 0.5 | km | csg-cn-hhq10-wiki | C-only | |
| Practical range vs ASCM | ~5 | km | csg-cn-hhq10-wsn | C-only | |
| Altitude envelope | 1.5 m - 6 km | m / km | csg-cn-hhq10-wiki | C-only | |
| Speed | >Mach 2 | Mach | csg-cn-hhq10-wsn | C-only | |
| Guidance | RF (passive radar) midcourse + passive IR / imaging IR terminal | - | csg-cn-afcea-3tier | B | Two RF horns in nose |
| Warhead | 3 (HE-frag, proximity fuze) | kg | csg-cn-hhq10-wsn | C-only | |
| Missile dimensions / mass | ~2.0 m × 0.12-0.127 m; ~20 kg | m / kg | csg-cn-hhq10-wiki | C-only | |
| Manoeuvre limit | up to 20 | g | csg-cn-hhq10-wsn | C-only | |
| HQ-10A | Naval point-defence missile revealed Sep 2025 | - | csg-cn-hhq10-wiki | C-only | Performance not public |

### Type 1130 (H/PJ-11) CIWS And Type 730 (H/PJ-12) CIWS

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
|---|---|---|---|---|---|
| Type 1130 configuration | 11 barrels, 30 mm Gatling | - | csg-cn-1130-mnd-2026 | A | PRC MND / China Military Online, 22 Feb 2026 |
| Type 1130 rate of fire | >10,000 | rds/min | csg-cn-1130-mnd-2026 | A | Official "exceeding 10,000 rounds per minute"; 11,000 rpm widely quoted (C) |
| Type 1130 role / ammo | Terminal-phase anti-ship-missile interception; "multiple types of ammunition"; barrage or direct hit; multi-target sequencing | - | csg-cn-1130-mnd-2026 | A | Ammunition types not named |
| Type 1130 effective range | 1-1.5 km practical vs missiles; ~3 km vs surface; 5 km max | km | csg-cn-1130-wsn | C-only | TWZ: "similar engagement range" to Type 730 (B, qualitative only) |
| Type 1130 muzzle velocity | 1,000-1,150 | m/s | csg-cn-1130-wsn | C-only | Ammunition-dependent |
| Type 1130 ready rounds | ~1,280 | rounds | csg-cn-1130-wsn | C-only | At 10,000 rpm ≈ 7.7 s continuous fire; magazine depth is a sim-critical residual |
| Type 1130 elevation | -25° to +85° | deg | csg-cn-1130-wsn | C-only | |
| Type 1130 platforms | First seen on Liaoning; 052D, 055, later 054A, 054B; Fujian "11-barrel 30-mm CIWS gatling guns" (multiple) | - | csg-cn-1130-twz; csg-cn-fujian-usnipro-2026 | B | Fujian mount count not public (3 commonly claimed, C-only) |
| Type 730 configuration | 7 barrels, 30 mm Gatling | - | csg-cn-1130-twz | B | |
| Type 730 rate of fire | 5,800 | rds/min | csg-cn-730-wiki | C-only | Not traced to an A source |
| Type 730 effective range | up to 3 | km | csg-cn-730-wiki | C-only | |
| Type 730 ammunition | 640 or 2 × 500 rounds | rounds | csg-cn-ciws-wiki | C-only | |
| Type 730 CSG relevance | Earlier 054A hulls, 052C | - | csg-cn-730-wiki | C-only | Being superseded by Type 1130 on new builds |

### 130 mm Main Gun (H/PJ-38, Also Reported As H/PJ-45)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
|---|---|---|---|---|---|
| Designation | H/PJ-38 (common) vs H/PJ-45 (Naval News 2026: "H/PJ-45 130 mm naval gun … in service onboard 052D and 055") | - | csg-cn-130-navalnews-2026; csg-cn-130-gs | B / C | DESIGNATION CONFLICT; both refer to the single-barrel 130 mm/70 on 052D/055. Use "130 mm/70" as canonical key |
| Calibre / barrel | 130 mm / 70 cal, single barrel, AK-130 derived (Zhengzhou 713 Institute) | - | csg-cn-130-navweaps; csg-cn-130-gs | C-only | |
| Rate of fire | 40 | rds/min | csg-cn-130-gs; csg-cn-130-sinodef | C-only | |
| Max range (unguided) | ~30 | km | csg-cn-130-gs; csg-cn-130-sinodef | C-only | Guided/ER shell: not public |
| Round mass | 86.2 | kg | csg-cn-130-sinodef | C-only | Likely complete round, not projectile |
| Mount mass | >50 (incl. stealth housing) | t | csg-cn-130-gs | C-only | |
| Successor | New large-calibre PLAN gun turret observed 2025-2026 | - | csg-cn-130-navalnews-2026 | B | Performance not public |

### Yu-6 (533 mm Heavyweight Torpedo; Submarine-Launched)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
|---|---|---|---|---|---|
| Role | Dual-purpose heavyweight torpedo (ASW + ASuW); Mk 48-class counterpart | - | csg-cn-yu6-gs; csg-cn-yu6-ni | C-only | No A/B source found giving Yu-6 numbers; ONI 2015 does not list PLAN torpedo performance |
| Launch platforms | Type 039 Song, 039A/B Yuan, Type 093/093A/093B Shang SSN (533 mm tubes); possibly 095 in future | - | csg-cn-yu6-gs | C-only | Carrier-group escort SSN (093B) torpedo loadout not public |
| Diameter | 533 | mm | csg-cn-yu6-gs; csg-cn-yu6-wiki | C-only | |
| Max speed (attack) | >65 | kt | csg-cn-yu6-gs; csg-cn-yu6-wiki | C-only | Single-source lineage (Chinese-language material via GlobalSecurity) |
| Max range | >45 (at cruise speed, not at 65 kt) | km | csg-cn-yu6-wiki | C-only | Speed/range pairing unknown; engineering_estimate: Otto-II Mk48-class ≈ 38 km @ 55 kt / 50 km @ 40 kt — model two-speed |
| Max depth | not public | m | - | - | engineering_estimate: Mk48 Mod 4-class ~800 m; do not assert |
| Guidance | Wire guidance + active/passive acoustic homing + wake homing | - | csg-cn-yu6-gs | C-only | Wake homing stated in PRC-origin descriptions; wire length not public |
| Propulsion | Otto Fuel II (monopropellant thermal) | - | csg-cn-yu6-gs; csg-cn-yu6-ni | C-only | |
| Warhead / fuze | HE, mass not public; proximity + contact fuze | kg | csg-cn-yu6-wiki | C-only | engineering_estimate ~250-300 kg (Mk48-class 267-295 kg) |
| IOC | 2005 | year | csg-cn-yu6-gs | C-only | |
| Successors | Yu-9 (electric counterpart); Yu-10 (electric heavyweight, reported) | - | csg-cn-yu6-wiki | C-only | Performance not public |

### Yu-7 (324 mm Lightweight Torpedo; Ships And Helicopters) And Yu-11 Successor

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
|---|---|---|---|---|---|
| Role | Lightweight ASW torpedo | - | csg-cn-afcea-052d | B | |
| Launch platforms | 2 × triple 324 mm tubes on 052D, 055, 054A (Type 7424B); Z-9C/Z-18F/Z-20F helicopters; also payload of VLS ASW rocket | - | csg-cn-afcea-052d; csg-cn-oni-2015 | B / A | ONI 2015: Z-9C "usually observed with a single, lightweight torpedo" |
| Lineage | Mk 46 Mod 1/2 + Italian A244/S features | - | csg-cn-yu7-wsn; csg-cn-yu6-ni | C-only | |
| Diameter / length / mass | 324 mm / 2.6-2.7 m / 235 kg | mm / m / kg | csg-cn-yu7-gs; csg-cn-yu7-wsn | C-only | Military Periscope (paywalled summary) matches 235 kg |
| Speed | 42-43 | kt | csg-cn-yu7-gs; csg-cn-yu7-wsn | C-only | |
| Range | 10-14 | km | csg-cn-yu7-wsn (10 km); csg-cn-yu7-gs (14 km) | C-only | CONFLICT 10 vs 14 km; likely speed-dependent |
| Depth band | 6-400 | m | csg-cn-yu7-gs; csg-cn-yu7-wsn | C-only | |
| Guidance | Active/passive acoustic homing; no wire | - | csg-cn-yu7-wsn | C-only | GS claims 90% acquisition probability (C-only, unverified) |
| Warhead | 45 (shaped charge) | kg | csg-cn-yu7-gs; csg-cn-yu7-wsn | C-only | |
| Propulsion | Otto-fuel II thermal, twin contra-props | - | csg-cn-yu7-wsn | C-only | |
| Yu-11 successor | Publicly unveiled 2016; replacing Yu-7 (Military Periscope); ~50 kt / >20 km speculative | kt / km | csg-cn-yu7-mp; csg-cn-yu11-gs | C-only | GS figures are explicitly speculative ("may") — do not use as fact |

### CY-5 / Yu-8 (VLS-Launched Rocket-Assisted ASW Torpedo, "ASROC-Type")

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
|---|---|---|---|---|---|
| Designation | DESIGNATION CONFLICT: "CY-5" (export CY-series lineage, Wikipedia/GlobalMilitary) vs "Yu-8" (PRC-media designation for the 054A VLS rocket-assisted torpedo, per GlobalSecurity translation); AFCEA mentions "Changying-5" | - | csg-cn-cy5-wiki; csg-cn-yu8-gs; csg-cn-afcea-052d | C / B | Probably the same functional weapon; treat "CY-5/Yu-8" as one sim entity until resolved |
| Role | Stand-off ASW: rocket-boosted flight, releases lightweight torpedo (Yu-7 class) near datum | - | csg-cn-yu8-gs | C-only | Also "certain anti-ship capability" claimed (C) |
| Launch platforms | Type 054A 32-cell VLS (shared with HHQ-16, compatible launch control); Type 052D / 055 universal VLS reported; 056A via YJ-83 boxes | - | csg-cn-yu8-gs; csg-cn-afcea-052d | C-only / B | AFCEA (B): 054A VLS "possibly" ASW; 052D universal VLS "reportedly has a new rocket-propelled torpedo" |
| Max range | ~30 (CY-5, C); "about 50 km" design goal for Changying-2 → Yu-8 (C); AFCEA "5-8 km" (B) | km | csg-cn-cy5-wiki; csg-cn-yu8-gs; csg-cn-afcea-052d | B / C | LARGE CONFLICT. AFCEA's 5-8 km (2014-era) likely a pre-service estimate; PRC-media "tens of km". Scenario band 20-50 km |
| Flight speed | >Mach 1.5 max, Mach 0.7 terminal cruise; glide trajectory rather than purely ballistic | Mach | csg-cn-yu8-gs | C-only | Translation of Chinese-language material |
| Payload | Yu-7 lightweight torpedo (45 kg warhead) | - | csg-cn-yu8-gs; csg-cn-cy5-wiki | C-only | Yu-11 payload for newer rounds: not public |
| Cells per missile | 1 per VLS cell | - | engineering_estimate | - | Rocket-booster + 324 mm torpedo fits 054A strike-length cell; no multi-packing reported |
| First live fire | July 2015 South China Sea exercise (054A) | date | csg-cn-yu8-gs | C-only | |
| IOC | 2006 (with 054A) | year | csg-cn-yu8-gs | C-only | |
| 054B long-range ASW missile | "Yu-8 … maximum range 100 km" for 054B (GlobalSecurity translation) | km | csg-cn-yu8-054b-gs | C-only | Implausible for a Yu-8-class round; likely a different/new weapon or error. Flag, do not use |

### PL-15 (Long-Range Active-Radar AAM; J-35, J-15T, J-15 Air Wing) With PL-15E Export Figures

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
|---|---|---|---|---|---|
| Role | Primary BVR air-to-air missile of PLA/PLANAF fighters | - | csg-cn-dod-cmpr-2025 | A | DoD 2025 notes export versions of PL-12A/PL-15/PL-11 revealed Nov 2024 "improved for performance or completely redesigned" |
| Carrier-aircraft platforms | J-35 (internal bay; CCTV: up to 6 AAMs internal), J-15T, J-15 | - | csg-cn-j35-scmp-cctv; csg-cn-pl15-cma-blog | B / C | CCTV designer programme (via SCMP, Sep 2025) shows 6 AAMs in J-35 bay — mix (PL-15 vs PL-10 vs folded-fin PL-15/"PL-16") not stated |
| Max range, PLA service PL-15 | "over 200" / 200-300 / 150-200 | km | csg-cn-pl15-armyrec; csg-cn-pl15-wiki | C-only | No A/B service-variant range found. TWZ (B) "reported maximum range around 124 miles (≈200 km)" — secondary |
| Max range, PL-15E | >145 | km | csg-cn-pl15e-scmp-avic | B, export | AVIC official Weibo (Zhuhai 2021) via SCMP — manufacturer export claim. NOT a PLAN figure |
| Speed | Mach 4 (military source, PL-15E) / Mach 5+ (C) | Mach | csg-cn-pl15e-scmp-avic; csg-cn-pl15-wiki | B, export / C | SCMP cites an unnamed military source for "four times the speed of sound" |
| Propulsion | Dual-pulse solid rocket motor | - | csg-cn-pl15-twz; csg-cn-pl15-armyrec | B / C | |
| Guidance | INS (+BeiDou) midcourse, two-way datalink, terminal active AESA radar seeker (active + passive modes) | - | csg-cn-pl15-twz | B | Ku-band claim (C-only, blog) |
| Dimensions / mass (PL-15E) | 3,996 mm length, 203 mm diameter, ≤210 kg | mm / kg | csg-cn-pl15-gs (Zhuhai display board) | C-only, export | Display-board figures relayed by GlobalSecurity translation |
| Warhead | not public | kg | - | - | |
| Internal-carriage variant | Folded-fin PL-15 variant (2024 Zhuhai) enabling up to 6 in J-20/J-35 bays | missiles | csg-cn-pl15-cma-blog; csg-cn-pl15-wiki | C-only | Some sources call it "PL-16" (C) — designation unresolved |
| Combat use | PL-15E used by Pakistan AF in May 2025 India-Pakistan air battle; debris recovered in India | - | csg-cn-pl15-twz | B | Export variant; performance in that engagement not publicly quantified |

### PL-10 (Short-Range IIR Dogfight AAM)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
|---|---|---|---|---|---|
| Role | Short-range, high-off-boresight IR AAM | - | csg-cn-pl10-armyrec | B | |
| Carrier-aircraft platforms | J-35 (internal; per CCTV-model reporting), J-15T/J-15 | - | csg-cn-j35-19fortyfive; csg-cn-j35-scmp-cctv | C / B | Exact carrier loadouts not public |
| Max range, PL-10E | 20 (up to ~30 under favourable launch conditions) | km | csg-cn-pl10-armyrec | B, export | Zhuhai 2016/2018 PL-10E figures (export) |
| Seeker / off-boresight | Multi-element imaging IR; ±90° off-boresight, helmet-cued | deg | csg-cn-pl10-armyrec | B, export | |
| Airframe control | Thrust-vector control | - | csg-cn-pl10-armyrec; csg-cn-pl10-gs | B | |
| Speed | ~Mach 4 | Mach | csg-cn-pl10-gmn | C-only | |
| Dimensions / mass | 3.0 m × 160 mm; ~105 kg | m / mm / kg | csg-cn-pl10-wiki; csg-cn-pl10-armyrec | C / B, export | Alternative listings 110 kg |
| Warhead | ~33 | kg | csg-cn-pl10-gmn | C-only | |
| IOC | ~2015 | year | csg-cn-pl10-wiki | C-only | |

### PL-17 (Very-Long-Range AAM; Relevance To Carrier Aircraft)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
|---|---|---|---|---|---|
| Role | Very-long-range AAM against high-value airborne assets (AEW&C, tankers) | - | csg-cn-dod-cmpr-2025 | A | DoD 2025 table: "J-16 with PL-17 — AAM — 1400 km — Anti-air, HVAA" |
| DoD system reach (J-16 + PL-17) | 1,400 | km | csg-cn-dod-cmpr-2025 | A | Total reach = missile + J-16 combat radius (~1,000 km per DoD footnote) ⇒ implied missile-only ≈ 400 km (engineering_estimate by subtraction) |
| Missile range | ~400 (estimates 300-500) | km | csg-cn-pl17-gpm; csg-cn-pl17-mwm | B / C | Named-analysis estimate; no PRC disclosure |
| Speed | ≥Mach 4 (assessed) | Mach | csg-cn-pl17-gpm | B | Mach 6 claims are C-only |
| Propulsion | Dual-pulse solid rocket motor | - | csg-cn-pl17-gpm | B | |
| Dimensions | ~5.8-6.0 m length, ~305 mm diameter | m / mm | csg-cn-pl17-mwm | C-only | From first close-up photo |
| Carriage | J-16 external heavy pylon (2 per aircraft reported) | - | csg-cn-pl17-gpm | B | |
| Carrier-aircraft relevance | No public evidence of PL-17 on J-15/J-15T/J-35 or Fujian air wing | - | - | not public | engineering_estimate: J-15T (Flanker-derived, J-16 sibling) is the only plausible Fujian carrier; J-35 bay too short for ~6 m round. Model as J-15T external option only if scenario requires, flagged as speculative |
| IOC | Chinese state media indicated service 2022; not independently confirmed | year | csg-cn-pl17-gpm | B | Not shown at Sep 2025 parade |

## Arbitrated Corrections

- Tongliao (554) is a **Type 054A**, not a Type 054B. The PRC MND 2025-11-18 release names Fujian's escorts as Yan'an (106), Tongliao (554) (`csg-cn-fujian-mnd-20251118`, A) but does not state Tongliao's class; public evidence (Huangpu-built, commissioned about Nov 2023, identified as 054A by MP-IDSA, Seaforces and Wikipedia) confirms 054A. The only publicly confirmed Type 054B hulls are Luohe (545, Northern Theater) and Qinzhou (555, Southern Theater); a third hull was reported under construction in Jan 2026.
- The 2025-26 Type 055 (and, from Jul 2026, Type 052D) ship-launched hypersonic anti-ship round is modelled as **YJ-20**, not YJ-21. The April 2022 Type 055 test was called "possibly designated the YJ-21" by DoD (via CRS); after the Sept 2025 Victory Day parade unveiled YJ-15/17/19/20, PLA footage (Dec 2025 on Wuxi, Jul 2026 on a Type 052D) re-attributed the ship-launched round to YJ-20. YJ-21 is modelled as the 2022 assessment and as the air-launched (H-6K/N; export YJ-21E) weapon.
- The SSN in the group (1 x Type 093B baseline) is an **analyst assumption, not an observed fact**. PRC state media never reports SSN escort of a carrier group; the only indirect evidence is a 2022 CCTV Liaoning anniversary clip and 2021 reports of a Type 093 shadowing a UK CSG, both C-tier relays.
- Air-wing counts are **estimates**; no official count exists. Official sources (MND, PLAN spokesperson, DoD CMPR 2025) confirm only the aircraft types (J-35, J-15T, J-15D, KJ-600, Z-20 series, plus unnamed UAVs). Every per-type count in the Order Of Battle is an engineering_estimate built from Tier B totals (CSIS 50-60 fixed-wing, INDSR ~60 total) and Tier C breakdowns.
- The **Type 346B radar attribution on Fujian is Tier C only**. No A/B source names the radar; CSIS lists it as "TBD". The 500-600 km detection figure quoted for it is a Type 055 figure (Deagel), not a confirmed Fujian fit.
- **Type 052D values conflict with the existing repo catalog**: Naval News (B) gives beam 17.2 m, draft 6.2 m and gun designation H/PJ-45A, while the existing catalog (C, `p5-cn-naval-type052d-*`) gives 18 m, 6.5 m and H/PJ-38. The Platform Parameters section above prefers the Naval News (B) values and flags the conflict inline.
- The **Type 093B VLS cell count conflicts** across sources: ONI testimony says 24 cells (A via B), a Feb 2025 satellite image showed 12 open hatches (C-relay of a named analyst), and a CSSC model shows 18. The baseline uses 24 (ONI) with a sensitivity case at 12.
- The **YJ-18 range figure conflicts by a factor of about 2.4**: DoD gives 290 nm (~537 km) for the submarine-launched round, while ONI, Carlson and Janes give about 120 nm. Both threat rings should be modelled.

## Residuals

- **Air-wing counts are not public.** Official sources (MND, PLAN spokesperson, DoD CMPR 2025) confirm only the aircraft types. Every per-type count in the OOB is an engineering_estimate built from B totals (CSIS 50-60 fixed-wing, INDSR ~60 total) and C breakdowns. The J-35 share is the largest unknown, and the right 2026 value may be well below 12.
- **Hangar dimensions and capacity are not public.** The only figure (>24 fighters) is PRC commentary from 2022.
- **Installed power, endurance and sortie rate** have no A/B values beyond Reuters' "some analysts ~10,000 nmi". The CNN estimate of 60% of Nimitz air-ops rate is opinion.
- **HHQ-10 cells per launcher** conflict (18 vs 24). The ASW rocket and anti-torpedo list traces to Chinese forum material.
- **J-35 performance is entirely Tier C.** Engine fit (WS-21 vs WS-19), radar type, internal fuel and naval MTOW are unconfirmed. The MTOW conflict (28 t vs 30 t) is recorded, not resolved.
- **KJ-600 radar architecture** (rotating two-face vs fixed three-face) and detection range are not public. The 15,000 m ceiling and the empty-weight figure published by Deagel and Wikipedia are implausible. Endurance of ~5 h is C-only.
- **CATOBAR combat radius of J-15T** is not public. The ~1,270 km baseline and the 1,000-1,300 km engineering estimate are not measured. Buddy-tanker assignment aboard Fujian is not public.
- **Z-20F / Z-20J / Z-20S naval deltas** (MTOW, endurance, sonar model) are not public; base-airframe C values are reused.
- **GJ-21** has not been confirmed operating at sea from Fujian. It is kept at 0 in the default OOB.
- **Readiness timeline:** Fujian had not reached FOC as of the latest sources (Apr 2026). An Aug 2026 USNI report of Fujian heading into the SCS was seen only through a secondary relay (Migflug) and was not independently read.
- **Paywalled sources not read:** Janes, FlightGlobal (Apr 2026 KJ-600 fleet), IISS Military Balance 2026. An IISS air-wing count remains a gap.
- **SSN presence is inferential**: no A/B source confirms an SSN sailing with any PLAN CSG. The 2022 CCTV Liaoning clip and the 2021 UK-CSG shadowing reports are only C-tier relays. The 1 x 093B baseline is therefore an assumption, and a 0-SSN branch should be kept.
- **Type 093B VLS count and weapons**: cell count sources disagree (24 ONI vs 12-hatch imagery vs 18-cell CSSC model); ONI does not say what missiles the cells carry; YJ-18 range conflicts by a factor of about 2.4 (run both threat rings).
- **SSN performance is almost all C-only**: displacement, speed, test depth, crew and tube count all rest on C sources. The about 400 m test depth comes from a PLAN Navy Day poster relayed by Army Recognition. The poster dimensions (120 x 13 m, 8,000 t submerged) conflict with Western estimates (about 110 x 11 m, about 7,000 t). CMSI China Maritime Report 30 (Carlson & Wang, the key B source) was Cloudflare-blocked; fetch it manually to upgrade these rows.
- **Acoustic signatures**: only relative classes are public (Victor II/III-class for 093A, possibly Sierra-class for 093B, via Wikipedia citing CMR-30). There are no dB source levels, so use relative noise classes with a sensitivity sweep.
- **Radar ranges**: no A/B range exists for the Type 346A/346B or the 054B AESA. The 346B figure of 400-600 km is forum-grade plus an aperture-scaling argument, so treat it as a parameter sweep.
- **Type 054B speed, range and propulsion are unresolved**: USNI (2025) says "reliable details have yet to surface". The 28 kt figure is C-only. For FEP vs CODAD, CODAD is preferred per USNI and TWZ.
- **Type 052D conflicts with the existing catalog**: Naval News (B) gives beam 17.2 m, draft 6.2 m and gun H/PJ-45A; the catalog (C) gives 18 m, 6.5 m and H/PJ-38. Sources disagree on which CIWS model came first by batch. The new **Type 052DM** subvariant (Proceedings 2026, eight commissioned in 2025) has no public characterisation.
- **Type 055 hulls 109/110**: their official debut was 2026-03-08 (CCTV, Eastern Theater); Proceedings says commissioned May 2025 and Wikipedia says March 2026. This matters for availability. Neither hull is Southern Theater, so Fujian's 055 pool is 105-108.
- **Type 901 availability and capacity**: only 2 hulls exist for 3 carriers. Fuel 20,000 t, cargo 25,000 t and the 48,000 t displacement come from USCC 2020 relaying Jane's. The widely cited 45,000 t figure is a media value. The transfer rate is not public (engineering_estimate only), and at-sea VLS reload is not demonstrated.
- **New large AOE (271 x 37 m)**: launched July 2026 with no official designation. The 60-65 kt displacement is C-only / engineering_estimate. It is excluded from the 2025-2026 OOB.
- **No manoeuvring data** (tactical diameter, acceleration) exists for any PLAN escort. Only the 052D engineering estimate is given.
- **Sources checked but not fully usable**: DoD CMPR 2025 was read. It confirms the 054B/Z-20 fit and the STC flotilla structure but gives **no CSG composition and no SSN-escort statement**. IISS "Boomtime at Bohai" (Feb 2026) returned HTTP 403 and was used only through secondary reporting.
- **YJ-21 vs YJ-20 attribution** for the ship-launched hypersonic ASBM is unresolved beyond the arbitration above. The YJ-20 range spread is wide and all of it traces to Janes: ~965-1,450 km (USNI Jul 2026) vs 1,500-2,000 km (USNI Mar 2026). No US-government YJ-20 number was found. Seeker type, warhead and the terminal-manoeuvre profile are not public.
- **YJ-15 range** runs from 500 to 1,800 km across sources, and the Janes 1,200-1,800 km figure may describe a class of new missiles rather than YJ-15 specifically. No PRC data exists. This is the largest open question for the Fujian air wing's anti-ship reach, together with whether J-35 or J-15T carry YJ-12 or YJ-15 operationally.
- **HHQ-9B naval range**: the only A-tier anchor is ONI 2015 (HHQ-9 about 55 nm; the extended-range 052D variant charted at about 80-90 nm). The 250-300 km land-based HQ-9B figures should not be carried over to the naval round without evidence. HHQ-9B seeker type (SARH/TVM vs active) is unresolved. HHQ-9C quad-packing is supported only by social media.
- **The actual VLS magazine loadout** of the Fujian escorts (055/052D/054A/054B) is not public: the HHQ-9B/HHQ-16/YJ-18/YJ-20/CY-5 mix and whether anything is multi-packed. It needs to be a scenario parameter, not a sourced value.
- **Type 1130 figure** is A-tier only for barrel count and rate of fire (>10,000 rpm, PRC MND 2026). Effective range, magazine depth (~1,280 rounds, roughly 7.7 s of fire) and Pk vs supersonic or hypersonic targets are C-only or not public. The same applies to the Type 730 numbers (5,800 rpm, 3 km).
- **Torpedoes**: every Yu-6, Yu-7 and Yu-11 number is C-only, and most trace to GlobalSecurity translations of PRC-language material. Yu-6 depth, wire length, warhead mass and the speed/range pairs are not public. The US-official ONI 2015 report gives no torpedo performance.
- **CY-5 vs Yu-8 designation** is unresolved, and range estimates run from 5-8 km (AFCEA 2014) to about 50 km (PRC-media design goal). The "100 km" figure for 054B is implausible and is flagged.
- **The PL-15 service-variant range** has no A/B figure. The only manufacturer number is export PL-15E >145 km (AVIC). PL-17 on carrier aircraft has no public evidence. The DoD "1,400 km" figure is J-16 radius plus missile, not missile range.
- **HHQ-10 and HHQ-16 envelope figures** (9/6 km; 40 km, 15 m-18 km) are export-brochure derived (FL-3000N, LY-80). Fujian's HHQ-10 and Type 1130 mount counts are not public; only "multiple" is stated (USNI Proceedings).
- **The 130 mm gun designation** conflicts (H/PJ-38 vs H/PJ-45), and all of its performance data (40 rpm, ~30 km) is C-only.
- **Access gaps**: USNI News 2025-12-29 (YJ-20 test) and 2026-03-11 pages returned HTTP 403, so only search snippets were used. The DoD CMPR 2025 PDF was read via extraction and keyword-searched, not read in full. The Janes articles are paywalled and were read only as summaries.

## Evidence Boundary

- This document is research-grade, not runtime authority: every value is a public-source candidate pending calibration, not a simulation-ready parameter.
- Nothing here predicts real-world operational behaviour; it does not forecast PLAN readiness, deployment timing, or combat outcomes.
- Counts and figures marked as estimates (`engineering_estimate`, ranges, "C-only") are estimates, not observed facts, and should be treated as scenario parameters rather than ground truth.
- A Tier A or Tier B source supersedes a `C-only` or estimate row wherever one becomes available; this page should be revised, not overridden silently, when that happens.
