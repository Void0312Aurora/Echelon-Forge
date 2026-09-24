# U.S. Army TM 9-2320-272-24-1 — M939A2 CTIS maintenance architecture

Source ID: `p5-us-ground-m939-ctis-tm9232027241`
Tier: `A`
Publisher: U.S. Department of the Army
Author / maintainer: Headquarters, Department of the Army
Title: TM 9-2320-272-24-1, Unit, Direct Support, and General Support Maintenance Manual, M939/M939A1/M939A2 Series Trucks, Volume 1 of 4
URL: https://www.nsndepot.com/Library/TM/TM-9-2320-272-24-1?PageNumber=88
Accessed: 2026-09-14
Domain: ground
Equipment: M939A2 central tire inflation system
Configuration boundary: M939A2 maintenance description of the CTIS pneumatic controller, wheel valves, pressure sensing, and air-brake integration; older M939/M939A1 systems and other 4x4/8x8 chassis are outside this leaf.
Availability/status: Public NSN Depot mirror; page 88 (manual page 1-78) returned the CTIS operation text at access. It is a mirror of an Army technical manual, not a live vehicle-support or parts-availability statement.
Estimation / uncertainty: The named components and six-wheel/three-quick-exhaust topology are direct for the M939A2 6x6 description. The source's printed metric conversion beside the 85-psi protection threshold is internally inconsistent; the module retains the source's psi value and does not reuse the suspect conversion. Connector pinouts, seal dimensions, flow coefficients, and variant-specific valve counts remain unknown.
Retention: manifest and extracted parameter notes only
Rights status: not_recorded
Provenance status: manifest+retention
Residual status: open

## Use

The maintenance manual describes clean, dry compressed air entering the air dryer, wet tank, and CTIS branch; an air-pressure switch protects the brake supply; an ECU receives pressure-switch, pressure-transducer, and speed-generator inputs; a pneumatic controller operates inflation/deflation through quick-exhaust valves; and wheel valves isolate tire pressure during normal operation or wheel removal. These relationships support the module's interface and fail-safe notes without implying a universal wheel count.
