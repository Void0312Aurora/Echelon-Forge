# M1135 Nuclear, Biological, and Chemical Reconnaissance Vehicle

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/stryker/m1135-nbcrv/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-stryker-m1135-nbcrv` |
| Family / variant | Stryker / M1135 NBCRV |
| Hull context | Nuclear, biological, and chemical reconnaissance configuration |
| Role | CBRN detection, warning, and reconnaissance |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Listed configuration mass | 17.3 t | `p5-us-ground-stryker-usace-dims` | A | Source table configuration |
| Length × width × height | 7.57 × 2.82 × 2.62 m | `p5-us-ground-stryker-usace-dims` | A | Sensor/mission fit context |
| Crew / payload | 4 (commander, driver, surveyor, assistant surveyor) | `p5-us-ground-stryker-m1135nbcrv-afvdatabase` | C | Secondary source resolves the crew count left unknown above; surveyor seating is mission-specific |
| Armament | M2 .50 cal remote weapon station and M6 smoke launchers | `p5-us-ground-stryker-army-nbcrv-2006` | A | Variant-specific Army NBCRV test source; exact store/load unknown |
| Armament (detailed) | .50 cal M2HB on the M151E2 remote weapon system with 2,000 rounds, 360 deg electric traverse at 60 deg/s, elevation +55 to -20 deg, laser rangefinder | `p5-us-ground-stryker-m1135nbcrv-afvdatabase` | C | Supplies the mount, store load and traverse limits the row above leaves open |
| Mission systems | CBRN detectors integrated with navigation and meteorological inputs; digital warning messages | `p5-us-ground-stryker-pm-atlss` | A | Detection ranges, thresholds and latency unknown |
| Propulsion | Caterpillar 350 hp diesel | `p5-us-ground-stryker-army-nbcrv-2006` | A | Variant-specific Army NBCRV test source; dynamic performance unknown |
| Engine designation | Caterpillar 3126, six-cylinder four-cycle inline turbocharged diesel, 350 hp at 2,500 rpm | `p5-us-ground-stryker-m1135nbcrv-afvdatabase` | C | Names the engine the Army test source describes generically; the 2018 A1 450 hp upgrade is not merged |
| Transmission | Allison MD 3066P, six forward and one reverse | `p5-us-ground-stryker-m1135nbcrv-afvdatabase` | C | Secondary source; shift schedule and torque curve not public |
| Fuel capacity | 53 gal (200 L) | `p5-us-ground-stryker-m1135nbcrv-afvdatabase` | C | Secondary source; usable reserve fraction not stated |
| Mobility | 60 mph (96 km/h) maximum level road speed; approximately 330 mi (530 km) road range | `p5-us-ground-stryker-m1135nbcrv-afvdatabase` | C | Replaces the earlier unestablished mobility state with variant-level road figures; off-road performance still not published |
| Combat dimensions | 290.6 × 134.1 × 126.4 in (7.381 × 3.406 × 3.211 m) | `p5-us-ground-stryker-family-gdlsbrochure` | B | GDLS manufacturer combat envelope, which agrees with the Tier C compilation on all three axes for this variant |
| Shipping dimensions | 289 × 109 × 103.62 in (7.341 × 2.769 × 2.632 m) | `p5-us-ground-stryker-family-gdlsbrochure` | B | GDLS shipping envelope; retained separately so the shorter transport length is not read as a combat value |
| Combat weight | 42,665 lb (19,353 kg) | `p5-us-ground-stryker-m1135nbcrv-afvdatabase` | C | Heaviest of the family set, reflecting the CBRN mission fit; distinct from the 17.3 t listed configuration mass above |
| Trench / vertical obstacle | 78 in (200 cm) / 23 in (58 cm) | `p5-us-ground-stryker-m1135nbcrv-afvdatabase` | C | Cross-country obstacle envelope; configuration-dependent |
| Fording depth | 51 in (130 cm) | `p5-us-ground-stryker-m1135nbcrv-afvdatabase` | C | Fording, not swimming; preparation requirements not stated |
| Grade / sideslope | 60% / 30% | `p5-us-ground-stryker-m1135nbcrv-afvdatabase` | C | Slope limits as published; load-dependent in practice |
| Minimum turning diameter | 52 ft (16 m) | `p5-us-ground-stryker-m1135nbcrv-afvdatabase` | C | Four-wheel steering geometry; measurement convention not stated |
| Public protection | Armored Stryker hull; CBRN mission protection context | `p5-us-ground-stryker-pm-atlss` | A | Exact collective-protection performance unknown |
| Hull armor maximum | welded high-hard steel structure, maximum 0.5 in (1.3 cm) | `p5-us-ground-stryker-m1135nbcrv-afvdatabase` | C | Single maximum plate figure from a secondary source. It is not a protection rating, not an all-round value, and not an RHAe equivalent |

Field confidence follows the evidence tier and context column: direct system statements are high confidence; family/configuration context is medium confidence; `unknown` fields remain unestimated.

## Configuration Boundary

The source states the M1135 was not modified with the double-V hull, but received Stryker A1 upgrades from 2018 (450 hp engine, 60,000 lb suspension, 910 A alternator, in-vehicle network). This record is the pre-A1 configuration; the 350 hp engine figure and the figures above must not be carried into an A1 leaf.

## Source References

- `p5-us-ground-stryker-usace-dims`
- `p5-us-ground-stryker-army-nbcrv-2006`
- `p5-us-ground-stryker-pm-atlss`
- `p5-us-ground-stryker-m1135nbcrv-afvdatabase`
- `p5-us-ground-stryker-family-gdlsbrochure`
- `p5-us-ground-stryker-family-gao03671`
