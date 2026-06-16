# PF-R5 Proximity Fuze Surrogate Validation Result

Status: `2026-06-16` PF-R5 focused matrix validation complete.

Validation decision: `pass_with_residuals`.

## Scope

- live missile / fuze runtime path;
- mechanism families: `blast_fragmentation` and `continuous_rod`;
- trigger radii: `7, 8, 10, 12, 16, 24, 35, 50 m`;
- initial lateral offsets: `-120..120 m`; initial vertical offsets: `-80..80 m`;
- final CSV, JSON, and one heatmap figure only.

## Findings

- The trigger-radius / actual-miss ratio clearly opens or closes the detection gate; small radii produce `target_not_detected` and no-load.
- The centerline no-load-aware expected detonation probability is monotonic non-decreasing with trigger radius.
- Initial lateral/vertical offsets have weaker effect because guidance compensates part of the geometry; actual miss distances fall between `6.58` and `8.33` m.
- Left/right lateral symmetry is not a failure criterion here: this sweeps launch initial conditions while guidance, target motion, and airframe orientation stay in the loop; pure fuze-geometry symmetry needs a fixed local-point harness.
- `continuous_rod` and `blast_fragmentation` share the detection gate but can diverge through mechanism coverage.
- This validation does not claim real fuze thresholds, real Pk, weapon-specific lethality, or deterministic fuze authority.

## Outputs

- CSV: `pf_r5_proximity_fuze_validation_20260616.csv`
- JSON: `pf_r5_proximity_fuze_validation_20260616.json`
- Heatmap: `pf_r5_proximity_fuze_validation_heatmaps_20260616.png`
