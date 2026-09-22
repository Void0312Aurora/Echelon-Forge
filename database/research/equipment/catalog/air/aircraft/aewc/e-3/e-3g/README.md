# E-3G Sentry

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/aewc/e-3/e-3g/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-23`
Equipment ID: `eq-us-air-e3g`
Content status: parameter table complete for the U.S. E-3G research record. Family airframe values are separated from official Block 40/45 mission-system and crew context.

## Identity

- Family: E-3
- Variant: E-3G
- Role: Airborne warning and control system
- Manufacturer: Boeing Aerospace Co. (airframe); mission system modernized under the Block 40/45 programme
- Configuration scope: E-3 airframe with the modernized mission system. The source publishes airframe figures at family level; no E-3G-specific geometry is claimed.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| United States Air Force | In service | `p5-us-air-e3sentry-usaf-factsheet` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Powerplant | Four Pratt & Whitney TF33-PW-100A turbofans | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Thrust | 20,500 lb each at sea level | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Rotodome | 30 ft (9.1 m) diameter, 6 ft (1.8 m) thick, mounted 11 ft (3.33 m) above the fuselage | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Wingspan | 145 ft 9 in (44.4 m) | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Length | 152 ft 11 in (46.6 m) | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Height | 41 ft 9 in (13 m) | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Weight (zero fuel) | 205,000 lb (92,986 kg) | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Maximum takeoff weight | 325,000 lb (147,418 kg) per the Air Force fact sheet; 347,000 lb (156,150 kg) per the Tinker Air Force Base page | `p5-us-air-e3sentry-usaf-factsheet`; `p5-us-air-e3sentry-tinker` | A | Two official Air Force publications disagree by 22,000 lb. Both values are recorded and neither is averaged or preferred; the field is not settled |
| Optimum cruise speed | 360 mph (Mach 0.48) | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Ceiling | Above 29,000 ft (8,788 m) | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Endurance | More than 8 hours unrefuelled | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Crew | Flight crew of four plus 13 to 19 mission specialists, varying with mission | `p5-us-air-e3sentry-usaf-factsheet` | A |
| Date deployed | March 1977 | `p5-us-air-e3sentry-usaf-factsheet` | A |
| E-3G mission crew context | Up to 24 weapons officers, surveillance officers, radar/communications technicians and flight-deck crew on a mission | `p5-us-air-e3g-block4045-af` | A |
| Block 40/45 mission system | Upgraded computer platform for weapons and surveillance scopes; faster tracking, configurable airspaces and improved command-and-control workflow | `p5-us-air-e3g-block4045-af` | A |
| E-3G operational surveillance context | Exercise surveillance of aircraft in a 300-mile radius; command-and-control and air-battle-management role | `p5-us-air-e3g-block4045-af` | A |

## Configuration Boundary

The airframe, powerplant and performance rows rest on the Air Force E-3 Sentry fact sheet and remain family-level. The separate official E-3G Block 40/45 package supplies the variant-specific mission-system, crew-context and operational-surveillance rows. No universal radar range, datalink throughput or weapon loadout is inferred from the exercise context.

Maximum takeoff weight is stated differently by two official Air Force publications: 325,000 lb on the fact sheet and 347,000 lb on the Tinker Air Force Base page. Both are recorded and the divergence is left open rather than averaged.

The `p5-us-air-e3g-usaf` source is a news tag page for the E-3. It carries no specification table at all and is retained only as service-presence context; it is not the origin of any parameter row. Earlier revisions of this leaf cited it as the parameter source, which was a provenance error now corrected.

## Source References

- `p5-us-air-e3sentry-usaf-factsheet`: `raw/sources/us_air_force/p5-us-air-e3sentry-usaf-factsheet/manifest.md`
- `p5-us-air-e3sentry-tinker`: `raw/sources/tinker_air_force_base/p5-us-air-e3sentry-tinker/manifest.md`
- `p5-us-air-e3g-block4045-af`: `raw/sources/us_air_force/p5-us-air-e3g-block4045-af/manifest.md` — official Block 40/45 mission-system and E-3G operational context
- `p5-us-air-e3g-usaf`: `raw/sources/us_air_force/p5-us-air-e3g-usaf/manifest.md` — context only, no parameter rows
