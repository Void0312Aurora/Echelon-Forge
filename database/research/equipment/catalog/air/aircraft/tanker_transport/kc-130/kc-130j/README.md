# KC-130J

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/tanker_transport/kc-130/kc-130j/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-24`
Equipment ID: `eq-fr-air-kc130j`
Content status: parameter-complete research record for the KC-130J platform operated by the French Air and Space Force; customer-specific French fit is not inferred where the public platform sources do not state it.

## Identity

- Family: KC-130
- Variant: KC-130J
- Role: Tactical tanker/transport and close-air-support platform
- Configuration scope: Standard-length KC-130J platform. C-130J-30, HC-130J, MC-130J and KC-130T values are excluded.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| French Air and Space Force | In service | French procurement context in backlog; platform parameters use the named KC-130J references |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Role | Multi-role tactical transport, air-to-air refuelling and close air support | `p5-us-air-kc130j-navair` | A |
| Length | 29.3 m (NAVAIR); 29.79 m (manufacturer standard-length table) | `p5-us-air-kc130j-navair`; `p5-us-air-kc130j-lockheed2023` | A/B |
| Wingspan | 39.7 m (NAVAIR); 40.41 m (manufacturer standard-length table) | `p5-us-air-kc130j-navair`; `p5-us-air-kc130j-lockheed2023` | A/B |
| Height | 11.84 m | `p5-us-air-kc130j-lockheed2023` | B |
| Maximum gross/takeoff mass | 155,000 lb (70,306 kg) NAVAIR; 164,000 lb (74,389 kg) manufacturer/USMC planning value | `p5-us-air-kc130j-navair`; `p5-us-air-kc130j-lockheed2023`; `p5-usmc-air-kc130j-avplan2019` | A/B |
| Operating empty mass | 87,961 lb (39,898 kg) | `p5-us-air-kc130j-lockheed2023` | B |
| Maximum payload | 47,000 lb (21,319 kg) | `p5-us-air-kc130j-lockheed2023` | B |
| Powerplant | Four Rolls-Royce AE 2100D3 engines with GE-Dowty R391 six-blade propellers | `p5-us-air-kc130j-lockheed2023` | B |
| Maximum cruise speed | 365 KTAS (675 km/h) manufacturer; 320 KTAS in the USMC tanker planning condition | `p5-us-air-kc130j-lockheed2023`; `p5-usmc-air-kc130j-avplan2019` | A/B |
| Range condition | 3,250 nmi with 20,000 lb payload | `p5-usmc-air-kc130j-avplan2019` | A |
| Fuel capacity | 58,500 lb | `p5-usmc-air-kc130j-avplan2019` | A |
| Cruise ceiling | 25,000 ft | `p5-usmc-air-kc130j-avplan2019` | A |
| Tanker offload | 30,000 lb at 1,200 nmi / 20,000 ft | `p5-usmc-air-kc130j-avplan2019` | A |
| Ground troops | 92 | `p5-usmc-air-kc130j-avplan2019` | A |
| Paratroops | 64 | `p5-usmc-air-kc130j-avplan2019` | A |
| Air-ambulance litters | 74 | `p5-usmc-air-kc130j-avplan2019` | A |
| Defensive systems | ALR-56M RWR, AAR-47(V)2 missile warning, ALQ-157A(V)1 IR countermeasure and ALE-47 dispenser | `p5-usmc-air-kc130j-avplan2019` | A |

## Configuration Boundary

The French queue row names the KC-130J platform, not a French-specific avionics or offload fit. NAVAIR and Lockheed Martin establish the standard platform, while the USMC plan supplies tanker/transport operating conditions. The 155,000 lb NAVAIR maximum gross figure and the 164,000 lb manufacturer/USMC planning figure are retained as separate source-labelled limits; neither is silently reconciled. C-130J-30 and HC-130J values are excluded.

## Source References

- `p5-us-air-kc130j-navair`: `raw/sources/us_navy/p5-us-air-kc130j-navair/manifest.md`
- `p5-usmc-air-kc130j-avplan2019`: `raw/sources/us_marine_corps/p5-usmc-air-kc130j-avplan2019/manifest.md`
- `p5-us-air-kc130j-lockheed2023`: `raw/sources/lockheed_martin/p5-us-air-kc130j-lockheed2023/manifest.md`
