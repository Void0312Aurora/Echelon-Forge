# A2 G5-R Event Chain Map - 2026-06-02

状态：`2026-06-02 / G5-R-C-EVENT-CHAIN-MAP / pass / research_candidate / non_authoritative`。

本文把 `G5-R` 的 terminal geometry、fuze proxy、G4 mechanism-load、G4 component
response 和 consequence surface 串成一条 research event chain。它不实现 runtime，
不创建 descriptor，不授予 `pk_authority` 或 `deterministic_fuze_authority`。

## Event Chain

| stage id | stage | input refs | research output | uncertainty class | forbidden interpretation | replacement rule |
|---|---|---|---|---|---|---|
| `G5EVT-001` | terminal geometry bucket | `G5SRC-006`, `G5SRC-007`, runtime event refs | aspect / closure / miss-distance bucket | source + model-form | not hit probability | 被 executed guidance / miss-distance benchmark packet 替换 |
| `G5EVT-002` | fuze proxy branch | `G5SRC-004`, `G5SRC-005` | fallback-compatible branch label | source + scope | not deterministic trigger | 被 admitted fuze evidence or stronger public source packet 替换 |
| `G5EVT-003` | mechanism-load coupling | `G5SRC-001`, `G4-R-B` packet | blast / fragment research axis reference | source + model-form | not real warhead row | 被 admitted mechanism-load row or updated G4-R-B packet 替换 |
| `G5EVT-004` | component response coupling | `G5SRC-002`, `G5SRC-003`, `G4-R-C` packet | component response label / curve-family ref | source + scope + model-form | not calibrated component probability | 被 independent fragility benchmark or updated G4-R-C packet 替换 |
| `G5EVT-005` | consequence proxy | `G5SRC-008`, runtime report surface | consequence class / non-probability score placeholder | model-form + scope | not Pk and not mission-kill claim | 被 maintained runtime contract or reviewed consequence schema 替换 |
| `G5EVT-006` | aggregate research proxy | `G5EVT-001..005` | ordered research label with uncertainty ledger refs | combined | not stock behavior | 被 G5-R integration packet or later authority task superseded |

## Flow Rules

- Each stage consumes only the previous stage output plus declared source refs.
- No stage may infer a probability value from an ordinal label.
- Fuze proxy branch labels must remain compatible with fallback / RNG-like runtime behavior.
- G4-R-B and G4-R-C outputs are dependencies, not kill-chain truth.
- Runtime consequence flags are observations / reports, not calibration targets.
- Any future numeric proxy score must include source ids, uncertainty class, confidence and replacement rule.

## Research Row Shape

```json
{
  "chain_id": "g5_research_chain_example",
  "profile": "research_candidate",
  "authority": {
    "pk_authority": false,
    "deterministic_fuze_authority": false,
    "stock_descriptor_created": false
  },
  "stages": [
    "G5EVT-001",
    "G5EVT-002",
    "G5EVT-003",
    "G5EVT-004",
    "G5EVT-005"
  ],
  "output": {
    "type": "non_authoritative_research_proxy",
    "value_type": "ordered_label_or_score_placeholder",
    "probability_claim": false
  },
  "uncertainty_refs": [
    "G5UNC-001",
    "G5UNC-002",
    "G5UNC-003"
  ],
  "replacement_rule": "supersede only with stronger scoped source packet or explicit authority task"
}
```

## Worker Packet

```md
status: pass
touched files:
- docs/task/air_combat/archive/a2_high_fidelity_damage_model/g5_research_event_chain_map_20260602.zh.md
commands/outcomes:
- pending integration validation
remaining paths:
- G5-R-D uncertainty / independence audit
behavior risks:
- ordered proxy label being read as Pk
- fuze proxy branch being read as deterministic trigger
integration notes:
- Feed this into the G5 audit and integration acceptance only.
research boundary confirmation:
- `pk_authority=false`
- `deterministic_fuze_authority=false`
- `stock_descriptor_created=false`
```
