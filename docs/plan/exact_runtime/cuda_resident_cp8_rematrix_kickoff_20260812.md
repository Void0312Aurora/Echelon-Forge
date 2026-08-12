# CP-8 Post-Optimization Matrix Re-Measurement -- Kickoff Freeze Draft

Language:
- English canonical: `cuda_resident_cp8_rematrix_kickoff_20260812.md`
- Chinese companion: [cuda_resident_cp8_rematrix_kickoff_20260812.zh.md](cuda_resident_cp8_rematrix_kickoff_20260812.zh.md)

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/plan/exact_runtime/cuda_resident_cp8_rematrix_kickoff_20260812.md`
Owner: `exact-runtime / CUDA-resident promotion workline`
Last verified: `2026-08-12`

- Program: [CP promotion program](cuda_resident_promotion_program_20260808.md),
  iteration CP-8
- Authorization: the repository owner instructed "start CP-8" on 2026-08-12.
  Starting means freezing scope and building the tooling prerequisite now;
  it does not reorder the program: the measurement itself stays gated on
  CP-5 and CP-7 landing, as the program plan requires.

## What CP-8 is

Re-measure the production matrix (worlds 1/4/16/64/256, both lanes, all
modes) on the optimized build, using the frozen CR2-6b campaign design, so
the post-optimization evidence is directly comparable to the CR2-6b package.
Exit gate per the program plan: optimized evidence comparable to CR2-6b.

## Two verified readings that shape the scope

1. **"Order swapped, two campaigns" is the lane order, and the tooling
   already supports it.** The frozen CR2-6b manifest design is
   `campaign_01_cpu_then_cuda` then `campaign_02_cuda_then_cpu` with
   `order_balanced: true` -- two full campaigns with the lane execution
   order swapped between rounds. An earlier reading of this iteration's
   preparation claimed the matrix probe's ascending-only `--worlds` parser
   was a CP-8 blocker; that was wrong and is withdrawn. No probe change is
   in scope.
2. **The real tooling prerequisite is the evidence chain, and it is the
   counter-chain failure class again.** The matrix evidence validator
   (`tools/diagnostics/cuda_resident_cr2_matrix_evidence.py` with
   `cuda_resident_cr2_matrix_evidence_schema.py`) pins one frozen
   generation: the literal `evidence_date == "2026-08-04"`, single
   `MANIFEST_SCHEMA` / `EVIDENCE_SCHEMA` / `ITERATION` identities, and
   CR2-6b-specific advisory/interpretation content. A CP-8 evidence package
   would be rejected by our own validator today, exactly as a v3 counter
   capture would have been before the counter chain became
   generation-aware.

## Scope

1. **Generation-aware matrix evidence chain** (can be built before CP-5 and
   CP-7 land, mirroring the counter-chain pattern):
   - the frozen 20260804 package keeps validating byte-for-byte under the
     v1 identities;
   - a v2 manifest/evidence generation registers once (identities, its own
     capture date and source commit, same campaign design shape);
   - full pin inventory found on reading the validator, all of which the v2
     shape must re-own rather than inherit: the literal evidence date and
     the `CR2-6b` iteration id; `selection_policy` validated against the
     CR2-6b advisory *result* (per-world routing rules baked into
     `selection_policy_contract()`); `counter_status` pinned to the CR2-6b
     era (`achieved_counter_gate_complete: False` with the historical
     permission blocker, both false today); `parity_confirmation` pinned to
     the 12-field v1 slice; `cr2_6`-prefixed gate keys;
   - freeze decisions to record at implementation: v2 keeps the cross-lane
     comparison shape (same metrics, per world count and mode) so the two
     packages read side by side, references the CR2-6b package as a
     hash-pinned prior-evidence input, drops the selection-policy result
     block (routing authority lives with CP-7's disposition), and carries a
     counter_status whose values reflect capture-time truth instead of the
     frozen 2026-08-04 era;
   - unknown generations fail closed.
2. **Measurement runbook** (gated; do not run before every precondition
   holds):
   - CP-5 fusion, the counter-chain commit, and the CP-7 disposition are
     landed; the worktree is clean at capture
     (`source_worktree_clean_at_capture: true` is a hard manifest
     requirement, so nothing uncommitted may be present);
   - the machine is quiet: no builds or compilers running. The 2026-08-12
     contamination incident (post-fusion campaigns overlapping a ninja
     fan-out, CPU-lane rows unusable above world 1) is the standing reason
     this is a hard requirement, not a preference;
   - both probes rebuilt from the landed SHA (`build-cuda` and `build-cpu`);
   - campaign 1 runs CPU lane then CUDA lane; campaign 2 runs CUDA lane
     then CPU lane; production protocol defaults, full world matrix;
   - manifest captured with byte hashes, host environment, and honest
     control flags (the CR2-6b design's `background_load_uncontrolled`
     style honesty flags stay);
   - evidence package built, validated by the generation-aware chain, and
     registered in the program document.
3. **Comparison target:** the CR2-6b package, with the explicit caveat that
   CR2-6b measured the pre-fusion binary on the same single host; the
   single-host boundary from the program constraints stands.

## Non-goals

- No promotion, support-flag, or tuning authority; all four authorization
  flags stay false in every artifact.
- No probe CLI or world-count-order changes.
- No performance claims until the evidence package validates end to end.
- The reviewer's contamination-reproduction reruns
  (`.memcheck/review_rerun/`) are diagnostics, not CP-8 evidence: they run
  against an uncommitted worktree and deliberately fail the clean-worktree
  requirement.

## Sequencing

1. Tooling prerequisite (scope item 1) implements next, as its own
   validated change, committable independently of CP-5 (the matrix chain
   does not reference the fusion identities).
2. Measurement (scope item 2) runs in the first window where all landed
   preconditions and the quiet-machine requirement hold together.
3. CP-9 consumes the validated package alongside the rest of the gate
   evidence.
