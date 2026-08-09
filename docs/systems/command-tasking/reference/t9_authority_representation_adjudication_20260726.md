# T9 Authority Representation Adjudication (2026-07-26)

Language:
- English canonical: `t9_authority_representation_adjudication_20260726.md`
- Chinese companion: [t9_authority_representation_adjudication_20260726.zh.md](t9_authority_representation_adjudication_20260726.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/systems/command-tasking/reference/t9_authority_representation_adjudication_20260726.md`
Owner: `systems/command-tasking/authority-boundary`
Last verified: `2026-08-08`
Verification boundary: owner route, lifecycle, no-mapping decision, and the
named consistency-gate route were rechecked; path-by-path citations retain the
recorded baseline boundary.
Baseline commit: `dd292f4b`

Status: owner-local maintained adjudication. It originated as the T9 (agency
and doctrine architecture) slice for the completed Unified Architecture
Program. The I68 A3 default-name ownership
move ([Agency Authority Census](agency_authority_census_20260721.md) §9)
surfaced a premise correction: the compiled `authorize_maintained_*` gates
operate on the `AgentRole` / `AgentAuthorityScope` **action-interface**
authority representation, not on the `CommandRelationship` / `AuthorityScope`
**echelon** enums. That correction exposed a representation boundary that had
never been adjudicated path-by-path: does any maintained code path ever map,
flow, or compare a value of one representation into/against the other? This
document adjudicates that boundary for every relevant censused path
(A2, A4, A5, A6, A13) plus the reverse (action-interface) direction, with
source pointers, and pins the verdicts with a load-bearing consistency gate
(`tests/architecture/agency/test_authority_representation_boundary.py`).

Per the T9 key-risk constraint (C2 semantics are research subject matter and
changes need domain-evidence review, not just parity), this slice makes **zero
C2 behavior change**: it reads code, records verdicts, and adds one read-only
structural gate. No profile, loader, runtime, or compiled file is modified.

## 1. The Two Representations

**Echelon authority** — doctrinal command-echelon relationships between command
nodes, represented as compiled C++ enums and carried as task-order data:

| Item | Source |
|------|--------|
| `enum class CommandRelationship` (`None`, `COCOM`, `OPCON`, `TACON`, `Support`, `ADCON`, `CoordinatingAuthority`, `DIRLAUTH`) | `src/components/tasking/common/core_tasking_enums.h:31-40` |
| `enum class AuthorityScope` (`Unspecified`, `Strategic`, `Operational`, `Tactical`, `Execution`) | `src/components/tasking/common/core_tasking_enums.h:42-48` |
| Carrier fields `TaskOrderCore::command_relationship` / `::authority_scope` | `src/components/tasking/common/task_order_core.h:15-16` |
| pybind exports (enums; `TaskOrderCore` / `TaskOrder` fields) | `src/interfaces/python/bindings_command.cpp:150-165, 493-494, 627-628` |

**Action-interface authority** — what a maintained agent may *do* through
which interface, represented as compiled string-scoped contracts and enforced
by the WP12 authorization gates:

| Item | Source |
|------|--------|
| `struct AgentAuthorityScope` (`scope` string + `world_index` / `entity_ids` / `roster_id` / `command_family`) | `src/runtime/contracts/policy_contracts.h:278-285` |
| Scope values `platform_control` / `mission_command` / `formation_coordination` | `src/runtime/contracts/policy_contracts.h:41-46, 187-191` |
| `struct AgentRole` (five-part schema; `authority_scope` member) | `src/runtime/contracts/policy_contracts.h:319-325` |
| Shape / compatibility / authorization predicates (`agent_authority_scope_has_required_shape`, `agent_role_action_interface_matches_authority_scope`, `authorize_maintained_action_intent`, `authorize_maintained_coordination_intent`) | `src/runtime/contracts/policy_contracts.h:339-360, 397-416, 454-503` |
| pybind exports | `src/interfaces/python/bindings_runtime.cpp:399-406, 441-452, 638-645` |

**Compiled-surface disjointness (load-bearing fact).** Across `src/**`, the
only compiled uses of `CommandRelationship::` / `AuthorityScope::` are the enum
definitions themselves, the `TaskOrderCore` default-member initializers, and
the pybind value exports — **no compiled decision logic reads an echelon value**
(`rg 'CommandRelationship::|AuthorityScope::' src/` exhausts to
`core_tasking_enums.h`, `task_order_core.h:15-16`, `bindings_command.cpp`).
Conversely, the action-interface family's defining headers
(`policy_contracts.h`, `information_transform_contracts.h`,
`counterfactual_replay_contract_types.h:96`) never name an echelon type. The
echelon enums are, on the compiled surface, pure carried data; the
action-interface representation is the only compiled authorization decision
surface.

**Terminology homonyms (documented, not mappings).** Two spellings straddle
the boundary without carrying values across it:

- `mission_command` is simultaneously the action-interface scope string
  `kAgentAuthorityScopeMissionCommand` (`policy_contracts.h:43-44`), the payload
  type `kActionInterfacePayloadMissionCommand` (`policy_contracts.h:37`), the
  scenario-data dict key (`gym_envs/scenario_loader/loading.py:113-117`), and
  the compiled `MissionCommand` DTO name. Same spelling, four meanings; no code
  converts one into another as an *authority value*.
- The snake_case attribute `authority_scope` names both the echelon field
  (`TaskOrderCore::authority_scope`, an `AuthorityScope` enum) and the
  action-interface member (`AgentRole::authority_scope`, an
  `AgentAuthorityScope` struct). The value domains are disjoint (enum int vs
  string-scoped struct); only the attribute spelling collides. The consistency
  gate therefore discriminates on type/enum/member names, not on this
  attribute spelling.

## 2. Method

For each A2/A4/A5/A6/A13 path the question adjudicated is: *does an
echelon-authority value (`CommandRelationship` / `AuthorityScope` member, or
its accessor spelling) ever flow into, or get compared against, an
action-interface authority value (`AgentRole` / `AgentAuthorityScope`, a scope
string, or an `authorize_maintained_*` call)* — in either direction? Evidence
is `rg` over the maintained surface plus a read of every implicated
definition/call site; verdict options are `mapped(evidence)` /
`no-mapping(evidence)` / `ambiguous(exact open question)`. The reverse
direction (the runtime-face action-interface authorization path) is
adjudicated with the same standard against the echelon vocabulary.

Whole-surface negative evidence used by several rows below: the action-interface
identifiers (`AgentRole`, `AgentAuthorityScope`, `authorize_maintained_*`,
`agent_role_*`, `is_known_agent_authority_scope`, `platform_control`,
`formation_coordination`, `PilotActionAssignment`, `CommandChainAssignment`)
have **zero occurrences** under `python/rl/tasking/**`, `python/rl/profile/**`,
and `gym_envs/**` — with the single exception of the out-of-census scalar
`NAVAL_STATION3_CARRIER_INTERFACE_KIND = "PilotActionAssignment"`
(`gym_envs/universal_env_parts/naval_actions.py:24`), a station-metadata
constant already recorded by the census (§3.2 out-of-census note) that touches
no echelon value.

## 3. Verdict Matrix

| Path | Site | Verdict | Evidence |
|------|------|---------|----------|
| A2 | `python/rl/tasking/common_core_profile.py` | **no-mapping** | Echelon-only surface: field->enum coercion map (`:191-192`), unset-field defaulting (`:219-222`, `:256-259`), spec coercion onto `TaskOrder.command_relationship` / `.authority_scope` (`:630-640`), inference dispatch + defaults (`:792-804`). Every value produced is an `ef_py.CommandRelationship` / `ef_py.AuthorityScope` member written to task-order fields. No action-interface identifier anywhere in `python/rl/tasking/**` (§2 negative evidence); nothing routes the produced enum into an `AgentRole` or compares it against a scope string. |
| A4 | `python/rl/profile/air_profile.py` | **no-mapping** | Echelon defaults (`:188-189`, `:211-214`, `:237-240`) and fire-authority field resolution incl. the leader-precedence arbitration (`:604-622`) write `MissionCommand` engagement fields (`engagement_authority_holder_id` / `_grantor_id` / `authorization_to_fire`) and task-order echelon fields. `MissionCommand` carries **no** echelon field (`src/components/command/common/mission_command_core.h`: `authorization_to_fire` at `:23`; no `command_relationship` / `authority_scope` member exists), and the file names no action-interface identifier (§2). |
| A5 | `python/rl/profile/ground_profile.py` | **no-mapping** | `infer_command_relationship` returns `Support` vs default (`:24-25`, `:156-170`); echelon defaults (`:233-234`, `:254-257`, `:287-297`); leader-vs-mission fire-authorization precedence (`:428-431`); OTC fallback naming (`:462`). All values are echelon enums or mission-command DTO fields; no action-interface identifier (§2). The precedence at `:428-431` arbitrates between two *echelon-side* producers (`leader_intent` vs `mission_cmd`), not between representations. |
| A6 | `python/rl/profile/naval_profile.py` | **no-mapping** | Echelon defaults (`:206-207`, `:223-226`, `:246-249`); warfare-role / OTC inference (`:273-292`); engagement-authority and ROE field fills plus mission-config re-reads (`:425-458`, `:505-552`). Same shape as A4/A5: `NavalWarfareRole` / `CommandRelationship` / `AuthorityScope` members and DTO fields only; no action-interface identifier (§2). (The census A6 open question about `loader.mission_cmd` vs `scenario_data["mission_command"]` rebinding is a *within-echelon-side* aliasing question and does not touch this boundary.) |
| A13 | `gym_envs/universal_env_parts/air_combat_event_action.py` | **no-mapping** | The canonical who-may-fire gate reads mission-command DTO fields through `cmd_view`: `holder_id = cmd_view.int_field("engagement_authority_holder_id", 0)`; `holder_ok = holder_id <= 0 or holder_id == agent_id`; `c2_authorized = authorization_to_fire AND holder_ok` (`:167-169`). `agent_id` is the env-layer agent/entity identity, not an `AgentAuthorityScope.entity_ids` read — the file (and all of `gym_envs/**`, §2) names no action-interface identifier. Noted adjacency, honestly recorded: both `engagement_authority_holder_id` and `AgentAuthorityScope.entity_ids` denote entities in the same integer id space, but no shared code path, conversion, or comparison links them. |
| Reverse | `python/rl/runtime/world_batch/adapter.py` | **no-mapping** | The runtime-face `AgentRole` construction derives `authority_scope.scope` **only** from the action payload type (`"mission_command"` if the payload is a mission command else `"platform_control"`, `:481-488`) and fills ids from the window request in the same block; the authorization call (`:639-642`) passes that role plus the intent. No echelon identifier (`CommandRelationship` / `AuthorityScope` / member names / `command_relationship`) occurs in the file. Even when the authorized intent carries a `MissionCommand`, the authorization predicate reads only the role shape, the scope<->interface compatibility, and the packet's `action_interface` descriptor + `has_pilot_action` / `has_mission_command` flags (`policy_contracts.h:418-436, 454-476`) — never a payload field, echelon or otherwise. |
| Reverse | `python/rl/runtime/agent_shim.py` | **no-mapping** | The Python-side `AgentRole` sketch (`:215` ff.) and its `authority_scope` mapping use only the action-interface keys (`scope` / `world_index` / `entity_ids` / `roster_id` / `command_family`, `:259-272`); no echelon identifier occurs in the file. |

**Summary: 5 of 5 forward paths and 2 of 2 reverse paths adjudicate to
no-mapping; 0 mapped; 0 ambiguous.** The two authority representations are
fully disjoint on today's maintained surface: echelon values live and die on
the task-order / mission-command DTO side; action-interface values live and
die on the runtime authorization side; the only touching points are spelling
homonyms (§1).

## 4. What This Verdict Does And Does Not Say

- It **does** say: converging A2/A4-A6/A13 onto the compiled
  `authorize_maintained_*` gates (the census §7 deferred semantic convergence)
  cannot be a mechanical re-pointing — there is no existing bridge to widen. A
  future convergence slice must *design* a mapping (or decide none should
  exist), which is exactly the domain-evidence decision T9 defers.
- It does **not** say the two representations are unrelated *doctrinally*.
  Whether an echelon state (e.g. `TACON` at `Tactical` scope) *should* imply
  an action-interface grant (e.g. `mission_command` scope over some roster) is
  a C2 design question this slice deliberately does not decide. The verdict is
  about what the code does today, and the gate pins that a mapping cannot be
  introduced silently.
- Registry note: `python/tasking_contracts/agency_registry.py` declares both
  vocabularies side by side (echelon mirrors `COMMAND_RELATIONSHIPS` /
  `AUTHORITY_SCOPE_LEVELS`; action-interface mirrors `ACTION_INTERFACE_SCOPES`
  / `ACTION_INTERFACE_KINDS` / `COMPILED_AUTHORIZATION_GATES`). Co-declaration
  in a frozen, consumer-free registry is documentation, not a mapping; the
  registry maps neither family onto the other.

## 5. Domain-Review Record

**Honest status: this is a code-evidence adjudication performed by the unified
architecture program workline (this iteration). No human C2 domain expert has
reviewed or signed off on these verdicts yet.** The verdicts are structural
claims about what the code does — the kind of claim code evidence can settle —
and each row is falsifiable from its cited lines. What code evidence cannot
settle, and what a human domain reviewer is asked to adjudicate before any
mapping slice lands:

1. Should an echelon->action-interface mapping exist at all (e.g. does holding
   `TACON` / `Tactical` over a unit doctrinally entail `mission_command`
   action-interface authority over it), or are the representations
   intentionally orthogonal (echelon = command-node doctrine, action-interface
   = execution-agent capability)?
2. If a mapping should exist, which side owns it (compiled contract vs Python
   normalization layer) and which of the census A-paths must route through it?
3. Is the A13 identity adjacency (holder id and `entity_ids` sharing one id
   space) a latent requirement that who-may-fire should eventually consult
   `AgentAuthorityScope.entity_ids`, or a coincidence of id allocation?

Sign-off state: `pending human domain review` (record the reviewer, date, and
verdict deltas here when that review happens; until then, the no-mapping gate
pins the status quo).

### 5.1 Sign-Off Record (2026-07-27, Owner-Delegated)

**Nature of this record (honesty constraint).** This is an **owner-delegated
agent adjudication**: the repository owner (single maintainer) explicitly
authorized recording this sign-off on their behalf ("允许代签", 2026-07-27).
It is **not** an independent human C2 domain-expert review and must never be
cited as one. The three §5 questions were adjudicated substantively before
recording — against the cited code paths, the census record, and the
repository's C2/doctrine forward docs — and the evidence consulted is listed
per verdict.

**Question 1 — should an echelon->action-interface mapping exist at all:
NO implicit mapping; the no-mapping verdicts stand as the maintained
contract.** Holding `TACON` at `Tactical` scope does not, in this program's
doctrine model, implicitly entail `mission_command` action-interface
authority:

- The repository's own doctrine reference frames C2 as a mission-command
  problem built around authority delegation that is **explicit**
  (`docs/domains/joint/service_profiles/domains/air_force_profile.md` — AFDP 3-0.1's commander-centered
  function with *explicit delegation of authority*); nothing in
  `docs/systems/command-tasking/work/issues/` (command-link roadmap, operation layer) derives an
  execution-agent capability from an echelon annotation.
- The echelon defaults are ubiquitous carried data: A3 defaults **every**
  normalized task order to `TACON`/`Tactical` (census §9), and no compiled
  decision logic reads an echelon value (§1). An implicit entailment would
  therefore grant `mission_command` interface authority to essentially every
  agent by default — collapsing the deliberate distinction between carried
  command-node doctrine data and enforced execution-agent capability.
- Consequently the two representations are maintained as **intentionally
  orthogonal** (echelon = command-node doctrine annotation; action-interface =
  execution-agent capability contract). Any future mapping must arrive as an
  **explicit registered structure** (G5 "extension is registration") through a
  dedicated domain-evidence slice — never by name similarity (iteration-queue
  §5 red line).

**Question 2 — which side owns a mapping if one is ever introduced: moot
under the Question 1 verdict; the registry is pre-designated as the
declaration owner.** Should a future domain-evidence slice ever introduce a
mapping, `python/tasking_contracts/agency_registry.py` is pre-designated as
its declaration owner: it is already the single declarative owner of the
authority vocabulary and the only place both families stand side by side
(`CATEGORY_SCOPE` co-declares `AUTHORITY_SCOPE_LEVELS +
ACTION_INTERFACE_SCOPES` at `agency_registry.py:604` — a disclosed
co-declaration, not a mapping), and its G5 discipline (frozen declaration plus
drift-pin gates) is exactly the shape such a mapping would need. Which
A-paths would route through it stays with that future slice.

**Question 3 — the A13 identity adjacency: coincidence of id allocation,
monitored by gate; not a latent requirement.** `engagement_authority_holder_id`
and `AgentAuthorityScope.entity_ids` share one integer id space because both
denote world entities and every entity reference uses that space — the shared
value domain is inherent to entity identity, not evidence of a designed
linkage. The two checks answer different questions (per-mission-command
engagement authority held by an entity vs per-agent interface capability over
entities); no cross-read, conversion, or comparison exists (§3 A13 row), and
the landed boundary gate
(`tests/architecture/agency/test_authority_representation_boundary.py`) turns
a future cross-read red: obtaining an action-interface value inside the pinned
files requires naming at least one discriminating identifier (`AgentRole` /
`AgentAuthorityScope` / `authorize_maintained_*`), which the gate catches.
Status: **monitored-by-gate**. If who-may-fire is ever redesigned to consult
`AgentAuthorityScope.entity_ids`, that is a Question-1-class mapping and takes
the same explicit-registration path.

**Queue consequence.** With no-mapping signed off, the scheduled T9 behavioral
slice **I86 closes held** per its own row logic in the I72+ iteration queue
(`iteration_queue_i72_plus_20260726.md`: "If I77 returns no mapping, I86
closes held instead").

Sign-off state: `adjudicated — owner-delegated (2026-07-27)`; the pending line
above is retained as landed history, and this record is the entry it called
for — with the delegation nature stated rather than a human domain-expert
identity.

Sign-off line: "Owner-delegated agent adjudication under explicit owner
authorization (2026-07-27); recorded by the unified architecture program
workline."

## 6. Consistency Gate

`tests/architecture/agency/test_authority_representation_boundary.py` makes
the no-mapping verdicts load-bearing:

1. **Forward pins.** Each A2/A4/A5/A6/A13 file's executable-code surface
   (docstrings/comments stripped, import/`__all__` plumbing dropped — reusing
   the census gate's scanner so both gates agree on what "code" means; string
   literals kept, since scope values travel as literals) must contain none of
   the action-interface discriminators (`AgentRole`, `AgentAuthorityScope`,
   `AgentRoleAuthorizationResult`, `authorize_maintained_*`, `agent_role_*`,
   `is_known_agent_authority_scope`, `platform_control`,
   `formation_coordination`, `PilotActionAssignment`,
   `CommandChainAssignment`), matched by word boundary.
2. **Reverse pins.** `adapter.py` / `agent_shim.py` must contain none of the
   echelon discriminators (`CommandRelationship`, `AuthorityScope`, `COCOM`,
   `OPCON`, `TACON`, `ADCON`, `DIRLAUTH`, `CoordinatingAuthority`,
   `command_relationship`, `infer_command_relationship`).
3. **Compiled disjointness pins.** Each family's defining headers
   (comment-stripped) must not name the other family's types; a word-boundary
   regression test proves `AuthorityScope` does not fire inside
   `AgentAuthorityScope`.
4. **Own-family sanity markers.** Each pinned file must still carry a marker
   of its *own* family, so a hollowed-out or repurposed file fails loudly
   instead of passing the absence check vacuously.
5. **Tamper self-tests.** Injecting `ef_py.AgentRole()` +
   `"platform_control"` into a profile, injecting
   `ef_py.CommandRelationship.TACON` into the adapter, and a synthetic
   cross-family comparison are each detected; docstring/comment mentions are
   not false positives. An on-disk tamper run (appending a
   `"platform_control"` literal to `ground_profile.py`) was verified to turn
   the gate red before being reverted.

Homonym boundary (deliberate): `mission_command` and the snake_case
`authority_scope` attribute are excluded from the discriminator sets (§1), so
the gate cannot flag the legitimate homonym uses; a mapping smuggled *only*
through those spellings would need to name at least one real type, member, or
gate identifier to do anything, which the discriminators catch.

The gate is registered in `tests/smoke/ci_smoke_suite.json` (measured cost:
the whole agency gate directory, including this module, runs in under three
seconds).

## 7. Deferred / Held

- **Designing any echelon<->action-interface mapping** (or formally deciding
  none shall exist) — held for a domain-evidence-reviewed T9 semantic slice
  (§5 questions). This document only proves no mapping exists today.
- **Census §7 semantic convergence** of A1-A14 — unchanged, still deferred;
  this adjudication narrows its design space (§4) but converges nothing.
- **A6 mission_cmd aliasing open question** — unchanged (within-echelon-side;
  see census §3.2 A6 row).

## Related

- Historical origin: completed Unified Architecture Program T9 adjudication;
  current authority is the simulation architecture standard below.
- [Agency Authority Census (2026-07-21)](agency_authority_census_20260721.md)
  (A-path register; §9 I68 premise correction this adjudication completes)
- [Simulation System Architecture Design](../../../architecture/standards/simulation_system_architecture_design.md)
  (Agency face; AgentRole five-part schema)
- `python/tasking_contracts/agency_registry.py` (both vocabularies' declarative owner)
- `tests/architecture/agency/test_authority_representation_boundary.py`
  (this adjudication's consistency gate)
- `tests/architecture/agency/test_authority_registry_gate.py` (census ratchet gate)
