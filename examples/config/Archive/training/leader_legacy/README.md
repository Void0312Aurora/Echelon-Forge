# Leader Legacy Training Configs

This directory archives pre-freeze leader-layer training configs that were previously kept at the top level of `examples/config/training/`.

- Scope: historical `p6_*` and `p7_*` leader experiments.
- Status: archived; retained for provenance and result lookup only.
- Maintained baseline: [examples/config/training/frozen](../../../training/frozen/README.md)

These files may still reference historical naming and older experiment intent. Internal execution-config references are kept repo-relative to the archived pre-freeze config location so the archive remains inspectable. New training runs should start from the frozen configs, not from this archive.

## Retired Files (2026-08-13)

A reference sweep over the whole repository removed the archived configs that no
maintained doc, test, contract, or tool pointed at. Recover any of them with
`git show 3ac600a6:examples/config/Archive/training/leader_legacy/<name>`:

- `p6_leader_layer_frozen_exec_smoke_v1.json`
- `p7_leader_layer_c2_reporting_baseline_v1.json`
- `p7_leader_layer_c2_reporting_generalization_batched_gpu_v1.json`
- `p7_leader_layer_c2_reporting_generalization_highcpu_v1.json`
- `p7_leader_layer_c2_task_chain_baseline_v1.json`
- `p7_leader_layer_c2_task_chain_earlystop_v1.json`
- `p7_leader_layer_c2_task_chain_fasttrack_v1.json`

The remaining configs are kept because something outside the archive still names
them: `p6_leader_layer_frozen_exec_generalization_v1.json`,
`p7_leader_layer_c2_reporting_generalization_v1.json`, and
`p7_leader_layer_c2_reporting_generalization_fast_v2.json` are lineage links in
`examples/config/training/frozen/README.md`; `p6_leader_layer_smoke_v1.json`,
`p7_leader_layer_c2_reporting_smoke_v1.json`, and
`p7_leader_layer_c2_reporting_generalization_fast_v1.json` are cited by archived
rearchitecture notes and `tools/README.md`.
