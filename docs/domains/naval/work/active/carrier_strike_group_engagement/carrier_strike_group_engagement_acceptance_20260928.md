# Carrier Strike Group Engagement Acceptance Gate

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/work/active/carrier_strike_group_engagement/carrier_strike_group_engagement_acceptance_20260928.md`
Owner: `domains/naval`
Last verified: `2026-10-08`

Status: `2026-10-08`; package decision `not accepted`. `CSG-S0` is accepted:
its runtime, throughput, replay, and agent-free visualization gates pass. Later
stages remain open, so the package as a whole is not accepted. S1-A/B have a
validated runtime checkpoint pending integration review; S1-C/D/X remain open.

Parent project: [Carrier Strike Group Engagement](README.md)

## Acceptance Decision

Current decision: `not accepted` for the package. `P0 Boundary`, `S0-A`..`S0-D`,
and the `S0-X` stage gate are accepted. `CSG-S1` and `CSG-U1` are no longer
blocked by S0.

## Stage Gates

A stage is accepted only when its acceptance cluster records all of:

1. both the named and the symmetric-mirror scenario run on the maintained
   runtime for their full stated duration;
2. focused tests pass for every mechanism the stage added;
3. the stage's claim ceiling is met by maintained evidence, not a
   diagnostics-only path;
4. a throughput record exists (entities, fixed step, simulated duration,
   wall-clock, host);
5. a replay artifact and visualization profile exist;
6. every new named-platform parameter has a provenance record;
7. lower-stage scenarios still pass; a regression below blocks the stage
   (Claim Rule 5).

| Stage | Claim ceiling | Stage-specific requirement | Status |
| --- | --- | --- | --- |
| `CSG-S0` | `G0` | full order of battle spawns with identity, side, and position; geodetic frame in use | accepted `2026-09-30`; replay/viz verified |
| `CSG-S1` | `G1`-`G2` | formations hold through turns; damage reduces mobility through the maintained path | partial: A/B validated; C/D/X dependency-blocked |
| `CSG-S2` | `G3` | launch and recovery rates are bounded by deck resources; CAP is sustained | planned |
| `CSG-S3` | `G4` | group picture forms from sensors and data links with no truth reads | planned |
| `CSG-S4` | `G5` | anti-ship strike, layered defense, soft-kill, and leaker damage close one causal chain | planned |
| `CSG-S5` | `G6` | two-sided strikes with escort, jamming, and depletion | planned |
| `CSG-U1` | `G1`-`G2` | submarine noise tracks speed and depth | planned |
| `CSG-U2` | `G4` | undersea detection with no truth reads | planned |
| `CSG-U3` | `G5` | torpedo engagement including countermeasures and flooding damage | planned |
| `CSG-S6` | `G6` | adjudicated termination in named and mirror variants; RL boundaries exercised | planned |

## CSG-S0 Runtime Checkpoint (`2026-09-30`)

Source baseline: `087c1928` (`work/naval-mechanisms`), with the S0 scenario
test extended from 20 steps to the scenario's declared 240 steps. Local
Windows MSVC Release, `build-independent-win`, Python 3.12. The extension is
selected explicitly with `CMO_BUILD_DIR`: automatic discovery selects the older
`build-local-win`, which lacks the S0-B geodesy bindings.

| Variant | Explicit hulls | Stowed helicopters | Live runtime entities | Aircraft inventory | Step / duration | Step wall-clock | Entity steps / s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ford vs Fujian, named | 14 (7 per side) | 10 (4 Blue, 6 Red) | 24 | 74 Blue / 55 Red | 0.5 s / 240 steps / 120 s | 0.109748 s | 52,483.63 |
| Ford vs Ford, mirror | 14 (7 per side) | 8 (4 per side) | 22 | 74 per side | 0.5 s / 240 steps / 120 s | 0.108835 s | 48,513.63 |

Timing is a single local measurement with seed `20260930`. It covers native
`SimulationKernel.step()` calls only; database loading, scenario compilation,
state export, and visualization are excluded. Entity counts come from
`get_all_units()`, including the automatically spawned stowed helicopters.
The remaining inventory aircraft are not live entities, so these rates do not
predict full airborne-wing performance at S2 or later.

Both variants use the `(21 N, 125 E)` anchor and great-circle station placement.
Every hull retains its initial position throughout the declared duration. The
first tick pins each stowed helicopter to its host's position at the waterline;
after that tick all runtime entity positions remain unchanged. This is the
existing stowed representation, not a flight-deck contact or deck-cycle result.

The maintained test `tests/scenario/test_csg_group_composition.py` now checks
every tick for unchanged entity membership, finite positions, hull station
keeping, stowed-helicopter stability, and correct sides and counts. Parameter
provenance and spawn checks remain in `tests/content/test_csg_unit_content.py`.

Focused validation is run with:

```powershell
$env:CMO_BUILD_DIR = (Resolve-Path build-independent-win).Path
python -m pytest -q tests/scenario/test_csg_group_composition.py tests/content/test_csg_unit_content.py tests/runtime/naval tests/architecture/composition tests/architecture/command_tasking
```

| Check | Outcome |
| --- | --- |
| `ef_py` / `ef_test` / composition evidence build | current; no work required |
| `ef_test.exe` | 202 / 202 cases; 152,866 assertions |
| `ef_composition_evidence_test.exe` | 7 / 7 cases; 90 assertions |
| focused Python suites above | 187 passed, 1 skipped, 16 subtests passed |
| CSG JSON contracts via `ci_contract_smoke` | named and mirror composition plus replay contracts passed |

S0-X closure evidence:

- `csg_s0_ford_vs_fujian_named_v1.replay.json` and
  `csg_s0_ford_mirror_v1.replay.json` declare the scenario hash, seed, fixed
  step, duration, roster, and all 241 native state frames. The
  `naval_csg_replay` contracts regenerate both scenarios and compare every
  frame's runtime IDs and positions.
- `naval_csg_s0_ford_vs_fujian_replay.json` and
  `naval_csg_s0_ford_mirror_replay.json` load through `SessionManager` and
  stream the same versioned `map_setup` / `state_update` contract without a
  model or agent. The companion `*_spectator.json` profiles step the native
  `ScenarioLoader + SimulationKernel` path directly. All four profiles were
  exercised; the browser page rendered both groups with no console errors.
- `S0-X` is accepted under Stage Gate 5. S1/U1 implementation is unblocked by
  this checkpoint; later stage gates still require their own evidence.

## CSG-S1 A/B Runtime Checkpoint (`2026-10-08`)

Decision: implementation validation for S1-A/B, pending integration review.
This checkpoint does not accept S1-X. Baseline `origin/main` `cedfa01c3`;
delivery stack `codex/naval-csg-s1-motion` then `codex/naval-csg-s1-transit`.
The integration source is retained on `codex/naval-csg-s1-integration`. Both variants use native
ship motion and maintained scenario command publication, without an agent.

### Exercised behavior and claim boundary

- Quadratic surge response, full-astern stopping without reverse thrust after
  rest, bounded Nomoto yaw, and declared steady-turn speed loss. DDG-51 Flight I
  acceleration and stopping tests use the USNI trial figures; turning geometry
  and other hull parameters retain their explicitly labelled proxy provenance.
  This is a bounded maneuvering model, not full hydrodynamics or fleet calibration.
- Live `PlatformDamageState` changes attainable speed. A native flooding test
  exercises the registered naval damage system, checks liveness every tick,
  and observes reduced mobility and speed. `DM-N1` remains synthetic; these tests
  do not validate real-world compartment or casualty predictions.
- Scenario-owned guide routes publish through the maintained command adapter;
  surface escorts and replenishment hulls preserve true-bearing station offsets.
  Submarines remain static and embarked aircraft remain stowed. No combat authority,
  Joint group command hierarchy, or learned-policy capability is added.
- Each variant runs 7200 steps at 0.5 s (3600 s), with three 2250 m route legs
  and two guide turns. Both routes complete. Every surface station error stays
  below 1500 m during the run, below 250 m continuously for the final 300 s, and
  final surface speeds are below 0.1 m/s. These are scenario test tolerances.
- Low-speed station acquisition retains steering speed while changing heading,
  allows slow aligned approaches, and follows guide velocity inside a 50 m
  arrival window. The window and 5-degree alignment tolerance are controller settings.

Platform provenance is in the ship records and the
[source ledger](../../../reviews/csg_order_of_battle_20260928/csg_source_ledger_20260928.md).
Retired `max_turn_rate_deg_s` / `low_speed_turn_factor` content fields are replaced
by `steady_turning_diameter_m`, `nomoto_time_constant`, and
`steady_turn_speed_ratio`. Repository records and state-transfer reflection are
updated together; old external records require migration and remain subject to
strict unknown-field rejection. The ECS migration evidence digest is repinned
for the changed serialized field set and the explicit N-1 ship normalizers.

The runtime's N-1 ECS admission translates the previous 22-field hull record
before strict current decoding. Its reference speed is `max(1, economic speed)`
when economic speed is positive, otherwise `max(1, maximum speed)`. The old
positive rate limit maps to diameter `2 * reference speed / rate_rad_s`; a zero
rate maps to zero steering authority. Nomoto `T'=1` and turn-speed ratio `1`
are deterministic compatibility defaults, not new trial calibration. The
retired low-speed turn-rate floor has no equivalent in the new maneuvering law.
Only legacy hulls get missing `AngularVelocity` seeded to zero; existing angular
state and current hull fields are retained. Mixed old/new fields, malformed
legacy values and migration requests outside N-1 fail closed. Unknown fields
remain subject to strict decoding, and a direct N reader still rejects old hull
fields. The owner-registry test constructs the exact pre-#117 reflected shape,
imports it through the durable twelve-owner transaction and executes a native
step with the restored ship; it also checks economic-speed fallback, zero turn
authority, existing yaw preservation and rejection without live-world mutation.

### Validation and throughput

Windows MSVC 14.44 Release uses a clean build in
`build-s1-win-verified-20261008`, explicitly selected with `CMO_BUILD_DIR`.
The previous incremental build was excluded after its localized header-dependency
scanner failed to rebuild changed headers. HEI uses an isolated source snapshot
at `/home/void0312/work/naval-s1-20261008`, GCC Release and Python 3.13.5;
`ef_test`, `ef_py`, and the runtime host candidate target build with `-j32`.
The existing HEI checkout is preserved.

| Check | Outcome |
| --- | --- |
| Windows full `ef_test` | 284 passed; 169,269 assertions |
| HEI full `ef_test` | 284 passed; 169,269 assertions |
| Windows / HEI runtime host/state-transfer candidate after review repair | each: 72 passed; 1,993 assertions |
| Windows / HEI N-1 ship migration and refusal cases | each: 2 cases, 145 assertions passed; reproduced failure before the fix |
| Windows naval runtime + S1/S0 scenarios + CSG content | 101 passed; 16 subtests |
| Windows S0/S1 visualization wire profiles + state-transfer evidence | 14 passed |
| HEI final focused Python set | 135 passed; 16 subtests |
| Windows / HEI focused post-review S1 transit + migration evidence | each: 15 passed |
| Full-duration replay regeneration | named and mirror: 7201 frames each; `naval_csg_replay` contract passed |
| Static gates | repository Ruff, changed C++ clang-format and internal code governance passed; 263 maintained documents / 2015 local links, zero issues |

The S1 spectator profiles under `examples/viz/profiles/naval_csg_s1_*_spectator.json`
stream all 7201 frames through `VizSession`'s maintained `map_setup` /
`state_update` contract. This is wire-contract verification; no browser-render
claim is made for this checkpoint. Full replay files are generated into the
ignored build directory rather than committing the large state streams. Reproduce with:

```powershell
$env:CMO_BUILD_DIR = 'D:/workshop/Research/Echelon-Forge/build-s1-win-verified-20261008'
python tools/runners/run_csg_replay.py --scenario scenarios/naval/csg/csg_s1_ford_vs_fujian_named_v1.json --output "$env:CMO_BUILD_DIR/csg_s1_named.replay.json" --seed 20261008 --verify
python tools/runners/run_csg_replay.py --scenario scenarios/naval/csg/csg_s1_ford_mirror_v1.json --output "$env:CMO_BUILD_DIR/csg_s1_mirror.replay.json" --seed 20261008 --verify
```

The build path above must resolve to the directory containing the current
extension; when running from an isolated worktree, use its absolute path.

| Variant | Live entities | Step / simulated duration | Native step wall-clock | Command publication wall-clock | Native entity steps / s |
| --- | --- | --- | --- | --- | --- |
| Ford vs Fujian | 24 | 0.5 s / 3600 s | 2.934895 s | 1.219352 s | 58,877.75 |
| Ford mirror | 22 | 0.5 s / 3600 s | 3.208262 s | 1.563625 s | 49,372.53 |

Single seed-`20261008` samples on `Void0312`, Windows 11 10.0.26200,
MSVC Release / Python 3.12. Native steps and scenario command publication are
timed separately; loading, state export, JSON serialization, and visualization
are excluded. Concurrent validation may affect these samples. The live roster
includes stowed helicopters and excludes the inventory air wing, so these rates
do not establish S2/full-air-wing capacity or a mixed-step fidelity decision.

### Remaining S1 gates

| Cluster | Blocker / remaining work |
| --- | --- |
| `S1-C` | No accepted shared ship fuel/endurance owner contract exists. Current `NavalStores` transfer does not integrate burn, endurance or group replenishment scheduling. |
| `S1-D` | Environment Runtime `P3-A` has not been delivered. The legacy global maritime-state interface does not provide the position/layer bathymetry query required by this cluster. Joint group hierarchy integration also remains open. |
| `S1-X` | Requires A-D and all stage gates. A/B validation, throughput and replay do not close the missing C/D mechanisms. |

The task clusters' Dispatch Rules and the queue's No-Dispatch Conditions require
consuming accepted shared-owner deliverables and prohibit building local stand-ins.
Next: shared logistics contract and implementation, Environment Runtime `P3-A`,
naval C/D integration, then the complete S1-X acceptance run.

## Package Acceptance

The package is accepted when every stage above is accepted, the conditions in the
[README acceptance gate](README.md#acceptance-gate) hold, and the naval owner
README and indexes point at the accepted record.

## Fail-Closed Rules

- A stage that needs an unsourced, calibrated-looking coefficient to pass is
  `partial`, not accepted.
- A stage whose sensing path reads true state while claiming `G4` or higher fails.
- A stage that passes only on the mirror variant is `partial`.
- Any claim of learned-policy quality or real-world prediction fails the package.
