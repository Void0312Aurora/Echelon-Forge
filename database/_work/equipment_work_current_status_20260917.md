# Equipment Work Current Status

Status: `2026-09-25` measured state of the equipment tree under the reduced write set.

Parent: [README.md](README.md)

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/_work/equipment_work_current_status_20260917.md`
Owner: `database/equipment-data`
Last verified: `2026-09-25`

This revision replaces the first measurement pass, which was produced by a
hand-written audit and reported three deviations that do not survive the runnable
check in [check_equipment_tree.py](check_equipment_tree.py). See
[Retracted Findings](#retracted-findings).

## Branch And Divergence

| Item | Value |
| --- | --- |
| Branch | `codex/database-scaffold` |
| Base | `d1ebb5d3` |
| Off-base commits | 103 |
| Behind `origin/main` | 218 commits |
| Ahead of `origin/main` | 103 commits |
| `origin/main` files under `database/` | 0 |
| Tracked files under `database/` | 736 |
| Merge dry-run conflicts (`HEAD` vs `origin/main`) | 0 |

`origin/main` carries no files under `database/`, so the tree this work touches is
branch-exclusive and the lag is conflict-free. Anything written outside `database/`
would land in the moving mainline surface instead; that is the reason the write set
is reduced.

## Automated Check Result

Command: `python database/_work/check_equipment_tree.py`

| Condition | Result |
| --- | --- |
| `C1` every referenced source id resolves | PASS, 0 dangling, 0 manifest/path mismatch |
| `C2` backlog leaf binding (`Equipment ID`) | PASS after the `E2` backfill |
| `C3` backlog vs coverage status | PASS, 106 of 106 coverage rows agree |
| `C4` source admission floor | PASS; all 368 manifests now carry explicit rights/provenance/residual fields, with rights values still `not_recorded` |
| `C5` source-artifact consistency | PASS, no unnamed or aggregate package claims |
| `C6` retrieval record | PASS, 233 citations remain advisory with failed/not_attempted/no_record status; all 368 packages now carry an explicit Retrieval block, including 157 `not_recorded` blocks |
| `C7` field-level provenance | PASS, 2,298 parameter rows checked; 0 missing value/source/tier/uncertainty metadata findings |
| `C8` materialized source ledger | PASS, 368 ledger rows match 368 manifests; 211 include retrieval+retention provenance and 157 include manifest+retention only; scope is explicit as complete/partial |

Measured counts:

| Metric | Value |
| --- | --- |
| Source packages (manifests) | 368 |
| Materialized source-ledger rows | 368 |
| Catalog leaves (carry `## Parameters`) | 150 |
| Distinct source ids referenced by leaves | 368 |
| Leaves without `Equipment ID` | 0 |
| Backlog rows | 151 |
| Coverage rows | 106 |
| Status: `cataloged` / `parameter_complete` / `held` | 0 / 151 / 0 |

## Leaf Completeness Against The Queue

The queue now calls all 151 rows `parameter_complete`, and the former M1252
`cataloged` leaf carries a complete research parameter table with an explicitly
bounded Tier C mobility estimate. The checker therefore reports no stub leaf binding defect
for the non-held queue rows. A separate catalog scan finds 232 README leaves: 150
with a parameter table and 82 without one. The 82 are outside the current queue-
binding defect and remain a depth follow-up rather than evidence of completed extraction.

## Coverage Semantics

`coverage/README.md` describes `coverage.csv` as a discovery queue that feeds the
backlog, and defines its `status` column as starting at `queued`. The file does not
behave that way: its 106 rows are exactly the 106 in-scope `parameter_complete` rows of the
backlog, verified in both directions. It is an extract of the completed set, not a
pre-backlog discovery surface.

The content is therefore consistent; the documented role and the documented status
vocabulary are not. This is a documentation drift, not a data defect. The current
extract contains 106 rows.

## Open Findings

| Id | Finding | Evidence | State |
| --- | --- | --- | --- |
| `D2` | Source rights/redistribution are unresolved | C4 finds no missing rights field; the ledger records `rights_status=not_recorded` for all 368 packages | open; metadata shape is closed, but legal status still needs source-specific confirmation |
| `D3` | 82 catalog leaves outside the non-held queue have no parameter table | catalog scan: 232 README leaves, 150 with `## Parameters`, 82 without; all 82 are recorded in [`catalog_scope_decisions_20260925.csv`](catalog_scope_decisions_20260925.csv) as hierarchy indexes or family parents with no `Equipment ID` | closed in R-34; excluded from the parameter queue rather than treated as incomplete equipment leaves |
| `D4` | Parameter table shape split | 88 leaves use `Parameter \| Value \| Source \| Confidence`; 58 use the common `Field` form; 3 module/extended leaves use the other supported forms | open; C7 covers all five forms while new leaves default to the common `Field` form |
| `D5` | Disjoint naval namespaces | Live tree check finds the canonical `catalog/naval/ships/surface-combatant/` path and no alternate `surface-combatants/` directory; the canonical rule is now documented | closed in R-35 |
| `D6` | Ledger not materialized | `sources/ledger/ledger.csv` now indexes all 368 manifests; missing rights/scope/retrieval values remain explicit in the index | closed in R-31; source-admission debt remains visible |
| `D7` | `coverage.csv` role and status vocabulary contradicted its own README | README now defines it as a discovery/index surface whose admitted rows mirror backlog status; 106 of 106 current rows are `parameter_complete` | closed in R-32 |
| `D8` | Country rows share a variant leaf without a stated rule | README and backlog docs now define operator-row versus shared-variant-leaf binding and prohibit silent operator-scope merging | closed in R-32 |
| `D9` | `Equipment ID` scheme was not declared | README now defines country-owned `eq-*`, reusable `module-*`, and explicitly scoped country-less shared identities | closed in R-32 |

## Repaired In This Pass

| Repair | What changed |
| --- | --- |
| `C2` binding | 32 leaves received an `Equipment ID` line derived from their queue row, inserted as additive metadata after `Last verified` rather than as a new `## Identity` section, so the change stays independent of the `D4` shape question |
| `C2` predicate | The check no longer demands a binding from a stub leaf or a `held` row, and no longer treats a shared variant leaf as a defect |
| C-17A operator gap | The leaf listed only the United States Air Force while a Royal Air Force queue row pointed at it. Added the RAF operator row citing `p5-uk-air-c17a-raf`, which was an acquired but unreferenced package. The UK queue row keeps its own id and now carries a note explaining the share |
| Leaf identity | The C-17A leaf had been given `eq-uk-air-c17a` by the backfill. Its parameters and operator table are United States; corrected to `eq-us-air-c17a` |
| `C4` retention | 43 manifests, all air-domain, received the `Retention:` line the raw-source rule requires. The wording follows the 146 packages that already carried it |
| F-35C completion | Added variant-specific propulsion, flight, fuel, armament and crew/ceiling fields; the latter two remain explicitly Tier C and are not copied from F-35A/B |
| KC-46A completion | Added propulsion, thrust, speed, ceiling, range, aircrew-seat semantics and refueling-system fields from the AMC fact sheet |
| C-17A completion | Added height, cargo compartment, ceiling, crew, troop/medical load and mission-conditioned range semantics from the Dover fact sheet |
| Retrieval records | Added or refreshed retrieval blocks for the three USAF/Navy packages and the F-35C manufacturer package; added one traceable HiWars secondary package for the remaining public F-35C crew/ceiling fields |
| MQ-9A completion | Promoted the existing baseline/extended-range parameter table after retrieving both USAF fact-sheet packages; ER readings remain configuration-labelled |
| C-130J completion | Promoted the standard-length C-130J table after retrieving the USAF fact sheet; retained explicit arithmetic corrections and excluded the stretched J-30 values |
| F/A-18E completion | Added E-mark propulsion, speed, ceiling, conditioned combat/ferry range, crew and armament fields from NAVAIR; Boeing is used only for the family maximum-takeoff-weight block, not as an E-specific wingspan substitute |
| EA-18G completion | Added variant-specific propulsion, geometry, mass, ceiling, conditioned combat range, crew and electronic-attack stores from NAVAIR |
| F-16C Block 50 completion | Replaced generic-family engine and geometry readings with the Shaw Block 50/52 fact sheet, removed the unsupported 42,300 lb reading, and bounded APG-68(V)9 applicability to the FMS context the source actually states |
| Retrieval records (third batch) | Added successful Tavily-proxy retrieval records for the two NAVAIR pages, the Boeing family page and both USAF F-16 pages; recorded fields not returned instead of inferring them |
| F-15EX completion | Added the Boeing capability fields for representative AMRAAM/large-ordnance carriage and AESA/EPAWSS/open mission-system context; engine and empty-weight conflicts remain source-bounded |
| RAF C-17A queue promotion | Promoted the UK row against the already complete shared C-17A leaf after verifying the RAF operator/source row is explicit |
| Rafale C/B/M completion | Added official Dassault common performance blocks, named C/B/M variant readings, and an official armament/stores package; family-level values and the M 13-station boundary remain explicit |
| Rafale retrieval records | Replaced stale hand-entered access dates with successful Tavily-proxy retrieval records for the Dassault and Aviationist pages, recording fields not returned |
| Typhoon FGR4 completion | Refreshed the RAF retrieval record and promoted the complete weapon/sensor table; generic-type mass and fuel remain explicitly bounded secondary readings |
| F-35B completion | Added the RAF weapons, sensor and powerplant rows, while preserving the Marine Corps fuel band and class-qualified weight boundary |
| P-8A/Poseidon MRA1 completion | Added RAF sensor, weapon, defensive-aids and crew fields plus Boeing common mass, propulsion and conditioned range; UK mission-loadout scope remains explicit |
| A400M Atlas C.1 completion | Added RAF Atlas-specific fields and the Airbus 2025 manufacturer specification block; retained empty-weight and length differences rather than reconciling them |
| Retrieval records (P-8/A400M) | Added successful Tavily-proxy retrieval records for the RAF pages and retained separate official Boeing/Airbus packages for the common data blocks |
| R-31 evidence roles | Added explicit `direct_variant`, `family_context`, `bounded_estimate`, and `open` semantics; community/Tier C values remain non-authoritative and raw HTML is not retained |
| R-31 source ledger | Materialized `sources/ledger/ledger.csv` from the 368 source manifests; missing rights, retrieval and scope fields are preserved as visible findings rather than inferred |
| R-31 field provenance check | Added C7 metadata validation for 2,298 parameter rows and C8 exact manifest-to-ledger coverage; both pass |
| R-32 identity and queue rules | Documented Equipment ID syntax, shared-leaf/operator-row binding, module identity, and the actual discovery/index role of `coverage.csv` |
| R-33 ledger provenance status | Added explicit `provenance_status` to the source ledger; rights remain `not_recorded` for all 368 rows rather than being inferred |
| R-34 catalog scope decisions | Classified all 82 no-parameter README nodes as hierarchy indexes or family parents, with path/title/evidence recorded in `catalog_scope_decisions_20260925.csv` |
| R-35 naval namespace | Verified the alternate namespace is absent and documented `surface-combatant/` as the sole canonical path |
| R-36 manifest admission fields | Added explicit rights, provenance, and residual status to all 368 manifests; unknown rights remain `not_recorded` and retrieval failures remain visible |
| R-37 retrieval gap materialization | Added explicit `not_recorded` Retrieval blocks to the 157 legacy manifests that lacked one; no retrieval success is inferred |
| R-38 manifest scope status | Added explicit `Scope status: complete/partial` to all 368 manifests; the 53 partial scopes remain visible in the ledger |
| R-39 AH-1Z small research batch | Added a named AH-1Z leaf plus NAVAIR, Bell and GlobalSecurity manifests; official/product/secondary boundaries remain explicit |
| French C-130J-30 completion | Added the French Ministry's J-30 operating block for endurance, operating mass, cruise profile, crew and load configurations without overwriting the separate U.S. stretch-column definitions |
| French C-130J-30 retrieval record | Replaced the stale access-only manifest with a successful Tavily-proxy retrieval record and a single-artifact title |
| Voyager KC2 completion | Added the RAF KC2/KC3 fit and Airbus A330 MRTT structural, fuel, payload and conditioned-range block; carried fuel, offload and capacity remain distinct quantities |
| Voyager retrieval records | Added a successful RAF retrieval record and a separate official Airbus technical-brochure package |
| Protector RG Mk1 completion | Added RAF-specific weapons, crew and mission-system rows plus common MQ-9B geometry, mass, fuel, payload, range and data-link values; UK certification and configuration boundaries remain explicit |
| Protector retrieval records | Added a successful RAF retrieval record and a separate official General Atomics MQ-9B data-sheet package; the common package does not stand in for UK-specific integration claims |
| French E-3F completion | Added official French variant-level geometry, CFM56-2-A3 propulsion, mass, speed, ceiling, endurance, crew and AWACS mission-system rows; family TF33 readings remain cross-checks |
| French ATL2 completion | Added Dassault geometry/performance values and the government Standard 6 radar, acoustic, optronic and tactical-console block; conflicting range and empty-weight definitions remain separate |
| French Mirage 2000-5F completion | Added official single-seat, five-display, RDY and MICA evidence; no weapon station count was inferred and family numeric readings remain bounded |
| French retrieval records | Refreshed the E-3F, Mirage 2000-5F and ATL2 manufacturer packages and added separate official E-3F AWACS-system and ATL2 Standard 6 packages |
| UK Wildcat HMA2 completion | Added Royal Navy length, speed, range, lifting, crew, sensor and weapon rows alongside Leonardo AW159 mass, fuel, engine and condition-specific performance; customer loadout limits remain unstated |
| UK Merlin HM2 completion | Added Royal Navy Mk2 length, speed, range, lifting, crew, sonar/radar and weapon rows; retained the RTM322 direction and generic AW101 performance boundaries |
| UK naval helicopter retrieval records | Added successful Royal Navy Wildcat/Merlin operator packages and refreshed the Leonardo AW159/AW101 retrieval records |
| UK Chinook HC6A completion | Added RAF fleet geometry, engine, crew, payload, weapons, sensors and defensive-aids rows; CH-47F family empty/max weights are retained as bounded references rather than HC6A certification |
| French NH90 NFH completion | Added Airbus NFH-specific useful load, crew, engine-power, speed, range, missions and weapon-capacity rows while retaining common NH90 10,000 kg performance conditions |
| Chinook/NH90 retrieval records | Added successful U.S. Army CH-47F and Airbus NFH packages and refreshed the RAF Chinook/NHIndustries retrieval blocks |
| U.S. E-3G completion | Added official Block 40/45 mission-system, crew-context and operational-surveillance rows while keeping E-3 family airframe values bounded |
| UK AH-64E completion | Added British Army E-variant speed, engine, weight, weapon and sensor rows plus a versioned Tier C community empty-weight cross-check; no source is treated as certification |
| E-3G/AH-64E retrieval records | Added the official E-3G Block 40/45, British Army AH-64E and CMANO variant packages and refreshed the Boeing AH-64E retrieval record |
| French Mirage 2000D RMV completion | Added the official French 2000D technical-card geometry, crew, thrust, mass, carried-fuel, speed, ceiling and refuelling fields; RMV armament and mission-system integration remains separately bounded |
| Expansion run setup | Added the unattended 150-record target, blocker/skip policy and per-batch commit gate in `equipment_expansion_20260923.md` |
| U.S. transport/mission-aircraft expansion batch | Added C-5M, AC-130J, CV-22B, HC-130J and E-2D leaves with official USAF/Navy source packages; common-family readings remain explicitly bounded |
| Russian export fighter completion batch | Promoted Su-35S, Su-34E and Su-30SME after refreshing ROSOBORONEXPORT/UAC retrievals; export/family boundaries and the Su-35S Tier C empty-mass reading remain explicit |
| Chinese/Russian transport and fighter completion batch | Promoted J-16, Tu-160M and Il-76MD-90A after live retrieval; official modernization/role blocks remain separate from public Tier C platform readings |
| Weapon expansion batch | Added AIM-9X Block II, AIM-120D and GBU-39A/B with official NAVAIR/Boeing geometry, mass, propulsion/guidance, warhead and fuze fields; classified performance remains unestimated |
| U.S. naval-aircraft expansion batch | Added P-3C, F/A-18C and UH-1Y with official Navy/NAVAIR/Marine Corps geometry, mass, propulsion, flight, crew, payload, armament and mission-system fields; common A-D and conditioned HOGE/radius boundaries remain explicit |
| Chinese fighter/bomber completion batch | Promoted J-11B/BS, J-15 and H-6K after adding named armament, crew, avionics/mission-system and empty-mass blocks; B/BS, baseline/STOBAR, engine-batch and 79/95 t mass boundaries remain explicit |
| Chinese AEW/tanker/utility-aircraft completion batch | Promoted KJ-500, YY-20A and Z-20 after adding named radar/refuelling/flight-control and crew/fuel rows; dimensional and fuel conflicts remain source-bounded |
| Small-arms expansion batch | Added M4A1, AK-74M, FN SCAR-L Mk2 STD and HK416 A5 14.5-inch with variant-specific geometry, mass, operation, feed and rate fields; AK-74M government/community conventions remain separate |
| Machine-gun expansion batch | Added M249, PKM, MG3 and MG4 with sourced caliber, feed, geometry, mass, rate and employment fields; differing range and bolt-rate conventions remain explicit |
| Crew-served weapon expansion batch | Added M2A1, M240B, Mk 19 Mod 3 and AGS-17 with variant-bounded mass, geometry, range, crew and employment fields; mount and weapon mass remain distinct |
| Artillery expansion batch | Added M777A2, CAESAR 6x6 and BM-21 Grad with sourced calibre, mass, range, mobility and fire-control fields; baseline and rocket-envelope limits remain explicit |
| Anti-armour launcher expansion batch | Added Carl-Gustaf M4, AT4CS HP and M72A5-C1 with variant-bounded calibre, dimensions, mass, range/effect and employment fields; ammunition-independent range claims remain excluded |
| Anti-armour missile/launcher expansion batch | Added Panzerfaust 3, RPG-7 and SPIKE LR II with variant-bounded launcher, round, range/effect, guidance and employment fields; launcher/round quantities remain separate |
| MiG-31BM held-record completion | Added a named MiG-31BM technical profile with variant-specific geometry, mass, propulsion, conditioned range, crew, radar and weapon rows; no MiG-31B or MiG-31K values were substituted |
| Su-57 held-record completion | Added separate UAC programme and RedStar baseline profiles for the Russian Su-57; Su-57E export and prototype-only values remain excluded and the alternate engine-thrust reading is retained |
| Tu-95MS held-record completion | Added a named Tu-95MS profile with geometry, mass, fuel, powerplant, conditioned performance, warload and MS-6/MS-16 missile-carriage rows |
| Attack-helicopter held-record completion | Added named Ka-52 and Mi-28NM profiles with variant-bounded geometry, mass, propulsion, performance, weapon and employment rows; naval/modernised and other marks remain separate |
| KC-130J held-record completion | Added NAVAIR, USMC and Lockheed Martin platform/tanker blocks with source-labelled dimensional, mass, propulsion, range, offload and transport capacities; C-130J-30 and HC-130J values remain excluded |
| Tiger HAD held-record completion | Added Airbus HAD geometry, engine, fuel, conditioned performance, mission-system and weapon-capacity rows plus a separate French retrofit/operator package; HAP/UHT/MkIII values remain excluded |
| A-50U held-record completion | Added Xinhua A-50U performance and separate Airforce Technology/RedStar upgrade, crew, mission-system and family-baseline packages; 190/210 t and 800/850 km/h source readings remain separate |
| Residual variant-boundary audit | Rechecked Y-20 and M1252 with current official, specialist and community alternatives; M1252 still lacks a direct propulsion/mobility package and remains `cataloged` rather than receiving cross-variant values |
| Y-20 public-parameter completion | Added generic Y-20 Store norske leksikon and Military Factory packages for crew, speed, ceiling and payload-conditioned range; retained Y-20A/Y-20B/YY-20A boundaries and the 45 m versus 50 m wingspan conflict |
| M1252 family-power boundary refresh | Added the DOT&E legacy DVH 350 hp C7 versus DVH-A1 450 hp C9 boundary as a named family reference; M1252-specific engine, speed and range remain unknown and the queue row stays `cataloged` |
| M1252 community corroboration | Added a Tier C WarWheels package for crew/configuration and the DVH-to-M1252/M1252-A1 boundary; no unresolved mobility field was filled and the queue row stays `cataloged` |
| M1252 RMS6-L range completion | Added the MCTP 3-01D M1252-specific approximate HE mortar range (200–6,570 m); vehicle propulsion, speed and operational range remain unknown and the queue row stays `cataloged` |
| M1252 operator-manual search boundary | Confirmed the public four-volume TM 9-2355-364-10-1 through -4 set and date, but did not obtain parameter-bearing manual text; propulsion, speed and vehicle range remain unknown and the queue row stays `cataloged` |
| M1252 PMCS mirror exclusion | ArmyADP's public Stryker checklist is for M1126/M1127 and TM 9-2355-311-10; it does not expose M1252/TM 9-2355-364-10 parameters, so no mobility value was imported |
| M1252 low-tier family baseline | Added IJEAT's generic C7/approximately 97–100 km/h/approximately 500 km IAV reference as an explicit Tier C family context row |
| M1252 bounded estimate completion | Promoted the M1252 queue row after converting the cited family baseline into an explicitly labelled Tier C bounded estimate; direct M1252 validation remains a cross-check and the estimate is not a runtime default |

## Retracted Findings

The first pass reported these. All three are withdrawn.

| Withdrawn | Why it was reported | Why it is withdrawn |
| --- | --- | --- |
| Dangling citation `p5-us-ground-m1a2sepv3-armytechnology` on the M1A2 SEP v3 leaf | An audit script that resolved source packages by declared `Source ID` under only part of the `raw/sources/` tree | The package exists at `raw/sources/army_technology/p5-us-ground-m1a2sepv3-armytechnology/manifest.md`, its `Source ID` line matches, and its own text names the geometry, crew, AGT1500, M256, FLIR, data-link and APU statements the leaf cites it for. The then-current C1 run confirmed 0 dangling ids; the present tree also resolves all 368 manifests |
| `coverage.csv` status not trustworthy | The file marked all 55 rows `parameter_complete` and held only 18 air rows against 70 in `air.csv` | The `air.csv` comparison was the observation, the conclusion was wrong. Both directions of the coverage-to-backlog comparison agree, so `C3` passes. The real defect is documentary and is now `D7` |
| Source-reference count 169 against 193 on disk | The same partial-scan audit | The comparison mixed two denominators: 169 is the count of *distinct* ids leaves cite, against 193 *packages* on disk. Both are correct; the implied gap was not |

## Admission Boundary

Every open finding sits inside the reduced write set. `D2` is the only one that
depends on a maintained standard owned outside this tree
(`docs/research/standards/public_data_source_admission.md`); under the reduced scope
the repair is to complete the missing fields at the manifest level rather than to
amend that standard.

## Explicit Overclaim Refusals

- The 151 `parameter_complete` rows are research drafts. They are not calibrated, not
  cross-checked, and not runtime-eligible.
- No file in this tree is consumed by the runtime loader.
- Family names remain grouping nodes; only concrete variant leaves count as records.
- `cataloged` means a draft leaf exists. It does not mean the parameter set is complete.

## Next Action Order

All eight machine-checkable conditions pass. What remains is not a defect the check
can see:

1. `D2` source-admission fields — backfill rights/redistribution and residual details where the source permits it; retain `not_recorded` when it does not.
2. `D4` shape convergence — use the five supported forms only for migration, and make the `Field | Value | Source | Tier | Configuration / uncertainty` form the default for new leaves.
3. Backfill source rights/provenance details where evidence permits; keep unknowns explicit.
4. Resume new research in small batches only after the above rules are stable; run C1–C8 and commit each batch.
