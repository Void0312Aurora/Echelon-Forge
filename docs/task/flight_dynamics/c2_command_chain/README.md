# C2 Command-Chain And Communications Subproject

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Status: `2026-05-17` actively advancing.

This subproject collects documents directly tied to the current
`MissionCommand / CommandLink / DataLink / ROE / naval command-chain`
workstream, so ongoing progress does not keep getting piled back into one
frozen analysis draft.

## Document Entry Points

- [frozen analysis baseline](c2_command_chain_realism_analysis_20260517.zh.md)
  - Preserves the defect analysis and non-overstatement framing captured on
    `2026-05-17`.
- [current progress checkpoint](c2_command_chain_progress_checkpoint_20260517.md)
  - Records what this round has already implemented, verified, and exposed on
    the mainline capability surface.
- [open-issues analysis](c2_command_chain_unresolved_issues_20260517.md)
  - Focuses on unresolved technical gaps, current boundaries, and next-round
    recommendations.

## Current Scope

This subproject currently focuses on:

1. Minimal executable semantics and authority unification for `MissionCommand`
   across the air and naval sides.
2. Minimal FIFO/latency/pending-queue semantics for `CommandLink`.
3. Control-boundary handling between `PilotAction` and `MissionCommand`.
4. Minimal `ROE / engagement authority` fields and runtime gates.
5. Minimal `DataLink` budget, priority, and observable congestion state.

This subproject is not trying to solve in one pass:

1. Full Link 16 / NPG / relay / ACK / retransmission behavior.
2. Full naval fire-control AI / CEC / engage-on-remote behavior.
3. Full naval tasking state machine and multi-ship formation doctrine.
4. Complete episode/json/schema redundancy elimination.

## Related Documents

- [naval simulation realism analysis](../naval/naval_realism_analysis_20260516.zh.md)
- [sensor and situational-awareness realism analysis](../sensor_situation/sensor_situation_realism_analysis_20260516.zh.md)
- [weapon-system and guidance-loop realism analysis](../weapon_guidance/weapon_guidance_realism_analysis_20260516.zh.md)
- [naval progress checkpoint](../../naval/naval_progress_checkpoint_20260517.md)

## Maintenance Rules

1. Frozen analysis stays in the original file; do not rewrite "what was true at
   the time" inside that record.
2. Current implementation progress goes into the `progress checkpoint`.
3. Still-open issues that affect the next scheduling round go into
   `unresolved issues`.
