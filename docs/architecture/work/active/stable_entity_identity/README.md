# Stable Entity Identity For Stochastic Draws

Status: `2026-10-08` bounded implementation integrated on `main`: the #74-#78 stable-identity stack merged 2026-09-30 and the #82-#85 Ground stack followed 2026-10-01, including Ground direct-fire draw-site integration. P0-P5 and the original review HOLD/repairs remain historical evidence. Raw-Flecs-id semantic-reference portability is still a separate residual.

Language:
- English canonical: `README.md`
- Chinese companion: not required yet; high-churn implementation slice (English-only).

Document kind: `task`
Lifecycle: `active`
Canonical: `docs/architecture/work/active/stable_entity_identity/README.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-09-30`

Inputs:

- Defect record `docs/architecture/work/issues/stable_entity_identity_for_stochastic_draws.md`.
  It is on `work/army-mechanisms`, where the defect was found, so read it there with
  `git show`. This package supersedes its design section. It is not imported here, so that
  army's copy does not conflict when army integrates main.
- [Runtime composition baseline](../../../standards/runtime_composition_baseline.md)
- [Simulation conventions](../../../standards/simulation_conventions.md) (determinism)
- [Subproject creation standard](../../../../engineering/automation/rules/subproject_creation_standard.md)

## Defect

Every per-engagement and per-detection stochastic draw mixes **raw Flecs entity ids** into
its seed. A Flecs id is an allocation handle, not an identity. It moves with the
composition (component and system registrations), with earlier spawns, and with the
generation recycled after `reset()`, and the recycle list is LIFO. So outcomes change
when the census changes, when unrelated units spawn first, and between the first and later
episodes after `reset(seed)` on one kernel. Sites 3, 5, 6 and 7 below are also
**seed-blind**: they mix only time and ids, never the reset seed.

Measured on `2026-09-28` (Windows MSVC, `cfb9924e`) for
`test_phase2_fire_suppression_integrity_reduces_fire_cascade_growth`: an E-3 target, three
profiled blast-fragmentation hits, then 80 steps.

| Variation, nothing else changed | Ids (attacker, target) | Outcome |
| --- | --- | --- |
| baseline | `581, 586` | survives 80 steps |
| 1 / 2 / 3 unrelated units spawned first | `582,587` / `583,588` / `584,589` | removed at step 1 / 12 / 1 |
| same kernel, `reset(20260529)`, episode 0 | `0x245, 0x24a` | survives |
| same kernel, same reset, episodes 1–3 | `0x1_0000_024a…` | removed at step 1 |

## Main-Branch Inventory (`9ee4558e`)

| # | Site | Draw | Id inputs | Seed-aware |
| --- | --- | --- | --- | --- |
| 1 | `src/core/engine/simulation_kernel_damage_debug_api.cpp` `make_debug_synthetic_missile_seed` (3 callers) | synthetic `Missile::rng_state` | attacker, target | via 2 `mt19937` draws |
| 2 | `src/core/engine/simulation_kernel_weapon_release_service.cpp` ~811, missile release | fired `Missile::rng_state` | attacker, target | via 2 `mt19937` draws |
| 3 | same file ~1051, naval gun/CIWS | hit roll | attacker, target | no |
| 4 | Ground direct fire (`fire_ground_weapon`) | hit roll | attacker, target | not on main. `DrawSite` value 4 is reserved; army converts it |
| 5 | `src/models/systems/default_sensor_model.cpp` ~383 | detection plus range, bearing and Doppler noise | owner, target | no |
| 6 | `src/models/systems/default_acoustic_model.cpp` ~172 | detection plus bearing and range noise | owner, target | no |
| 7 | `src/core/engine/simulation_kernel_command_api.cpp` 170, 187, 240, 356 | command-link drop roll | entity | no |

Sites 1–2 seed the munition's `rng_state`, which its downstream draws inherit: fuze
reliability in `damage_system_common.h`, component failure in the effects model, and the
legacy splash roll.

- **Primitive copies.** There are five private splitmix64 copies: command_api,
  weapon_release_service, the sensor model, the acoustic model, and
  `models/weapons/detail/default_effects_geometry_detail.h`. There is also
  `damage_splitmix64` in `systems/combat/damage_system_common.h`. The last two are **stream
  steps** on an existing state, and they are different streams. The geometry step is Weyl
  form: `state += γ; out = mix(state)`. The damage step is feedback form:
  `state = mix(state + γ)`.
- **`std::mt19937 rng`.** It is reseeded only in `SimulationKernel::reset`
  (`simulation_kernel.cpp` ~142). It is drawn only at site 1 (two draws) and site 2 (two
  draws).
- **Creation points (entities carrying `KeyEntity`).**
  - `default_unit_factory.h`: the root at ~648; the `<unit>_Stn_<n>` munitions at ~822
    (`child_of`, created in `std::unordered_map` iteration order); the embarked helo at
    ~1548, created by recursive `spawn` plus `child_of`.
  - Weapon-release missile at ~957.
  - EW chaff and flare in `systems/systems/ew_system.h` ~30 and ~63, created inside a
    system and therefore deferred.

  The kernel `spawn_unit` adds `SimObject` to the root only. The three debug synthetic
  missiles carry no `KeyEntity` and are not participants. There are no flecs observers in
  `src/`.
- **Layering** (`tools/architecture/cpp_include_graph.py`). models, systems and core_engine
  can all reach `core_interfaces` and `components`, and nothing above those.
- **Census** `83 components / 2 kernel systems / 34 systems`, pinned at:
  - `system_contribution_registry.cpp:286,296`;
  - `tools/maintenance/runtime_composition_evidence_contract.py` ~166;
  - `test_runtime_composition_evidence_contract.py:57–60`;
  - `test_runtime_profile_projection_contract.py:46`;
  - `test_simulation_composition_contract.py:188,212`;
  - `src/tests/test_composition_lifecycle.cpp:624,646`.
- **CPU-reference CUDA `ef_test` cases** pinned raw id base `581` on main. P2-A fixes this
  with `817fcefc` (a verbatim `-x` pick of army `dbc616fe`, itself a pick of LHG `ae9de540`)
  plus `caad87f1`.
- **CUDA/GPU** (scanned `2026-09-29`). No copy of any seed formula exists. The only shared
  constant is γ, used in `src/gpu/gpu_interaction_broadphase_runtime_cuda.cu` as a spatial
  broadphase hash. CUDA-resident code carries reset seeds as passthrough metadata, computes
  no detection, hit, fuze or drop outcome, and never touches `rng_state`. No CPU/CUDA
  divergence can arise from this package.

## Decisions

1. **Serial assignment: explicit stamping through one creation primitive, not an
   observer.**
   - An observer would be an executable contribution. The registry has no observer row
     kind, so admitting one means a new composition row kind across the manifest, the Cordis
     bundle, the projection and the closure. Hand-registering one in kernel source is the
     unadmitted channel that `test_simulation_composition_contract.py` already forbids for
     `ecs.system<`.
   - The primitive is `stamp_stable_serial(flecs::entity)`, applied at the moment `KeyEntity`
     is set on each of the 5 creation paths.
   - A structural guard makes it non-bypassable at the source level: `set<KeyEntity>` is
     forbidden in `src/` outside those stamped paths.
   - A runtime coverage test asserts that every `KeyEntity` entity carries a serial after
     spawn, fire and step.
   - The primitive refuses to re-stamp.
   - Deferred EW creation increments the singleton counter in system iteration order. This
     is P1 item E3.
2. **State: one world singleton `StableIdentityState { next_serial; episode_seed; }`** in
   `components/basic`, the owner of identity. `reset(seed)` rewrites it, restarting the
   counter at 1 and capturing the seed. Model code running on the flecs world alone reads
   it. **Census delta: 83 → 85** (`StableEntitySerial`, `StableIdentityState`); both
   system counts are unchanged.
3. **Helper: `src/core/interfaces/stochastic_draw.h`.** This is the cross-layer draw-seed
   contract, header-only and pure:

   ```cpp
   std::uint64_t draw_seed(const flecs::world&, DrawSite, double sim_time_s,
                           std::initializer_list<flecs::entity> participants,
                           std::initializer_list<std::uint64_t> words = {});
   ```

   - `DrawSite` values are fixed and append-only. Value 4 is reserved for Ground direct fire.
   - The header also owns `uniform01(seed)`, `lane(seed, tag)` (which replaces the sites'
     xor constants), and the two stream steps. The stream steps are kept **bit-identical**
     and named by form: `splitmix64_weyl_next` and `splitmix64_feedback_next`.
   - Sites 1–2 keep their two `mt19937` draws, in the same order, and pass the 64-bit word as
     `words`, so the mt19937 stream position is unchanged. Replacing mt19937 is out of scope.
4. **Missing serial.**
   - At the public API boundaries (the debug hit APIs, the command API and
     `fire_naval_weapon`), a caller-supplied id without a serial is rejected with a warning,
     on the same path as an invalid id.
   - Inside `draw_seed` it is an invariant violation, and the helper aborts with the site and
     entity. It does not throw, because sites 5–6 run inside flecs systems where exceptions
     cannot cross the C frames.
   - There is no fallback to the raw id or to 0.
5. **Guard.** A pytest scans `src/core`, `src/models`, `src/systems` and `src/components`,
   excluding `src/tests` by layer, and fails on any of:
   - a splitmix or seed constant literal outside `stochastic_draw.h`;
   - the `2^53` uniform literal;
   - `^`, `*const` or `<<` applied to an identifier matching `\w*_id\b` or `.id()`;
   - `uint64_t(<time> * k)` quantization.

   `src/gpu` is out of the guard's scope by layer, since it computes no stochastic outcome.
   The guard forces army to convert its site 4 when it integrates main. Calibration is P1
   item E4.
6. **WorldBatch.** `reset_batch(seeds)`, `world_batch_setup::apply_world_setup` and the
   setup path already call each world's `reset(resolve_reset_seed(i, …))`. The singleton
   captures that seed, so no WorldBatch change is needed. `world_index` is not mixed into the
   seed: equal seeds mean an equal episode, and per-world diversity comes from the seeds the
   caller supplies.
7. **Semantic reference: separate follow-up.**
   - `default_runtime_host_batch_semantic_reference.v1.json` has 6 raw `entity_id` fields.
     The parity file `…windows_msvc.v1.json` has 12. `world_index` accompanies only the 2
     `action_inputs` rows.
   - Re-keying them by `(world_index, serial)` needs the serial on the facade observation
     surface, which is a runtime-facade DTO change, plus capture changes
     (`runtime_host_batch_parity_contract.py` `_refs`, `_pilot_actions` and the observation
     rows).
   - This package recaptures the files once, in P4. The follow-up's entry condition is that
     the serial is exported on the facade.
8. **Test plan.** See the acceptance gate for the node mapping.
9. **CUDA.** None found (see inventory). The obligation is recorded: any future device-side
   stochastic outcome must mirror `draw_seed` and add a parity test.

Also held out of scope: two draws at the same site with the same participants in the same
millisecond stay correlated, exactly as today. No occurrence counter is added.

## P1 Evidence Items (unverified at P0)

| Id | Question | Safer default already decided |
| --- | --- | --- |
| E1 | Station children are created in `unordered_map` order, which differs between MSVC and libstdc++ | create them in ascending station order |
| E2 | Does `ecs.entity("<unit>_Stn_<n>")` always yield a fresh entity when the same type is spawned again? | the primitive refuses to re-stamp (loud) |
| E3 | Inside EW systems, does deferred `get_mut<StableIdentityState>` increment immediately and in order? | stamp through the singleton, never through the command queue |
| E4 | Does the guard flag exactly the main sites and nothing else? Negative controls on a tmp tree | the guard lands with its calibration test |
| E5 | Which native raw-world tests reach draw sites without the singleton? | a test fixture installs the state; the helper never defaults |
| E6 | Reproduce the E-3 table on the main build, on HEI and on Windows | the P2 baseline for the invariance nodes |
| E7 | Does `delete_with<SimObject>` cascade to `ChildOf` children in flecs v4.0.0 `eeb9eaa6`, leaving no stale serial? | coverage test after `reset` |
| E8 | Does LHG P4-B transfer world singletons? | the obligation below names the singleton explicitly |

### P1 Findings (code reading, `2026-09-29`)

Answered by reading `9ee4558e` and the pinned flecs source. E6 and E7 are measurements and
are recorded separately.

- **E1: confirmed defect.** Station munitions are created by iterating
  `def.default_loadout`, an `std::unordered_map<int, std::string>`
  (`content/unit_definition.h:196`), in `spawn_default_loadout_stores`
  (`default_unit_factory.h:809`). Creation order is bucket order and differs between MSVC
  and libstdc++. **P2:** iterate in ascending station order. The change is local to that
  function.
- **E2: confirmed defect, so the re-stamp refusal carries real load.** `ecs.entity(name)`
  resolves the name at root scope before `.child_of(e)` applies (flecs `entity.hpp:68`,
  `entity.c:1882`). `mun_name` is built from the unit *type* name, so a second spawn of the
  same type finds the first spawn's `<type>_Stn_<n>` and re-parents it instead of creating
  a new child. **P2:** create station munitions as scoped children, with the parent set in
  the entity descriptor or created unnamed under the parent, so every spawn gets fresh
  children. Keep the re-stamp refusal. This is a pre-existing identity bug; the package
  fixes it because a serial cannot be stable on a shared entity.
- **E3: safe as designed.** The EW chaff and flare systems run deferred, so entity creation
  is queued. `get_mut` on a world singleton writes to live storage, so increments take
  effect immediately, in iteration order. **P2:** stamp through `get_mut`, never through a
  `set` command.
- **E5.** `src/tests/test_structural_failure_system.cpp` builds 14 raw worlds without a
  kernel. None of them reach a draw site today. **P2:** give the native test fixture an
  explicit state installer, and give these tests the installer only when a converted path
  reaches them.
- **E8: no singleton channel exists.** LHG P4-B serializes entities through
  `query<SimObject>()`, and kernel-level state through dedicated channels
  (`serialize_rng`, `serialize_clock`, `serialize_episode_barrier`). **Obligation:**
  `StableEntitySerial` joins the per-entity field set, and `StableIdentityState` needs its
  own `serialize_/restore_stable_identity_state` pair.
- **E9: one crash path, now designed out.**
  - Sensor and acoustic targets come from `query<const KeyEntity, const Transform>`, so every
    target has `KeyEntity`.
  - The debug synthetic missiles carry no `KeyEntity` and never enter those queries.
  - The naval-gun/CIWS site (`weapon_release_service.cpp` around 1051) looks its target up
    by raw id, with no `KeyEntity` gate, so a missile without a serial would reach
    `draw_seed` and abort. **P2:** check at that boundary. `fire_naval_weapon` rejects a
    target without a serial, on the invalid-target path. `draw_seed` keeps the abort as
    an invariant.
- **E4: guard calibration.**
  - The constant and `2^53` patterns match only the known sites.
  - The time-quantization pattern must also match `static_cast<std::uint64_t>`; the
    acoustic site uses the qualified form.
  - The id-arithmetic pattern must require an operator applied to the id. Otherwise it
    flags plain uses of `.id()` as an event key (`structural_consequence_system.h:213`,
    `structural_failure_system.h:541`) and entity lookups (`default_guidance_model.cpp:1394`,
    `track_manager_system.h`).
  - It correctly flags one genuine non-draw use: `ship_motion_system.h:246` derives the
    ship-motion phase from `id() % 1024`. That phase moves with the census and with
    spawn order, which is the same defect class in a deterministic value. **P3:** derive
    the phase from the serial. Do not exempt it.

### P1 Findings (measurement on HEI, `2026-09-29`)

- **E6: the defect reproduces on main.** Measured with the release build of `9ee4558e` on
  Linux GCC. The scenario is the E-3 target with three profiled blast-fragmentation hits,
  then 80 steps.

  | Variation | Ids (attacker, target) | Outcome |
  | --- | --- | --- |
  | baseline | `581, 586` | survives 80 steps |
  | 1 unrelated pre-spawn (MQ-9) | `582, 587` | removed, step 1 |
  | 2 unrelated pre-spawns | `583, 588` | removed, step 12 |
  | 3 unrelated pre-spawns | `584, 589` | removed, step 1 |
  | one kernel, `reset(20260529)`, episode 0 | `0x245, 0x24a` | survives |
  | same kernel, episode 1 | `0x1_0000_024a, 0x1_0000_0246` | removed, step 1 |
  | episode 2 | `0x2_0000_024a, 0x6_0000_024b` | removed, step 1 |
  | episode 3 | `0x3_0000_024a, 0x5_0000_0246` | removed, step 1 |

  The outcomes match the `work/army-mechanisms` record exactly. Main's ids differ only
  because main's census is 83. The ids differ, but the per-variation pattern is the same.
  This table is the P2 baseline for the invariance node. Probe: `SimulationKernel()`,
  `reset`, `load_database`, `spawn_unit`, then `debug_apply_profiled_local_proximity_hit`
  with a `WarheadProfile`, then step and poll `is_unit_active(target)` each step.
- **E7: reset deletes the children.**
  - Source: flecs `bootstrap.c:880` sets `(ChildOf, OnDeleteTarget, Delete)`, so
    `delete_with<SimObject>()` cascades to station munitions and the embarked helo.
  - Measured on the root only: `get_all_units()` goes from 1 to 0, and
    `is_unit_active(root)` goes from true to false. No Python surface can see the children,
    so their deletion is taken from the source. P2's coverage test checks it natively.
  - Re-spawning after reset recycles the index with a new generation (`0x245` becomes
    `0x1_0000_0245`), as the record states.

P1 exit met: E1–E9 are answered. E2 and E1 bring two pre-existing factory identity bugs into
P2. E9 adds one boundary check.

## Phase Plan

Builds and tests run on **HEI**: `ssh HEI`, not `HEI-WIRED`. The worktree there is
`~/Workshop/CMO/.worktrees/stable-identity` on this branch.

- Build: `cmake --build build-si-linux -j32`.
- Tests: `CMO_BUILD_DIR=… bash tools/maintenance/cmo_env.sh python -m pytest …`.
- Baseline: `ef_test` 174/174; `tests/runtime/air_combat` 344 passed / 39 xfailed.

The Cordis producer (`npm`) and the `windows_msvc` parity capture run on the Windows host.
There, force a rebuild of the TUs that depend on any edited header, and add a negative
control, because of the `#deps 0` hazard. Commit per topic. Never push.

| Phase | Entry | Exit |
| --- | --- | --- |
| `P0 Boundary` | the dispatch | this README plus index entries committed; coordinator review |
| `P1 Evidence` | P0 reviewed | E1–E9 answered, with measurements recorded here. **Met `2026-09-29`**, see the findings above |
| `P2 Seam` | P1 | `git cherry-pick -x dbc616fe e674672d` first. Then the components, singleton, primitive, helper, reset wiring and guard, the native seam tests, and the census pins 83→85. Composition evidence is knowingly red until P4 |
| `P3 Sites` | P2 | sites 1–3 and 5–7 converted, and the ship-motion phase moved to the serial; private copies deleted; stream steps bit-identical (fuze and failure draws unchanged for an equal `rng_state`); guard green. **Met `2026-09-29`**, see `SI-P3` |
| `P4 Evidence + re-decision` | P3 | evidence regenerated in the order below; Air marker table complete; all gates at or above baseline. Evidence regeneration (`SI-P4-A`) **met `2026-09-29`** (`90661466`); Air marker table and re-decision (`SI-P4-B`) **met `2026-09-29`** (`9676a250`): all 3 changed nodes rewritten to K = 16 seeds with premise/property splits, no real finding under rule 8, Air 355p/38xf/0F (was 352p/38xf/3F), naval and ground unchanged |
| `P5 Acceptance` | P4 | one independent review; accepted, or held with a named blocker. **Round 1 `2026-09-30`: HOLD, then fixed** (see Review Record). Every finding is addressed; no second review round, per the owner's cadence |

Regeneration order for P4:

1. Census pins, including `packages/cordis-runtime/test/producer.test.mjs:90`.
2. `python -m tools.maintenance.runtime_profile_projection_contract generate` (this step regenerates the profile projection; the tool name previously read `runtime_composition_projection_contract`, which instead regenerates the request/lock/authority fixtures and leaves the projection stale — corrected `2026-09-29` per `SI-P4-A`).
3. Re-pin the raw-byte sha256 values, first in `packages/cordis-runtime/profiles/default-compatibility.bundle.json`, then in `packages/default-compatibility.package.json`.
4. In `packages/cordis-runtime`, run `npm ci`, then `node src/cli.mjs produce --out <dir>`.
5. Adopt the provenance and diagnostics fixtures.
6. Rebuild the native binaries and `ef_py`.
7. `python -m tools.maintenance.runtime_host_batch_parity_contract capture --native-binary <exe> --node node --refresh-semantic-reference`.
8. `python -m tools.maintenance.runtime_composition_migration_closure generate`, then `npm test`.

The raw-byte-pinned files are `-text` with LF endings (`.gitattributes` lines 10–14 and
18–22). Army commit `b0a17ab1` is one worked run of this order.

## Task Clusters

Owner: the main thread dispatches. Run serially, in order. No agent may push. Reasoning
effort is steered by the prompt because the tool has no reasoning parameter.

| Cluster | Tier / model ID / reasoning | Goal | Host | Gate |
| --- | --- | --- | --- | --- |
| `SI-P1` | moderate / sonnet / medium | answer E1–E8 (read and measure only) | HEI plus Windows | the evidence table is filled in |
| `SI-P2-A` | main thread (trivial) | the two `-x` cherry-picks | Windows | **pass `2026-09-29`**: `4bd90a3c`, `8f0ffd42`; HEI `ef_test` 174/174 (19646 assertions), CUDA lifecycle guard 5 passed |
| `SI-P2-B` | high / opus / high, adversarial | serial, singleton, primitive, helper, guard, native seam tests, census pins | HEI | **pass `2026-09-29`** on HEI (`a1114fcd` plus this branch): `ef_test` 182/182 (20817 assertions); air_combat 352p/39xf, unchanged from main; naval 66p, ground 12p. governance has main's 3 reds, structural has main's 2 WP22 reds, composition 5F+9E is stale evidence for P4. The guard moved to `SI-P3` |
| `SI-P3` | moderate / sonnet / medium | the Decision 5 guard with its calibration test (landed first as strict xfail), then per-site conversion, copy removal and stream consolidation | HEI | **pass `2026-09-29`**. Written on army (`325f4ed6`..`92d6539c`) and ported with `-x`. The site 2–4 commit was adapted to sites 2–3 (`344ec39f`), and the site 4 half of the native test was dropped (`b974df0d`). HEI measurements at `b974df0d`: `ef_test` 187/187 (20887 assertions); the guard and its calibration pass; `structural_boundaries` shows only main's 2 WP22 reds; governance shows main's 3 reds; composition 5F+9E is stale evidence for P4. Air goes from main's 352p/39xf to 352p/38xf/3F, and naval 66p and ground 12p are unchanged. The three changed Air nodes are listed under P4-B |
| `SI-P4-A` | moderate / sonnet / medium | evidence regeneration steps 1–8 | Windows (npm, msvc capture) | **pass `2026-09-29`** (`90661466`): composition 72 passed/1 skipped; `npm test` 20/20; `ef_test` 187/187 (20887 assertions, matches `SI-P3`); governance shows only main's 3 reds. Step 2's tool name in the regeneration order above is stale — `runtime_composition_projection_contract` regenerates the request/lock/authority fixtures, not the profile projection; `tools/maintenance/runtime_profile_projection_contract.py` is the correct tool and was used. Entity_id in the parity fixture is unchanged at 581; no kinematic or other non-hash value moved. P4-B still open |
| `SI-P4-B` | moderate / sonnet / high | run the Air suite and fill the re-decision table | HEI | **pass `2026-09-29`** (`9676a250`): all 3 changed nodes rewritten to K = 16 fixed seeds with premise/property splits (node 1 premise 10/16, node 2 premise 4/16, node 3 premise 14/16); node 3's stale strict xfail removed; no real finding under rule 8; Air 355p/38xf/0F/219 subtests in 53.56s (was 352p/38xf/3F/219 subtests in 50.17s at `3dc2b718`); naval 78p/4 subtests (66 naval + 12 ground) unchanged |
| `SI-P5` | high / opus / high, independent | the single stage-acceptance review | HEI plus Windows | **round 1 HOLD → fixed `2026-09-30`**. Fixes landed on the main thread in `0e9adee4`, `e0405910`, `e4533683`, `0eec74de`, `edf352b5`, `a9acec13` and `1f47eeec`. Measured locally (Windows MSVC): `ef_test` 190/190, and `-ts=*stable*` passes in isolation; air_combat plus structural plus composition give 445 passed / 1 skipped / 38 xfailed / 2 failed, the 2 being main's WP22 reds |

### P3 Changed Air Nodes (input to SI-P4-B)

Measured on HEI with main plus this branch at `b974df0d`. The baseline is main `a1114fcd`, 352 passed / 39 xfailed.

| Node | Main | After P3 | First reading |
| --- | --- | --- | --- |
| `test_consumer_validation.py::…::test_mlf7_stabilator_component_damage_stays_bounded_without_tail_loss` | pass | fail (`StopIteration`) | reaches the site 1 draw through `debug_apply_profiled_local_proximity_hit`; the cause is not yet confirmed |
| `test_warhead_and_component_damage.py::…::test_phase2_fire_suppression_integrity_reduces_fire_cascade_growth` | pass | fail | the E-3 scenario of the defect table. On main it passes only in the baseline arrangement, which the invariance node shows is draw luck |
| `test_warhead_and_component_damage.py::…::test_shot_effect_record_links_fuze_geometry_warhead_part_entry_and_consequence_hook` | xfail (strict) | XPASS (strict, fails) | the strict marker's expectation now holds under the stable draw |

P4-B re-decides each row across K seeds, as the Acceptance Gate requires. It does not re-tune anything or flip a marker silently.

### SI-P4-B Re-Decision (K = 16 seeds per node, HEI)

Each node was rewritten to run its scenario over a fixed list of K = 16 seeds
(`BASE + 97*i`), split into a premise (the scenario reached the state the test is about) and
a property (what the test claims), asserting the property in full only on premise-satisfying
seeds, and counting (not silently skipping) premise failures. A non-vacuity assertion
requires at least one seed to satisfy the premise. Measured on HEI at `9676a250`.

| node | marker reason | main (K=32) | package (K=32) | decision | evidence |
| --- | --- | --- | --- | --- | --- |
| 1 `test_mlf7_stabilator_component_damage_stays_bounded_without_tail_loss` | none (was an unconditional pass on main) | 26/32 | 21/32 | rewritten to K = 16 seeds (`BASE=20260618`); premise (a `left_horizontal_tail_actuator_or_surface_component` damage event exists) holds on 10/16; property (bounded damage, no tail loss) holds on every premise-satisfying seed | HEI `9676a250`: passes; premise 10/16 |
| 2 `test_phase2_fire_suppression_integrity_reduces_fire_cascade_growth` | none (was an unconditional pass on main) | 4/32 | 8/32 | rewritten to K = 16 seeds (`BASE=20260529`); premise (the E-3 target survives both the initial hits and the 80-step window, in both the intact and degraded runs) holds on 4/16; property (fire-suppression integrity reduces cascade growth) holds on every premise-satisfying seed | HEI `9676a250`: passes; premise 4/16 |
| 3 `test_shot_effect_record_links_fuze_geometry_warhead_part_entry_and_consequence_hook` | stale: "the direct aileron hit no longer produces `component_failure_count > 0`" | xfail (strict) holds on all 32 (the marker's premise) | 29/32 satisfy `component_failure_count > 0`; 31/32 XPASS (strict, fails) | strict xfail marker removed; rewritten to K = 16 seeds (`BASE=20260607`); premise (`component_failure_count > 0`) holds on 14/16; the full property (every original assertion, verbatim) holds on every premise-satisfying seed | HEI `9676a250`: passes; premise 14/16 |

No real finding under rule 8 (a premise-satisfying seed with a failing property) was
observed on any of the 3 nodes.

Air suite after the rewrite (HEI `9676a250`, `tests/runtime/air_combat`): 355 passed, 38
xfailed, 0 failed, 219 subtests passed, 53.56s. Baseline at `3dc2b718` (before this package's
3 nodes were rewritten): 352 passed, 38 xfailed, 3 failed, 219 subtests passed, 50.17s. The
plan's "xfail count 38 minus 1 = 37" arithmetic double-counted node 3: main's 39 xfailed
already dropped to 38 at P3 when node 3's marker XPASS'd (strict, counted as 1 of the 3 F,
not as an xfail), so removing that same marker in P4-B does not change the xfail count again
— it converts that 1 F (and the other 2 F from nodes 1-2) back to passes. 38 xfailed is
therefore the correct unchanged count; 352 + 3 = 355 passed. Runtime grew by about 3.4s, well
under the ~20s flag threshold.

`tests/runtime/naval tests/runtime/ground` (HEI `9676a250`): 78 passed (66 naval + 12
ground), 4 subtests passed — unchanged from the P3 baseline.

### Review Record

Round 1 was independent and run at `ba17b647` on `2026-09-30`. Verdict: **HOLD** on one
blocker. All findings are fixed, and none needed new calibration.

| Finding | Class | Disposition |
| --- | --- | --- |
| B1: firing at a target whose track outlived it aborted the process. ContactList keeps dead ids for track memory, and `draw_seed` aborts on a non-live participant. Reproduced for `fire_missile` and a DDG deck gun | blocking | **Fixed** in `e4533683`. `fire_missile` now rejects a dead or serial-less target before its two mt19937 draws. `fire_naval_weapon` keeps main's visible behaviour (the shot is consumed and the call returns true) and draws only for a live target. Regression tests are in `edf352b5` (ready_count goes 10 → 9 for both a live and a dead target) |
| S1: the draw guard missed an id on the right of an operator (`seed_base ^ target.id()`), `+`, the functional-cast forms and `* 1e3` / `* 1000`, and flagged `grid_id * cell_area` | should-fix | **Fixed** in `0e9adee4`. The id rule is scoped to entity-id names plus `.id()`, and each form is a calibration case |
| S2: the Decision 1 guard (`set<KeyEntity>` only on stamped paths) did not exist | should-fix | **Fixed** in `e0405910`, `test_key_entity_stamping_guard.py`, which asserts the exact admitted file set and that each file calls `stamp_stable_serial` |
| S3: sites 1, 3 and 7 checked only A == A, and the census-change invariance node was missing | should-fix | **Fixed** in `edf352b5`. It adds A ≠ B checks on the drawn seed or roll, plus a native census-change case (23 extra entities move raw ids, while serials and seeds stay the same) |
| N1: the ship-motion phase fell back to 0 without a serial | nit | **Fixed** in `0eec74de`, which makes it an invariant violation |
| N2: "invariant under unrelated pre-spawns" overstated the guarantee, because serials count creation order within an episode | nit | **Fixed** in `1f47eeec`. The claim now reads: invariant to the census and to raw-id movement, not to within-episode creation order. The node fences pre-spawns before `reset` and covers ×1–4. It is non-vacuous: on the pre-package main build the same variations give alive / alive / removed@38 / removed@0 / alive |
| `test_air_combat_post_launch_assessment` flake: `WorldBatchVecEnv` draws its reset seed from global `np.random`, and sites 5 and 7 are now seed-aware | real, legitimate | **Fixed** in `a9acec13`, which pins `env.seed(20260618)`. 20 of 20 runs pass across `np.random` states, including 101 and 152, the two the review found failing |

Confirmed by the review with no change needed: the stream steps are bit-identical; layering
is respected; the E1/E2 station children resolve by name under the launch resolver; the
SI-P4-B rewrites weakened no assertion; and the SI-P4-A evidence differs only in hashes and
timing.

One more defect was found while writing S3. A native test that registers *new C++
component types* in a kernel world poisons the process-wide flecs type-id cache for later
kernels, which is the same class as `3dc2b718`. The census case therefore models extra census
as extra entities, and its comment records why.

Landing review, 2026-09-30. The automated PR review on #74–#78 found no blocking issue and
made two suggestions:

| Suggestion | Disposition |
| --- | --- |
| #78, P3: the header carried two status narratives | **Fixed.** A single current status remains, and `Last verified` moved to `2026-09-30`. |
| #76, P2: the three premise/property rewrites only require `premise_satisfied > 0`, so a regression that cuts reachability to 1 of 16 seeds would stay green. It suggests a loose minimum premise count taken from the measured baseline | **Declined, and recorded here.** A minimum count would pin the stochastic incidence rate, which is a calibration property; the rewrite deliberately scopes these tests to the conditional property. It would also be the uncalibrated threshold this package refuses to add. The rate did not move with this package: the K=32 main-vs-package fractions agree within ±0.2. If incidence itself needs to be guarded, that is a calibration test with owned evidence, which is outside this package. |

## Acceptance Gate

- **Invariance** (Python, `tests/runtime/air_combat/test_stable_entity_identity_draws.py`).
  The E-3 scenario gives exactly equal final overlays under all of:
  - the baseline;
  - 1, 2 or 3 unrelated units spawned first;
  - episodes 0–3 after `reset(20260529)` on one kernel.
- **Census-change invariance** (native, `src/tests/test_stable_entity_identity.cpp`). The
  same scenario is unchanged after extra components and entities are registered in the
  kernel world before spawning. The real 83→85 change is measured on the Air suite in P4.
- **Seed sensitivity at every site** (native, where the drawn value is inspectable: sites 1,
  2, 3, 7; Python plus native for sites 5–6). Seeds A and B must produce differing draw
  sequences at each site.
- **Helper unit tests.** Every input changes the seed, participant order matters, and a
  missing serial is rejected at the API boundary. The abort path is covered by a subprocess
  test.
- **Structure.** The guard flags zero main sites after P3 and every synthetic violation.
  The coverage test shows every `KeyEntity` entity carrying a serial after spawn, fire, step
  and reset.
- **Stream bit-identity.** Both stream steps produce the pre-change sequence for a fixed
  state.
- **Air re-decision.** Starting from 344 passed / 39 xfailed, every node whose status changes
  gets a row: `node | marker reason | old | new | decision | evidence`. A strict XPASS or a
  new failure is checked across K seeds. A draw-dependent node is rewritten to a
  seed-robust assertion or held with a named residual. Nothing is re-tuned or flipped
  silently.
- **Composition.** Evidence is regenerated in the order above, closure and parity validate,
  and the governance suite shows no failure beyond the base set.
- **Restore-equivalence** is not claimed here. It is handed to LHG P4-B (below).

## Out Of Scope

- Replacing `mt19937` or changing any distribution.
- Calibration.
- Re-keying the semantic reference (decision 7).
- Merging branches.
- Raw ids in observations and contacts, which remain the within-episode references.

## Obligations Handed To Other Lines

- **`work/army-mechanisms`, site 4.** When army integrates main, convert Ground direct fire
  to `draw_seed(DrawSite::ground_direct_fire, …)`, with the serial boundary check that
  army's `1449ffdc` already carries. Restore the site 4 half of the native test that
  army's `3fe74b03` carries. The guard makes the conversion mandatory. The census becomes
  `85 + army's own admissions`, and army regenerates its evidence on top of this package's.
- **LHG P4-B state transfer.** Transfer, do not re-derive:
  - `StableEntitySerial`, in the per-entity field set that `serialize_world` walks;
  - `StableIdentityState.next_serial` and `.episode_seed`, through a new
    `serialize_/restore_stable_identity_state` channel beside `serialize_rng` and
    `serialize_clock`. E8 found no generic singleton channel. The gate
  there: a checkpointed and restored episode draws identically to an uninterrupted run.
