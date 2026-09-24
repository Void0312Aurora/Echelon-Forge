# U.S. Army TM 9-2320-365-10 — FMTV M1078/M1081 CTIS operator data

Source ID: `p5-us-ground-fmtv-m1078-ctis-tm9232036510`
Tier: `A`
Publisher: U.S. Department of the Army
Author / maintainer: Headquarters, Department of the Army
Title: TM 9-2320-365-10, Operator's Manual for M1078 Series 2-1/2-Ton 4x4 Light Medium Tactical Vehicles (LMTV)
URL: https://trucks25tonv1-2.tpub.com/TM-9-2320-365-10/css/TM-9-2320-365-10_262.htm
Accessed: 2026-09-14
Domain: ground
Equipment: FMTV/LMTV M1078/M1081 CTIS
Configuration boundary: M1078/M1081 2-1/2-ton 4x4 LMTV operator configuration and its CTIS ECU; M1079 van, M1083-series 5-ton MTV, later FMTV upgrades, and customer tire/load packages are not silently merged.
Availability/status: Public tpub mirror; CTIS control, normal-operation, pressure/restriction, emergency, run-flat, reset, and troubleshooting pages were reachable at access. The mirror is not an Army-hosted publication portal.
Estimation / uncertainty: Direct table values are 55 psi highway, 33 psi cross-country, 20 psi sand, and 14 psi emergency; speed limits are 55/40/12/5 mph and emergency/run-flat operation is ten minutes. The 74-psi automatic shutoff, two-minute overspeed upshift, 15-second run-flat check, and five-light reset behavior are direct for this manual. ECU protocol, pressure tolerance, compressor flow, axle split, and wheel-end seal topology remain unknown; use only as cross-vehicle bounds outside M1078/M1081.
Retention: manifest and extracted parameter notes only
Rights status: not_recorded
Provenance status: manifest+retention
Residual status: open

## Use

The manual identifies an ECU with HWY, X-C, SAND, EMER, and RUN FLAT buttons/indicators. A flashing mode light means pressure is changing; steady means the target is reached. CTIS shuts off when system air is below 74 psi or a malfunction occurs. In RUN FLAT, the ECU checks tire pressure every 15 seconds and feeds wet-tank air to a leaking tire; after ten minutes the mode must be deliberately reselected or CTIS shuts down. Persistent five-light faults require reset/maintenance rather than silent continuation.
