# Stable Entity Identity For Stochastic Draws

Language:
- English canonical: `stable_entity_identity_for_stochastic_draws.md`
- Chinese companion: not maintained (English-only work surface).

Document kind: `plan`
Lifecycle: `superseded`
Canonical: `docs/architecture/work/issues/stable_entity_identity_for_stochastic_draws.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-10-01`
Content status: superseded defect record. Replaced by the main-line package
[Stable Entity Identity For Stochastic Draws](../active/stable_entity_identity/README.md),
which supersedes the design below and owns its acceptance. The measurement and inventory
are kept as the original finding, taken on the pre-fix base build; they no longer describe
the tree. Current state on the army stack is recorded under
[Resolution On The Army Stack](#resolution-on-the-army-stack-2026-10-01).

## Resolution On The Army Stack (`2026-10-01`)

Main implements the package (`StableEntitySerial`, `StableIdentityState`, reset episode
seeds, the single `stochastic_draw::draw_seed` path and its structural guard) and reserves
`DrawSite` value 4 for Ground direct fire. Its two obligations on this line are met by
`6935b2b92` on `codex/army-direct-fire`:

- `fire_ground_weapon` draws through `draw_seed(DrawSite::ground_direct_fire, …)` and
  rejects a target without a `StableEntitySerial` at the API boundary;
- the native suite carries `site 4 (ground direct fire): reset seed drives the hit roll`,
  which pins equal draws for one reset seed and differing draws for two.

The census is main's 85 plus army's own admissions. The per-layer counts and the
regenerated evidence are recorded in
[runtime_composition_registry_sync.md](runtime_composition_registry_sync.md). The two Air
nodes listed under [Known Exposures](#known-exposures-on-other-lines) were re-decided by the
main package (`SI-P4-B`); on the army stack the Air and naval suites show the same failure
set as main `e1e077cb`, measured on HEI.

Not claimed here: the frozen host/batch semantic reference still pins raw Flecs entity ids
(`582` on main, `584` on the army stack). Re-keying it is out of scope for the main package
(its decision 7) and remains the residual named below.

## Defect

Every stochastic draw in the kernel that is keyed per engagement or per detection mixes
**raw Flecs entity ids** into its seed. A Flecs id is an allocation handle, not an
identity. Its low 32 bits depend on how many ids the world has handed out before the
entity: component *and* system registrations, plus every entity created earlier. Its high
32 bits carry a generation that advances whenever a recycled index is reused. Seeds built
from it change when:

- the composition changes. `581` at census 83 components / 34 systems, `582` at 85 / 34,
  and `583` at 85 / 35 on this branch. The shift follows system registrations as well as
  components, so "the census" here means the whole composition, not the component count;
- unrelated entities are spawned first;
- the same kernel is `reset()` with the same seed. `reset()` deletes the `SimObject`
  entities, and the next episode reuses their indices with new generations **and in a
  different order**: the recycle list is LIFO. Measured: the first post-reset spawn got
  `0x1_0000_0248` and the second `0x1_0000_0247`.

So a draw can differ between two runs that the simulation should treat as identical.

## Measurement (`2026-09-28`, Windows MSVC, base `cfb9924e` build)

The scenario is `test_phase2_fire_suppression_integrity_reduces_fire_cascade_growth`:
E-3 target, three profiled blast-fragmentation hits, then 80 steps.

| Variation, nothing else changed | Entity ids (attacker, target) | Outcome |
| --- | --- | --- |
| baseline | `581, 586` | survives 80 steps |
| 1 unrelated unit spawned first | `582, 587` | removed at step 1 |
| 2 unrelated units spawned first | `583, 588` | removed at step 12 |
| 3 unrelated units spawned first | `584, 589` | removed at step 1 |
| same kernel, `reset(20260529)`, episode 0 | `0x245, 0x24a` | survives |
| same kernel, same reset, episodes 1–3 | `0x1_0000_024a…` (new generations) | removed at step 1 |

Two consequences:

- **The reset result matters most.** One kernel reset with one seed gives a different
  first episode from every later episode. RL training reuses kernels across episodes,
  so its episodes are not reproducible from `(seed, actions)` even though the harness
  treats them as if they were.
- **Every census change moves draws.** On `work/army-mechanisms` (census 85), two Air
  realism nodes flipped for this reason alone: `test_phase2_fire_suppression_…` now fails
  and `test_shot_effect_record_links_…` XPASSes a strict marker. This is not a
  damage-model regression.

## Inventory

| # | Site | Draw | Id inputs |
| --- | --- | --- | --- |
| 1 | `src/core/engine/simulation_kernel_damage_debug_api.cpp` `make_debug_synthetic_missile_seed` | synthetic missile `rng_state` (3 debug hit APIs) | attacker, target |
| 2 | `src/core/engine/simulation_kernel_weapon_release_service.cpp` missile release | fired missile `rng_state` | attacker, target |
| 3 | same file, naval gun/CIWS | hit roll | attacker, target |
| 4 | same file, Ground direct fire | hit roll | attacker, target |
| 5 | `src/models/systems/default_sensor_model.cpp` | detection roll | owner, target |
| 6 | `src/models/systems/default_acoustic_model.cpp` | detection roll and bearing noise | owner, target |
| 7 | `src/core/engine/simulation_kernel_command_api.cpp` (four call sites: lines 170, 187, 240, 356) | command-link drop rolls | entity |

Understatements corrected by review:

- Site 5 also drives the range, bearing and Doppler noise draws from the same `seed_det`,
  not only the detection roll.
- Sites 1–2 seed a munition's `rng_state`, which downstream consumers inherit: component
  failure sampling, fuze reliability (`damage_system_common.h` fuze draws) and the legacy
  splash roll. The defect therefore reaches every draw a munition makes.

**Two defects, not one.** Sites 1–2 also mix in draws from the kernel `std::mt19937`,
which `reset(seed)` reseeds, so only their id terms are defective. Sites 3–7 mix only
`current_time` and ids: they never consult the reset seed at all. Replacing ids with serials
would make those sites reproducible but still **seed-blind**. Two `WorldBatch` worlds reset
with different seeds would draw identical sensor, CIWS, ground-fire and command-drop
results for identical scenarios, which defeats per-world seed diversity.

The same allocator dependence also affects two non-seed surfaces. They fall under this
package because the serial is what can replace their ids:

| Surface | Dependence |
| --- | --- |
| `tests/architecture/composition/fixtures/default_runtime_host_batch_semantic_reference.v1.json` and the parity host rows | frozen `entity_id` values (`581` on main, `583` on `work/army-mechanisms`), so every census change forces a recapture |
| future Flecs-vs-CUDA parity (the held closure residual `cuda_backend_parity`) | must join on world index and stable serial, never on raw ids; the CPU reference tests stopped pinning the CUDA identity in `ae9de540` |

Target: key those surfaces by `(world_index, StableEntitySerial)` so a census change
leaves the frozen reference untouched.

## Target Design

1. **A per-world stable serial.** A new `components/basic` component (working name
   `StableEntitySerial { std::uint64_t value; }`) is assigned to every simulation entity
   from a per-world counter at creation. `reset()` restarts the counter, so the serial
   depends only on creation order within an episode: never on the Flecs allocator, the
   registry, or the generation.
2. **One assignment point per creation path.** The creation paths are:
   - kernel `spawn_unit`, together with the factory's child entities (embarked helo,
     `<unit>_Stn_<n>` munitions);
   - weapon release;
   - the three debug synthetic-hit APIs;
   - EW chaff and flare.

   The coverage guard must not key on `SimObject`. Factory children (the embarked helo,
   spawned through `spawn()` plus `child_of`, and the `_Stn_` munitions) are never tagged
   `SimObject`; only the root gets the tag. The helo takes part in sensor seeds. The guard
   asserts instead that every entity carrying `KeyEntity` (or `Transform`) has a serial
   after each spawn.
3. **One seed helper, and the only path.** The helper takes a **per-world episode seed**
   captured at `reset(seed)`, the participants' serials, the simulation time and a
   draw-site tag. Serials alone would leave sites 3–7 seed-blind. The helper is the only
   way to build a seed. A `.id()` pattern guard is not enough: sites 1–4 and 7 receive ids
   as plain `uint64` parameters (`attacker_id`, `target_id`, `entity_id`), not `.id()`
   calls. Enforce it structurally instead, by forbidding the raw splitmix/xor seed
   constructions outside the helper under `src/models/**` and `src/core/engine/**`.
4. **Admission.** The new component moves the census from 85 to 86. It follows the
   causal repair order in
   [runtime_composition_registry_sync.md](runtime_composition_registry_sync.md):
   census pin, then projection, Cordis bundle and descriptor, producer, provenance,
   parity capture, and closure.
5. **State transfer.** The Long-Horizon Governance P4-B state transfer copies components
   by owner. Three things must be transferred, not re-derived: the serial (with the entity
   owner), the **per-world serial counter**, and the captured episode seed. Without the
   counter, creations after a restore would reuse serials. Without the seed, draws after a
   restore would diverge from the uninterrupted run.

## Acceptance Gate

- The measurement table above becomes invariant. The same scenario gives the same outcome
  whether or not unrelated units are spawned first, and whether it is the first or the
  n-th episode after `reset(seed)` on one kernel. Pinned as native and Python tests.
- A census change leaves the Air realism outcomes unchanged. Pinned by running that suite
  before and after a dummy-component admission in a test.
- **Seed sensitivity:** the same scenario reset with a *different* seed must draw
  differently at every site, including sites 3–7. Invariance alone would accept a
  seed-blind fix.
- The seed helper is the only seed-construction path, enforced by the structural guard.
- Transfer: an episode checkpointed and restored mid-run draws identically to an
  uninterrupted run.
- Every Air realism strict marker is re-decided against the new stable draws and recorded
  one by one. None is flipped silently; this package owns that re-baseline.
- Composition evidence is regenerated in the documented order, and closure/parity
  validate.

## Out Of Scope

- Replacing `std::mt19937` or changing any draw distribution.
- Calibration changes. Air realism markers are re-decided against the new stable draws,
  not re-tuned.
- Merging branches. `work/army-mechanisms`, `work/naval-mechanisms`, and LHG each carry
  composition evidence; this package lands after whichever of them lands first and
  regenerates on top of it.

## Known Exposures On Other Lines

- `work/army-mechanisms` (census 85):
  `test_phase2_fire_suppression_integrity_reduces_fire_cascade_growth` fails, and
  `test_shot_effect_record_links_fuze_geometry_warhead_part_entry_and_consequence_hook`
  XPASSes its strict marker. Both are recorded there as known exposures of this defect and
  deliberately left unmarked, so that the defect stays visible until this package lands.
