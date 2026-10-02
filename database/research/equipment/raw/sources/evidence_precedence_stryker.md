# Stryker Variant Record — Evidence Precedence Record

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/raw/sources/evidence_precedence_stryker.md`
Owner: `database/equipment-data`
Last verified: `2026-09-18`
Content status: resolution order applied to the Stryker variant records. It is a working rule for these records, not an amendment to `docs/research/standards/public_data_source_admission.md`.

## Purpose

The same Stryker variant field is stated differently by different sources. Where two sources directly disagree, the record needs a stated precedence rather than a case-by-case judgement. This file records the order used, and the reasoning, so the same conflict resolves the same way on the next variant.

## Precedence

| Rank | Source class | In-tree examples | Weight |
| --- | --- | --- | --- |
| 1 | Official Army / government publication and Army-maintained reference | ODIN, ARMOR, Infantry Magazine, Fort Carson environmental assessment | Takes precedence for equipment designation, configuration and load figures |
| 2 | Manufacturer documentation | GDLS Stryker Combat Vehicles brochure | Takes precedence for the manufacturer's own product geometry, and for combat-versus-shipping configuration splits |
| 3 | Government assessment | GAO-03-671 | Authoritative as an assessment of programme capability; used to bound claims, not to supply specifications |
| 4 | Specialist compilation | AFV Database | Accepted for variant-level detail when ranks 1-3 are silent; retained as a recorded claim when they disagree |

## Rules that follow from the order

1. A lower-rank source is never deleted when a higher-rank source contradicts it. The original claim and the disagreement are both retained, so the record shows what each source actually says.
2. Rank does not transfer across fields. Manufacturer precedence for geometry does not make the manufacturer the authority for armour protection, and an Army precedence for a gun designation does not settle a shipping envelope.
3. A rank-1 source that cannot be reached is recorded as cited, not as verified. An unreachable primary is a reason to mark a field as a conflict, not a reason to accept the next source silently.
4. A source whose URL has stopped resolving is not a long-term citation. It is retained with that fact recorded and flagged for re-citation.
5. Configuration labels are part of the claim. `Combat length` and `Shipping length` are different fields; a value that is unlabelled in the source is recorded as unlabelled rather than assigned to whichever field makes the numbers agree.

## Applied conflicts

| Field | Higher-rank value | Lower-rank value | State |
| --- | --- | --- | --- |
| M1128 main gun | M68A1E4 (ODIN, ARMOR 2002, Infantry Magazine 2014, Fort Carson EA) | M68A1E8 (AFV Database) | Recorded with both; canonical reading follows rank 1 |
| M1132 combat length | 298.5 in (GDLS) with 287.9 in as the shipping length | 287.9 in presented unlabelled (AFV Database) | Split into combat and shipping rows; the Tier C value is labelled as shipping |
| M1134 combat envelope | 287 x 153 x 137 in (GDLS) | 287.0 x 149.8 x 119.3 in (AFV Database) | Both retained; flagged as needing configuration-level cross-check |
| M1132 crew | 11 total (Army programme page) | 8-10 (AFV Database) | Unresolved; neither treated as settled |
| Hull armour maximum | not stated as a plate value (GDLS, GAO) | 0.5 in maximum plate (AFV Database) | Retained as a Tier C claim, explicitly barred from conversion to a protection equivalence |

## Maintenance trigger

Update this file when a new source class enters the tree, when a rank-1 source becomes reachable or reachable again, or when a listed conflict closes.
