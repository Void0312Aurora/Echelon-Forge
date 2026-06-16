# Runtime Tests

`tests/runtime/` is organized by capability domain:

- `air_combat/`
- `bindings/`
- `core/`
- `engagement/`
- `execution/`
- `facade/`
- `ground/`
- `link/`
- `mission/`
- `multi_agent/`
- `naval/`
- `navigation/`

`ground/` currently covers MVP scenario, native platform-schema, and
realism-gradient bootstrap guardrails; `mission/` also carries the ground
tasking/lifecycle bridge dispatch tests. Movement, terrain, sensing, fires,
damage, and full ground runtime behavior remain held. `naval/` includes the
accepted `N4` pre-fire/tasking/contact reward surface alongside ship database,
sensor, ASW-helo, station-command, and legacy movement debug checks; `N4`
training entries still exclude weapon release, damage, and kill rewards.

Keep new runtime regressions in the smallest matching subdomain. Reserve the
root only for temporary migration helpers.

Common entry points:

```bash
cmo_python -m pytest -q tests/runtime/core/test_env_config.py
cmo_python -m pytest -q tests/runtime/engagement
cmo_python -m pytest -q tests/runtime/facade/test_runtime_facade_core.py
cmo_python -m pytest -q tests/runtime/facade/test_runtime_facade_counterfactual.py
```

The maintained repository smoke boundary is defined separately in
`tests/smoke/ci_smoke_suite.json` and should be invoked through
`tools/runners/run_pytest_suite.py` rather than by copying file paths into CI,
docs, or ad hoc LLM instructions.
