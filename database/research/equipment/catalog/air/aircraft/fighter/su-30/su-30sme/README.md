# Su-30SME

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/su-30/su-30sme/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-23`
Equipment ID: `eq-ru-air-su30sme`
Content status: parameter-complete export-variant record; not merged with Russian service Su-30SM. Official ROSOBORONEXPORT and UAC readings are retained with their definitions.

## Identity

- Family: Su-30
- Variant: Su-30SME
- Role: Multirole fighter, export configuration
- Manufacturer: Irkut, within the United Aircraft Corporation group
- Configuration scope: the export designation of the Su-30SM family, as offered for export. It is not the Russian service Su-30SM and no value is carried between the two.

## Parameters

| Parameter | Value | Source | Confidence |
| --- | --- | --- | --- |
| Weight | 34 t | `p5-ru-air-su30sme-roe` | A |
| Crew | 2 | `p5-ru-air-su30sme-roe` | A |
| Maximum speed | Mach 1.75 | `p5-ru-air-su30sme-roe` | A |
| Flight range | 3,000 km | `p5-ru-air-su30sme-roe` | A |
| Payload | Up to 8,000 kg across 12 external points | `p5-ru-air-su30sme-uac` | B |
| Length | 21.9 m | `p5-ru-air-su30sme-uac` | B |
| Wingspan | 14.7 m | `p5-ru-air-su30sme-uac` | B |
| Height | 6.36 m in the earlier package; 6.4 m in the current UAC table | `p5-ru-air-su30sme-uac` | B |
| Normal takeoff mass | 26,090 kg | `p5-ru-air-su30sme-uac` | B |
| Maximum takeoff mass | 34,000 kg | `p5-ru-air-su30sme-roe`; `p5-ru-air-su30sme-uac` | A/B |
| Powerplant | 2 × AL-31FP afterburning turbofans | `p5-ru-air-su30sme-uac` | B |
| Engine thrust | 7,770 kgf dry / 12,500 kgf afterburning per engine | `p5-ru-air-su30sme-uac` | B |
| Internal fuel | 5,270 kg normal / 9,300 kg maximum | `p5-ru-air-su30sme-uac` | B |
| Service ceiling | 16,100 m | `p5-ru-air-su30sme-roe`; `p5-ru-air-su30sme-uac` | A/B |
| Combat load | Up to 8,000 kg on 12 external points | `p5-ru-air-su30sme-roe`; `p5-ru-air-su30sme-uac` | A/B |
| Range | 3,000 km practical; 5,600 km with refuelling | `p5-ru-air-su30sme-uac` | B |
| In-flight refuelling | Yes | `p5-ru-air-su30sme-uac` | B |
| Mission system / armament | Radar, optical-electronic sight/navigation, helmet-mounted cueing, satellite navigation, electronic suppression and guided/unguided air-to-air/air-to-surface/anti-ship/anti-radar stores | `p5-ru-air-su30sme-uac` | B |

## Configuration Boundary

The ROSOBORONEXPORT sheet supplies maximum takeoff weight, crew, speed, ceiling, payload and hardpoint count at Tier A. The UAC page supplies the detailed dimensions, engine, fuel, range, refuelling and mission-system block.

The UAC specification block is now returned by the retrieval and supplies the dimensions, engine, fuel, range, refuelling and mission-system rows. The earlier 6.36 m height is retained as the prior UAC reading alongside the current 6.4 m table value; the difference is not reconciled.

The Su-30SME is the export designation and the Su-30SM is a separate Russian service configuration. The two are separate records and no value is carried between them.

## Source References

- `p5-ru-air-su30sme-roe`: `raw/sources/rosoboronexport/p5-ru-air-su30sme-roe/manifest.md` — weight, crew, speed, range
- `p5-ru-air-su30sme-uac`: `raw/sources/uac/p5-ru-air-su30sme-uac/manifest.md` — payload, hardpoints, dimensions
