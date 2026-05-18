# C2 Command-Chain And Communications Analysis

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Status: `2026-05-17` analysis baseline retained; the current framing comes from the analysis closure marker, not `program/` or `archive/`.

This subtree keeps the frozen analysis baseline for the
`MissionCommand / CommandLink / DataLink / ROE / naval command-chain`
workstream.

## Document Entry Points

- [frozen analysis baseline](c2_command_chain_realism_analysis_20260517.zh.md)
  - Preserves the defect analysis and non-overstatement framing captured on
    `2026-05-17`.
## Analysis Scope

This analysis currently focuses on:

1. Minimal executable semantics and authority unification for `MissionCommand`
   across the air and naval sides.
2. Minimal FIFO/latency/pending-queue semantics for `CommandLink`.
3. Control-boundary handling between `PilotAction` and `MissionCommand`.
4. Minimal `ROE / engagement authority` fields and runtime gates.
5. Minimal `DataLink` budget, priority, and observable congestion state.

This analysis is not trying to solve in one pass:

1. Full Link 16 / NPG / relay / ACK / retransmission behavior.
2. Full naval fire-control AI / CEC / engage-on-remote behavior.
3. Full naval tasking state machine and multi-ship formation doctrine.
4. Complete episode/json/schema redundancy elimination.

## Related Documents

- [naval simulation realism analysis](../naval/naval_realism_analysis_20260516.zh.md)
- [sensor and situational-awareness realism analysis](../sensor_situation/sensor_situation_realism_analysis_20260516.zh.md)
- [weapon-system and guidance-loop realism analysis](../weapon_guidance/weapon_guidance_realism_analysis_20260516.zh.md)

## Maintenance Rules

1. Frozen analysis stays in the original file; do not rewrite "what was true at
   the time" inside that record.
2. Current state only comes from the closure marker in this analysis.
3. If a new status snapshot is needed later, create a fresh document instead of
   rewriting this frozen analysis.
