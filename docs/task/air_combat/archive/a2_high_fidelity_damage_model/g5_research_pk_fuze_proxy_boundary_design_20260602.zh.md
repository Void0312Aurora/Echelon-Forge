# A2 G5-R Pk / Fuze Proxy Boundary Design - 2026-06-02

状态：`2026-06-02 / G5-R-B-PROXY-BOUNDARY / pass / research_candidate / non_authoritative`。

本文定义 `G5-R` 的 Pk / fuze proxy 研究边界。它只给后续 event-chain map 提供变量、
连接关系和禁用声明，不授予 `pk_authority` 或 `deterministic_fuze_authority`。

## Design Scope

G5-R proxy chain 只回答：

- 哪些 runtime / G4 research input 可以进入一个 kill-chain proxy；
- 每个输入如何标注 source、uncertainty、confidence 和 replacement rule；
- proxy 输出最多能表达什么研究级状态；
- 哪些说法必须保持禁止。

G5-R proxy chain 不回答：

- 单发 Pk；
- mission-kill probability；
- deterministic fuze trigger truth；
- target signature truth；
- stock database behavior。

## Proxy Event Chain

| stage | research input | allowed proxy output | required boundary |
|---|---|---|---|
| `terminal_geometry` | guidance / miss-distance public methods and runtime event refs | miss-distance / aspect / closure bucket | not hit probability |
| `fuze_proxy_branch` | fuze authority package shape and public fuze terminology | fallback-compatible branch label: proximity-like / contact-like / no-trigger-window | not deterministic trigger |
| `mechanism_load` | `G4-R-B` mechanism-load vector | blast / fragment qualitative load axis | not real warhead row |
| `component_response` | `G4-R-C` component fragility surface | component response label / curve-family ref | not calibrated component probability |
| `consequence_proxy` | `DamageReport` / EffectsEvent consequence flags | ordered consequence class or non-probability score placeholder | not Pk or mission-kill probability |
| `uncertainty` | G4 uncertainty audit plus G5 source scan | source/model/scope uncertainty labels | not reviewer-accepted truth |

## Proxy Variable Shape

Each future row should use this shape:

```json
{
  "proxy_id": "g5_research_proxy_example",
  "profile": "research_candidate",
  "authority": {
    "pk_authority": false,
    "deterministic_fuze_authority": false,
    "stock_descriptor_created": false
  },
  "inputs": {
    "terminal_geometry_ref": "G5SRC-006",
    "fuze_proxy_ref": "G5SRC-004",
    "mechanism_load_ref": "G5SRC-001",
    "component_response_ref": "G5SRC-002",
    "consequence_ref": "G5SRC-008"
  },
  "output": {
    "type": "non_authoritative_research_proxy",
    "value_type": "ordinal_label_or_score_placeholder",
    "not_pk": true,
    "not_mission_kill_claim": true
  },
  "uncertainty": {
    "source": "required",
    "model_form": "required",
    "scope": "required",
    "confidence": "required"
  },
  "replacement_rule": "required"
}
```

## Forbidden Claims

The following claims remain forbidden in this research lane:

- Pk calibration claim;
- deterministic fuze authority claim;
- RNG fallback removal claim;
- mission-kill probability established;
- combat reward / terminal win used as truth;
- G4 component response promoted to kill-chain authority;
- stock descriptor created.

## Worker Packet

```md
status: pass
touched files:
- docs/task/air_combat/archive/a2_high_fidelity_damage_model/g5_research_pk_fuze_proxy_boundary_design_20260602.zh.md
commands/outcomes:
- pending integration validation
remaining paths:
- G5-R-C event-chain map
- G5-R-D uncertainty / independence audit
behavior risks:
- proxy score being interpreted as Pk
- fuze branch label being interpreted as deterministic trigger
integration notes:
- Event-chain map should consume this as a boundary document, not as a runtime descriptor.
research boundary confirmation:
- `pk_authority=false`
- `deterministic_fuze_authority=false`
- `stock_descriptor_created=false`
```
