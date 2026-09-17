# AGM-158C LRASM

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/weapon/anti-ship/lrasm/agm-158c/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-weapon-agm158c` |
| Family / variant | LRASM / AGM-158C (C-1 baseline) |
| Role | Air-launched low-observable, semi-autonomous long-range anti-ship cruise missile |
| Configuration boundary | Fielded AGM-158C/C-1 on B-1B and F/A-18E/F; C-3 extended-range development, JASSM-A/B and surface-launch concepts are excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Mass | 1,020-1,250 kg all-up missile (public bounded estimate) | `p5-us-weapon-agm158c-navair`; `p5-us-weapon-agm158c-lockheedmartin` | A/C | LRASM-specific mass is not officially published; JASSM-ER-derived body and added maritime sensors bound the range |
| Dimensions | 4.26-4.29 m length; 2.7 m deployed wingspan; 0.60-0.66 m body width and 0.44-0.48 m height | `p5-us-weapon-agm158c-lockheedmartin` | C | Length/span derive from JASSM-ER outer mold line; width/height are bounded specialist geometry estimates |
| Propulsion / motor | Williams F107-WR-105 turbofan, 5.8-6.5 kN thrust bound; folding wings and tail for carriage | `p5-us-weapon-agm158c-navair`; `p5-us-weapon-agm158c-lockheedmartin` | A/C | Engine thrust is JASSM-ER family value; LRASM inlet/mission software differences not separately published |
| Guidance / seeker | GPS-aided INS with anti-jam receiver, weapon data link, passive RF/multimodal sensor suite and imaging-IR terminal classification; autonomous target selection and re-attack logic | `p5-us-weapon-agm158c-navair`; `p5-us-weapon-agm158c-lockheedmartin` | A/C | Exact sensor weighting and target libraries are classified; represent functional multimodal seeker only |
| Range / flight envelope | Greater than 200 nmi (>370 km) public standoff range; high-subsonic, low-observable sea-skimming/terrain-following terminal profile | `p5-us-weapon-agm158c-navair`; `p5-us-weapon-agm158c-lockheedmartin` | A/C | Navy states >200 nmi; precise C-1 range and altitude schedule are classified; do not infer JASSM-ER 925 km range |
| Warhead | 450-454 kg (1,000 lb class) penetrator/blast-fragmentation warhead, WDU-42/B family | `p5-us-weapon-agm158c-navair`; `p5-us-weapon-agm158c-lockheedmartin` | A/C | Public budget and USAF test reports confirm class and effect; exact fuze/liner details omitted |
| Fuze / trigger | Programmable electronic fuze with delayed penetrator detonation; impact/height-of-burst behavior functionally bounded | `p5-us-weapon-agm158c-lockheedmartin` | C | Specific FMU designation and delay settings are not public in current sources; model impact plus selectable delay |

## Source References

- `p5-us-weapon-agm158c-navair`: `raw/sources/us_navy/p5-us-weapon-agm158c-navair/manifest.md`
- `p5-us-weapon-agm158c-lockheedmartin`: `raw/sources/lockheed_martin/p5-us-weapon-agm158c-lockheedmartin/manifest.md`
