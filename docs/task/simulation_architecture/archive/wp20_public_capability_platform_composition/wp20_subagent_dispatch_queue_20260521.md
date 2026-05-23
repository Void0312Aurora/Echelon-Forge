# WP20 Subagent Dispatch Queue

Status: `2026-05-21` closed / accepted.

Language:

- English canonical: `wp20_subagent_dispatch_queue_20260521.md`
- Chinese companion:
  [wp20_subagent_dispatch_queue_20260521.zh.md](wp20_subagent_dispatch_queue_20260521.zh.md)

Inputs:

- [WP20 main plan](public_capability_platform_composition_wp20_20260521.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Queue

| Stream | Dependency | Dispatch status | Write scope |
|--------|------------|-----------------|-------------|
| `WP20-A Public Capability Fact Ledger` | none | pass | Docs only: fact ledger. Read-only source/test inventory. |
| `WP20-B Public Typed Platform Spawn Contract` | A may refine, but not blocking | focused pass | Contract/result DTOs and focused architecture tests. No runtime materialization. |
| `WP20-E Compatibility And Schema Guard` | A may refine, but not blocking | pass | Architecture/schema/compatibility tests. No runtime behavior edits. |
| `WP20-C Runtime Setup Consume Bridge` | B contract | accepted / focused pass | Runtime/facade setup consume path and runtime/facade tests. |
| `WP20-D Facade And Binding Public Surface` | B and C | accepted / focused pass | Python/facade binding exposure and binding tests. |
| `WP20-F Integration And Handoff` | A-E | complete / accepted | Integration, validation rollup, residuals, indexes, acceptance review. |

## First-Wave Dispatch

| Stream | Suggested model / reasoning | Dispatch packet |
|--------|-----------------------------|-----------------|
| `WP20-A` | `gpt-5.4-mini`, xhigh | Produce source-backed fact ledger; edit only the A cluster docs if needed. |
| `WP20-B` | `gpt-5.4`, xhigh | Implement/add public result/admission contract and focused tests; do not edit runtime materialization. |
| `WP20-E` | `gpt-5.4`, high | Update guards from WP14 additive-only to WP20 validation-first publicization; do not edit runtime behavior. |

## Second-Wave Dispatch

| Stream | Suggested model / reasoning | Dispatch packet |
|--------|-----------------------------|-----------------|
| `WP20-C` | `gpt-5.4`, xhigh | Returned by Bernoulli and accepted after focused validation. It consumed typed setup requests through the B contract in runtime/facade setup and did not edit bindings. |
| `WP20-D` | `gpt-5.4`, high | Returned by Lovelace and accepted after focused validation. It exposed `TypedPlatformSpawnResult` and `BatchWorldSetupResult.typed_platform_spawn_results` through Python bindings without changing runtime materialization semantics. |

## Closure-Wave Dispatch

| Stream | Suggested model / reasoning | Dispatch packet |
|--------|-----------------------------|-----------------|
| `WP20-F` | `gpt-5.4-mini`, xhigh | Closed. Integrate A-E evidence, run validation rollup, record residuals, sync README/index status, and draft acceptance review. Do not change implementation semantics. |

## Worker Return Packet

Every worker must return:

- status: `pass`, `blocked`, or `preflight-only`;
- touched files;
- validation commands and outcomes;
- blockers and residuals;
- integration notes for the next stream;
- confirmation that unrelated edits were not reverted.

## Stop Rules

- Do not remove or deprecate `spawn_unit(type_name)` or `WorldSpawnRequest.type_name`.
- Do not force scenario JSON, examples, or Python callers to migrate.
- Do not move platform capability semantics into backend `RuntimeCapabilities`.
- Do not add new tactical behavior.
- Stop at a named blocker instead of broadening into WP21.
