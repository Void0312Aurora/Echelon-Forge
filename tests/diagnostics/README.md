# Diagnostics README

`tests/diagnostics/` is reserved for temporary exploratory or debugging
checks. It is not a maintained home for stable pytest regressions.

Current status: no active pytest scripts live in this directory. The former
stable checks were promoted into capability-owned files:

- `tests/runtime/air_combat/test_diagnostics_probe_contracts.py`
- `tests/training/test_fire_timing_diagnostic_contracts.py`
- `tests/runtime/link/test_external_proxy_backend_contracts.py`
- `tests/runtime/bindings/test_lazy_binding_resolution.py`

When a diagnostic stabilizes into deterministic regression evidence, migrate it
to the owning test domain or encode it as a JSON contract. New files here should
be short-lived and should document the target promotion path before they land.
