# `src/tools` Boundary

`tools/` houses development‑time utilities, diagnostic tools, and experimental verification entry points. Code here may call runtime APIs for probing, but does not constitute a maintained library API or training mainline.

## Allowed

- One‑shot diagnostic tools.
- Performance or parity probe entry points.
- Command‑line programs that assist development.

## Prohibited

- Reverse dependency from `runtime/facade`, `core/`, or `interfaces/python`.
- Defining a mainline component, system, model, or facade contract.
- Being part of a default training or simulation path.

## Subdirectory Conventions

- `experimental/`: Experimental tools not yet on the maintained mainline.

## Migration Notes

If a tool is to be promoted to the mainline, it should first be moved to the corresponding layer, accompanied by a freezing plan, tests, and a README boundary explanation.
