# Protector RG1

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/uas/protector/protector-rg1/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-22`
Equipment ID: `eq-uk-air-protector-rg1`
Content status: parameter table complete for the UK Protector RG Mk1 research record; RAF-specific weapon/sensor/crew rows and common MQ-9B mass/payload data remain separated.

## Identity

- Family: Protector / MQ-9B SkyGuardian
- Variant: RG Mk1
- Role: Remotely piloted medium-altitude long-endurance aircraft for surveillance, intelligence and strike
- Manufacturer: General Atomics Aeronautical Systems Inc (`MQ-9B SkyGuardian` basis); UK designation Protector RG Mk1
- Configuration scope: UK system, including UK-specific datalink and weapon integration.

## Operators

| Operator | Status | Source |
| --- | --- | --- |
| Royal Air Force | In service | `p5-uk-air-protector-rg1-raf` |

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Powerplant | Honeywell TPE331-10T turboprop | `p5-uk-air-protector-rg1-raf` | A |
| Shaft power | 900 shp | `p5-uk-air-protector-rg1-raf` | A |
| Length | 11.43 m | `p5-uk-air-protector-rg1-raf` | A |
| Height | 3.78 m | `p5-uk-air-protector-rg1-raf` | A |
| Wingspan | 24.07 m | `p5-uk-air-protector-rg1-raf` | A |
| Maximum speed | 250 kt | `p5-uk-air-protector-rg1-raf` | A |
| Maximum altitude | 50,000 ft | `p5-uk-air-protector-rg1-raf` | A |
| Endurance | Over 40 hours in the capability section; over 30 hours in the accompanying video description | `p5-uk-air-protector-rg1-raf` | A |
| Missiles | MBDA Brimstone 3A | `p5-uk-air-protector-rg1-raf` | A |
| Bombs | Raytheon UK Paveway IV, 500 lb precision bomb | `p5-uk-air-protector-rg1-raf` | A |
| Radar | Synthetic aperture radar with ground moving target indication | `p5-uk-air-protector-rg1-raf` | A |
| Electro-optics | AN/DAS-4 multi-spectral targeting system | `p5-uk-air-protector-rg1-raf` | A |
| Aircrew (remote) | One pilot, one sensor operator and one mission intelligence coordinator | `p5-uk-air-protector-rg1-raf` | A |
| Main operating base | RAF Waddington, with deployments to up to two additional global locations | `p5-uk-air-protector-rg1-raf` | A |
| Maximum gross takeoff weight | 12,500 lb (5,670 kg) | `p5-uk-air-protector-rg1-gaasi` | B (common MQ-9B) |
| Internal fuel | 6,000 lb (2,721 kg) | `p5-uk-air-protector-rg1-gaasi` | B (common MQ-9B) |
| Payload capacity | 4,750 lb (2,155 kg) across nine hardpoints, including 800 lb internal | `p5-uk-air-protector-rg1-gaasi` | B (common MQ-9B) |
| Range | 6,000+ nmi, configuration-dependent | `p5-uk-air-protector-rg1-gaasi` | B (common MQ-9B) |
| Data links / airworthiness | C-band LOS; X/Ku/Ka-band BLOS; STANAG 4671 and civil-airspace compliant design context | `p5-uk-air-protector-rg1-gaasi`; `p5-uk-air-protector-rg1-raf` | A/B |

## Configuration Boundary

The RAF page states endurance twice with different values: the capability section gives over 40 hours, while the linked video description gives over 30 hours at altitudes up to 40,000 ft. Both are recorded rather than reconciled; the difference may reflect a load or profile the page does not state. GA-ASI supplies common MQ-9B mass, fuel, payload, range and link figures; those are not presented as UK-specific certification values. Brimstone 3A and Paveway IV are the UK-specific store integrations and are not generic MQ-9B capability.

## Source References

- `p5-uk-air-protector-rg1-raf`: `raw/sources/royal_air_force/p5-uk-air-protector-rg1-raf/manifest.md`
- `p5-uk-air-protector-rg1-gaasi`: `raw/sources/general_atomics/p5-uk-air-protector-rg1-gaasi/manifest.md` — common MQ-9B structural, payload, performance and link data
