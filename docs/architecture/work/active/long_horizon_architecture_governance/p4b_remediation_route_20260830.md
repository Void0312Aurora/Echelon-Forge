# P4-B Remediation Route: Provenance And Durable Transfer

Status: `2026-08-30` planning artifact; P4-B remains `repair-required`.

## Objective

Close caller-forgeable owner provenance and non-durable import transactions.
This route is long-horizon; fixture compatibility is evidence only.

## Work packages

1. **Host-issued owner capability**: construct owners behind a host-owned
   admission factory; return an opaque single-use handle bound to host boot
   identity, slot incarnation, resource identity, generation and authenticator;
   reject copied, replayed, cross-host, cross-slot and post-reclaim handles.
2. **Durable import transaction**: replace synchronous `void noexcept` hooks with
   monotonic status, deadline, cancellation, idempotent commit/abort and
   interruption recovery; persist pre-mutation and terminal records; quarantine
   ambiguous records fail-closed.
3. **Typed decoder and replay matrix**: maintain exporter/importer pairs for all
   twelve categories with exact N/N-1 behavior, unknown-field policy, migration
   hashes, replay vectors and rollback semantics.
4. **Acceptance**: review independently after each work package; require native,
   Python, boundary, interruption-recovery and replay evidence. P4-C remains
   dark/shadow and P5 durability/authenticity/canary gates remain separate.

## Non-goals and exit criteria

No caller migration, production publication, rebuild retirement, multi-world
enablement or fixture-only reduction is authorized. Accept only when handles are
host-authenticated, transactions have durable terminal state and recovery, all
decoders pass compatibility/replay, and review finds no Critical/High blocker.
