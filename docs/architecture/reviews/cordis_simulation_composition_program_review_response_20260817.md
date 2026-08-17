# Response to the Cordis Simulation Composition Program Architecture Review — 2026-08-17

Language:

- English canonical: `cordis_simulation_composition_program_review_response_20260817.md`
- Chinese companion:
  [cordis_simulation_composition_program_review_response_20260817.zh.md](cordis_simulation_composition_program_review_response_20260817.zh.md)

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/architecture/reviews/cordis_simulation_composition_program_review_response_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-17`
Review answered:
[Cordis simulation composition program architecture review](cordis_simulation_composition_program_review_20260817.md)
Review basis: `b9f289c81fd4`
Response plan revision: `153d5f4e`
Decision state: `partially accepted and incorporated; Cordis strategic target retained; re-review requested`
Authority: owner response to an advisory review. The review remains an immutable
independent judgment snapshot; this response changes the active program only
through the cited active-work documents and commits.

## 1. Response Outcome

The review identified real authority, admission, abstraction, evidence-timing,
and closure defects in the previous plan. Those defects are accepted and the
active plan has been revised.

The review's further conclusion that Cordis should remain an optional adapter
is not adopted. The program objective is specifically to introduce Cordis's
context, service, injection, effect, profile, and plugin composition model into
the simulation runtime architecture. Treating Cordis as indefinitely optional
would turn the project into a generic native manifest/lifecycle refactor and
would not satisfy that objective.

The corrected decision is:

| Question | Owner decision |
| --- | --- |
| Who owns experiment intent? | The Experiment Face. |
| Who owns declarative runtime capability/plugin/service/profile composition? | Cordis, after an explicit runtime-composition projection. |
| Who admits implementations? | The applicable model, system, backend, domain, evidence, and security owners through an `AdmittedCatalogLock`. |
| Who deterministically validates, resolves, realizes, freezes, and disposes the plan? | The native composition compiler/root. |
| Who owns executable simulation semantics? | Flecs, the native scheduler, backend, batch/runtime, episode, and engine owners. |
| Is Cordis required for overall program closure? | Yes: at least one repository-owned Cordis producer/native realization vertical path is required. |
| Is Node required? | No. Node hosting remains conditional on an approved host use case. |
| Are external plugins required? | No. External distribution, authenticity, ABI, sandbox, and marketplace work remains a separately governed residual. |

## 2. Relationship To Cordis And DeepSeek Harness

The native composition kernel is not a substitute for Cordis. It is the
deterministic realization substrate required to introduce Cordis without
placing host-runtime semantics in the simulation truth path.

The intended mapping is:

| Cordis concept | Simulation composition role |
| --- | --- |
| Context hierarchy | application, backend, batch, world, and episode administrative ownership boundaries |
| Services and injection | typed runtime provider requirements and bindings |
| Effects | reversible administrative registrations and staged host-side actions |
| Profiles and plugins | declarative capability/profile/package composition |
| Cordis resolution | construction of the canonical requested composition from admitted declarations |
| Native composition compiler/root | independent revalidation, exact implementation binding, transactional realization, generation handover, and deterministic disposal |

DeepSeek Harness is relevant because it demonstrates the larger architectural
pattern in which Cordis supplies a compositional harness/control layer rather
than numerical execution. Echelon Forge is not embedding DeepSeek Harness as
its simulation runtime. It is applying the underlying Cordis composition model
to simulation providers, packages, profiles, and administrative lifecycle while
keeping the existing native engine authoritative for deterministic execution.

## 3. Amended Authority Flow

```mermaid
flowchart LR
    EXP["ExperimentSpec\nsimulation + policy + evaluation intent"]
    PROJECT["RuntimeCompositionRequest\ncapabilities + policies + configuration"]
    CORDIS["Cordis declarative control plane\ncontexts + services + profiles + plugins"]
    COMPAT["Native / Python compatibility producer\noffline and embedded"]
    REQUEST["Canonical low-level\nSimulationCompositionManifest"]
    CATALOG["AdmittedCatalogLock\nowner-approved implementations + provenance"]
    NATIVE["Native composition compiler/root\nrevalidate + resolve + realize + freeze"]
    PLAN["ResolvedRuntimePlan + EvidenceLock"]
    FACADE["RuntimeFacade / session owner"]
    EXEC["Backend -> Batch -> Worlds -> Episodes"]

    EXP --> PROJECT
    PROJECT --> CORDIS
    PROJECT --> COMPAT
    CORDIS --> REQUEST
    COMPAT --> REQUEST
    REQUEST --> NATIVE
    CATALOG --> NATIVE
    NATIVE --> PLAN
    PLAN --> FACADE
    FACADE --> EXEC
```

This resolves the apparent conflict between the Experiment Face and Cordis:
the Experiment Face owns intent; Cordis owns declarative runtime composition of
that projected intent; owner-specific authorities admit implementations; the
native path owns deterministic realization.

## 4. Finding Disposition

| Finding | Disposition | Incorporated change |
| --- | --- | --- |
| `F-01` composition authority ambiguity | accepted | Added the explicit Experiment intent -> runtime projection -> Cordis declaration -> owner admission -> native realization chain to the README, architecture, status, task, and acceptance surfaces. |
| `F-02` Cordis prerequisite before unique value is established | premise rejected; evidence concern accepted | Cordis remains the strategic target, but the first real Cordis proof moved forward to `P2-C` immediately after production default-provider migration. It must demonstrate canonical/native parity against the real default path before broader Cordis or host work. |
| `F-03` one package conflates three programs | partially accepted | Native, system/profile, Cordis, backend/evidence, and Node work now have bounded acceptance. The proposed optional Program C is split into a required Cordis producer path and a conditional Node/external-ecosystem path. |
| `F-04` universal plugin plane obscures owner admission | accepted | Added `AdmittedCatalogLock` and explicit category owners. Shared lifecycle mechanics do not grant model/system/backend/domain/evidence/security admission. |
| `F-05` systems should compile admitted packages | accepted | `P3-A` now targets repository-admitted system packages compiled by the existing native graph/scheduler owners; discovery order and private pipelines remain forbidden. |
| `F-06` domain profiles risk replacing capability composition | accepted | `P3-B` is renamed `Capability And Profile Projection`; capabilities and policies are primary, while named domain profiles are compatibility bundles. |
| `F-07` authoring request/catalog/resolved distinction | accepted without reopening P1-B | Added the conceptual `RuntimeCompositionRequest`, `AdmittedCatalogLock`, and `ResolvedRuntimePlan` layers. The existing P1-B requested manifest remains the canonical low-level interchange and compatibility artifact, not the sole future authoring API. |
| `F-08` scope/DAG/evidence concerns | accepted | Scope containment remains separate from the realized dependency DAG. Production composition identity moves into `P2-B`; `P5-A` becomes evidence expansion rather than first evidence introduction. |

## 5. Response To The Proposed Program Split

The review's independent-closure concern is valid, but the proposed optional
Cordis program boundary is too broad. The amended delivery streams are:

### Stream A — Native Runtime Composition

- P1-B and P2-A remain accepted foundations.
- P2-B migrates production default providers and publishes the first production
  composition identity.
- This stream may receive bounded native acceptance without claiming Cordis
  completion.

### Stream B — Executable Package And Capability Composition

- P3-A compiles repository-admitted system packages into the native stage graph.
- P3-B projects capabilities, policies, and compatibility profiles into those
  packages.
- Stage/domain owners retain admission and execution authority.

### Stream C1 — Required Cordis Composition Path

- P2-C is the minimum default-profile vertical slice.
- P6-A matures Cordis profiles, overlays, diagnostics, provenance, dependency
  resolution, and package ergonomics after the vertical path is proven.
- Overall program closure requires C1; otherwise Cordis has not actually been
  introduced.

### Stream C2 — Conditional Host And External Ecosystem

- P6-B Node hosting requires a separate approved host use case.
- External packages, authenticity, ABI, sandboxing, remote catalogs, and a
  marketplace remain separately governed.
- C2 may be held or rejected without invalidating A, B, or the C1 Cordis/native
  composition objective.

## 6. Amended Sequence And Closure

The maintained sequence is now:

1. `P2-B Default Provider Migration`;
2. `P2-C Cordis Default-Profile Vertical Slice`;
3. `P3-A System Contribution Migration`;
4. `P3-B Capability And Profile Projection`;
5. `P4-A Backend Provider Migration`;
6. `P5-A Composition Evidence Expansion`;
7. `P6-A Cordis Package Maturation`;
8. conditional `P6-B Node Host Adapter`;
9. applicable producer/host/backend/batch parity;
10. migration closure and residual routing.

The active documents amended by `153d5f4e` are:

- [program README](../work/active/cordis_simulation_composition_kernel/README.md);
- [target architecture](../work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_architecture.md);
- [task clusters](../work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_task_clusters_20260817.md);
- [dispatch queue](../work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_dispatch_queue_20260817.md);
- [current status](../work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_current_status_20260817.md);
- [acceptance contract](../work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_acceptance_20260817.md).

## 7. Immediate Dispatch Decision

`P2-B` remains the next eligible implementation cluster. It must not implement
the Cordis package in the same write set. It must, however:

- construct the production default profile through admitted native providers;
- remove the unsafe raw provider capture;
- preserve behavior and replay parity;
- export stable requested/resolved production identity;
- leave an explicit projection/evidence seam that P2-C can consume.

After P2-B is accepted, P2-C becomes the next strategic cluster. It must prove
the Cordis model against the production default path, not merely against a
synthetic schema fixture.

## 8. Requested Re-review

The independent reviewer is asked to re-evaluate the amended plan on these
questions:

1. Is the Experiment Face/Cordis/admission/native authority chain unambiguous?
2. Does P2-C prove a real Cordis relationship early enough to justify later
   package maturation?
3. Are owner-specific system/backend/domain/evidence admission boundaries
   preserved?
4. Does independent slice acceptance avoid Node/external-ecosystem blockage
   without making Cordis optional?
5. Does the closure rule accurately require Cordis producer/native conformance
   while allowing Node and external distribution to remain conditional?

## 9. Final Response State

Response state: `architecture findings partially accepted and incorporated`.

The review's authority, typed-admission, capability-composition, abstraction,
evidence-timing, and independent-slice concerns have materially changed the
plan. Its recommendation to make Cordis an optional adapter has not been
adopted because it conflicts with the program's strategic objective. The
revised plan now requires earlier executable evidence of Cordis rather than
deferring it behind a long native-only sequence.
