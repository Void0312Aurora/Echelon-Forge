# Ground Systems Owner Admission — Current Status

Status: `2026-09-21` checkpoint after 12 independent review rounds. The declaration
cluster, the `DM-G1` measurement, and the owner admission with its guards are recorded,
and round 10 authorised the closure. The acceptance record is
[ground_systems_owner_admission_acceptance_20260921.md](ground_systems_owner_admission_acceptance_20260921.md).

Parent subproject:
[Ground Systems Owner Admission README.md](README.md).

## What Changed Since The Package Opened

| Cluster | Commits | State |
| --- | --- | --- |
| `GA-A` Declaration reconciliation | `2d0addf7`, `7ec76ff6`, `0fec39bb`, `d1be28a1`, `4821eb54`, `f3f85859` | `pass` |
| `GA-D` `DM-G1` measurement | `a9c8e6c0`, `3462ce1d`, `dcd25425`, `f3f85859` | `pass` |
| `GA-B` Owner admission and move | `59523a96` | `pass` |
| `GA-C` Guard and plan text | `59523a96` | `pass` |
| `GA-E` Acceptance and closure | `8f00d935`..`1de2a895` | `pass` (authorised round 10) |

## Maturity Matrix

Snapshot as of the review. The effects half became reachable `2026-09-22` through the
[Ground Damage Effects Route Repair](../ground_damage_effects_route_repair_20260922/README.md)
package, which resolved the component id once per world in the composition path; the row
below records what the review measured, not a current status.

| Area | Status | Evidence |
| --- | --- | --- |
| Ground damage mechanism, per-tick half | reachable | `GroundDamageStateUpdate` matches spawned ground entities; the review probe matched an entity four times in the registration unit |
| Ground damage mechanism, effects half | unreachable | the effects unit resolves a duplicate component id (`105`) while the factory and registration units resolve `94` |
| `DM-G1` cause | located | [DM-G1 diagnosis](../../../../systems/combat/reviews/ground_damage_reachability_20260921.md) |
| Ground declarations | reconciled | [specialization_baseline.md](../../standards/specialization_baseline.md), [Ground owner README](../../README.md) |
| Ground systems owner directory | admitted (via round 5's `GA-B` authorisation) | [src/systems/domains/ground/](../../../../../src/systems/domains/ground/README.md) owns the relocated damage system; the governance guard now asserts that owner instead of asserting absence |
| Ground capability claims | refused | no page claims ground damage works; the four `xfail(strict=True)` nodes remain |

## Review Log

12 independent rounds are recorded below. Rounds 1-3 predate the adoption
of [pr-review.md](../../../../../.github/codex/prompts/pr-review.md) as the brief
for this work, so their verdicts use an off-contract vocabulary and the table
records both the words used and the contract mapping. This log is the artifact
that makes a promotion traceable: a later round can see which round authorised
which status change.

Round 5 is recorded late: it reviewed `59523a96` and authorised the `GA-B` and `GA-C`
promotions, but the row was never written.

Its five follow-up suggestions are counted but **not enumerated**: no artifact records
them, and `b74e100a`'s message states only the count. A round asked for the same per-item
disposition the composition record carries ([runtime_composition_registry_sync.md](../../../../architecture/work/issues/runtime_composition_registry_sync.md)),
and that cannot be reconstructed honestly, so the gap is recorded rather than filled in.

| Round | Reviewed | Reported verdict | Blocking findings | Authorised |
| --- | --- | --- | --- | --- |
| 1 | `2d0addf7` | changes requested | six, including false status and test-backed framings | nothing; produced `7ec76ff6` |
| 2 | `7ec76ff6` | changes requested | four, including a refuted claim still asserted | nothing; produced `0fec39bb` |
| 3 | `dcd25425` | blocked | one: a source comment still carried the retracted reading | `GA-A` → `pass`; `P2` → `accepted`; produced `f3f85859` |
| 4 | `f3f85859` | no blocking issues; three follow-up suggestions | none | `GA-D` → `pass` |
| 5 | `59523a96` | no blocking issues; five follow-up suggestions | none | `GA-B` → `pass`; `GA-C` → `pass` |
| 6 | `8f00d935` | `Blocking issues found: 3` | three: the domain owner page still denied the admitted owner; the package README still said the admission had not started; four status cells were promoted with no authorising round | nothing; produced `bec208b1` |
| 7 | `bec208b1` | `Blocking issues found: 1` | one: the Chinese phase table kept the promotions the English table had just withdrawn | nothing; produced `4362fba3` |
| 8 | `4362fba3` | `Blocking issues found: 2` | two: the package README restated the owner page's authorization window, and the modularization plan contradicted itself about the admitted owner | nothing; produced `42c119e4` |
| 9 | `42c119e4` | no blocking issues; four follow-up suggestions | none | nothing; the pending promotions were not put to it. Produced `1de2a895` |
| 10 | `1de2a895` | no blocking issues; no follow-up suggestions | none | `GA-E` → `pass`; `P5` → `accepted`; `P0` → `accepted`; `P1` → `accepted` |
| 11 | `4ae027a8` | `Blocking issues found: 1` | one: the log named the wrong reviewed revision for the authorising round, and the real defect under that misreading was that three rounds had never been recorded at all | nothing; produced `f9e4a49a` |
| 12 | `f9e4a49a` | `Blocking issues found: 2` | two: the status line still counted seven rounds, and the new first action cited an Archive clause the linked page does not carry | nothing; produced this change |

Round 10's authorisation, quoted rather than paraphrased:

> Round 7 reviewed `1de2a895`, reported no blocking issues and no follow-up suggestions,
> verified all four of round 6's follow-ups closed (including an independent
> re-measurement of the link-audit selection membership, which confirms four of the five
> edited documents are inside the default selection and only `README.zh.md` is outside
> it), confirmed the validation table is one contiguous headed table, and authorises
> `GA-E` → `pass`, `P5` → `accepted`, `P0` → `accepted`, `P1` → `accepted`.

It withheld none.

The quote carries the round numbers that were in force when it was given, before rounds 6
to 8 were recorded here. Read its "Round 7" as this table's round 10 and its "round 6's
follow-ups" as round 9's, which reviewed `42c119e4` and returned them. The sentence is left
as spoken rather than silently renumbered, because the log's value is that it quotes the
authorising round instead of paraphrasing it.

A bookkeeping note from that round, recorded because it affects how the row above should be
read: the package states no phase-to-cluster mapping anywhere, so the annotations pairing
`P5` with `GA-E` and `P0`/`P1` with the closing cluster are the reviewer's derivation, not a
declared mapping. The authorisation itself is unqualified.

Rounds 6 to 8 are recorded late, like round 5. Each returned blocking findings and produced
the commit that closed them, and the table showed the resulting fixes with no round behind
them for as long as they went unrecorded. Recording a round late is the smaller error; not
recording it at all is how a promotion loses its authorising row, which is the gap round 4
objected to.

Round 4 declined to endorse round 3's authorisation because it existed only in
review correspondence. This log is the response to that objection, and it is the
reason later rounds no longer have to take a promotion on trust.

## Residual Register

Immediate:

- the four `xfail(strict=True)` nodes stay in place until a fix package closes
  the effects route.

Follow-on:

- the composition registry-sync debt this package reported is **transferred, not
  absorbed**. [runtime_composition_registry_sync.md](../../../../architecture/work/issues/runtime_composition_registry_sync.md)
  owns it and has repaired it there. None of its surfaces lie inside this package's
  write set, and widening that write set would have made a domain package the owner of
  a cross-domain composition concern. It is listed here as follow-on rather than
  immediate because nothing remains to do on it inside this package;
- a `DM-G1` fix package. The candidates are resolving the component once in the
  composition path and passing that id down, or having the effects route look the
  component up by name;
- a `ground_p2_stage_node` package, which needs its own declarations;
- an archive-ledger registration for the retired `docs/task/ground/` records.

Deferred:

- ground movement, terrain, sensing, fires, logistics, and observation export;
- any facade-visibility promotion for Ground.

## Next Recommended Action Order

`GA-A` through `GA-E` are complete and the package is accepted. What remains is the packages
this one deliberately did not take.

1. **Done.** Retire this package from `work/active/`. Its own
   [Archive](README.md#archive) clause required that it not stay there once accepted with
   its lasting facts promoted, which they were in `GA-A`. It now lives at
   `docs/domains/ground/reviews/ground_systems_owner_admission_20260921/`.
2. A `DM-G1` fix package: either resolve the component once in the composition path and
   pass that id down, or have the effects route look the component up by name.
3. A `ground_p2_stage_node` package: the only Ground-claimed stage still has no
   registered node.
4. An archive-ledger registration for the retired `docs/task/ground/` records, which
   belongs to the documentation governance owner.

## Overclaim Refusals

- Ground damage is not a capability, and nothing here makes it one. The per-tick
  half being reachable does not make the mechanism work.
- "Only the effects route is affected" holds for the routes measured and the
  static include graph; its universality is unverified.
- The retired `docs/task/ground/` plan is provenance, not current authority.
