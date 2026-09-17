# M1130 Command Vehicle

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/stryker/m1130-cv/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-stryker-m1130-cv` |
| Family / variant | Stryker / M1130 CV |
| Hull context | Command-vehicle configuration |
| Role | Command, control, communications, and mission planning |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Listed configuration mass | 16.6 t | `p5-us-ground-stryker-usace-dims` | A | Source table configuration; communications fit can change mass |
| Length × width × height | 7.49 × 2.84 × 2.69 m | `p5-us-ground-stryker-usace-dims` | A | Command antenna/power fit context |
| Crew | 5 | `p5-us-ground-stryker-pm-atlss` | A | Draft mission configuration; exact seat allocation unknown |
| Armament | Remote weapon station | `p5-us-ground-stryker-pm-atlss` | A | Weapon fit not further specified |
| Mission systems | C2 communications, data, planning, and aircraft antenna/power interface | `p5-us-ground-stryker-pm-atlss` | A | Radio suite and network performance unknown |
| Propulsion / mobility | Unknown at M1130-specific evidence level | — | — | Do not copy M1126 family baseline |
| Public protection | Armored Stryker hull; exact thickness/level unknown | `p5-us-ground-stryker-army-wsh-2020` | A | Qualitative only |

Field confidence follows the evidence tier and context column: direct variant statements are high confidence; mission/configuration context is medium confidence; unknown fields remain unestimated.

## Source References

- `p5-us-ground-stryker-usace-dims`
- `p5-us-ground-stryker-pm-atlss`
- `p5-us-ground-stryker-army-wsh-2020`
