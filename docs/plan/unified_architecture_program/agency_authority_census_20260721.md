# Agency Authority Census (2026-07-21)

Language:
- English canonical: `agency_authority_census_20260721.md`
- Chinese companion: [agency_authority_census_20260721.zh.md](agency_authority_census_20260721.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/plan/unified_architecture_program/agency_authority_census_20260721.md`
Owner: `unified architecture program workline`
Last verified: `2026-07-21`
Baseline commit: `8bd21d86`

Status: T9 (agency and doctrine architecture) slice-1 census for the
[Unified Architecture Program](README.md). This is a descriptive census
register (`reference`), not an independent review: it enumerates the scattered
authority-check ("who-may-command / who-may-fire / who-may-write") sites on the
maintained tasking surface, classifies each into one or more authority
dimensions, and records the registered vocabulary and ratchet gate that pin
them. Per the T9 key-risk constraint (C2 semantics are research subject matter
and changes need domain-evidence review, not just parity), this slice makes
**zero C2 behavior change**: it only produces the census, a single declarative
vocabulary owner, and a ratchet gate. Converging the pinned call sites onto the
vocabulary is deferred to a later, domain-evidence-reviewed slice.

This is the **second repair round** of the slice-1 census (independent review
verdicts: needs-repair, twice). Round 1 (1) completed the vocabulary mirror
against the compiled authorities, (2) re-adjudicated several site classifications
that a rigid detection-token-to-category mapping had distorted, and (3) closed
ratchet blind spots. Round 2 (4) made the compiled-header authority extractor
comment-proof (quote-aware C++ comment stripping before enum/scope extraction, so
a commented-out "ghost" member or a `}` inside a block comment can no longer
deceive it), (5) actually tokenized the synonym family behind **word-boundary**
matching so the ratchet bites a file that only uses a derived spelling, (6)
re-adjudicated A14 from `arbitration` to `gating` on source-code evidence, and (7)
pinned the *exact* category set of the key re-adjudicated sites. The per-item
changes are marked inline below and summarized in §8.

**T9 slice 2 (I53) update.** The §7 "call-site convergence" backlog was
adjudicated for its **zero-semantic-risk mechanical subset only** (per-site: is a
token a string/constant literal repointable at an `agency_registry` constant, or
control-flow/semantic logic?). **Within the censused A1-A14 list the narrow
adjudication converged 0 of 14 sites** -- their scatter is compiled-`ef_py`-enum
access, schema-layer DTO field-name keys, and `if/else`/prose logic (§3.2). A
full-maintained-surface hunt (I53 repair round) then found **one true mechanical
site outside the A-list**: `python/rl/runtime/agent_shim.py` locally duplicated
the five-policy merge vocabulary; its `ALLOWED_MERGE_POLICIES` now references the
registry's `MERGE_POLICIES` directly, with a drift-pin unit test (§3.2). No
fixture or ratchet-gate change was needed (the site is outside the T9 scan roots
and merge-policy strings are not detection tokens). Semantic convergence stays
deferred.

## 1. Scope And Method

The maintained authority surface was surveyed with `rg` across
`python/tasking_contracts/**`, `python/rl/tasking/**`, `python/rl/profile/**`,
and the C2/ROE-relevant `gym_envs/**` modules; `src/**` was surveyed read-only
for the compiled authority contracts. A site qualifies as an authority-check
scatter when it decides, delegates, arbitrates, or gates *who may command whom*
or *who may write which command/ROE field* -- as distinct from pure DTO field
plumbing.

Each site is fingerprinted by a per-file **token-to-count** map over a stable set
of **detection tokens** (distinctive authority identifiers/phrases), matched by
**word boundary** (`\bTOKEN\b`) so a token never double-counts inside a longer
identifier. A repeated occurrence of an already-present token changes the count
and therefore drifts the fingerprint. Word-boundary matching (round 2) is what
lets the previously-untokenized synonym family be tokenized without collisions:
the bare `commander_id` local (distinct from `ground_commander_id`), the
snake_case `command_relationship` accessor, the `infer_command_relationship`
inference function, and the loader-delegate spelling
`_hierarchical_command_chain_active` are now first-class tokens, so a file that
carries authority logic only under a derived spelling is caught rather than
slipping the ratchet. The scanner matches `code`-surface tokens only in
executable code -- comments, docstrings, and `import`/`__all__` re-export plumbing
are stripped first, so an innocent docstring mention or a pure re-export is not a
false positive -- and matches `prose`-surface folklore phrases only in
docstrings/comments (where such conventions deliberately live).

Each site is classified into one or more of six authority dimensions (`role`,
`scope`, `delegation`, `arbitration`, `gating`, `doctrine`), plus an `undecided`
bucket reserved for sites whose semantics are not yet adjudicated. Each detection
token maps to a **set of candidate categories** (not one fixed category) in
`python/tasking_contracts/agency_registry.py:AUTHORITY_TOKEN_CATEGORIES`; a
site's declared categories must be *grounded* in (a subset of) and *cover* (touch
every one of) its pinned tokens' candidate categories. The per-file fingerprint
is pinned in
`tests/architecture/fixtures/agency_authority_census_20260721.json`.

The compiled authority model already exists as the reference target: the WP12
`AgentRole` / `authorize_maintained_action_intent` /
`authorize_maintained_coordination_intent` contracts in
`src/runtime/contracts/policy_contracts.h` and
`src/runtime/contracts/information_transform_contracts.h`, gated by
`tests/architecture/policy_execution/*`. The Python maintained surface has not
yet converged onto it; that convergence is the rest of T9's work.

## 2. Authority Vocabulary (Source Of Truth)

The registered vocabulary is aligned with the architecture authority
([Simulation System Architecture Design](../architecture/simulation_system_architecture_design.md)
Agency face) and the compiled contracts. The ratchet gate parses the enum/scope
headers and fails on any drift between the mirror below and the compiled values.
Nothing below is invented.

- **AgentRole five-part schema** (`simulation_system_architecture_design.md`):
  `role`, `authority_scope`, `information_state_source`, `decision_model_ref`,
  `action_interface`. Each declared role now carries all five slots (see §5).
- **`AuthorityScope`** (`src/components/tasking/common/core_tasking_enums.h`):
  `Unspecified`, `Strategic`, `Operational`, `Tactical`, `Execution`.
- **Action-interface scopes** (`src/runtime/contracts/policy_contracts.h`
  `kAgentAuthorityScope*` / `is_known_agent_authority_scope`): `platform_control`,
  `mission_command`, `formation_coordination`. (Repair: `mission_command` was
  missing from the first-round mirror and is restored.)
- **Action-interface kinds** (`policy_contracts.h`
  `is_known_agent_action_interface_kind`): `PilotActionAssignment`,
  `CommandChainAssignment`.
- **`CommandRelationship`** (`core_tasking_enums.h`): `None`, `COCOM`, `OPCON`,
  `TACON`, `Support`, `ADCON`, `CoordinatingAuthority`, `DIRLAUTH`.
- **`CoordinationMode`** (`core_tasking_enums.h`): `Unspecified`, `Independent`,
  `Attached`, `Follow`, `Support`, `Screen`, `Rejoin`, `Recover`, `Detached`.
- **`NavalWarfareRole`** (`src/components/domains/naval/tasking/naval_tasking_enums.h`):
  `Unspecified`, `ScreenCommander`, `SurfaceActionCommander`, `AirDefenseCommander`,
  `SeaControlCommander`, `LogisticsCoordinator`. (Repair: all six members --
  including `Unspecified` -- are now declared, matching the header.)
- **`merge_policy` arbitration** (`simulation_system_architecture_design.md`):
  `last_write_wins`, `priority_override`, `reject_on_conflict`, `merge_by_field`,
  `append_only`; source priority `human > policy > scripted > diagnostic`
  (source: `simulation_system_architecture_design.md`, Agency-face cross-layer
  merge/arbitration rule).
- **Enable/disable gates (`gating`)**: the command-chain activation gate
  `hierarchical_command_chain_active` (loader-delegate spelling
  `_hierarchical_command_chain_active`) that decides whether the leader/command-chain
  authority path runs at all (A7/A9), and the air-combat fire-eligibility mask
  `_air_combat_c2_roe_policy_fire_mask_open` (A14) that decides whether the policy
  *may fire*. Both are enable/disable gates and read no holder id to pick a winner;
  this is a distinct dimension from `arbitration` (conflict resolution among
  competing sources). (Repair round 2: fire-eligibility gate added as a second
  gating family.)
- **`DoctrineFamily`** (`simulation_system_architecture_design.md` domain-extension
  model): task templates, ROE, authority delegation, engagement policy --
  declared as a vocabulary placeholder only this slice (no mechanism).

## 3. Authority Scatter Register

Every maintained gated site is pinned below. `Category` is the site's adjudicated
authority dimensions (grounded in and covering its detection-token candidate
categories). `Form` records the current shape of the check. The per-file
token-to-count fingerprint lives in the census JSON.

| # | Location | Detection tokens | Category | Form | Semantic |
|---|----------|------------------|----------|------|----------|
| A1 | `python/rl/tasking/leader_tasking.py` | `allowed to directly author` (prose) | scope | docstring-convention | `ScriptedC2TaskManager` folklore: C2 may consume situation + reports but may not directly author low-level mission commands (leader-layer authority). |
| A2 | `python/rl/tasking/common_core_profile.py` | `AuthorityScope`, `CommandRelationship`, `NavalWarfareRole`, `command_relationship`, `commander_id`, `ground_commander_id`, `infer_command_relationship`, `officer_in_tactical_command`, `warfare_role_code` | delegation, role, scope | default-inference | Cross-profile authority defaults: command relationship + authority scope, OTC delegation, naval warfare role, ground/`commander_id` role, `infer_command_relationship` dispatch. Default/identity inference; no conflict resolution. **R2: pins the snake_case/`commander_id`/`infer_` synonyms.** |
| A3 | `python/rl/profile/common_core_defaults.py` | `AuthorityScope`, `CommandRelationship` | delegation, scope | default-provider | Leaf default-value providers for the delegation/scope enums. (Its `command_relationship_default()` function name is compound-excluded by word boundary; pinned via `CommandRelationship`.) |
| A4 | `python/rl/profile/air_profile.py` | `AuthorityScope`, `CommandRelationship`, `authorization_to_fire`, `command_relationship`, `engagement_authority_grantor_id`, `engagement_authority_holder_id`, `roe_state` | arbitration, delegation, doctrine, scope | default+precedence | Air defaults + engagement-authority field resolution + **leader-intent-over-mission-command fire-authority precedence**. (`leader_authorization_to_fire` local is word-boundary excluded; file pinned via the bare field.) |
| A5 | `python/rl/profile/ground_profile.py` | `AuthorityScope`, `CommandRelationship`, `authorization_to_fire`, `command_relationship`, `ground_commander_id`, `infer_command_relationship`, `officer_in_tactical_command` | arbitration, delegation, role, scope | default+delegation+precedence | Ground defaults + OTC/ground-commander delegation + **leader-intent-vs-mission-command fire-authorization precedence** (`build_kernel_mission_command`, lines 428-431). **R1: added arbitration**; **R2: pins the `command_relationship`/`infer_command_relationship` synonyms and pins the category set exactly.** |
| A6 | `python/rl/profile/naval_profile.py` | `AuthorityScope`, `CommandRelationship`, `NavalWarfareRole`, `authorization_to_fire`, `command_relationship`, `engagement_authority_grantor_id`, `engagement_authority_holder_id`, `officer_in_tactical_command`, `roe_state`, `warfare_role_code` | arbitration, delegation, doctrine, role, scope | default+delegation+precedence | Densest single-file surface: warfare-role, OTC, command relationship, ROE, engagement/fire-authority field resolution. **I53 correction (was "leader precedence"):** the naval profile carries no `leader_intent`; its `build_kernel_mission_command` fills the authority/ROE fields from `loader.mission_cmd` and then re-reads the same fields from `scenario_data["mission_command"]` -- on the regular load path the two names are bound to the **same dict** (`loading.py:113-117`, re-synced at `:242`), so the re-read is idempotent rather than a real precedence; whether any runtime rebinding ever separates them is to-be-adjudicated (§3.2). **R2: pins the snake_case `command_relationship` token.** |
| A7 | `gym_envs/scenario_loader/core.py` | `_hierarchical_command_chain_active` | gating | delegate-method | Loader delegate of the command-chain **activation** gate (enable/disable). **R1: arbitration -> gating**; **R2: pinned via the loader-delegate token `_hierarchical_command_chain_active`** (word-boundary matching no longer folds the gate name into the underscore-prefixed method) with the category set pinned exactly. |
| A8 | `gym_envs/scenario_loader/runtime_state.py` | `authorization_to_fire`, `engagement_authority_grantor_id`, `engagement_authority_holder_id`, `ground_commander_id`, `roe_state` | delegation, doctrine, role | state-projection | Pure state mirror: projects mission-command authority/ROE + ground-commander fields into runtime-state JSON mirrors; makes no decision. **R1: dropped arbitration** (mirror, not a gate; `engagement_authority_holder_id` here is a mirrored identity); **R2: category set pinned exactly** so arbitration cannot be silently re-added. |
| A9 | `gym_envs/scenario_loader/behavior_runtime/command_chain.py` | `hierarchical_command_chain_active` | gating | activation-gate | **Definition site** of the command-chain **activation** gate (from task_order/leader_intent/pilot_report/c2_task_name presence). **R1: arbitration -> gating**; **R2: category set pinned exactly**. |
| A10 | `gym_envs/scenario_loader/behavior_runtime/post_waypoint_transition.py` | `authorization_to_fire` | delegation | field-copy | Propagates the fire-authority delegation onto `leader_intent` at a transition. |
| A11 | `gym_envs/scenario_loader/reward_runtime/air_combat.py` | `authorization_to_fire`, `roe_state` | delegation, doctrine | reward-gate | ROE `authorized_candidate` gate conditioning pre-fire reward terms (reader; no command authorship). |
| A12 | `gym_envs/scenario_loader/reward_runtime/naval.py` | `authorization_to_fire`, `roe_state` | delegation, doctrine | reward-gate | Pre-fire ROE-hold bonus vs authorization penalty gate (reader; no command authorship). |
| A13 | `gym_envs/universal_env_parts/air_combat_event_action.py` | `authorization_to_fire`, `engagement_authority_holder_id` | arbitration, delegation | fire-authority-gate | **Canonical target**: `holder_ok = (holder_id <= 0 or == agent_id)`; `c2_authorized = authorization_to_fire AND holder_ok`. Who-may-fire as folklore in a call site. |
| A14 | `gym_envs/scenario_loader/mission_observation.py` | `authorization_to_fire`, `engagement_authority_grantor_id`, `engagement_authority_holder_id`, `roe_state` | delegation, doctrine, gating | observation-projection+fire-mask | Projects the C2/ROE authority fields into the `air_combat_c2_roe` observation **and computes the `_air_combat_c2_roe_policy_fire_mask_open` eligibility gate** (`authorization_to_fire AND wcs_state != 1 AND not engage_hold AND shot_policy_state > 0 AND shot_budget_remaining > 0 AND not pending_assessment AND target_contact_present`, lines 281-300). **R2 (P1-3): arbitration -> gating** -- the mask reads `authorization_to_fire` (+ wcs/engage/shot state) but **not** the holder/grantor id (pure projection, lines 405-406), so it resolves no who-may-fire competition (that is A13's job); category set pinned exactly. **Write-excluded** (I45 observation face); read-only census. |

### 3.1 Cross-referenced sites and scan-scope boundary (not gated by T9)

These carry authority logic but sit outside the T9 gated scan roots; they are
recorded for completeness and deliberately not ratcheted (repair: the previous
`### 2.1` mis-numbering is corrected to `### 3.1`).

| # | Location | Semantic |
|---|----------|----------|
| R1 | `python/rl/runtime/world_batch/cooperative_director.py` | Runtime/observation face: world-level `is_leader` role/leader arbitration and formation-role metadata assignment. |
| R2 | `python/rl/runtime/world_batch/adapter.py` | Runtime/observation face: sets `authorization_to_fire` on the facade command path. |

Additional deliberately out-of-scope faces (documented so a new authority-bearing
file there is not silently missed, and to state a uniform standard):

- **Policy-network / algorithm face** (`python/rl/policy_algo/**`):
  `policies.py`, `hmoe_routing.py`, `first_event_projection.py`, and
  `_first_event_mixin.py` read the `authorization_to_fire` mission column as a
  neural-network input. These are *consumers* of the authority field, not
  tasking-authority decision/delegation/arbitration sites, and are out of the T9
  scan roots.
- **Re-export plumbing** (uniform standard): pure `import` + `__all__` re-exports
  are not authority sites. `gym_envs/scenario_loader/behavior_runtime/__init__.py`
  (re-exports `hierarchical_command_chain_active`) and
  `python/rl/tasking/ground_adapter.py` (re-exports `infer_command_relationship`)
  are treated identically -- the scanner strips `import`/`__all__` statements, so
  neither is counted. The authority logic is pinned at its definition/delegate
  site (A9 / A2) instead. (Repair: the first round counted the `__init__.py`
  re-export but not `ground_adapter.py`; both are now excluded consistently.)

### 3.2 I53 Mechanical-Convergence Adjudication (T9 Slice 2)

T9 slice 2 works the §7 call-site-convergence backlog for the **zero-semantic-risk
mechanical subset only**: per site, is each authority token a *string/constant
literal* that can be mechanically repointed at an `agency_registry` constant with a
byte-identical runtime value, or *control-flow / semantic logic* that must not move
this slice? **Finding: within the censused A1-A14 list the narrow adjudication
stands at 0 of 14 convergeable; a full-maintained-surface hunt (I53 repair round)
found one true mechanical site outside the A-list -- the `agent_shim` merge-policy
collection -- which was converged this slice (see "Converged at I53" below).**
The A1-A14 authority "scatter" is not duplicated literal vocabulary
collections. It is three forms, each already out of the mechanical subset:

- **Compiled `ef_py` enum attribute access** (A2-A6): the vocabulary lives in the
  compiled kernel and is read as `getattr(ef_py.CommandRelationship, "TACON")` /
  `getattr(namespace, "ScreenCommander")`. The registry is a **mirror** of that
  compiled source of truth (the §6 gate pins registry == header), so repointing a
  consumer at the mirror would *regress* the source of truth, not converge it --
  and the census's own "do not touch" list already excludes compiled-enum access.
- **Schema-layer DTO field-name keys** (A4-A6, A8, A10-A14): `mission_cmd.get(
  "authorization_to_fire")`, `("roe_state", "roe_state")` mirror pairs, etc. These
  are mission-command DTO/JSON contract field names owned by the schema layer
  (`python/tasking_contracts/mission_defs.py` / the DTO schema generator); the
  registry only *cross-references* them as `DELEGATION_CARRIERS` /
  `DOCTRINE_FAMILY.roe_pattern_fields` "declared documentation, not an enforced
  ACL". Repointing dozens of field reads at the registry would be a category error
  (DTO ownership belongs to T1) and an anti-hub violation (G2), and the registry
  exposes them only positionally (fragile), so it is not a clean mechanical win.
- **`if/else` authority logic or English-prose folklore** (A1, A7, A9, A11-A13):
  the activation gate, the who-may-fire arbitration, the reward ROE gates, and the
  scripted-C2 authorship convention. These are the semantic logic itself and the
  census already defers them.

A one-time equivalence proof confirmed every site's vocabulary is **byte-identical**
to the registry constants, split by the term's *actual registration location*
(I53 repair: the first-round claim folded everything into carriers/pattern
fields, which was imprecise for two role-identity fields):

- **Enum mirrors**: `COMMAND_RELATIONSHIPS`, `AUTHORITY_SCOPE_LEVELS`,
  `COORDINATION_MODES`, `NAVAL_WARFARE_ROLES` set-equal the live `ef_py` members.
- **Delegation carriers** (`DELEGATION_CARRIERS`): `officer_in_tactical_command`,
  `engagement_authority_grantor_id`, `authorization_to_fire`,
  `command_relationship`.
- **ROE pattern fields** (`DOCTRINE_FAMILY.roe_pattern_fields`): `roe_state`,
  `authorization_to_fire`, `engagement_authority_holder_id`,
  `engagement_authority_grantor_id`.
- **Role `authors` fields** (`AUTHORITY_ROLES[*].authors`): `ground_commander_id`
  is registered as `AUTHORITY_ROLES["ground_commander"].authors[0]` and
  `warfare_role_code` as `AUTHORITY_ROLES["naval_warfare_commander"].authors[0]`
  -- role-identity author fields, **not** carriers or pattern fields.

So every A1-A14 non-convergence verdict below is **architectural, never a value
mismatch**. Because no A-list code changed, the per-file token->count
fingerprints are unchanged and the ratchet gate is untouched.

**Converged at I53 (full-surface hunt, outside the A-list):**
`python/rl/runtime/agent_shim.py` locally re-declared the five SCAL merge
policies -- five `MERGE_*` string constants plus an `ALLOWED_MERGE_POLICIES`
tuple duplicating `MERGE_POLICIES` (same values, same order, same type). This is
the exact "locally re-declared vocabulary collection" shape the mechanical
subset targets, and the dependency direction `python.rl -> python.tasking_contracts`
is the census's recorded legal direction. Convergence keeps the five named
constants as literals (they are keyword-argument defaults and greppable call-site
vocabulary; deriving them by unpacking/indexing would add positional fragility)
and repoints the *collection* -- `ALLOWED_MERGE_POLICIES` is now the registry's
`MERGE_POLICIES` object itself, so the `_normalize_merge_policy` membership gate
validates against the registry-owned vocabulary. A drift-pin unit test
(`tests/runtime/test_agent_shim.py::test_merge_policy_vocabulary_is_owned_by_the_agency_registry`)
asserts tuple identity plus each named constant's value/order against the
registry, so neither side can drift silently. `agent_shim.py` sits outside the
T9 scan roots and the merge-policy strings are not detection tokens, so the
census fixture and ratchet gate needed no change.

| # | Vocabulary form at site | Verdict | Reason (not a mechanical subset this slice) | Held precondition |
|---|---|---|---|---|
| A1 | Prose folklore in a docstring | not convergeable | English convention, not code -- cannot become an import; `SCOPE_FOLKLORE_RULES` mirrors it descriptively. | Semantic slice: make the C2 authorship boundary enforceable data (domain-evidence review). |
| A2 | Compiled `ef_py` enum access + default-inference dispatch | not convergeable | Compiled-enum source of truth + control-flow; registry is a mirror of `ef_py`, so repointing would regress source of truth. | Route default-inference through the compiled `authorize_maintained_*` (domain review). |
| A3 | `getattr(ef_py.CommandRelationship,'TACON')` / `AuthorityScope 'Tactical'` | not convergeable | Single compiled-enum member access; `COMMAND_RELATIONSHIPS[i]` would be fragile positional indexing into the mirror (excluded: compiled-enum). | Default-provider convergence onto compiled defaults (later slice). |
| A4 | Compiled enums + DTO keys + leader-vs-mission precedence | not convergeable | Compiled-enum + DTO field keys + arbitration `if/else`. | Semantic arbitration slice (domain review). |
| A5 | Compiled enums + DTO keys + `infer_command_relationship` + precedence | not convergeable | Compiled-enum + delegation/arbitration control-flow (category set pinned). | Semantic delegation/arbitration slice. |
| A6 | `getattr(namespace,'ScreenCommander')` + compiled enums + DTO keys | not convergeable | Compiled-enum member access (warfare-role inference) + DTO field keys. Precision note (I53 repair round 2): `naval_profile.py` carries no `leader_intent`. Its `build_kernel_mission_command` fills the authority/ROE fields (`roe_state`, holder/grantor ids, `authorization_to_fire`) from `loader.mission_cmd` and then re-reads the same fields from `scenario_data["mission_command"]`; at load time the two names are bound to the **same mapping** (`loading.py:113-117`, re-synced at `:242`), so on the regular path the re-read is idempotent, not a precedence. Whether any runtime rebinding site ever separates the two mappings into a real override is **to-be-adjudicated**. | Semantic warfare-role/delegation slice, plus adjudicating whether the runtime rebinding of `loader.mission_cmd` vs `scenario_data["mission_command"]` ever forms a real precedence (or evidence of an actual separation path). |
| A7 | `_hierarchical_command_chain_active` delegate method | not convergeable | Pure delegation to the activation-gate impl; control-flow, no vocabulary literal. | Semantic command-chain activation convergence. |
| A8 | DTO field-name pairs in JSON-mirror tuples | not convergeable | State mirror over schema-layer field names (not agency vocabulary); repointing = category error + hub coupling. | DTO field-name ownership decision (T1 schema), not T9. |
| A9 | `hierarchical_command_chain_active()` presence checks | not convergeable | The `if/else` activation-gate logic itself (excluded). | Semantic activation-gate slice. |
| A10 | `leader_intent.authorization_to_fire = mission_cmd.get(...)` | not convergeable | Field-copy control-flow over a DTO key. | Semantic delegation slice. |
| A11 | reads `roe_state`/`authorization_to_fire` -> ROE reward gate | not convergeable | Reward-side `if/else` reader; DTO keys. | Semantic ROE / DoctrineFamily-mechanism slice. |
| A12 | reads `authorization_to_fire`/`roe_state` -> reward gate | not convergeable | Reward-side `if/else` reader; DTO keys. | Semantic ROE / DoctrineFamily-mechanism slice. |
| A13 | `holder_ok`/`c2_authorized` who-may-fire arbitration | not convergeable | The who-may-fire arbitration logic itself (excluded); DTO keys. Canonical T9 target. | Semantic arbitration slice (domain-evidence review). |
| A14 | fire-mask eligibility gate + DTO keys | not convergeable + write-excluded | Observation-face ownership (I45/I50; I50 actively converged its reads onto `observation_view`) -- write-exclusion still applies; the mask is control-flow, not a literal collection. | Observation-face (T8 line) coordination; semantic gate slice. |

**Out-of-census note.** `gym_envs/universal_env_parts/naval_actions.py` defines the
module scalar `NAVAL_STATION3_CARRIER_INTERFACE_KIND = "PilotActionAssignment"`
(a byte-match of `ACTION_INTERFACE_KINDS[0]`). It is **not** a censused authority
site -- it carries no detection token, so the ratchet never sees it -- and is a
single scalar rather than a duplicated collection; repointing it at the mirror by
positional index would add fragility for no authority-decision benefit, so it is
recorded here and left untouched.

## 4. Category Distribution

| Category | Files | Description |
|----------|-------|-------------|
| scope | 6 (A1-A6) | Authority echelon + the C2 read/write-scope folklore. |
| role | 4 (A2, A5, A6, A8) | Command-node identities (OTC, ground/`commander_id`, naval warfare role). |
| delegation | 11 (A2-A6, A8, A10-A14) | Command relationships (incl. the snake_case / `infer_` synonyms), OTC/grantor transfer, fire-authority delegation. |
| arbitration | 4 (A4, A5, A6, A13) | Leader-over-mission precedence (A4/A5) + who-may-fire holder gate (A13); A6's arbitration-shaped re-read is idempotent on the regular load path and to-be-adjudicated (I53 correction, §3 A6 row). (**R2**: A14 moved out -- its fire mask is a gate, not conflict resolution.) |
| gating | 3 (A7, A9, A14) | Command-chain activation (A7/A9) + the air-combat fire-eligibility mask (A14). |
| doctrine | 6 (A4, A6, A8, A11, A12, A14) | ROE-state / weapon-control pattern fields. |
| undecided | 0 | No unadjudicated sites this slice. |

Total gated sites: 14 files. Cross-referenced / out-of-scope: R1, R2 (runtime
face) plus the policy-network face (`python/rl/policy_algo/**`).

## 5. Registered Vocabulary Design

`python/tasking_contracts/agency_registry.py` is the single declarative owner of
the authority vocabulary (G5 "extension is registration"). It is pure stdlib,
frozen, imports neither `ef_py` nor `python.rl`/`gym_envs`, wires nothing, and is
consumed by no runtime path this slice.

- `AGENT_ROLE_SCHEMA_FIELDS` -- the SCAL five-part AgentRole schema key order.
- `AUTHORITY_ROLES` -- nine declared roles (autopilot_controller, flight_lead,
  scripted_c2, cooperative_director, officer_in_tactical_command,
  ground_commander, naval_warfare_commander, formation_member,
  engagement_authority_holder), each now carrying the **five-part schema**
  (`role`, `authority_scope`, `information_state_source`, `decision_model_ref`,
  `action_interface`). Values are filled from census evidence; a slot is
  `"unspecified"` (with a note) only where the site is a command-node
  identity/delegation holder rather than a compiled decision-model-bearing agent
  (e.g. OTC, ground/naval commander, formation member, engagement holder). The
  four decision-model-bearing roles are: autopilot_controller
  (`platform_control` / `external_policy` / `PilotActionAssignment`), flight_lead
  (`mission_command` / `rule_based` / `CommandChainAssignment`), scripted_c2
  (`rule_based`; scope/interface `unspecified` because the C2 task-state layer has
  no compiled action-interface and folklore forbids authoring low-level mission
  commands), and cooperative_director (`formation_coordination` /
  `CommandChainAssignment`; decision model `unspecified`, runtime-face owned).
- `AUTHORITY_SCOPE_LEVELS` + `ACTION_INTERFACE_SCOPES` + `ACTION_INTERFACE_KINDS`
  + `SCOPE_FOLKLORE_RULES`.
- `COMMAND_RELATIONSHIPS` + `COORDINATION_MODES` + `NAVAL_WARFARE_ROLES` +
  `DELEGATION_CARRIERS`.
- `MERGE_POLICIES` + `SOURCE_PRIORITY_ORDER` + `ARBITRATION_MECHANISMS` +
  `ACTIVATION_GATES` + `FIRE_ELIGIBILITY_GATES` (R2: the air-combat fire mask, so
  the `gating` dimension's declared vocabulary covers A14) +
  `COMPILED_AUTHORIZATION_GATES` (the compiled fail-closed gates to converge onto).
- `DOCTRINE_FAMILY` -- a `DoctrineFamilyPlaceholder` naming the family and its
  components (task_templates, roe, authority_delegation, engagement_policy) plus
  the existing ROE pattern fields (`roe_state`, `wcs_state`, `shot_policy_state`,
  `engage_order_state`, `authorization_to_fire`, `engagement_authority_holder_id`,
  `engagement_authority_grantor_id`). Status: `vocabulary_placeholder` -- no
  mechanism this slice.
- `AUTHORITY_TOKEN_CATEGORIES` (token -> candidate category *set*; R2 adds the
  synonym tokens `commander_id` / `command_relationship` / `infer_command_relationship`
  and the loader delegate `_hierarchical_command_chain_active`, and widens
  `authorization_to_fire`'s candidates with `gating` to ground the A14 fire mask),
  `AUTHORITY_TOKEN_SURFACE` (token -> `code`/`prose` scan surface), and
  `CATEGORY_VOCABULARY` (per-category declared term sets).

## 6. Ratchet Gate Design

`tests/architecture/agency/test_authority_registry_gate.py` enforces five things,
following the I38 include-direction allowlist precedent (shrink-only, fail-loud):

1. **Registry <-> census consistency (candidate-set model).** Each census file's
   declared categories are *grounded* in (a subset of) and *cover* (touch every
   one of) its pinned tokens' candidate categories; every category surfaced by the
   census has a non-empty registered vocabulary; the AgentRole five-part schema and
   DoctrineFamily placeholder are declared as expected. (Repair: replaces the rigid
   token-to-fixed-category derivation that distorted A5/A7/A8/A9 classification.)
2. **Compiled authority mirror.** The gate parses `core_tasking_enums.h`,
   `naval_tasking_enums.h`, and `policy_contracts.h` (enum-member and
   `kAgentAuthorityScope*` extraction) and asserts the registry mirror reproduces
   `CommandRelationship`, `AuthorityScope`, `CoordinationMode`, `NavalWarfareRole`,
   and the action-interface scopes exactly. Any drift in either the header or the
   mirror fails the gate. (R1: new, covers P1-1. **R2**: the extractor now strips
   C++ comments *quote-awarely* from the whole header before the enum/scope regex
   runs, so a commented-out "ghost" member and a `}` inside a block comment can no
   longer deceive it -- string-literal scopes such as `kAgentAuthorityScope* = "..."`
   survive because the stripper preserves quoted content.)
3. **Fingerprint pin (token -> count, word-boundary).** Each pinned file must still
   reproduce its exact authority-token *counts*; a token added to or removed from a
   file -- including a *second* occurrence of an already-present token -- fails the
   gate until the census is updated. Tokens are matched by **word boundary**
   (`\bTOKEN\b`), so a token never double-counts inside a longer identifier
   (`commander_id` inside `ground_commander_id`). (R1: upgraded from a
   token-set-only fingerprint. Trade-off vs a content-hash + token-set fingerprint:
   token->count is precise about the "second authority check with the same token"
   blind spot and is stable under unrelated formatting/comment edits, whereas a
   content hash would churn on any whitespace change. **R2**: word-boundary matching
   both fixes the substring double-count and unblocks tokenizing the synonym family.)
4. **Ratchet against new scatter.** The scan of the maintained authority surface
   (directories scanned recursively, so a new file inside the owned surface cannot
   hide) must contain no file outside the census; a new unregistered
   authority-check site fails the gate, resolved by routing through the registry or
   adding an attributed census entry. The scanner strips comments, docstrings, and
   `import`/`__all__` plumbing for `code`-surface tokens and matches `prose`
   folklore only in docstrings/comments. (R2: the synonym tokens `commander_id` /
   `command_relationship` / `infer_command_relationship` and the loader delegate
   `_hierarchical_command_chain_active` close the derived-spelling blind spot.)
5. **Exact-category pins for key re-adjudicated sites (R2, NB).** Ordinary sites
   keep the candidate-set model (grounded + cover) to avoid over-rigidity, but the
   sites this review re-decided -- A5 (arbitration kept), A7/A9 (gating), A8
   (arbitration dropped), A14 (gating) -- pin their *exact* category set, so a
   silent re-flip (delete A5 arbitration, re-add A8 arbitration, move A7/A9 off
   gating, revert A14 to arbitration) fails the gate rather than passing under the
   subset freedom.

Negative self-tests prove the gate bites rather than passing vacuously:
`test_gate_flags_an_injected_unregistered_scatter` (an injected token file is
flagged), `test_scanner_counts_repeated_tokens_in_the_same_file` (a second
occurrence drifts the fingerprint), `test_scanner_ignores_docstring_and_comment_mentions`
(an innocent docstring mention is not a false positive),
`test_scanner_ignores_reexport_import_plumbing` (a pure re-export is not counted,
unifying the `__init__.py`/`ground_adapter.py` standard),
`test_scanner_matches_prose_folklore_only_in_docstrings` (folklore is still caught
on the prose surface), `test_enum_extractor_detects_registry_drift` (the
authority-mirror extractor recovers members and detects a dropped member), and the
round-2 additions: `test_enum_extractor_ignores_commented_ghost_members` (a
commented ghost member -- `//` or `/* */` -- is not resurrected),
`test_enum_extractor_survives_brace_in_block_comment` (a `}` inside a block comment
does not truncate the enum body), `test_comment_stripper_preserves_string_literal_comment_markers`
(quote-aware stripping keeps string-literal scopes intact),
`test_scanner_detects_synonym_only_file` (a file using only `commander_id` /
`command_relationship` is detected and, unregistered, flagged),
`test_scanner_word_boundary_excludes_substring` (`commander_id` does not match
inside `ground_commander_id`), `test_key_readjudicated_sites_pin_exact_categories`
(the key sites pin their exact category set), and
`test_pinned_key_site_check_bites_on_reflip` (a re-flip of A5/A8/A14/A7 breaks the
pin).

## 7. Deferred / Held

- **Call-site convergence.** The **mechanical vocabulary subset was converged at
  I53 (T9 slice 2)**: within the censused A1-A14 list the narrow adjudication
  stands at **0 of 14 convergeable** -- their scatter is compiled-`ef_py`-enum
  access (the registry is a mirror of that source of truth), schema-layer DTO
  field-name keys, and `if/else`/prose logic (full 14-site adjudication in §3.2,
  byte-equivalence proven). A full-maintained-surface hunt (I53 repair round)
  found **one true mechanical site outside the A-list** -- the
  `python/rl/runtime/agent_shim.py` merge-policy collection -- **converged this
  slice** (its `ALLOWED_MERGE_POLICIES` now references the registry's
  `MERGE_POLICIES`, drift-pinned by a unit test; §3.2). **Semantic convergence is
  still deferred**: routing A1-A14's behavior through the registry / the compiled
  `authorize_maintained_*` gates, the `DoctrineFamily` mechanism, and any
  compiled-side change all wait for a later T9 slice with domain-evidence review.
- **`DoctrineFamily` mechanism** (real ROE/engagement-policy behavior) is held;
  only the name and vocabulary are declared.
- **Runtime-face sites R1-R2** and the **policy-network face**
  (`python/rl/policy_algo/**`) are owned by other faces; T9 coordinates rather than
  modifies them, and they stay out of the scan roots (documented boundary).
- **Detection-vocabulary coverage boundary.** The scanner matches the registered
  token vocabulary by **word boundary** over the code/prose surface. Repair round 2
  promoted the previously-documented synonyms (`commander_id`,
  `command_relationship`, `infer_command_relationship`) and the loader-delegate
  spelling (`_hierarchical_command_chain_active`) to first-class tokens, so the
  former "documented, not tokenized" gap that the review rejected is now closed.
  What remains an honest boundary is the set of *compound* identifiers that embed a
  base token but are deliberately not separately tokenized because their file is
  already pinned via the base token: `leader_authorization_to_fire` (air),
  `infer_warfare_role_code` (naval), `command_relationship_default` /
  `_command_relationship_default` / `_support_command_relationship`, and the
  `_hierarchical_command_chain_active_impl` import alias. Word-boundary matching
  excludes each from the base token's count while keeping the file pinned.
- **`gym_envs/scenario_loader/mission_observation.py` (A14)** is write-excluded
  (I45); it is censused read-only and must not be modified by T9.

## 8. Repair-Round Change Summary

### Round 1

- **P1-1 vocabulary mirror.** Added `mission_command` to the action-interface
  scopes; declared all six `NavalWarfareRole` members; gave every `AuthorityRole`
  the five-part schema (`authority_scope`/`decision_model_ref`/`action_interface`,
  `"unspecified"` where honest). Added the compiled-authority mirror gate.
- **P1-2 re-adjudication.** A5 gained `arbitration` (leader-vs-mission fire
  precedence); A8 lost `arbitration` (pure state mirror); A7/A9 moved from
  `arbitration` to the new `gating` dimension (activation, not conflict
  resolution); A14 semantic completed to record the `fire_mask_open` policy gate.
- **P1-3 ratchet blind spots.** Fingerprint upgraded to token->count; scanner now
  ignores comments/docstrings and `import`/`__all__` re-export plumbing (unifying
  the re-export standard) while still catching prose folklore; scan roots broadened
  to whole directories; synonym coverage boundary documented.

### Round 2 (this round)

- **P1-1 extractor no longer comment-deceived.** The compiled-header enum/scope
  extractor now strips C++ comments (quote-aware: `//` + `/* */`, preserving
  string/char literals) from the whole header before the regex runs, and the enum
  body is delimited by its real closing brace (`{[^}]*}`). This fixes both the
  commented "ghost" member being resurrected and a `}` inside a block comment
  truncating the enum body. Two negative self-tests were added
  (`test_enum_extractor_ignores_commented_ghost_members`,
  `test_enum_extractor_survives_brace_in_block_comment`), plus a quote-awareness
  proof (`test_comment_stripper_preserves_string_literal_comment_markers`).
- **P1-2 synonym blind spot actually fixed.** The scanner now matches by **word
  boundary** and the synonym family is tokenized: `commander_id`,
  `command_relationship`, `infer_command_relationship`, and the loader-delegate
  spelling `_hierarchical_command_chain_active` (needed because word-boundary
  matching -- correctly -- no longer folds the gate name into the underscore-prefixed
  method, which would otherwise have dropped A7). A synonym-only file is now
  detected (`test_scanner_detects_synonym_only_file`) and word-boundary
  non-collision is proven (`test_scanner_word_boundary_excludes_substring`). All 14
  per-file fingerprints were regenerated with the new scanner (word boundary drops
  compound-identifier substrings such as `leader_authorization_to_fire`,
  `infer_warfare_role_code`, and the `air_combat_c2_roe_state_from_*` names; see §7).
- **P1-3 A14 re-adjudicated on source evidence.** `fire_mask_open`
  (`_air_combat_c2_roe_policy_fire_mask_open`) reads `authorization_to_fire` plus
  weapon/engage/shot state but **not** the `engagement_authority_holder_id` /
  `engagement_authority_grantor_id` (those are pure observation projection, lines
  405-406), so it decides *whether* the policy may fire (a gate) rather than *which
  producer wins* (arbitration). A14 moved `arbitration -> gating` (delegation /
  doctrine retained). Contrast A13, which *does* read the holder id to resolve
  who-may-fire and stays `arbitration`. The `gating` vocabulary gained
  `FIRE_ELIGIBILITY_GATES` so the dimension declares the fire mask.
- **NB candidate-set gate now pins the re-adjudicated conclusions.** The key
  re-adjudicated sites (A5, A7, A8, A9, A14) pin their *exact* category set, so a
  silent re-flip fails the gate (`test_key_readjudicated_sites_pin_exact_categories`,
  `test_pinned_key_site_check_bites_on_reflip`); ordinary sites keep the
  candidate-set model to avoid over-rigidity.

## Related

- [Unified Architecture Program](README.md) (T9 track definition)
- [Simulation System Architecture Design](../architecture/simulation_system_architecture_design.md)
  (Agency face; AgentRole schema; DoctrineFamily; merge/source-priority rule)
- [SCAL Conformance Census (2026-07-20)](scal_conformance_census_20260720.md)
  (sibling `reference`-kind register; structural precedent)
- `python/tasking_contracts/agency_registry.py` (registered vocabulary owner)
- `tests/architecture/agency/test_authority_registry_gate.py` and
  `tests/architecture/fixtures/agency_authority_census_20260721.json`
  (ratchet gate + fingerprint pin)
- `tests/architecture/policy_execution/*` (compiled WP12 AgentRole authority
  gates -- the convergence target)
