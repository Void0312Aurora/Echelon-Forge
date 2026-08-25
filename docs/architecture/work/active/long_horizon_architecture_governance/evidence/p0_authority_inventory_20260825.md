# P0 Authority Inventory — 2026-08-25

Status: `accepted` P0-A evidence against plan commit
`c668bae91900df4b5488099384c95d9820209de2` and remote base
`82d5b6e893c442950e334eb3e9ec92f8174eeb35`.

Parent subproject: [Long-Horizon Architecture Governance](../README.md)

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p0_authority_inventory_20260825.md`
Owner: `cross-domain architecture/evidence`
Last verified: `2026-08-25`

## Decision Boundary

This inventory closes the P0 reproducible-baseline obligation for live callers,
targets, composition artifacts, architecture controls, CI lanes, and documents.
It does not select the P1 target mechanisms, implement a host, change a runtime
caller, retire a control, or accept any P1-P8 result.

The inventory reuses the existing runtime-composition closure generator and
test-system audit. It does not create another registry, generator, fixture, or
blocking gate. P1 and P2 own future semantic classification and lifecycle
decisions; this file is a dated evidence snapshot.

## Reproduction Environment

| Item | Accepted P0 fact |
| --- | --- |
| Branch | `codex/long-horizon-governance-architecture` |
| Plan commit | `c668bae91900df4b5488099384c95d9820209de2` |
| Remote base | `origin/main` at `82d5b6e893c442950e334eb3e9ec92f8174eeb35` |
| Primary checkout | dirty user work remained isolated and unchanged |
| Fresh build directory | ignored `build-long-horizon-p0/` in the dedicated worktree |
| Generator/toolchain | Ninja; MSVC 19.44.35217; Release; CUDA helper and resident backend flags off |
| Python | CPython 3.12.4; use an environment with `jsonschema>=4.18,<5` for closure validation |

Core reproduction commands:

```powershell
$baseline = "c668bae91900df4b5488099384c95d9820209de2"
git fetch origin --prune
git rev-parse $baseline
git rev-parse origin/main
python tools/maintenance/runtime_composition_migration_closure.py validate
python -m pytest -q -p no:cacheprovider --confcutdir tests/architecture tests/architecture/composition
```

The closure validator returned
`498c64f4f9fc85395939e9056280ad9bd5e4ebc6df84d58b83763cb16f85d5b2`.
Composition architecture validation returned `69 passed, 4 skipped`.

## Caller And Replacement Inventory

The existing
[`default_runtime_composition_migration_closure.v1.json`](../../../../../../tests/architecture/composition/fixtures/default_runtime_composition_migration_closure.v1.json)
is the caller inventory owner. Its generator ignores test/archive/cache roots for
live Python/C++ discovery, adds explicit native/binding/test-only seams, checks
source truth, and rejects a stale closure. The accepted snapshot contains nine
surface groups and 23 caller paths.

| Surface | Class / owner | Current caller paths | P0 fact |
| --- | --- | --- | --- |
| `runtime_facade.maintained_host` | maintained host / `runtime/facade` | `python/rl/runtime/world_batch/adapter.py`; `tools/maintenance/runtime_host_batch_parity_contract.py` | maintained Python host enters through `RuntimeFacade` |
| `simulation_kernel.default_compatibility` | compatibility and diagnostics / `core/engine` | CI inline probe, visualization server, four `python/testing/contracts` files, two diagnostic benchmarks, kill-chain probe, and two geometry probes | default constructor remains a broad compatibility/diagnostics surface |
| `simulation_kernel.native_default_callers` | standalone and batch compatibility / `core/engine` | `src/core/engine/world_batch_runtime.cpp`; `src/main.cpp` | both use the generated default resolved manifest alias |
| `simulation_kernel.python_binding_exposure` | compatibility binding / `interfaces/python` | `src/interfaces/python/bindings_core_simulation_kernel.cpp` | raw kernel remains exported in the single `ef_py` module |
| `world_batch_runtime.native_backend_owner` | native backend internal / `runtime/backend` | `src/runtime/facade/internal/flecs_cpu_backend.cpp` | batch runtime sits behind the admitted CPU backend provider |
| `world_batch_runtime.python_binding_exposure` | compatibility binding / `interfaces/python` | `src/interfaces/python/bindings_runtime_engine.cpp` | raw batch runtime remains exported for compatibility/diagnostics |
| `runtime_facade.python_binding_exposure` | maintained binding / `interfaces/python` | `src/interfaces/python/bindings_runtime_facade.cpp` | facade and raw compatibility APIs ship in the same module |
| `simulation_kernel.explicit_manifest` | Cordis/native bridge / `architecture/runtime-composition` | `src/tests/test_cordis_runtime_conformance.cpp` | native conformance validates Cordis-produced artifacts before realization |
| `simulation_kernel.test_fault_injection` | test-only / `core/engine` | composition test-access source/header and kernel smoke test | rollback seam shares the production realizer and is test-compiled only |

Rebuild reachability is narrower than construction compatibility:

```powershell
git grep -n -I 'rebuild_world_composition' $baseline -- `
  ':(exclude)tests/**' ':(exclude)src/tests/**' ':(exclude)docs/**'
git grep -n -I 'rebuild_world_composition' $baseline -- src/interfaces/python
```

The first command returns only the declaration and definition in
`simulation_kernel.h/.cpp`; the binding query returns nothing. There is no
maintained non-test production caller and no Python exposure. This is evidence
for P1-A; it is not deletion authorization.

## Target, Link, And Package Inventory

A prior build directory pointed at a removed Cordis worktree and failed CMake
regeneration. It is historical evidence only. A fresh current-worktree graph
was configured with:

```powershell
$cmdLine = 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x64 && cmake -S . -B build-long-horizon-p0 -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DEF_ENABLE_CUDA_EXPERIMENTS=OFF -DEF_ENABLE_CUDA_RESIDENT_BACKEND=OFF -DEF_FETCHCONTENT_REVALIDATE_PINS=OFF'
cmd.exe /d /s /c $cmdLine
cmake --build build-long-horizon-p0 --target help
ninja -C build-long-horizon-p0 -t query ef_py.cp312-win_amd64.pyd
ninja -C build-long-horizon-p0 -t query ef_facade.lib
ninja -C build-long-horizon-p0 -t query ef_core.lib
ninja -C build-long-horizon-p0 -t query ef_composition.lib
```

The current graph exposes 25 repository `ef_*` targets:

- production/compatibility: `ef_composition`, `ef_content`, `ef_core`,
  `ef_facade`, `ef_py`, `ef_app`, and `ef_flecs`;
- experimental: `ef_cuda_resident_backend`,
  `ef_cuda_resident_full_window_runner`, `ef_gpu_experiments`, and seven
  `ef_gpu_*_phase0_probe` targets;
- qualification: `ef_test`, `ef_composition_lifecycle_test`,
  `ef_cordis_runtime_conformance_test`, `ef_backend_provider_migration_test`,
  `ef_composition_evidence_test`, and three CUDA-resident test targets.

| Boundary | Configured graph fact | Long-horizon consequence |
| --- | --- | --- |
| Composition | `ef_composition` is an independent seven-source static library with no `ef_core`, facade, binding, or Cordis link | usable contract/lifecycle foundation, but not yet the final resolved-plan public target |
| Core | `ef_core` publicly links `ef_composition` and `ef_content` | native execution remains above composition validation |
| Facade | `ef_facade` publicly links `ef_core` and publicly exports the entire `src` include root | facade direction exists, but private engine ownership is physically reachable |
| Python module | `ef_py` directly links `ef_facade`, `ef_core`, and `ef_gpu_experiments`; it compiles raw kernel, raw batch, facade, diagnostics, legacy, and override bindings together | production and diagnostics/package boundaries are not physically separated |
| Public DTO headers | `runtime_facade_types.h` includes `components/physics/instruments.h` and `core/interfaces/observation.h` | the current public DTO shell is engine/component dependent |
| Standalone host | `ef_app` directly links `ef_core` | standalone compatibility bypasses the facade |
| CUDA | CUDA-resident and helper targets are explicit experimental targets and are configured off in this baseline | CPU exact remains canonical; no CUDA promotion is implied |

`ef_composition` built successfully in eight Ninja steps on the fresh MSVC
configuration. The build emitted existing MSVC C4834 warnings for discarded
`[[nodiscard]]` results in `runtime_composition_projection_contract.cpp`; those
warnings do not fail P0 but must not be reported as warning-free evidence.

## Artifact Authority Inventory

The closure validator joins and revalidates the following live artifacts. Hashes
are stored in the closure record and are not duplicated here as a second
authority.

| Artifact | Current role | Long-horizon classification question |
| --- | --- | --- |
| `default_runtime_composition_request.v1.json` | experiment intent (`runtime_composition_request.v1`) | durable request candidate |
| `default_admitted_catalog_lock.v1.json` | owner admission and implementation identity lock | build/admission input; not executable truth by itself |
| `default_runtime_profile_projection.v1.json` | joined request/lock/profile projection | derived input whose permanent interchange role is unresolved |
| `default_compatibility_manifest.requested.json` | requested low-level composition graph | current producer/native interchange input |
| `default_compatibility_manifest.resolved.json` | deterministic resolved graph and canonical hashes | current executable interchange authority; P1-B must define successor/version route |
| `default_backend_provider_request.v1.json` | accepted CPU backend selection request | derived backend admission input |
| `default_runtime_composition_evidence.v1.json` | composition identity, versions, graph, backend, host mode, and world scopes | strong composition evidence but not a complete per-run receipt |
| `default_runtime_package_provenance.v1.json` | Cordis package/dependency/overlay provenance | build and producer provenance |
| parity budget and semantic reference | frozen host/batch comparison contract | qualification input, not runtime truth |
| `default_runtime_host_batch_parity.windows_msvc.v1.json` | measured local Python/native/Cordis parity | platform-specific qualification evidence |
| generated headers | compiled default manifest and evidence projection | derived build output; freshness is tested |
| `default_runtime_composition_migration_closure.v1.json` | caller/truth-path/hash/residual closure record | governance evidence; must not become another runtime resolver |

The current composition evidence lacks actual executable/module/wheel digests,
toolchain/ABI/OS identity, scenario/content/config/seed, world/episode/run
identity, lifecycle-transition receipts, result hashes, and completion state.
P1-B/P5-B therefore remain responsible for `RunReceipt`; P0 does not relabel
the existing evidence as complete run provenance.

## Control, Test, And CI Inventory

The complete active-test baseline is reproduced with:

```powershell
$raw = python tools/runners/audit_test_system.py --format json
$audit = $raw | ConvertFrom-Json
$audit.summary
$audit.directories | Where-Object {
  $_.directory -in @('tests/architecture','tests/runtime','tests/runners','tests/world_batch','tests/gpu')
}
```

| Surface | Current measured baseline |
| --- | --- |
| Active non-archive test files | 486 total; 342 Python; 287 Python test files |
| Static test items | 2,610; heuristic only, not pytest collection |
| Risk-flagged files | 193 |
| Architecture tests | 119 files; 92 Python; 735 static items; 79 files flagged as source-scan guards |
| Runtime tests | 130 files; 128 Python; 898 static items; 15 source-scan-flagged files |
| Runner tests | 10 files; 55 static items; 8 source-scan-flagged files |
| Pytest smoke | 124 entries across 85 base files |
| Contract smoke | 10 specifications among 61 active contract JSON files |

Program-critical blocking-control families are fully enumerable from checked-in
paths and manifests:

| Control family | Files / lane | Current purpose and boundary |
| --- | --- | --- |
| Composition architecture | eight `tests/architecture/composition/test_*.py`; all in the 82-entry architecture guard suite; two also selected by smoke, while CI runs the whole directory separately | schema, projection, Cordis/native, evidence, parity, closure, and caller/source-truth admission |
| Runtime facade architecture | nine test files plus one helper; all nine tests in architecture guard; six selected by smoke; CI separately runs provider/design-boundary files | facade direction, escape hatches, DTOs, scenario setup, tasking, and compatibility callers |
| Native admission | five CPU/composition targets in CTest/CI plus `ef_test` | lifecycle, Cordis conformance, backend selection, evidence, and broad native behavior |
| Governance audit | seven paths in `governance_audit_suite.json`; only selected information/link nodes are in smoke | document structure, closure, tier census, runtime docs, standards, and archive retirement |
| Suite integrity | runner manifest/runner tests; five runner files selected by smoke | checked-in suite membership and executable routing |
| Packaging | isolated Linux wheel build/import/behavior block in `ci-smoke.yml` | proves a self-contained `ef_py` wheel, but not facade-only physical ownership |
| CUDA | separately named targets and tests; feature flags off in the P0 graph | experimental qualification cannot change CPU-canonical authority |

The full governance manifest remains `53 passed, 1 failed`. The failure is the
known `test_archive_retirement.py` conflict with 20 tracked architecture archive
documents. This is a live blocking-control contradiction assigned exclusively
to P7-A; it is not authorization to delete history during P0.

The document-tier census baseline was mechanically refreshed from 821 to 829
tracked Markdown files (`tier_b` 66 to 73; `tier_d` 587 to 588) so it includes
the seven plan/review documents from the preceding commit and this evidence
file. Tier A bilingual SLA count remains 148; the refresh does not promote a
new normative authority.

## Document And Retention Inventory

The keyword-scoped current/historical document surface is reproduced against the
named baseline, not the evolving working tree:

```powershell
$docHits = @(git grep -l -I -i -E `
  'runtime composition|simulationkernel|rebuild_world_composition|runtimefacade|worldbatchruntime|cordis|archive-retirement|retired_documents' `
  $baseline -- 'docs/**/*.md')
$docs = @($docHits | ForEach-Object { $_ -replace "^$baseline`:", '' } | Sort-Object -Unique)
$maintained = @($docs | Where-Object { $_ -notmatch '/archive/' -and $_ -notmatch '/Archive/' })
$archived = @($docs | Where-Object { $_ -match '/archive/' -or $_ -match '/Archive/' })
```

The result is 72 relevant documents: 52 outside archive paths and 20 under the
architecture archive path. Their authority classes are:

- current owner indexes and standards: architecture README, simulation system,
  runtime workflow, and runtime composition baselines;
- current project authority at the named baseline: active README pair, status,
  queue, task clusters, acceptance contract, and review; this follow-on P0
  evidence file is intentionally not part of the frozen 72-document count;
- maintained reference/review/issue inputs: truth-leak inventory, facade and
  modularization issues, operations engine maps, and bounded historical reviews;
- Cordis work packet: 20 tracked archive-path documents that remain linked from
  current architecture authority while the retirement test prohibits them;
- other-owner references: learning, naval, effects, weapons, operations, and
  systems documents that mention the runtime surfaces but do not own this plan.

P7-A must choose and migrate to one policy/template/gate/suite/path/retrieval
model. P0 preserves the conflict as evidence and creates no new archive path.

## P0 Acceptance Decision

P0-A is `accepted` because:

- remote revision, branch, worktree, and dirty-root separation are recorded;
- caller/source truth is covered by a validated existing closure generator;
- a fresh current-worktree MSVC/Ninja target graph exists and its composition
  contract target builds;
- artifacts, controls, test/CI lanes, and documents have reproducible complete-
  scope commands and dated counts;
- project document gates pass and independent P0-B plan review passed without an
  unresolved critical/high finding.

P0 acceptance authorizes P1-A/P1-B/P1-C architecture decisions only. It proves
no host implementation, immutable production kernel, RunReceipt, facade-only
package, control retirement, evidence migration, or operational readiness.

## P1 Entry Facts

- No production caller requires in-kernel rebuild, but compatibility callers of
  the raw kernel remain broad.
- The composition lifecycle link unit is real and buildable; the final public
  plan/contracts target is not yet defined.
- The facade is directionally above core but physically exports and links core;
  production and diagnostics bindings share one module.
- The artifact chain is strongly closed for the accepted default profile but is
  not a complete per-run receipt.
- Control and document mechanisms are numerous, and archive retention currently
  has contradictory normative and executable authorities.

These facts constrain P1 mechanisms. They do not pre-decide P1 outcomes beyond
the independently accepted long-horizon contract.
