# Su-30SME

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/air/aircraft/fighter/su-30/su-30sme/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-18`
Equipment ID: `eq-ru-air-su30sme`
Content status: Export-variant record; not merged with Russian service Su-30SM. The payload and dimensions rest on a manufacturer table that did not render in the text capture, which is stated on the rows themselves.

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
| Height | 6.36 m | `p5-ru-air-su30sme-uac` | B |

## Configuration Boundary

The export specification held here supplies weight, crew, maximum speed and flight range at Tier A. It states no payload, no hardpoint count and no dimensions, which is why the manufacturer page is used for those rows.

The manufacturer table is rendered by script on the page and did not resolve in the text capture. The payload, hardpoint count and dimensions are therefore recorded from the page's published specification content as returned in search indexing rather than from a rendered read of the table, and they are labelled Tier B rather than presented as first-hand extractions. The two secondary sources that an earlier revision of this leaf cited as repeating the 8,000 kg payload are withdrawn, because neither was named and neither could be re-located; the payload now stands on this page alone with that limitation stated.

The Su-30SME is the export designation and the Su-30SM is a separate Russian service configuration. The two are separate records and no value is carried between them.

## Source References

- `p5-ru-air-su30sme-roe`: `raw/sources/rosoboronexport/p5-ru-air-su30sme-roe/manifest.md` — weight, crew, speed, range
- `p5-ru-air-su30sme-uac`: `raw/sources/uac/p5-ru-air-su30sme-uac/manifest.md` — payload, hardpoints, dimensions
