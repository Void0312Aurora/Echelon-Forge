# M1132 Engineer Squad Vehicle

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/stryker/m1132-esv/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-stryker-m1132-esv` |
| Family / variant | Stryker / M1132 ESV |
| Hull context | Engineer squad configuration |
| Role | Mobility and limited countermobility support |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Listed configuration mass | 16.5 t | `p5-us-ground-stryker-usace-dims` | A | Source table configuration; attachments change mass |
| Length × width × height | 7.59 × 2.87 × 2.69 m | `p5-us-ground-stryker-usace-dims` | A | Engineer attachment envelope |
| Crew / payload | 11 total personnel | `p5-us-ground-stryker-pm-atlss` | A | Army programme page total; crew/squad split and attachment load remain unnormalized |
| Mission systems | Obstacle neutralization, lane marking, and mine-detection equipment | `p5-us-ground-stryker-pm-atlss` | A | Attachment models and performance unknown |
| Armament | Remote weapon station context | `p5-us-ground-stryker-pm-atlss` | A | Exact station fit unknown |
| Propulsion / mobility | Unknown at M1132-specific evidence level | — | — | Do not copy M1126 family baseline |
| Public protection | Armored Stryker hull; exact thickness/level unknown | `p5-us-ground-stryker-army-wsh-2020` | A | Qualitative only |

Field confidence follows the evidence tier and context column: direct variant statements are high confidence; attachment-sensitive statements are medium confidence; unknown fields remain unestimated.

## Source References

- `p5-us-ground-stryker-usace-dims`
- `p5-us-ground-stryker-pm-atlss`
- `p5-us-ground-stryker-army-wsh-2020`
