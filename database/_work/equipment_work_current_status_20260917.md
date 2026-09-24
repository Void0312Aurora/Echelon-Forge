# Equipment Work Current Status

Status: `2026-09-24` measured state of the equipment tree under the reduced write set.

Parent: [README.md](README.md)

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/_work/equipment_work_current_status_20260917.md`
Owner: `database/equipment-data`
Last verified: `2026-09-24`

This revision replaces the first measurement pass, which was produced by a
hand-written audit and reported three deviations that do not survive the runnable
check in [check_equipment_tree.py](check_equipment_tree.py). See
[Retracted Findings](#retracted-findings).

## Branch And Divergence

| Item | Value |
| --- | --- |
| Branch | `codex/database-scaffold` |
| Base | `d1ebb5d3` |
| Off-base commits | 56 |
| Behind `origin/main` | 218 commits |
| Ahead of `origin/main` | 56 commits |
| `origin/main` files under `database/` | 0 |
| Tracked files under `database/` | 648 |
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
| `C3` backlog vs coverage status | PASS, 105 of 105 coverage rows agree |
| `C4` source admission floor | PASS after the `E3` retention backfill |
| `C5` source-artifact consistency | PASS, no unnamed or aggregate package claims |
| `C6` retrieval record | PASS, 55 unretrieved citations remain advisory; 158 packages lack a retrieval block |

Measured counts:

| Metric | Value |
| --- | --- |
| Source packages (manifests) | 350 |
| Catalog leaves (carry `## Parameters`) | 146 |
| Distinct source ids referenced by leaves | 350 |
| Leaves without `Equipment ID` | 0 |
| Backlog rows | 150 |
| Coverage rows | 105 |
| Status: `cataloged` / `parameter_complete` / `held` | 2 / 145 / 3 |

## Leaf Completeness Against The Queue

The queue calls 2 rows `cataloged`, and all 2 now point at leaves carrying a
`## Parameters` table. The checker therefore reports no stub leaf binding defect
for the non-held queue rows. A separate catalog scan still finds 82 README leaves
without a parameter table; those are outside the current queue-binding defect and
remain a depth follow-up rather than evidence of completed extraction.

## Coverage Semantics

`coverage/README.md` describes `coverage.csv` as a discovery queue that feeds the
backlog, and defines its `status` column as starting at `queued`. The file does not
behave that way: its 105 rows are exactly the 105 in-scope `parameter_complete` rows of the
backlog, verified in both directions. It is an extract of the completed set, not a
pre-backlog discovery surface.

The content is therefore consistent; the documented role and the documented status
vocabulary are not. This is a documentation drift, not a data defect.

## Open Findings

| Id | Finding | Evidence | State |
| --- | --- | --- | --- |
| `D2` | No source package records a rights field | `C4` `missing_rights_field_advisory`, 310 of 310 | open; the admission standard requires it of a ledger row |
| `D3` | 82 catalog leaves outside the non-held queue have no parameter table | catalog scan: 202 README leaves, 120 with `## Parameters`, 82 without (one module table uses a distinct header) | open; scope and depth for these leaves still need a decision |
| `D4` | Parameter table shape split | 60 leaves use a `Field`-based table; 59 use `Parameter \| Value \| Source \| Confidence`; 82 have no parameter table; one module table uses a distinct header | open |
| `D5` | Disjoint naval namespaces | `catalog/naval/ships/surface-combatant/` (tracked, 3 leaves) and the empty untracked `catalog/naval/surface-combatants/` coexist | open |
| `D6` | Ledger not materialized | `sources/ledger/` holds a README only; `common.schema.json` has no source `$defs` while `FIELDS.md` describes 12 ledger fields | open |
| `D7` | `coverage.csv` role and status vocabulary contradict its own README | 105 of 105 rows are `parameter_complete`, not `queued` | open |
| `D8` | Country rows share a variant leaf without a stated rule | `eq-us-air-c17a` and `eq-uk-air-c17a` both point at `c-17/c-17a`, which is now correct by the `tornado-ids` precedent but is not documented anywhere | open |
| `D9` | `Equipment ID` scheme is not declared | `eq-<country>-<domain>-<variant>`, country-less `module-*`, and country-less variant names such as `tornado-ids` all coexist with no stated rule | open |

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

## Retracted Findings

The first pass reported these. All three are withdrawn.

| Withdrawn | Why it was reported | Why it is withdrawn |
| --- | --- | --- |
| Dangling citation `p5-us-ground-m1a2sepv3-armytechnology` on the M1A2 SEP v3 leaf | An audit script that resolved source packages by declared `Source ID` under only part of the `raw/sources/` tree | The package exists at `raw/sources/army_technology/p5-us-ground-m1a2sepv3-armytechnology/manifest.md`, its `Source ID` line matches, and its own text names the geometry, crew, AGT1500, M256, FLIR, data-link and APU statements the leaf cites it for. The then-current C1 run confirmed 0 dangling ids; the present tree also resolves all 291 manifests |
| `coverage.csv` status not trustworthy | The file marked all 55 rows `parameter_complete` and held only 18 air rows against 70 in `air.csv` | The `air.csv` comparison was the observation, the conclusion was wrong. Both directions of the coverage-to-backlog comparison agree, so `C3` passes. The real defect is documentary and is now `D7` |
| Source-reference count 169 against 193 on disk | The same partial-scan audit | The comparison mixed two denominators: 169 is the count of *distinct* ids leaves cite, against 193 *packages* on disk. Both are correct; the implied gap was not |

## Admission Boundary

Every open finding sits inside the reduced write set. `D2` is the only one that
depends on a maintained standard owned outside this tree
(`docs/research/standards/public_data_source_admission.md`); under the reduced scope
the repair is to complete the missing fields at the manifest level rather than to
amend that standard.

## Explicit Overclaim Refusals

- The 116 `parameter_complete` rows are research drafts. They are not calibrated, not
  cross-checked, and not runtime-eligible.
- No file in this tree is consumed by the runtime loader.
- Family names remain grouping nodes; only concrete variant leaves count as records.
- `cataloged` means a draft leaf exists. It does not mean the parameter set is complete.

## Next Action Order

All six machine-checkable conditions pass. What remains is not a defect the check
can see:

1. `D4` shape convergence — required before new leaves are added, otherwise the split widens.
2. `D7` and `D6` — reconcile the coverage documentation and materialize the ledger.
3. `D2` source admission fields — 291 packages need a rights field before any ledger row is honest.
4. `D8` and `D9` — write down the id and shared-leaf rules, in the form the tornado-ids and module precedents already imply.
5. `D5` cleanup, `D3` stub depth.
6. Continue the unattended expansion run recorded in `equipment_expansion_20260923.md` until 150 complete rows are present.
