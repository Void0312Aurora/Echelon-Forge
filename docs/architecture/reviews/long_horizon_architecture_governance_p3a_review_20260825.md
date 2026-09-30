# Long-Horizon Architecture Governance P3-A Independent Review

Status: `2026-08-25` accepted P3-A public-contract foundation after one
independent initial review, repair, and final read-only confirmation. The
overall long-horizon program remains not accepted; no host publication,
production caller migration, SDK release, or platform qualification is proven.

Parent subproject:
[Long-Horizon Architecture Governance](../work/active/long_horizon_architecture_governance/README.md)

Reviewed cluster:
[P3-A public-contract foundation](../work/active/long_horizon_architecture_governance/long_horizon_architecture_governance_task_clusters_20260825.md)

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/architecture/reviews/long_horizon_architecture_governance_p3a_review_20260825.md`
Owner: `cross-domain architecture review`
Last verified: `2026-08-25`

## Review Decision

Final integrated verdict: `pass`.

P3-A has no unresolved critical, high, medium, or low finding. The accepted
result is a build-tree-only, engine-independent `ef_runtime_contracts` target
and a versioned same-build identity value-contract family. It does not claim a
portable native object representation, wire/storage format, supported SDK ABI,
Linux qualification, host freshness validation, or production authority.

No review detected short-term scope substitution, a caller cutover, host
publication, an install/export rule, or a second serialization/result identity
authority.

## Independence And Review Configuration

The reviewer was an independent read-only agent using:

- model: `gpt-5.6-sol`;
- reasoning: `max`;
- write authority: none;
- review worktree:
  `D:\workshop\Research\Echelon-Forge\.worktrees\long-horizon-governance-architecture`;
- branch: `codex/long-horizon-governance-architecture`;
- reviewed HEAD: `b68a366a65cbcc53f7ad805fd0e95a48598fb4ec`;
- remote baseline: `origin/main`
  `82d5b6e893c442950e334eb3e9ec92f8174eeb35`.

The reviewer did not draft, edit, stage, or commit the implementation. It read
the P1 decisions, P3-A cluster/acceptance terms, CMake target graph, generated
schemas, public header, native and architecture tests, legacy callers, and
build/install evidence. It then performed a second read-only review after all
findings were repaired.

## Reviewed Final Snapshot

These SHA-256 values anchor the core reviewed files before this review record
and status updates were persisted:

| File | SHA-256 |
| --- | --- |
| `CMakeLists.txt` | `a0a7ba3cad3bb49d154adb3373ca72f95aee203450dce3a40e5ef4d6596fab31` |
| `cmake/verify_runtime_contracts_boundary.cmake` | `41daf70ca11adc4fda24ccfe502e790bf2d26648b64e87055b45b74d578a7bf1` |
| `include/echelon_forge/runtime_contracts/runtime_identity.h` | `e0a0fdc1e466934703a298e21becf16540ea454aff619fd6a87b6385942668c9` |
| `src/runtime/contracts/public/runtime_identity.cpp` | `14680b7254b7848eb9c1b979130d0f4f4e7a8d49b7ab7f3ed7ea36d0ab43e00f` |
| `src/tests/test_runtime_identity_contracts.cpp` | `68a8ca8f2e678acfcaa8bed709909ea22a9dd81bea273641d8ad78ed6f467de9` |
| `tests/architecture/runtime_contracts/test_public_runtime_contract_foundation.py` | `fd409e0851185bc40c235565106e0387b8ffa92be421bd1af8f8693d85ff950f` |
| `tools/maintenance/dto_schema/schemas/runtime_contracts/__init__.py` | `0c96c0a33364c93ff1cd7542b7ddb38ea79f114986a84cf8017d6a6a627eb457` |

The generated field lists and their eight schema modules are additionally
covered by the existing DTO schema manifest/freshness gate. Commit identity is
delivery metadata, not a substitute for these content hashes and executable
checks.

## Initial Findings And Disposition

The initial verdict was `pass_with_repairs`: zero critical findings, two high,
four medium, and one low.

| ID | Finding | Final disposition |
| --- | --- | --- |
| `H-01` | fixed native sizes were described as an admitted ABI without separating canonical serialization authority | closed: explicit `v1` source-level value contract; native bytes are forbidden as persistence/hash/signature/IPC; P3-B remains the only canonical JSON/digest projection; Windows/Linux qualification stays P5/P8 work |
| `H-02` | `RuntimeResultRef` invented an unowned `result_sequence` namespace beyond P1 | closed: the terminal result identity is exactly its request identity; future streaming needs a separately reviewed protocol |
| `M-01` | stable host identity and published incarnation were one misleading type | closed: `RuntimeHostIdentity` and `RuntimeIncarnationRef` are distinct; every world and inner reference contains the incarnation |
| `M-02` | `.valid()` could be mistaken for authoritative freshness admission | closed: `.well_formed()` proves non-zero local shape only; P4 must validate current slot, tombstones, enclosing generations, membership and lease under the host authority |
| `M-03` | hand-written fields bypassed the existing `dto_schema` single source | closed: eight registered schemas generate the public field lists; manifest, freshness and bounded-directory gates own drift detection |
| `M-04` | marker-based CMake/source scans could be bypassed | closed: final configure-time target/consumer checks, generated target/install manifest verification, malicious graph fixtures, closed public schema type/header/footer/output rules, and raw-pointer/relative-include injection tests fail closed |
| `L-01` | native tests missed zero and enclosing-generation mutations | closed: the mutation matrix covers host/boot/incarnation/world/entity/episode/request/result shape plus propagation across nested identities |

## Repair-Review Findings And Disposition

The repair review found three additional defects before its final pass:

| ID | Finding | Final disposition |
| --- | --- | --- |
| `RM-01` | the boundary README accidentally downgraded all existing internal contracts to transitional | closed: maintained contracts retain their lifecycle; only the bare `WorldEntityRef` identity predecessor is classified transitional by P3-A |
| `RM-02` | generated field types could inject a same-size raw pointer | closed: public schemas use a closed C++ type allowlist and an import-time validator with a malicious `void *` negative test |
| `RM-03` | generated header/footer text could inject a private relative include | closed: output path, ASCII header, single field macro and matching-only `#undef` footer are closed and a relative-include injection test rejects the bypass |

The reviewer also confirmed the new schema package and public `detail/` root are
covered by the maintained flat-directory gate. The final integrated verdict was
`pass` with no unresolved finding.

## Accepted P3-A Result

P3-A accepts only these foundations:

1. `ef_runtime_contracts` is a static build-tree target with the public
   `include/` root and no engine, facade, Flecs, binding, JSON, Cordis, install,
   or export dependency.
2. The public `runtime_contracts::v1` family separates stable host identity from
   published incarnation and nests world/entity/episode/request/result identity
   through every enclosing generation.
3. One admitted request has one terminal-result identity. DTO
   `well_formed()` checks cannot replace P4 host/lease freshness validation.
4. The native object representation is a same-build layout only. P3-B owns the
   sole canonical wire/storage projection; P5/P8 own package ABI and platform
   qualification.
5. The existing `dto_schema` lifecycle is the only public field-list owner.
   Configure-time graph checks and generated post-configuration evidence make
   dependency, consumer, source, include and install drift fail closed.
6. The legacy facade, `WorldEntityRef`, raw bindings and maintained callers are
   unchanged. P4 dark/shadow work may replace the temporary no-consumer gate;
   production activation remains reserved for P5-D.

## Validation Evidence

The main thread and independent reviewer verified:

- Windows AMD64 MSVC/Ninja Release build of `ef_runtime_contracts` and the
  focused consumer: pass;
- CTest `runtime_contracts_compile` and `runtime_contracts_boundary`: `2/2`
  passed;
- fresh `BUILD_TESTING=OFF` configure/build of only
  `ef_runtime_contracts`: pass;
- P3-A plus schema-freshness/flat-directory focus: `18 passed`;
- P3-A/composition/source-boundary expansion: `101 passed, 4 skipped`;
- full runtime-facade plus DTO-schema checks with the worktree-local
  `ef_py`: `87 passed`;
- DTO generator `--check`: 110 registrations current, including all eight
  public identity schemas;
- clang-format, Ruff and `git diff --check`: pass, with line-ending conversion
  warnings only;
- generated target evidence: static library, empty direct/interface link sets,
  only the public include root, the declared public/generated/source files, and
  no install/export entry;
- source census: only the library implementation and focused native consumer
  include the public header.

An early expanded facade collection failed closed because the nonstandard
build directory was not selected. It passed after explicitly setting
`CMO_BUILD_DIR`/`PYTHONPATH` to the local MSVC `ef_py`; it is not counted as a
project assertion failure.

## Remaining Boundaries

- Linux x86_64 was not compiled because the available WSL distribution has no
  C++ compiler. That required target row remains unqualified.
- P3-B canonical envelopes and serialization, P3-C rollout/ledger storage,
  P4 host freshness/leases/tombstones/exhaustion, and P5 package/cutover remain
  unimplemented.
- The target is not an installed SDK and has no maintained production consumer.
- Overall program acceptance remains `not accepted`.
