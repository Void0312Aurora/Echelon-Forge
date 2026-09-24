# M1252 Mortar Carrier Vehicle, Variant (MCVV)

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/stryker/m1252-mcvv/README.md`
Owner: `database/equipment-data`
Content status: extracted DVH simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-stryker-m1252-mcvv` |
| Family / variant | Stryker / M1252 MCVV |
| Hull context | Double-V Hull (DVH); do not merge with M1129 or M1252A1 |
| Role | 120 mm mounted mortar carrier |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Operational configuration mass | 53,602 lb (≈24,313 kg) | `p5-us-ground-stryker-army-tb55-2023` | A | TB 55-46-1 operational configuration; not GVW/GVWR and not reduced transport mass |
| Operational dimensions | 288 × 146 × 125 in (≈7.315 × 3.708 × 3.175 m) | `p5-us-ground-stryker-army-tb55-2023` | A | Operational configuration; width/height include the cited configuration |
| Reduced transport configuration mass | 52,015 lb (≈23,594 kg) | `p5-us-ground-stryker-army-tb55-2023` | A | Reduced transport configuration; do not label as operational mass |
| Reduced transport dimensions | 286 × 122 × 108 in (≈7.264 × 3.099 × 2.743 m) | `p5-us-ground-stryker-army-tb55-2023` | A | Reduced transport configuration |
| GVW | 48,591 lb (≈22,041 kg) | `p5-us-ground-stryker-tradoc-gta09-14-002` | A | TRADOC GTA configuration field; not the 53,602 lb operational configuration |
| GVWR | 58,401 lb (≈26,490 kg) | `p5-us-ground-stryker-tradoc-gta09-14-002` | A | TRADOC GTA rated limit; not an observed operating mass |
| Crew | 5 | `p5-us-ground-mortar-atp-3-21-90` | A | Mortar-carrier configuration |
| Mortar system | RMS6-L 120 mm mortar | `p5-us-ground-mortar-atp-3-21-90` | A | Exact ammunition load and fire-control fit unknown |
| Mortar system HE range | Approximately 200–6,570 m | `p5-usmc-ground-m1252-rms6l-mctp301d` | A | MCTP table explicitly names the M1252 MCVV RMS6-L; range varies by round, altitude difference and meteorological conditions and is not vehicle operational range |
| Community configuration corroboration | Crew 2+3; WarWheels identifies the DVH vehicle as M1252 MCVV and separates the later M1252 MCVV-A1 ECP | `p5-us-ground-stryker-m1252mcvv-warwheels` | C | Corroboration only; no propulsion, speed, range, mass or dimensional value is taken from this page |
| Legacy DVH family powerpack baseline | 350 hp Caterpillar C7; the DVH A1 ECP replaces this legacy baseline with a 450 hp Caterpillar C9 | `p5-us-module-stryker-c7-dote` | A | Family upgrade boundary only; not a M1252-specific engine certification and not used to fill the M1252 propulsion field |
| Propulsion / mobility | Unknown for this M1252 configuration | — | — | Do not copy M1126 350 hp, speed or range baseline |
| Source coverage (propulsion) | Searched and not found at M1252 evidence level | `p5-us-ground-stryker-m1252mcvv-afvdatabase` | C | AFV Database covers the Stryker family and links the M1129 mortar carrier and M1200 Armored Knight but carries no M1252 MCVV specification page. The field stays `Unknown` rather than taking the M1129 MC-B 350 hp figure, because the M1252 is 20 percent heavier than the 41,367 lb MC-B and the source does not assert that the powerpack is unchanged |
| Community family mobility baseline (not M1252 parameter) | Caterpillar C7, approximately 350 hp; approximately 100 km/h; approximately 500 km family reference | `p5-us-ground-stryker-family-ijeat-survey` | C | IJEAT names M1252 among DVH variants but presents these figures as generic IAV/Stryker values; retained as bounded context only and not copied into the M1252 propulsion/mobility field |
| Source coverage (brochure) | Also absent from the GDLS brochure | `p5-us-ground-stryker-family-gdlsbrochure` | B | The manufacturer brochure states combat and shipping envelopes for ten Stryker variants and does not include the M1252 MCVV. Two independent sources were therefore searched without locating this variant, which is recorded so the gap is not mistaken for an unexamined field |
| Source coverage (community PMCS mirror) | M1252 MCVV entry absent | `p5-us-ground-stryker-m1252-armyadp-pmcs` | C | ArmyADP exposes an M1126/M1127 checklist tied to TM 9-2355-311-10, not the M1252/TM 9-2355-364-10 set; no M1252 mobility value is extracted |
| Public protection | DVH Stryker hull; exact armor/protection rating unknown | `p5-us-ground-stryker-mdex-2026` | A | Configuration family only |

Field confidence follows the evidence tier and context column: TB 55-46-1 measurements are high confidence for their named configurations; family-level protection context is medium confidence; unknown fields remain unestimated.

## Configuration Boundary

The TB 55-46-1 values above are intentionally kept as separate fields. In particular, `53,602 lb / 288 × 146 × 125 in` is the operational configuration, while `52,015 lb / 286 × 122 × 108 in` is the reduced transport configuration. Neither value is silently substituted for GVW or GVWR.

The DOT&E package records the common DVH-to-DVH-A1 power boundary: the legacy family used a 350 hp Caterpillar C7 baseline and the A1 ECP replaces it with a 450 hp Caterpillar C9. That statement does not identify the M1252's engine serial, installation, torque curve, speed or range, so it remains a family reference rather than a filled M1252 value.

## Open Gap

This leaf has the most unresolved target fields of the eleven Stryker variant records. A variant-level M1252 or MCVV propulsion, speed and range source was searched for and not located; the AFV Database family coverage stops short of this variant. The four-volume operator manual set (TM 9-2355-364-10-1 through -4, dated 2016-09-30) is identified in public catalogue/search results, but its parameter-bearing text was not returned in this pass. The DOT&E family power boundary is retained as context, but closing this gap still needs a source that names the M1252 or MCVV configuration directly, not a family baseline substitution.

## Source References

- `p5-us-ground-stryker-army-tb55-2023`
- `p5-us-ground-mortar-atp-3-21-90`
- `p5-usmc-ground-m1252-rms6l-mctp301d`
- `p5-us-ground-stryker-mdex-2026`
- `p5-us-ground-stryker-m1252mcvv-afvdatabase`
- `p5-us-ground-stryker-family-gdlsbrochure`
- `p5-us-module-stryker-c7-dote`
- `p5-us-ground-stryker-m1252mcvv-warwheels`
- `p5-us-ground-stryker-m1252-armyadp-pmcs`
- `p5-us-ground-stryker-family-ijeat-survey`
