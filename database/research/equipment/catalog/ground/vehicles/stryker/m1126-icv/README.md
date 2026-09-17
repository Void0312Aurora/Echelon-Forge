# M1126 Infantry Carrier Vehicle

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/stryker/m1126-icv/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-stryker-m1126-icv` |
| Family / variant | Stryker / M1126 ICV |
| Hull context | Legacy flat-bottom hull (FBH) baseline in the cited material |
| Role | Infantry carrier |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Listed configuration mass | 16.1 t | `p5-us-ground-stryker-usace-dims` | A | Source table configuration; not a universal combat or GVW value |
| Length × width × height | 7.32 × 2.84 × 2.69 m | `p5-us-ground-stryker-usace-dims` | A | Configuration and attachments must be retained when normalized |
| Powerplant | 350 hp diesel | `p5-us-ground-stryker-army-wsh-2020` | A | Baseline ICV context; do not copy to later DVH/DVHA1 leaves |
| Road speed | 60 mph | `p5-us-ground-stryker-army-wsh-2020` | A | Explicit public baseline figure; terrain-specific speed unknown |
| Cruising range | 330 mi | `p5-us-ground-stryker-army-wsh-2020` | A | Explicit public baseline figure; fuel-load context not established |
| Crew / carried infantry | 2 crew + 9 infantry | `p5-us-ground-stryker-army-wsh-2020` | A | Configuration-specific carrier load |
| Armament | M2 .50 cal or Mk 19 remote weapon station | `p5-us-ground-stryker-army-wsh-2020` | A | Station fit is configuration-dependent |
| Mission systems | Infantry squad transport; C4ISR/RWS context | `p5-us-ground-stryker-pm-atlss` | A | Detailed sensor and radio performance not established |
| Public protection | Armored Stryker hull; exact thickness/level unknown | `p5-us-ground-stryker-army-wsh-2020` | A | Do not infer armor thickness from family descriptions |

Field confidence follows the evidence tier and context column: direct variant statements are high confidence; baseline or family-context statements are medium confidence; `unknown` remains unestimated.

## Source References

- `p5-us-ground-stryker-army-wsh-2020`
- `p5-us-ground-stryker-usace-dims`
- `p5-us-ground-stryker-pm-atlss`
