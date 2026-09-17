# Caterpillar C7 — Stryker engine module

Language: English canonical. Chinese companion: not established.
Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/module/engine/caterpillar-c7/README.md`
Record type: `module / engine`
Owner: `database/equipment-data`
Last verified: `2026-09-14`
Equipment ID: `module-stryker-caterpillar-c7`
Content status: parameter-first research record; not runtime authority.

## Identity and configuration boundary

- Module: Caterpillar C7 (7.2 L, inline-six, four-stroke turbocharged/aftercooled diesel).
- Intended use: legacy Stryker powerpack context (M1126/M1127/M1128/M1129/M1133/M1134/M1135 and related C7-era installations).
- Excluded: Stryker A1 / DVH-A1 450 hp Caterpillar C9 powerpack, the earlier 3126-only baseline, and generic non-Stryker C7 ratings unless explicitly labelled as a cross-check.
- The public sources do not expose a Stryker engine serial, military rating sheet, installed cooling-pack capacity, or installed powerpack mass. Those remain unresolved rather than silently inherited from the vehicle record.

## Parameters

| Field | Value | P5 source ID(s) | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| **Power** | **350 hp (261 kW)** Stryker C7 powerplant claim; **2,400 rpm** is the matching Cat C7 350-hp reference rating | `p5-us-module-stryker-c7-dieselarmy`; `p5-us-module-stryker-c7-dote`; `p5-us-module-caterpillar-c7-rv` | C / A / C | 350 hp is stated for the C7-era Stryker and independently bounded by the official DOT&E statement that the old Stryker C7 was replaced by a 450 hp C9. The 2,400 rpm governor point comes from the Caterpillar RV sheet, not a Stryker-specific technical manual. |
| **Torque** | **1,028 lb-ft (1,394 N·m)** reported for the Stryker C7; retain a **bounded 860–1,028 lb-ft (1,166–1,394 N·m)** envelope pending the Stryker engine serial/TM | `p5-us-module-stryker-c7-dieselarmy`; `p5-us-module-caterpillar-c7-rv` | C / C | Diesel Army gives 1,028 lb-ft but no test sheet or rpm. Caterpillar's 350-hp RV C7 sheet gives 860 lb-ft at 1,440 rpm. Do not collapse these different application ratings into one unqualified torque curve; use 1,028 lb-ft only as the Stryker-specific working point and keep the range for sensitivity tests. |
| **Fuel** | Diesel distillate, direct injection with **HEUI** (hydraulically actuated electronic unit injectors); Cat fuel transfer pump and priming pump | `p5-us-module-caterpillar-c7-cat`; `p5-us-module-caterpillar-c7-rv` | C / C | The C7 pages identify a diesel engine and HEUI system. Exact Stryker fuel grade, military fuel qualification, filtration restriction and fuel-rate curve are not public in the retained sources; do not assume a JP-8 calibration or a consumption value. |
| **Cooling** | Liquid-cooled jacket-water circuit with centrifugal water pump, thermostat housing and air-to-air aftercooler; **13.2 L (3.5 US gal)** engine-only coolant capacity on the Cat RV sheet | `p5-us-module-caterpillar-c7-cat`; `p5-us-module-caterpillar-c7-rv` | C / C | Direct engine-system values. The 13.2 L figure excludes the Stryker radiator, hoses, heater circuit and vehicle cooling pack; installed thermal capacity and fan-control map are unresolved. |
| **Mass** | **588 kg (1,295–1,296 lb) net dry engine, including flywheel / basic engine without optional attachments** | `p5-us-module-caterpillar-c7-rv`; `p5-us-module-caterpillar-c7-cat` | C / C | Direct Cat-published engine mass. It is not an installed Stryker powerpack mass: fan, alternator, starter, mounts, fluids, transmission adapter, exhaust and vehicle cooling hardware are outside the published figure. |
| **Interfaces** | SAE No. 1 or No. 2 flywheel housing; electronic SAE/ATA and SAE J1939 link with ADEM ECM; 12 V or 24 V starter options; HEUI fuel supply/return with transfer and priming pumps; jacket-water inlet/outlet, turbocharger/air-to-air aftercooler and dry exhaust; Stryker article pairs the C7 with Allison 3200SP six-speed automatic | `p5-us-module-caterpillar-c7-rv`; `p5-us-module-caterpillar-c7-cat`; `p5-us-module-stryker-c7-dieselarmy` | C / C / C | Engine-side interfaces are direct Cat data. Allison 3200SP is a Stryker-level pairing claim, not a substitute for a flange/ratio drawing. Exact Stryker harness pinout, engine mounts, cooling-pack connectors and transfer-case interface remain unknown. |

## Source references

- `p5-us-module-caterpillar-c7-cat`
- `p5-us-module-caterpillar-c7-rv`
- `p5-us-module-stryker-c7-dote`
- `p5-us-module-stryker-c7-dieselarmy`

## Remaining uncertainty

The C7 family is multi-rating and application-configurable. A Stryker-specific engine serial, military performance curve, fuel-rate map, cooling-pack design, installed module mass and harness/drive-line drawings are still required before dynamic calibration or runtime promotion. This leaf deliberately preserves the 860–1,028 lb-ft torque discrepancy and excludes the C9-powered A1 configuration.
