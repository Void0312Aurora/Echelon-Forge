# Kill-Chain Guidance Mechanism Review - 2026-07-15

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/systems/weapons/reviews/kill_chain_guidance_mechanism_20260715/README.md`
Owner: `systems/weapons/reviews`
Last verified: `2026-09-13`
Review basis: retained guidance-calibration note and the complete `2026-07-15`
five-stage mechanism, envelope, and scalar-calibration packet sequence.

## Scope

This package preserves bounded diagnostics for guidance/mechanism attribution in
the repository's AIM-120C-like engineering proxy. The source experiments are
simulation evidence, not real missile-performance measurements.

## Retained Evidence

- [Guidance and lethality calibration note](kill_chain_guidance_lethality_calibration_20260621.zh.md)
- [Mechanism-ablation conclusions](review_packets/kill_chain_guidance_mechanism_ablation_20260715/kill_chain_guidance_mechanism_ablation_conclusions_20260715.md)
- [Exact-mechanism conclusions](review_packets/kill_chain_guidance_exact_mechanism_ablation_20260715/kill_chain_guidance_exact_mechanism_ablation_conclusions_20260715.md)
- [World LOS-history PN validation](review_packets/kill_chain_world_pn_production_validation_20260715/world_pn_production_validation.zh.md)
- [World-frame CV tracker validation](review_packets/kill_chain_world_cv_tracker_validation_20260715/world_cv_tracker_validation.zh.md)
- [Capture-structure ablation](review_packets/kill_chain_capture_structure_ablation_20260715/kill_chain_capture_structure_ablation_conclusions_20260715.zh.md)
- [Corrected continuous envelope](review_packets/kill_chain_guidance_envelope_rebuild_20260715/kill_chain_guidance_envelope_rebuild_20260715_conclusions.zh.md)
- [Constrained scalar calibration](review_packets/kill_chain_guidance_scalar_calibration_20260715/kill_chain_guidance_scalar_calibration_20260715_conclusions.zh.md)
- [Stage-4/5 heatmap evidence](review_packets/kill_chain_guidance_calibration_visualization_20260715/kill_chain_guidance_calibration_visualization_summary_20260715.md)

## Verdict And Limitations

Accepted as retained diagnostic evidence. The sequence retains `nav_gain=4`
and holds default promotion because maneuver-target/APN authority is absent.
It does not establish real AIM-120C guidance, fuze, lethality, or Pk authority
and does not authorize descriptor or default-runtime retuning. Further
experiments must open a separate owner-local package.
