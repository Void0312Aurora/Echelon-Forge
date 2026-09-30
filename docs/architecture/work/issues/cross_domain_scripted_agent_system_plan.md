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
- `python/tasking_contracts/common/agency_registry.py` is the canonical
  declarative registry; the former root path has been removed. It explicitly
  avoids wiring behavior. It currently includes autopilot, flight
  lead, scripted C2, cooperative director, naval, and ground command roles.
+ `python/tasking_contracts/common/agent_contracts.py` currently carries observation provenance,
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

### 6. Algorithm strategy substitution boundary

The common lifecycle registry selects complete decision models. It must not be
replaced by a second global registry for inner algorithms. Within a domain,
observation decoding, tactical planning, post-action assessment, and action
transport are separate responsibilities and must be independently replaceable
when a second maintained consumer exists.

For the current Air slice, the next composition seam is documented in the
[Air algorithm substitution research review](../../reviews/air_scripted_algorithm_substitution_research_20260926.md).
The required direction is:

```text
ObservationAdapter -> PlanningContext -> TacticalPlanner
                                      -> TacticalDecision
AssessmentAdapter -> AssessmentInput -> PostLaunchAssessor
TacticalDecision + FlightAction -> ActionAdapter -> domain action
```

The first implementation must preserve the current default planner and
assessor behavior, inject them through Air-owned protocols, and extract the
mission/contact and action-layout adapters from the engagement orchestrator.
No raw mission arrays, action indices, reward values, or World Truth may cross
the strategy seam. RL remains an optional consumer of the same neutral
lifecycle and is not permitted to own these scripted strategy contracts.

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

Initial WP1 slice used `python/tasking_contracts/common/scripted_registry.py` to
provide
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

Initial runtime slice: `python/tasking_contracts/common/decision_runtime.py` now
owns
the common scheduling envelope for registered scripted models. It provides
single-agent and active-roster lifecycle entry points, monotonic clock checks,
decision cadence, action hold/expiry, provenance context, deterministic replay
identity, and common runtime reports. It deliberately does not define a second
observation/action DTO or import RL/native simulation code.

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

### WP3-AIR-EXP — Air combat, electronic warfare, and joint playable expansion

The Air slice is intentionally deeper than the basic scramble-to-recovery
loop. These stages extend the same neutral lifecycle and existing world-batch
runtime; they do not create an Air-only agent runtime or make RL a prerequisite.

1. **Command/report closure.** Complete the `TaskOrder -> LeaderIntent ->
   PilotReport -> MissionCommand` roundtrip for a scripted Air unit, including
   task updates, report validity, authority checks, reset/replay, and a direct
   operator entry point.
2. **Tactical engagement.** Add a maintained scripted tactical role that
   consumes declared sensor/track products and emits intent/action through the
   existing Air combat event and C2/ROE surfaces. Weapon release, post-launch
   assessment, abort, and recovery must remain owned by their existing runtime
   contracts. The privileged red opponent remains a demo/diagnostic fixture
   unless a separate information-boundary review admits it as playable.
3. **Electronic warfare.** Add an EW decision role over the existing sensor,
   ESM, jamming, and data-link components. EMCON, detection confidence,
   communication loss/latency, and countermeasure/resource constraints belong in
   declared observations and domain payloads; no generic mega-schema may absorb
   Air EW semantics.
4. **Multi-aircraft coordination.** Route two or more active-roster members
   through `cooperative_world_batch_vec_env.py` and `cooperative_director.py`,
   preserving formation roles, authority/arbitration, communication state,
   deterministic reset/replay, and single-world/batch parity. Formation,
   wingman, support, and engagement roles are separate decision roles behind the
   same lifecycle.
5. **Joint operations.** Exercise Air C2 and coordination against the common
   command/authority envelope while Naval and Ground payloads remain owned by
   their domains. A joint scenario may report a cross-domain task graph, but it
   must not promote Naval or Ground beyond their admitted capability labels.
6. **Large-scale demonstration.** Build a scenario family and batch evaluation
   path for many aircraft only after the two-aircraft contract is closed. The
   demonstration must report roster routing, communication/resource constraints,
   deterministic replay identity, termination reasons, and performance; a large
   entity count alone is not playable evidence.

#### Air database input rule

When an Air scenario needs a type that is absent from the maintained database,
the unit builder may read the database worktree/branch
`codex/database-scaffold` (`C:\Users\30483\.codex\worktrees\database-enrichment\Echelon-Forge`)
as a provisional source. The builder must retain the source commit, dirty-state
marker, source path, schema/version, and evidence references in its manifest.
Uncommitted records are staging inputs only: they cannot silently become
maintained database content or final capability evidence. A later admission
batch must copy or regenerate the unit through the repository's database owner,
source ledger, and validation gates.

#### Air expansion promotion order

The required order is command/report closure, one tactical engagement role,
one EW role, two-aircraft coordination, joint tasking, and then the large-scale
demonstration. Each stage gets its own scenario, direct/proxy evidence
boundary, and thematic commit. RL adapters may consume a closed stage but may
not be used to claim that the independent scripted stage is playable.

### WP3-AIR-ALG — Air algorithm composition and substitution

This work package addresses the internal modularity gap after the first Air
tactical planner and post-launch assessor exist. It is a strategy-composition
package, not a new combat-runtime package.

1. Freeze typed Air planning, decision, assessment, and adapter DTOs around the
   current default behavior.
2. Add Air-owned planner/assessor/observation/action protocols and inject the
   current implementations by default.
3. Extract mission/contact decoding and 17/12 action-layout mapping from
   `AirScriptedEngagementModel`.
4. Prove independent replacement with deterministic no-fire and blocking
   test doubles, then run default-policy release/replay and 4v4 parity.
5. Add a versioned strategy profile only when a second maintained Air or
   cross-domain consumer is named; do not create a parallel global registry.

Promotion condition: default behavior is unchanged, each inner strategy can
be replaced independently, strategy modules remain RL/native independent, and
the test matrix proves transport/action/fire-gate ownership did not move.

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

### 2026-09-25 — WP3 standalone Air scripted CLI slice

- Starting commit: `5d6168a5`.
- Affected owners: Air execution, diagnostics CLI, and neutral tasking
  contracts.
- Expected evidence: `flight_trajectory_diagnostics --scripted` constructs and
  steps `air.execution.phase_scripted` directly, while learned-policy mode
  keeps its existing wrapper path.
- Known residual: the CLI still requires a compatible local `ef_py` artifact
  for scenario stepping; the existing import blocker remains proxy-only and is
  not retried in this iteration.
- Focused proxy verification: Air CLI source-boundary and neutral lifecycle
  tests, capability-manifest tests, and registry tests passed `15 passed`;
  Python compilation and `git diff --check` passed. A real scenario rollout was
  not claimed because the local binding artifact is still unavailable.

### 2026-09-25 — WP7 RL-wrapper consumer slice

- Starting commit: `1f8f89ee`.
- Affected owners: Air neutral execution, RL/world-batch adapter, and wrapper
  compatibility tests.
- Expected evidence: the combined `takeoff_cruise_landing` baseline in both
  wrapper consumers is instantiated through the neutral Air registry; residual
  blending, hold cadence, and fixed single-phase compatibility remain owned by
  the adapter.
- Known residual: the wrapper module remains an RL adapter and still carries
  residual/hold policy logic; it is not the owner of the neutral Air phase
  controller after this slice.
- Focused proxy verification: the wrapper neutral-route test, Air CLI test,
  Air lifecycle test, and registry tests passed `13 passed`; an isolated
  `MultiTimescaleActionController` probe produced a 17-element baseline action
  with active mode `takeoff`. Python compilation and `git diff --check` passed.

### 2026-09-25 — runtime binding build probe

- Starting commit: `75e34f4d`.
- Scope: isolated worktree build only; no tracked source change is planned in
  this probe.
- Expected evidence: configure and build a local `ef_py` artifact so the Air
  CLI and bounded Naval runtime gates can move from proxy evidence to direct
  execution evidence.
- Blocker protocol: if configure/build fails, retain the exact command and
  first failure, do not repeat the same command, and continue with the static
  evidence path. Generated build output remains untracked and is not part of a
  thematic commit.
- Result: CMake configure completed after supplying the installed Windows SDK
  resource compiler/manifest tool and SDK/MSVC library paths. The first build
  invocation exposed an incomplete MSVC include environment; the bounded
  follow-up under `VsDevCmd.bat` completed with exit code 0 and produced
  `build-scripted-agent/ef_py.cp312-win_amd64.pyd`.
- Direct verification: importing that local artifact succeeded. The standalone
  Air scripted CLI then ran the maintained combined scenario for five steps
  with zero randomization and wrote a plot plus summary; exit code was 0,
  `mode` was `scripted`, `steps` was `5`, and the final baseline mode was
  `takeoff`.
- Evidence boundary: this promotes the Air CLI slice from proxy-only to a
  bounded direct runtime smoke result. It does not establish a complete
  mission, reset/replay, multi-unit, cooperative, Naval, Ground, or full
  playable acceptance claim. The generated build directory and probe outputs
  remain untracked.

### 2026-09-25 — direct Naval N4 station report probe

- Starting commit: `1f551102`.
- Scope: the maintained Naval station adapter and its existing compiled
  scenario runtime; no fleet or weapon behavior was added.
- First probe used the representative contact-report scenario with the active
  station-hold training entry. The evaluator failed closed because that entry
  declares `scenarios/naval/ddg51_take1_screen_threat_roe_v1.json`; this exact
  scenario/config mismatch was recorded and not retried with the same pair.
- Alternative path: the evaluator was rerun with the scenario declared by the
  active entry. The eight-step direct report exited 0 with `passed: true`,
  finite rewards, all required station/contact/report reward terms present, and
  no forbidden weapon/damage terms.
- Evidence boundary: this closes the direct-report gate for the scoped N4
  adapter only. It does not promote Naval beyond `bounded_adapter`, and does
  not establish fleet combat, weapon employment, general maneuver, reset/replay,
  or full Naval playable coverage. Probe JSON remains under the ignored build
  directory.

### 2026-09-25 — Air same-process reset/replay probe

- Starting commit: `8ca6184b`.
- Scope: the compiled single-world Air runtime and the neutral
  `air.execution.phase_scripted` lifecycle, with zero randomization and a
  bounded four-step episode.
- Direct verification: one environment was reset twice with the same seed and
  the scripted model was rebuilt and closed for each run. Position, command,
  waypoint, and baseline-mode arrays were exactly equal; the two summaries
  matched and the probe exited 0.
- Evidence boundary: this closes only the bounded same-process reset/replay
  smoke gate. Full mission replay, command/report roundtrip, visualization,
  multi-unit roster parity, and complete playable acceptance remain open.

### 2026-09-25 — cooperative Air diagnostic boundary probe

- Starting commit: `575a69c6`.
- The first direct diagnostic used the representative standalone Air scenario;
  the cooperative runtime failed closed before stepping because that scenario
  has no controllable roster member. This was an input/entry mismatch, not a
  scripted-model failure.
- The alternative used the maintained cooperative scenario, which has a valid
  roster. A four-step cap then failed because the diagnostic contract requires
  the episode to terminate before returning a report. The same short-horizon
  command will not be retried.
- Proxy/direct alternatives retained: the standalone compiled Air CLI smoke and
  same-process reset/replay smoke already provide bounded direct execution;
  cooperative full-episode and multi-unit acceptance remain open until a
  bounded scenario/report contract can terminate or a full budget is authorized.

### 2026-09-25 — manifest-driven runtime routing slice

- Starting commit: `442b9742`.
- Change batch: a neutral `resolve_scripted_model_id` contract now validates
  domain, role, non-held label, and `reset_decide_close` lifecycle. The Air
  scripted CLI and Naval N4 evaluator use the declared scenario manifest when
  present and retain an explicit legacy-ID fallback only when metadata is
  absent. The active Naval threat/ROE scenario now carries the same additive
  manifest shape as the representative contact-report scenario.
- Focused proxy verification: manifest, Air entrypoint, Naval entrypoint, and
  registry tests passed `15 passed`; Python compilation and `git diff --check`
  passed.
- Direct verification: the manifest-bearing Air scenario completed the
  five-step scripted CLI smoke with exit 0; the manifest-bearing Naval N4
  scenario completed the eight-step report with `passed: true`, finite rewards,
  required terms present, and forbidden terms absent.
- Evidence boundary: manifest resolution is an admission/routing check, not a
  playable promotion. Ground remains held; Air full mission/cooperative
  acceptance and Naval full combat/fleet acceptance remain open.

### 2026-09-25 — visualization manifest route slice

- Starting commit: `ac5d90c6`.
- Change batch: the combined scripted Air visualization path now resolves the
  scenario manifest before passing `scripted_model_id` into the neutral wrapper
  consumer. The wrapper keeps the explicit legacy model ID only as its default
  when no override is supplied.
- Focused proxy verification: visualization route, wrapper route, manifest, and
  registry tests passed `17 passed`; Python compilation and `git diff --check`
  passed.
- Direct verification: importing the maintained viz session against the local
  binding and resolving the manifest-bearing Air scenario returned
  `air.execution.phase_scripted`.
- Evidence boundary: this establishes declaration parity between the Air CLI
  and viz wrapper route; it is not a full visualization process, render, replay,
  or complete playable acceptance result.

### 2026-09-25 — Air full single-world mission probe

- Starting commit: `f4a30e7c`.
- Direct command used the manifest-bearing Air scenario with the local
  compiled `ef_py`, the standalone neutral scripted model, and zero
  randomization without a short step cap.
- Result: the process exited 0 after `16416` steps, but the mission terminated
  with `off_runway_terminate`; the final command was landing (`command_code: 4`),
  `final_on_runway_geom` was `0.0`, and `mission_status[3]` was `-1.0`.
- Acceptance boundary: process success is not task success. Air remains
  `playable_candidate`; the failure is now a concrete landing-geometry blocker
  for complete mission/playable promotion. The generated plot and summary stay
  in the ignored build directory while the landing path is analyzed.

### 2026-09-25 — Air landing geometry correction and full mission success

- Starting commit: `c3221535`.
- Change batch: the neutral landing controller now accepts the declared runway
  length from the scenario adapter. Its localizer cross-track estimate adds
  that length to threshold DME because the compiled localizer cue is referenced
  from the far runway end. CLI, world-batch wrappers, and the leader adapter
  pass the same geometry input; no kernel or RL dependency was added.
- Focused proxy verification: Air lifecycle, wrapper, visualization, manifest,
  and registry tests passed `15 passed`; Python compilation and
  `git diff --check` passed.
- Direct verification: the same manifest-bearing Air scenario completed a full
  zero-randomization single-world run in `16638` steps with exit 0,
  `termination_reason: success_objective`, `mission_status: [4, 1, 1, 1]`,
  final runway geometry true, and final runway cross-track `6.45 m`.
- Evidence boundary: this closes the complete single-world Air mission gate
  for the tested seed and static-randomization condition. Full command/report
  roundtrip, full replay, visualization process/render, multi-unit parity, and
  promotion to final `playable` remain open.

### 2026-09-25 — Air randomized full mission probe

- Starting commit: `da0a3096`.
- Direct command repeated the complete Air scripted scenario without
  `--zero_randomization`, using seed 0 and the local compiled binding.
- Result: the run exited 0 after `16942` steps with
  `termination_reason: success_objective`, `mission_status: [4, 1, 1, 1]`,
  `world_yaw_deg: 197.5728614138369`, final runway geometry true, and final
  runway cross-track `0.916 m`.
- Evidence boundary: the Air single-world mission now has one static and one
  randomized direct success record. This still does not establish accepted
  seed coverage, full command/report roundtrip, full replay, visualization
  process/render, multi-unit parity, or final `playable` promotion.

### 2026-09-25 — Air full randomized reset/replay probe

- Starting commit: `256ecf2a`.
- Direct verification reused one compiled single-world environment and ran the
  complete manifest-bearing Air mission twice with seed 0 and randomization
  enabled. Position, altitude, command, and waypoint arrays were exactly equal;
  summary tuples were equal; both runs terminated with `success_objective` in
  `16942` steps.
- Evidence boundary: same-process full reset/replay is now directly evidenced
  for this seed and condition. Command/report closure, visualization
  process/render, multi-unit roster parity, broader accepted-seed coverage, and
  final `playable` promotion remain open.

### 2026-09-25 — Air command-chain contract probe

- Starting commit: `fe1355eb`.
- Direct command: the maintained `loader_command_chain` scenario contract was
  run against the local compiled binding with seed 7.
- Result: exit 0; `TaskOrder -> LeaderIntent -> PilotReport -> MissionCommand`
  initialized, each active object reached the kernel, and the intent and
  mission command codes remained aligned.
- Evidence boundary: this closes the command-chain initialization/kernel-sync
  contract. It is not yet a full scripted episode report roundtrip with
  command updates and final report ownership; that gate remains open.

### 2026-09-25 — Air expansion scope and database staging rule

- Starting commit: `9896bcc6`.
- Change batch: extend the plan and capability matrix with the Air
  command/report, tactical engagement, EW, multi-aircraft, joint-tasking, and
  large-scale demonstration stages; record the non-blocking concurrency rule
  and the provisional database worktree input boundary.
- Evidence basis: the current direct Air single-world and replay records,
  existing Air combat/C2/ROE/EW/cooperative runtime surfaces, and the separate
  `codex/database-scaffold` worktree inventory.
- Capability boundary: Air remains `playable_candidate`; the new stages are
  planned work, not promoted capabilities. The database worktree may provide
  staging inputs only, with source commit and dirty-state provenance retained.
- Known residual: command/report episode closure, tactical engagement, EW,
  multi-aircraft parity, joint tasking, and large-scale demonstration still
  require dedicated implementation and evidence batches. This planning batch
  does not change runtime behavior or database admission.

### 2026-09-25 — Air scripted C2 command/report runtime probe

- Starting commit: `f1b1c56a`.
- Direct command: `LeaderTrainingEnv` with `execution_backend=scripted`, local
  `build-scripted-agent/ef_py`, seed `7`, and
  `scenarios/combined/takeoff_to_landing_c2_task_only_demo_v1.json`.
- First probe residual: the retained JSON summary attempted to serialize a
  NumPy `float32` mission-status value and failed before emitting a report. The
  probe was corrected by converting the four mission-status fields to Python
  floats; the same failing serialization path was not retried unchanged.
- Direct result after the correction: `104` leader decision windows ran;
  report types `1` and `20` were observed; `report_valid` was true for all
  windows; `TASK_RECOVER_LAND` was entered at window `18` with
  `recovery_window_open` and `rtb_report`; the terminal result was
  `off_runway_terminate` with mission success flag `-1`.
- Evidence boundary: command/report objects are being produced and synced,
  but this scenario does not yet provide a successful scripted C2 episode
  closure. The residual is a concrete task-only route/landing geometry or
  entry-contract mismatch, not evidence to promote Air beyond
  `playable_candidate`.
- Continuation choice: retain the exact residual for a later C2 geometry/entry
  batch and proceed independently with the planned tactical engagement and EW
  contract work. No unrelated domain task is blocked by this residual.

### 2026-09-25 — Air tactical engagement scripted adapter slice

- Starting commit: `cb830cc2`.
- Change batch: add `AirScriptedEngagementModel` and the aggregate Air scripted
  model registry. The model composes the neutral phase-flight controller and
  derives radar, TMS, master-arm, and one-shot fire requests only from the
  declared `air_combat_c2_roe_v2` mission observation fields.
- Boundary: the model has no RL import, kernel access, World Truth read, or
  privileged target geometry. The existing environment fire gate remains the
  authority for release acceptance. The tactical registration is deliberately
  `adapter`, not `playable`.
- Focused verification: the neutral Air execution tests and tactical adapter
  tests passed `8 passed` with `pytest --noconftest`; the model emits a finite
  17-element full Air action, produces one fire pulse, suppresses fire during
  `pending_assessment`, and fails closed on a non-C2/ROE mission shape.
- Known residual: no maintained Air combat scenario or operator CLI consumes
  this adapter yet; runtime weapon employment, post-launch assessment, EW, and
  full engagement evidence remain open.

### 2026-09-25 — Cooperative Air roster trace probe

- Starting commit: `89ed1faf`.
- Direct command: `diagnose_cooperative_trajectory.py --scripted` on
  `cooperative_takeoff_to_cruise_landing_continuous_eval_v1.json`, seed `0`,
  with the local compiled binding and a `3000`-world-step trace budget.
- Direct result: the existing cooperative runtime routed two active roster
  members, `ElementLead:Lead` and `Wingman:Wing`, through the shared execution
  route. Lead was cleared/rolling/airborne at steps `0/128/292`; Wing was
  hold-short/cleared/rolling/airborne at `0/248/547`. Both slots remained
  represented in the trace and the command/clearance segments were distinct.
- Evidence boundary: the trace ended with `trace_cutoff` before waypoint
  capture; `world_success=false`. This closes only a bounded roster-routing
  and cooperative takeoff trace, not multi-unit mission completion, formation
  maintenance, single-world/batch parity, or full playable promotion.
- Continuation choice: retain this as the first direct multi-aircraft evidence
  record and move to the EW entry-surface review; no cooperative runtime rewrite
  is justified by this bounded trace.

### 2026-09-25 — EW entry-surface review

- Starting commit: `89ed1faf`.
- Read-only evidence: the database EW suite, native EW components, RWR
  observation export, countermeasure command bridge, and maintained Air action
  mappings were inspected. RWR data and chaff/flare native consumers exist;
  the maintained `full` and `air_combat_hybrid_v1` action vectors currently set
  `program_chaff`/`program_flare` false, and no jammer activation field or
  command system is exposed in the reviewed path.
- Change batch: add
  `docs/domains/air/reviews/scripted_ew_entry_surface_20260925.md` with the
  exact ownership boundary and closure slices. No runtime or database files
  were changed.
- Capability boundary: the Air EW line is `entry_surface_incomplete`; a
  scripted EW model must not be promoted until a versioned action extension,
  native jammer owner, direct acceptance scenario, and replay/multi-aircraft
  evidence exist.
- Continuation choice: keep EW interface work independent of the C2 landing
  residual and continue with the next Air coordination/joint-tasking design
  slice. No unrelated domain task is blocked.

### 2026-09-25 — Joint scripted tasking entry-surface review

- Starting commit: `b9746db4`.
- Read-only evidence: the maintained Joint command/modeling and command-link
  standards, compiled `AgentRole`/intent contracts and bindings, Air/Navy/Army
  tasking projection tests, and the cooperative roster director were inspected.
- Focused verification: with `CMO_BUILD_DIR=build-scripted-agent`,
  `tests/leader/test_tasking_profile_contracts.py`,
  `tests/leader/test_command_field_projection_contracts.py`, and
  `tests/world_batch/test_world_batch_runtime_surface.py` passed `48` tests.
- Capability boundary: common DTOs, authority checks, and roster transport are
  contract-ready, but no maintained cross-domain scenario, independent joint
  scripted producer, joint CLI, or joint visualization route exists. Joint
  remains an open expansion stage and does not promote Naval or Ground.
- Change batch: add
  `docs/domains/joint/reviews/scripted_joint_tasking_entry_surface_20260925.md`
  with the owner boundary and six closure slices. No runtime or domain payload
  files were changed.
- Continuation choice: implement the smallest task-graph/coordination producer
  only after an admitted second-domain execution consumer is selected; keep
  this work independent of the Air C2 landing residual and EW action-surface
  gap. No unrelated domain task is blocked.

### 2026-09-25 — Air tactical adapter hybrid-entry slice

- Starting commit: `c8711fd2`.
- Change batch: extend `AirScriptedEngagementModel` to map both the maintained
  17-element `full` action and the existing 12-element
  `air_combat_hybrid_v1` action. The model still reads only the declared
  `air_combat_c2_roe_v2` mission fields; no RL, kernel, or World Truth import
  was added.
- Focused verification: Air execution and engagement tests passed `9` tests;
  Python compilation and `git diff --check` passed.
- Direct command: a single-world Stage 1 BVR C2/ROE scenario was run with
  `AirScriptedEngagementModel(action_dim=12)` and the compiled runtime for
  `2400` steps.
- Direct result: the maintained hybrid transport reported
  `fire_once_requested=true`, `fire_once_accepted=true`, and
  `release_executed=true` for one scripted shot. The episode ended at the
  `combat_timeout` trace boundary with mission success flag `0`; this is a
  real scenario-consumption and native-release record, not complete engagement
  or playable evidence.
- Capability boundary: tactical engagement remains `adapter`; post-launch
  assessment, terminal objective closure, broader seed/replay coverage, and
  visualization/operator admission remain open.
- Continuation choice: keep the hybrid mapping as the maintained entry path,
  then investigate post-launch/terminal assessment independently of the Air C2
  landing residual and EW action-surface gap. No unrelated domain task is
  blocked.

### 2026-09-25 — Air post-launch assessment alternative probe

- Starting commit: `de418726`.
- Alternative command: the same Stage 1 C2/ROE hybrid scenario was run through
  `WorldBatchVecEnv` with the existing post-launch assessment path enabled for
  `240` steps, then repeated with an `800`-step assessment budget.
- Direct result: both runs accepted the scripted release at step `282`; the
  assessment path then terminated at its own budget with
  `post_launch_assessment_timeout`, mission status `[1, 0, 0, 0]`, and no
  objective success. Increasing the budget from `240` to `800` did not change
  the terminal class.
- Blocker record: the residual is not explained by a short assessment window;
  the target/weapon consequence or terminal-objective path remains unresolved.
  The existing assessment adapter is retained as an alternative and no
  unreviewed direct world-state write is introduced.
- Continuation choice: preserve the release evidence as a bounded tactical
  adapter gate, defer tactical `playable` promotion, and continue with the
  independent EW and roster/interface lines. No unrelated domain task is
  blocked.

### 2026-09-25 — Air scripted EW observation probe

- Starting commit: `f8c2d40a`.
- Direct command: the Stage 3 limited-weapons Air scenario was run with the
  maintained `AirScriptedExecutionModel`, compiled runtime, `full` action
  mode, `mission_obs_mode=basic`, seed `0`, and a `2400`-step trace budget.
- Direct result: a non-zero RWR observation row first appeared at step `441`
  and remained present through step `2121`; the trace ended still running with
  mission status `[1, 0, 0, 0]`. No countermeasure action was available in the
  maintained action mapping, and no EW terminal objective was claimed.
- Capability boundary: this is direct RWR observation evidence only. It does
  not close launch-warning interpretation, chaff/flare transport, jammer
  activation, resource/cooldown state, or EW replay/multi-aircraft gates.
- Continuation choice: retain the observation evidence, keep EW at
  `entry_surface_incomplete`, and wait for a versioned action extension plus a
  native command owner before adding a scripted EW producer. No unrelated
  domain task is blocked.

### 2026-09-25 — Neutral scripted runtime scheduler slice

- Starting commit: `b90d7209`.
- Change batch: add the dependency-terminal
  `DecisionRuntimeAgent`/`DecisionRuntimeRoster` scheduler in
  `python/tasking_contracts/common/decision_runtime.py`. It reuses the existing
  `ScriptedDecisionModel` and `ScriptedModelRegistry`; it does not add a second
  observation/action DTO or import RL, gym, NumPy, native bindings, or a world
  runtime.
- Runtime semantics: explicit reset/close/terminate lifecycle, monotonic clock,
  decision cadence, action hold and expiry, per-agent observation-version and
  communication/authority provenance context, deterministic episode seed and
  replay identity, and sorted active-roster routing. Missing active observations
  and duplicate agent IDs fail closed.
- Focused verification: the new runtime tests plus tasking-contract boundary
  and ScenarioLoader runtime-contract tests passed `28` tests with
  `CMO_BUILD_DIR=build-scripted-agent`; Python compilation and
  `git diff --check` passed.
- Capability boundary: this closes the neutral scheduling substrate only. It
  does not claim a domain scenario is playable, does not replace the existing
  cooperative world-batch runtime, and does not bypass domain action/report
  owners.
- Continuation choice: route the next Air operator/evaluation entry through
  this scheduler and record the adapter boundary before extending EW or joint
  payloads. No unrelated domain task is blocked.

### 2026-09-25 — Air CLI neutral-runtime routing slice

- Starting commit: `b5d79e0d`.
- Change batch: route the standalone Air takeoff-to-landing diagnostic CLI
  through `DecisionRuntimeAgent` while preserving the learned-policy wrapper
  path. The CLI now reports runtime decision/hold counts and the deterministic
  replay identity for scripted episodes.
- Focused verification: Air CLI contract tests and neutral runtime tests
  passed `7 passed`; Python compilation and `git diff --check` passed.
- Direct verification: with `CMO_BUILD_DIR=build-scripted-agent`, the
  manifest-bearing Air scenario was run through the CLI for `80` scripted
  steps with zero randomization. The process exited `0`, wrote the plot and
  summary, produced `80` runtime decisions and `0` holds, and reported
  `581:air.execution.phase_scripted:seed=0:reset=1` as the runtime identity.
- Evidence boundary: this proves operator-entry integration with the neutral
  scheduler for a bounded Air rollout. It does not add action/report closure,
  multi-aircraft parity, EW command ownership, or a new playable promotion.
- Continuation choice: reuse the same runtime envelope for the maintained
  Naval scripted evaluation entry, then add roster-level cross-domain routing
  evidence. The Air landing/C2, EW, and tactical residuals remain independent
  work items and do not block that continuation.

### 2026-09-25 — Naval evaluator neutral-runtime routing slice

- Starting commit: `710048b8`.
- Change batch: route the maintained Naval N4 station evaluator through
  `DecisionRuntimeAgent` while preserving the existing station command,
  contact/report, reward, and compatibility transport owners. The evaluator
  now reports runtime decision/hold counts and replay identity alongside its
  existing gate payload.
- Focused verification: Naval entrypoint, Naval adapter, and neutral runtime
  tests passed `9 passed`; the direct evaluator contract test passed `1
  passed`; Python compilation and `git diff --check` passed.
- Direct verification: with `CMO_BUILD_DIR=build-scripted-agent`, the active
  manifest-bearing Naval N4 scenario ran for `8` steps and exited `0` with
  `passed: true`, finite reward, all required station/contact/report terms,
  no forbidden weapon/damage terms, `8` runtime decisions, `0` holds, and
  identity `Blue_Screen_DDG51:naval.station.screen_hold:seed=20260525:reset=1`.
- Evidence boundary: this proves cross-domain operator/evaluator reuse of the
  neutral scheduler for the scoped Naval station adapter. It does not promote
  Naval beyond `bounded_adapter`, and it does not establish fleet combat,
  weapons, general maneuver, reset/replay, or full Naval playable coverage.
- Continuation choice: use the Air and Naval runtime identities as the basis
  for a roster-level routing probe, while keeping Air C2/landing, EW, tactical
  assessment, and Joint task-graph residuals independent.

### 2026-09-25 — Cross-domain scripted roster contract slice

- Starting commit: `ed278d05`.
- Change batch: add a contract test that constructs the maintained Air
  execution model and the bounded Naval station model under one
  `DecisionRuntimeRoster`. The test uses the real domain registries and keeps
  each domain's action payload and role/authority metadata behind the common
  runtime envelope.
- Focused verification: cross-domain roster, neutral runtime, Air lifecycle,
  and Naval lifecycle tests passed `13 passed`; Python compilation and
  `git diff --check` passed.
- Direct result: deterministic sorted routing returned `air:lead` and
  `naval:screen`, both models reset with seed `7`, both made a first decision,
  both held that action at `0.1 s`, and their reports preserved `air` versus
  `naval` domain identity with action shapes `(17,)` versus `(3,)`.
- Evidence boundary: this closes a pure-Python cross-domain scheduling and
  provenance contract. It does not constitute a joint simulation episode,
  command arbitration, communication loss, cross-domain effects, or Naval/
  Ground playable promotion.
- Continuation choice: select the smallest maintained joint task-graph
  producer/consumer slice next, without coupling it to the Air C2 landing,
  EW action-surface, or tactical assessment residuals.

### 2026-09-25 — Joint task-graph producer contract slice

- Starting commit: `8dcb8af1`.
- Change batch: add the dependency-terminal
  `ScriptedJointTaskGraph`/`ScriptedJointCoordinationModel` contract. The
  versioned graph declares node identity, domain, role, service profile,
  task-group, coordination mode, authority scope, payload reference, and
  authority/support edges. The producer emits only a graph-scoped
  `ScriptedJointCoordinationIntent`; it does not read geometry or write any
  domain component.
- Focused verification: joint graph/producer, cross-domain roster, neutral
  runtime, and tasking-boundary tests passed `20 passed`; Python compilation
  and `git diff --check` passed.
- Direct result: the producer ran through `DecisionRuntimeAgent` with seed
  `11`, emitted the declared Air and Naval target node IDs, preserved the
  graph/task-group/coordination metadata, and retained communication,
  authority, clock, and observation-version provenance.
- Evidence boundary: this is a producer and declaration contract only. It is
  not a compiled `CoordinationIntentPacket` roundtrip, command-link delivery,
  domain execution episode, replay acceptance, or Joint/Air/Naval playable
  promotion.
- Continuation choice: keep the producer at `adapter` status and add a
  read-only consumer projection or compiled DTO bridge only after the exact
  command-link owner and scenario entry are selected. Existing Air, Naval,
  EW, and landing residuals remain independent.

### 2026-09-25 — Joint coordination DTO projection slice

- Starting commit: `9e1dce6e`.
- Change batch: add a dependency-terminal projection helper that accepts the
  compiled binding module explicitly and maps a neutral joint coordination
  intent to `CoordinationIntentPacket` plus `ProducedIntentRef` task-node
  references. The helper reports every common field absent from the current
  compiled DTO instead of encoding those fields into unrelated payload slots.
- Focused verification: joint producer/projection, cross-domain roster,
  neutral runtime, and tasking-boundary tests passed `16 passed`; Python
  compilation and `git diff --check` passed.
- First direct command failed immediately because the inline probe imported
  `ef_py` before repository bootstrap and the module was not on `sys.path`.
  Alternative path used the maintained `ensure_repo_imports()` bootstrap with
  `CMO_BUILD_DIR=build-scripted-agent`; the compiled projection then produced
  source `joint:director`, graph roster
  `joint.air_naval_screen_demo_v1`, Air/Naval refs, and
  `authorize_maintained_coordination_intent(...).authorized == true`.
- Evidence boundary: the DTO projection is an adapter proof, not command-link
  delivery or a joint episode. The explicit residual fields are
  `task_group_id`, `coordination_mode`, `clock_s`, `observation_version`,
  `communication_state`, and `authority_scope`; Joint remains
  `bounded_adapter` and has no playable promotion.
- Continuation choice: retain the compiled projection as a read-only bridge
  and next select a maintained scenario/command-link consumer. Do not infer
  execution closure from DTO authorization alone; Air C2/landing, EW, and
  tactical assessment remain parallel residuals.

### 2026-09-25 — Air scripted EW producer contract slice

- Starting commit: `588ea7bd`.
- Change batch: add `AirScriptedEWModel` and register
  `air.ew.rwr_response_scripted` in the aggregate Air registry as an
  `adapter`. The model interprets only declared RWR rows (bearing, signal,
  lock, launch warning) and emits a typed EW intent with a response-doctrine
  decision, while explicitly reporting `native_action_owner_required`.
- Focused verification: EW, Air tactical, Air execution, neutral runtime, and
  tasking-boundary tests passed `28 passed`; Python compilation and
  `git diff --check` passed.
- Direct result: the producer detected a declared launch warning and lock,
  selected `request_chaff_and_flare` only when the explicit
  `countermeasure_ready` doctrine was supplied, and otherwise held or deferred
  without reading World Truth or writing native EW components.
- Evidence boundary: no maintained action mode consumes this intent; no
  chaff/flare release, jammer transition, resource decrement, or EW terminal
  objective was claimed. Air remains `playable_candidate`, and EW remains an
  incomplete entry surface pending a versioned action extension and native
  command owner.
- Continuation choice: keep this producer independent of the C2/landing and
  tactical post-launch residuals, then design the smallest Air-owned
  countermeasure action extension with negative and replay tests before any
  EW runtime promotion.

### 2026-09-25 — Air EW versioned action-extension slice

- Starting commit: `fb211da2`.
- Change batch: add the opt-in `air_ew_hybrid_v1` action shape with two
  explicit tail fields for `program_chaff` and `program_flare`; map the fields
  to `PilotAction` without changing the existing 17-element `full` or
  12-element `air_combat_hybrid_v1` layouts. Add a scripted EW action model
  that composes the neutral Air flight controller and emits the extension.
- Focused verification: EW transport/model, existing Air hybrid action, C2/ROE
  observation, and tasking-boundary tests passed `25 passed`; Python
  compilation and `git diff --check` passed.
- Direct verification: the local compiled `WorldBatchVecEnv` accepted
  `air_ew_hybrid_v1` with action dimension `14`; one zero-randomization Stage 3
  step carried transport tail `[1.0, 1.0]` for chaff/flare and returned a
  finite reward without termination. A 79-step scripted run also stepped the
  new mode without runtime errors, but no RWR launch warning occurred in that
  short horizon.
- Evidence boundary: the extension is deliberately outside the canonical
  `python.env_config.ACTION_MODES` list, has no maintained scenario/config or
  CLI admission, and has no native countermeasure inventory decrement/report
  proof. This is transport and model evidence only; EW remains
  `entry_surface_incomplete`.
- Continuation choice: add the smallest direct scenario/report gate that can
  observe native chaff/flare acceptance and inventory/resource change, or log
  the first concrete scenario mismatch and use a bounded proxy. Jammer
  activation remains a separate owner decision.

### 2026-09-25 — Air EW action-mode negative runtime probe

- Starting commit: `27be956c`.
- Direct command: the local compiled `WorldBatchVecEnv` ran the Stage 3
  limited-weapons scenario for `2400` steps with
  `air_ew_hybrid_v1`, `AirScriptedEWActionModel`, seed `0`, and the explicit
  `countermeasure_ready` doctrine.
- Direct result: the process remained finite and running with mission status
  `[1, 0, 0, 0]`, but produced no RWR launch-warning rows and therefore no
  natural chaff/flare requests. A separate one-step forced action probe did
  carry transport tail `[1.0, 1.0]` through the environment with finite
  reward, but exposed no maintained inventory/report state.
- Residual: this entry point is not a valid EW acceptance scenario for the
  new action mode under the tested seed/horizon. The exact 2400-step command
  will not be repeated unchanged; a future gate must choose a scenario or
  threat schedule that emits a declared launch warning and exposes a native
  resource/report owner.
- Evidence boundary: the result is a negative scenario-selection/runtime
  finding, not an EW failure diagnosis and not playable evidence. EW remains
  `entry_surface_incomplete`; jammer ownership and replay/multi-aircraft gates
  remain open.

### 2026-09-25 — Air EW optional-binding test isolation slice

- Starting commit: `ffb68380`.
- Change batch: keep the pure EW producer/action-model tests runnable without a
  local compiled `ef_py`; the two transport-shape assertions now skip only
  when the binding action surface is unavailable.
- Focused verification: without `CMO_BUILD_DIR`, the EW and joint contract
  tests passed `8 passed, 1 skipped`; with
  `CMO_BUILD_DIR=build-scripted-agent`, the full EW file passed `5 passed`.
  Python compilation and `git diff --check` passed.
- Evidence boundary: this is test-environment isolation only. It does not
  expand EW runtime ownership or change the native acceptance residual.

### 2026-09-25 — Air EW cooperative action-mode routing probe

- Starting commit: `b32881d1`.
- First probe used the standalone Stage 3 combat scenario with
  `CooperativeWorldBatchVecEnv`; it failed closed because the scenario has no
  controllable cooperative roster member. This exact scenario/entry pairing
  will not be retried.
- Second probe used the maintained cooperative Air scenario but supplied one
  action row for a two-slot world; the cooperative runtime raised the expected
  slot-shape `IndexError`. The malformed action shape will not be retried.
- Alternative result: the same cooperative scenario with an action array
  sized to `slots_per_world=2` accepted `air_ew_hybrid_v1` for one compiled
  step, returned finite rewards, and remained running.
- Evidence boundary: this proves only action-mode transport through the
  cooperative slot route. It does not prove EW observation delivery,
  countermeasure state change, inventory/report closure, or multi-aircraft EW
  behavior; those gates remain open.

### 2026-09-25 — Leader Air execution neutral-runtime integration slice

- Starting commit: `8a0eb0ec`.
- Change batch: route the Leader environment's maintained Air scripted
  execution entry through `DecisionRuntimeAgent`. The adapter now carries the
  common lifecycle, clock, decision index, communication/authority metadata,
  seed/replay identity, and runtime report while leaving the Air observation
  and action payloads domain-owned. Leader info exposes the report as
  `leader_scripted_runtime`; frozen-model and existing action-repeat paths
  remain unchanged.
- Focused verification: Air execution, cross-domain roster, and Air CLI tests
  passed `8 passed`; Python compilation and `git diff --check` passed. A direct
  compiled Leader step also returned a finite running result with runtime
  identity `581:air.execution.phase_scripted:seed=7:reset=1`, 20 low-level
  decisions, and observation version `scramble`.
- Direct C2 follow-up: the fasttrain C2 scenario still traversed
  `TASK_SCRAMBLE -> TASK_CAP -> TASK_RTB -> TASK_RECOVER_LAND` under the
  scripted path, but the tested command schedule remained at waypoint index 2
  and did not reach terminal landing within the 320-window probe. This is a
  remaining command/route/landing closure failure; it is not promoted to
  playable evidence and the exact long probe will not be repeated unchanged.
- Evidence boundary: this closes the Leader-to-neutral-runtime adapter and
  provenance surface only. It does not close the Air C2 terminal episode,
  native EW acceptance, multi-aircraft parity, or Joint execution.
- Continuation choice: select a maintained C2 route/landing entry that can
  expose the route-to-landing command transition, or use a bounded proxy with
  a recorded blocker; keep EW and Joint residuals independent.

### 2026-09-25 — Air multi-role roster contract slice

- Starting commit: `50266dca`.
- Change batch: extend the neutral roster contract with three Air roles in
  one deterministic route: maintained phase execution, C2/ROE tactical
  engagement, and versioned EW action. Each role retains its own observation
  and action payload, role id, authority scope, and registry model id while
  sharing only the runtime lifecycle envelope.
- Focused verification: cross-domain roster, Air execution, and EW tests
  passed `11 passed, 1 skipped` without requiring a native transport binding;
  Python compilation and `git diff --check` passed. The pure route produced a
  17-element tactical action with a one-shot fire pulse and a 14-element EW
  action with chaff/flare tails, and both held at `0.1 s` under the common
  cadence.
- Evidence boundary: this is a role-routing and payload-isolation contract.
  It does not authorize weapon release, decrement EW inventory, prove native
  jammer/countermeasure state, or provide multi-aircraft simulation parity.
  Tactical and EW registrations remain `adapter`.
- Continuation choice: use the roster slice as the Air multi-role seam while
  the next runtime batch selects a native engagement or EW acceptance owner;
  do not infer playable promotion from pure model outputs.

### 2026-09-25 — Air database staging inventory probe

- Source boundary: read-only inspection of the separate
  `codex/database-scaffold` worktree at commit `505318b9`; its worktree was
  clean and no files were copied or modified from this task.
- Direct result: the runtime-facing database layer currently exposes staged
  aircraft unit records for `F-16C_Block50`, `Su-35S_Flanker-E`,
  `MQ-9_Reaper`, `E-3_Sentry_AWACS`, and `MH-60R_MVP`. The research catalog
  also contains a draft AH-1Z leaf (`eq-us-air-ah1z`) with explicit
  `parameter_complete` research status but no runtime-authority claim.
- Admission rule: the database worktree can supply candidate platform/module
  inputs for the Air large-scale demonstration only after a source commit,
  dirty-state snapshot, schema validation, and scenario-loader admission are
  recorded. A research leaf alone cannot promote an Air unit or scripted role.
- Evidence boundary: this is a candidate inventory and provenance record;
  no new unit was admitted, no scenario was changed, and no capability label
  moved. Large-scale composition remains open alongside multi-aircraft
  mission parity and tactical/EW terminal closure.
- Continuation choice: use the existing runtime-facing F-16/Su-35/MQ-9/E-3
  records for a future bounded roster scenario first; treat AH-1Z and other
  research leaves as staged inputs pending loader compatibility evidence.

### 2026-09-25 — Air scripted combat demo CLI slice

- Starting commit: `5f3d1aa4`.
- Change batch: add `tools/diagnostics/air_combat_scripted_demo.py`, a
  reusable no-RL Stage 1 C2/ROE demonstration entry. It resolves the
  maintained Air engagement registry model, routes decisions through
  `DecisionRuntimeAgent`, drives the compiled `WorldBatchVecEnv`, and emits a
  compact JSON record of fire acceptance, native release, post-launch status,
  termination, and runtime replay identity.
- Focused verification: Python compilation and `git diff --check` passed. The
  direct command with `--post_launch_assessment --max_steps 400` exited `0`;
  it made `282` scripted decisions, recorded
  `fire_once_accepted=true` and `release_executed=true` at step `282`, then
  terminated at `post_launch_assessment_timeout` after four consequence steps.
- Evidence boundary: this is a reusable operator/demo entry and a native
  release acceptance record. It does not claim target destruction, terminal
  combat success, multi-aircraft engagement, EW resource closure, or
  `playable` promotion. The generated probe artifact is ignored and remains
  local evidence only.
- Continuation choice: retain this CLI as the tactical demo seam and next
  either close the existing post-launch terminal objective or record a bounded
  consequence proxy; keep the Air landing, EW, roster, Joint, and database
  lines independently schedulable.

### 2026-09-25 — Air tactical terminal near-range proxy probe

- Proxy setup: an ignored temporary copy of the maintained Stage 1 C2/ROE
  scenario moved `Red_Target` from `y=35000 m` to `y=10000 m`; no tracked
  scenario or native state was changed.
- Direct result: the scripted engagement model accepted a release at step `2`
  in the proxy, but a `1200`-step run still ended at `combat_timeout` with no
  target-destruction terminal. The proxy therefore rules out a simple
  long-range-only explanation for the current consequence gap; it is not a
  candidate maintained scenario.
- Evidence boundary: native fire/release acceptance is reproducible, while
  missile consequence and terminal objective closure remain unresolved. The
  temporary proxy is discarded from capability accounting.
- Continuation choice: do not promote tactical engagement to `playable`; next
  owner work must inspect the post-release effect/target-damage chain or use a
  sanctioned consequence proxy with explicit provenance.

### 2026-09-25 — Air EW native countermeasure resource gate

- Change batch: preserve the database unit's `ew_suite_ref` through the content
  parse pass while keeping suite resolution deferred to the existing factory
  materialize boundary; expose a diagnostics-only read-only
  `debug_get_countermeasure_state` snapshot; and add a direct native Air test
  that drives `PilotAction.program_chaff` and `program_flare` through the
  existing EW systems.
- Focused verification: rebuilt `ef_py` under the Visual Studio developer
  environment; the Air fixture plus EW contract tests passed `14 passed`. The
  native test observed the database-backed F-16 inventory and verified one
  chaff decrement followed by one flare decrement after native stepping.
  `git diff --check` passed. A plain PowerShell `ninja` invocation first lacked
  the MSVC standard include environment (`assert.h`/`cstdint`); the same build
  succeeded through `VsDevCmd.bat`, so this is an invocation prerequisite, not
  a source failure.
- Evidence boundary: this closes database-to-native EW component
  initialization and low-level countermeasure resource consumption. The getter
  is diagnostics-only and the scripted model still cannot write components.
  The canonical Air action-mode admission, launch-warning-driven scripted
  scenario/report, jammer command/state owner, replay, and multi-aircraft EW
  gates remain open; EW stays `entry_surface_incomplete` and Air stays
  `playable_candidate`.
- Continuation choice: use this native gate as the owner baseline while adding
  a maintained launch-warning scenario/report and deciding the jammer command
  owner; do not infer playable EW status from the direct low-level test.

### 2026-09-25 — Air EW native MAWS launch-warning fact

- Blocker evidence: a direct raw-kernel probe could fire a red missile at the
  blue unit, but the blue observation contained only the launch platform's ESM
  signal and `RWREvent.is_launch` remained false. The existing
  `RWR::is_missile_launch` field had no native producer, so a scripted EW
  launch-warning response could not be driven by a real inbound missile.
- Change batch: add a native MAWS pass to the Air sensor model that records
  active missiles targeting the owner within `120 km`, preserves their launch
  platform IDs for the frame, clears the fact in the existing `RWR_Reset`
  system, and merges source-specific launch rows into the observation API.
  The scripted side still reads only `rwr_warnings`; it does not inspect
  missile truth or mutate EW components.
- Focused verification: rebuild `ef_py` through the Visual Studio developer
  environment; `tests/runtime/air_combat/test_air_combat_1v1_fixture.py -q`
  passed `5 passed`; `tests/runtime/air/test_air_scripted_ew.py -q` passed
  `5 passed`; `git diff --check` passed before commit. The new Air fixture
  test fires a real native missile and asserts a blue `is_launch` row with the
  red launcher's `source_id`.
- Evidence boundary: the native launch-warning observation fact and reset path
  are now closed. This does not close the canonical EW action mode, scripted
  countermeasure/report path, jammer command owner, replay, multi-aircraft
  parity, or EW terminal objective. EW remains `entry_surface_incomplete` and
  Air remains `playable_candidate`.
- Continuation choice: use the native MAWS row as the input for the next
  maintained EW action scenario, while keeping the tactical missile terminal
  residual and the EW command-owner decision independent.

### 2026-09-25 — Air EW maintained action transport demo

- Change batch: add `tools/diagnostics/air_ew_scripted_demo.py`, a compiled
  `WorldBatchVecEnv` entry point using `air_ew_hybrid_v1`, the registered
  `air.ew.rwr_action_scripted` model, and the existing red scripted opponent.
  The CLI reports launch-warning steps, scripted countermeasure-request steps,
  runtime identity, and its native-state reporting limitation.
- Focused verification: `python tools/diagnostics/air_ew_scripted_demo.py
  --max_steps 120` completed with exit `0`; the head-on fixture produced
  launch-warning steps `[42, 82]` and matching countermeasure request steps
  `[42, 82]`, with `120` scripted runtime decisions. `py_compile` and
  `git diff --check` passed before commit.
- Evidence boundary: this demonstrates a real observation-to-action transport
  path under the compiled maintained runtime. `RuntimeFacade` does not expose
  countermeasure inventory/cooldown state, so the demo cannot prove native
  action acceptance, resource decrement, replay parity, or terminal EW
  closure. EW remains `entry_surface_incomplete`; Air remains
  `playable_candidate`.
- Continuation choice: add a read-only native EW state/report surface or an
  equivalent maintained event product before admitting this action mode as a
  consumed adapter; keep the low-level `SimulationKernel` resource gate as the
  separate native-owner evidence.

### 2026-09-25 — Air EW maintained countermeasure state projection

- Change batch: project Air-owned `Countermeasures` state into the existing
  read-only `InstrumentState` surface: chaff/flare counts, release interval,
  last release time, and auto mode. Missing components report `-1` for counts
  and timing values. The scripted model still only reads the declared
  observation and emits action fields; it does not write components.
- Focused verification: because the header dependency scan did not rebuild all
  consumers after the DTO layout change, the first incremental binding-only
  build caused a Windows stack-buffer-overrun at scenario load. A clean
  `build-scripted-agent` rebuild through `VsDevCmd.bat` completed all `139`
  objects and restored ABI consistency. After the clean build, the full Air
  fixture passed `11 passed`, the EW contract file passed `5 passed`, and the
  maintained demo reported launch/request steps `[42, 82]` with chaff
  `[60, 59]` and flare `[30, 30]`. `py_compile` and `git diff --check` passed.
- Evidence boundary: the maintained compiled Air action path now has a native
  read-only resource report and proves chaff consumption after the native
  release interval. Flare cadence, canonical action-mode admission, jammer
  ownership, replay/multi-aircraft parity, and terminal EW closure remain
  open. EW remains `entry_surface_incomplete`; Air remains
  `playable_candidate`.
- Continuation choice: retain clean rebuild as a gate for future shared DTO
  layout changes, add a cadence-complete EW report (including flare), and keep
  the action extension opt-in until scenario ownership and replay/roster gates
  are closed.

### 2026-09-25 — Air EW projection compatibility recheck

- Focused verification: after the clean rebuild and projection batch,
  `tests/runtime/bindings/test_bindings_runtime_dto_surface.py -q` passed
  `28 passed, 32 subtests passed`; the existing Air weapon path
  `tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py -q` passed
  `10 passed, 2 subtests passed`. The worktree remained clean and
  `git diff --check` passed.
- Evidence boundary: the new read-only InstrumentState fields do not change
  the existing binding DTO surface or missile release behavior. This is a
  compatibility recheck, not replay, flare-cadence, jammer, multi-aircraft,
  or playable promotion evidence.

### 2026-09-25 — Air EW maintained replay trace

- Change batch: add `tests/runtime/air_combat/test_air_ew_replay.py` to run the
  maintained compiled EW demo twice with the same scenario, seed, and doctrine.
  The test compares termination/report fields, source-driven warning steps,
  countermeasure request steps, native InstrumentState samples, runtime
  decision count, and scripted runtime identity.
- Focused verification: `CMO_BUILD_DIR=build-scripted-agent python -m pytest
  tests/runtime/air_combat/test_air_ew_replay.py -q` passed `1 passed` in
  `12.28s`. The paired runs both produced warning/request steps `[42, 82]`,
  chaff `[60, 59]`, flare `[30, 30]`, and `120` decisions. `git diff --check`
  passed before commit.
- Evidence boundary: this closes a bounded same-process two-run replay check
  for the opt-in EW demo trace. It does not establish canonical action-mode
  admission, reset/replay across cooperative roster members, flare cadence
  under independent requests, jammer state, or terminal EW closure. EW
  remains `entry_surface_incomplete`; Air remains `playable_candidate`.
- Continuation choice: preserve the replay test as a regression gate while
  keeping the action extension opt-in; next EW work should close a
  cadence-complete report and then exercise distinct roles through the
  cooperative roster.

### 2026-09-25 — Air cooperative EW resource-routing gate

- Change batch: add a cooperative runtime regression using the existing
  two-member Lead/Wing roster and the opt-in `air_ew_hybrid_v1` action shape.
  Lead receives only the chaff tail and Wing receives only the flare tail;
  the test reads each slot's native `InstrumentState` and checks formation
  metadata after the same-world step loop.
- Focused verification: `CMO_BUILD_DIR=build-scripted-agent python -m pytest
  tests/runtime/multi_agent/test_cooperative_vec_env_tasking.py -k
  routes_ew_resources_per_roster_slot -q` passed `1 passed, 15 deselected`.
  After 42 compiled steps, Lead chaff was below `60` while Lead flare stayed
  `30`; Wing flare was below `30` while Wing chaff stayed `60`. The two infos
  retained `ElementLead` and `Wingman` identities, and neither slot terminated.
- Evidence boundary: this closes only cooperative action-tail and native
  resource isolation for the existing no-threat cruise scenario. It is not a
  two-aircraft threat response, scripted producer replay, formation combat
  episode, or playable multi-aircraft EW result; the scenario has no hostile
  launcher, launch-warning objective, jammer path, or terminal EW report.
- Continuation choice: retain this as a multi-aircraft transport gate, then
  select or stage a database-backed two-aircraft threat scenario before
  claiming cooperative EW parity or promoting the action extension.

### 2026-09-25 — Cooperative hostile-threat behavior-owner residual

- Read-only finding: `CooperativeWorldBatchVecEnv` builds an isolated
  `ScenarioLoader` for every controlled roster slot, while each loader builds
  scripted opponents from the shared world layout. The cooperative post-step
  loop then invokes the behavior update hook once per slot. A future hostile
  two-aircraft scenario with scripted red units therefore needs an explicit
  world-level owner or a slot-safe opponent update contract before its
  runtime evidence can be trusted.
- Evidence: the relevant source path is
  `python/rl/runtime/cooperative_world_batch_vec_env.py` (`_build_slot_loader`
  and `_step_wait_refresh_state_and_behavior`) plus
  `gym_envs/scenario_loader/behavior_runtime/scripted_opponents.py`
  (`build_from_loader`/`update_scripted_opponents`). This is an ownership
  analysis, not a claim that an unbuilt 2v2 scenario has already failed.
- Alternative used: keep the no-threat Lead/Wing cooperative scenario as the
  bounded action-tail/resource-isolation proxy and defer hostile 2v2 staging
  until the owner decision is made. No capability label is promoted.
- Gate impact: cooperative hostile-threat EW replay, formation combat, and
  large-scale Air demonstration remain open; Air stays `playable_candidate`
  and EW stays `entry_surface_incomplete`.

### 2026-09-25 — Cooperative Air 2v2 scripted EW demo

- Change batch: make the hostile cooperative slice a maintained scenario and
  CLI: `scenarios/air_combat/cooperative_air_2v2_scripted_ew_response_v1.json`,
  `tools/diagnostics/air_cooperative_ew_scripted_demo.py`, and its runtime
  regression. The scenario contains two Blue roster members and two Red
  `red_scripted_agent` opponents, with explicit Lead/Wing targets and no
  terminal combat objective.
- Behavior owner: cooperative slot loading now accepts
  `build_scripted_opponents=False`; only the world routing/owner loader builds
  and updates scripted opponents. Non-owner slot loaders still own their
  platform guidance and command chain but do not duplicate shared-world
  opponent updates.
- Focused verification: the cooperative 2v2 test and CLI regression passed.
  With seed `20260516`, the CLI ran `204` steps without termination and
  reported Lead warning/request steps `[162, 202]`, Wing `[202]`, native chaff
  samples Lead `[60, 59]` and Wing `[60]`, and two active owner reports mapped
  to the Lead/Wing entity IDs. The owner roster was `[2, 0]` scripted
  opponents for Lead/Wing. Python compilation and `git diff --check` passed.
- Evidence boundary: this is the first maintained hostile cooperative EW
  response demonstration and closes the world-level opponent-owner residual
  for this path. It is still an EW response demo, not a full multi-aircraft
  combat episode: there is no terminal objective, no jammer/ESM action, no
  datalink loss, no tactical reassignment, and no target-destruction claim.
  EW remains `entry_surface_incomplete`; Air remains `playable_candidate`.
- Continuation choice: use this scenario as the base for cooperative EW replay
  and later formation combat. Keep its no-terminal-objective boundary explicit
  until weapon consequence, command/report, and mission-success contracts are
  separately closed.

### 2026-09-25 — Cooperative Air 2v2 EW replay gate

- Change batch: add a paired-run regression for the maintained hostile 2v2
  scenario and its cooperative CLI. The test compares world termination state,
  roster owner counts, source-driven warning/request traces, native resource
  samples, scripted opponent reports, runtime decision counts, and both
  scripted runtime identities.
- Focused verification: `tests/runtime/air_combat/test_air_cooperative_ew_demo.py
  -q` passed `2 passed`; the replay test reproduced the exact Lead/Wing
  warning/request traces and owner report values for seed `20260516`.
  `git diff --check` passed before commit.
- Evidence boundary: bounded same-process replay/reset parity for the hostile
  cooperative EW response demo is now verified. This does not close terminal
  combat, jammer/ESM, communication loss, tactical reassignment, or full
  formation mission replay. EW remains `entry_surface_incomplete`; Air remains
  `playable_candidate`.
- Continuation choice: retain this replay gate and use the same scenario for a
  later terminal-objective slice only after native weapon consequence and
  command/report ownership are resolved.

### 2026-09-25 — Air EW single-countermeasure doctrines

- Change batch: extend the Air-owned scripted EW doctrine vocabulary with
  `chaff_only` and `flare_only`. The 14-element action producer maps these
  doctrines to exactly one tail bit; the existing `countermeasure_ready`
  doctrine continues to request both resources.
- Focused verification: `tests/runtime/air/test_air_scripted_ew.py -q`
  passed `7 passed`; `tests/runtime/air_combat/test_air_ew_replay.py -q`
  passed `2 passed`; Python compilation and `git diff --check` passed. The
  maintained head-on scenario with `flare_only` produced warning/request steps
  `[42, 82]`, chaff `[60, 60]`, and flare `[30, 29]`.
- Evidence boundary: this closes a maintained flare-specific action/resource
  trace and keeps doctrine selection explicit. It does not admit the action
  mode into the canonical config, add jammer command ownership, prove hostile
  cooperative replay, or close a terminal EW objective. EW remains
  `entry_surface_incomplete`; Air remains `playable_candidate`.
- Continuation choice: retain the three doctrines as opt-in scenario inputs;
  next admission work must supply scenario ownership, complete cadence/report
  semantics, and the cooperative hostile-threat owner decision.

### 2026-09-25 — Air scripted weapon selector and native consequence recheck

- Root-cause finding: the scripted C2/ROE producer had been writing selector
  `0` for both maintained Air action transports. The existing transport maps
  that value to no valid station, so the compiled release path accepted a
  `legacy:missile` fallback even though the database-backed F-16 loadout had
  generated station-1 `AIM-120C-7` stores. This was an action-contract bug, not
  a missing `DefaultUnitFactory` loadout materialization.
- Change batch: encode station 1 as `1/7` in the 17-element `full` transport
  and as categorical value `1` in `air_combat_hybrid_v1`; add model-level and
  compiled WorldBatch regression assertions that the accepted launch includes
  `AIM-120C-7`.
- Focused verification: the Air engagement, hybrid action, and maintained
  fire-missile tests passed `18 passed, 2 subtests passed`. A maintained
  compiled Stage 1 run with seed `20260516` then exported a native packet with
  nearest approach at `43.1280 s`, miss distance `0.6321 m`, closure
  `657.4265 m/s`, and a triggered `15.0 m` fuze. The target consequence was
  `detonated_no_effect` with `destroyed=false` and loss state
  `combat_capable`.
- Evidence boundary: the scripted release now reaches the database weapon and
  native near-approach/fuze path; this does not close target vulnerability,
  damage-effect, terminal combat, or post-launch assessment acceptance. Air
  remains `playable_candidate`, and the Stage 1 C2/ROE path remains an accepted
  release demonstration rather than a playable terminal engagement.
- Continuation choice: retain the selector fix as the baseline and keep the
  terminal gate focused on the native effect/damage owner. Do not substitute a
  Python-side kill or silently widen the target model to claim terminal success.

### 2026-09-25 — Air C2/ROE native terminal surrogate

- Change batch: add the maintained
  `air_combat_1v1_c2_roe_terminal_generic_aircraft_surrogate_v1.json` scenario
  and `test_air_scripted_terminal_surrogate.py`. The scenario uses the
  built-in generic `Aircraft` factory definition as an explicit terminal-chain
  surrogate; it does not alter the named-platform database profiles.
- Focused verification: the compiled no-RL CLI with seed `20260516` accepted
  the scripted release at step `2`, terminated at step `203` with native
  `combat_win`, and awarded the existing `combat_win_bonus` of `1500.0`.
  The regression passed `1 passed` in `15.15s`; Python compilation and
  `git diff --check` passed.
- Evidence boundary: this closes an end-to-end playable terminal demo for the
  declared generic surrogate, including C2/ROE, database weapon selection,
  native missile/effects/damage, and objective termination. It does not close
  named-platform vulnerability calibration, MQ-9 terminal consequence,
  tactical evasion, red weapons, or formation combat. Air remains
  `playable_candidate`; the surrogate is not a promotion to `playable`.
- Continuation choice: retain this scenario as the bounded terminal-chain
  baseline while keeping the Stage 1 MQ-9 target on the native damage-effect
  investigation path. Any future promotion must name the target model and
  evidence boundary separately.

### 2026-09-26 — Air delayed online-sensor burst geometry

- Root-cause finding: an `online_sensor` delayed fuze stored no trigger-frame
  burst point, so delayed resolution fell back to the missile transform from a
  later ECS frame. With a `0.015 s` delay and `0.05 s` step this moved the
  effective burst by tens of metres and made the native effect result depend on
  frame cadence.
- Change batch: preserve the sensor-trigger-frame missile point, expose the
  stored detonation coordinates through the native missile diagnostics surface,
  and reproject that point from the trigger-frame target-relative geometry when
  the delayed effect resolves. Add a maintained regression at the coarse step
  that fails the previous drift and keeps the effect within the bounded
  trigger-frame envelope.
- Focused verification: clean `ef_py` rebuild completed `139/139`; the final
  Air suite passed `85 passed, 8 subtests passed`, including
  `test_online_sensor_delayed_burst_projection.py` and the existing launch,
  fuze, scripted engagement, generic terminal surrogate, and hybrid-action
  tests. `git diff --check` passed before commit `8d143940`.
- Maintained Stage 1 MQ-9 CLI recheck with seed `20260516` still accepted the
  database release at step `282` but ended at step `2400` with
  `combat_timeout`, `pending_assessment=true`, and no terminal kill. This is
  direct evidence that the geometry fix does not close the named-platform
  damage/effects or post-launch assessment chain.
- Evidence boundary: the native delayed online-sensor geometry is now stable
  for the maintained coarse-step regression and remains observable in the
  diagnostic packet. This does not establish named-platform damage authority,
  stable MQ-9 terminal kill, post-launch assessment, evasion, red weapons,
  formation combat, or a promotion beyond `playable_candidate`.
- Continuation choice: use this fix as the native effects prerequisite for a
  later named-platform terminal slice; keep the generic-Aircraft surrogate as
  the only bounded terminal-chain demonstration and do not add a Python-side
  kill substitute.

### 2026-09-26 — Air named-platform live damage after trigger-frame fix

- Evidence recheck: the maintained MQ-9/AIM-120 live consumer path was rerun
  after the delayed online-sensor geometry fix. At the fixed `8000 m` setup it
  records `damage_applied`, a `3.28 m` miss, a direct hitbox intersection, three
  projected hitboxes, four component loads, negative system-health delta, and
  `mission_kill=true` while the target entity remains active. At the fixed
  `14000 m` setup it records `damage_applied`, a `3.73 m` miss, three projected
  hitboxes, four component loads, and a negative system-health delta without a
  terminal loss state.
- Change batch: update the two maintained MQ-9 live-chain assertions that still
  encoded the pre-fix `detonated_no_effect`/zero-component outcome. The tests
  now require native damage evidence and explicitly retain the synthetic,
  unvalidated vulnerability boundary through `_assert_mq9_event_is_non_authoritative`.
- Focused verification: the consumer wrapper passed `14 passed, 7 xfailed,
  4 subtests passed`; the full `tests/runtime/air_combat/weapon_guidance_realism`
  package passed `171 passed, 33 xfailed, 217 subtests passed` in the local
  run. The prior clean native build remains the artifact under test.
- Evidence boundary: this establishes a reproducible native named-platform
  damage/effects path for two controlled live geometries, including one
  mission-kill consequence. It does not establish calibrated MQ-9 Pk or fuze
  authority, deterministic terminal destruction, post-launch assessment
  closure, evasion, red weapons, formation combat, or a promotion beyond
  `playable_candidate`.
- Continuation choice: keep the generic-Aircraft surrogate as the only bounded
  terminal `combat_win` demonstration, use the MQ-9 cases as native consequence
  fixtures, and investigate terminal/post-launch closure separately rather
  than widening projection radii or substituting a Python kill.

### 2026-09-26 — Air roster-driven 4v4 EW scale demonstration

- Change batch: generalize `tools/diagnostics/air_cooperative_ew_scripted_demo.py`
  to resolve controllable slots and formation roles from the scenario-owned
  roster instead of hard-coding Lead/Wing. The runner now supports any positive
  roster size, uses the scenario time step for scripted runtime clocks, and
  preserves the world-owner update path. Add the maintained
  `cooperative_air_4v4_scripted_ew_response_v1.json` scenario with two Blue
  elements and four Red scripted opponents.
- Focused verification: the maintained cooperative EW test passed `3 passed`.
  With seed `20260516` and `204` steps, all four slots remained running, the
  owner roster was `[4, 0, 0, 0]`, all four Red opponent reports were active,
  and the warning/request traces were Lead-A `[42, 82, 122, 162, 202]`,
  Wing-A `[42, 82, 122, 162, 202]`, Lead-B `[162, 202]`, and Wing-B `[202]`.
  Chaff samples were `[60,59,58,57,56]`, `[60,59,58,57,56]`, `[60,59]`, and
  `[60]` respectively, with flare remaining `30` in every sample. The same
  seed replay matched roster, warning/request, resource, report, and scripted
  identity traces.
- Evidence boundary: this establishes a roster-driven four-slot, two-element
  EW response and resource-isolation demonstration at a larger scale. It does
  not establish terminal combat, full multi-aircraft weapon employment,
  jammer/ESM, communication loss, tactical reassignment, formation combat
  mission parity, or a full visualization/large-scale combat claim. EW remains
  `entry_surface_incomplete`; Air remains `playable_candidate`.
- Continuation choice: retain the 4v4 scenario as the bounded scale baseline;
  use the same roster contract for later 8+ slot or joint demonstrations only
  after command/report and native weapon ownership gates are separately
  evidenced.

### 2026-09-26 — Air cooperative multi-aircraft C2/ROE terminal slice

- Change batch: admit the existing Air `air_combat_hybrid_v1` event-action gate
  and post-step finalizer in `CooperativeWorldBatchVecEnv` at per-slot scope;
  preserve each slot's previous policy intent and pre-step truth, reset the
  event state with the slot, and project native event fields into each slot's
  report. Add the RL-independent
  `tools/diagnostics/air_cooperative_combat_scripted_demo.py` runner and the
  maintained `cooperative_air_2v1_scripted_c2_roe_engagement_v1.json` scenario.
- Focused verification: the maintained cooperative combat test passed `2
  passed`; seed `20260516` reached `combat_win` at step `202` with both
  Blue slots reporting `fire_once_accepted` and `release_executed` at step `2`.
  The paired run reproduced the roster, event steps, decision reports, and
  scripted identities. The cooperative runtime compatibility regression and
  existing EW regressions also passed (`7 passed, 17 deselected`).
- Evidence boundary: this closes a bounded two-aircraft, one-shared-world
  native weapon-release and terminal-objective route using the generic
  `Aircraft` target surrogate. It does not establish named-platform
  vulnerability calibration, multi-target assignment, red weapons, formation
  mission parity, communication loss, tactical reassignment, visualization,
  or a large-scale terminal combat claim. Air remains
  `playable_candidate`.
- Continuation choice: retain the 2v1 route as the first cooperative weapon
  baseline; next close per-member target/task override ownership and broaden
  only after native report/replay evidence is retained. Keep the generic
  target explicitly marked as a terminal surrogate.

### 2026-09-26 — Air cooperative per-member mission target ownership

- Change batch: make the already-declared roster
  `mission_command_overrides` an effective director-owned seam. Cooperative
  slot loaders now receive non-formation/non-takeoff member command fields,
  including C2/ROE and assigned-target fields; a member's target name is
  resolved back to the slot-local `assigned_target_id` and `primary_target_id`
  after the override so the observation, objective, and event gate share one
  target owner. Formation and takeoff fields remain under their existing
  director progression logic.
- Focused verification: the new target-owner regression passed, and the full
  cooperative tasking and observation files passed `19 passed` each. The test
  mutates the maintained 2v2 roster so Lead owns `Red_Lead` and Wing owns
  `Red_Wing`, then verifies the slot-local name, ID, and C2 authorization
  fields after reset.
- Evidence boundary: this closes the roster-to-mission target projection
  contract, not a multi-target terminal engagement. It does not by itself
  prove target reassignment, data-link loss, formation mission parity, or
  calibrated named-platform consequences.
- Continuation choice: use the owner seam for a paired generic-Aircraft
  two-target scenario, retaining the same native event/replay gates before
  widening the Air scale claim.

### 2026-09-26 — Air cooperative two-target terminal demonstration

- Change batch: add `cooperative_air_2v2_scripted_c2_roe_terminal_v1.json`
  with two generic `Aircraft` targets and slot-owned `Red_A`/`Red_B`
  assignments. Extend the RL-independent cooperative combat CLI to report the
  resolved per-slot target owner.
- Focused verification: the maintained combat test file passed `3 passed`.
  With seed `20260516` the two slots resolved to `Red_A` and `Red_B`, each
  recorded native `fire_once_accepted` and `release_executed`, and both ended
  with `combat_win`; a paired run matched event steps, target owners, reports,
  decision counts, and runtime identities.
- Evidence boundary: this is a bounded two-aircraft/two-target terminal
  surrogate demonstration. It does not establish target reassignment under
  communication loss, red weapons, formation mission parity, named-platform
  calibration, visualization, or large-scale terminal combat.
- Continuation choice: retain the two-target trace as the multi-aircraft
  baseline; next inspect command/report closure and formation behavior before
  moving to 4+ aircraft terminal composition.

### 2026-09-26 — Air cooperative 4v4 terminal scale demonstration

- Change batch: add `cooperative_air_4v4_scripted_c2_roe_terminal_v1.json`
  with two declared Blue elements, four slot-owned generic-Aircraft targets,
  and the same native C2/ROE event route used by the 2v2 baseline. Extend the
  maintained combat regression to four active scripted slots.
- Focused verification: the maintained cooperative combat test file passed `4
  passed`. With seed `20260516`, target owners resolved as `Red_A`, `Red_B`,
  `Red_C`, and `Red_D`; all four slots recorded `fire_once_accepted` and
  `release_executed`, ended with `combat_win` without truncation, and retained
  four unique scripted runtime identities. The paired run matched event
  steps, target owners, terminal reasons, decision reports, decision counts,
  and identities.
- Evidence boundary: this is a bounded four-aircraft/two-element terminal
  surrogate demonstration. The generic targets have no red weapons and do not
  provide calibrated named-platform vulnerability, formation mission parity,
  communication loss, tactical reassignment, visualization, or a full
  command/report presentation claim.
- Continuation choice: retain 4v4 as the current large-scale scripted combat
  baseline; inspect formation/report and visualization gates before widening
  the label or adding joint tasking.

### 2026-09-26 — Air deterministic tactical planning layer

- Change batch: add the RL-independent `AirEngagementPlanner` and
  `AirEngagementPlannerConfig` under `python/tasking_contracts`. The planner
  consumes only the declared C2/ROE mission fields and the five-column contact
  token, evaluates hold/intercept/reposition candidates, filters by target
  contact, authority, window, assessment, and shot-budget constraints, and
  selects a weighted range/geometry/closure/freshness utility. It emits an
  auditable plan with candidate scores and reason codes; bounded guidance is
  applied through the existing flight action transport, while native fire
  gates retain final release authority. No RL, simulator truth, or privileged
  target geometry is imported.
- Focused verification: the pure planner and engagement model tests passed
  `9 passed`; the cooperative scripted combat regression passed `4 passed`
  after the planner was integrated. A clean `b7c63944` baseline reproduced
  the four-ship terminal trace at step `206`; the first planner attempt waited
  for the quality-window age and delayed release to step `33`, causing one
  surrogate miss. Removing that duplicate gate restored release at step `2`
  and the full 4v4 terminal trace. This is a recorded behavioral correction,
  not evidence of calibrated weapon optimality.
- Evidence boundary: this closes the first L3-style bounded tactical-planning
  seam (finite candidate evaluation plus receding replanning) above the L1
  flight controllers and L2 event policy. It does not establish global
  optimality, a calibrated WEZ/LAR/Pk model, adversarial maneuver search,
  post-launch guidance, dynamic multi-aircraft task allocation, or a
  named-platform terminal claim. Air remains `playable_candidate`.
- Continuation choice: retain the planner as an explicit algorithm layer and
  next add source-backed weapon-envelope inputs and post-launch assessment
  before claiming an optimal firing-position policy. Keep RL on its separate
  adapter line.

### 2026-09-26 — Air source-backed weapon-envelope planning slice

- Change batch: add the pure-Python `AirWeaponEnvelope` loader and expose it
  as an optional input to `AirEngagementPlannerConfig` and
  `AirScriptedEngagementModel`. The loader reads only declared database
  fields: AIM-120C-7 seeker/sensor opportunity range, flight time, speed,
  lateral-g, and any explicitly supplied launch limits. It retains source
  fields and labels the profile `runtime_tuning_only` with `pk_authority=false`.
- Algorithm boundary: the planner adds a guidance-opportunity term to its
  finite candidate utility. An explicit closed opportunity prevents scripted
  `commit`, while the native fire gate remains the final release authority.
  The implementation does not infer effective range from speed, fill missing
  minimum range/off-boresight values, or claim WEZ/LAR/Pk calibration.
- Focused verification: Air planner and engagement tests passed `12 passed`;
  Python compilation and `git diff --check` passed. Direct construction loaded
  `examples/config/database/weapons/air_to_air/aim_120c.json` as
  `AIM-120C-7` with `guidance.active_seek_range=16000` and no inferred launch
  limits.
- Evidence boundary: this is a source-backed planning constraint, not a
  weapon-effectiveness model. Post-launch outcome assessment, midcourse
  guidance, dynamic weapon allocation, and named-platform terminal success
  remain open. Air remains `playable_candidate`; RL remains a separate
  optional adapter line.
- Continuation choice: add a conservative scripted post-launch assessment
  state machine that consumes declared event facts and mission observation,
  then independently test reattack gating and inconclusive outcomes.

### 2026-09-26 — Air conservative scripted post-launch assessment slice

- Change batch: add `AirPostLaunchAssessment` as an RL-independent state
  estimator with explicit `idle`, `in_flight`, `terminal_observed`,
  `reattack_ready`, `track_lost`, and `track_unavailable` states. The
  engagement model consumes the previous step's declared event info and the
  C2/ROE mission fields, reports the assessment beside the tactical plan, and
  uses only the estimator's `blocks_fire` result for scripted reattack gating.
- Algorithm boundary: `terminal_observed` requires explicit
  `target_effect_observed`, `target_mission_killed`, or `target_destroyed`
  evidence. A missing contact, stale track, or missing effect evidence stays
  `inconclusive`; no state writes rewards, damage, terminal status, or RL
  buffers. The native environment remains the owner of release acceptance and
  terminal semantics.
- Focused verification: Air assessment, planner, and engagement tests passed
  `17 passed`; the cooperative 4v4 scripted combat regression passed `4
  passed`; cross-domain roster and tasking-boundary regression passed `13
  passed`; Python compilation and `git diff --check` passed.
- Evidence boundary: this closes a conservative scripted post-launch
  decision layer and reattack gate, not a calibrated hit/miss classifier or
  complete terminal objective. Midcourse guidance, target-effect authority,
  dynamic multi-aircraft weapon allocation, and named-platform playable
  promotion remain open. RL stays on its separate optional adapter line.
- Continuation choice: use the assessment report in a maintained scenario
  trace, then address target-effect/event ownership before any claim of
  complete post-launch combat assessment.

### 2026-09-26 — Air algorithm substitution research and planning slice

- Scope: read-only architecture research after the Air planner and conservative
  post-launch assessor were implemented. No runtime or scenario behavior was
  changed in this slice.
- Finding: `ScriptedModelRegistry` can replace the complete scripted model,
  while `AirScriptedEngagementModel` still directly constructs the planner and
  assessor and also owns mission decoding, fire-latch state, and 17/12 action
  mapping. The algorithm modules are independently testable, but the inner
  strategies are not yet drop-in replaceable.
- Research record: add
  `docs/architecture/reviews/air_scripted_algorithm_substitution_research_20260926.md`
  with the dependency map, replacement assessment, typed Air-owned strategy
  seams, ALG-0 through ALG-4 migration batches, acceptance gates, and open
  research questions.
- Boundary decision: use Air-owned planner/assessor/observation/action
  protocols and dependency injection; retain the existing model registry as
  the outer selection surface; do not create a second global strategy
  registry, common weapon/geometry mega-schema, or RL-owned implementation.
- Evidence boundary: this is a planning and research record. Air remains
  `playable_candidate`; no strategy substitution, behavior parity, or
  complete target-effect closure is claimed until WP3-AIR-ALG is implemented
  and its acceptance gates pass.
- Continuation choice: implement ALG-0/ALG-1 as the next code batch, starting
  with typed context/decision contracts and default-injection parity tests.

### 2026-09-26 — Air ALG-0 typed strategy contract slice

- Starting commit: `30706c5c`.
- Change batch: add the Air-owned `AirPlanningContext`, `AirTacticalDecision`,
  `AirAssessmentInput` and replacement protocols in
  `air_scripted_strategy_contracts.py`. The existing planner now exposes a
  context entry point and projects its rich audit record onto the typed
  decision DTO; legacy primitive `plan(...)` callers remain available.
- Focused verification: the new strategy-contract tests and existing planner
  tests passed `10 passed`; Python compilation and `git diff --check` passed.
- Boundary decision: the contracts validate finite/non-negative declared
  values and bound guidance outputs, while retaining diagnostics as an
  immutable mapping. They do not import RL/native runtime, expose raw mission
  arrays, or grant fire/terminal authority.
- Evidence boundary: this freezes the typed substitution boundary but does not
  yet prove that the engagement orchestrator can inject a replacement planner
  or assessor. That is the next ALG-1 batch.

### 2026-09-26 — Air ALG-1 planner and assessor injection slice

- Starting commit: `da806d93`.
- Change batch: add Air-owned planner/assessor protocol use to
  `AirScriptedEngagementModel`; the default implementations are constructed
  only when no override is supplied. The engagement model now passes typed
  `AirPlanningContext` and `AirAssessmentInput` values and consumes the typed
  tactical decision. Default rich diagnostics remain available under the
  tactical-plan report for replay compatibility.
- Replacement proof: a no-fire planner suppresses only tactical release while
  preserving flight and radar transport; a blocking assessor suppresses only
  the fire request while preserving the default planner. Configuration is
  rejected when it is ambiguously combined with an injected planner.
- Focused verification: the strategy-contract, assessment, planner, and
  engagement tests passed `25 passed`; the cooperative terminal and tasking
  boundary regression passed `19 passed`; Python compilation and
  `git diff --check` also passed.
- Evidence boundary: this closes planner/assessor injection, not observation
  decoding or action-layout extraction. `_mission_values`, contact geometry,
  17/12 action mapping, and fire-latch transport remain in the orchestrator
  until ALG-2. Air remains `playable_candidate`; RL remains optional.
- Continuation choice: extract observation and action adapters with a default
  parity fixture before adding any second maintained strategy profile.

### 2026-09-26 — Air strategy physical-layer split

- Starting commit: `1ff78ff2`.
- Change batch: move the canonical Air strategy implementations into
  `python/tasking_contracts/air/strategy/` (`contracts`, `planning`,
  `assessment`, and `weapons`). The old flat `air_scripted_*` strategy paths
  were removed. Strategy tests now live under `tests/runtime/air/strategy/`;
  a physical-layer test checks the package contents and RL/environment-free
  imports.
- Boundary decision: physical location now reflects policy ownership without
  moving the neutral lifecycle or creating a second registry. The engagement
  model imports the canonical Air strategy layer; repository consumers use
  canonical imports directly.
- Focused verification: canonical strategy, compatibility, engagement, and
  physical-layer tests passed `28 passed`; explicit-file Python compilation and
  `git diff --check` passed. The earlier wildcard compile invocation was a
  PowerShell argument-expansion error and was replaced by an explicit-file run.
- Evidence boundary: this closes the first physical-layer split only. The
  remaining `python/tasking_contracts` root still contains mixed common and
  domain modules; the next layout batch must partition those into common,
  Air, Naval, and Joint packages without changing runtime ownership claims.

### 2026-09-26 — Tasking contracts physical domain partition

- Starting commit: `8bb307a4`.
- Change batch: partition the canonical tasking-contract implementation into
  `python/tasking_contracts/common`, `air`, `naval`, and `joint`. Air is split
  further into `execution`, `engagement`, `ew`, and `strategy`. The former root
  module paths were removed after repository consumers migrated to canonical
  imports; no second compatibility path is retained.
- Consumer update: maintained Air, Naval, visualization, evaluation, and
  diagnostics entry points now import their canonical physical layers. The RL
  control package remains a facade for wrapper access, while scripted models
  are imported from their canonical Air/common modules.
- Focused verification: Air/Naval/Joint/runtime regressions passed `67 passed`;
  physical-layer, compatibility, neutral-boundary, CLI, wrapper, and
  visualization contract tests passed `31 passed` with the explicit local
  `ef_py` path; Python compilation and `git diff --check` passed.
- Environment residual: one initial compatibility test invocation omitted the
  explicit `PYTHONPATH=build-scripted-agent` binding and stopped at the known
  missing-`ef_py` collection boundary. Re-running with the maintained local
  binding passed; no code failure was inferred from the first invocation.
- Boundary decision: physical placement now distinguishes common contracts
  from domain policy and adapters. This is a structural refactor only; it does
  not promote Air, Naval, Joint, or Ground capability labels and does not make
  RL part of the scripted line.

### 2026-09-26 — Canonical tasking imports and compatibility-shell removal

- Starting commit: `acc19c87`.
- Change batch: removed the remaining flat `python/tasking_contracts/*.py`
  forwarding modules and the scripted-controller/mission forwarding modules
  under `python/rl/control`. Repository production code, tests, scenario
  manifests, tools, and visualization entry points now import the canonical
  `common`, `air`, `naval`, or `joint` modules directly.
- Structural consequence: the tasking-contract root contains only its package
  initializer; the RL control package retains only real wrapper behavior and
  direct canonical exports. There is no repository-owned dual-path contract to
  maintain.
- Focused verification: canonical physical-layer, boundary, registry,
  capability-manifest, Air/Naval/Joint runtime, authority-census, and
  visualization tests passed `274 passed` plus `7` subtests in the final focused run; the first
  run exposed stale manifest and census paths, which were migrated to the
  canonical files before the green rerun.
- Boundary decision: this is an import-topology cleanup only. It does not
  change scripted capability labels, RL participation rules, or native action
  ownership. Downstream external consumers of the deleted paths must migrate
  to the canonical modules.

### 2026-09-26 — Air ALG-2 observation and action adapter extraction

- Starting commit: `33e59f36`.
- Change batch: extract Air mission/contact decoding into
  `AirMissionContactObservationAdapter` and the maintained full/hybrid action
  layout, target-contact edge pulse, station encoding, and fire latch into
  `AirActionLayoutAdapter`. Add typed `AirTacticalObservation`,
  `AirTacticalActionIntent`, and `AirActionApplication` contracts plus
  `AirObservationAdapter`/`AirActionAdapter` protocols.
- Consumer update: `AirScriptedEngagementModel` now coordinates the flight
  model, observation adapter, planner, assessor, and action adapter. The model
  no longer owns mission-array indexing, contact-row selection, action indices,
  or fire-latch state. Default adapters are injected automatically and custom
  adapters are validated structurally.
- Focused verification: Air strategy physical-layer, adapter contract,
  Air engagement/execution, cross-domain roster, and cooperative 4v4 terminal
  tests passed `43 passed`; compile and `git diff --check` passed. The direct
  adapter test covers both first-fire and repeated-fire latch behavior, while
  the engagement test verifies recording adapter injection.
- Boundary decision: the extraction changes ownership and substitution seams
  only. It preserves the 17/12 action transports and leaves native event/fire
  acceptance, terminal effects, capability labels, and RL participation rules
  unchanged.

### 2026-09-26 — Air ALG-3 adapter substitution parity

- Starting commit: `725103fc`.
- Change batch: add a private model-factory injection point to the maintained
  cooperative Air combat diagnostic and a regression that runs the same 2v1
  compiled scenario through the canonical default route and through recording
  observation/action adapters delegating to the default implementations.
- Focused verification: the cooperative combat regression passed `5 passed`.
  The injected route matched terminal state, event/release steps, roster,
  decision reports, runtime decision counts, and deterministic replay identity;
  both per-slot adapters recorded calls.
- Boundary decision: this proves the adapter layer is substitutable at a
  scenario terminal boundary without changing fire-gate or native ownership.
  No second maintained strategy profile or strategy registry was added, and
  Air remains `playable_candidate` pending command/report, visualization, and
  named-platform effect gates.

### 2026-09-26 — Air scripted CLI without a training configuration

- Starting commit: `b243f1b1`.
- Change batch: make `--train_config` optional only for `--scripted`;
  keep it required with `--model`. Defer the CLI's learned-policy and
  wrapper imports to the learned branch, and defer world-batch runtime import
  until environment construction. The CLI report now reads the declared
  scenario name and `InstrumentState.alt_radar`, omits non-finite optional
  fields, and rejects non-standard JSON constants.
- Focused verification: the native-free import/argument regression passed
  `3 passed`; a five-step compiled scripted smoke ran without a training
  configuration, and a second five-step smoke ran with SB3 and Torch imports
  blocked. The learned path rejected a missing training configuration before
  opening a runtime.
- Direct full-episode verification: the maintained continuous Air scenario
  ran with `--scripted`, seed `0`, no training configuration or
  checkpoint, and local compiled binding. It ended after `16942` steps
  with `success_objective`, `mission_status=[4,1,1,1]`, runway
  geometry true, and a strictly parseable JSON summary with a non-empty
  scenario name and finite final radar altitude.
- Boundary decision: this closes the training-config requirement for the
  scripted Air CLI, not full package-level RL isolation. The shared
  world-batch runtime is still physically under `python.rl.runtime`, and
  the CLI run does not prove command/report episode closure or visualization
  process acceptance. Air remains `playable_candidate`.

### 2026-09-26 — Air C2 departure-to-route deadlock correction

- Starting commit: `0ad1609f`.
- Diagnostic before the change: a fixed-route C2 scenario with a scripted
  execution backend, seed `7`, and zero leader adjustments reached
  `TASK_CAP` but held command code `1` and phase `departure` for all
  `800` decision windows before timeout. A 121-window trace showed the
  aircraft above `1700 m` AGL while the first route waypoint and command
  code remained unchanged. The departure phase inferred from an unadvanced
  first waypoint emitted a takeoff command; route guidance requires command
  code `3`, so the original condition could not make progress.
- Change batch: `RuleBasedLeaderPhaseManager` now enters
  `transit_to_station` when an aircraft with a route is airborne above the
  configurable `departure_route_alt_agl_m` threshold (default `140 m`),
  even before the first waypoint advances. Below that gate it retains the
  takeoff/departure command. A contract regression covers both sides of the
  transition without changing waypoint state.
- Focused verification: leader, leader-tasking, and command-bridge regressions
  passed `73 passed, 6 subtests passed`; Python compilation and diff checks
  passed.
- Direct post-change probe: the same fixed-route C2 scenario entered
  `TASK_SCRAMBLE -> TASK_CAP -> TASK_RTB -> TASK_RECOVER_LAND`, observed
  command codes `1`, `3`, and `4`, advanced through waypoint index `9`,
  and emitted report types `1`, `17`, and `20`. The three C2 transitions
  occurred at decision windows `19`, `351`, and `681`.
- Remaining failure: the episode terminated at decision window `776` with
  `off_runway_terminate` and mission success `-1`, despite a valid final
  report. This is command/report transition coverage, not successful episode
  closure. Inspect the terminal recovery geometry and command timing in a
  separate landing batch; do not promote Air beyond `playable_candidate`.
- Dependency boundary: the corrected manager still resides under
  `python.rl.tasking`. This change does not establish independent C2
  package ownership or a no-RL full command/report loop.

### 2026-09-26 — Air C2 terminal-vector and ILS readiness correction

- Starting commit: `508936e0`.
- Diagnostic before the change: the route exhausted around 8.2 km before the
  runway center with a roughly 35-degree inbound heading error. The C2
  route-exhaustion branch immediately armed ILS without the existing terminal
  runway-frame gate. The resulting approach reached the ground about 4.6 km
  cross-runway and ended with `off_runway_terminate`.
- Change batch: route exhaustion now retains the pending landing vector until
  the runway/ILS terminal geometry is ready. The phase manager consults the
  same loader-owned readiness gate and fails closed if it is unavailable. The
  C2 demonstration declares the maintained 2600 m intercept and 3500 m
  terminal window used by the successful continuous Air scenario; no route
  coordinate or target state is injected into the policy.
- Focused verification: execution, leader, mission-tasking, and command-bridge
  regressions passed `86 passed, 17 subtests passed`; Python compilation and
  `git diff --check` passed. A new regression proves that an exhausted C2
  route remains pending outside the terminal window and becomes ready inside
  it, while the leader gate rejects premature arming.
- Direct native verification on the final code: scripted execution with seed
  `7` and zero leader adjustments followed `TASK_SCRAMBLE -> TASK_CAP ->
  TASK_RTB -> TASK_RECOVER_LAND` at windows 0, 19, 351, and 681. It terminated
  at window 769 with `success_objective`, mission status `[4,1,1,1]`,
  valid final report, runway geometry true, and 3.63 m cross-runway offset.
- Boundary decision: this closes one C2 full-episode recovery regression. The
  tested `LeaderTrainingEnv` still imports Gym/Torch and uses C2 ownership in
  `python.rl.tasking`. No-RL C2 command/report closure, broader seed coverage,
  visualization, and the full Air `playable` gate remain open.

### 2026-09-26 — Neutral decision-model registry and explicit model-kind gate

- Starting commit: `8f856d70`.
- Change batch: move the canonical registry implementation from
  `common/scripted_registry.py` to `common/decision_registry.py` and rename its
  contract to `DecisionModel`/`DecisionModelRegistration`/`DecisionModelRegistry`.
  The old module and names are removed, with no compatibility forwarding shell
  or parallel RL registry. Registration now requires an explicit kind:
  `scripted`, `learned`, `human`, or `hybrid`.
- Selection rule: role/domain/status/kind filtering is explicit; omitted kind
  with multiple eligible registrations fails closed. The existing
  `DecisionRuntimeRoster` requests `model_kind="scripted"`, so it cannot
  silently instantiate a learned, human, or hybrid entry.
- Evidence: pure-registry tests exercise all four kinds with stub factories,
  ambiguous selection, explicit-ID mismatch, and unknown-kind rejection.
  After the explicit-kind edit, architecture, scripted runtime, Air, and Naval
  regressions passed `85 passed` with the local `CMO_BUILD_DIR` binding.
  Before that final declaration edit, cooperative Air/EW/replay/evaluation
  regressions passed `22 passed, 2 skipped, 18 subtests passed`. Python
  compilation and `git diff --check` passed. The neutral registry imports no
  RL, Gym, or world-step implementation.
- Boundary decision: this establishes one shared model-selection seam, not
  production learned/human/hybrid providers or an interchangeable runtime.
  Air/Naval/Joint registered implementations remain scripted; the full no-RL
  C2 command/report loop and cross-kind scenario execution remain open.

### 2026-09-27 — Neutral agent contract ownership moved out of RL runtime

- Starting commit: `ecc0f81d`.
- Change batch: move the Python-side `AgentRole`, `DecisionBelief`,
  `ObservationProvenance`, `ActionIntent`, and `CoordinationIntent` contracts
  from `python/rl/runtime/agent_shim.py` to
  `python/tasking_contracts/common/agent_contracts.py`. The old module and
  package export are removed; no compatibility forwarding shell remains.
- Consumer update: the world-batch authorization adapter now imports the
  neutral contract vocabulary directly. Architecture and runtime tests were
  moved to the neutral path, and package boundaries continue to enforce
  `gym_envs -> python/tasking_contracts <- python.rl`.
- Evidence: focused contract, provenance, authority, and dependency-boundary
  tests passed `65 passed` with the local `CMO_BUILD_DIR` binding.
- Boundary decision: this removes RL ownership of the common role, belief,
  provenance, and intent contracts. It does not yet remove RL ownership from
  world-batch execution, C2 phase management, or Gym environment adapters.
  The next runtime slice must preserve compiled authorization and provenance
  gates while adding a non-RL scenario entry point.

### 2026-09-27 — Decision runtime unified across model kinds

- Starting commit: efb3e379.
- Change batch: rename the dependency-terminal scheduler from
  common/scripted_runtime.py to common/decision_runtime.py and remove the old
  module path. DecisionRuntimeAgent, DecisionRuntimeRoster, report, step,
  and scheduling constants now describe the neutral lifecycle rather than a
  scripted-only runtime.
- Runtime selection: DecisionRuntimeAgentSpec.model_kind is validated against the
  shared DecisionModelRegistry vocabulary; roster construction forwards the declared
  kind instead of forcing scripted. A learned stub and a scripted model both run
  through the same reset, decide, hold, report, and close path in regression tests.
- Evidence: decision-runtime, cross-domain tasking, Joint, Air, Naval, and
  entry-point tests passed 16 passed for the focused runtime batch; Python
  compilation passed. Existing diagnostic JSON keys remain unchanged because
  they are output-schema fields, not runtime ownership names.
- Boundary decision: this unifies model lifecycle scheduling without importing
  RL, Gym, NumPy, native bindings, or world stepping. Actual learned policy
  providers and the non-RL scenario/world adapter remain separate open work.

### 2026-09-27 — Neutral simulation backend selection boundary

- Starting commit: `aad3fe78`.
- Change batch: add `python/simulation/backend.py` and its package export as a
  dependency-light simulation backend boundary. It defines the lifecycle
  protocol and explicit backend registration without importing RL, Gym, NumPy,
  or native bindings. The existing WorldBatch single/cooperative providers are
  loaded lazily only when `create_single_backend` or
  `create_cooperative_backend` opens an episode.
- Consumer update: Air combat, Air EW, cooperative Air combat/EW, and Naval N4
  scripted entry points now construct the selected backend through
  `python.simulation`; they no longer import `python.rl.runtime` directly.
  The current default provider remains `world_batch`, so this is an ownership
  and dependency boundary, not a claim that a second native backend already
  exists.
- Evidence: backend import-laziness, registration, and entrypoint boundary
  tests plus tasking/scripted-entry regressions passed `54 passed`; the focused
  runtime and Air diagnostics passed `49 passed, 2 skipped, 18 subtests
  passed`. Python compilation and `git diff --check` passed. The first test
  invocation without `CMO_BUILD_DIR` stopped at the known local-`ef_py`
  bootstrap guard and was rerun with the maintained local build binding.
- Boundary decision: scripted and learned decision models now depend on a
  simulation selection seam rather than a direct RL package path. The default
  provider is still RL-owned and remains an open migration target for a native
  or otherwise independent simulation provider; this batch does not promote
  full no-RL scenario execution or Air `playable` status.

### 2026-09-27 — Air trajectory entry routed through simulation boundary

- Starting commit: `a12d287e`.
- Change batch: route the maintained `takeoff_to_landing` scripted/learned
  trajectory entry through `create_single_execution_runtime`. The backend
  contract now distinguishes direct batch providers from the single-world
  execution wrapper, and accepts an execution-only provider for future native
  or alternate simulation implementations.
- Evidence: the backend boundary, Air CLI, and decision-runtime regressions
  passed `13 passed`; Python compilation and `git diff --check` passed. A
  compiled five-step scripted run through the new execution factory exited 0,
  produced the expected scripted report, and wrote the plot/summary under the
  ignored `build-scripted-agent` directory.
- Boundary decision: the trajectory entry no longer imports
  `python.rl.runtime.single_world_batch_runtime` directly. The default
  `world_batch` provider still lazily loads that RL-owned implementation when
  requested, so this closes the entry-point dependency edge but does not yet
  prove an independent no-RL world implementation or full Air playable
  promotion.

### 2026-09-27 — Air C2 transition policy extraction

- Starting commit: `6ca58df3`.
- Change batch: extract the pure `SCRAMBLE -> CAP -> RTB -> RECOVER_LAND`
  transition algorithm into
  `python/tasking_contracts/air/tasking/c2_policy.py`. The policy consumes a
  typed information-state projection and returns only next task, transition
  provenance, and station-timer state. It does not read a loader, author a
  command, touch a kernel, or import RL/native/runtime adapters.
- Consumer update: the maintained `ScriptedC2TaskManager` injects the default
  `ScriptedC2TransitionPolicy` and passes the existing report, geometry,
  route-exhaustion, and readiness products into it. Task DTO projection,
  command-chain synchronization, and domain report ownership remain in the
  existing manager.
- Substitution/evidence: the policy tests cover scramble thresholds, station
  timer completion, report-triggered RTB, route-exhaustion precedence, and
  recovery-window gating. Air tasking physical-layer tests enforce no RL/Gym/
  native/NumPy imports. Existing leader/tasking/bridge tests passed `34 passed,
  4 subtests passed`; Python compilation and `git diff --check` passed.
- Boundary decision: this closes one replaceable Air C2 algorithm seam and
  proves the transition logic is independent of RL. It does not yet relocate
  the full DTO-producing manager from `python.rl.tasking`, nor does it claim
  no-RL scenario execution or final Air `playable` promotion.

### 2026-09-27 — Air C2 information assessment extraction

- Starting commit: `a886bf79`.
- Change batch: move station-entry assessment, pilot-report validity, and
  recovery-window geometry gating into the RL-independent
  `python/tasking_contracts/air/tasking/c2_observation.py` module. The module
  accepts declared scalar/object projections and injected report enum values;
  it does not read a loader, mutate DTOs, import RL/Gym/native bindings, or
  resolve compiled enums.
- Consumer update: `ScriptedC2TaskManager` remains the runtime adapter, but now
  only collects loader observations, supplies compiled report codes, and
  projects the pure results into its existing task/report state. The default
  thresholds and report reasons are preserved.
- Substitution/evidence: pure tests cover station geometry, invalid station
  and bingo reports, and recovery geometry gates. The C2, leader, tasking,
  bridge, and physical-layer regressions passed `76 passed, 4 subtests
  passed`; Python compilation and `git diff --check` passed.
- Boundary decision: three additional C2 algorithms now have an independent
  substitution seam. The DTO-producing manager, common-core task-order
  profile, and default WorldBatch provider remain open RL-owned adapter
  surfaces; this batch does not claim no-RL scenario execution or Air
  `playable` promotion.

### 2026-09-27 — Air C2 task-order projection port

- Starting commit: `6394be9d`.
- Change batch: add the RL-independent `C2TaskOrderProjection` protocol under
  `python/tasking_contracts/air/tasking/task_order_projection.py`. Move the
  compiled Air task-order mutation and common-core profile application into
  the explicit `python/rl/tasking/air_c2_task_order_projection.py` adapter.
- Consumer update: `ScriptedC2TaskManager` accepts and validates an injected
  projection and no longer owns `_retask_order` or its route-block mutation
  helpers. Existing callers use the default compiled adapter; tests also prove
  a recording projection can replace it at the manager boundary.
- Evidence: Air tasking/profile, manager runtime, bridge, and physical-layer
  tests passed `69 passed, 4 subtests passed`; Python compilation and
  `git diff --check` passed. An initial test run exposed three tests calling
  the removed private manager method; those tests were migrated to the public
  projection port before the passing rerun.
- Boundary decision: task-order DTO ownership is now explicit at an adapter
  boundary, but the default adapter still depends on RL profile/common-core
  code and compiled bindings. The full C2 manager migration and independent
  no-RL simulation provider remain open.

### 2026-09-27 — Air C2 manager moved to the neutral tasking layer

- Starting commit: `86f721c2`.
- Change batch: move `ScriptedC2TaskManager` state, observation collection,
  recovery readiness, report assessment, and transition orchestration into
  `python/tasking_contracts/air/tasking/c2_manager.py`. The manager now
  requires injected `C2ReportTypeCodes` and `C2TaskOrderProjection` ports;
  its implementation contains no RL, Gym, native-binding, or compiled-enum
  import.
- Adapter update: `python/rl/tasking/air_adapter.py` is now the explicit
  compiled Air adapter. It binds report enum values and the task-order
  projection before constructing the neutral manager. The generic bridge
  fails closed for profiles without a domain factory, and Ground/Naval
  adapters no longer re-export the Air-only manager.
- Consumer update: internal tests now import the neutral manager for constants
  and obtain runtime instances through the Air factory. The RL leader module
  retains only a private constant reference for phase gating and no longer
  exposes the manager as an RL-owned symbol.
- Evidence: Air physical-layer, leader/tasking/profile, architecture boundary,
  and mission-runtime tests passed `179 passed, 10 subtests passed`; Python
  compilation and `git diff --check` passed with the maintained local
  `CMO_BUILD_DIR` binding. A test run without that binding remains rejected by
  the repository's local-`ef_py` fail-closed guard.
- Boundary decision: C2 state-machine ownership is now neutral and can be
  supplied to the simulator independently of RL. The compiled Air adapter,
  common-core profile, WorldBatch provider, and a complete no-RL playable
  scenario remain open; this batch does not claim final Air `playable`
  promotion.

### 2026-09-27 — Air leader-phase policy extraction

- Starting commit: `680d566e`.
- Change batch: add the RL-independent
  `python/tasking_contracts/air/tasking/leader_phase_policy.py` policy seam.
  It maps normalized command, route, altitude, speed, DME, and ground-state
  facts to `scramble`, `takeoff`, `departure`, `transit_to_station`, `rtb`,
  `approach_armed`, `landing_final`, or `rollout` without reading a loader,
  constructing DTOs, resolving compiled enums, or importing RL/Gym code.
- Consumer update: `RuleBasedLeaderPhaseManager` now injects a
  `LeaderPhasePolicy` and passes a typed `LeaderPhaseInput` to the default
  `ScriptedLeaderPhasePolicy`. Its former inline `_infer_phase_name` algorithm
  was removed; command/report projection and kernel synchronization remain in
  the runtime adapter.
- Evidence: pure phase-policy, Air physical-layer, leader/tasking/profile, and
  mission-runtime regressions passed `196 passed, 10 subtests passed`; Python
  compilation and `git diff --check` passed with the maintained local
  `CMO_BUILD_DIR` binding.
- Boundary decision: phase selection is now independently replaceable at the
  algorithm layer. The leader DTO projection, common-core profile, compiled
  Air adapter, WorldBatch provider, and complete no-RL playable command/report
  scenario remain open; this batch does not promote Air beyond
  `playable_candidate`.

### 2026-09-27 — Air leader approach gate extraction

- Starting commit: `231eed9f`.
- Change batch: add the RL-independent
  `python/tasking_contracts/air/tasking/leader_approach_policy.py` gate for
  post-waypoint landing entry. It evaluates task admission, landing command
  identity, route exhaustion, ILS validity, DME/localizer/glide-slope limits,
  runway heading, and runway-frame geometry from a typed input.
- Consumer update: `RuleBasedLeaderPhaseManager` now collects loader-owned ILS,
  beacon, and runway-frame facts, injects `LeaderApproachPolicy`, and delegates
  the pure gate. The existing recovery-task readiness callback and fail-closed
  terminal geometry behavior are preserved in the adapter.
- Evidence: Air tasking policy, physical-layer, leader/profile, and mission
  runtime regressions passed `213 passed, 10 subtests passed`; Python
  compilation and `git diff --check` passed with the maintained local
  `CMO_BUILD_DIR` binding.
- Boundary decision: phase and approach selection are now separate neutral
  algorithms. DTO construction, common-core normalization, compiled tasking
  projection, WorldBatch execution, and complete no-RL playable command/report
  closure remain open; Air stays `playable_candidate`.

### 2026-09-27 — Simulation-side compiled Air C2 adapter

- Starting commit: `ede77ea6`.
- Change batch: add `python/simulation/air/tasking.py` as a compiled simulation
  adapter for the neutral `ScriptedC2TaskManager`. It binds `ef_py` report
  codes, creates a missing `TaskOrder`, projects Air task types and route
  blocks, preserves authored common task-order fields, and applies Air
  defaults. The adapter imports neither RL packages nor environment packages.
- Consumer/test update: add the physical boundary test and a simulation-side
  factory smoke test. The neutral manager can now be instantiated from a
  simulation package without importing `python.rl`; the existing RL adapter
  remains in place until full consumer migration and parity evidence are
  complete.
- Evidence: focused simulation and boundary tests passed `4 passed`; the
  related architecture, leader, Air tasking, mission, and simulation suite
  passed `216 passed, 10 subtests passed`; Python compilation and
  `git diff --check` passed. A field-level probe matched the existing compiled
  projection for populated orders across `TASK_CAP`, `TASK_SCRAMBLE`,
  `TASK_RTB`, and `TASK_RECOVER_LAND` when no authored override is being
  re-applied.
- Boundary decision: the simulation-side DTO adapter is now a concrete
  no-RL construction path for Air C2, but it does not yet replace the RL
  adapter, remove the RL-owned common-core profile, or prove a complete no-RL
  playable scenario. Air remains `playable_candidate`; the next closure is
  adapter migration plus command/report execution evidence.

### 2026-09-27 — RL Air entry delegates C2 projection to simulation

- Starting commit: `91c6883c`.
- Change batch: update `python/rl/tasking/air_adapter.py` so its maintained
  C2-manager entry injects `CompiledAirC2TaskOrderProjection` from
  `python/simulation/air/tasking.py`. Existing RL-facing call sites remain
  source-compatible, while compiled Air task-order DTO ownership moves to the
  simulation adapter. The old RL projection file remains only for the leader
  task-order override helper and is not deleted in this batch.
- Regression repair: the simulation adapter now matches the existing
  common-core force-refresh semantics for task family and coordination mode;
  this preserves `CAP -> RTB` retasking behavior and authored field handling.
- Evidence: the focused leader/profile/physical-layer/simulation batch passed
  `43 passed`; the related architecture, leader, Air tasking, mission, and
  simulation suite passed `217 passed, 10 subtests passed`; Python
  compilation and `git diff --check` passed.
- Boundary decision: the RL entry no longer selects the RL-owned compiled C2
  projection by default. The RL profile/common-core surface, leader task-order
  override helper, WorldBatch provider, and complete no-RL command/report
  playable episode remain open; Air stays `playable_candidate`.

### 2026-09-27 — Remove the duplicate RL Air C2 projection module

- Starting commit: `e853de84`.
- Change batch: move the remaining authored task-order override helper into
  `python/simulation/air/tasking.py`, update the Air leader and cooperative
  world director consumers, and delete the unused
  `python/rl/tasking/air_c2_task_order_projection.py` module. This removes the
  duplicate compiled DTO implementation rather than retaining a forwarding
  compatibility shell.
- Evidence: the focused leader/profile/cooperative/simulation/tasking-contract
  suite passed `106 passed`; Python compilation and `git diff --check` passed.
  A broader command that included legacy runtime-facade path tests reported
  four unrelated failures because those tests still read the removed
  `python/tasking_contracts/bridge_views.py` path instead of the maintained
  `python/tasking_contracts/common/bridge_views.py` location; no Air migration
  test failed.
- Boundary decision: compiled Air C2 task-order projection and authored
  overrides now have one simulation-side owner. The RL common-core profile,
  leader DTO construction, WorldBatch provider, and complete no-RL playable
  episode remain open; Air stays `playable_candidate`.

### 2026-09-27 — Restore canonical bridge architecture test path

- Starting commit: `e9e604e1`.
- Change batch: update the runtime-facade architecture test helper to read the
  maintained `python/tasking_contracts/common/bridge_views.py` location after
  the earlier physical-layer move removed the old flat path.
- Evidence: `tests/architecture/runtime_facade/test_runtime_escape_hatches.py`
  passed `28 passed`; this is a test-path correction only and does not change
  runtime behavior.
- Boundary decision: the runtime-facade escape-hatch gate is green again; it
  does not alter the open no-RL WorldBatch provider or Air playable boundary.
