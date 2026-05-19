# Runtime Tests

`tests/runtime/` is organized by capability domain:

- `air_combat/`
- `bindings/`
- `core/`
- `execution/`
- `facade/`
- `engagement/`
- `link/`
- `mission/`
- `multi_agent/`
- `naval/`
- `navigation/`

Keep new runtime regressions in the smallest matching subdomain. Reserve the
root only for temporary migration helpers.

Common entry points:

```bash
cmo_python -m pytest -q tests/runtime/core/test_env_config.py
cmo_python -m pytest -q tests/runtime/engagement
cmo_python -m pytest -q tests/runtime/facade/test_runtime_facade.py
```

The maintained repository smoke boundary is defined separately in
`tests/smoke/ci_smoke_suite.json` and should be invoked through
`tools/runners/run_pytest_suite.py` rather than by copying file paths into CI,
docs, or ad hoc LLM instructions.
