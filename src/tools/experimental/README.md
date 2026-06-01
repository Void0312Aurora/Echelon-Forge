# `src/tools/experimental` Boundary

`tools/experimental` stores experimental C++ probes and one-off tools. Code here is not part of the maintained runtime/tooling surface.

## Allowed

- Phase probes.
- Parity or performance exploration tools.
- Temporary diagnostic entry points.

## Prohibited

- Default training or runtime paths.
- Dependencies from core library code.
- Migration to a maintained API without a freezing plan.

## Migration Notes

Experimental tools that need long-term retention should first determine their target layer: GPU helpers go into `gpu/`, runtime APIs go into `runtime/facade`, Python exposure goes into `interfaces/python`.
