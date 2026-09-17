# M1132 Engineer Squad Vehicle

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/stryker/m1132-esv/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-stryker-m1132-esv` |
| Family / variant | Stryker / M1132 ESV |
| Hull context | Engineer squad configuration |
| Role | Mobility and limited countermobility support |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Listed configuration mass | 16.5 t | `p5-us-ground-stryker-usace-dims` | A | Source table configuration; attachments change mass |
| Length × width × height | 7.59 × 2.87 × 2.69 m | `p5-us-ground-stryker-usace-dims` | A | Engineer attachment envelope |
| Crew / payload | 11 total personnel | `p5-us-ground-stryker-pm-atlss` | A | Army programme page total; crew/squad split and attachment load remain unnormalized |
| Mission systems | Obstacle neutralization, lane marking, and mine-detection equipment | `p5-us-ground-stryker-pm-atlss` | A | Attachment models and performance unknown |
| Armament | Remote weapon station context | `p5-us-ground-stryker-pm-atlss` | A | Exact station fit unknown |
| Armament (detailed) | .50 cal M2HB or 40 mm Mk 19 MOD3 on the M151E2 remote weapon system; 2,000 or 480 rounds; 60 deg/s electric traverse | `p5-us-ground-stryker-m1132esv-afvdatabase` | C | Resolves the station fit left open above |
| Engine designation | Caterpillar 3126, six-cylinder four-cycle inline turbocharged diesel, 350 hp at 2,500 rpm | `p5-us-ground-stryker-m1132esv-afvdatabase` | C | Secondary-sourced designation; the A1 450 hp rating is not merged |
| Transmission | Allison MD 3066P, six forward and one reverse | `p5-us-ground-stryker-m1132esv-afvdatabase` | C | Secondary source; shift schedule and torque curve not public |
| Fuel capacity | 53 gal (200 L) | `p5-us-ground-stryker-m1132esv-afvdatabase` | C | Secondary source; usable reserve fraction not stated |
| Combat weight | 41,790 lb (18,956 kg) | `p5-us-ground-stryker-m1132esv-afvdatabase` | C | Secondary combat-mass figure. Distinct from the 16.5 t listed configuration mass above, which excludes engineer attachments |
| Combat dimensions | 298.5 × 153.6 × 125.1 in (7.582 × 3.901 × 3.178 m) | `p5-us-ground-stryker-family-gdlsbrochure` | B | GDLS manufacturer combat envelope for the Engineer Squad Vehicle. This supersedes the earlier `287.9 in` length, which is the shipping length, not the combat length |
| Shipping dimensions | 287.9 × 112.0 × 105.7 in (7.313 × 2.845 × 2.685 m) | `p5-us-ground-stryker-family-gdlsbrochure` | B | GDLS shipping envelope. The 287.9 in length belongs to this configuration only; do not combine it with the combat width or height above |
| Secondary dimensions (Tier C) | 287.9 × 153.6 × 125.1 in | `p5-us-ground-stryker-m1132esv-afvdatabase` | C | Source conflict, retained rather than deleted. The Tier C compilation gives 287.9 in as a combat length, which reproduces GDLS's shipping length. GDLS is the manufacturer and takes precedence for the combat envelope |
| Maximum level road speed | 60 mph (96 km/h) | `p5-us-ground-stryker-m1132esv-afvdatabase` | C | Variant-level road figure; off-road speed not published |
| Road range | approximately 330 mi (530 km) on roads | `p5-us-ground-stryker-m1132esv-afvdatabase` | C | Explicitly a road figure; cross-country range not published |
| Trench / vertical obstacle | 76 in (190 cm) / 23 in (58 cm) | `p5-us-ground-stryker-m1132esv-afvdatabase` | C | Trench figure is below the ICV value and is retained as variant-specific |
| Fording depth | 51 in (130 cm) | `p5-us-ground-stryker-m1132esv-afvdatabase` | C | Fording, not swimming; preparation requirements not stated |
| Grade / sideslope | 60% / 30% | `p5-us-ground-stryker-m1132esv-afvdatabase` | C | Slope limits as published; load-dependent in practice |
| Minimum turning diameter | 52 ft (16 m) | `p5-us-ground-stryker-m1132esv-afvdatabase` | C | Four-wheel steering geometry; measurement convention not stated |
| Crew (conflicting sources) | 11 total per the retained Army programme page; 8-10 (commander, driver, six to eight engineers) per the Tier C compilation | `p5-us-ground-stryker-pm-atlss`; `p5-us-ground-stryker-m1132esv-afvdatabase` | A/C | Source conflict, unresolved. The two totals cannot both be right, and the 11-person figure is not a split of the 8-10 figure. Per `evidence_precedence_stryker.md` the rank-1 Army programme page carries the higher weight, but neither figure is treated as settled. An Army source naming the M1132 crew explicitly, such as the ODIN asset page, would close this |
| Mission systems (detailed) | Jettison Fitting Kit forward for mine rollers, plows and obstacle blades controlled by the MECU; side-mounted Lane Marking System with two dispensers of 50 poles each at 100 psi | `p5-us-ground-stryker-m1132esv-afvdatabase` | C | Names the engineer attachments the row above describes generically |
| Public protection | Armored Stryker hull; exact thickness/level unknown | `p5-us-ground-stryker-army-wsh-2020` | A | Qualitative only |
| Hull armor maximum | welded high-hard steel structure, maximum 0.5 in (1.3 cm) | `p5-us-ground-stryker-m1132esv-afvdatabase`; `p5-us-ground-stryker-family-gao03671` | C | Single maximum plate figure from a secondary source. It is not a protection rating, not an all-round value, and not an RHAe equivalence. GAO describes Stryker protection as capability against defined threats across defined arcs, which is a different kind of claim from a plate thickness |

Field confidence follows the evidence tier and context column: direct variant statements are high confidence; attachment-sensitive statements are medium confidence; `unknown` fields remain unestimated.

## Configuration Boundary

The GDLS brochure gives this variant two distinct envelopes and both are retained above: combat is `298.5 × 153.6 × 125.1 in`, shipping is `287.9 × 112.0 × 105.7 in`. No value is carried across the two columns.

Rows carried from `p5-us-ground-stryker-m1132esv-afvdatabase` describe the engineer squad configuration. The source records the 2010 double-V hull and the separate Stryker A1 upgrade (450 hp, 60,000 lb suspension, 910 A alternator, in-vehicle network) as distinct configurations; neither is merged into this record.

## Source References

- `p5-us-ground-stryker-usace-dims`
- `p5-us-ground-stryker-pm-atlss`
- `p5-us-ground-stryker-army-wsh-2020`
- `p5-us-ground-stryker-m1132esv-afvdatabase`
- `p5-us-ground-stryker-family-gdlsbrochure`
- `p5-us-ground-stryker-family-odin`
