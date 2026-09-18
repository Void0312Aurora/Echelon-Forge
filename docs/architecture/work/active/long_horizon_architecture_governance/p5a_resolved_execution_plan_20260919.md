# P5-A Resolved Execution Plan Evidence

Status: `2026-09-19` accepted for the current in-process, default CPU-exact
supported topology. This packet does not authorize production cutover and does
not close P5-B, P5-C, P5-D, or the P8 acceptance clusters.

## Delivered Contract

P5-A now has one generated `echelon_forge.resolved_execution_plan.v1` artifact
that binds the request, admitted catalog lock, profile projection, backend
request, requested manifest, and resolved manifest. The plan carries the
owner-derived backend join, canonical input digests, a typed authority envelope,
and the generated native header used by the default native constructor.

The Python maintenance generator and Cordis producer build the same canonical
bytes and plan digest. Native admission verifies the embedded owner inputs and
their joins, including the unique admitted backend lock entry, rather than
trusting only a resealed wrapper. The default `SimulationKernel()` path first
admits the closed plan and extracts its resolved manifest. The explicit
manifest constructor remains a compatibility/test input path.

The legacy resolved-manifest authority remains input-only compatibility data;
the new plan is the runtime interchange for this accepted topology. Durable
RunReceipt/ledger storage, installed facade packaging, and production caller
activation remain later-phase responsibilities.

## Sealed Artifact

- Fixture: `tests/architecture/composition/fixtures/default_resolved_execution_plan.v1.json`
- Schema: `src/runtime/contracts/composition/resolved_execution_plan.v1.schema.json`
- Native generated header: `src/runtime/contracts/composition/resolved_execution_plan.v1.generated.h`
- Plan SHA-256: `505df883b8cb08dcbbedbcb2fb2a2cffb3c27eb386e76476cbc1efc7f99a3b18`
- Migration-closure SHA-256 after the new default entry point: `390db92a45b5d923f33b09a1e1a4026d17a1019e826c3ffceb6998d24f476bb6`

## Verification

- Python composition set: `54 passed, 2 warnings`.
- Cordis package tests: `27 passed, 0 failed`.
- Cordis producer to native conformance: passed; native output reported `providers=11`, `production_generation=1`.
- Native authority contract test: `8 test cases, 36 assertions, all passed`.
- Focused CTest: `runtime_authority_contract` and `cordis_runtime_conformance`, `2/2 passed`.
- P8-A migration-closure suite: `13 passed`.
- Default-kernel smoke and provider rollback tests passed on the refreshed `build-long-horizon-p4c` tree.

Negative coverage includes stale owner joins, backend implementation-version
substitution, stale profile projection, wrapper resealing after catalog-lock
mutation, noncanonical JSON/BOM/numeric forms, authority-envelope mismatch,
and Cordis/native byte mismatch.

## Remaining Work

P5-B must qualify a durable ArtifactLedger and emit complete versioned
`RunReceipt` evidence before any production activation. P5-C must establish the
facade-only package and supported build/binding boundary. P5-D must then own the
single canary decision, caller migration, process-aware rollback, and rebuild
retirement. Broader profiles/backends, multi-process execution, external
artifact authenticity, and state-complete replay remain unsupported and fail
closed.
