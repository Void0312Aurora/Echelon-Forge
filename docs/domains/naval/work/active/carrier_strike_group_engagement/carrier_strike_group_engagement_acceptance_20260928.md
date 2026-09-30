# Carrier Strike Group Engagement Acceptance Gate

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/work/active/carrier_strike_group_engagement/carrier_strike_group_engagement_acceptance_20260928.md`
Owner: `domains/naval`
Last verified: `2026-09-30`

Status: `2026-09-30`; package decision `not accepted`. `CSG-S0` is accepted:
its runtime, throughput, replay, and agent-free visualization gates pass. Later
stages remain open, so the package as a whole is not accepted.

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
| `CSG-S1` | `G1`-`G2` | formations hold through turns; damage reduces mobility through the maintained path | planned |
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
