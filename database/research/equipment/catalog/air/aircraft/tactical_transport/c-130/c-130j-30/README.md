# C-130J-30 Super Hercules

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/tactical_transport/c-130/c-130j-30/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-18`
Equipment ID: `eq-fr-air-c130j30`
Content status: model-level draft with parameter coverage from two sources; stretch-specific figures come from the United States Air Force fact sheet, which publishes the C-130J-30 column separately.

## Identity

- Family: C-130
- Variant: C-130J-30
- Role: Tactical airlift, stretched fuselage
- Manufacturer: Lockheed-Martin Aeronautics Company
- Configuration scope: the C-130J-30 is a stretch version of the C-130J with a 15 ft (4.57 m) fuselage extension. Its figures differ from the standard-length C-130J and are kept separate from that leaf.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| French Air and Space Force | In service | `p5-fr-air-c130j30` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Powerplant | Four Rolls-Royce AE 2100D3 turboprops | `p5-us-air-c130j-usaf` | A |
| Shaft power | 4,700 hp each | `p5-us-air-c130j-usaf` | A |
| Length | 112 ft 9 in (34.69 m) | `p5-us-air-c130j-usaf` | A |
| Height | 38 ft 10 in (11.9 m) | `p5-us-air-c130j-usaf` | A |
| Wingspan | 132 ft 7 in (39.7 m) | `p5-us-air-c130j-usaf` | A |
| Cargo compartment | Length 56 ft (16.9 m), width 123 in (3.12 m), height 9 ft (2.74 m); rear ramp length 119.9 in (3.05 m), width 118.9 in (3.02 m) | `p5-us-air-c130j-usaf` | A | Source arithmetic in this block is unreliable and was corrected on transcription: the fact sheet prints the rear ramp as 119.9 inches (3.12 meters) and the ramp width as 118.9 inches (36.24 meters), and prints the compartment width as 123 inches (meters) with no metric value. The metric values here are computed from the imperial figures. |
| Cruise speed | 410 mph / 356 ktas (Mach 0.58) at 22,000 ft (6,706 m) | `p5-us-air-c130j-usaf` | A |
| Ceiling | 26,000 ft (7,925 m) with 44,500 lb (20,185 kg) payload | `p5-us-air-c130j-usaf` | A | The fact sheet prints 26,000 ft as 8,000 m and 44,500 lb as 20,227 kg, both arithmetically wrong. The metric values here are computed (7,925 m and 20,185 kg); the imperial figures are the source values. |
| Maximum takeoff weight | 164,000 lb (74,389 kg), identical to the standard C-130J | `p5-us-air-c130j30-ang-factsheet` | A | The main Air Force fact sheet publishes this figure for the C-130J column only. The Air National Guard fact sheet supplies the J-30 column and states the structural limit is identical between the two marks, so the stretch did not raise it |
| Maximum payload (Air National Guard figure) | 46,700 lb (21,183 kg) against 47,000 lb (21,319 kg) for the standard C-130J | `p5-us-air-c130j30-ang-factsheet` | A | The stretched airframe carries slightly less payload than the standard one under this source's definition. This is a second, differently defined payload figure alongside the 44,000 lb maximum allowable payload row above, and the two are not reconciled |
| Maximum allowable payload | 44,000 lb (19,958 kg) | `p5-us-air-c130j-usaf` | A |
| Maximum normal payload | 36,000 lb (16,329 kg) | `p5-us-air-c130j-usaf` | A |
| Range at maximum normal payload | 1,956 mi (1,700 nmi) | `p5-us-air-c130j-usaf` | A |
| Range with 35,000 lb payload | 2,417 mi (2,100 nmi) | `p5-us-air-c130j-usaf` | A |
| Maximum load | 8 pallets, 97 litters, 24 CDS bundles, 128 combat troops or 92 paratroopers, or a combination up to compartment capacity or maximum allowable weight | `p5-us-air-c130j-usaf` | A |
| Crew | Three (two pilots and a loadmaster) | `p5-us-air-c130j-usaf` | A |
| Aeromedical role | Basic crew of five added (two flight nurses, three medical technicians) | `p5-us-air-c130j-usaf` | A |

## Configuration Boundary

The stretch is not cosmetic: the 15 ft fuselage extension increases length to 112 ft 9 in against 97 ft 9 in for the standard C-130J, raises the cargo compartment from 41 ft to 56 ft, and changes the ceiling, both payload figures and both range figures. None of these are shared with the `eq-us-air-c130j` leaf.

The cited fact sheet does not publish a maximum takeoff weight for the J-30 column; it states 164,000 lb for the C-130J and 155,000 lb for the C-130E/H. That value is therefore left unrecorded rather than inferred. The French source held for this leaf states approximately 8 hours endurance, which is a French operational figure and is not merged with the US performance table.

## Source References

- `p5-fr-air-c130j30`: `raw/sources/ministere_des_armees/p5-fr-air-c130j30/manifest.md`
- `p5-us-air-c130j-usaf`: `raw/sources/us_air_force/p5-us-air-c130j-usaf/manifest.md`
- `p5-us-air-c130j30-ang-factsheet`: `raw/sources/us_air_force/p5-us-air-c130j30-ang-factsheet/manifest.md`
