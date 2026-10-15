# Python binding registration order

Language:
- English canonical: `python_binding_registration_order.md`
- Chinese companion: [python_binding_registration_order.zh.md](python_binding_registration_order.zh.md)

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/python_binding_registration_order.md`
Owner: `architecture/python-bindings`
Last verified: `2026-10-10`

The diagnostic `ef_py` module and the production facade-only module share one
ordered registration spine in `bindings_runtime_detail.h`. This keeps the
nanobind DTO registration order in one source site.

Both modes register the same 16 maintained runtime DTO groups and the facade in
the same order. The diagnostic mode inserts `bind_runtime_engine(m)` after the
tasking-world DTO group and before the facade, preserving the existing raw
engine dependency position. The production mode omits that call.

The helper is an ordering contract, not a generic registration loop. New
runtime slices must be inserted deliberately and covered by the architecture
guard so type visibility and signature resolution cannot drift between build
modes.
