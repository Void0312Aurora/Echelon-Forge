<!-- Machine-translated draft generated on 2026-05-18 from src/interfaces/README.md. Review before treating this file as authoritative. -->

# `src/interfaces` Boundary

`interfaces/` holds external language, tooling, or integration boundaries. It is responsible for exposing the maintained C++ API and does not own simulation, mission, or model domain logic.

## Allowed

- Language bindings.
- External ABI/API adaptation.
- Lightweight type conversion and error mapping.
- Small helpers that serve only the bindings.

## Disallowed

- Mission-command JSON business interpretation.
- Reward, termination, episode transition, or physics behavior.
- Direct implementation of runtime capability.
- Injecting training configuration or scenario semantics into the binding layer.

## Subdirectory conventions

- `python/`: nanobind Python module and Python‑related adaptations.

## Migration notes

It may be considered later to rename `interfaces/python` to `bindings/python`. Before the rename, new bindings should still be placed under `interfaces/python`, but must adhere to the "binding only, no domain logic" principle.
