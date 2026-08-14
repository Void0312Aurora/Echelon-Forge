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

The `takeoff_departure_full_visual_*` and `transformer_*` groups no longer have
files on disk; see the retirement ledger below for how to read them back.

## Retired Files (2026-08-13)

A reference sweep over the whole repository removed the archived configs that no
maintained doc, test, contract, or tool pointed at. Recover any of them with
`git show 3ac600a6:examples/config/Archive/training/pre_freeze_experiments/<name>`:

- `p2_ablation_longrollout_earlystop_v1.json`
- `p2_ablation_vfboost_earlystop_v1.json`
- `p2_aggressive_adaptivekl_3090.json`
  - Its only consumer, `tools/archive/legacy_scripts/train_p2_aggressive.sh`, was
    retired by the same sweep; restore both together if that retirement is undone.
- `p2_aggressive_stageA_test.json`
- `p2_aggressive_stageB_test.json`
- `p2_diag_smoke_continue_v1.json`
- `p2_earlystop_smoke_v1.json`
- `p2_midrun_longroll_earlystop_v2.json`
- `p2_perf_smoke_novis.json`
- `p2_rewardbalance_smoke_v1.json`
- `p2_sop_switches_smoke_v1.json`
- `p2_stability_diagnostic_v1.json`
- `p2_stability_long_earlystop_v1.json`
- `p2_visual_aggressive_24env_safeadapt_v2.json`
- `p2_visual_aggressive_24env_v2.json`
- `p2_visual_aggressive_3090_smoke_v2.json`
- `p2_visual_aggressive_3090_v2.json`
- `p2_visual_aggressive_40env_smoke_v2.json`
- `p2_visual_aggressive_40env_v2.json`
- `p2_visual_perf_smoke.json`
- `p3_takeoff_to_cruise_full_visual_navv2_mixedmode_flyoverfocus_smoke_v1.json`
- `p3_takeoff_to_cruise_full_visual_navv2_residual_smoke_v1.json`
- `p3_takeoff_to_cruise_full_visual_navv2_residual_smoke_v2.json`
- `p3_takeoff_to_cruise_full_visual_navv2_residual_v1.json`
- `p5_takeoff_to_landing_full_visual_navv2_residual_smoke_v1.json`
- `p5_takeoff_to_landing_full_visual_navv2_residual_smoke_v2.json`
- `takeoff_departure_full_visual_adaptivekl_residual_v9_corridor_smoke.json`
- `takeoff_departure_full_visual_adaptivekl_residual_v9_corridor_train.json`
- `transformer_hardware_max.json`
- `transformer_large_scale.json`
- `transformer_ppo.json`

Four configs stay because maintained documents still resolve to them:
`p2_autopilot_residual_navv2_paramroute_turnaware_long_v1.json`,
`p3_takeoff_to_cruise_full_visual_navv2_multileg_smoke_v1.json`,
`p4_landing_full_visual_ils_smoke_v1.json`, and
`p5_takeoff_to_landing_full_visual_navv2_residual_smoke_v3.json` are linked from
`docs/reference_artifacts.md`, and the last one is also the
`execution_train_config` every archived leader config resolves to.

## Revival Rule

Do not point new docs, tests, or launch commands at this archive directly. Existing historical regression contracts may reference archived configs when the contract is intentionally preserving an old wrapper/control baseline. To revive one of these configs for active training, copy it into a maintained active directory, document the intended scenario pairing, and validate it against the current runtime/facade path.
