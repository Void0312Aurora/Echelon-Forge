# Echelon Forge Cordis Runtime Package

This package contains the accepted P2-C1 producer seam and the accepted bounded
P6-A package-maturation surface. It uses Cordis `Context`, plugin, event, service,
injection, effect, and fiber-disposal primitives to lower the repository-owned
`builtin.default_compatibility` package into the frozen
`RuntimeCompositionRequest`.

The P6-A surface adds strict versioned schemas and public SDK helpers for:

- repository-owned package and configuration-overlay definitions;
- deterministic dependency resolution with missing-dependency and cycle
  rejection;
- raw-byte pins for the profile module, profile bundle, overlays, and exact
  Cordis version/package lock;
- canonical package provenance bound to request, catalog lock, and profile
  projection identities;
- stable path-free diagnostics for the native-validation handoff.

The package descriptor never owns providers, backend selection, component
contributions, or system order. Those remain in owner-admitted repository
artifacts and the native validator. The only admitted overlay in this bounded
slice restates the frozen default configuration; a truth-changing overlay is
rejected because it no longer matches the admitted request/catalog-lock
identity. Broader configurable profiles remain a later admission slice.

```text
npm install
npm test
npm run produce -- --out build/default-profile
```

The CLI additionally emits `runtime_package_provenance.v1.json` and
`runtime_package_diagnostics.v1.json`, while retaining the existing request,
lock, authority, projection, requested/resolved manifest, and metadata files.
Import the supported SDK from `@echelon-forge/cordis-runtime`; package contracts
and repository-owned definitions are exposed through explicit subpath exports.

Unknown profiles, unpinned bytes, dependency cycles, overlay conflicts, altered
configuration, and missing catalog-lock artifacts fail before native handoff.
External package signing, arbitrary third-party plugins, broader profiles,
Node hosting, CUDA parity, and simulation stepping in JavaScript remain outside
this bounded slice.
