# DM-G1 Ground Damage Reachability — Diagnosis

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/systems/combat/reviews/ground_damage_reachability_20260921.md`
Owner: `systems/combat`
Last verified: `2026-09-22`

Status: cause located and repaired `2026-09-22`. The DM-G1 ground damage mechanism
is implemented and compiles; its structured effects route was never selected at
runtime, so no ground consequence was ever applied. The cause is located: the
factory and registration translation units resolve `GroundPlatformDamageState` to
component `94`, the effects unit resolved a duplicate `105`, and the effects reader
therefore found nothing where the spawn path wrote. The per-tick system reads the
same component the factory writes and was unaffected. The repair resolves the id once
per world in the composition path and passes it to the route, so the same probe now
reads `state=1`; it is recorded in
[Ground Damage Effects Route Repair](../../../domains/ground/work/active/ground_damage_effects_route_repair/README.md).
One expectation inside the mechanism was left open and named there: a Ground hit leaves
mobility at `1.0`. It was decided on `2026-09-28`: the expectation is withdrawn and pinned,
because the effects model estimates warhead mechanism load only for structured air
targets, so no warhead family reaches the Ground chassis mobility branches.

Every trace and reading below is the **pre-repair** measurement that located the cause,
kept as the record of how it was found. `state=0`, "the route never selects", and "the
effects half is unreachable" describe that state, not the current one. This note also
retracts one conclusion an earlier version of it drew from a stale binary.

## Symptom

A ground element receiving a resolved structural hit is destroyed on the first
hit with an all-zero capability vector:

```text
before  damage_state [1.0, 1.0, 1.0, 1.0]  position [100.0, 250.0, 0.0]  active True
debug_apply_local_proximity_hit(a, t, 0.2, 0.1, 0.0, 120.0, 80.0) -> True
after   damage_state [0.0, 0.0, 0.0, 0.0]  position [0.0, 0.0, 0.0]      active False
log: "SPLASH! Target 582 Destroyed."
```

Reproduced identically on two independent builds:

| Host | Toolchain | Build | Result |
| --- | --- | --- | --- |
| Windows | MSVC 14.44 / Ninja | forced full rebuild | `key_type=11 state=0` |
| HEI-LAN (Linux) | GCC 13.3 / Ninja | clean from-source build | `key_type=11 state=0` |

~~Same host, same world, same component id in both the spawn and the effects
translation units, so this is not a platform difference, a stale artifact, or a
cross-translation-unit id divergence.~~ **Falsified.** The "same component id"
reading was false, and the cross-translation-unit divergence it ruled out is the
located cause. What survives this paragraph is the platform reading only: the
symptom replicates on MSVC/Windows and GCC/Linux, so it is not platform-specific.

## Measurements

Instrumented diagnostics, both firing for the same entity in the same process:

```text
SPAWN DOMAIN STATE entity=582 unit_type=11 writes_ground=1 state_id=94 has_before=0
SPAWN DOMAIN STATE after_set entity=582 has_after=1
GROUND SELECT entity=582 key_type=11 state=0 hitbox=1 sys=1 platform=1
SPLASH! Target 582 Destroyed.
```

Reading of that trace:

- `unit_type=11` is `UnitType::Ground`, so the spawn branch for ground is taken
  and `def.type` is resolved correctly.
- `has_after=1` means the component was genuinely written and readable
  immediately after the write, inside the factory translation unit.
- `state_id=94` was read as showing that both translation units agree on the
  component. **That reading is wrong**: the effects unit resolves a different id.
  See "Why the earlier reading was wrong".
- `hitbox=1 sys=1 platform=1` means the shared damage surface
  (`HitboxConfig`, `SystemHealth`, `PlatformDamageState`) is present and intact
  at routing time.
- `state=0` means the effects model does not see `GroundPlatformDamageState` on
  that entity. It is not absent from the entity: the effects translation unit
  resolves a duplicate component id, which is the located cause below.

The ground selection predicate therefore returns false, the router falls
through to the `GroundPlaceholder` fallback, and that fallback's shared finalize
destructs the element. The all-zero vector and the destruction are the fallback
path, not a ground consequence.

## An earlier measurement, since corrected

This trace was captured from a binary that had never been rebuilt, and two of the
readings drawn from it below are wrong. It is kept because the corrections are
what make the current reading usable. Diagnostics were added at the write site and
inside the per-tick ground system, then the ground suite was run. Captured output:

```text
GROUND BRANCH WROTE entity=582 has=1 id=94
GROUND BRANCH WROTE entity=583 has=1 id=94
GROUND SELECT      entity=582 key_type=11 state=0 hitbox=1 sys=1 platform=1
SPLASH! Target 582 Destroyed.
```

Four facts, all from the same process:

1. **The spawn branch runs for ground.** `GROUND BRANCH WROTE ... has=1 id=94`
   proves both ground entities reached the ground branch, the component was set,
   and it was readable immediately after the set.
2. ~~**The state is already gone by the time effects routing reads it.**~~
   **Reframed.** The line reports `state=0`, which is a fact about what the effects
   reader resolves, not about the entity losing the component. Nothing was removed
   between the write and the read; the reader addresses a different component id.
3. ~~**The per-tick ground system never matches any entity.**~~ **Refuted.** The
   absence of that line proved nothing, because the diagnostic was not in the
   binary. A probe compiled into the registration unit shows the tick system
   matching the spawned entity four times:
   `PROBE-TICK site=registry matched ent=583 n=1..4`. The registration and factory
   units agree on component `94`, so the per-tick system reads what the spawn path
   wrote.
4. ~~The spawn and routing translation units agree on the component.~~ **Refuted.**
   The routing unit resolves a different id; only the factory and the registration
   unit agree.

So the component is written, readable at the write site, and absent for the
effects reader in the same world. It is not a predicate problem or a severity
problem. It is a component-identity problem, and it is a problem for the effects
route only: the per-tick system reads the same component the spawn path wrote.

## Ruled out

| Hypothesis | Evidence against it |
| --- | --- |
| Stale build artifact | Reproduced on a clean from-source Linux build on the Linux host. |
| Component not registered | The row is in the admitted registry macro, the admitted count matches, and the generated composition manifest contains the component. |
| Cross-translation-unit id divergence | **The hypothesis is confirmed; only the earlier evidence against it is retracted.** The "both report `id=94`" reading came from a binary that had not been rebuilt (see "Why the earlier reading was wrong"). Precisely: the factory and the registration unit agree on `94`, the effects unit resolves a duplicate `105`, and that divergence is the located cause. |
| Flecs component misuse | An isolated probe on the same toolchain shows the component sets, reads back, and survives five subsequent `PlatformDamageState` writes in a plain world. |
| Platform-specific behavior | Identical symptom on MSVC/Windows and GCC/Linux. |
| Wrong unit type | `get_unit_type()` and the diagnostics both report `UnitType::Ground` (11). |
| The spawn branch never runs | `GROUND BRANCH WROTE ... has=1` proves it runs and the set is readable at the write site. |
| Shared pipeline severity destroys on one hit | The relaxed-predicate experiment leaves the element alive with an untouched capability vector. |

## The located cause

Component-id resolution for `GroundPlatformDamageState` disagrees between the
factory and registration units on one side and the effects unit on the other.
Measured on a binary rebuilt from the probe sources, one test, one process, by the
implementing round and reproduced independently by the reviewing round:

```text
PROBE-SYSTEM  site=registry idT=94  by_name=94 world=0x265a4222c10 sizeof=80 align=8
PROBE-SYSTEM-PRE105 alive=0
PROBE-WRITE   site=factory  ent=582 idx=582 gen=0 idT=94  has=1 by_name=94
PROBE-READ    site=effects  ent=582 idx=582 gen=0 idT=105 has=0 by_name=94
PROBE-READ-NAMES ent94_alive=1 ent94_name=GroundPlatformDamageState ent105_alive=1 ent105_name=GroundPlatformDamageState
PROBE-TICK    site=registry matched ent=583 idx=583 gen=0 n=1..4
```

Reading:

- The entity is the same one at the write and at the read: `idx=582 gen=0`, same
  world `0x265a4222c10`. This is neither id reuse nor a different entity.
- The factory and the registration unit resolve `T` to component `94`. The effects
  unit resolves `T` to `105`. Only the effects reader is wrong.
- The per-tick system matches: `PROBE-TICK ... matched ent=583 n=1..4`. It reads
  the component the spawn path wrote, so the per-tick half of the mechanism is
  reachable. Only the effects half is unreachable.
- Both components carry the name `GroundPlatformDamageState`, so
  `lookup("GroundPlatformDamageState")` returns the first one (`94`) and hides the
  duplicate.
- `ent105_alive=0` while the composition registers components and `=1` afterwards,
  so `105` is a lazy duplicate created after registration. The probes show when it
  appeared and that it carries the same name; they do not observe which call
  created it, so attributing the creation to the effects unit is an inference from
  the single-call-site argument below rather than a measurement.
- Both ids report `sizeof=80 align=8`, so this is not a layout or ODR problem: the
  type is identical and only the registration is duplicated.
- The earlier version of this section cited `by_reg=0` as evidence about the
  registry id. That was a non-signal: `register_component<T>` calls
  `ecs.component<T>()`, and the `flecs.component.*` string is bookkeeping that
  never becomes an entity, so that lookup fails for every component.

Scope of the cause: this explains why the effects route falls through to the
placeholder and why one hit destroys the element. It does **not** explain a
per-tick failure, because there is none.

Boundary of that scope: "only the effects route" holds for the three routes
measured here, and the static include graph shows a single translation unit
resolving the effects selection, so a second creation site is unlikely.
Enumerating every translation unit that could lazily resolve this type would need
another instrumented build, so the universality of "only" is **unverified**.

## Why the earlier reading was wrong

An earlier version of this note reported that both units agree on `id=94`. That
reading came from a stale binary. On this Windows toolchain a header edit never
rebuilds the translation units that include it: every object in the local build
tree carries `#deps 0`, and Ninja treats that record as valid, so it answers
"no work to do" and the probe was never compiled in. The repository already
records this hazard for its compiler cache, but the cache is disabled in this
build tree and the failure persists, so the cause is the toolchain's non-UTF-8
`/showIncludes` stream rather than the cache. Any measurement taken here has to
force the affected translation units to recompile first.

The toolchain is the proximate cause, but it is not the whole reason a wrong
reading reached this note. The measurement was never checked against the artifact
it claimed to come from: no freshness check between the edited sources and the
built binary, and no negative control that would have shown the diagnostic was
absent. The repository's own agent contract already says that a build system
answering "no work to do" is a claim rather than evidence, and this note is what
happens when that rule is applied to other people's measurements and not one's
own.

## Next step, not yet taken

The fix is not chosen here. The candidates are ways of stopping the effects unit
from registering a second component:

- resolve the component once, in the composition path, and pass that id to the
  effects route instead of letting its translation unit resolve `T` again;
- or make the effects route look the component up by name, which currently
  returns the registered one;
- the `flecs.component.*` bookkeeping string is not involved and does not need to
  become an entity.

That choice belongs to a fix package; this note stops at the measurement.

## A rejected alternative

Temporarily relaxing the predicate to accept a ground-keyed target carrying the
shared surface, even with the state absent, was tried and reverted. The
measurement:

```text
GROUND SELECT entity=582 key_type=11 state=0 hitbox=1 sys=1 platform=1
EXPERIMENT-RESULT True [1.0, 1.0, 1.0, 1.0] alive True
```

It keeps the element alive but produces **no ground consequence at all** — the
capability vector is unchanged — because the route then has no `ground_damage`
pointer to write into. Tolerating the absence would convert a loud defect into a
silent no-op, which is worse than the current fail-visible behavior, so the
predicate is restored to its strict form and the state must genuinely exist at
routing time.

## Consequences while open

- Ground damage authority is neither delivered nor refused: a single hit
  destroys the element through the placeholder fallback.
- The DM-G1 mechanism (consequence ledger, per-tick system, ground-owned
  effects route) is implemented and its tests are written, but four of five
  ground runtime tests fail on this defect.
- Ground movement, sensing, fires, terrain, and full ground damage fidelity
  remain unowned and unclaimed.
- The cause is located: the effects unit resolves a duplicate component id, so the
  effects route never selects. The per-tick system is unaffected and does match.
  The fix is a bounded change but still needs its own package, and the four
  `xfail(strict=True)` nodes stay in place until then.
