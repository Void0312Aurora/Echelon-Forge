# C-130J Hercules

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/tactical_transport/c-130/c-130j/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-18`
Equipment ID: `eq-us-air-c130j`
Content status: model-level draft with first-party parameter coverage; C-130E/H values from the same fact sheet are excluded rather than merged.

## Identity

- Family: C-130
- Variant: C-130J
- Role: Tactical airlift
- Manufacturer: Lockheed-Martin Aeronautics Company
- Configuration scope: standard-length C-130J. The stretched C-130J-30 is a separate leaf and its values are not carried here.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| United States Air Force | In service | `p5-us-air-c130j-usaf` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Powerplant | Four Rolls-Royce AE 2100D3 turboprops | `p5-us-air-c130j-usaf` | A |
| Propeller | Six-bladed all-composite | `p5-us-air-c130j-usaf` | A |
| Shaft power | 4,700 hp each | `p5-us-air-c130j-usaf` | A |
| Length | 97 ft 9 in (29.3 m) | `p5-us-air-c130j-usaf` | A |
| Height | 38 ft 10 in (11.9 m) | `p5-us-air-c130j-usaf` | A |
| Wingspan | 132 ft 7 in (39.7 m) | `p5-us-air-c130j-usaf` | A |
| Cargo compartment | Length 41 ft (12.5 m), width 123 in (3.12 m), height 9 ft (2.74 m); rear ramp length 119 in (3.02 m), width 118.9 in (3.02 m) | `p5-us-air-c130j-usaf` | A |
| Cruise speed | 417 mph / 362 ktas (Mach 0.59) at 22,000 ft (6,706 m) | `p5-us-air-c130j-usaf` | A |
| Ceiling | 28,000 ft (8,615 m) with 42,000 lb (19,090 kg) payload | `p5-us-air-c130j-usaf` | A |
| Maximum takeoff weight | 164,000 lb (74,393 kg) | `p5-us-air-c130j-usaf` | A |
| Maximum allowable payload | 42,000 lb (19,090 kg) | `p5-us-air-c130j-usaf` | A |
| Maximum normal payload | 34,000 lb (15,422 kg) | `p5-us-air-c130j-usaf` | A |
| Range at maximum normal payload | 2,071 mi (1,800 nmi) | `p5-us-air-c130j-usaf` | A |
| Range with 35,000 lb payload | 1,841 mi (1,600 nmi) | `p5-us-air-c130j-usaf` | A |
| Maximum load | 6 pallets, 72 litters, 16 CDS bundles, 90 combat troops or 64 paratroopers, or a combination up to compartment capacity or maximum allowable weight | `p5-us-air-c130j-usaf` | A |
| Crew | Three (two pilots and a loadmaster) | `p5-us-air-c130j-usaf` | A |
| Date deployed | February 1999 | `p5-us-air-c130j-usaf` | A |

## Configuration Boundary

The fact sheet publishes C-130E, C-130H, C-130J and C-130J-30 figures side by side. Only the C-130J column is recorded here. The C-130J-30 stretch adds 15 ft to the fuselage, which changes length, cargo compartment, ceiling and both range figures; those values belong to the `eq-fr-air-c130j30` and `eq-us-air-c130j` sibling leaves and are not merged. The C-130J-30 figures stated in this same source are available for that leaf.

## Source References

- `p5-us-air-c130j-usaf`: `raw/sources/us_air_force/p5-us-air-c130j-usaf/manifest.md`
