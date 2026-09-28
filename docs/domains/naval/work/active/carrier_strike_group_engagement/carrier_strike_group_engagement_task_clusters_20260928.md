# Carrier Strike Group Engagement Task Clusters

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/work/active/carrier_strike_group_engagement/carrier_strike_group_engagement_task_clusters_20260928.md`
Owner: `domains/naval`
Last verified: `2026-09-28`

Status: `2026-09-28` finite task-cluster plan for
[Carrier Strike Group Engagement](README.md). `P0-A` accepted `2026-09-28`.

## Boundary Decision

This package may add naval, carrier-aviation, and undersea platforms and
mechanisms, the shared mechanisms each stage names, and the `CSG-*` scenario
ladder with its contracts and tests.

Mechanisms that other domains also use are built by their cross-domain system
owners (see the README's System Dependency Register). Clusters here integrate
those deliverables and build only the naval-owned part.

It must not:

- build cross-domain mechanisms (geodesy, environment, generic sensing, data
  links, EW, weapon families, generic effects, shared logistics) in the naval
  tree;
- re-own Air-domain flight, guidance, or effects mechanisms; carrier aviation
  consumes them through the Air owner's maintained surfaces, and any change to
  them goes through that owner;
- redefine Joint common-core fields; group command relationships use the Joint
  baseline and the Navy service profile;
- claim learned-policy quality or real-world operational prediction;
- invent calibrated-looking coefficients. A parameter without an admissible
  source is recorded as an engineering estimate with its uncertainty, or is left
  unset with a named residual.

Clusters are grouped by stage. A stage's acceptance cluster (`*-X`) is serial and
closes the stage; implementation clusters within a stage may run in parallel only
where the dependency column says so.

## Finite Task Cluster List

Model and reasoning are chosen per the
[Subagent Usage Policy](../../../../../engineering/automation/standards/subagent_usage_policy.md)
at dispatch; `n/a` means not yet dispatched.

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-A` | main thread | main thread / session model / high | Freeze scope, ladder, claim ceilings, and provenance policy. | this directory; naval owner README index | runtime code | doc link audit; bilingual audit | owner approves README, clusters, acceptance | first | 1 | accepted |
| `S0-A` | future worker | moderate (public-source research) / sonnet for integration; research ran on default / medium | Order-of-battle research: both groups' ship, submarine, aircraft, weapon, and sensor lists with sources. | `docs/domains/naval/reference/csg_order_of_battle_*.md` | runtime content | provenance check: every row has source ID, tier, uncertainty | both sides' OOB tables complete | after `P0-A`; parallel with `S0-B` | 2 | active |
| `S0-B` | main thread | moderate / sonnet / medium | Integrate [Geodetic Frame](../../../../../systems/physics/work/active/geodetic_frame/README.md): scenarios declare a geodetic anchor; OOB placement and ranges use the shared frame. | `scenarios/naval/csg/`; naval scenario tests | building the frame (owned by `systems/physics`) | scenario anchor tests | CSG scenarios place both groups through the shared frame | after Geodetic Frame `P3-B` accepted | 1 + 1 repair | planned |
| `S0-C` | future worker | moderate / sonnet / medium | Named unit content for both groups from `S0-A`. | `examples/config/database/**` (ships, submarines, aircraft, weapons, sensors) | new mechanisms | content-compile tests; unit spawn tests | every OOB row spawns with provenance | after `S0-A` | 2 + 1 repair | planned |
| `S0-D` | future worker | moderate / sonnet / medium | Group-composition scenario schema plus `CSG-S0` named and mirror scenarios. | scenario loader schema, `scenarios/naval/csg/`, `tests/contracts/unit/naval/csg/` | motion | scenario contract runner | both variants load and spawn the full OOB | after `S0-C` | 2 | planned |
| `S0-X` | main thread | high (stage acceptance) / main thread + opus reviewer / high | Accept `CSG-S0`; first throughput record. | stage acceptance record | — | stage validation plan | `G0` gate met | after `S0-B`, `S0-D` | 1 | planned |
| `S1-A` | future worker | n/a | Group formation and screen geometry; route following. | naval command/formation components and systems | fleet doctrine beyond formation | formation-keeping tests | formation holds under turns | after `S0-X` | 2 + 1 repair | planned |
| `S1-B` | future worker | n/a | Ship turning-circle and speed response; damage-to-mobility coupling. | `ship_motion_system.h`, platform fields | full hydrodynamics | motion tests against sourced turning data | damaged ship loses speed through the maintained path | after `S0-X`; parallel with `S1-A` if write sets split | 2 + 1 repair | planned |
| `S1-C` | future worker | n/a | Ship endurance and group replenishment scheduling on the shared logistics components. | naval logistics system; naval stores content | shared fuel/logistics components (owned by `systems/physics`) | logistics tests | endurance and replenishment observable in the scenario | after `S0-X` and the shared-logistics owner package | 2 | planned |
| `S1-D` | future worker | n/a | Integrate [Environment Runtime](../../../../../systems/environment/work/active/environment_runtime/README.md); ship seakeeping response to sea state; group command hierarchy on Joint relationships with naval formation roles. | ship motion response; naval command hierarchy content | environment state (owned by `systems/environment`); new Joint common-core fields | environment-consumer and hierarchy tests | sea state, day/night, and bathymetry reach ship motion through the environment query | after `S0-X` and Environment Runtime `P3-A` | 2 | planned |
| `S1-X` | main thread | n/a | Accept `CSG-S1`; throughput record; fidelity decision input. | stage acceptance record | — | stage validation plan | `G1`-`G2` gate met | after `S1-A..D` | 1 | planned |
| `S2-A` | future worker | n/a | Catapult and arresting-gear cycle; deck, elevator, hangar capacity. | carrier-aviation components/systems | aircraft flight model changes | deck-cycle tests | launch/recovery rates bounded by deck resources | after `S1-X` | 2 + 1 repair | planned |
| `S2-B` | future worker | n/a | Sortie generation, launch waves, recovery pattern, carrier landing. | carrier-aviation systems; Air-owner seam if needed | new Air flight dynamics | wave/CAP tests; landing tests | CAP stations sustained across cycles | after `S2-A` | 2 + 1 repair | planned |
| `S2-C` | future worker | n/a | Embarked helicopter operations; aircraft recovery fuel limits consumed from the shared fuel components. | embarked air ops | shared fuel and aerial-refuelling components (owned by `systems/physics`) | helicopter and recovery-fuel tests | fuel limits sortie radius through the shared path | after `S1-X`; parallel with `S2-A` | 2 | planned |
| `S2-X` | main thread | n/a | Accept `CSG-S2`; throughput record. | stage acceptance record | — | stage validation plan | `G3` gate met | after `S2-A..C` | 1 | planned |
| `S3-A` | future worker | n/a | Naval sensor platform adapters and group track reporting on the shared sensing and data-link deliverables; AEW content. | naval sensor adapters; AEW unit content | sensor physics and data-link mechanics (owned by `systems/sensing`, `systems/command-tasking`) | adapter and reporting tests | group picture forms through shared sensing and links | after `S2-X` and the sensing / command-tasking owner packages | 2 | planned |
| `S3-B` | future worker | n/a | Naval emission-control doctrine and ship ESM platform content on the shared EW deliverable. | naval EMCON doctrine; ship ESM content | EW mechanics (owned by `systems/sensing`) | EMCON doctrine tests | group emission state follows doctrine | after `S2-X` and the EW owner package; parallel with `S3-A` | 2 | planned |
| `S3-C` | main thread | n/a | Integrate the shared identification deliverable into naval ROE handling. | naval ROE/identity use sites | identification mechanics (owned by `systems/command-tasking`) | ROE-identity tests | ROE decisions read identity confidence | after `S3-A` | 1 + 1 repair | planned |
| `S3-D` | main thread | n/a | Verify no truth reads remain in naval surface sensing paths used by CSG scenarios. | naval sensor adapters | removal work in shared sensing (owned by `systems/sensing`) | truth-read guard test | guard passes for all `G4` CSG scenario paths | after `S3-A..C` | 1 + 1 repair | planned |
| `S3-X` | main thread | n/a | Accept `CSG-S3`; throughput record. | stage acceptance record | — | stage validation plan | `G4` gate met | after `S3-A..D` | 1 | planned |
| `S4-A` | future worker | n/a | Naval launch seams and platform loadouts for anti-ship missiles on the shared weapon families. | naval launch seams; weapon loadout content | missile guidance, fuze, and family models (owned by `systems/weapons`) | launch and engagement tests | ship- and air-launched missiles engage a ship through shared weapons | after `S3-X` and the weapons owner package | 2 + 1 repair | planned |
| `S4-B` | future worker | n/a | Ship fire-control channels, VLS, and layered air-defense doctrine. | naval air-defense systems; VLS path | interceptor missile models (owned by `systems/weapons`); new radar physics | interception and saturation tests | channel limits govern leak-through | after `S3-X`; parallel with `S4-A` | 2 + 1 repair | planned |
| `S4-C` | future worker | n/a | Ship decoy launchers and self-protection doctrine on the shared soft-kill deliverable. | ship decoy content and doctrine | soft-kill mechanics (owned by `systems/sensing` / `systems/weapons`) | soft-kill doctrine tests | ship decoys change terminal outcome through the shared path | after `S4-A` | 2 | planned |
| `S4-D` | future worker | n/a | Ship compartments and flight-deck capacity loss on the shared damage deliverable; retire the `DM-N1` synthetic profile or bind it to the shared path. | ship compartment content; naval damage profile | generic damage and damage control (owned by `systems/effects`) | damage chain tests | a hit degrades mobility, sensors, and deck capacity | after `S4-A` and the effects owner package | 2 + 1 repair | planned |
| `S4-X` | main thread | n/a | Accept `CSG-S4`; throughput record. | stage acceptance record | — | stage validation plan | `G5` gate met | after `S4-A..D` | 1 | planned |
| `S5-A` | future worker | n/a | Group fighter escort and intercept tasking on Air-owner seams; group use of stand-off jamming. | naval group tasking | air-combat mechanics (Air owner); jamming mechanics (`systems/sensing`) | escort/intercept tests | escort changes strike survival | after `S4-X` | 2 + 1 repair | planned |
| `S5-B` | future worker | n/a | Group strike planning and target assignment; magazine depletion. | scripted C2 for the group | learned planning | assignment tests | two-sided strikes run with depletion | after `S4-X`; parallel with `S5-A` | 2 + 1 repair | planned |
| `S5-C` | future worker | n/a | Downed-aircrew search and rescue by embarked helicopters. | embarked air ops; SAR task | ground combat | SAR tests | a downed crew can be located and recovered | after `S4-X`; parallel | 2 | planned |
| `S5-X` | main thread | n/a | Accept `CSG-S5`; throughput record. | stage acceptance record | — | stage validation plan | `G6` gate met | after `S5-A..C` | 1 | planned |
| `U1-A` | future worker | n/a | Submarine depth, speed, self-noise coupling; quiet running. | `submarine_motion_system.h`, platform fields | propagation | submarine motion tests | noise tracks speed and depth | after `S0-X`; parallel with `S1-*` | 2 | planned |
| `U1-X` | main thread | n/a | Accept `CSG-U1`. | stage acceptance record | — | stage validation plan | `G1`-`G2` gate met | after `U1-A` | 1 | planned |
| `U2-A` | future worker | n/a | Sonar platforms: hull, towed array, dipping sonar, sonobuoy fields, on the shared acoustic deliverable. | naval sonar platform adapters and content | propagation physics (owned by `systems/sensing`); acoustic environment ([Environment Runtime](../../../../../systems/environment/work/active/environment_runtime/README.md)) | sonar platform tests | detection depends on geometry and environment through shared paths | after `U1-X`, `S3-X`, and the undersea-sensing owner package | 2 + 1 repair | planned |
| `U2-B` | main thread | n/a | Verify no truth reads remain in undersea sensing paths used by CSG scenarios. | naval sonar adapters | removal work in shared sensing (owned by `systems/sensing`) | truth-read guard | guard passes for undersea paths | after `U2-A` | 1 + 1 repair | planned |
| `U2-X` | main thread | n/a | Accept `CSG-U2`. | stage acceptance record | — | stage validation plan | `G4` gate met | after `U2-A..B` | 1 | planned |
| `U3-A` | future worker | n/a | Torpedo tubes, launch, and submarine/ship loadouts on the shared torpedo family. | naval launch seams; loadout content | torpedo guidance, run, fuze, and countermeasure models (owned by `systems/weapons`) | torpedo engagement tests | torpedo engages and can be decoyed | after `U2-X`, `S4-X`, and the weapons owner package | 2 + 1 repair | planned |
| `U3-B` | future worker | n/a | Below-waterline compartments on the shared damage deliverable. | ship and submarine compartment content | flooding mechanics (owned by `systems/effects`) | damage tests | torpedo hit floods through the shared path | after `U3-A` | 2 | planned |
| `U3-X` | main thread | n/a | Accept `CSG-U3`. | stage acceptance record | — | stage validation plan | `G5` gate met | after `U3-A..B` | 1 | planned |
| `S6-A` | future worker | n/a | CSG outcome conditions on the shared adjudication and replay deliverables. | CSG scenario termination rules | generic adjudication and replay tooling (owned by `systems/weapons` and architecture) | termination tests | episodes end on adjudicated CSG outcomes | after `S5-X`, `U3-X`, and the adjudication owner package | 2 | planned |
| `S6-B` | future worker | n/a | Freeze reserved RL observation, action, and termination-event boundaries; scripted controller exercises them. | boundary docs; adapter seams | training | boundary tests | boundaries exercised end-to-end | after `S6-A` | 2 | planned |
| `S6-X` | main thread | n/a | Accept `CSG-S6` named and mirror. | stage acceptance record | — | stage validation plan | `G6` gate met | after `S6-A..B` | 1 | planned |
| `P5-A` | main thread | n/a | Close the package; sync indexes; archive. | this directory; naval owner README | late implementation | doc audits | acceptance record complete | after `S6-X` | 1 | planned |

## Dispatch Rules

- Every worker packet maps to exactly one cluster above.
- A cluster that consumes a system-owner deliverable waits for that owner's
  package to reach the named phase; it does not build a stand-in.
- Clusters that touch an Air-owner seam or `src/runtime/contracts/**` run
  serially.
- Do not let two workers edit the same scenario contract, public API, component
  schema, or status line at once.
- Acceptance clusters (`*-X`) and `P5-A` are serial and run on the main thread.
- If a cluster exceeds its round cap, stop and re-scope before any follow-up.
- Follow the [Subagent Usage Policy](../../../../../engineering/automation/standards/subagent_usage_policy.md).

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
cluster:
touched files:
commands/outcomes:
throughput (if the cluster runs a scenario): entities / step / sim duration / wall-clock / host
provenance (if the cluster adds content): source IDs, tiers, uncertainty
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan

Docs-only clusters:

```bash
python tools/maintenance/translate_docs_batch.py audit
python -m pytest -q tests/architecture/governance/test_document_link_audit.py
```

Implementation clusters (Windows host, from the worktree root):

```bash
cmake --build build-independent-win --target ef_test ef_py ef_composition_evidence_test
build-independent-win/ef_test.exe
python -m pytest -q tests/runtime/naval tests/architecture/composition tests/architecture/command_tasking
```

Stage scenarios that the local host cannot complete run on HEI; the packet
records the host.

## Acceptance Criteria

- Each stage acceptance record names its claim ceiling, validation outcomes,
  throughput record, and residuals.
- Each stage's named and mirror scenarios run on the maintained runtime.
- No stage claims a realism level higher than its evidence supports.

## Residual Map

Immediate:

- `P0-A` owner review.

Follow-on:

- a learned-policy package consuming the `S6-B` boundaries;
- mixed-rate stepping, only if the throughput records show uniform stepping
  cannot carry the full order of battle.

Deferred:

- land-based aviation, long-range anti-ship ballistic missiles, shore batteries,
  and space assets;
- deception and decoy networks beyond self-protection soft-kill.
