# Voyager KC2

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/tanker/voyager/voyager-kc2/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-18`
Equipment ID: `eq-uk-air-voyager-kc2`
Content status: model-level draft with first-party parameter coverage; KC2 and KC3 figures are separated where the source distinguishes them.

## Identity

- Family: A330 MRTT / Voyager
- Variant: KC2
- Role: Air-to-air refuelling tanker and strategic air transport
- Manufacturer: Airbus (airframe); AirTanker consortium owns, manages and maintains the UK fleet
- Configuration scope: the KC2 has two underwing refuelling pods. The KC3 adds a centreline hose for large aircraft and is a distinct configuration.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| Royal Air Force | In service | `p5-uk-air-voyager-kc2-raf` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Powerplant | Two Rolls-Royce Trent 772B turbofans | `p5-uk-air-voyager-kc2-raf` | A |
| Thrust | 71,000 lb each | `p5-uk-air-voyager-kc2-raf` | A |
| Length | 58.82 m | `p5-uk-air-voyager-kc2-raf` | A |
| Height | 17.39 m | `p5-uk-air-voyager-kc2-raf` | A |
| Wingspan | 60.3 m | `p5-uk-air-voyager-kc2-raf` | A |
| Maximum speed | 330 kt | `p5-uk-air-voyager-kc2-raf` | A |
| Maximum altitude | 41,000 ft | `p5-uk-air-voyager-kc2-raf` | A |
| Refuelling fit (KC2) | Two underwing pods, for fast jets | `p5-uk-air-voyager-kc2-raf` | A |
| Fuel carried | Up to 109 tonnes | `p5-uk-air-voyager-kc2-raf` | A | The source states the aircraft can carry up to 109 tonnes of fuel. This is a carried-fuel load, not an offload rate, a transferable quantity or an internal tank capacity; the source does not state how much of it is transferable per sortie |
| Fuel capacity (alternative reading) | Up to 111,000 kg (245,000 lb as published) | `p5-uk-air-voyager-kc2-ukdf` | C | Recorded alternative to the 109-tonne row. The two readings differ by 2,000 kg and both are retained; neither is preferred and neither is averaged. The source prints 111,000 kg (245,000 lb); 111,000 kg is 244,713 lb, so its imperial value is rounded up to the nearest thousand and is recorded as published rather than as a conversion |
| Fuel offload | 65,000 kg (143,000 lb as published) at 1,000 nautical miles (1,852 km) with two hours on station | `p5-uk-air-voyager-kc2-ukdf` | C | An offload quantity under a stated mission profile, which is a different quantity from the carried-fuel rows above and is not derived from either. 65,000 kg is 143,300 lb; the source's 143,000 lb is rounded to the nearest thousand |
| Maximum fuel offload (type figure) | Up to 70 tonnes (154,000 lb as published) during a one-hour loitering mission at 1,250 nautical miles (2,315 km) from take-off | `p5-eu-air-a330mrtt-airbus` | B | The manufacturer's own offload figure for the A330 MRTT family, of which the Voyager is the British fit. It is a family value under a stated profile and is not asserted as Voyager-specific. 70 tonnes is 154,324 lb; the manufacturer prints 154,000 lb, rounded down to the nearest thousand |
| Payload (type figure) | Up to 45 tonnes (99,000 lb), of which 37 tonnes (82,000 lb) of cargo | `p5-eu-air-a330mrtt-airbus` | B | Family-level manufacturer figure, recorded as such |
| Maximum speed (alternative reading) | 880 km/h | `p5-uk-air-voyager-kc2-ukdf` | C | The Royal Air Force page states 330 kt, which is about 611 km/h. The two readings are not reconciled; both are retained |
| Passenger capacity | Up to 291 passengers, with the cargo hold available for freight | `p5-uk-air-voyager-kc2-raf` | A |
| Aeromedical fit | Up to 40 stretchers and three critical care patients | `p5-uk-air-voyager-kc2-raf` | A |
| Sensors | Weather radar | `p5-uk-air-voyager-kc2-raf` | A |
| Defensive aids | Enhanced Defensive Aids Suite | `p5-uk-air-voyager-kc2-raf` | A |
| Aircrew | Two pilots, one mission systems operator for air-to-air refuelling, eight cabin crew for air transport | `p5-uk-air-voyager-kc2-raf` | A |
| Platform basis | Airbus A330-200 | `p5-uk-air-voyager-kc2-raf` | A |

## Configuration Boundary

The page describes the Voyager as a whole and distinguishes KC2 from KC3 only by refuelling fit: the KC2 has two underwing pods, the KC3 adds a centreline hose for large aircraft. All other figures above are common to both marks and are not asserted as KC2-unique. The 109-tonne figure is a carried-fuel load, not an internal tank capacity, and the source notes that fuel is stored in existing tanks with the cabin left available. Structural masses and range are not published on the page and are not recorded.

Three packages now supply fuel and payload quantities and they are not the same quantity:
- The Royal Air Force page gives up to 109 tonnes of fuel carried.
- The UK Defence Forum thread gives up to 111,000 kg (245,000 lb) of fuel capability, a 2,000 kg higher reading, and an offload of 65,000 kg at 1,000 nautical miles with two hours on station.
- The Airbus A330 MRTT page gives up to 70 tonnes (154,000 lb) of maximum fuel offload under a one-hour loiter at 1,250 nautical miles, and up to 45 tonnes of payload of which 37 tonnes is cargo.

A carried load, a capacity and an offload under a stated profile are three different quantities. None of the three is derived from another, none is averaged, and the 111,000 kg capacity reading is not attributed to the manufacturer because the page fetch did not confirm the capacity figure that the search return showed. The 330 kt maximum speed on the Royal Air Force page and the 880 km/h reading on the forum thread are likewise both retained and unreconciled.

## Source References

- `p5-uk-air-voyager-kc2-raf`: `raw/sources/royal_air_force/p5-uk-air-voyager-kc2-raf/manifest.md` — Royal Air Force platform page
- `p5-uk-air-voyager-kc2-ukdf`: `raw/sources/uk_defence_forum/p5-uk-air-voyager-kc2-ukdf/manifest.md` — fuel capability and offload readings
- `p5-eu-air-a330mrtt-airbus`: `raw/sources/airbus/p5-eu-air-a330mrtt-airbus/manifest.md` — manufacturer family offload and payload figures
