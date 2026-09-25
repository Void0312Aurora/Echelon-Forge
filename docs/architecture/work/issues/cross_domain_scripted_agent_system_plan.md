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

Initial runtime slice: `python/tasking_contracts/scripted_runtime.py` now owns
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
  `ScriptedRuntimeAgent`/`ScriptedRuntimeRoster` scheduler in
  `python/tasking_contracts/scripted_runtime.py`. It reuses the existing
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
  through `ScriptedRuntimeAgent` while preserving the learned-policy wrapper
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
  `ScriptedRuntimeAgent` while preserving the existing station command,
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
  `ScriptedRuntimeRoster`. The test uses the real domain registries and keeps
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
- Direct result: the producer ran through `ScriptedRuntimeAgent` with seed
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
  execution entry through `ScriptedRuntimeAgent`. The adapter now carries the
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
  `ScriptedRuntimeAgent`, drives the compiled `WorldBatchVecEnv`, and emits a
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
