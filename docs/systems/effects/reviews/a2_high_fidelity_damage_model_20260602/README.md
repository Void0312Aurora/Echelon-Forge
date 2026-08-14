# A2 High-Fidelity Air-Combat Damage Model

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `review`
Lifecycle: `retained`
Canonical: `docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README.md`
Owner: `systems/effects`
Last verified: `2026-08-14`

Status: `2026-06-02 / archived_sealed_index / research_profile_closed / non-authoritative`.

The sealed retained project entry is the Chinese index:

- [README.zh.md](README.zh.md)
- [Task cluster dispatch packet](task_cluster_dispatch_20260601.zh.md)
- [Task cluster execution status](task_cluster_execution_status_20260601.zh.md)
- [Default effects modularization task list](default_effects_modularization/README.md)
- Research closeout archive (`git show 77610218:docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/archive/20260602_research_closeout/README.zh.md`)

The previous long English runtime narrative was archived at:

- `git show 77610218:docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/archive/20260601_doc_governance/README_legacy_runtime_narrative_20260601.md`

Current shorthand: A2 is archived as a sealed research/candidate record. Its
structured-aircraft damage/effects runtime surface is maintained, the
blast-fragmentation candidate package is accepted as non-authoritative, and
G4/G5 research packets are accepted. It does not grant stock runtime authority,
Pk authority, or deterministic fuze authority.

Future work should start only from an explicit follow-on request: authority
promotion uses `authority_promotion_backlog.zh.md`; new research expansion must
first create a separate follow-on record instead of reopening this sealed packet.

Tooling retirement (2026-08-14): the closed A2 maintenance/governance toolchain,
candidate-artifact generators, path resolver, and self-referential manifest guards
were removed. The last complete implementation is recoverable from `c0e4f31f`.
Historical retained material remains readable but is no longer an active CI or
release input. The one invariant that still constrains live runtime behavior is
now constructed inside its runtime regression test.

## Evidence-integrity note (2026-08-11)

Several `.zh.md` files in the sealed retained-artifacts tree contain
markdown links whose relative depth reflected the pre-migration location
under `docs/task/air_combat/archive/`. During the ownership-first
documentation migration (`77610218`) these links were mechanically updated
to the new owner root, which invalidated their SHA-256 pins in the
retained-artifact manifests.

After review, the six files that remain hash-mismatched pre-date the
migration (`ae5cdb03`) and are an inherited condition of the sealed packet.
The two files whose pins my commit broke were restored to their original
bytes:

- `validation_res001_release_signoff_gate_20260531.zh.md` — changed
  field was a backtick-quoted path string (not a live link); restored and
  gate-clean.
- `data_collection/f16c_block50_target_geometry/source_ledger.zh.md` —
  the broken link (`../../../../../../examples/…`) references a live repo
  file but sits outside the strict link-audit scope (full-tree only).
  Original bytes preserved; the relative path is correct at the
  pre-migration depth and the audit does not block on it.

Decision rationale: hash pins on immutable evidence artifacts take
precedence over cosmetic link-depth corrections in sealed, out-of-scope
archive files. Regenerating pins would have cascaded across 4 manifests and
their transitive chain with no gate benefit. This paragraph records the
pre-retirement analysis; the manifest-integrity tool and its CI contracts were
retired on 2026-08-14.

Update (2026-08-13): by owner instruction the second file was taken out of
the "original bytes preserved" state after all. The
`data_collection/f16c_block50_target_geometry/source_ledger.zh.md` link to
`examples/config/database/aircraft/units/f16c_block50.json` now carries the
correct depth for the owner-root location (seven `../` components instead
of the pre-migration six), and the affected pin chain was re-derived in
lockstep: the `target_geometry_source_ledger` entries (sha256,
content_hash, size_bytes) in
`retained_artifacts/geometry_warhead_row_provenance_20260531/manifest.json`
and `geometry_warhead_row_provenance_gate.json`, plus the manifest's pin of
the gate artifact itself. The chain terminates there (nothing pins the
manifest). The actual cascade proved narrower than the 4-manifest estimate
above: the other closeout gates reference this ledger by path only. The
six pre-migration hash mismatches remain untouched inherited conditions.

The historical manifest-pinned governance dependency is preserved byte-for-byte in the
[retained governance dependency snapshot](retained_dependencies/governance_20260531/README.md).
The retired path resolver is available from `c0e4f31f` for forensic replay; no
current reader translates this logical path or treats it as active policy.

Historical tooling counts (2026-08-13). The "six files" above counts distinct
hash-mismatched `.zh.md` files. The retired `manifest_integrity.py` counted manifest
*fields* and reports 109 mismatch rows across 29 manifests; the two figures
measure different things and both are correct. The 109 rows decompose into 9
content mismatches and 100 newline-representation rows. The 9 cover those six
`.zh.md` files (two of them pinned twice, through a paired
`sha256`/`content_hash` field) plus one pin of
`res001_release_signoff_gate.json`. The 100 record the committed LF digest,
which the tool's raw-byte comparison cannot reproduce from a CRLF working
tree; they are a Windows checkout artifact rather than evidence damage, and
are absent on Linux CI, where the same scan reports 9.

Both groups are enumerated row by row in
`tests/tools/manifest_pin_baseline.json` and enforced as shrink-only by
`tests/tools/test_manifest_pin_baseline.py`: a newly broken pin fails the
default test tier immediately, and repairing an inherited one requires
deleting its baseline entry in the same change. To find which manifests pin a
file, or to re-derive a whole pin chain after an authorised edit, use
`manifest_integrity.py --who-pins <path>` and `--cascade <path> [--write]`.
