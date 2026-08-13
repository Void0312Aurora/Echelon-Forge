# A2 MLF-5 Target Component Vulnerability And Failure

Status: `2026-06-11` archived pointer. The accepted MLF-5 evidence package was
moved to
archive/mlf_5_component_failure_accepted_20260611 (`git show 77610218:docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure/archive/mlf_5_component_failure_accepted_20260611/README.md`).

Language:

- Chinese main text: [README.zh.md](README.zh.md)
- English companion: `README.md`

This path is retained only as the navigation entry for the completed fifth
stage. MLF-5 closes the target component vulnerability and failure fact chain:
post-detonation component-load / cut-exposure facts can produce same-chain
component damage facts with component name, system, redundancy group, failure
probability, random sample, failure mode, severity, before/after integrity, and
diagnostic summaries.

MLF-5 does not decide whether an aircraft crashes, create structural breakup or
wreck/debris, compute Pk, or calibrate real AIM-120C/MQ-9 or other
weapon/target-specific lethality. Component state changes are handed to the
maintained damage, flight-dynamics, propulsion, and sensor systems.

Current archived evidence package:
`git show 77610218:docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure/archive/mlf_5_component_failure_accepted_20260611/README.md`.

Follow-on work that turns component failure into structural breakup,
wreck/debris lifecycle, Pk, or weapon-specific calibration must create a
separate `docs/agent` subproject instead of adding rules inside this completed
MLF-5 subproject.

Reusable conclusion: the system can now explain which component was damaged,
why, what the probability/sample said, and how the component state changed,
then hand that state to maintained systems. Those facts still do not directly
claim fragmentation, crash, or kill.
