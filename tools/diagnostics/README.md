# Tools Diagnostics README

`tools/diagnostics/` contains ad hoc operator-facing scripts used for investigation and matrix-style sanity checks.

These scripts are intentionally separate from the top-level `tools/` entrypoints because they usually:

- run one-off exploratory sweeps
- depend on local model/checkpoint availability
- print human-oriented summaries instead of stable machine-checked assertions
- help diagnose failures rather than serve as maintained core workflows

Current examples:

- [diagnose_training_matrix.py](/home/void0312/CMO/tools/diagnostics/diagnose_training_matrix.py)
  - Runs a small evaluation matrix across model/scenario pairs and extracts headline metrics from evaluator output.
- [sanity_check.py](/home/void0312/CMO/tools/diagnostics/sanity_check.py)
  - Performs a low-level kernel/API sanity probe against a spawned unit.
