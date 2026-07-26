"""G4 per-file maintained truth-reader classification (Unified Architecture Program T8).

The T8 gate-net hardening slice (I63) closed the "new unregistered consumer with
raw World-Truth reads" escape only for ``gym_envs/scenario_loader/reward_runtime/**``
-- a clean, bounded package holding only reward consumers -- and recorded the
broader observation surfaces as an open escape hatch: those directories
interleave legitimate non-consumer truth readers (command / action / loading /
behavior paths), so a bare directory-level "no unregistered raw reads" scan
would false-positive on them.

This module (this iteration) closes that recorded escape hatch with the per-file
maintained-consumer classifier the I63 register asked for: every maintained file
on the scanned surface that performs a raw World-Truth read (``truth.<attr>`` or
``getattr(truth, ...)``, minus explicitly marked diagnostic reads) is classified
here, per file, into one of four roles. The companion architecture gate
(``tests/architecture/information_state/test_g4_consumer_classification.py``)
AST-scans the surface and enforces, in both directions, that the scan hits and
this registry agree exactly -- so an injected unregistered truth reader goes red
(it has no classification row) and a stale row goes red (its file no longer
reads truth). Extension is registration (G5): a new legitimate truth reader is
added here with a category, in a reviewable diff; nothing is inferred.

Categories
----------

* ``observation-consumer`` -- the file's raw truth reads feed policy/agent
  observation content (G4 "Agent Observation" assembly paths).
* ``reward-consumer`` -- the file's raw truth reads feed reward-input assembly.
* ``command-action-loading-reader`` -- the file's raw truth reads serve command
  delivery, action gating/masking, behavior-phase transitions, or scenario
  loading/reset seeding. These are the legitimate non-consumer readers the I63
  register warned a naive directory scan would mislabel; classifying them here
  is exactly what lets the scan extend beyond ``reward_runtime/`` without
  flagging them as observation consumers.
* ``diagnostics`` -- a file whose raw truth reads exist only as diagnostic
  probes (design doc §15: diagnostics may read truth directly). No maintained
  file currently needs a whole-file diagnostics classification -- single
  diagnostic reads inside otherwise-clean files use the inline
  ``g4-diagnostic-truth-read`` marker instead -- but the category is part of
  the authoritative vocabulary so a future dedicated probe module registers
  instead of inventing a name.
* ``declared-view-owner`` -- the declared observation-view read owner
  (``MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS`` in
  :mod:`python.architecture.information_layer`): the one place raw truth reads
  legitimately live on behalf of the converged consumers.

Structural cross-checks (the "classification lie" net)
------------------------------------------------------

Where a classified file carries a G4 declaration (the three module-level
constants from :data:`python.architecture.information_layer.REQUIRED_DECLARATION_ATTRS`),
its declared ``SEMANTIC_STAGE`` pins the classification structurally:

* a declaration including ``P10 ObservationExport`` marks an observation/reward
  consumer -- classifying that file as ``command-action-loading-reader`` (or
  ``diagnostics``) is a lie and goes red;
* a declaration *without* ``P10 ObservationExport`` (e.g. the scripted C2
  leader director, declared on ``P2 TaskingIntent`` / ``P3 CommandDelivery``)
  marks a command-path reader -- classifying it as an observation/reward
  consumer goes red.

Files without a G4 declaration cannot be stage-checked; their category is a
registry assertion reviewed at registration time. That is the documented limit
of "structurally checkable" for this slice.

G4-declaration follow-up
------------------------

Classification here is not a substitute for a G4 declaration. Classified
observation/reward consumers that are not yet registered in
``MAINTAINED_INFORMATION_LAYER_CONSUMERS`` are pinned, exactly, in
:data:`G4_DECLARATION_PENDING_CONSUMERS`; the gate fails if that set drifts in
either direction, so a new observation/reward consumer cannot be classified
without either carrying a G4 declaration or growing the pinned pending list in
a reviewable diff. Migrating any reads is out of scope for this slice (no
production read migration); a later slice settles the pending declarations.

This module is import-time stdlib-only and imports nothing from ``gym_envs`` or
``python.rl``; the pure validator below takes every repo fact as a parameter so
the gate can tamper-test it against in-memory copies without touching the tree.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence


# --- Authoritative category vocabulary ---------------------------------------

OBSERVATION_CONSUMER = "observation-consumer"
REWARD_CONSUMER = "reward-consumer"
COMMAND_ACTION_LOADING_READER = "command-action-loading-reader"
DIAGNOSTICS = "diagnostics"
DECLARED_VIEW_OWNER = "declared-view-owner"

CONSUMER_CLASSIFICATION_CATEGORIES: frozenset[str] = frozenset({
    OBSERVATION_CONSUMER,
    REWARD_CONSUMER,
    COMMAND_ACTION_LOADING_READER,
    DIAGNOSTICS,
    DECLARED_VIEW_OWNER,
})

# The categories that mark a G4 observation/reward consumer in the sense of
# Kernel Invariant G4 ("every observation/reward consumer declares its
# information-state layer").
OBSERVATION_REWARD_CONSUMER_CATEGORIES: frozenset[str] = frozenset({
    OBSERVATION_CONSUMER,
    REWARD_CONSUMER,
})

# The canonical semantic-stage string that structurally marks a G4 declaration
# as observation/reward-relevant. Kept as a literal so this module stays free of
# non-stdlib imports; the gate cross-checks it against
# ``python.architecture.information_layer.CANONICAL_SEMANTIC_STAGES`` so it
# cannot silently drift from the authoritative vocabulary.
OBSERVATION_EXPORT_STAGE = "P10 ObservationExport"


# --- Scanned surface ----------------------------------------------------------

# Repo-relative package roots the classifier gate scans for raw World-Truth
# reads. This is the maintained observation/reward surface the I63 register
# named (mission_observation, universal_env_parts, leader_env_parts,
# navigation_runtime, ...) plus the python.rl runtime/tasking paths, i.e. a
# strict superset of the reward_runtime/ directory the I63 escape-hatch scan
# covers.
SCANNED_SURFACE_PACKAGES: tuple[str, ...] = (
    "gym_envs",
    "python/rl",
)

# Path components excluded from the scan: generated DTO builders are not
# hand-maintained files (their generator is the maintained source, and they
# hold no raw truth reads today), and bytecode caches are not sources.
SCANNED_SURFACE_EXCLUDED_PARTS: tuple[str, ...] = (
    "_generated",
    "__pycache__",
)


# --- The per-file classification registry (G5: extension is registration) -----

MAINTAINED_TRUTH_READER_CLASSIFICATION: dict[str, str] = {
    # The declared observation-view read owner: raw truth reads live here on
    # behalf of the converged consumers (ban-gated elsewhere).
    "gym_envs.observation_view": DECLARED_VIEW_OWNER,

    # G4-registered declared-but-deferred consumers (the I56 adjudication,
    # settled in the I63 register). Their declarations include
    # "P10 ObservationExport", which structurally pins these categories.
    "gym_envs.scenario_loader.step_evaluation": REWARD_CONSUMER,
    "gym_envs.scenario_loader.execution_runtime.mainline": OBSERVATION_CONSUMER,
    "gym_envs.scenario_loader.navigation_runtime.guidance": REWARD_CONSUMER,

    # G4-registered declared-but-deferred reader on the command stages: the
    # scripted C2/leader director. Its declaration (P2 TaskingIntent /
    # P3 CommandDelivery, no P10) structurally pins it as a command-path
    # reader, exactly the adjudication recorded in the I63 register (migration
    # forbidden: routing its reads through gym_envs.observation_view would
    # create a python.rl -> gym_envs reverse dependency).
    "python.rl.tasking.leader_tasking": COMMAND_ACTION_LOADING_READER,

    # Maintained observation consumers not yet carrying a G4 declaration
    # (pinned in G4_DECLARATION_PENDING_CONSUMERS below): batch execution /
    # mission observation assembly reads own-ship truth x/y to build the ILS
    # observation input.
    "python.rl.runtime.world_batch._vec_env_support": OBSERVATION_CONSUMER,
    "python.rl.runtime.world_batch.observation_batching": OBSERVATION_CONSUMER,

    # Command / action / loading / behavior readers -- the legitimate
    # non-consumer truth readers the I63 register said a directory scan would
    # mislabel. None carries a G4 declaration; each category below is a
    # registry assertion reviewed at registration time.
    #
    # Leader decision-runtime command construction: own-ship/station geometry
    # and runway/ILS frame reads that gate which commands are emitted.
    "gym_envs.leader_env_parts.decision_runtime.commands": COMMAND_ACTION_LOADING_READER,
    # Behavior-phase transition gating after waypoint completion (runway
    # frame / ILS checks deciding a phase change, not observation content).
    "gym_envs.scenario_loader.behavior_runtime.post_waypoint_transition": COMMAND_ACTION_LOADING_READER,
    # Scenario loading/reset: one-shot load-time reads seeding baselines
    # (prev altitude, initial missile count, waypoint leg origin) during
    # P1 WorldSetup; the per-step consumers of those baselines are the
    # registered reward consumers, not this loader path.
    "gym_envs.scenario_loader.loading": COMMAND_ACTION_LOADING_READER,
    # Air-combat event-action masking: reads target-track presence and
    # missiles-remaining to gate/mask actions, not to build observations.
    "gym_envs.universal_env_parts.air_combat_event_action": COMMAND_ACTION_LOADING_READER,
    # Batch vec-env command-chain gating: reads last-truth health to decide
    # whether the command-chain entity is still active.
    "python.rl.runtime.world_batch.vec_env": COMMAND_ACTION_LOADING_READER,
}

# Classified observation/reward consumers not yet registered in
# ``MAINTAINED_INFORMATION_LAYER_CONSUMERS`` (no G4 declaration yet). Pinned
# exactly: the gate fails if a classified observation/reward consumer is
# missing from both the G4 registry and this tuple, and fails if an entry here
# stops being a classified unregistered consumer (registered, reclassified, or
# no longer reading truth). Settling these declarations is a later slice.
G4_DECLARATION_PENDING_CONSUMERS: tuple[str, ...] = (
    "python.rl.runtime.world_batch._vec_env_support",
    "python.rl.runtime.world_batch.observation_batching",
)


# --- Pure validator (no I/O; every repo fact arrives as a parameter) ----------

def classification_violations(
    *,
    raw_truth_readers: Sequence[str],
    classification: Mapping[str, str],
    g4_registered_consumers: Sequence[str],
    g4_view_owners: Sequence[str],
    declared_semantic_stages: Mapping[str, Sequence[str]],
    declaration_pending: Sequence[str] = G4_DECLARATION_PENDING_CONSUMERS,
) -> list[str]:
    """Return human-readable violations for one classification state.

    An empty list means the classification is complete and honest with respect
    to the supplied facts:

    * ``raw_truth_readers`` -- dotted modules the AST scan flagged as
      performing raw World-Truth reads on the scanned surface;
    * ``classification`` -- the per-file registry (normally
      :data:`MAINTAINED_TRUTH_READER_CLASSIFICATION`, or an in-memory tamper
      copy under test);
    * ``g4_registered_consumers`` / ``g4_view_owners`` -- the
      :mod:`python.architecture.information_layer` registries;
    * ``declared_semantic_stages`` -- dotted module -> its module-level
      ``SEMANTIC_STAGE`` tuple, for exactly the scanned files that declare one.

    Pure function: no imports, no filesystem access, deterministic output, so
    the gate can rehearse tampered inputs without touching the working tree.
    """
    violations: list[str] = []
    readers = set(raw_truth_readers)
    registered = set(g4_registered_consumers)
    owners = set(g4_view_owners)

    # (1) Category vocabulary.
    for dotted, category in sorted(classification.items()):
        if category not in CONSUMER_CLASSIFICATION_CATEGORIES:
            violations.append(
                f"{dotted}: unknown classification category {category!r} "
                f"(authoritative vocabulary: {sorted(CONSUMER_CLASSIFICATION_CATEGORIES)})"
            )

    # (2) Completeness: every raw truth reader is classified. This is the
    # escape-hatch closure -- an injected unregistered consumer lands here.
    for dotted in sorted(readers - set(classification)):
        violations.append(
            f"{dotted}: performs raw World-Truth reads on the maintained surface but has "
            "no entry in MAINTAINED_TRUTH_READER_CLASSIFICATION -- classify it "
            "(observation/reward consumer, command-action-loading reader, or diagnostics), "
            "or route its reads through the declared observation view"
        )

    # (3) No stale rows: every classified file still reads truth. A converged
    # or deleted reader must drop its row, keeping the registry honest.
    for dotted in sorted(set(classification) - readers):
        violations.append(
            f"{dotted}: classified as a raw World-Truth reader but the scan found no raw "
            "truth reads there -- remove the stale classification row (if it converged onto "
            "the observation view, the G4 converged registry is the right place for it)"
        )

    # (4) View-owner cross-check, both directions.
    for dotted, category in sorted(classification.items()):
        if category == DECLARED_VIEW_OWNER and dotted not in owners:
            violations.append(
                f"{dotted}: classified as {DECLARED_VIEW_OWNER!r} but is not in "
                "MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS -- only the declared read owner "
                "may carry that classification"
            )
        if dotted in owners and category != DECLARED_VIEW_OWNER:
            violations.append(
                f"{dotted}: is a declared observation-view owner but classified as "
                f"{category!r}; the read owner must be classified {DECLARED_VIEW_OWNER!r}"
            )

    # (5) Declaration-stage lie check, where structurally checkable: a G4
    # declaration pins the file's role via its SEMANTIC_STAGE.
    for dotted, category in sorted(classification.items()):
        stages = declared_semantic_stages.get(dotted)
        if stages is None or category == DECLARED_VIEW_OWNER:
            continue
        exports_observation = OBSERVATION_EXPORT_STAGE in tuple(stages)
        if exports_observation and category not in OBSERVATION_REWARD_CONSUMER_CATEGORIES:
            violations.append(
                f"{dotted}: declares SEMANTIC_STAGE including {OBSERVATION_EXPORT_STAGE!r} "
                f"but is classified {category!r} -- an observation/reward consumer may not "
                "be labeled a command/loading/diagnostics reader"
            )
        if not exports_observation and category in OBSERVATION_REWARD_CONSUMER_CATEGORIES:
            violations.append(
                f"{dotted}: is classified {category!r} but its declared SEMANTIC_STAGE "
                f"{tuple(stages)!r} does not include {OBSERVATION_EXPORT_STAGE!r} -- a "
                "command-stage reader may not be labeled an observation/reward consumer"
            )

    # (6) A G4-registered consumer is never a whole-file diagnostics probe.
    for dotted, category in sorted(classification.items()):
        if dotted in registered and category == DIAGNOSTICS:
            violations.append(
                f"{dotted}: is registered in MAINTAINED_INFORMATION_LAYER_CONSUMERS but "
                f"classified {DIAGNOSTICS!r} -- a registered consumer is not a diagnostic probe"
            )

    # (7) Pending-declaration pinning, both directions: classified
    # observation/reward consumers must be G4-registered or pinned as pending.
    pending = set(declaration_pending)
    unregistered_consumers = {
        dotted
        for dotted, category in classification.items()
        if category in OBSERVATION_REWARD_CONSUMER_CATEGORIES and dotted not in registered
    }
    for dotted in sorted(unregistered_consumers - pending):
        violations.append(
            f"{dotted}: classified as an observation/reward consumer but neither registered "
            "in MAINTAINED_INFORMATION_LAYER_CONSUMERS nor pinned in "
            "G4_DECLARATION_PENDING_CONSUMERS -- register a G4 declaration for it, or grow "
            "the pinned pending list in a reviewed diff"
        )
    for dotted in sorted(pending - unregistered_consumers):
        violations.append(
            f"{dotted}: pinned in G4_DECLARATION_PENDING_CONSUMERS but is no longer a "
            "classified unregistered observation/reward consumer -- prune the stale pin"
        )

    return violations


__all__ = [
    "COMMAND_ACTION_LOADING_READER",
    "CONSUMER_CLASSIFICATION_CATEGORIES",
    "DECLARED_VIEW_OWNER",
    "DIAGNOSTICS",
    "G4_DECLARATION_PENDING_CONSUMERS",
    "MAINTAINED_TRUTH_READER_CLASSIFICATION",
    "OBSERVATION_CONSUMER",
    "OBSERVATION_EXPORT_STAGE",
    "OBSERVATION_REWARD_CONSUMER_CATEGORIES",
    "REWARD_CONSUMER",
    "SCANNED_SURFACE_EXCLUDED_PARTS",
    "SCANNED_SURFACE_PACKAGES",
    "classification_violations",
]
