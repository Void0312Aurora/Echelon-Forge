# Ford-Class Carrier Strike Group Order Of Battle

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/reviews/csg_order_of_battle_20260928/csg_order_of_battle_ford_20260928.md`
Owner: `domains/naval`
Last verified: `2026-09-28`

Language: English canonical only; no Chinese companion (dated research evidence).

Status: `2026-09-28` research-grade, non-authoritative order of battle for [Carrier Strike Group Engagement](../../work/active/carrier_strike_group_engagement/README.md) cluster `S0-A`. Values are public-source candidates; none is calibrated runtime authority. Sources are listed in the [CSG source ledger](csg_source_ledger_20260928.md).

## Scope And Conventions

- Group: Gerald R. Ford Carrier Strike Group (CSG-12 / CVW-8 / DESRON 2), 2025-2026 deployment baseline with doctrinal fills. Side: blue.
- No value here is calibrated or official beyond what its cited source is. Classified or non-public data is out of scope.
- Tier tokens: `A` official-standard source (navy.mil, NAVAIR, NAVSEA, DOT&E, CRS, GAO, DoD budget books, allied government); `B` public-engineering source (manufacturer/shipbuilder material, DoD academic press); `C` sanity-check source (trade press, Wikipedia, GlobalSecurity, seaforces, naval-technology, museums); combined tiers (`A+B`, `A+C`, `B+C`, `A+B+C`) mean the value is carried by the higher tier and cross-checked by the lower.
- `C-est`: only Tier C sources found in this pass, so the value is treated as an estimate (Tier C cannot stand alone). `est`: engineering_estimate derived here, with reasoning in the uncertainty column. `n/p`: not public; no value asserted unless an `est` bound is given alongside.
- Repo draft catalog source IDs (`p5-...`) are reused where they apply. New IDs follow `csg-us-<platform>-<publisher>`. Units: nmi = nautical miles; LT = long tons; t = metric tonnes.

## Order Of Battle

### Ships

| Group element | Class | Platform ID | Hull numbers / units | Count | Role | Justification | Source ID |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Carrier | Gerald R. Ford (CVN-78) | `cvn78_ford` | CVN-78 Gerald R. Ford | 1 | Flagship; air wing host; group AAW self-defense | CSG-12 flagship, deployed 24 Jun 2025 to May 2026 (326 days) | csg-us-usff-2026 |
| Escort (DESRON 2 + attached) | Arleigh Burke DDG-51 Flight IIA | `ddg51_flt2a` | DDG-96 Bainbridge, DDG-81 Winston S. Churchill | 2 | Area AAW, ASW, strike, anti-surface | Deployed with CSG-12. The Navy fact file defines Flight IIA as DDG-79 through DDG-124 plus DDG-127 | csg-us-usff-2026; csg-us-ddg51-navy-factfile |
| Escort (DESRON 2) | Arleigh Burke DDG-51 Flight II | `ddg51_flt2` | DDG-72 Mahan | 1 | AAW, ASW, strike; no helicopter hangar | Deployed with CSG-12. Fact file defines Flight II as DDG-72 through DDG-78. Mahan is neither Flight I (the repo record) nor Flight IIA | csg-us-usff-2026; csg-us-ddg51-navy-factfile |
| Doctrinal 4th large surface combatant (fill) | Arleigh Burke DDG-51 Flight IIA (generic) | `ddg51_flt2a` | generic (any of DDG-79..124) | 1 | Air-defense-commander ship in the slot historically held by a CG-47 | CSG-12 deployed without a cruiser. The CG-47 class is retiring (5 or fewer left after FY2026, and Tier C sources disagree on the count). A 4th DDG is the realistic fill. Set count to 0 for the as-deployed variant | csg-us-usff-2026; csg-us-cg-seapower-2026; csg-us-cg-metadefense |
| Optional cruiser branch | Ticonderoga CG-47 | repo `eq-us-naval-ticonderoga` | CG-52..73 (remaining hulls) | 0 | Alternative to the doctrinal DDG fill | Kept at 0 nominal because of retirements. If used, reuse the repo Ticonderoga record (122 Mk 41 cells) | p5-us-naval-ticonderoga-factfile; csg-us-cg-seapower-2026 |
| Attack submarine (doctrinal) | Virginia SSN-774 Block III/IV | `ssn_virginia_blk3_4` | generic (SSN-784..801) | 1 | Undersea screen, ASW, ASuW, strike | The Navy does not publicly name the SSN attached to a CSG. Block III/IV is the newest commissioned configuration: Block V/VPM boats (SSN-802+) were not commissioned as of the Nov 2025 fact file. Block III/IV share one payload set (4 torpedo tubes, 2 VPTs, LAB sonar); Block IV differs mainly in maintenance periodicity | csg-us-ssn-navy-factfile; csg-us-ssn-crs |
| Combat logistics (doctrinal) | John Lewis T-AO-205 fleet oiler | `tao205_john_lewis` | generic (Atlantic-based T-AO-206 Oscar V. Peterson or T-AO-208 Robert F. Kennedy) | 1 | Underway fuel and limited stores replenishment | T-AO-205 is replacing the 15-ship Kaiser class. Only 2 T-AOE Supply-class remain (Supply, Arctic). CLF ships are shared shuttles, not permanently assigned. CSG-12 made 23 replenishments at sea in 326 days | csg-us-tao-navy-factfile; csg-us-taoe-navy; csg-us-usff-2026 |
| Combat logistics (alternative) | Supply T-AOE-6 fast combat support ship | `taoe6_supply` | T-AOE-6 Supply, T-AOE-8 Arctic | 0 | Fuel + ammunition + stores; 25 kt, able to keep pace | Kept as an alternative branch: it is the only CLF type carrying ammunition at CSG speed, but just 2 hulls remain | csg-us-taoe-navy |

### Carrier Air Wing 8 (embarked, 2025-26 deployment)

| Group element | Class | Platform ID | Hull numbers / units | Count | Role | Justification | Source ID |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Strike fighter | F/A-18E Super Hornet | `ac_fa18e` | VFA-31, VFA-37, VFA-87 | 33 | Strike, CAP, SEAD escort, recovery tanking | 3 squadrons (A). Per-squadron strength is not published; 11 per squadron is an estimate so that the 4 VFA squadrons total the typical 44 strike fighters (NDU B; Seapower C). Plausible range 10–12 per squadron | csg-us-usff-2026; csg-us-cvw8-dvids-2026; csg-us-cvw-ndu; csg-us-cvw-seapower-2020 |
| Strike fighter | F/A-18F Super Hornet | `ac_fa18f` | VFA-213 | 11 | Strike, FAC(A), CAP, tanking | 1 squadron (A). Count is an estimate (plausible range 10–14) | csg-us-usff-2026; csg-us-cvw-ndu; csg-us-cvw-seapower-2020 |
| Electronic attack | EA-18G Growler | `ac_ea18g` | VAQ-142 | 5 | AEA, SEAD | Typical carrier VAQ squadron is 5 (NDU B; TWZ C); planning range 5–7 (Seapower C) | csg-us-usff-2026; csg-us-cvw-ndu; csg-us-cvw-twz; csg-us-cvw-seapower-2020 |
| AEW&C | E-2D Advanced Hawkeye | `ac_e2d` | VAW-124 | 4 | AEW, C2, NIFC-CA node | Typical 4 (NDU B; TWZ C); planned growth to 5 (Seapower C) | csg-us-usff-2026; csg-us-cvw-ndu; csg-us-cvw-twz |
| Helicopter (sea combat) | MH-60S Seahawk | `ac_mh60s` | HSC-9 | 8 | CSAR, plane guard, VERTREP, ASuW | Count is an estimate (range 6–8). NDU (B) gives 8–11 helicopters for the whole wing | csg-us-usff-2026; csg-us-cvw-ndu |
| Helicopter (maritime strike) | MH-60R Seahawk | `ac_mh60r` | HSM-70 (carrier element + DDG detachments) | 11 | ASW, ASuW, EW | Carrier-wing HSM squadrons are about 11 aircraft including detachments (Tier C). Estimated split: about 7 aboard CVN-78 and 2 each aboard DDG-81 and DDG-96. Mahan (Flight II) has no hangar | csg-us-usff-2026; csg-us-hsm-wiki |
| COD | C-2A Greyhound | `ac_c2a` | VRC-40 detachment | 2 | Carrier onboard delivery | A two-aircraft COD detachment is typical (B). CVW-8 flew C-2A, not CMV-22B, on this deployment (A) | csg-us-cvw8-dvids-2026; csg-us-c2a-northrop |
| Strike fighter (optional branch) | F-35C Lightning II | `ac_f35c` | none in CVW-8 2025–26 | 0 | Stealth strike and ISR | Not embarked: CVW-8 listed only Super Hornet VFA squadrons, and Ford's F-35C modifications were pending. Optional future variant: one 10–14 aircraft squadron replacing one VFA | csg-us-usff-2026; csg-us-f35c-seapower-2022; csg-us-cvn78-1945-f35c; csg-us-cvw-seapower-2020 |
| Unmanned tanker (not fielded) | MQ-25A Stingray | `ac_mq25a` | none | 0 | Organic tanking, secondary ISR | First production-representative MQ-25A flight was 25 Apr 2026, so it was not deployable in 2025–26. Future wing 5–9 (Seapower C) | csg-us-mq25-navy; csg-us-cvn78-dote-fy25; csg-us-cvw-seapower-2020 |
| COD (optional branch) | CMV-22B Osprey | `ac_cmv22b` | none in CVW-8 2025–26 | 0 | COD replacement for C-2A | Optional future variant: 3 aircraft (Seapower C) | csg-us-cmv22-navair; csg-us-cvw-seapower-2020 |

Nominal embarked totals: 44 strike fighters, 5 EA-18G, 4 E-2D, 8 MH-60S, about 7 MH-60R aboard (11 in the squadron), and 2 C-2A. That is about 70 aircraft aboard CVN-78, or 74 including the DDG detachments, against a stated capacity of 75+ (A). A Tier C report puts CVW-8 at "roughly 70 aircraft".

## Platform Parameters

### `cvn78_ford` — USS Gerald R. Ford (CVN-78)

Class-lineage cross-check: repo `eq-us-naval-nimitz` (p5-us-naval-nimitz-factfile). Ford reuses the Nimitz hull form (A: CRS, DOT&E).

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Full-load displacement | ~100,000 | LT | csg-us-cvn78-airlant; csg-us-cvn78-allhands | A | Stated as approximate. Nimitz lineage is 97,000–100,000 LT |
| Length overall | 1,106 (337) | ft (m) | csg-us-cvn78-airlant | A | CONFLICT: All Hands (A) gives 1,092 ft, the Nimitz overall length repeated. Using 1,106 ft overall |
| Waterline beam | 134 (40.8) | ft (m) | csg-us-cvn78-allhands | A | The AIRLANT page lists "Height: 134 feet", which appears to be the beam mislabeled |
| Flight deck width | 256 (78) | ft (m) | csg-us-cvn78-airlant; csg-us-cvn78-allhands | A | Nimitz is 252 ft |
| Draft (full load) | ~12 (39) | m (ft) | csg-us-cvn-seaforces | C-est | No A/B source found. Nimitz repo value is ~11.3 m, so use a 11.3–12.0 m band |
| Maximum speed | 30+ | kt | csg-us-cvn78-airlant; csg-us-cvn78-allhands | A | Public threshold only; the true maximum is not public |
| Group transit / economical speed | 15–20 | kt | — | est | Not public. A nuclear plant has no fuel-economy optimum, so the escorts' 20-kt range-reference speed and the T-AO's 20-kt maximum bound sustained group transit |
| Deployment-average speed of advance (derived) | 7.4 | kt | csg-us-usff-2026 | A | Derived: 57,713 nmi / (326 d × 24 h). Includes flight ops, station-keeping and port visits |
| Propulsion | 2 nuclear reactors (A1B PWR), 4 shafts | — | csg-us-cvn78-airlant; csg-us-cvn-seaforces | A+C | The reactor designation A1B comes from Tier C only |
| Shaft power | 260,000–280,000 | shp | p5-us-naval-nimitz-factfile | est | Ford's figure is not public. Bound: at least the Nimitz A4W plant (~260,000 shp, repo A/B) on the same hull at the same 30+ kt threshold |
| Reactor thermal power | ~700 per reactor | MWt | csg-us-cvn-armyrec | C-est | Tier C only; the same source claims ~27% more than the A4W |
| Electrical generating capacity | 104 (4 × 26 MW turbine generators) | MW | csg-us-cvn78-doncio | A | ~3× Nimitz (All Hands A; GAO A says "near three-fold"). CONFLICT: HII (B) says "more than twice" |
| Design service life | ~50, single mid-life refueling | years | csg-us-cvn-navy-factfile | A | — |
| Total crew (ship + air wing + staff) | ~4,550 | persons | csg-us-cvn78-allhands | A | HII (B) quotes berthing for up to 4,660 |
| Ship's company | 2,500–2,700 | persons | p5-us-naval-nimitz-factfile; csg-us-cvn78-crs | est | Not public. Derived from Nimitz's ~3,000 ship's company (repo A) minus "several hundred fewer sailors" (CRS A) |
| Manning reduction vs Nimitz | ~15 | % | csg-us-cvn78-dote-fy25 | A | CONFLICT: NAVSEA (A) says 20%; GAO (A) cites billet cuts of 500 threshold / 900 objective |
| Aircraft capacity | 75+ | aircraft | csg-us-cvn78-allhands | A | CVW-8 as deployed was about 70-74 (Order Of Battle section) |
| Catapults | 4 EMALS (2 bow, 2 waist) | count | csg-us-cvn78-crs-2013; csg-us-cvn-seaforces | A+C | CRS 2013, quoting DOT&E, refers to the "four-catapult electrical distribution". The bow/waist split comes from Tier C |
| EMALS recharge between launches | <60 | s | csg-us-ga-alre | B | Manufacturer claim. The real launch interval is set by deck handling, which is not public |
| Arresting gear engines (as installed) | 3 AAG engines | count | csg-us-cvn78-dote-fy25 | A | The original design was 4 engines / 3 wires, as on CVN-76/77. The 4th engine was deleted to save cost. A 4th-engine alternative is FY26-funded with installation targeted for FY29. The current configuration cannot rig a redundant barricade if an AAG engine fails |
| Arresting wires | 3 | count | csg-us-cvn78-dote-fy25 | A | Inferred from the "four engines and three wires" original plan. The wire-to-engine mapping as installed is not public |
| Aircraft elevators | 3 (deck-edge) | count | csg-us-cvn78-hii-elev; csg-us-cvn78-awe-navy | A+B | Nimitz has 4 |
| Advanced Weapons Elevators | 11 (10 main + 1 utility) | count | csg-us-cvn78-awe-navy; csg-us-cvn78-crs-213 | A | All 11 were turned over by Dec 2021 |
| AWE lift capacity / speed | 24,000 at 150 | lb, ft/min | csg-us-cvn78-awe-navy | A | Nimitz: 10,500 lb at 100 ft/min |
| AWE availability requirement | 99.7 (DOT&E: unlikely to be met) | % | csg-us-cvn78-crs | A | 23,042 AWE cycles through the 2023 COMPTUEX. Ordnance throughput at Design Reference Mission rates is not yet demonstrated (DOT&E FY25) |
| Design sortie generation rate, sustained | 160 | sorties/day | csg-us-cvn78-dote-fy10 | A | This is the KPP. DOT&E (2014, reported secondhand) called the threshold assumptions of fair weather and no equipment failures unrealistic |
| Design sortie generation rate, surge (24 h) | 270 | sorties/day | csg-us-cvn78-dote-fy10 | A | CONFLICT: naval-technology (C) gives a 220 surge. The KPP was not demonstrated in any DOT&E report through FY25 |
| Design goal vs Nimitz | +30 SGR with −20 crew | % | csg-us-cvn78-navsea-psa | A | — |
| Nimitz reference SGR | ~120 per 12-h fly day; 240 per 24-h surge | sorties | csg-us-cvn78-usni-sgr | C-est | Attributed to DOT&E by USNI News; the primary DOT&E text was not located in this pass (Tier C only - treated as estimate per admission rule) |
| Measured SGR, Feb 2026 test | 120–130 | % of Nimitz | csg-us-cvn78-usni-sgr | C-est | CNO remarks reported by USNI; the Navy released no numbers. USNI works this out to ~160 per 12 h and ~312 per 24 h. Treat as unconfirmed (Tier C only - treated as estimate per admission rule) |
| Single-day launch+recovery record (May 2020) | 167 | cycles/day | csg-us-ga-3000 | B | Carrier-qualification tempo, which DOT&E FY25 says is not KPP-representative |
| 2025–26 deployment air operations | 12,200 launches; 5,760 flight hours; 326 days | — | csg-us-usff-2026 | A | CONFLICT: CNAL/DVIDS (A) says "more than 11,500 aircraft events" over 322 days; a photo caption says 11,800. Average ~37 launches per deployed day |
| 2023 deployment | 8,700+ sorties; 22,900 cumulative launches+recoveries since commissioning | — | csg-us-ga-cvn79-deadload | B | Manufacturer figures |
| EMALS reliability requirement | 4,166 | mean cycles between critical failures | csg-us-cvn78-crs-208 | A | 1 cycle = 1 aircraft launch |
| EMALS reliability achieved | 272 (through ISE 18, FY21); 460 (FY21) / 614 (FY22) | MCBOMF | csg-us-cvn78-dote-fy21; csg-us-cvn78-crs | A | CONFLICT: the two FY21 figures cover different windows. FY23–FY25 reliability is only described as "consistent" with earlier data, with no new number. It is 1–2 orders of magnitude below the requirement |
| AAG reliability requirement | 16,500 | MCBOMF | csg-us-cvn78-crs-208 | A | 1 cycle = 1 aircraft recovery |
| AAG reliability achieved | 115 (FY21) / 460 (FY22) | MCBOMF | csg-us-cvn78-crs | A | No operational update through FY25 (DOT&E FY25) |
| Primary radar | Dual Band Radar: AN/SPY-3 MFR (X-band) + AN/SPY-4 VSR (S-band) | — | csg-us-cvn78-dote-fy25 | A | Unique to CVN-78. Slated for replacement by AN/SPY-6(V)3 EASR + AN/SPQ-9B + Mk 9 TIS, the CVN-79 configuration |
| Radar detection range | n/p | nmi | — | n/p | Not public. est: horizon-limited against a 5-m sea-skimmer at ~19 nmi (35 km) for arrays ~40 m above the waterline, using d = 4.12(√h1+√h2) km. Long-range S-band air search is assumed 150–250 nmi class (est) |
| Combat management / networking | SSDS Mk 2 Mod 6 Baseline 10; CEC AN/USG-2B | — | csg-us-cvn78-dote-fy25 | A | CVN-79 and later get SSDS Baseline 12 and CEC Block II |
| Electronic warfare | AN/SLQ-32B(V)6 with SEWIP Block 2 | — | csg-us-cvn78-dote-fy25 | A | — |
| Point-defense missiles | ESSM Block 1 (Mk 29 "NATO" launchers) + RAM Block 2 (Mk 49 launchers) | — | csg-us-cvn78-dote-fy25; csg-us-cvn78-cssqt | A | CVN-79 and later: an ESSM Block 1/2 mix and RAM Block 2A/2B |
| Mk 29 ESSM launchers | 2 × 8-round | launchers × rounds | csg-us-cvn-seaforces | C-est | Launcher count from Tier C only. Nimitz lineage has 2 Mk 29 (repo A/B) |
| Mk 49 RAM launchers | 2 × 21-round | launchers × rounds | csg-us-cvn-seaforces; csg-us-ram-navy | A+C | 21 rounds per Mk 49 (A); CVN listed as a RAM platform (A); launcher count from C only |
| Phalanx CIWS | 3 (Block 1B, standalone mode) | mounts | csg-us-cvn-seaforces; csg-us-cvn78-dote-fy25 | A+C | Standalone mode from A; mount count from C only |
| Magazines (self-defense reloads, air-wing ordnance tonnage) | n/p | — | — | n/p | Not public |
| Tactical diameter | 1.0–1.7 | km | — | est | No public trial data. Uses 3–5 ship lengths, typical for large high-speed hulls |
| Stores endurance | ~90 | days | p5-us-naval-nimitz-factfile | A+C | Nimitz lineage (repo A/C). Observed 2025–26: 23 replenishments at sea in 326 days, about one every 14 days (csg-us-usff-2026, A) |
| F-35C deployability | Not F-35C deployment-capable in 2025–26 (modifications pending) | — | csg-us-f35c-seapower-2022; csg-us-cvn78-1945-f35c; csg-us-usff-2026 | A+C | Seapower (2022, C): modifications planned for the FY2025 PIA. 19FortyFive (Sep 2026, C): Ford entered its first PIA in Jul 2026 with F-35C modification status unconfirmed. CVW-8 deployed with no F-35C (A) |
| Survivability features | Improved magazine protection; shock-hardened systems; Full Ship Shock Trials Aug 2021; Total Ship Survivability Trial Jan 2025 | — | csg-us-cvn78-dote-fy25 | A | Armor schedule not public (repo Nimitz est: 25–75 mm steel-equivalent) |

### `ddg51_flt2a` — Arleigh Burke Flight IIA (DDG-81 Winston S. Churchill, DDG-96 Bainbridge, plus the doctrinal 4th DDG)

The repo has no DDG-51 record. For CG-47 values use the repo Ticonderoga record, which is not repeated here.

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Full-load displacement | 9,496 | LT | csg-us-ddg-surflant | A | The class fact file (A) gives a 8,230–9,700 LT range across flights. Tech-insertion ships are heavier |
| Length overall | 509.5 (155.29) | ft (m) | csg-us-ddg51-navy-factfile | A | — |
| Beam | 59 (18) | ft (m) | csg-us-ddg51-navy-factfile | A | — |
| Draft | 31 (9.4) | ft (m) | csg-us-ddg-surflant | A | Likely a navigational draft that includes the sonar dome |
| Maximum speed | >30 | kt | csg-us-ddg51-navy-factfile | A | Public threshold |
| Range / reference cruise speed | 4,400 at 20 | nmi at kt | csg-us-ddg-surflant | A | The source says "miles" without specifying; nmi assumed. Fuel state and plant line-up are not given |
| Propulsion | 4 × GE LM2500-30 gas turbines, COGAG, 2 shafts, CPP | — | csg-us-ddg51-navy-factfile; csg-us-ddg-surflant | A | — |
| Shaft power | 100,000 | shp | csg-us-ddg51-navy-factfile | A | CONFLICT: SURFLANT (A) gives 105,000 hp maximum and 90,000 sustained |
| Ship-service generation | 3 × Allison/RR 501-K34 gas-turbine generators (7,500 kW listed) | — | csg-us-ddg-surflant | A | It is unclear whether the 7,500 kW is per unit or total; the SURFLANT table layout is ambiguous |
| Crew | 329 (32 officers, 27 CPO, 270 enlisted) | persons | csg-us-ddg51-navy-factfile | A | CONFLICT: SURFLANT (A) says 323; GlobalSecurity (C) says 380 including the air detachment |
| Combat system | Aegis Weapon System (Baseline varies by hull); Mk 99 fire control; CEC on modernized ships | — | csg-us-ddg-surflant; csg-us-aegis-navy | A | Per-hull baseline is not public in detail |
| Multifunction radar | AN/SPY-1D (DDG-79..90) / AN/SPY-1D(V) (DDG-91+) | — | csg-us-ddg-surflant; csg-us-ddg-globalsecurity | A+C | So DDG-81 has SPY-1D and DDG-96 has SPY-1D(V). The D/D(V) split comes from Tier C |
| SPY-1 track capacity | >100 | targets | csg-us-aegis-navy | A | — |
| SPY-1 air-search range | ~175 (large target) | nmi | csg-us-spy1-wiki; csg-us-spy1-csis | C-est | Not official. CSIS (C) gives ~370 km of track quality. Against sea-skimmers the limit is the radar horizon (~20–25 nmi for a 5-m target, est) |
| Fire-control illuminators | 3 × AN/SPG-62 | count | csg-us-ddg-surflant | A | Semi-active SM-2/ESSM terminal illumination channels. Channel timing is n/p |
| Surface search / navigation radar | AN/SPS-67(V)3; AN/SPS-73(V) | — | csg-us-ddg-surflant | A | DDG-119+ carry SPQ-9B (C); not relevant to the deployed hulls |
| Hull sonar | AN/SQS-53C(V)1 within AN/SQQ-89(V) | — | csg-us-ddg-surflant | A | Detection ranges are n/p |
| Towed array | AN/SQR-19 TACTAS or TB-37U MFTA (SQQ-89A(V)15 backfit) | — | csg-us-ddg-wiki-sandbox; csg-us-sqq89-esd | C-est | Per-hull fit is not public. TB-37U is standard on DDG-113+ and is backfitted via SQQ-89A(V)15 modernization |
| EW / decoys | AN/SLQ-32(V)3 or SEWIP; Mk 53 Nulka; AN/SLQ-25A Nixie; SLQ-39 | — | csg-us-ddg-surflant | A | — |
| VLS | 96 cells Mk 41 Mod 7 (fwd 32 + aft 64) | cells | csg-us-ddg-surflant; csg-us-mk41-navy | A+C | 96 total from A; the 32/64 split from C |
| VLS load categories | SM-2 Blk IIIA/IIIB (IIIC entering), SM-6 Blk I/IA, SM-3 (BMD ships), ESSM quad-pack (4 per cell), Tomahawk Blk IV/V incl. Maritime Strike Blk Va, VL-ASROC | — | csg-us-ddg51-navy-factfile; csg-us-mk41-navy; csg-us-sm-navy; csg-us-tomahawk-navair; csg-us-mst-gs | A+C | MST reached Early Operational Capability in Q4 FY2025, first on DDGs (C). Treat MST as fielded in small numbers |
| Representative CSG escort load (96 cells) | 40 SM-2 + 16 SM-6 + 8 cells ESSM (32 missiles) + 24 Tomahawk (of which 0–8 MST) + 8 VL-ASROC | cells / missiles | — | est | Actual loadouts are not public. Assumes an AAW-heavy CSG screen; SM-3 omitted outside a BMD mission |
| Gun | 1 × Mk 45 Mod 4 5-in/62 (DDG-81+); 600-round magazine; 16–20 rds/min; 13 nmi conventional | — | csg-us-mk45-navy | A | — |
| CIWS | DDG-81: 2 × Phalanx; DDG-85+: 1 × Phalanx (aft) | mounts | csg-us-ddg-wiki-sandbox | C-est | The Navy fact file only says "CIWS". DDG-96 therefore has 1 |
| Harpoon | none (Flight IIA not fitted) | — | csg-us-ddg-wiki-sandbox | C-est | Consistent with the fact-file armament list, which omits Harpoon |
| Torpedo tubes | 2 × Mk 32 triple (6 tubes), Mk 54 lightweight torpedoes | — | csg-us-ddg51-navy-factfile; csg-us-mk54-navy | A | The fact file still says "Mk 46". The fleet is transitioning to Mk 54 (A) |
| Other guns | 2 × Mk 38 25 mm | mounts | csg-us-ddg-surflant; csg-us-mk38-navy | A | Effective range 2,500 yd (A) |
| Embarked helicopters | 2 × MH-60R (dual hangar) | aircraft | csg-us-ddg51-navy-factfile | A | Detached from HSM-70 in this OOB |
| Tactical diameter | 700–1,100 | m | — | est | Not public. Uses ~4.5–7 ship lengths at full rudder, high speed |

### `ddg51_flt2` — Arleigh Burke Flight II (DDG-72 Mahan)

Only the differences from Flight IIA are listed.

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Full-load displacement | 8,637 | LT | csg-us-ddg-surflant | A | — |
| Length overall | 505 (153.92) | ft (m) | csg-us-ddg51-navy-factfile | A | — |
| Crew | ~303–320 | persons | csg-us-ddg-surflant | est | SURFLANT gives 303 for Flight I and leaves Flight II blank |
| VLS | 90 cells (29 + 61; strikedown crane positions) | cells | csg-us-ddg-globalsecurity; csg-us-ddg-wiki-sandbox | C-est | CONFLICT: the SURFLANT class-level text says "96 cell" for DDG-51 generally. That appears to describe Flight IIA only |
| Representative load (90 cells) | 40 SM-2 + 12 SM-6 + 6 cells ESSM (24) + 24 Tomahawk + 8 VL-ASROC | cells / missiles | — | est | Same logic as Flight IIA. ESSM integration on Flight I/II depends on modernization (n/p) |
| Radar | AN/SPY-1D | — | csg-us-ddg-globalsecurity | C-est | — |
| Gun | Mk 45 Mod 2 5-in/54 (DDG-51..80) | — | csg-us-mk45-navy | A | Same 13-nmi range and 600-round magazine |
| CIWS | 2 × Phalanx (not SeaRAM) | mounts | csg-us-ram-navy; csg-us-ddg-wiki-sandbox | A+C | The Navy RAM fact file lists SeaRAM only on DDG-64/71/75/78, not DDG-72 |
| Harpoon | 2 × Mk 141 quad launchers (8 RGM-84) if retained | missiles | csg-us-ddg-wiki-sandbox | C-est | Whether Mahan still carries them is not public |
| Towed array | AN/SQR-19 | — | csg-us-ddg-globalsecurity | C-est | — |
| Aviation | Flight deck only, no hangar | — | csg-us-ddg-surflant | A | Can refuel and rearm a visiting MH-60R, but embarks none |

### `ssn_virginia_blk3_4` — Virginia-class SSN, Block III/IV (doctrinal, generic hull)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Length | 377 (114.8) | ft (m) | csg-us-ssn-navy-factfile | A | Block V with VPM: 461 ft (not used) |
| Beam | 34 (10.36) | ft (m) | csg-us-ssn-navy-factfile | A | — |
| Submerged displacement | ~7,800 | tons | csg-us-ssn-navy-factfile | A | Stated as 7,925 metric tonnes |
| Surfaced displacement | n/p | tons | — | n/p | Not in Navy sources. est ~6,900–7,000 t, taking the Los Angeles-class surfaced/submerged ratio of ~0.88 from the repo record |
| Maximum submerged speed | 25+ | kt | csg-us-ssn-navy-factfile; csg-us-ssn-montana-navy | A | Public threshold. Commonly estimated at 30–35 kt (not asserted) |
| Quiet (patrol / transit) speed | n/p | kt | — | est | Not public. Suggested sim band: ≤8 kt search, 15–20 kt quiet transit |
| Test depth | >800 (>244) | ft (m) | csg-us-ssn-montana-navy; csg-us-ssn-oregon-seapower | A | Only a lower bound is public. Tier C estimates run up to ~490 m. Use 244–490 m (est) |
| Propulsion | 1 nuclear reactor (S9G), 1 shaft, pump-jet | — | csg-us-ssn-navy-factfile; csg-us-ssn-seaforces | A+C | Reactor designation and pump-jet from C |
| Shaft power | ~40,000 | shp | csg-us-ssn-seaforces | C-est | — |
| Crew | 145 (17 officers, 128 enlisted) | persons | csg-us-ssn-navy-factfile | A | CONFLICT: commissioning releases (A) say ~136 (Oregon); other sources give 134–135 |
| Torpedo tubes | 4 × 21 in (533 mm) | count | csg-us-ssn-navy-factfile | A | — |
| Torpedo-room weapon capacity | ~25 | torpedo-size weapons | csg-us-ssn-crs | A | Mk 48, Tomahawk, UUVs, or mines (in lieu) |
| Vertical payload | 2 × Virginia Payload Tubes × 6 Tomahawk = 12 | missiles | csg-us-ssn-navy-factfile | A | Block V adds 4 VPM tubes × 7 = 28 (not used) |
| Total torpedo-size weapons | ~37 | weapons | csg-us-ssn-crs | A | — |
| Weapons | Mk 48 ADCAP Mod 7; Tomahawk Blk IV/V; MST Blk Va (submarine fielding planned early 2026) | — | csg-us-ssn-navy-factfile; csg-us-mst-nsj | A+C | MST submarine fielding date from C. USN submarines no longer carry UGM-84: NAVAIR lists Harpoon sub-launch as "foreign submarine" |
| Bow sonar | Large Aperture Bow (LAB) water-backed array (SSN-784+), BQQ-10 processing | — | csg-us-ssn-navy-factfile; csg-us-ssn-seaforces | A+C | LAB from A; processing designation from C |
| Other arrays | Wide-aperture flank arrays; sail and chin high-frequency arrays; towed TB-34 (fat-line) and TB-29/TB-33 (thin-line) | — | csg-us-ssn-seaforces | C-est | Detection ranges and source levels are n/p |
| Masts | 2 photonics masts (no barrel periscope) | — | csg-us-ssn-navy-factfile | A | — |
| Radiated noise / detectability | n/p | dB | — | n/p | Classified. Needs a scenario-level parameter with a sensitivity sweep |

### `tao205_john_lewis` — John Lewis-class fleet replenishment oiler (doctrinal, generic hull)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Full-load displacement | 49,620 (T-AO-205..207) / 49,793 (T-AO-208+) | t | csg-us-tao-navy-factfile | A | Lightship 22,531 / 22,424 t |
| Length | 227.3 | m | csg-us-tao-navy-factfile | A | PACOM (A) says 746 ft, which is consistent |
| Beam | 32.2 | m | csg-us-tao-navy-factfile | A | — |
| Draft | n/p | m | — | est | est 10.5–11.5 m, by displacement scaling from the Kaiser class (~10.9 m, C) |
| Maximum speed | 20 | kt | csg-us-tao-navy-factfile | A | This caps CSG speed during replenishment and any escorted transit with the oiler |
| Propulsion | Twin shaft, geared medium-speed diesels with PTO/PTI generators | — | csg-us-tao-navy-factfile | A | Installed power is n/p |
| Crew | 125–129 civilian mariners | persons | csg-us-tao-navy-factfile | A | CONFLICT: DOT&E FY25 (A) says the design crew is 95 CIVMARs with accommodations for 34 more, for 129 total |
| Fuel cargo | 25,782 m³ (~162,000 bbl) | m³ | csg-us-tao-navy-factfile; csg-us-tao-pacom | A | Diesel (F-76) and JP-5 split is n/p |
| Dry stores | 1,589–1,590 | m³ | csg-us-tao-navy-factfile | A | — |
| Freeze/chill | 885 (205–207) / 1,017 (208+) | m³ | csg-us-tao-navy-factfile | A | — |
| Fresh-water cargo | 213 | m³ | csg-us-tao-navy-factfile | A | — |
| UNREP stations | Port and starboard fueling, astern fueling, connected cargo transfer, VERTREP deck; T-AO fleet can run up to 5 stations | — | csg-us-cvn78-dote-fy25; csg-us-tao-navy-factfile | A | Transfer rates are n/p |
| Ammunition | none (not an ammunition ship) | — | csg-us-tao-navy-factfile | A | Ordnance resupply needs a T-AKE/T-AOE; not modeled |
| Self-defense | Nixie torpedo countermeasure; crew-served machine-gun mounts; space/weight reserved for defensive weapons | — | csg-us-cvn78-dote-fy25 | A | — |
| Aviation | No embarked aircraft; VERTREP pad for H-60/MV-22 | — | csg-us-tao-navy-factfile | A | — |

### `taoe6_supply` — Supply-class T-AOE (alternative CLF branch; count 0)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Full-load displacement | 48,800 | LT | csg-us-taoe-navy | A | — |
| Length / beam | 754 (229.9) / 107 (32.6) | ft (m) | csg-us-taoe-navy | A | — |
| Maximum speed | 25 | kt | csg-us-taoe-navy | A | Fast enough to stay with a CSG |
| Propulsion | 4 × GE LM2500, 2 shafts, 105,000 hp | — | csg-us-taoe-navy | A | — |
| Cargo | >177,000 bbl fuel; 2,150 t ammunition; 500 t dry; 250 t refrigerated | — | csg-us-taoe-navy | A | — |
| Crew | 160 civilian + 29 military | persons | csg-us-taoe-navy | A | — |
| Aircraft | 2 × MH-60S (normally embarked) | aircraft | csg-us-taoe-navy | A | — |
| Hulls in service | 2 (Supply, Arctic) | — | csg-us-taoe-navy | A | The fact file was last updated 2021; Arctic was still operating in May 2026 (DVIDS RAS video) |

### `ac_fa18e` / `ac_fa18f` — F/A-18E/F Super Hornet (Block II/III)

Reuses repo `eq-us-air-fa18e` (p5-us-air-fa18e-navair, p5-us-air-fa18e-boeing). Rows marked "repo" already exist there; this section adds what the repo lacks.

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Maximum speed | Mach 1.8+ | Mach | p5-us-air-fa18e-navair | A | repo |
| Service ceiling | 50,000+ | ft | p5-us-air-fa18e-navair | A | repo |
| Combat range (clean + 2 AIM-9) | 1,275 | nmi | p5-us-air-fa18e-navair | A | repo. This is a range, not a radius |
| Ferry range (2 AIM-9, 3 × 480-gal tanks) | 1,660 | nmi | p5-us-air-fa18e-navair | A | repo |
| Combat radius, typical strike/interdiction | ~390 | nmi | csg-us-cvw-cimsec | C-est | Not published by NAVAIR. CIMSEC quotes 390 nmi; the Legacy Hornet was ~370. Planning band 390–500 nmi depending on tanks and profile (est) |
| MTOW | 66,000 | lb | p5-us-air-fa18e-boeing; csg-us-fa18-navair | A+B | NAVAIR now also lists 66,000 lb, so it is no longer single-source |
| Internal fuel | 14,700 (E) / 13,760 (F) | lb | csg-us-fa18-wiki | C-est | Not on the NAVAIR page. Tier C values |
| Buddy tanking (A/A42R-1 ARS + 4 × 480-gal) | ~29,000 total fuel aboard | lb | csg-us-fa18-wiki; csg-us-fa18-migflug | C-est | Offload at a given radius is n/p. est: ~12,000–16,000 lb give at ~150–200 nmi from the carrier (est). The MQ-25 is intended to take over this role (DOT&E A) |
| Radar | AN/APG-79 AESA (Block II+) | — | csg-us-fa18-navair | A | NAVAIR says "AESA" without the designation; APG-79 comes from C. Detection range n/p |
| IRST | IRST Block II (centerline pod/tank) | — | csg-us-cvn78-dote-fy25 | A | Fleet distribution is n/p |
| Weapon stations | 11 | stations | csg-us-fa18-migflug | C-est | Max external load ~17,750 lb (C) |
| Gun | M61A1/A2 20 mm | — | p5-us-air-fa18e-navair | A | repo |
| Loadout: CAP | 4–6 × AIM-120C/D + 2 × AIM-9X + 1–3 external tanks | stores | — | est | Mission config is not public; typical public imagery |
| Loadout: anti-ship strike | 2 × AGM-158C LRASM (or 4 × AGM-84D/Block II+ Harpoon) + 2 × AIM-120 + 2 × AIM-9X + 1 tank | stores | csg-us-lrasm-dote-fy25; csg-us-harpoon-navair | A+est | F/A-18E/F is a threshold LRASM platform (A). 2 LRASM per jet is the est heavy-store count |
| Loadout: SEAD | 2–4 × AGM-88E AARGM + AIM-120/AIM-9X | stores | csg-us-aargm-navair | A+est | AARGM-ER (AGM-88G) not yet at IOC (planned 1QFY27; DOT&E A) |
| Loadout: recovery / mission tanker | ARS centerline + 4 × 480-gal tanks | stores | csg-us-fa18-wiki | C-est | Tier C: one-fifth to one-third of Super Hornet sorties are tanking |
| Crew | 1 (E) / 2 (F) | — | p5-us-air-fa18e-navair | A | repo |

### `ac_ea18g` — EA-18G Growler

Reuses repo `eq-us-air-ea18g` (p5-us-air-ea18g-navair): 50,000-ft ceiling, 850+ nmi combat range with 2 × AIM-120, 3 × ALQ-99, 2 × AGM-88, 2 tanks; crew 2. Additions:

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Service ceiling | 50,000 | ft | p5-us-air-ea18g-navair | A | repo |
| Combat range (2 × AIM-120, 3 × ALQ-99 TJS, 2 × AGM-88, 2 × 480-gal tanks) | >850 | nmi | p5-us-air-ea18g-navair | A | repo. Mission-conditioned range, not a radius |
| Empty / recovery weight | 33,094 / 48,000 | lb | p5-us-air-ea18g-navair | A | repo |
| Crew | 2 | persons | p5-us-air-ea18g-navair | A | repo |
| Typical EA loadout | 3 × ALQ-99 (or 2 × NGJ-MB) + 2 × AGM-88 + 2 × AIM-120 + 2 tanks | stores | p5-us-air-ea18g-navair | A | repo configuration |
| Jammer pods | AN/ALQ-99 TJS (legacy) and/or NGJ-MB (2 underwing AESA pods) | — | csg-us-ngjmb-dote-fy25 | A | NGJ-MB passed IOT&E (Dec 2024) and FRP review (Sep 2025) but DOT&E rates it "not suitable" for operational missions because of reliability. Default sim load: ALQ-99, with NGJ-MB as a branch |
| Jamming effective radiated power / ranges | n/p | — | — | n/p | Classified |
| Maximum speed | ~Mach 1.8 | Mach | p5-us-air-fa18e-navair | est | Inherited from the F/A-18F airframe; lower with pods (not published) |

### `ac_e2d` — E-2D Advanced Hawkeye

Reuses repo `eq-us-air-e2d` (p5-us-navy-e2d-navair, p5-us-navy-e2d-airpac): 300+ kt, 37,000-ft ceiling, crew 5, APY-9. The repo explicitly lacks range, endurance and radar range. Additions:

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Speed | 300+ | kt | p5-us-navy-e2d-navair | A | repo |
| Ceiling | 37,000 | ft | p5-us-navy-e2d-navair | A | repo |
| Crew | 5 (2 pilots + 3 mission-systems operators) | persons | p5-us-navy-e2d-navair | A | repo |
| Engines | 2 × RR T56-A-427A, 5,100 shp each | — | p5-us-navy-e2d-navair | A | repo |
| Empty mass / maximum gross mass | 40,484 lb / 23,850 kg | — | p5-us-navy-e2d-navair; p5-us-navy-e2d-airpac | A | repo. Gross mass is the common E-2 reading |
| Radar | AN/APY-9 UHF AESA, mechanical + electronic scan, 360° with 90° electronic sector scan | — | csg-us-apy9-lockheed; csg-us-e2d-dote-fy25 | A+B | — |
| APY-9 search range | ~300–350 | nmi | csg-us-apy9-usni; csg-us-apy9-wiki | C-est | Not official. USNI (C) says "at least 300 nmi"; Wikipedia (C) says ~350 nmi. Target RCS is not specified |
| Maximum speed | 350 | kt | csg-us-e2-midway | C-est | NAVAIR gives only "300+" |
| Cruise speed | ~256 | kt | csg-us-e2-midway | C-est | — |
| Unrefueled endurance | ~6 | h | csg-us-e2-midway | C-est | Air-refueling capability is confirmed (A). Wikipedia (C) says refueling doubles time on station to ~5 h |
| Ferry range | ~1,460–1,540 | nmi | csg-us-e2-midway | C-est | E-2C-era figures |
| Datalinks | CEC, Link 16 (MIDS), TTNT | — | csg-us-e2d-dote-fy25 | A | NIFC-CA node |

### `ac_mh60r` — MH-60R Seahawk

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Crew | 3 | persons | csg-us-mh60r-navair | A | Tier C gives 3–4 |
| Engines | 2 × GE T700-GE-401C/D | — | csg-us-mh60r-navair | A | — |
| Weight | 15,170 empty / 23,500 max gross | lb | csg-us-mh60r-navair | A | — |
| Length | 64 ft 10 in | ft | csg-us-mh60r-navair | A | — |
| Maximum speed | ~180 | kt | csg-us-mh60s-navair | A | Taken from the MH-60S NAVAIR page (same airframe). CONFLICT: naval-technology (C) gives 267 km/h (144 kt) max cruise; ArmyRecognition (C) gives 146 kt max |
| Cruise speed | ~120–145 | kt | csg-us-mh60r-navaltech; csg-us-mh60r-armyrec | C-est | — |
| Range | 245–450 | nmi | csg-us-mh60s-navair; csg-us-mh60r-aerocorner | A+C | CONFLICT: MH-60S NAVAIR (A) gives 245 nmi; Tier C gives 380–470 nmi. Use 245 as the mission-radius-relevant conservative figure |
| Endurance | ~2.7 (ASW) / ~3.3 (ASuW) | h | csg-us-mh60r-navaltech | C-est | — |
| Sensors | AN/APS-153 multi-mode radar (ISAR, periscope detection); AN/AQS-22 ALFS dipping sonar; sonobuoy launcher (25 tubes, C); AN/AAS-44C FLIR; AN/ALQ-210 ESM | — | csg-us-mh60r-navair-frp; csg-us-mh60r-armyrec | A+C | NAVAIR (A) confirms dipping sonar, ESM, ISAR/periscope radar and FLIR. Designations come from C. Detection ranges n/p |
| ASW loadout | 2 × Mk 54 (up to 3) | torpedoes | csg-us-mh60r-armyrec | C-est | est: 2 torpedoes + sonobuoys is the planning load |
| ASuW loadout | up to 8 × AGM-114 Hellfire (4-rail × 2) or APKWS; crew-served gun | stores | csg-us-mh60r-armyrec | C-est | Hellfire range ~8 km (C) |

### `ac_mh60s` — MH-60S Seahawk

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Maximum speed | 180 | kt | csg-us-mh60s-navair | A | — |
| Ceiling | 13,000 | ft | csg-us-mh60s-navair | A | — |
| Range | 245 | nmi | csg-us-mh60s-navair | A | — |
| Weight | 14,430 empty / 23,500 max gross | lb | csg-us-mh60s-navair | A | — |
| Crew | 4 | persons | csg-us-mh60s-navair | A | — |
| Roles | ASuW, CSAR, VERTREP, MEDEVAC, SPECWAR, organic airborne MCM | — | csg-us-mh60s-navair | A | ASuW weapons (Hellfire, guns) as MH-60R, est |

### `ac_c2a` — C-2A Greyhound (VRC-40 detachment)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Payload | 10,000 | lb | csg-us-c2a-navy; csg-us-c2a-northrop | A+B | — |
| Range | 1,000+ (with payload) | nmi | csg-us-c2a-navy | A | CONFLICT: naval-technology (C) says 1,300 nmi |
| Cruise / max speed | ~260 / ~343 | kt TAS | csg-us-c2a-navy | A | — |
| Ceiling | 30,000 | ft | csg-us-c2a-navy | A | — |
| Crew | 4 | persons | csg-us-c2a-navy | A | Up to 26 passengers (C) |
| Engines | 2 × Allison T56-A-425, 4,600 shp each | — | csg-us-c2a-navy | A | — |

### `ac_cmv22b` — CMV-22B Osprey (optional branch, count 0)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Payload / range | 6,000 at 1,150 | lb at nmi | csg-us-cmv22-navair | A | — |
| Max VTO / rolling TO weight | 52,600 / 60,500 | lb | csg-us-cmv22-navair | A | — |
| Crew / troops | 4 / 24 | persons | csg-us-cmv22-navair | A | — |
| IOC | 14 Dec 2021 | date | csg-us-cmv22-navair | A | — |

### `ac_f35c` — F-35C Lightning II (optional branch, count 0 in the as-deployed CVW-8)

Reuses repo `eq-us-air-f35c` (p5-us-air-f35c-lockheed B: Mach 1.6, combat radius >600 nmi on internal fuel, internal fuel 19,750 lb, standard internal load 2 × AIM-120 + 2 × GBU-31; p5-us-air-f35c-hiwars C: 50,000-ft ceiling). Additions:

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Maximum speed (full internal load) | Mach 1.6 | Mach | p5-us-air-f35c-lockheed | B | repo |
| Combat radius (internal fuel) | >600 | nmi | p5-us-air-f35c-lockheed | B | repo |
| Internal fuel | 19,750 | lb | p5-us-air-f35c-lockheed | B | repo |
| Weapons payload | 18,000 | lb | p5-us-air-f35c-lockheed | B | repo |
| Standard internal load | 2 × AIM-120C/D + 2 × GBU-31 | stores | p5-us-air-f35c-lockheed | B | repo |
| Service ceiling | 50,000 | ft | p5-us-air-f35c-hiwars | C-est | repo (Tier C only) |
| Deployed on CVN-78 in 2025–26 | No | — | csg-us-usff-2026 | A | See the carrier F-35C deployability row |
| Planned squadron size | 10 (early deployments) → 14–16 (planned) → up to 20 ("super squadron" concept) | aircraft | csg-us-cvw-seapower-2020; csg-us-cvw-twz | C-est | CONFLICT: this changed several times between 2020 and 2022 (Tier C only - treated as estimate per admission rule) |
| Combat radius | ~613 | nmi | csg-us-cvw-cimsec | C-est | Consistent with the repo's Lockheed ">600 nmi" (B) (Tier C only - treated as estimate per admission rule) |
| Internal anti-ship weapon | n/p (LRASM is not integrated internally; JSM/NSM-type internal carriage is not integrated on the USN F-35C) | — | — | n/p | Treat F-35C ASuW as external-store or sensor/ISR role only (est) |

### `ac_mq25a` — MQ-25A Stingray (not fielded; count 0)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Status | First production-representative MQ-25A flight 25 Apr 2026; LRIP Lot 1 awarded Sep 2026; flight test continues to ~FY2029 | — | csg-us-mq25-navy; csg-us-mq25-boeing; csg-us-mq25-wiki | A+B+C | Not deployable in a 2025–26 scenario |
| Role | Organic carrier tanker (takes over F/A-18E/F tanking), secondary maritime ISR | — | csg-us-cvn78-dote-fy25 | A | — |
| Fuel offload | n/p (commonly cited ~15,000 lb at 500 nmi) | lb | — | C-est | Not verified in this pass. Do not use without a source |

## Weapons

### `wpn_sm2_blk3` — SM-2 Block IIIA/IIIB (RIM-66M) Medium Range

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Range | up to 90 | nmi | csg-us-sm-navy | A | Kinematic maximum. The engagement envelope vs altitude is n/p |
| Weight | 1,558 (708) | lb (kg) | csg-us-sm-navy | A | — |
| Length / diameter | 4.72 / 0.343 | m | csg-us-sm-navy | A | — |
| Propulsion | Dual-thrust solid rocket | — | csg-us-sm-navy | A | — |
| Guidance | Inertial + Aegis midcourse command; semi-active radar terminal (IIIA); SARH + IR (IIIB) | — | csg-us-sm-navy | A | Needs an SPG-62 illuminator in the terminal phase |
| Warhead | Blast-fragmentation, radar + contact fuze | — | csg-us-sm-navy | A | Mass n/p. Tier C commonly quotes ~62 kg (Mk 125), not verified here |
| Speed | n/p | Mach | — | C-est | Tier C commonly quotes Mach 3.5 (not verified in this pass) |
| Follow-on | SM-2 Block IIICU active variant entering procurement | — | csg-us-wpn-budget-fy27 | A | Not modeled in 2025–26 |

### `wpn_sm6` — SM-6 Block I/IA (RIM-174 ERAM)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Weight | ~3,300 | lb | csg-us-sm-navy | A | — |
| Length / span | ~21 ft 6 in / ~3 ft 6 in | ft | csg-us-sm-navy | A | — |
| Propulsion | Mk 72 booster + dual-thrust sustainer | — | csg-us-sm-navy; csg-us-sm6-csis | A+C | — |
| Seeker | Dual-mode active (AMRAAM-derived) + semi-active | — | csg-us-sm-navy | A | Supports engage-on-remote (NIFC-CA / CEC) and over-the-horizon engagements |
| Range | 130 (published) / up to ~200–250 | nmi | csg-us-sm6-wiki; csg-us-sm6-csis | C-est | CONFLICT: Wikipedia (C) gives 130 nmi published; CSIS (C) gives 370 km. The Navy fact file gives no range. Use 130–200 nmi |
| Speed | Mach 3.5 | Mach | csg-us-sm6-wiki; csg-us-sm6-defpost | C-est | — |
| Roles | AAW, terminal BMD, ASuW | — | csg-us-sm6-rtx; csg-us-wpn-budget-fy27 | A+B | — |
| Warhead | Blast-fragmentation | — | csg-us-sm6-csis | C-est | Mass n/p (Tier C ~64 kg, not verified) |

### `wpn_essm` — ESSM Block 1 (RIM-162D) / Block 2 (RIM-162 Blk 2)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Weight | 622 | lb | csg-us-essm-navy | A | Block 1 |
| Length | 12 | ft | csg-us-essm-navy | A | — |
| Diameter | 8 in guidance / 10 in motor (Blk 2: 10 in throughout) | in | csg-us-essm-navy | A | — |
| Range | n/p (Navy: "Classified"); ~27 nmi (50 km) open source | nmi | csg-us-essm-navy; csg-us-essm-navalnews | A+C | The Navy explicitly classifies range. The 50 km figure is C-est |
| Speed | n/p (Navy: "Classified"); Mach 4+ open source | Mach | csg-us-essm-navy; csg-us-essm-navalnews | A+C | C-est |
| Guidance | Blk 1: semi-active CW/ICW illumination with S/X-band midcourse uplink. Blk 2: dual active + semi-active | — | csg-us-essm-navy | A | Blk 2 IOC 2021 |
| Warhead | Annular blast-fragmentation, 90 | lb | csg-us-essm-navy | A | — |
| Packing | 4 per Mk 41 cell (Mk 25 quad-pack); 8 per Mk 29 launcher | — | csg-us-essm-navy; csg-us-cvn-seaforces | A+C | — |
| Fit | CVN-78: Block 1 only; DDGs: Block 1/2 | — | csg-us-cvn78-dote-fy25 | A | — |

### `wpn_ram` — RIM-116 RAM Block 2 (RIM-116C)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Weight | 194.4 (88.2) | lb (kg) | csg-us-ram-navy | A | Block 1A: 164 lb |
| Length / diameter | 2.88 m / 15.87 cm | — | csg-us-ram-navy | A | — |
| Speed | Supersonic | — | csg-us-ram-navy | A | Tier C: Mach 2–3 |
| Range | ~9 (Blk 1/1A) to ~15 (Blk 2) | km | csg-us-ram-weaponsystems; csg-us-ram-seaforces | C-est | CONFLICT: seaforces (C) reports "10 nmi" for Block 2B. The Navy gives no range |
| Guidance | Passive RF midcourse + IR terminal; fire-and-forget, no illuminator | — | csg-us-ram-navy | A | — |
| Warhead | 7.9 (explosive weight) | lb | csg-us-ram-navy | A | — |
| Launcher | Mk 49 GMLS, 21 rounds | rounds | csg-us-ram-navy | A | — |

### `wpn_phalanx` — Mk 15 Phalanx CIWS Block 1B

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Gun | M61A1 20 mm Gatling, APDS | — | csg-us-phalanx-navy | A | — |
| Rate of fire | 4,500 (ASM/aircraft) / 3,000 (asymmetric) | rds/min | csg-us-phalanx-navy | A | — |
| Magazine | 1,550 | rounds | csg-us-phalanx-navy | A | About 20 s of continuous fire at 4,500 rpm (derived) |
| Effective range | ~1.5–3.6 | km | csg-us-phalanx-seaforces | C-est | Navy range not published. seaforces (C) gives 3,600 m, which is likely a maximum. Use 1.5 km for kill against an ASCM (est) |
| Muzzle velocity | ~1,100 | m/s | csg-us-phalanx-seaforces | C-est | — |
| Weight | 13,600 | lb | csg-us-phalanx-navy | A | — |

### `wpn_mk45` — Mk 45 5-inch gun

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Range (conventional ammunition) | 13 | nmi | csg-us-mk45-navy | A | — |
| Rate of fire | 16–20 | rds/min | csg-us-mk45-navy | A | 20-round automatic loader drum |
| Magazine | 600 (DDG) / 1,200 (CG) | rounds | csg-us-mk45-navy | A | — |
| Variants | Mod 2 5"/54 (DDG-51..80); Mod 4 5"/62 (DDG-81+) | — | csg-us-mk45-navy | A | — |

### `wpn_tomahawk` — Tomahawk Block IV/V (TLAM-E); Block Va Maritime Strike (MST)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Range | 900 (1,600 km) | nmi | csg-us-tomahawk-navy | A | Block IV/V. MST range is n/p; the ~1,000 statute miles quoted in trade press is consistent |
| Speed | High subsonic | — | csg-us-tomahawk-navy | A | Tier C often quotes ~0.75 Mach / ~880 km/h (not verified) |
| Weight (with booster) | 3,330 | lb | csg-us-tomahawk-navair | A | — |
| Length / diameter / span | 20.3 ft / 21 in / 8 ft 6 in | — | csg-us-tomahawk-navair | A | — |
| Propulsion | Williams F415 turbofan + Mk 135 booster | — | csg-us-tomahawk-navair | A | — |
| Guidance (Blk IV/V) | INS, TERCOM, DSMAC, GPS; two-way satcom retargeting, loiter | — | csg-us-tomahawk-navy | A | — |
| Guidance (Blk Va MST) | Adds multi-mode seeker for moving maritime targets | — | csg-us-tomahawk-navair; csg-us-mst-gs | A+C | Seeker modes (active radar + passive RF/IR claimed by C) not confirmed by A |
| Warhead | 1,000-lb class unitary | lb | csg-us-tomahawk-navy | A | Block Vb JMEWS not yet fielded (A) |
| MST status | Early Operational Capability Q4 FY2025 on DDGs; submarines planned early 2026; up to 1,302 conversions | — | csg-us-mst-gs; csg-us-mst-nsj | C-est | Tier C only for the EOC date; the Navy fact file (2021) calls MST a "future" capability. Treat availability as est (Tier C only - treated as estimate per admission rule) |

### `wpn_harpoon` — Harpoon (RGM/AGM-84)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Weight (with booster) | 1,523 (690.8) | lb (kg) | csg-us-harpoon-navair | A | — |
| Length | 3.8 air / 4.6 surface | m | csg-us-harpoon-navair | A | — |
| Guidance | Sea-skimming, radar-altimeter cruise; active radar terminal; sea-skim or pop-up | — | csg-us-harpoon-navair | A | Block II+ adds GPS and datalink |
| Range | ~67 (Blk 1C) to ~120 (Blk II) | nmi | csg-us-harpoon-designation; csg-us-harpoon-ran | A+C | RAN (A, allied government) gives 124 km for Block II. The USN does not publish range |
| Warhead | 488 (221) | lb (kg) | csg-us-harpoon-designation | C-est | WDU-18/B penetrating blast-fragmentation |
| Speed | High subsonic | — | csg-us-harpoon-ran | A | — |
| USN launch platforms | F/A-18A–F, P-3C; Flight I/II DDGs (canisters) | — | csg-us-harpoon-navair | A | Not on Flight IIA DDGs |

### `wpn_lrasm` — AGM-158C LRASM

Reuses repo `eq-us-weapon-agm158c` (p5-us-weapon-agm158c-navair A, p5-us-weapon-agm158c-lockheedmartin C): >200 nmi, high-subsonic sea-skimming, 1,000-lb class warhead, GPS/INS + datalink + passive RF + IIR terminal. Additions:

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Range | >200 | nmi | p5-us-weapon-agm158c-navair | A | repo. The precise C-1 range is classified |
| Speed / profile | High subsonic, low-observable, sea-skimming terminal | — | p5-us-weapon-agm158c-navair; p5-us-weapon-agm158c-lockheedmartin | A+C | repo |
| Guidance | GPS/INS (anti-jam) + datalink; passive RF + IIR terminal; autonomous target selection | — | p5-us-weapon-agm158c-navair; p5-us-weapon-agm158c-lockheedmartin | A+C | repo. Sensor weighting classified |
| Warhead | 450–454 (1,000-lb class, WDU-42/B family) | kg | p5-us-weapon-agm158c-navair; p5-us-weapon-agm158c-lockheedmartin | A+C | repo |
| All-up mass | 1,020–1,250 | kg | p5-us-weapon-agm158c-navair; p5-us-weapon-agm158c-lockheedmartin | est | repo bounded estimate |
| Fleet configuration | All AGM-158C upgraded to LRASM 1.1 (fielded Nov 2023); AGM-158C-3 (extended range, BLOS comms) in development | — | csg-us-lrasm-dote-fy25 | A | C-3 excluded from the 2025–26 baseline |
| USN carrier platform | F/A-18E/F (threshold) | — | csg-us-lrasm-dote-fy25 | A | Not F-35C internal |
| Procurement | FY26 request: LRASM 30 + LRASM-ER 90 | missiles | csg-us-wpn-highlights-fy26 | A | Inventory magazine depth is n/p |

### `wpn_aim120d` — AIM-120D AMRAAM

Reuses repo `eq-us-weapon-aim120d`. Tier C range claims (~160 km) were not admitted.

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Mass | 162.4 (358) | kg (lb) | p5-us-weapon-aim120d-navair | A | repo |
| Length / diameter / span | 3.66 / 0.178 / 0.483 | m | p5-us-weapon-aim120d-navair | A | repo |
| Propulsion | Solid rocket motor | — | p5-us-weapon-aim120d-navair | A | repo |
| Guidance | Inertial midcourse + launch-aircraft datalink; active radar terminal; home-on-jam | — | p5-us-weapon-aim120d-navair | A | repo |
| Range / speed | Classified | — | p5-us-weapon-aim120d-navair | n/p | repo. The Navy explicitly classifies both |
| Warhead / fuze | Blast-fragmentation; active-radar proximity fuze | — | p5-us-weapon-aim120d-navair | A | repo |

### `wpn_aim9x` — AIM-9X Block II Sidewinder

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Launch weight | 186 (84.37) | lb (kg) | csg-us-aim9x-navair | A | — |
| Length / diameter / span | 3.02 m / 0.13 m / 0.45 m | — | csg-us-aim9x-navair | A | — |
| Motor | ATK Mk 139 solid rocket | — | csg-us-aim9x-navair | A | — |
| Guidance | Imaging IR, high off-boresight, thrust vectoring; Block II datalink (lock-on after launch) | — | csg-us-aim9x-navair | A | — |
| Warhead | Annular blast-fragmentation | — | csg-us-aim9x-navair | A | — |
| Range / speed | Classified | — | csg-us-aim9x-navair | A | n/p. est WVR planning envelope ≤ ~18 nmi (est) |

### `wpn_aargm` — AGM-88E AARGM (fielded) / AGM-88G AARGM-ER (not yet IOC)

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| AGM-88E weight | 795 (361) | lb (kg) | csg-us-aargm-navair | A | — |
| AGM-88E speed | Mach 2+ | Mach | csg-us-aargm-navair | A | — |
| AGM-88E guidance | GPS/INS, anti-radiation homing, active MMW terminal | — | csg-us-aargm-navair | A | — |
| AGM-88E range | ~80 | nmi | csg-us-aargm-designation | C-est | Not published by the Navy |
| AGM-88G status | IOC planned 1QFY27; IT events delayed in FY25 | — | csg-us-aargm-dote-fy25 | A | Excluded from the 2025–26 baseline |
| AGM-88G weight / range | ~1,030 lb / ~120–160 nmi | — | csg-us-aargm-designation | C-est | CONFLICT: Wikipedia (C) says 121 nmi; designation-systems (C) says 160 nmi |

### `wpn_mk48` — Mk 48 ADCAP Mod 7 heavyweight torpedo

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Weight | 3,744 | lb | csg-us-mk48-navy | A | — |
| Diameter | 21 | in | csg-us-mk48-navy | A | Length ~5.8 m (C) |
| Warhead | 650 | lb HE | csg-us-mk48-navy | A | — |
| Propulsion | Liquid propellant (Otto Fuel II), piston engine, pump-jet | — | csg-us-mk48-navy; csg-us-mk48-wiki | A+C | — |
| Guidance | Wire-guided; active/passive acoustic homing; CBASS sonar (Mod 7); re-attack | — | csg-us-mk48-navy; csg-us-mk48-dote-fy25 | A | APB 6 and Shallow Water Urgent Build tested in 2025 |
| Speed | >28 official; ~55 (up to 65) estimated | kt | csg-us-mk48-wiki; csg-us-mk48-seaforces | C-est | CONFLICT on the top figure: 55 vs 65 kt |
| Range | >5 mi official; ~20–27 nmi estimated (speed-dependent: ~21 nmi at 55 kt, ~27 nmi at 40 kt) | nmi | csg-us-mk48-wiki | C-est | — |
| Depth | >1,200 ft official; ~800 m estimated | — | csg-us-mk48-wiki; csg-us-mk48-seaforces | C-est | — |

### `wpn_mk54` — Mk 54 Mod 0/1 lightweight torpedo

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Weight | 607 | lb | csg-us-mk54-navy | A | — |
| Length / diameter | 106.9 / 12.75 | in | csg-us-mk54-navy | A | — |
| Warhead | 100 | lb HE | csg-us-mk54-navy | A | — |
| Propulsion | Liquid propellant | — | csg-us-mk54-navy | A | — |
| Launch platforms | Mk 32 SVTT, MH-60R, P-8A, VL-ASROC payload | — | csg-us-mk54-navy; csg-us-vla-navy | A | Mod 1 IOC 2023 |
| Speed / range | n/p (Mk 46 lineage ~40 kt / ~6 nmi, est) | kt / nmi | — | est | Not public. Bound from the Mk 46 dual-speed heritage; no admissible source in this pass |

### `wpn_vla` — RUM-139 Vertical Launch ASROC

| Parameter | Value | Unit | Source ID | Tier | Uncertainty / conflict |
| --- | --- | --- | --- | --- | --- |
| Range | over 10 | statute mi | csg-us-vla-navy | A | Delivers a Mk 54 (or Mk 46 Mod 5A(SW)) to a water-entry point |
| Weight | 1,650 | lb | csg-us-vla-navy | A | — |
| Length / diameter | 16.7 ft / 14.1 in | — | csg-us-vla-navy | A | — |
| Warhead (payload) | 96.8 lb HE | lb | csg-us-vla-navy | A | That is the torpedo payload warhead. The Mk 54 fact file gives 100 lb |

### Naval Strike Missile

Not fitted to any hull in this OOB. NSM on the USN is on LCS/FFG/USMC (FY26 budget lists NSM procurement). The only DDG with NSM is DDG-62 (C), which is not in this group. Excluded.

## Arbitrated Corrections

- DDG-72 Mahan is Flight II (fact file DDG-72..78), not Flight IIA and not the repo's Flight I record.
- F-35C, MQ-25A, and CMV-22B are count 0 for the 2025-26 Ford deployment.
- The fourth large surface combatant is a generic Flight IIA fill because CSG-12 deployed without a cruiser.
- The SSN and oiler are doctrinal fills because the Navy does not name them.
- The task premise put all DDGs at Flight IIA; the corrected mix is 2 × `ddg51_flt2a` (DDG-81, DDG-96) + 1 × `ddg51_flt2` (DDG-72 Mahan), plus the optional 4th DDG fill.

## Residuals

Status labels: `authority_blocked` = not public or classified. `research_open` = a public source may exist but was not reached in this pass. `conflict` = public sources disagree. `estimate` = value derived here or taken from Tier C only.

| # | Item | Status | Detail / recommended handling |
| --- | --- | --- | --- |
| R1 | Escort flight mix | conflict | The task premise put all DDGs at Flight IIA and the repo record is Flight I. In fact DDG-72 Mahan is Flight II (90 cells, no hangar, Mk 45 Mod 2), while DDG-81 and DDG-96 are Flight IIA. Model 2 × `ddg51_flt2a` + 1 × `ddg51_flt2`, plus the optional 4th DDG fill |
| R2 | No cruiser in CSG-12 | research_open | The group deployed with 3 DDGs and no CG. The cruiser slot is filled with a 4th generic Flight IIA DDG (doctrinal). Remaining CG count in 2026 is itself disputed (Tier C: 3, 5 or 7) |
| R3 | SSN and CLF assignment | authority_blocked | The Navy does not publish which SSN or oiler supported CSG-12. Both are doctrinal fills (Virginia Blk III/IV, T-AO-205) |
| R4 | Per-squadron aircraft counts (VFA/HSC/HSM) | estimate | Not published for CVW-8 2025–26. Using 11/11/11/11 VFA, 5 VAQ, 4 VAW, 8 HSC, 11 HSM, 2 VRC, which sums to the standard 44 strike fighters. Suggest scenario ranges of ±2 per VFA squadron and 4–5 E-2D |
| R5 | F-35C on Ford | conflict | Designed to operate the F-35C but not deployment-capable. The FY2025 modification plan (C) was not confirmed as executed. CVW-8 carried no F-35C. The `ac_f35c` branch is count 0 in the baseline |
| R6 | Sortie generation rate | conflict + authority_blocked | 160/270 per day is a design KPP (A) that DOT&E had not validated as of FY25. The surge figure conflicts (270 vs 220 C). The Feb 2026 test result is reported only as "120–130% of Nimitz" by the CNO (C, no numbers released). Nimitz reference numbers (120/12 h, 240/24 h) are attributed to DOT&E only via USNI. Recommend a sim default of 120–160 sustained sorties per flying day with EMALS/AAG failure injection |
| R7 | EMALS/AAG reliability | conflict | Several MCBOMF figures exist for different windows (EMALS 181/272/460/614; AAG 115/460). No FY23–25 numeric update. Only 3 AAG engines, so no redundant barricade rigging. Use a failure rate range rather than a point value |
| R8 | Ford radar performance (DBR SPY-3/SPY-4) | authority_blocked | No public detection ranges. DBR is one of a kind, with sustainment risk (DOT&E). Use radar horizon geometry plus a notional S-band volume-search range (est 150–250 nmi) |
| R9 | Ford defensive launcher counts (2 Mk 29, 2 Mk 49, 3 CIWS) | estimate | Only Tier C gives counts; A confirms the weapon types. The Nimitz lineage (repo A/B) is consistent |
| R10 | Ford draft, shaft power, reactor MWt | estimate | Draft ~12 m (C), shaft power ≥260,000 shp (est from the Nimitz lineage), ~700 MWt per reactor (C). Not public at Tier A/B |
| R11 | Turning data (tactical diameter) for all ships | authority_blocked | No public trial data. Length-scaled estimates only (CVN 1.0–1.7 km, DDG 0.7–1.1 km) |
| R12 | Economical / transit speeds | estimate | Only the DDG 4,400 nmi at 20 kt is public (A). Group transit of 15–20 kt is est. Measured deployment average speed of advance is 7.4 kt (derived from A) |
| R13 | VLS loadouts | authority_blocked | Real loadouts are never published. Representative loads are est (AAW-heavy). Maritime Strike Tomahawk availability relies on Tier C EOC reporting (Q4 FY2025) |
| R14 | Missile kinematics: ESSM, AIM-120D, AIM-9X range/speed | authority_blocked | The Navy marks these "Classified". Open-source ESSM ~50 km / Mach 4+ is C-est. AIM-120D and AIM-9X ranges were not admitted |
| R15 | SM-6 range, SM-2 speed and warhead mass | conflict / estimate | SM-6 published 130 nmi vs 200–250 nmi estimates (C). The Navy fact file gives SM-2 range only. Warhead masses are n/p |
| R16 | RAM, Phalanx, Harpoon ranges | estimate | RAM 9–15 km (C, and Block 2B "10 nmi" conflicts), Phalanx 1.5–3.6 km (C), Harpoon 67–120 nmi (A allied + C). USN publishes none |
| R17 | Mk 48 / Mk 54 speed, range and depth | authority_blocked | Official figures are lower bounds only (>28 kt, >5 mi, >1,200 ft). Tier C estimates are 55–65 kt, 21–27 nmi, ~800 m. The Mk 54 has no public speed/range; the Mk 46-lineage bound (~40 kt / ~6 nmi) is est |
| R18 | Sensor ranges (SQS-53C, TB-37U, SQR-19, BQQ-10/LAB, APS-153, AQS-22, APG-79) | authority_blocked | No public detection ranges. Need scenario-level sonar-equation parameters. SPY-1 ~175 nmi and APY-9 300–350 nmi are C-est only |
| R19 | Virginia test depth, top speed, acoustic signature | authority_blocked | Only >800 ft and 25+ kt are public (A). Radiated noise is classified |
| R20 | Buddy-tanking offload and MQ-25 performance | estimate / research_open | Super Hornet ARS total fuel ~29,000 lb is C. Offload vs radius is est. MQ-25 was not fielded in 2025–26 (A); its offload figure was not verified |
| R21 | Crew numbers | conflict | CVN total 4,550 (A) vs 4,660 berthing (B). DDG 329 (fact file) vs 323 (SURFLANT). SSN 145 (fact file) vs ~136 (commissioning release). T-AO 125–129 vs 95 + 34 |
| R22 | Ford length | conflict | 1,106 ft (AIRLANT A) vs 1,092 ft (All Hands A, likely carried over from Nimitz). Using 1,106 ft |
| R23 | Electrical capacity | conflict | ~3× Nimitz (All Hands A / GAO "near three-fold") vs "more than twice" (HII B). 4 × 26 MW turbine generators (DON CIO A) |
| R24 | Deployment air-ops totals | conflict | 12,200 launches / 326 days (USFF A) vs 11,500+ events / 322 days (CNAL A) vs 11,800 (photo caption). The differences are counting-window artifacts |
| R25 | Crew/air wing personnel, ship's company | estimate | Ship's company 2,500–2,700 is est. No A/B figure found |
| R26 | CRS RS20643 Ford class characteristics table | research_open | Only the text of the Mar 2025 PDF was mined; the congress.gov HTML was 403 to fetch tools. A later CRS version may give an updated SGR or F-35C status |

## Evidence Boundary

- This document is research-grade; it is not runtime authority for any Echelon-Forge simulation.
- No content here should be read as a real-world operational prediction.
- Counts and parameters marked as estimates (`est`, `C-est`) are estimates, not confirmed values.
- A Tier A or Tier B source supersedes a C-only or estimate row wherever a future pass finds one.
