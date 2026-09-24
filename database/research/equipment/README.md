# Global Equipment Research

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/README.md`
Owner: `database/equipment-data`
Last verified: `not established`
Content status: First research tranche. Coverage is intentionally incomplete; exact counts and variants must be verified source by source.

## Purpose

This research package establishes the source-first baseline for global in-service equipment collection. The five permanent members of the United Nations Security Council, China, France, Russia, the United Kingdom, and the United States, are the mandatory minimum baseline. They are not a scope ceiling.

The first tranche covers major P5 platforms and establishes the hierarchy for expanding to other countries and regions. It does not yet attempt to enumerate every global sub-variant, munition, sensor, electronic-warfare suite, or support vehicle.

## Simulation-Parameter Collection Profile

This profile is a research and extraction guide for simulation inputs. It is not a final schema, runtime contract, calibration set, or runtime data source.

- Collect a concrete variant and configuration (including FBH, DVH, or DVHA1 where relevant); family-level values are context only.
- Inventory, organizational tables, procurement totals, and in-service counts are optional metadata. They are not acceptance gates for a parameter record.
- Prefer field-level values for geometry, configuration-specific mass semantics, propulsion, mobility, crew and payload, armament, mission systems, and publicly stated protection.
- Preserve the source's meaning and units for `curb`, `gross`, `combat`, `operational`, `transport`, `GVW`, and `GVWR`; do not collapse them into one mass value.
- Attach a source ID, evidence tier, configuration context, and uncertainty note to each material field. A source that describes a family does not automatically support every leaf variant.
- `unknown` or `not established` is an interim collection gap only. Before a leaf can reach `parameter_complete`, every declared target field must have a cited value or a bounded estimate; a family baseline must not be silently copied into a heavier, attachment-specific, or later configuration.
- When an official source does not publish a field, use a traceable professional, museum, archival, specialist-community, or other reputable secondary source. Mark the field as secondary or estimated, preserve the source URL and date, and record the configuration and uncertainty. Do not present a secondary estimate as an official specification.
- Retain URLs and manifests rather than copying source documents. A collection leaf may be marked `cataloged` when its draft document exists, but it is not complete or runtime-eligible until `parameter_complete` and the relevant cross-check are recorded.

## Geographic Coverage

- Mandatory baseline: China, France, Russia, the United Kingdom, and the United States.
- Expansion regions: NATO Europe, non-NATO Europe, the Middle East, South Asia, East Asia, Southeast Asia, Africa, Latin America, and Oceania.
- Additional countries use operator files and country indexes; canonical equipment records are not duplicated by country.
- Regional coverage is an index concern, not a replacement for country ownership.

## Evidence Rules

- `A`: first-party government or official service publication. Strong for the facts that source owns and states.
- `B`: government assessment, professional defence reference, or peer-reviewed analysis. Strong as an assessment, not as first-party ground truth.
- `C`: traceable vendor, research organization, reputable secondary source, or specialist community source with an identifiable page, author/maintainer, date, and reproducible value. Used when an A/B source is unavailable; estimates must be labelled.
- `D`: unverified or unverifiable. Excluded from the inventory.
- Exact counts are not inferred from a type-name mention. A row may establish service presence at high confidence while leaving count confidence unestablished.
- Foreign-government assessments are marked as assessments, not as neutral inventory facts.

## Field-level Evidence Roles

Each populated parameter row must make its evidence role visible; a row-level
`parameter_complete` status does not turn every value into direct variant truth.

- `direct_variant`: the cited source names the concrete variant or configuration
  and states the field for that scope.
- `family_context`: the source supports a family or module boundary only. Keep it
  as context unless the leaf explicitly says why the scope is applicable.
- `bounded_estimate`: the value is an explicitly labelled range or estimate whose
  source scope is narrower than the leaf claim. Preserve the source tier,
  configuration boundary, uncertainty, and replacement rule in the row note.
- `open`: a search or cross-check residual. It belongs in the notes or blocker
  ledger, not as an unqualified value in a `parameter_complete` field.

Community and other Tier C material may supply `family_context` or
`bounded_estimate` in this research package. It must retain a stable URL or
other source reference, source tier, configuration scope, reasonableness note,
and non-authoritative status. It must not be silently promoted to a direct
variant value or runtime authority. Raw HTML is not retained; manifests keep
the locator and a short extracted boundary instead.

The canonical parameter-table forms are the existing `Parameter | Value |
Source | Confidence` and `Field | Value | Source | Tier | Configuration /
uncertainty` variants. New leaves should use the latter; existing leaves may be
migrated in bounded batches rather than rewritten only for formatting.

## Record Granularity

- Series and family names are grouping nodes only. Examples such as F-15, Rafale, Su-35, Type 055, and M1 are not valid final equipment records by themselves.
- A final record is a concrete model, variant, block, standard, operator, and dated service state where the evidence supports it.
- Parameters belong to the leaf record, not to the family row.
- Raw source packages are organized under [raw/sources/](raw/README.md) by publisher and source ID.
- Candidate coverage and processing state are tracked in [backlog/](backlog/README.md).
- Broad current and Cold-War discovery candidates are tracked in the [coverage plan](coverage/README.md) before they enter a domain backlog.

## Identity and Shared-Leaf Rules

- Country-owned equipment leaves use `eq-<country>-<domain>-<variant>`.
- Reusable modules use `module-<domain>-<module>` and are referenced as shared
  research inputs; they are not implicit runtime inheritance.
- A concrete variant leaf may serve multiple operator rows when the evidence
  supports the same variant boundary. Each backlog row keeps its own
  country/operator `equipment_id`, while the leaf carries an explicit operator
  table or scope note. Sharing a leaf does not merge operator-specific
  loadouts, certification, or service-state claims.
- A country-less `eq-*` ID is allowed only for an explicitly multinational or
  family-level research record, and its scope must be stated in the leaf. It
  must not be used to hide an unresolved country or variant boundary.
- Parent family/index pages and module pages are not equipment leaves unless
  they carry a concrete `Equipment ID` and a parameter table.

## Coverage Matrix

### United States

| Domain | Current first-tranche coverage | Evidence | Confidence |
| --- | --- | --- | --- |
| Air combat | F-22A, F-35A/B/C, F-15 family, F-16 family, F/A-18E/F, EA-18G | USAF fact sheets; US Navy fact files | Type coverage A; exact current counts not consolidated |
| Bombers | B-1B, B-2A, B-52H | USAF/AFLCMC public material | Type coverage A; B-21 remains a future system, not current inventory |
| Mobility, tanker, AEW | C-5M, C-17, C-130, KC-135, KC-46A, E-3 | USAF and AMC fact sheets | Type coverage A; platform-level transition status needs follow-up |
| Naval | CVN carriers, DDG-51, DDG-1000, SSN/SSBN, amphibious ships, logistics ships | US Navy and MSC inventories | Type coverage A; count-by-class pending |
| Land | M1 Abrams, Bradley, Stryker, HIMARS, M109, Patriot, THAAD | Service/public fact sheets | Type coverage A; current inventory and variants pending |
| Unmanned | MQ-9 family, tactical UAS | USAF/Marine Corps publications | Partial A; broad UAS inventory pending |

### United Kingdom

| Domain | Current first-tranche coverage | Evidence | Confidence |
| --- | --- | --- | --- |
| Maritime | 9 submarines: 4 ballistic nuclear and 5 nuclear attack submarines; 57 Royal Navy surface vessels and 13 RFA vessels | UK MoD 2025 accredited statistics | A |
| Land | 3,955 combat-equipment pieces: 997 APCs, 1,903 protected-mobility vehicles, 1,055 AFVs; 236 artillery vehicles; 274 combat-engineering pieces | UK MoD 2025 accredited statistics | A |
| Air | 504 fixed-wing platforms, 276 rotary-wing platforms, 180 uncrewed aircraft systems at 1 April 2025 | UK MoD 2025 accredited statistics | A |
| Named air platforms | Typhoon: 129; Chinook: 50; Apache AH-64E intake continues | UK MoD 2025 accredited statistics | A |
| Principal families | Queen Elizabeth carriers, Type 45 destroyers, Astute submarines, F-35B, P-8A, A400M, C-17, Voyager, Wildcat, Merlin | UK MoD/public programme pages | A/B; complete class-by-class count pending |

### France

| Domain | Current first-tranche coverage | Evidence | Confidence |
| --- | --- | --- | --- |
| Naval | 69 combat/support vessels; 4 SSBNs; 4 SSNs; 1 aircraft carrier; 3 amphibious helicopter carriers; 15 first-rank destroyers; 6 surveillance frigates; 17 offshore patrol vessels; 8 minehunters | Ministry of the Armed Forces key figures | A (official source; full-table extraction pending) |
| Air | 184 combat aircraft: 112 Rafale, 50 Mirage 2000D, 22 Mirage 2000-5F | Ministry of the Armed Forces key figures | A (official source; full-table extraction pending) |
| Transport/tanker/AEW | C-130 family, CN235, A400M, C-135/KC-135, A330 Phénix, E-3F | Ministry of the Armed Forces key figures | A |
| Principal naval families | Charles de Gaulle carrier group, Triomphant SSBNs, Suffren/Rubis submarines, FREMM/Horizon/frigate families | Ministry of the Armed Forces public material | A/B; aggregation varies by source |
| Land | Leclerc, VBCI, Griffon, Jaguar, Caesar and support families | Ministry and programme sources | B; a consolidated count table is still pending |

### China

| Domain | Current first-tranche coverage | Evidence | Confidence |
| --- | --- | --- | --- |
| Air combat | J-20, J-16, J-10B/C, J-11 family | PRC Ministry of National Defense official releases | A for service presence; inventory counts not disclosed |
| Bomber/AEW/transport | H-6K, KJ-500, Y-20, YY-20A | PRC Ministry of National Defense official releases | A for service presence |
| Carriers | Liaoning, Shandong, Fujian | PRC Ministry of National Defense official releases | A |
| Principal surface combatants | Type 055, Type 052D, Type 054A | PRC Ministry of National Defense official releases | A |
| Submarines and support ships | Kilo, Type 039 family, replenishment ships and other support types | US DoD China Military Power Report 2025 | B; foreign assessment, counts require dating |
| Land equipment | Major armored, artillery, air-defence and support families | Not yet source-normalized | Coverage pending |

### Russia

| Domain | Current first-tranche coverage | Evidence | Confidence |
| --- | --- | --- | --- |
| Air combat | Su-30SM, Su-35S as principal fighters; Su-34 as principal bomber | Russian Ministry of Defence public statement | A for declared role; not a complete inventory |
| Strategic aviation | Tu-95MS and Tu-160M families | Russian Ministry of Defence and procurement reporting | B; current operational counts disputed |
| Naval | Borei SSBNs, Yasen SSNs, Project 22350/20380 surface combatants, Kilo/Improved Kilo submarines | Russian Ministry of Defence and IISS Military Balance 2025 | B; public A-level inventory enumeration is limited |
| Strategic/air defence | S-400 and related air-defence families | Official and professional defence sources | B; exact composition pending |
| Land | T-72B3, T-80BVM, T-90M, BMP-3, BTR-82A, artillery and support families | Russian MoD and IISS Military Balance | B/C; wartime losses and active counts require dated evidence |

## Source Ledger

| ID | Tier | Source | Date | Used for | Limits |
| --- | --- | --- | --- | --- | --- |
| S1 | A | UK Ministry of Defence, [UK armed forces equipment and formations 2025](https://www.gov.uk/government/statistics/uk-armed-forces-equipment-and-formations-2025/uk-armed-forces-equipment-and-formations-2025) | 2025 | UK counts and major equipment categories | Counts as at 1 April 2025 |
| S2 | A | French Ministry of the Armed Forces, [Defence key figures 2025](https://www.defense.gouv.fr/sites/default/files/ministere-armees/Chiffres_Cle%CC%81s_2025_UK.pdf) | 2025 | French maritime, air, transport and tanker counts | Official aggregate source; this tranche captured the official PDF search snippet and still needs full-table extraction |
| S3 | B | US Department of Defense, [Military and Security Developments Involving the PRC 2025](https://media.defense.gov/2025/Dec/23/2003849070/-1/-1/1/ANNUAL-REPORT-TO-CONGRESS-MILITARY-AND-SECURITY-DEVELOPMENTS-INVOLVING-THE-PEOPLES-REPUBLIC-OF-CHINA-2025.PDF) | 23 Dec 2025 | PRC submarine, aircraft, and force-development assessment | Foreign-government estimate |
| S4 | B | IISS, [The Military Balance 2025](https://www.iiss.org/publications/the-military-balance/2025/the-military-balance-2025) | Feb 2025 | Cross-country equipment baseline and Russia context | Professional assessment; authoritative but not first-party |
| S5 | A | US Air Force, [Aircraft Fact Sheets](https://www.af.mil/About-Us/Fact-Sheets/) | Accessed 2026-09-11 | US aircraft service presence and descriptions | Per-type data, not one consolidated inventory |
| S6 | A | US Navy, [Fact Files](https://www.navy.mil/Resources/Fact-Files/) | Accessed 2026-09-11 | US naval classes and descriptions | Per-class data; counts and status vary by page |
| S7 | A | PRC Ministry of National Defense, J-20, J-10C, carrier and Type 055 releases | 2022-2025 | PRC service-presence confirmation | Does not disclose full inventories or counts |
| S8 | A | Russian Ministry of Defence, [public statement on principal aircraft](https://eng.mil.ru/news/175302dd-98a6-4f5e-807d-f35ed935d174) | Accessed 2026-09-11 | Su-30SM, Su-35S and Su-34 declared roles | Propaganda and disclosure controls apply |
| S9 | A | Russian Ministry of Defence, [Navy](https://eng.mil.ru/en/structure/forces/navy.htm) | Accessed 2026-09-11 | Russian Navy structure and selected platforms | No consolidated inventory |
| S10 | A | US Marine Corps, [2025 Aviation Plan](https://media.defense.gov/2025/Mar/12/2003665702/-1/-1/1/2025-MARINE-CORPS-AVIATION-PLAN.PDF) | Jan/Mar 2025 | USMC aviation transition and inventory context | Service-specific |
| S11 | A | French Ministry of the Armed Forces, Rafale Marine and aircraft-carrier pages | Accessed 2026-09-11 | French carrier air wing and Rafale Marine | Platform pages, not inventory totals |

## Open Gaps

1. Russia and China do not publish complete current inventories comparable to UK accredited statistics.
2. Exact active, storage, and decommissioning status must be dated separately.
3. Munitions, sensors, electronic warfare, ground-based air defence, and support vehicles need dedicated tranches.
4. The United States needs service-by-service inventory normalization rather than reliance on individual fact sheets.
5. Export variants, upgrade blocks, and prototype/non-service systems must not be merged into the same counting rule without an explicit marker.
6. Every row must eventually receive per-field confidence and source coverage, not only row-level confidence.

## Next Research Tranches

1. Replace every family row with concrete variant/block leaves.
2. US: Air Force, Navy, Marine Corps, and Army inventory normalization.
3. UK: full equipment-table extraction and named platform mapping.
4. France: full key-figures extraction plus major land and naval programmes.
5. China: separate official-confirmed service presence from foreign-assessment counts.
6. Russia: separate peacetime inventory claims, wartime losses, modernization plans, and active service evidence.
