# Proximity Fuze Surrogate Contract

Status: `2026-06-16` PF-R3 pass / PF-R4 implemented as focused runtime
evidence. This file remains the design contract; implementation evidence is in
[proximity_fuze_runtime_implementation_20260616.md](proximity_fuze_runtime_implementation_20260616.md).

Chinese companion: [proximity_fuze_surrogate_contract_20260616.zh.md](proximity_fuze_surrogate_contract_20260616.zh.md).

## Contract Boundary

This contract defines the behavior shape and validation expectations for a
non-authoritative surrogate. It does not release deterministic fuze authority,
Pk, or weapon-specific lethality.

## Desired Chain

```text
nearest_approach
  -> fuze_sensor_opportunity
  -> fuze_detection
  -> fuze_trigger_decision
  -> detonation_solution
  -> warhead_mechanism_coverage
  -> effects or no-load event
```

The key change is that nearest approach stays diagnostic. It should no longer be
the sole owner of fuze trigger or detonation geometry.

## Proposed Event/Field Contract

| Stage | Required facts | Failure reasons | Notes |
| --- | --- | --- | --- |
| `nearest_approach` | time, local point, center miss distance, closure, aspect bucket | none; observed event | Existing event can be retained. |
| `fuze_sensor_opportunity` | sensor family, candidate target surface/projection distance, range-window score, crossing state, terminal-track state | `outside_sensor_window`, `no_terminal_track`, `invalid_closing_state` | New logical stage; can initially be embedded in fuze event fields if schema churn is deferred. |
| `fuze_detection` | detected flag, target signature source, signature value, signature scale, detection confidence | `target_not_detected`, `signature_below_threshold`, `countermeasure_or_clutter_proxy` | Should occur before trigger probability. |
| `fuze_trigger_decision` | armed, trigger candidate, trigger probability, sample, reliability, reason | `fuze_no_detonation`, `trigger_probability_failed`, `safety_or_arm_blocked` | Existing fuze event can be extended. |
| `detonation_solution` | source, detonation time, local/world point, delay, delay source, missile axis, projected burst point | `no_valid_burst_solution` | For proximity, source should not default silently to nearest point. |
| `warhead_mechanism_coverage` | mechanism family, coverage score, range term, aspect/incidence term, vulnerable-region proxy, component candidate count | `mechanism_coverage_failed` | Blast-fragmentation and continuous rod must diverge here. |
| `effects` | existing effects fields and no-load invariant | existing outcome state | No detonation must still produce no positive load facts. |

## Minimum Surrogate Rules

1. Preserve existing contact and timed behavior.
2. Preserve no-detonation no-load behavior.
3. For proximity fuzes, compute a sensor opportunity before final trigger.
4. Treat target signature as detection evidence, not only as reliability scale.
5. Use closure/crossing state to decide whether delay and burst geometry are
   plausible.
6. Compute or name the detonation-point source:
   - `nearest_point_fallback`
   - `sensor_window_delay_solution`
   - `surface_projection_solution`
   - `debug_profiled_local_point`
   - `timed_fuze`
   - `contact_surface`
7. Split mechanism coverage:
   - blast-fragmentation: distance, exposed area/projection, incidence, fragment
     density proxy;
   - continuous rod: lateral sweep band, missile-axis relationship, cut margin,
     component crossing proxy.
8. Keep all numeric constants labeled as surrogate parameters, not real missile
   data.

## Focused Validation Plan

Documentation-only validation for this contract:

```bash
git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_proximity_fuze_realism
```

Implementation validation used by PF-R4:

```bash
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/runtime/air_combat/weapon_guidance_realism/test_launch_guidance_and_dynamics.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/runtime/air_combat/test_continuous_rod_surface.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py tests/runtime/air_combat/test_diagnostics_process_probe_summary.py
```

Additional focused cases required after implementation:

- Outside sensor window: near center distance is not enough to trigger.
- Detection but no trigger: target detected but trigger probability or burst
  solution fails.
- Trigger with delay: detonation point is not silently nearest point.
- High/low pass: height changes the opportunity and coverage score.
- Beam/nose/tail symmetry: symmetric geometry gives symmetric matrices where
  expected.
- Blast-fragmentation versus continuous rod: same approach can diverge by
  mechanism coverage.
- No detonation: no positive fragment, blast, or rod load facts.

## Implementation Write-Set Proposal

Implemented in PF-R4:

- `src/systems/combat/damage_system_common.h`
- Python bindings for new public event fields.
- Focused runtime tests under `tests/runtime/air_combat/weapon_guidance_realism/`.
- Diagnostic exporters after runtime fields exist.

Not part of the first implementation wave:

- Training reward changes.
- Default F-16 proxy database replacement.
- Scenario balance.
- Pk or authority promotion.
- Real weapon calibration.

## Acceptance Shape

The first implementation wave should be accepted only if it makes the chain more
explainable. A lower or higher damage probability is not itself acceptance
evidence. The accepted evidence must show why the fuze detected, did not detect,
triggered, failed, delayed, chose a burst point, and then produced or refused
mechanism load.
