# CP-9 Promotion Decision: Scoped Promotion

Language:
- English canonical: `cuda_resident_cp9_promotion_decision_20260813.md`
- Chinese companion: [cuda_resident_cp9_promotion_decision_20260813.zh.md](cuda_resident_cp9_promotion_decision_20260813.zh.md)
- Machine-readable record: [cuda_resident_cp9_promotion_decision_20260813.json](cuda_resident_cp9_promotion_decision_20260813.json)

Document kind: `decision`
Lifecycle: `frozen`
Canonical: `docs/plan/exact_runtime/cuda_resident_cp9_promotion_decision_20260813.md`
Owner: `exact-runtime / CUDA-resident promotion workline`
Last verified: `2026-08-13`

- Decision id: `cp9.scoped_promotion.cuda_resident.20260813`
- Program: [CP promotion program](cuda_resident_promotion_program_20260808.md),
  iteration CP-9
- Decided by: the repository owner, 2026-08-13, choosing scoped promotion
  over unrestricted promotion and over a hold
- Basis: all six frozen gates verified green on tracked artifacts, plus an
  independent review (separate context, zero implementation edits) with zero
  blocking findings and a `scoped_promote` recommendation
- Base commit: `b01a068a` (CP-8 landed)

## Outcome

**The CUDA-resident backend is promoted to a selectable, explicitly opt-in
maintained backend — within the scope the evidence actually covers, and no
further.**

What is promoted:

- **Surface**: the resident fixture contract only — the fixed-air
  fifteen-field observation surface that every gate measured.
- **Selection**: explicit opt-in with an advisory minimum of 4 worlds. The
  CPU reference remains the maintained default at **every** world count;
  worlds 1-3 route to the CPU reference per the frozen CP-7a rule
  (`cp7.small_batch_selection_rule.v1`), which CP-8's re-measurement
  confirmed without revision.
- **Correctness claims, maintained grade**: released-state digests are
  bit-identical across lanes and campaigns, and the 12-field selected-slice
  parity passes fresh at package build. These are backed by frozen,
  hash-closed evidence and architecture gates.
- **Performance claims, experimental grade only**: every timing number is
  single-host (RTX 3090, balanced power, uncontrolled background). Per the
  program constraints they cannot become a maintained performance contract
  until the owner records a documented second host or an explicit
  single-host acceptance. Neither is recorded today.

What is **not** promoted: the production dictionary-observation stack (never
measured by any gate), learner update / training-loop integration, any
maintained performance contract, kernel or launch tuning authority, and any
public ABI change without a compatibility shell.

## What changes now, and what does not

This decision record changes **no runtime behavior**. The facade flags
(`compiled_experimental_backend`, `supports_resident_state`,
`supports_device_observation_view`, `supports_exact_gpu_backend`) remain
false, and the frozen artifacts' authorization flags are not retroactively
edited — they describe what each artifact authorizes and stay false.

The decision **authorizes** the follow-up implementation scope: a public
opt-in selection surface built with compatibility shells, its own
architecture gates, and registration of the promoted profile. Until that
scope lands and passes its gates, runtime behavior is identical to the
pre-decision state.

## Gate application

| Frozen gate | Evidence applied | Verdict |
| --- | --- | --- |
| G-A full-window advance through the public SPI | CP-3 removed the non-SPI entry points; CP-8 reports pin `cuda_resident.full_window_spi.v1` and the SPI-only operation sequence | green |
| G-B CPU/CUDA invocation surfaces equivalent | Both CP-8 lanes share invocation surface, operation sequence, production protocol, and master trace signature `4b03b578675065d4` | green |
| G-C learner-equivalent consumption measured | CP-6: full-tensor consumer with contract-owned normalization, CPU parity oracle, measured at production protocol; scope is the fixture contract | green |
| G-D achieved hardware counters complete | CP-4: 12/12 launches, 5/5 counter families with real values (occupancy 8.32-11.38%, zero local traffic); collected under elevation per the program record | green |
| G-E selected-slice parity out of quarantine | Fresh parity at CP-8 package build: pass, 12/12 released numeric fields matched | green |
| G-F small-batch default does not regress | CP-7a frozen routing rule plus CP-8 measurement: world 1 stays CPU-preferred on every metric, all counts >= 4 prefer the resident lane | green |

## Independent review record

Performed 2026-08-13 in a separate context that edited no implementation
file. Verified: 238 architecture gates passed (the 15 failures are the known
g++-missing environmental class, none in cuda_resident scope); the three
CUDA-on suites passed on hardware (16/643, 4/77, 6/154); the CP-8 package's
80 campaign ratio entries recomputed exactly from the raw reports; 40/40
warmed-p50 cells improved against CR2-6b within [-62.2%, -1.8%]; exactly one
direction flip ((4, host_export_no_device) mixed to cuda_resident); the four
authorization flags are false in every contract and artifact; the facade
maintained boundary is intact, so promotion was not implemented de facto.
Blocking findings: none. Recommendation: `scoped_promote`.

## Recorded gaps (carried obligations)

1. **G-D artifact lacks an elevation-record field.** The program constraint
   says counter artifacts must record elevation; the fact is recorded in the
   program plan prose, not in the artifact. The next achieved-counter
   capture (against the v4 parent) must write elevation fields into the
   artifact itself.
2. **Achieved counters predate the CP-5 fusion.** The v4 execution graph has
   no achieved capture; fused-kernel occupancy figures are theoretical. Any
   tuning conclusion requires a v4 elevated capture first — and tuning
   authority is not granted by this decision anyway.
3. **No world 2-3 measurement.** The advisory minimum of 4 is the smallest
   measured winning count, not a measured crossover point.
4. **The v4 synchronization-activity band [5,8] includes the pre-fold value
   8.** The exact pinned API counts (5 launches, 3 syncs) are the invariant
   that would catch a fold regression.

## Forbidden without new explicit authority

Changing the maintained default backend; maintained performance-contract
claims; production dictionary-observation stack claims; kernel or launch
tuning; public ABI, Python, CLI, or config changes without a compatibility
shell; registry or driver-policy modification.

## Program closure

With this record, CP-0 through CP-9 are complete and the CUDA Resident
Backend Promotion Program has delivered its verdict. Follow-up work
(the opt-in exposure scope, a v4 counter capture, any second-host evidence)
proceeds only under the authorities this record grants or the owner
explicitly adds.

## Amendment (2026-08-13): PR review findings resolved

The remote independent review bot raised three blocking findings against the
integration PR; each is resolved in the record and the tree, none by
weakening a gate:

1. **G-D elevation provenance.** The mandatory constraint ("counter
   artifacts must record elevation") was met only in program-plan prose for
   the frozen v1/v2 captures. The frozen artifacts stay byte-identical; the
   owner waiver is now explicit in `recorded_gaps` (basis: the hash-pinned
   unelevated predecessor failing with `ERR_NVGPUCTRPERM` is itself evidence
   that elevation enabled the capture), and the counter validator fail-closes
   any post-frozen (v3+) available capture whose artifact lacks an
   in-artifact elevation record.
2. **G-C evidence generation.** The four CP-6 campaign reports carry the v1
   schema id with the learner mode appended, so the frozen four-mode
   validator rejected them and nothing hash-pinned them. The tracked package
   `cuda_resident_cp6_learner_consumption_evidence_20260813.json` now
   declares that generation, hash-pins all four reports, and its validator
   (learner extension checked, remainder delegated verbatim to the untouched
   v1 validator) accepts them end to end; this record's evidence index binds
   G-C to that package. Learner-flagged probe runs self-declare
   `cuda_resident.cp6.production_matrix_probe.v2` from now on.
3. **CUDA CI flag coverage.** The compile lane claimed both device surfaces
   while enabling only the resident flag, leaving the `src/gpu` helper `.cu`
   sources uncompiled. The lane now enables both flags, and an architecture
   gate maps every surface the lane builds to the CMake flag it requires.

The second review round (same day) found four gaps in those mechanisms, all
closed: the surface-to-flag gate now parses the configure step's run
commands (comments cannot satisfy it, with mutation gates proving it); the
learner-report validator dispatches on the package's declared generation
(exactly one schema id per registered generation, so a relabeled report
cannot ride into a package declaring another); the CP-6 package pins
capture-time source provenance (`source_commit` plus canonical hashes of the
learner contract, consumer implementation, session, and probe at that
commit, following the CP-8 manifest pattern); and the counter collector now
emits the runtime elevation record for v3+ captures, with a
generator-to-validator round-trip gate, so a v4 capture can no longer
self-reject.
