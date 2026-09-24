# U.S. Army TM 9-2320-272-10 — M939A2 CTIS operator data

Source ID: `p5-us-ground-m939-ctis-tm92320272`
Tier: `A`
Publisher: U.S. Department of the Army
Author / maintainer: Headquarters, Department of the Army
Title: TM 9-2320-272-10, Operator's Manual for Truck, 5-Ton, 6x6, M939, M939A1, and M939A2 Series Trucks (Diesel)
URL: https://trucks5tonops.tpub.com/TM-9-2320-272-10/css/TM-9-2320-272-10_80.htm
Accessed: 2026-09-14
Domain: ground
Equipment: M939A2-series trucks with CTIS
Configuration boundary: M939A2 CTIS-equipped configurations covered by the operator manual; M939/M939A1 non-CTIS variants and the M936A2 wrecker's 80-psi highway exception are not merged into the shared baseline.
Availability/status: Public mirror; the CTIS architecture (page 1-72), operating modes (page 2-202), and CTIS indications/malfunctions (page 3-21) HTML extracts were reachable at access. The mirror is not an Army-hosted publication portal.
Estimation / uncertainty: The M939A2 preset values (60 psi highway, 35 psi cross-country, 25 psi mud/sand/snow, 12 psi emergency) and mode/speed behavior are direct for the named configuration. Inflation rate, sensor tolerance, leak threshold, ECU electrical protocol, and wheel-end seal details are not published in these extracts. Any interval in the module README is an explicit cross-vehicle simulation bound, not a value for all M939 variants.
Retention: manifest and extracted parameter notes only
Retrieval:
  status: not_recorded
  method: not_recorded
  returned: not_recorded
  did_not_return: not_recorded
Rights status: not_recorded
Provenance status: manifest+retention
Residual status: open

## Use

The manual identifies CTIS as an automatic system that changes tire pressure after a road-surface selection, with a pneumatic controller, ECU selector, 85-psi air-pressure protection switch, air dryer/filter, exhaust valves, wheel valves, and a speed signal generator. It states that the same compressor supplies the brake system and CTIS, with brake operation taking priority. The operator troubleshooting table distinguishes stable, changing, interrupted-between-settings, leak/possible tire damage, and major-fault indications and permits RUN FLAT, reset, or CTIS disable according to the fault state.
