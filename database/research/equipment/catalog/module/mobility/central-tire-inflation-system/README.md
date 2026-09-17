# Central Tire Inflation System (CTIS)

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/module/mobility/central-tire-inflation-system/README.md`
Owner: `database/equipment-data`
Content status: bounded cross-vehicle mobility-module baseline; not a runtime record.

## Scope and configuration boundary

This leaf describes a pneumatic central tire inflation system (CTIS) for heavy or tactical wheeled vehicles. The baseline is anchored to the U.S. Army M939A2 5-ton 6x6 and FMTV M1078/M1081 2.5-ton 4x4 operator/maintenance manuals. It is a reusable module input, not a claim that every CTIS vehicle has the same preset pressures, wheel count, timer, or wheel-end hardware.

Included: compressor-fed inflation and exhaust, ECU-selected terrain presets, pressure feedback, speed protection, wheel isolation, leak/run-flat response, and shared compressed-air/brake integration. Excluded: tire-pressure-monitoring-only systems, physical run-flat inserts, civilian TPMS, and vehicle-specific tire/load tables not named by one of the cited configurations.

## Parameters

| Field | Baseline / bounded value | Source | Tier | Configuration / estimation metadata |
| --- | --- | --- | --- | --- |
| Pressure | Representative preset setpoints: **highway 55-60 psi (379-414 kPa)**; **cross-country 33-35 psi (228-241 kPa)**; **sand/mud/snow 20-25 psi (138-172 kPa)**; **emergency 12-14 psi (83-97 kPa)**. The FMTV table is 55/33/20/14 psi; the M939A2 table is 60/35/25/12 psi. FMTV emergency is limited to 5 mph (8 km/h) for 10 minutes; M939A2 emergency timing and speed are vehicle-specific and must not be copied from FMTV. | `p5-us-ground-m939-ctis-tm92320272`; `p5-us-ground-fmtv-m1078-ctis-tm9232036510` | A/A | Source values are direct for the named vehicle/tire configurations. The interval is an explicit cross-vehicle simulation bound, not a universal CTIS specification. Axle load, tire construction, temperature, and wrecker/cargo configuration can change setpoints; keep a per-vehicle table and preserve front/rear splits where the manual supplies them. |
| Control | Driver selects HWY/X-C/SAND(or soft terrain)/EMER on an ECU selector; mode indicators flash while pressure is changing and stay steady at the target. ECU commands a pneumatic controller/solenoids using pressure feedback and a vehicle-speed signal. M939A2 raises pressure to the next safer mode after sustained overspeed; FMTV flashes OVRSPD after 1 minute and automatically inflates to the next higher mode after 2 minutes. | `p5-us-ground-m939-ctis-tm92320272`; `p5-us-ground-fmtv-m1078-ctis-tm9232036510` | A/A | Selection, feedback, and speed-guard behavior are direct manual behavior. Mode names and the number of indicators vary by chassis. A simulation may use a finite-state mode controller and aggregate axle/wheel pressure, but ECU bus protocol, pressure tolerance, and inflation/deflation rate remain unestablished. |
| Failure behavior | Brake air has priority over CTIS: M939A2 stops inflation when reservoir pressure falls below its preset limit while allowing an in-progress deflation to continue. Leak/damage indications stop the system and request RUN FLAT, inspection, tire change, reset, or CTIS disable. FMTV shuts CTIS off below **74 psi (510 kPa)** system air pressure or on a malfunction; RUN FLAT checks every 15 seconds (normal interval 15 minutes) and supplies wet-tank air to a leaking tire. **On the FMTV**, RUN FLAT and EMER are time-limited to 10 minutes unless deliberately reselected; a persistent fault is handed to unit maintenance. | `p5-us-ground-m939-ctis-tm92320272`; `p5-us-ground-fmtv-m1078-ctis-tm9232036510` | A/A | Failure indications and timers are direct for M939A2/FMTV. The reusable baseline estimates a fail-safe state of `hold_last_pressure -> isolate leaking wheel -> alert -> disable CTIS`, but exact lamp codes, leak thresholds, and manual-inflate procedure are vehicle-specific. Do not model a pressure drop to zero merely because CTIS power is lost. |
| Interfaces | Pneumatic chain: engine compressor and wet tank/air dryer/filter -> air-pressure protection switch -> pneumatic controller -> exhaust/quick-exhaust valves -> wheel valves, rotary seals/hoses, and tire cavities. Control chain: ECU selector/indicators, pressure transducer, speed-signal generator, master power/circuit protection. The M939A2 6x6 maintenance manual names six wheel valves and three quick-exhaust valves and states that wheel valves isolate tire pressure during normal operation/removal; counts are not universal to 4x4/8x8 systems. | `p5-us-ground-m939-ctis-tm92320272`; `p5-us-ground-m939-ctis-tm9232027241`; `p5-us-ground-fmtv-m1078-ctis-tm9232036510` | A/A/A | Compressor/brake/ECU/valve/sensor relationships are manual-backed. Wheel-end seal geometry, hose routing, connector pinout, ECU protocol, and valve counts for other chassis are unknown. Preserve the distinction between the shared brake reservoir, CTIS pneumatic branch, electrical controls, and tire/wheel boundary. |

## Modeling guardrails

- Keep `configured_presets` as vehicle data. Never replace the four terrain modes with one nominal pressure.
- Apply mode speed and duration restrictions as safety gates, not as performance suggestions. The low-pressure emergency mode is a recovery state, not a normal travel state.
- Treat `RUN FLAT` as an active leak-management mode; it does not prove that the tire has a run-flat insert.
- Preserve brake-air priority and a non-destructive fail state. A lost ECU or major leak should produce an alert/maintenance state and retain the last physically plausible pressure until a tire/valve model changes it.
- Inflation/deflation time, compressor flow, sensor hysteresis/accuracy, rotary-seal leakage, pressure-by-load, and exact front/rear/axle splits remain open calibration fields.

All four target fields contain direct values for at least one named Army configuration plus an explicitly bounded cross-vehicle estimate. This module remains draft-only until the target vehicle's operator/maintenance manual supplies its own tire table, ECU behavior, and wheel-end topology.

## Source references

- `p5-us-ground-m939-ctis-tm92320272`
- `p5-us-ground-m939-ctis-tm9232027241`
- `p5-us-ground-fmtv-m1078-ctis-tm9232036510`
