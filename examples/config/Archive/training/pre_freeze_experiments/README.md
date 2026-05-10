# Pre-Freeze Training Experiment Archive

This directory keeps older execution-layer and model-architecture training configs that previously lived directly under `examples/config/training/`.

They are retained for provenance and comparison only. The maintained training surface is now:

- `examples/config/training/default_ppo.json`
- `examples/config/training/curriculum/`
- `examples/config/training/frozen/`

## Archived Groups

- `p2_*`
  - Takeoff, visual, stability, performance, smoke, and ablation experiments.
- `p3_*`
  - Takeoff-to-cruise full-visual/nav-v2 residual experiments.
- `p4_*`
  - Landing full-visual/ILS smoke experiments.
- `p5_*`
  - Takeoff-to-landing continuous smoke/retrain experiments.
- `takeoff_departure_full_visual_*`
  - Historical takeoff-departure residual controller-fix line.
- `transformer_*`
  - Early transformer policy/extractor scale experiments.

## Revival Rule

Do not point new docs, tests, or launch commands at this archive directly. Existing historical regression contracts may reference archived configs when the contract is intentionally preserving an old wrapper/control baseline. To revive one of these configs for active training, copy it into a maintained active directory, document the intended scenario pairing, and validate it against the current runtime/facade path.
