# Cross-Domain Scripted Agent System Plan

Language: English canonical; Chinese companion: not maintained (English-only
work surface).

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/architecture/work/issues/cross_domain_scripted_agent_system_plan.md`
Owner: `architecture/cross-domain-agency`
Last verified: `2026-09-24`
Content status: read-only repository analysis and proposed sequencing; no
implementation is authorized by this document.

Status: draft issue. This plan records the cross-domain scripted-agent
direction, the current evidence boundary, and the promotion gates required
before implementation work begins.

## Problem And Evidence

The repository currently has useful scripted behavior, but it is distributed
across domain-specific controllers, tasking helpers, opponent examples, and
learning-oriented adapters. The current shape supports pieces of scripted
execution rather than one independent, fully playable agent line.

Verified current facts:

- The maintained architecture models an Agency Graph containing agents, roles,
  authority scopes, decision models, action interfaces, and coordination
  relationships. It treats scripted, learned, and human-directed logic as
  policy-layer producers that must re-enter the simulation through facade-
  compatible contracts.
- `AgentRole` already has a five-part schema: `role`, `authority_scope`,
  `information_state_source`, `decision_model_ref`, and `action_interface`.
- `python/tasking_contracts/agency_registry.py` is a declarative registry and
  explicitly avoids wiring behavior. It currently includes autopilot, flight
  lead, scripted C2, cooperative director, naval, and ground command roles.
- `python/rl/runtime/agent_shim.py` currently carries observation provenance,
  maintained versus diagnostics-only status, action-intent metadata, and policy
  routing. These are reusable contract ideas, but the current location makes
  RL appear to own a capability that must also run without RL.
- Air has maintained scripted takeoff, stable-flight, landing, tasking, and
  red-opponent surfaces. Naval has bounded N4 tasking/contact/reporting and
  screen/station behavior. Ground currently proves identity and static
  task/status semantics, not movement, sensing, fires, effects, or damage.
- Scenario and world-batch paths already carry `is_agent`, active rosters,
  formation roles, and `policy_route`, but compatibility paths still retain a
  first-agent `agent_id` concept.
- The current cooperative visualization path explicitly does not support the
  scripted entry point, and the red scripted opponent uses privileged geometry
  and direct kernel access. Those are capability-boundary facts, not evidence
  of a complete playable scripted-agent system.

The project-wide target is therefore a cross-domain scripted-agent system that
is independently runnable and fully playable. Air is the first complete
vertical slice, not the architectural boundary.

## Product Definition

The scripted-agent line is a first-class decision and execution path. It must
run without RL dependencies and must be evaluated by simulation-semantic
outcomes, contract compliance, deterministic replay, and operator usability.

An agent is `playable` only when it can complete the supported lifecycle:

```text
spawn / ready
  -> receive task or command
  -> consume legal information
  -> form belief and decision
  -> emit intent or action
  -> obey authority, communication, resource, and domain constraints
  -> interact with other entities
  -> complete, fail, abort, recover, or become unavailable
  -> report, terminate, reset, and replay
```

`scripted`, `learned`, `human`, and `hybrid` are decision-model kinds behind
the same runtime contract. RL participation is an adapter choice, not the
ownership boundary of the scripted line.

## Proposed Architecture Direction

### 1. Common envelope, domain payload

Use a domain-neutral envelope with typed domain extensions. The common layer
should cover:

- identity, role, domain, capabilities, and roster membership;
- authority scope, command relationships, and arbitration;
- clock domain, update cadence, action hold, expiry, and effective time;
- observation provenance, snapshot/version identity, freshness, and confidence;
- communication/data-link availability and message ancestry;
- tasking, intent, action, report, event, termination, reset, and replay data.

Domain payloads remain owned by their domains:

- Air: flight control, navigation, formation, sensors, weapons, and ROE;
- Naval: maneuver, station/screen, maritime contacts, reports, and bounded
  engagement state;
- Ground: movement, terrain, sensing, fires, effects, logistics, and damage
  when those runtime owners are admitted.

The abstraction must prevent duplicate parallel contracts while preserving
domain semantics. A generic field is justified only when at least two domains
consume the same meaning or when the architecture standard already declares
it common.

### 2. Neutral agent lifecycle

The intended lifecycle is conceptually:

```text
AgentSpec -> reset(context) -> observe(packet) -> decide(dt)
          -> emit(intent/action) -> report(events) -> close/reset
```

The concrete placement of these contracts must be selected after a complete
consumer census. The first implementation must not create a second registry or
another private runtime beside the existing Agency/Facade/WorldBatch seams.

### 3. Role separation

The first role families are:

- platform/execution controller;
- unit or flight behavior controller;
- mission/C2 or tasking director;
- formation and multi-unit coordination director;
- tactical engagement controller;
- human override or supervisory controller.

The role determines authority and action interface. It does not determine
whether the decision model is scripted or learned.

### 4. Information boundary

Maintained scripted agents consume declared `ObservationPacket` and
`DecisionBelief` inputs. World Truth, raw ECS state, reward errors, hidden
scenario metadata, and privileged geometry are diagnostics-only unless a
specific maintained doctrine exception is documented and gated.

### 5. RL adapter boundary

RL adapters may:

- replace a scripted decision model;
- use a scripted agent as an opponent, teacher, fallback, residual baseline,
  or curriculum component;
- route through the same role, observation, intent, action, and report seams.

The scripted runtime, scenarios, tests, and playable acceptance must remain
usable when RL packages and checkpoints are absent.

## Proposed Work Packages

### WP0 — Authority and consumer census

Inventory every existing scripted controller, scripted director, opponent,
roster route, policy adapter, and playable entry point. Classify each as:

- maintained gameplay path;
- adapter projection;
- demo surface;
- diagnostics/oracle;
- draft or unresolved.

The census must include Python, C++, scenario JSON, CLI, visualization, tests,
and documentation references. It must record import direction and identify any
existing contract that would be duplicated by a new abstraction.

The initial read-only census is recorded in the [WP0 consumer census review](../../reviews/cross_domain_scripted_agent_system_consumer_census_20260924.md).
It confirms that `python/tasking_contracts` and the compiled policy contracts
are the reuse anchors, while the remaining `python.rl` surfaces are bounded
adapter entanglements rather than permission to create a parallel runtime.

### WP1 — Cross-domain contract placement

Select the neutral home for the common agent contracts and define their
versioning rules. Align with existing `AgentRole`, information-layer,
`ActionIntentPacket`, `CoordinationIntentPacket`, lifecycle, merge-policy, and
replay contracts. Keep domain fields in domain-owned extensions.

Promotion condition: a repository-wide consumer map, dependency direction, and
rollback plan exist before changing a maintained contract.

Initial WP1 slice: `python/tasking_contracts/scripted_registry.py` now provides
a dependency-terminal scripted model-factory registry and a minimal structural
`reset -> decide -> close` lifecycle. It does not duplicate observation,
action, or AgentRole DTOs, and it does not wire a runtime or import RL.

### WP2 — Independent scripted runtime and registry

Provide a runtime registry that can instantiate scripted, learned, human, and
hybrid decision models through the same role declaration. The scripted path
must have its own dependency-light entry point, reset semantics, clock policy,
action hold/expiry behavior, report stream, and deterministic seed handling.

The registry must route by scenario and active roster without making the legacy
first-agent compatibility path authoritative for new multi-agent scenarios.

### WP3 — Air complete playable slice

Compose the existing air execution pieces into one complete unit lifecycle:

```text
scramble -> departure -> transit/CAP -> task update -> RTB/recovery -> landing
```

The first slice should prove single-unit operation, command/report roundtrip,
authority handling, reset/replay, CLI execution, and visualization. It should
then extend to two or more air units using the existing active-roster and
world-batch facilities.

Initial implementation slice: `AirScriptedExecutionModel` composes the
maintained takeoff, stable-flight, and landing controllers behind the neutral
scripted lifecycle. `gym_envs/leader_env_parts/scripted_exec.py` remains an
environment adapter and no longer owns phase-controller composition.

### WP4 — Naval bounded playable slice

Use the existing N4 tasking, contact/reporting, screen/station, and recovery
surfaces. Do not claim full fleet combat. Acceptance should be limited to the
maintained naval capability profile and must preserve the Navy service-profile
and Naval-domain ownership split.

### WP5 — Ground admission and capability gate

Use the common agent lifecycle and static task/status contracts for ground
bootstrap. Do not label ground as fully playable until movement, terrain
interaction, sensing, fires, effects, damage, and observation export each have
an admitted runtime owner and evidence.

### WP6 — Multi-unit, communication, and cross-domain coordination

Add roster-level coordination, role-split routing, communication loss/latency,
delegation, task transfer, resource constraints, and deterministic arbitration.
Reuse the world-batch runtime and avoid a domain-specific two-unit runtime.

### WP7 — Optional RL adapters

Add RL integration only after the scripted runtime passes its own playable
acceptance. RL adapters must consume and emit the same neutral contracts and
must not become a hidden owner of scripted behavior.

### WP8 — Evidence and release gates

Add contract tests, lifecycle tests, authority/merge tests, information-leak
tests, deterministic replay checks, single-world/batch parity, scenario
capability manifests, CLI/viz smoke paths, and performance baselines.

## Capability And Acceptance Matrix

| Capability | Air | Naval | Ground | Required evidence |
| --- | --- | --- | --- | --- |
| Common reset/step/report lifecycle | first complete target | bounded reuse | schema-only until runtime admission | contract and replay tests |
| Single-unit playable loop | WP3 | WP4 bounded loop | not yet admitted | scenario + CLI + viz |
| Multi-unit roster routing | WP3/WP6 | later bounded extension | later | world-batch parity |
| Sensor/track-based decision | required for realistic combat | bounded contact products | held | provenance and negative tests |
| Full effects/damage authority | current air evidence scope must be stated per scenario | future/limited | held | domain owner gate |
| RL participation | optional adapter | optional adapter | optional adapter | no-RL run remains green |

Capability labels must be attached to scenarios and reports. Directory
presence, a successful action call, or a focused controller test is not enough
to promote a domain to `playable`.

## Non-goals For The First Promotion

- Do not introduce a new parallel simulation runtime.
- Do not move all domain semantics into a common mega-schema.
- Do not make RL training or self-play a prerequisite.
- Do not claim ground or naval capabilities beyond their maintained owner
  boundaries.
- Do not use World Truth in a maintained scripted pilot/tactical path without a
  documented, reviewed doctrine exception.
- Do not mix a new abstraction with unrelated physics, weapon, GPU, or frontend
  migrations.

## Risks And Open Decisions

1. The current registry is declarative while behavior remains scattered;
   convergence must avoid a second source of truth.
2. Several useful contracts currently live beside RL code. Their ownership and
   import direction require a consumer census before relocation or reuse.
3. `ScriptedC2TaskManager` has a declared maintained doctrine exception for its
   own-ship reads. The new system must preserve the documented exception or
   replace it with a facade-compatible source.
4. The current red scripted opponent is suitable for a demo/diagnostic role but
   cannot automatically receive a realistic playable label.
5. Ground runtime maturity is insufficient for a project-wide claim that every
   domain is already fully playable.
6. Common interfaces can become speculative if their second consumer is not
   named. Every new field or extension point must record its cross-domain
   consumer and acceptance test.

## Promotion Gate

This draft may be promoted to an active work package only after:

1. the repository owner confirms the product definition and domain capability
   labels;
2. WP0 produces a complete consumer and dependency census;
3. the common envelope/domain-payload split is reviewed by architecture,
   Joint, Air, Naval, Ground, and learning owners where their contracts are
   affected;
4. the first implementation slice is limited to one bounded vertical outcome;
5. contract versioning, migration, rollback, and evidence gates are written;
6. the plan has a named test matrix and no unreviewed parallel implementation;
7. implementation work receives an explicit owner decision.

Until those gates are satisfied, this file remains a draft proposal and does
not authorize code, scenario, contract, or runtime changes.

## Unattended Execution And Commit Protocol

The active execution goal supplies explicit owner authorization to progress
through this plan, while this document remains a draft governance record until
the promotion gate is satisfied. Each implementation iteration must preserve
the following protocol:

1. Select one bounded work package or one named contract slice.
2. Record the starting commit, affected owners, expected evidence, and any
   known residuals before changing files.
3. Keep the main worktree untouched and work only in the dedicated worktree.
4. When a command, dependency, environment, or contract blocks progress,
   record the command, observed failure, impact, attempted alternatives, and
   the next decision. Do not silently retry the same failing path.
5. Prefer, in order, a narrower local probe, an existing maintained helper, a
   read-only substitute, or a temporary proxy/skip that preserves the
   resumable state. A proxy result must be labeled as proxy evidence and must
   not be promoted to a final acceptance claim.
6. Continue independent work while a bounded blocker is recorded. Do not make
   the main process wait for an unrelated external service or expensive gate.
7. A blocker may be reported as a goal-level blocking condition only after the
   same condition has recurred for three consecutive goal turns and no
   meaningful alternative remains. Until then it remains a residual or a
   deferred work item.
8. End every iteration with a focused verification record and one thematic
   batch commit. Do not mix unrelated cleanup, generated artifacts, or
   speculative refactors into that commit.

The initial planning iteration had no blocker. Subsequent blockers and proxy
evidence are appended below until the first implementation package is promoted
to a dedicated owner-local evidence document.

## Current Execution Ledger

### 2026-09-24 — WP1 neutral registry slice

- Starting commit: `5560c900`.
- Change batch: neutral scripted model registry, lifecycle contract test, and
  this ledger update.
- Direct repository pytest was attempted with the maintained root `.venv`, but
  the worktree test bootstrap stopped before collection because no local
  `ef_py` build artifact exists in the worktree. The command and residual are
  retained as an environment boundary, not a code failure.
- Proxy verification used the same root `.venv` with `--noconftest`: the new
  registry test passed `4 passed`; an independent AST/import and lifecycle
  probe also passed.
- Proxy evidence is limited to the pure-Python registry slice. It does not
  establish C++ binding, full repository, or scenario acceptance.
- Residual: run the repository-managed architecture and runtime tests after a
  compatible local `ef_py` build artifact is available. This does not block
  independent WP1/WP3 design work.

### 2026-09-24 — WP3 air execution composition slice

- Starting commit: `d8b021ae`.
- Change batch: `AirScriptedExecutionModel`, air model registration, leader
  execution adapter delegation, and focused air lifecycle tests.
- Proxy verification: neutral registry plus air lifecycle tests passed `7
  passed` with `pytest --noconftest`; an isolated adapter probe passed for
  takeoff and phase transition to stable flight.
- Repository-managed compatibility collection remains deferred because its
  import path requires the missing local `ef_py` artifact. This is the same
  environment condition recorded above, not a second code blocker.
- Residual: scenario-level command/report roundtrip, CLI, visualization, and
  facade-backed acceptance are still open for the next slice.

### 2026-09-24 — WP3 visualization scripted-entry slice

- Starting commit: `59d6849f`.
- Affected owners: Air execution, visualization/runtime, and architecture
  contract tests.
- Expected evidence: visualization and task-evaluation scripted policy
  construction uses the neutral air controller modules, with the combined
  takeoff-to-landing mode resolved through the registry, without importing the
  RL control shells; fixed scripted modes retain their existing action shape
  and lifecycle behavior.
- Known residuals: the visualization process still imports learned-policy and
  compiled-runtime modules for its learned and environment paths; this slice
  only removes RL ownership from the scripted controller path. Cooperative
  scripted visualization and full scenario replay remain open.
- Focused proxy verification: the neutral registry, air lifecycle, and
  scripted-entrypoint contract tests passed `10 passed`; Python compilation and
  `git diff --check` also passed.
- A direct visualization import probe was attempted once with the maintained
  root `.venv`, but `runtime_bootstrap` stopped before import because this
  worktree has no local `ef_py` build artifact. The static and pure-Python
  proxies above are retained; no repeated import retry is warranted until the
  compatible artifact is available.

### 2026-09-24 — WP4 naval station baseline adapter slice

- Starting commit: `11996665`.
- Affected owners: Naval domain, cooperative runtime/evaluation, and
  architecture contract tests.
- Expected evidence: the maintained N4 station baseline obtains its neutral
  scripted action producer from the shared registry, while station geometry,
  contact/reporting, recovery, and reward ownership remain in the existing
  naval scenario runtime.
- Capability boundary: this is an `adapter` registration for the scoped
  station-hold baseline, not a claim of full naval combat or fleet-playable
  coverage.
- Focused proxy verification: the naval registry lifecycle/route tests plus
  the air registry and lifecycle tests passed `10 passed`; Python compilation
  and `git diff --check` passed. Full cooperative N4 execution remains subject
  to the already recorded missing local `ef_py` artifact and is not promoted
  from this proxy evidence.

### 2026-09-25 — WP2 role-aware registry resolution slice

- Starting commit: `88496f88`.
- Affected owners: cross-domain tasking contracts, Air execution, Naval
  bounded evaluation, and registry contract tests.
- Expected evidence: consumers can resolve a scripted model by domain and
  declared role through one registry API; explicit model IDs remain supported
  for deterministic scenario selection and fail closed on domain/role/status
  mismatch.
- Known residual: scenario manifests and active-roster routing do not yet
  select these registrations directly; that remains WP2/WP6 work.
- Focused proxy verification: registry, Air adapter, Naval adapter, and
  visualization contract tests passed `15 passed`; Python compilation and
  `git diff --check` passed. No compiled-runtime or scenario-playability claim
  is made from this pure-Python slice.

### 2026-09-25 — WP8 capability evidence matrix slice

- Starting commit: `84f75f23`.
- Affected owners: architecture evidence, Air, Naval, Ground, and scenario
  reporting.
- Expected evidence: one maintained review records the current capability
  labels, exact model registrations, accepted claims, deferred claims, and
  promotion gates for each domain.
- Known residual: the matrix is an evidence boundary and does not retrofit
  scenario JSON or promote any domain; a later scenario-manifest slice must
  attach machine-readable labels to maintained playable entry points.

### 2026-09-25 — WP8 scenario capability manifest slice

- Starting commit: `94a776c5`.
- Affected owners: scenario contracts, architecture evidence, Air, Naval, and
  Ground domain owners.
- Expected evidence: representative maintained scenarios carry additive
  `scripted_capability.v1` metadata whose label, model/role, lifecycle, and
  deferred claims match the maintained evidence matrix.
- Known residual: this slice covers representative fixtures only; it does not
  make the Air candidate playable, broaden Naval beyond N4, or admit Ground
  runtime capabilities.
- Focused proxy verification: the manifest and existing Ground realism tests
  passed `6 passed`; all three JSON files parsed successfully and referenced
  repository evidence files exist. No scenario compiler or compiled-runtime
  acceptance was claimed.

### 2026-09-25 — WP8 scripted capability manifest validator slice

- Starting commit: `537b9a86`.
- Affected owners: neutral tasking contracts, scenario metadata, and evidence
  tests.
- Expected evidence: a dependency-light parser validates the additive
  `scripted_capability.v1` shape and allowed label transitions without owning
  domain runtime behavior.
- Known residual: no maintained scenario loader/report path consumes the
  parsed object yet; integration remains a later evidence-tool slice.
- Focused proxy verification: capability-manifest parsing, representative
  scenario checks, registry checks, and the Naval adapter checks passed
  `13 passed`; Python compilation and `git diff --check` passed. The parser is
  not a runtime admission gate and does not alter domain behavior.
