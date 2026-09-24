# Scripted Agent Capability Evidence Matrix

- Document kind: review
- Lifecycle: maintained
- Date: 2026-09-25
- Owner: architecture/cross-domain-agency
- Scope: current evidence boundary for the independent scripted-agent line

This matrix is a reporting boundary. It does not promote a domain because a
model is registered, an action call succeeds, or a focused proxy test is green.
The final `playable` label requires the scenario, runtime, CLI, visualization,
reset/replay, authority, and report evidence named in the plan.

## Current domain matrix

| Domain | Registration | Current label | Evidence retained | Accepted claims | Deferred claims |
| --- | --- | --- | --- | --- | --- |
| Air | `air.execution.phase_scripted` (`maintained`, `autopilot_controller`); `air.engagement.c2_roe_scripted` (`adapter`, `air_tactical_engagement_controller`) | `playable_candidate` | `python/tasking_contracts/air_scripted_execution.py`; `python/tasking_contracts/air_scripted_engagement.py`; neutral lifecycle and manifest-resolution tests; runway-geometry correction tests; leader adapter; task-eval and manifest-driven viz route tests; direct static and randomized full single-world successes plus full same-process randomized reset/replay recorded in the plan ledger; bounded cooperative roster trace with Lead/Wing roles; direct Stage 1 C2/ROE hybrid scenario probe with accepted scripted fire and native release | takeoff, stable-flight, and landing controller composition through a neutral lifecycle; no-RL model construction path; manifest-driven compiled single-world route; complete single-world mission success under one static and one randomized seed; exact full reset/replay for the tested randomized seed; tactical model emits radar/TMS/master-arm/fire request fields only from declared C2/ROE observation fields; the maintained hybrid Air combat scenario consumes the adapter and reports `fire_once_requested`, `fire_once_accepted`, and `release_executed`; cooperative runtime routes two active roster members with distinct takeoff clearance segments | command/report episode closure; accepted seed coverage; visualization process/render acceptance; complete tactical engagement success and post-launch assessment; EW/EMCON and data-link constraints; multi-unit mission/formation parity; joint tasking; large-scale demonstration |
| Naval | `naval.station.screen_hold` (`adapter`, `naval_warfare_commander`) | `bounded_adapter` | `python/tasking_contracts/naval_scripted_execution.py`; scoped `naval_station_policy_eval.py`; N4 station surface and manifest-resolution tests; direct eight-step report recorded in the plan ledger | zero station-order baseline can enter the common scripted lifecycle while the naval scenario runtime owns contact, station geometry, reporting, recovery, and reward; manifest-driven route; required terms and forbidden-term checks passed in the bounded report | fleet combat, weapon employment, general naval maneuver policy, reset/replay, full naval playable label |
| Ground | no scripted model registration | `held` | `scenarios/ground/*`; native G1 static schema and realism-gradient guardrails | static task/status shell and explicit deferred claims | movement, terrain interaction, sensing/track export, fires, effects, damage, and playable runtime |

## Label rules

The following labels are intentionally ordered by evidence strength:

- `held`: runtime capability or required owner is absent; no playable claim is
  allowed.
- `bounded_adapter`: a maintained domain path can consume the common lifecycle,
  but the adapter delegates domain semantics to an existing scoped runtime.
- `playable_candidate`: the domain has an independent scripted producer and a
  concrete vertical path, but one or more final runtime/entry-point gates are
  open.
- `playable`: only after the promotion gate in
  `cross_domain_scripted_agent_system_plan.md` is satisfied and the evidence
  bundle names the exact scenario, commit, test, CLI, visualization, and
  replay records.

RL participation is orthogonal to these labels. A learned or RL adapter may
  consume the same neutral contracts after the scripted path is accepted; its
  presence cannot raise a label.

## Required machine-readable manifest shape

The scenario-manifest slice now attaches an additive object to three
representative maintained entry points. The keys below are the minimum review
shape;
the object must preserve domain-owned payloads rather than flattening them into
a mega-schema:

```json
{
  "scripted_capability": {
    "version": "scripted_capability.v1",
    "domain": "air",
    "label": "playable_candidate",
    "model_id": "air.execution.phase_scripted",
    "role_id": "autopilot_controller",
    "lifecycle": "reset_decide_close",
    "evidence_refs": [
      "commit:...",
      "test:...",
      "scenario:...",
      "cli:...",
      "viz:...",
      "replay:..."
    ],
    "deferred_claims": []
  }
}
```

`evidence_refs` are references, not proof by themselves. The evidence bundle
must still be inspected, and proxy evidence must remain marked as proxy.
The dependency-light parser in
`python/tasking_contracts/scripted_capability.py` validates this shape; it does
not grant runtime admission and is not yet wired into the scenario loader.

## Open acceptance gates

1. Air: static single-world completion and one full randomized reset/replay
   gate are satisfied; close the neutral command/report chain first, then add
   accepted seed coverage and visualization process/render evidence.
2. Air tactical/EW: admit sensor/track-based engagement and EW roles only with
   declared information provenance, ROE/resource constraints, and negative
   tests for privileged geometry or hidden truth.
3. Air multi-unit: route two or more active-roster members through the existing
   world-batch runtime and preserve authority/provenance boundaries, then extend
   to joint tasking and the large-scale demonstration.
4. Naval: keep the N4 station adapter scoped; the direct runtime report gate is
   satisfied, while combat, fleet, reset/replay, and full playable coverage
   remain open.
5. Ground: leave the label `held` until every deferred runtime owner is
   admitted with evidence.
6. All domains: attach the manifest object to maintained scenarios and reports
   only after the corresponding gate passes.
