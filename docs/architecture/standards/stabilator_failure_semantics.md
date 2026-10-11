# Stabilator Failure Semantics

Language:
- English canonical: `stabilator_failure_semantics.md`
- Chinese companion: [stabilator_failure_semantics.zh.md](stabilator_failure_semantics.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/stabilator_failure_semantics.md`
Owner: `architecture/air-damage`
Last verified: `2026-10-10`

Aircraft damage content distinguishes control actuation from the lifting
surface and its structural support.

## Runtime rules

- `*_stabilator_actuator` is a control-linkage receiver. Its loss can reduce
  control authority through the ordinary aircraft damage projection, but it is
  never a direct `TailLeft` or `TailRight` detachment trigger.
- `*_stabilator_surface` is a structural lifting-surface receiver. A
  structurally damaging failure at the maintained threshold can create the
  corresponding tail detachment group.
- `*_stabilator_hinge` is a structural support receiver. A structurally
  damaging failure can create the corresponding detachment group when that
  receiver is present.
- Legacy `*_horizontal_tail_actuator_or_surface_component` names remain a
  compatibility path. They are treated as structural only when their primary
  failure mode is structurally damaging; a pure hydraulic or control failure
  remains non-detaching.

The current F-16C example content uses the separate surface receiver names.
The split is a semantic ownership correction, not a claim that the synthetic
proxy geometry is an authoritative aircraft engineering model.

The native regression suite covers actuator-only negative behavior, surface
structural positive behavior, legacy compatibility, and F-16C content loading.
