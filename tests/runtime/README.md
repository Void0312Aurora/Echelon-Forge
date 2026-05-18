# Runtime Tests

`tests/runtime/` is organized by capability domain:

- `air_combat/`
- `bindings/`
- `core/`
- `execution/`
- `facade/`
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
cmo_python -m pytest -q tests/runtime/facade/test_runtime_facade.py
```
