# M1128 Mobile Gun System

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/stryker/m1128-mgs/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-stryker-m1128-mgs` |
| Family / variant | Stryker / M1128 MGS |
| Hull context | Legacy flat-bottom-hull mobile gun system |
| Role | Direct fire support |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Crew | 3 (driver, gunner, vehicle commander) | `p5-us-ground-m1128-army` | A | Direct Army description |
| Main armament | 105 mm cannon with autoloader | `p5-us-ground-m1128-army` | A | Specific cannon designation varies by source; retain as 105 mm pending TM closure |
| Main-gun effective range | 3,200 m (HEAT/antitank context) | `p5-us-ground-m1128-armor-army` | A | Ammunition and engagement conditions matter |
| Coaxial weapon effective range | 7.62 mm: 900 m | `p5-us-ground-m1128-armor-army` | A | Gunnery article figure |
| Flex weapon effective range | M2 .50 cal: 1,800 m | `p5-us-ground-m1128-armor-army` | A | Gunnery article figure |
| Ammunition load | 18 × 105 mm; 400 × .50 cal; 3,400 × 7.62 mm | `p5-us-ground-m1128-army` | A | Full-load training description |
| Rate of fire | Up to 6 rounds/min | `p5-us-ground-m1128-army` | A | Army training description |
| Gross weight | 47,070 lb (21,351 kg) | `p5-us-ground-stryker-m1128mgs-afvdatabase` | C | Secondary gross-mass figure, reported as a gross weight rather than a combat weight; not a GVWR |
| Dimensions | 300.53 × 116.34 × 130.44 in (7.633 × 2.955 × 3.313 m) | `p5-us-ground-stryker-m1128mgs-afvdatabase` | C | Gun-forward length. The elevated 105 mm turret is included in the height figure |
| Engine designation | Caterpillar 3126, six-cylinder four-cycle inline turbocharged diesel, 350 hp at 2,500 rpm | `p5-us-ground-stryker-m1128mgs-afvdatabase` | C | Secondary-sourced designation; the A1 450 hp rating is not merged |
| Transmission | Allison MD 3066P, six forward and one reverse | `p5-us-ground-stryker-m1128mgs-afvdatabase` | C | Secondary source; shift schedule and torque curve not public |
| Fuel capacity | 53 gal (200 L) | `p5-us-ground-stryker-m1128mgs-afvdatabase` | C | Secondary source; usable reserve fraction not stated |
| Maximum level road speed | 60 mph (96 km/h) | `p5-us-ground-stryker-m1128mgs-afvdatabase` | C | Variant-level road figure; off-road speed not published |
| Road range | approximately 300 mi (480 km) on roads | `p5-us-ground-stryker-m1128mgs-afvdatabase` | C | Below the ICV figure; the higher gross mass is the stated reason to keep this value variant-specific |
| Trench / vertical obstacle | 78 in (200 cm) / 23 in (58 cm) | `p5-us-ground-stryker-m1128mgs-afvdatabase` | C | Cross-country obstacle envelope; configuration-dependent |
| Fording depth | 66.9 in (170 cm) | `p5-us-ground-stryker-m1128mgs-afvdatabase` | C | Deeper than the ICV figure and therefore retained separately |
| Grade / sideslope | 60% / 30% | `p5-us-ground-stryker-m1128mgs-afvdatabase` | C | Slope limits as published; load-dependent in practice |
| Minimum turning diameter | 52 ft (17 m) | `p5-us-ground-stryker-m1128mgs-afvdatabase` | C | Four-wheel steering geometry; measurement convention not stated |
| Main gun designation | 105 mm M68A1E8, low-profile turret, electric traverse at 45 deg/s, elevation +15 to -5 deg | `p5-us-ground-stryker-m1128mgs-afvdatabase` | C | Resolves the 105 mm designation left open above; gun is mounted inverted in the low-profile turret |
| Autoloader layout | 18 rounds total: eight in the turret ready carousel, ten in a hull-rear replenisher | `p5-us-ground-stryker-m1128mgs-afvdatabase` | C | Clarifies the 18-round load above; emergency manual loading hatch also described |
| Coaxial / flex store loads | 3,400 × 7.62 mm (500 ready); 400 × .50 cal | `p5-us-ground-stryker-m1128mgs-afvdatabase` | C | Matches the Army load figures above and adds the ready-round split |
| Public protection | Three-person crew protected from small arms, mortar and artillery fragments | `p5-us-ground-m1128-army` | A | Public qualitative statement; thickness/level unknown |
| Hull armor maximum | welded high-hard steel structure, maximum 0.5 in (1.3 cm) | `p5-us-ground-stryker-m1128mgs-afvdatabase` | C | Single maximum plate figure from a secondary source. It is not a protection rating, not an all-round value, and not an RHAe equivalence |

Field confidence follows the evidence tier and context column: direct Army MGS statements are high confidence; qualitative or context-limited statements are medium confidence; `unknown` fields remain unestimated.

## Configuration Boundary

Rows carried from `p5-us-ground-stryker-m1128mgs-afvdatabase` describe the flat-bottom-hull MGS. That source states the M1128 was not given the double-V hull and records the separate Stryker A1 upgrade (450 hp, 60,000 lb suspension, 910 A alternator, in-vehicle network). The 350 hp engine figure and the 300 mi road range above are this configuration's values and must not be carried into an A1 leaf.

## Source References

- `p5-us-ground-m1128-army`
- `p5-us-ground-m1128-armor-army`
- `p5-us-ground-stryker-m1128mgs-afvdatabase`
