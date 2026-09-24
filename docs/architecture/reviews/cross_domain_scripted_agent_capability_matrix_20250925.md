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
| Air | `air.execution.phase_scripted` (`maintained`, `autopilot_controller`) | `playable_candidate` | `python/tasking_contracts/air_scripted_execution.py`; neutral lifecycle tests; leader adapter; task-eval and viz route tests | takeoff, stable-flight, and landing controller composition through a neutral lifecycle; no-RL model construction path | scenario command/report roundtrip, compiled facade execution, full reset/replay, CLI and visualization runtime acceptance, multi-unit roster parity |
| Naval | `naval.station.screen_hold` (`adapter`, `naval_warfare_commander`) | `bounded_adapter` | `python/tasking_contracts/naval_scripted_execution.py`; scoped `naval_station_policy_eval.py`; N4 station surface tests | zero station-order baseline can enter the common scripted lifecycle while the naval scenario runtime owns contact, station geometry, reporting, recovery, and reward | fleet combat, weapon employment, general naval maneuver policy, full naval playable label |
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

1. Air: run a compatible local `ef_py` build, then exercise the maintained
   single-world scenario through the neutral model, command/report chain,
   reset/replay, CLI, and visualization process.
2. Air multi-unit: route two or more active-roster members through the existing
   world-batch runtime and preserve authority/provenance boundaries.
3. Naval: keep the N4 station adapter scoped and produce a real runtime report;
   do not infer combat or fleet coverage from it.
4. Ground: leave the label `held` until every deferred runtime owner is
   admitted with evidence.
5. All domains: attach the manifest object to maintained scenarios and reports
   only after the corresponding gate passes.
