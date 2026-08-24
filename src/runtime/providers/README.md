# Runtime Providers

`src/runtime/providers` is the native integration seam for admitted provider
catalogs and composition-root adapters. It binds concrete engine/model
implementations to the host-neutral lifecycle kernel in
`src/runtime/composition`.

This layer may depend on native engine ownership, abstract model interfaces,
components, models, and runtime contracts. It must not define a second
manifest resolver, bypass native admission, or place provider callbacks in the
simulation step hot path. Cordis and Node adapters remain separate host-side
layers and lower into the same native composition boundary.
