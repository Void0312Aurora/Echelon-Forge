# Carrier Strike Group Engagement Task Clusters

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/work/active/carrier_strike_group_engagement/carrier_strike_group_engagement_task_clusters_20260928.md`
Owner: `domains/naval`
Last verified: `2026-09-28`

Status: `2026-09-28` finite task-cluster plan for
[Carrier Strike Group Engagement](README.md). No cluster has started.

## Boundary Decision

This package may add naval, carrier-aviation, and undersea platforms and
mechanisms, the shared mechanisms each stage names, and the `CSG-*` scenario
ladder with its contracts and tests.

It must not:

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
| `P0-A` | main thread | n/a | Freeze scope, ladder, claim ceilings, and provenance policy. | this directory; naval owner README index | runtime code | doc link audit; bilingual audit | owner approves README, clusters, acceptance | first | 1 | active |
| `S0-A` | future worker | n/a | Order-of-battle research: both groups' ship, submarine, aircraft, weapon, and sensor lists with sources. | `docs/domains/naval/reference/csg_order_of_battle_*.md` | runtime content | provenance check: every row has source ID, tier, uncertainty | both sides' OOB tables complete | after `P0-A`; parallel with `S0-B` | 2 | planned |
| `S0-B` | future worker | n/a | Geodetic frame: earth curvature and a consistent geodetic-to-local frame shared by all domains. | shared frame component/system, sensor horizon use, tests | per-domain retuning | native + Python frame tests; air/naval regression suites unchanged | curvature-dependent tests pass; no regressions | after `P0-A`; **serial** (shared runtime) | 2 + 1 repair | planned |
| `S0-C` | future worker | n/a | Named unit content for both groups from `S0-A`. | `examples/config/database/**` (ships, submarines, aircraft, weapons, sensors) | new mechanisms | content-compile tests; unit spawn tests | every OOB row spawns with provenance | after `S0-A` | 2 + 1 repair | planned |
| `S0-D` | future worker | n/a | Group-composition scenario schema plus `CSG-S0` named and mirror scenarios. | scenario loader schema, `scenarios/naval/csg/`, `tests/contracts/unit/naval/csg/` | motion | scenario contract runner | both variants load and spawn the full OOB | after `S0-C` | 2 | planned |
| `S0-X` | main thread | n/a | Accept `CSG-S0`; first throughput record. | stage acceptance record | — | stage validation plan | `G0` gate met | after `S0-B`, `S0-D` | 1 | planned |
| `S1-A` | future worker | n/a | Group formation and screen geometry; route following. | naval command/formation components and systems | fleet doctrine beyond formation | formation-keeping tests | formation holds under turns | after `S0-X` | 2 + 1 repair | planned |
| `S1-B` | future worker | n/a | Ship turning-circle and speed response; damage-to-mobility coupling. | `ship_motion_system.h`, platform fields | full hydrodynamics | motion tests against sourced turning data | damaged ship loses speed through the maintained path | after `S0-X`; parallel with `S1-A` if write sets split | 2 + 1 repair | planned |
| `S1-C` | future worker | n/a | Ship fuel/endurance and replenishment scheduling for the group. | naval logistics system, stores | aviation fuel | logistics tests | endurance and replenishment observable in the scenario | after `S0-X`; parallel | 2 | planned |
| `S1-D` | future worker | n/a | Environment: sea state, wind, and day/night as scenario inputs, and the group command hierarchy on Joint relationships. | environment components; naval command hierarchy | weather forecasting; new Joint common-core fields | environment and hierarchy tests | sea state and day/night change motion and sensing through maintained paths | after `S0-X`; parallel with `S1-A..C` | 2 | planned |
| `S1-X` | main thread | n/a | Accept `CSG-S1`; throughput record; fidelity decision input. | stage acceptance record | — | stage validation plan | `G1`-`G2` gate met | after `S1-A..D` | 1 | planned |
| `S2-A` | future worker | n/a | Catapult and arresting-gear cycle; deck, elevator, hangar capacity. | carrier-aviation components/systems | aircraft flight model changes | deck-cycle tests | launch/recovery rates bounded by deck resources | after `S1-X` | 2 + 1 repair | planned |
| `S2-B` | future worker | n/a | Sortie generation, launch waves, recovery pattern, carrier landing. | carrier-aviation systems; Air-owner seam if needed | new Air flight dynamics | wave/CAP tests; landing tests | CAP stations sustained across cycles | after `S2-A` | 2 + 1 repair | planned |
| `S2-C` | future worker | n/a | Aircraft fuel state and aerial refuelling; embarked helicopter operations. | fuel/logistics components; embarked air ops | new tanker platforms beyond OOB | fuel and refuelling tests | fuel limits sortie radius | after `S1-X`; parallel with `S2-A` | 2 | planned |
| `S2-X` | main thread | n/a | Accept `CSG-S2`; throughput record. | stage acceptance record | — | stage validation plan | `G3` gate met | after `S2-A..C` | 1 | planned |
| `S3-A` | future worker | n/a | AEW aircraft sensing and track reporting. | sensor models; AEW content | fused multi-source estimation | AEW detection tests | AEW contributes tracks to the group picture | after `S2-X` | 2 | planned |
| `S3-B` | future worker | n/a | Data-link track sharing with latency and capacity. | data-link / command-link systems | full message-standard emulation | latency/capacity tests | shared picture degrades with link limits | after `S2-X`; parallel with `S3-A` | 2 + 1 repair | planned |
| `S3-C` | future worker | n/a | ESM, emission control, target identification. | ESM, EMCON, identification | deception | ESM/EMCON tests | emitting units are detectable; silent units are not | after `S2-X`; parallel | 2 | planned |
| `S3-D` | future worker | n/a | Remove truth reads from naval surface sensing paths. | naval sensor adapters | undersea sensing (in `U2-*`) | truth-read guard test | guard passes for all `G4` scenario paths | after `S3-A..C` | 2 | planned |
| `S3-X` | main thread | n/a | Accept `CSG-S3`; throughput record. | stage acceptance record | — | stage validation plan | `G4` gate met | after `S3-A..D` | 1 | planned |
| `S4-A` | future worker | n/a | Anti-ship missiles (air-, ship-, submarine-launched), reusing Air guidance and effects through owner seams. | weapon content; naval launch seams | new guidance laws | flight/terminal tests | missile reaches and engages a ship target | after `S3-X` | 2 + 1 repair | planned |
| `S4-B` | future worker | n/a | Layered ship air defense: area and point SAMs, CIWS, fire-control channels. | naval air-defense systems; VLS path | new radar physics | interception tests; saturation tests | channel limits govern leak-through | after `S3-X`; parallel with `S4-A` | 2 + 1 repair | planned |
| `S4-C` | future worker | n/a | Soft-kill: decoys and self-protection jamming against anti-ship missiles. | countermeasure systems | offboard deception networks | soft-kill tests | soft-kill changes terminal outcome | after `S4-A` | 2 | planned |
| `S4-D` | future worker | n/a | Leaker damage via compartments; damage control; capability loss including flight-deck loss. | naval effects routing; damage system | calibrated vulnerability claims | damage chain tests | a hit degrades mobility, sensors, and deck capacity through maintained paths | after `S4-A` | 2 + 1 repair | planned |
| `S4-X` | main thread | n/a | Accept `CSG-S4`; throughput record. | stage acceptance record | — | stage validation plan | `G5` gate met | after `S4-A..D` | 1 | planned |
| `S5-A` | future worker | n/a | Fighter escort and intercept; stand-off jamming. | Air-owner seams; EW systems | new air-combat doctrine | escort/intercept tests | escort changes strike survival | after `S4-X` | 2 + 1 repair | planned |
| `S5-B` | future worker | n/a | Group strike planning and target assignment; magazine depletion. | scripted C2 for the group | learned planning | assignment tests | two-sided strikes run with depletion | after `S4-X`; parallel with `S5-A` | 2 + 1 repair | planned |
| `S5-C` | future worker | n/a | Downed-aircrew search and rescue by embarked helicopters. | embarked air ops; SAR task | ground combat | SAR tests | a downed crew can be located and recovered | after `S4-X`; parallel | 2 | planned |
| `S5-X` | main thread | n/a | Accept `CSG-S5`; throughput record. | stage acceptance record | — | stage validation plan | `G6` gate met | after `S5-A..C` | 1 | planned |
| `U1-A` | future worker | n/a | Submarine depth, speed, self-noise coupling; quiet running. | `submarine_motion_system.h`, platform fields | propagation | submarine motion tests | noise tracks speed and depth | after `S0-X`; parallel with `S1-*` | 2 | planned |
| `U1-X` | main thread | n/a | Accept `CSG-U1`. | stage acceptance record | — | stage validation plan | `G1`-`G2` gate met | after `U1-A` | 1 | planned |
| `U2-A` | future worker | n/a | Propagation model, active sonar, towed array. | acoustic model; sonar system | full ocean model | sonar tests | detection depends on geometry and environment | after `U1-X`, `S3-X` | 2 + 1 repair | planned |
| `U2-B` | future worker | n/a | Dipping sonar and sonobuoys; submarine truth-read removal. | ASW sensors; sonar adapters | — | ASW tests; truth-read guard | guard passes for undersea paths | after `U2-A` | 2 | planned |
| `U2-X` | main thread | n/a | Accept `CSG-U2`. | stage acceptance record | — | stage validation plan | `G4` gate met | after `U2-A..B` | 1 | planned |
| `U3-A` | future worker | n/a | Heavyweight and lightweight torpedoes: guidance, run, fuze; countermeasures. | torpedo components/systems; content | wake-homing beyond sourced data | torpedo tests | torpedo engages and can be decoyed | after `U2-X`, `S4-X` | 2 + 1 repair | planned |
| `U3-B` | future worker | n/a | Below-waterline damage and flooding path. | naval damage routing | calibrated vulnerability | damage tests | torpedo hit floods through maintained path | after `U3-A` | 2 | planned |
| `U3-X` | main thread | n/a | Accept `CSG-U3`. | stage acceptance record | — | stage validation plan | `G5` gate met | after `U3-A..B` | 1 | planned |
| `S6-A` | future worker | n/a | Outcome and termination adjudication; whole-engagement replay. | scenario termination; replay tooling | victory-condition doctrine beyond the stated rules | termination tests | episodes end on adjudicated outcomes | after `S5-X`, `U3-X` | 2 | planned |
| `S6-B` | future worker | n/a | Freeze reserved RL observation, action, and termination-event boundaries; scripted controller exercises them. | boundary docs; adapter seams | training | boundary tests | boundaries exercised end-to-end | after `S6-A` | 2 | planned |
| `S6-X` | main thread | n/a | Accept `CSG-S6` named and mirror. | stage acceptance record | — | stage validation plan | `G6` gate met | after `S6-A..B` | 1 | planned |
| `P5-A` | main thread | n/a | Close the package; sync indexes; archive. | this directory; naval owner README | late implementation | doc audits | acceptance record complete | after `S6-X` | 1 | planned |

## Dispatch Rules

- Every worker packet maps to exactly one cluster above.
- Clusters that touch shared runtime surfaces (`S0-B`, any Air-owner seam, any
  `src/runtime/contracts/**` change) run serially.
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
