# A330 Phénix

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/tanker/a330-mrtt/a330-phenix/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-18`
Equipment ID: `eq-fr-air-a330-mrtt`
Content status: model-level draft with first-party parameter coverage. The French Ministry of the Armed Forces page publishes a complete characteristics block for this variant.

## Identity

- Family: A330 MRTT
- Variant: Phénix (A330 MRTT Enhanced)
- Role: Multi-role aerial refuelling and strategic transport; primary mission is refuelling the airborne component of the French nuclear deterrent
- Manufacturer: Airbus
- Programme: French MRTT programme launched 2014; fifteen aircraft planned by 2028; replaces the C-135FR/KC-135RG fleet and the A310/A340 transport aircraft
- Configuration scope: A330 MRTT Enhanced on an A330-200 platform with French-specific modifications. The first standard covers deterrent mission permanence, strategic passenger transport and medical evacuation; a second standard planned for 2025 improves survivability and communications.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| French Air and Space Force | In service | `p5-fr-air-a330-mrtt` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Engines | Two Rolls-Royce Trent 772B | `p5-fr-air-a330-mrtt` | A |
| Engine thrust | 316 kN per engine | `p5-fr-air-a330-mrtt` | A | The source labels this figure under engine performance and gives the unit as kN, which is thrust, not power. Recorded as thrust; no shaft or equivalent power figure is published |
| Wingspan | 60.3 m | `p5-fr-air-a330-mrtt` | A |
| Length | 58.8 m | `p5-fr-air-a330-mrtt` | A |
| Height | 17.4 m | `p5-fr-air-a330-mrtt` | A |
| Maximum takeoff mass | 233 t | `p5-fr-air-a330-mrtt` | A |
| Fuel capacity | 110 t, distributed in the wing | `p5-fr-air-a330-mrtt` | A |
| Maximum speed | Mach 0.86 | `p5-fr-air-a330-mrtt` | A |
| Cruise speed | Mach 0.82 | `p5-fr-air-a330-mrtt` | A |
| Payload | 40 t | `p5-fr-air-a330-mrtt` | A |
| Maximum passengers | 272 | `p5-fr-air-a330-mrtt` | A |
| Crew | Two pilots, plus cabin crew or air refuelling operator depending on mission | `p5-fr-air-a330-mrtt` | A |
| Refuelling fit | Two wingtip pods each deploying a 27 m hose and drogue; a centreline boom for aircraft that cannot be refuelled by the pods | `p5-fr-air-a330-mrtt` | A |
| Simultaneous receivers | Two fighters, or one E-3F surveillance aircraft | `p5-fr-air-a330-mrtt` | A |
| Refuelling operator station | Dedicated console in the cabin, using a camera system, rather than the rear boom position used on the C-135 | `p5-fr-air-a330-mrtt` | A |
| Camera system | Two 3D day/night cameras, three panoramic cameras (left, centre, right) and two removable 330-degree cameras at the rear | `p5-fr-air-a330-mrtt` | A |
| Datalink | Fully integrated into the Link 16 bubble, with an L16-JRE improvement to transmit the general situation to the command centre | `p5-fr-air-a330-mrtt` | A |
| Medevac configuration CM30 | 20 stations for up to 40 lightly wounded, plus 88 passengers and lower-hold freight | `p5-fr-air-a330-mrtt` | A |
| Medevac configuration Morphée | 10 modules for around ten seriously wounded, plus 88 passengers and lower-hold freight | `p5-fr-air-a330-mrtt` | A |
| Opportunity medevac configuration | Two stretchers, plus 256 passengers and lower-hold freight | `p5-fr-air-a330-mrtt` | A |

## Configuration Boundary

The three medevac configurations are mutually exclusive fits and are recorded separately rather than collapsed into a single patient capacity. The fuel capacity of 110 t is a total carried load distributed in the wing, not a fuselage tank figure, and it is separate from the 40 t payload value. The UK Voyager KC2 is the same A330 MRTT family but a different national configuration with a different refuelling fit and a different fuel figure; those values are not interchangeable with this leaf.

## Source References

- `p5-fr-air-a330-mrtt`: `raw/sources/ministere_des_armees/p5-fr-air-a330-mrtt/manifest.md`
