"""Registered agency & doctrine vocabulary (T9 slice 1: census + registry).

This module is the single declarative owner of the *authority model vocabulary*
for the maintained tasking surface: the roles, authority scopes, delegation
relationships, arbitration policies, and command-chain activation gates that
today live as scattered ``if`` checks, field plumbing, and prose conventions
across ``python.rl.tasking``, ``python.rl.profile``, and ``gym_envs`` (see the
[Agency Authority Census](../../docs/systems/command-tasking/reference/agency_authority_census_20260721.md)).

Design constraints (Unified Architecture Program, track T9 slice 1):

- **G5 "extension is registration".** The vocabulary is declared here once as
  frozen data; a future consumer names a role/scope/relationship by referencing
  these constants rather than re-deriving them inline. This is the pure-
  declaration precursor to the eventual single Agency-graph entry.
- **Vocabulary is aligned, not invented.** Every term mirrors the architecture
  authority (``docs/architecture/standards/simulation_system_architecture_design.md``
  Agency face -- the five-part ``AgentRole`` schema, the ``merge_policy`` and
  source-priority ordering, and the ``DoctrineFamily`` extension family) and the
  compiled contracts: the tasking enums
  (``src/components/tasking/common/core_tasking_enums.h`` and
  ``src/components/domains/naval/tasking/naval_tasking_enums.h``) and the WP12
  ``AgentRole`` authority model (``src/runtime/contracts/policy_contracts.h``).
  The companion gate parses those headers and fails on any drift between the
  registry mirror and the compiled enum/scope values.
- **Pure-stdlib frozen declaration / zero C2 behavior change.** This module has
  no import of ``ef_py``, ``python.rl``, or ``gym_envs``; it registers no
  callback, patches no call site, and wires nothing. Slice 1 (I47) declared and
  gated only. Two later name-ownership moves repointed a locally spelled
  vocabulary item at the constant that owns it, in the census-legal direction
  ``python.rl -> python.tasking_contracts``, each pinned byte-identically by a
  drift/equivalence test so no behavior changes: I53 pointed
  ``agent_shim.ALLOWED_MERGE_POLICIES`` at :data:`MERGE_POLICIES`, and I68
  pointed the A3 command-relationship / authority-scope default *names* at
  :data:`DEFAULT_COMMAND_RELATIONSHIP` / :data:`DEFAULT_AUTHORITY_SCOPE`
  (census EN/ZH §9). Converging the *behavior* of the remaining scattered call
  sites onto this vocabulary (and onto the compiled ``authorize_maintained_*``
  gates) stays deferred to later, domain-evidence-reviewed slices (T9's key
  risk: C2 semantics are research subject matter).

The companion architecture gate
(``tests/architecture/agency/test_authority_registry_gate.py``) pins the census
scatter fingerprint against this vocabulary and fails on any new unregistered
authority-check site (ratchet, I38 allowlist precedent), and asserts the
registry mirror matches the compiled enum/scope authorities.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


# --------------------------------------------------------------------------- #
# Census category vocabulary
# --------------------------------------------------------------------------- #
# Every scattered authority site found by the census is classified into one or
# more of these authority dimensions. A single site can express several
# dimensions at once (e.g. a default-inference site that also carries a
# leader-vs-mission precedence). ``undecided`` is the honest "待裁定" bucket for a
# site whose authority semantics are not yet adjudicated (bias to it rather than
# mis-classify).
CATEGORY_ROLE = "role"
CATEGORY_SCOPE = "scope"
CATEGORY_DELEGATION = "delegation"
CATEGORY_ARBITRATION = "arbitration"
CATEGORY_GATING = "gating"
CATEGORY_DOCTRINE = "doctrine"
CATEGORY_UNDECIDED = "undecided"

AUTHORITY_CATEGORIES: frozenset[str] = frozenset(
    {
        CATEGORY_ROLE,
        CATEGORY_SCOPE,
        CATEGORY_DELEGATION,
        CATEGORY_ARBITRATION,
        CATEGORY_GATING,
        CATEGORY_DOCTRINE,
        CATEGORY_UNDECIDED,
    }
)


# --------------------------------------------------------------------------- #
# SCAL Agency face: the five-part AgentRole schema
# --------------------------------------------------------------------------- #
# simulation_system_architecture_design.md: "Every maintained agent role
# declares role, authority_scope, information_state_source, decision_model_ref,
# and action_interface." Mirrored here as the canonical schema key ordering, and
# carried per-role by ``AuthorityRole`` below.
AGENT_ROLE_SCHEMA_FIELDS: tuple[str, ...] = (
    "role",
    "authority_scope",
    "information_state_source",
    "decision_model_ref",
    "action_interface",
)

# Sentinel for a five-part schema slot whose value the census has not yet
# adjudicated for a role (honest gap, not an invented value).
SCHEMA_UNSPECIFIED = "unspecified"


@dataclass(frozen=True)
class AuthorityRole:
    """A declared role on the maintained agency surface, carrying the SCAL
    five-part ``AgentRole`` schema.

    The five schema slots (``simulation_system_architecture_design.md``) are:

    - ``role`` -> :attr:`role_id`
    - ``authority_scope`` -> :attr:`authority_scope` (an ``ACTION_INTERFACE_SCOPES``
      value from ``policy_contracts.h``, or ``"unspecified"``)
    - ``information_state_source`` -> :attr:`information_state_layer`
    - ``decision_model_ref`` -> :attr:`decision_model_ref`
    - ``action_interface`` -> :attr:`action_interface` (a ``policy_contracts.h``
      action-interface kind, or ``"unspecified"``)

    Values are filled from census evidence; a slot is ``"unspecified"`` only
    where the site is a command-node identity / delegation holder rather than a
    compiled decision-model-bearing agent, and the :attr:`note` records why.

    ``authors`` / ``consumes`` name the contract packets or command fields the
    role is (today, by convention) permitted to write / read. They are declared
    documentation of the existing folklore, not an enforced ACL in this slice.
    """

    role_id: str
    label: str
    authority_scope: str
    information_state_layer: str
    decision_model_ref: str
    action_interface: str
    authors: tuple[str, ...]
    consumes: tuple[str, ...]
    note: str = ""

    def schema_values(self) -> tuple[str, str, str, str, str]:
        """Return the five-part ``AgentRole`` schema tuple for this role."""
        return (
            self.role_id,
            self.authority_scope,
            self.information_state_layer,
            self.decision_model_ref,
            self.action_interface,
        )


# Roles surfaced by the census. ``role_id`` values reuse the compiled
# ``policy_contracts.h`` ``role_type`` spellings where one exists so a later
# convergence slice can bind to the C++ AgentRole without renaming. The
# five-part schema slots use the ``policy_contracts.h`` action-interface scope /
# kind vocabulary (``ACTION_INTERFACE_SCOPES`` / ``ACTION_INTERFACE_KINDS``).
AUTHORITY_ROLES: Mapping[str, AuthorityRole] = MappingProxyType(
    {
        "autopilot_controller": AuthorityRole(
            role_id="autopilot_controller",
            label="Platform autopilot / direct-control agent",
            authority_scope="platform_control",
            information_state_layer="AgentObservation",
            decision_model_ref="external_policy",
            action_interface="PilotActionAssignment",
            authors=("ActionIntentPacket", "PilotActionAssignment"),
            consumes=("AgentObservation",),
            note="Canonical maintained AgentRole example; a learned policy that "
            "emits direct platform control (platform_control -> pilot_action).",
        ),
        "flight_lead": AuthorityRole(
            role_id="flight_lead",
            label="Scripted leader / phase manager (RuleBasedLeaderPhaseManager)",
            authority_scope="mission_command",
            information_state_layer="DecisionBelief",
            decision_model_ref="rule_based",
            action_interface="CommandChainAssignment",
            authors=("TaskOrder", "LeaderIntent", "PilotReport", "CoordinationIntentPacket"),
            consumes=("AgentObservation", "instrument_state"),
            note="Leader layer authors the low-level command chain (mission_command "
            "scope) the scripted C2 layer may not.",
        ),
        "scripted_c2": AuthorityRole(
            role_id="scripted_c2",
            label="Scripted C2 task-state manager (ScriptedC2TaskManager)",
            authority_scope=SCHEMA_UNSPECIFIED,
            information_state_layer="SharedTacticalPicture",
            decision_model_ref="rule_based",
            action_interface=SCHEMA_UNSPECIFIED,
            authors=("c2_task_name", "c2_task_id", "TaskOrder.task_type"),
            consumes=("shared situation data", "PilotReport"),
            note="Folklore rule: may consume situation + reports, MUST NOT author "
            "low-level mission commands (leader-layer authority). authority_scope "
            "and action_interface are 'unspecified': the C2 task-state layer has no "
            "compiled action-interface scope (it authors task-state fields, not the "
            "leader's mission_command).",
        ),
        "cooperative_director": AuthorityRole(
            role_id="cooperative_director",
            label="World-level cooperative coordination director",
            authority_scope="formation_coordination",
            information_state_layer="SharedTacticalPicture",
            decision_model_ref=SCHEMA_UNSPECIFIED,
            action_interface="CommandChainAssignment",
            authors=("mission_cmd formation slice", "LeaderIntent formation slice", "role metadata"),
            consumes=("cooperative roster", "leader_overrides"),
            note="Runtime-face owner (python/rl/runtime/world_batch); cross-referenced "
            "by the census, governed by the runtime face, not converged here. "
            "decision_model_ref is 'unspecified' pending that face's adjudication.",
        ),
        "officer_in_tactical_command": AuthorityRole(
            role_id="officer_in_tactical_command",
            label="Officer in tactical command (OTC delegation holder)",
            authority_scope=SCHEMA_UNSPECIFIED,
            information_state_layer="SharedTacticalPicture",
            decision_model_ref=SCHEMA_UNSPECIFIED,
            action_interface=SCHEMA_UNSPECIFIED,
            authors=("officer_in_tactical_command",),
            consumes=("task_group_id", "parent_node_id"),
            note="Delegation-holder command-node identity inferred from group/parent "
            "node identity, not a compiled decision-model-bearing agent; the "
            "action-interface schema slots stay 'unspecified'.",
        ),
        "ground_commander": AuthorityRole(
            role_id="ground_commander",
            label="Ground objective commander (ground_commander_id)",
            authority_scope=SCHEMA_UNSPECIFIED,
            information_state_layer="SharedTacticalPicture",
            decision_model_ref=SCHEMA_UNSPECIFIED,
            action_interface=SCHEMA_UNSPECIFIED,
            authors=("ground_commander_id",),
            consumes=("objective_area_id", "task_group_id"),
            note="Ground-profile command-node identity; identity/role carrier, not a "
            "compiled action-interface agent (schema slots 'unspecified').",
        ),
        "naval_warfare_commander": AuthorityRole(
            role_id="naval_warfare_commander",
            label="Naval warfare-role commander (NavalWarfareRole)",
            authority_scope=SCHEMA_UNSPECIFIED,
            information_state_layer="SharedTacticalPicture",
            decision_model_ref=SCHEMA_UNSPECIFIED,
            action_interface=SCHEMA_UNSPECIFIED,
            authors=("warfare_role_code",),
            consumes=("task_family", "coordination_mode"),
            note="Screen/SurfaceAction/AirDefense/SeaControl/Logistics command-node "
            "role identity (see NAVAL_WARFARE_ROLES); not a compiled action-interface "
            "agent (schema slots 'unspecified').",
        ),
        "formation_member": AuthorityRole(
            role_id="formation_member",
            label="Formation/element member (role_code / relative_slot_code)",
            authority_scope=SCHEMA_UNSPECIFIED,
            information_state_layer="AgentObservation",
            decision_model_ref=SCHEMA_UNSPECIFIED,
            action_interface=SCHEMA_UNSPECIFIED,
            authors=("role_code", "relative_slot_code"),
            consumes=("formation_role_id", "reference_entity_id"),
            note="Non-leader membership/slot identity arbitrated by the director; the "
            "member's own controlling agent is an autopilot_controller. Membership "
            "identity, so the action-interface schema slots stay 'unspecified'.",
        ),
        "engagement_authority_holder": AuthorityRole(
            role_id="engagement_authority_holder",
            label="Engagement (fire) authority holder",
            authority_scope=SCHEMA_UNSPECIFIED,
            information_state_layer="SharedTacticalPicture",
            decision_model_ref=SCHEMA_UNSPECIFIED,
            action_interface=SCHEMA_UNSPECIFIED,
            authors=("authorization_to_fire",),
            consumes=("engagement_authority_holder_id", "engagement_authority_grantor_id"),
            note="Fire-authority holder identity; the 'who-may-fire' arbitration keys "
            "off holder id rather than a compiled action interface (schema slots "
            "'unspecified').",
        ),
    }
)


# --------------------------------------------------------------------------- #
# Authority scopes
# --------------------------------------------------------------------------- #
# Mirrors ``enum class AuthorityScope`` (core_tasking_enums.h). Ordered from the
# broadest command echelon to the narrowest execution echelon (compiled order).
AUTHORITY_SCOPE_LEVELS: tuple[str, ...] = (
    "Unspecified",
    "Strategic",
    "Operational",
    "Tactical",
    "Execution",
)

# Action-interface scopes named by the compiled policy contract
# (``policy_contracts.h`` ``kAgentAuthorityScope*`` / ``is_known_agent_authority_scope``):
# the narrow scopes an AgentRole's ``authority_scope.scope`` string may take on the
# maintained surface. Ordered to match the header declaration order.
ACTION_INTERFACE_SCOPES: tuple[str, ...] = (
    "platform_control",
    "mission_command",
    "formation_coordination",
)

# Action-interface kinds named by the compiled policy contract
# (``policy_contracts.h`` ``kActionInterface*`` / ``is_known_agent_action_interface_kind``).
ACTION_INTERFACE_KINDS: tuple[str, ...] = (
    "PilotActionAssignment",
    "CommandChainAssignment",
)

# The one authority-scope rule that lives only as prose today (folklore): the
# scripted C2 layer's read/write scope boundary.
SCOPE_FOLKLORE_RULES: tuple[str, ...] = (
    "scripted_c2 may consume shared situation data and pilot reports but may not "
    "directly author low-level mission commands",
)


# --------------------------------------------------------------------------- #
# Delegation relationships
# --------------------------------------------------------------------------- #
# Mirrors ``enum class CommandRelationship`` (core_tasking_enums.h): the doctrinal
# command/support authority relationships between echelons.
COMMAND_RELATIONSHIPS: tuple[str, ...] = (
    "None",
    "COCOM",
    "OPCON",
    "TACON",
    "Support",
    "ADCON",
    "CoordinatingAuthority",
    "DIRLAUTH",
)

# Mirrors ``enum class CoordinationMode`` (core_tasking_enums.h): how a unit is
# coordinated relative to its command node.
COORDINATION_MODES: tuple[str, ...] = (
    "Unspecified",
    "Independent",
    "Attached",
    "Follow",
    "Support",
    "Screen",
    "Rejoin",
    "Recover",
    "Detached",
)

# Mirrors ``enum class NavalWarfareRole``
# (src/components/domains/naval/tasking/naval_tasking_enums.h): the naval
# warfare-role command-node identities. All six members (including
# ``Unspecified``) are declared so the gate can pin the mirror against the header.
NAVAL_WARFARE_ROLES: tuple[str, ...] = (
    "Unspecified",
    "ScreenCommander",
    "SurfaceActionCommander",
    "AirDefenseCommander",
    "SeaControlCommander",
    "LogisticsCoordinator",
)

# Delegation carriers found on the maintained surface (fields/ids that transfer
# an authority from one entity to another).
DELEGATION_CARRIERS: tuple[str, ...] = (
    "officer_in_tactical_command",
    "engagement_authority_grantor_id",
    "authorization_to_fire",
    "command_relationship",
    "coordination_mode",
)


# --------------------------------------------------------------------------- #
# Maintained-tasking authority defaults (single declarative source for A2/A3)
# --------------------------------------------------------------------------- #
# The default *value choice* the maintained tasking normalization layer applies
# when a task order still carries the compiled struct's raw-construction sentinel
# in ``command_relationship`` / ``authority_scope`` -- namely
# ``CommandRelationship::None`` / ``AuthorityScope::Unspecified`` (both enum value
# 0; see ``src/components/tasking/common/task_order_core.h``). This is a
# *normalization default*, deliberately distinct from that raw-construction
# sentinel: the maintained Python profile layer (A2
# ``python/rl/tasking/common_core_profile.py`` and its leaf provider A3
# ``python/rl/profile/common_core_defaults.py``) upgrades an *unset* echelon
# field to a doctrinal default (TACON command relationship at the Tactical
# authority scope) so a maintained order that omitted them is still well-formed.
#
# There is **no compiled counterpart that produces these values**: nothing in
# ``src/**`` ever assigns ``TACON`` / ``Tactical`` (the only compiled mentions are
# the enum member definitions and the pybind exports), and the compiled
# ``authorize_maintained_*`` gates operate on the ``AgentRole`` /
# ``AgentAuthorityScope`` *action-interface* representation
# (``platform_control`` / ``mission_command`` / ``formation_coordination``
# strings), not the ``CommandRelationship`` / ``AuthorityScope`` echelon enums.
# So the value source is already single (Python A3); this change (I68) elevates
# the *name choice* to the registry declaration layer so A3 resolves
# ``getattr(ef_py.<enum>, NAME)`` from here rather than a local string literal.
# The resolved runtime value is byte-identical (same enum member), so the move is
# zero-behavior (census EN/ZH §9). Each name below
# is a member of its mirror tuple above; the equivalence test in
# ``tests/architecture/agency/test_authority_default_single_source.py`` pins that.
DEFAULT_COMMAND_RELATIONSHIP: str = "TACON"
DEFAULT_AUTHORITY_SCOPE: str = "Tactical"


# --------------------------------------------------------------------------- #
# Arbitration policies
# --------------------------------------------------------------------------- #
# Mirrors the SCAL cross-layer ``merge_policy`` enum
# (simulation_system_architecture_design.md contract-detail table): how
# conflicting writes to the same entity/field are resolved.
MERGE_POLICIES: tuple[str, ...] = (
    "last_write_wins",
    "priority_override",
    "reject_on_conflict",
    "merge_by_field",
    "append_only",
)

# SCAL source-priority ordering used by ``priority_override``. Source:
# ``docs/architecture/standards/simulation_system_architecture_design.md`` (Agency
# face cross-layer merge/arbitration rule: human > policy > scripted > diagnostic).
SOURCE_PRIORITY_ORDER: tuple[str, ...] = (
    "human",
    "policy",
    "scripted",
    "diagnostic",
)

# Arbitration mechanisms found on the maintained surface: the precedences/gates
# that decide *which producer wins* when several authority sources compete for
# the same field (distinct from a pure enable/disable activation gate, which is
# ``CATEGORY_GATING`` below).
ARBITRATION_MECHANISMS: tuple[str, ...] = (
    "engagement_authority_holder_id",  # 'who may fire' holder gate (holder_ok)
    "leader_intent_overrides_mission_command",  # leader precedence over mission_cmd
    "task_priority",  # TaskOrder.priority
)

# Command-chain activation gates found on the maintained surface: they decide
# *whether* the leader/command-chain authority path runs at all (enable/disable),
# and do not resolve conflicts between competing authority sources. This is a
# distinct dimension from ``ARBITRATION_MECHANISMS`` (conflict resolution).
ACTIVATION_GATES: tuple[str, ...] = (
    "hierarchical_command_chain_active",
)

# Fire-eligibility gates on the censused surface: they decide *whether* the policy
# *may fire* as a conjunction of eligibility conditions and, unlike the who-may-fire
# arbitration (A13, which reads the engagement-authority holder id to resolve which
# agent wins), do not read the holder/grantor id at all. The air-combat C2/ROE fire
# mask (A14) is the observation-face gate surfaced today: it reads
# ``authorization_to_fire`` (+ wcs/engage/shot state) but not the holder id, so it
# is a gate, not conflict resolution. Owned by the I45 observation face (read-only
# census); named here so the ``gating`` dimension's declared vocabulary covers A14.
FIRE_ELIGIBILITY_GATES: tuple[str, ...] = (
    "_air_combat_c2_roe_policy_fire_mask_open",
)

# Fail-closed authorization gates that already exist as the compiled reference
# (``policy_contracts.h`` / ``information_transform_contracts.h``). Named here so
# the Python arbitration surface can be converged onto them later.
COMPILED_AUTHORIZATION_GATES: tuple[str, ...] = (
    "authorize_maintained_action_intent",
    "authorize_maintained_coordination_intent",
    "authorize_maintained_decision_belief_action_intent_injection",
)


# --------------------------------------------------------------------------- #
# DoctrineFamily (vocabulary placeholder only -- no mechanism this slice)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DoctrineFamilyPlaceholder:
    """Declared name + component list for the SCAL ``DoctrineFamily`` extension.

    simulation_system_architecture_design.md domain-extension model lists
    ``DoctrineFamily: task templates, ROE, authority delegation, engagement
    policy``. This slice declares only the family name and its component/ROE
    vocabulary so a later slice can attach a real mechanism by registration.
    No engagement/ROE behavior is implemented or altered here.
    """

    name: str
    declared_components: tuple[str, ...]
    roe_pattern_fields: tuple[str, ...]
    status: str


DOCTRINE_FAMILY: DoctrineFamilyPlaceholder = DoctrineFamilyPlaceholder(
    name="DoctrineFamily",
    declared_components=(
        "task_templates",
        "roe",
        "authority_delegation",
        "engagement_policy",
    ),
    # Existing ROE / weapon-control pattern fields already carried on the mission
    # command surface, declared (not mechanized) so the family has a concrete
    # vocabulary to formalize later.
    roe_pattern_fields=(
        "roe_state",
        "wcs_state",
        "shot_policy_state",
        "engage_order_state",
        "authorization_to_fire",
        "engagement_authority_holder_id",
        "engagement_authority_grantor_id",
    ),
    status="vocabulary_placeholder",
)


# --------------------------------------------------------------------------- #
# Census detection tokens -> authority category candidates + scan surface
# --------------------------------------------------------------------------- #
# The ratchet gate scans the maintained authority surface for these tokens. Each
# token maps to the *set of authority categories it may legitimately express*
# depending on the site context -- not a single fixed category. A per-site census
# entry then adjudicates which of a token's candidate categories actually apply at
# that site (grounded by these candidate sets and required to cover every token),
# rather than being forced into one rigid category by the token alone.
#
# Rationale (I47 repair): a fixed token->category map distorts classification.
# ``engagement_authority_holder_id`` is *arbitration* when it keys the who-may-fire
# gate (A13) but a mirrored *role/delegation* identity when merely projected into a
# state mirror (A8); ``authorization_to_fire`` is a *delegation* field-copy (A10),
# participates in an *arbitration* leader-vs-mission precedence (A5), and feeds a
# *gating* fire-eligibility mask (A14, which reads it but not the holder id, so it
# is a gate rather than the A13 who-may-fire arbitration). Candidate sets let each
# site be adjudicated honestly while staying grounded in the tokens.
#
# Repair round 2 also tokenizes the previously-untokenized synonym family so the
# ratchet actually bites a file that carries authority logic under a derived
# spelling: the bare ``commander_id`` local (a role identity, distinct from the
# ``ground_commander_id`` field), the snake_case ``command_relationship`` field
# accessor, the ``infer_command_relationship`` delegation-inference function, and
# the loader-side delegate spelling ``_hierarchical_command_chain_active`` (the
# ScenarioLoader method that forwards to the behavior-runtime activation gate --
# a *gating* site the substring scanner had only caught by accident, matching the
# gate name inside the underscore-prefixed method name). All are matched by *word
# boundary* so they never double-count inside a longer identifier such as
# ``ground_commander_id`` / ``_command_relationship_default`` /
# ``_hierarchical_command_chain_active_impl`` -- see ``scan_authority_surface``.
AUTHORITY_TOKEN_CATEGORIES: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "allowed to directly author": frozenset({CATEGORY_SCOPE}),
        "authorization_to_fire": frozenset(
            {CATEGORY_DELEGATION, CATEGORY_ARBITRATION, CATEGORY_GATING}
        ),
        "engagement_authority_holder_id": frozenset(
            {CATEGORY_ARBITRATION, CATEGORY_DELEGATION, CATEGORY_ROLE}
        ),
        "engagement_authority_grantor_id": frozenset({CATEGORY_DELEGATION}),
        "officer_in_tactical_command": frozenset({CATEGORY_DELEGATION, CATEGORY_ROLE}),
        "ground_commander_id": frozenset({CATEGORY_ROLE}),
        "commander_id": frozenset({CATEGORY_ROLE}),
        "CommandRelationship": frozenset({CATEGORY_DELEGATION}),
        "command_relationship": frozenset({CATEGORY_DELEGATION}),
        "infer_command_relationship": frozenset({CATEGORY_DELEGATION}),
        "AuthorityScope": frozenset({CATEGORY_SCOPE}),
        "NavalWarfareRole": frozenset({CATEGORY_ROLE}),
        "warfare_role_code": frozenset({CATEGORY_ROLE}),
        "hierarchical_command_chain_active": frozenset({CATEGORY_GATING}),
        "_hierarchical_command_chain_active": frozenset({CATEGORY_GATING}),
        "is_leader": frozenset({CATEGORY_ROLE, CATEGORY_ARBITRATION}),
        "roe_state": frozenset({CATEGORY_DOCTRINE}),
    }
)

# Scan surface for each token: ``"code"`` tokens are code identifiers matched only
# in executable code (docstrings, comments, import statements, and ``__all__``
# re-export plumbing are stripped before matching, so an innocent docstring
# mention or a pure re-export is not a false positive). ``"prose"`` tokens are
# folklore phrases matched only in docstrings/comments (that is where the
# convention deliberately lives, e.g. the scripted-C2 authorship boundary).
SURFACE_CODE = "code"
SURFACE_PROSE = "prose"

AUTHORITY_TOKEN_SURFACE: Mapping[str, str] = MappingProxyType(
    {
        "allowed to directly author": SURFACE_PROSE,
        "authorization_to_fire": SURFACE_CODE,
        "engagement_authority_holder_id": SURFACE_CODE,
        "engagement_authority_grantor_id": SURFACE_CODE,
        "officer_in_tactical_command": SURFACE_CODE,
        "ground_commander_id": SURFACE_CODE,
        "commander_id": SURFACE_CODE,
        "CommandRelationship": SURFACE_CODE,
        "command_relationship": SURFACE_CODE,
        "infer_command_relationship": SURFACE_CODE,
        "AuthorityScope": SURFACE_CODE,
        "NavalWarfareRole": SURFACE_CODE,
        "warfare_role_code": SURFACE_CODE,
        "hierarchical_command_chain_active": SURFACE_CODE,
        "_hierarchical_command_chain_active": SURFACE_CODE,
        "is_leader": SURFACE_CODE,
        "roe_state": SURFACE_CODE,
    }
)

# Category -> the registry vocabulary tuple(s) that give that dimension its
# declared terms. Used by the gate to assert every census-present category has a
# non-empty registered vocabulary ("declared sets cover census semantics").
CATEGORY_VOCABULARY: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        CATEGORY_ROLE: tuple(AUTHORITY_ROLES.keys()),
        CATEGORY_SCOPE: AUTHORITY_SCOPE_LEVELS + ACTION_INTERFACE_SCOPES,
        CATEGORY_DELEGATION: COMMAND_RELATIONSHIPS + DELEGATION_CARRIERS,
        CATEGORY_ARBITRATION: MERGE_POLICIES + ARBITRATION_MECHANISMS,
        CATEGORY_GATING: ACTIVATION_GATES + FIRE_ELIGIBILITY_GATES,
        CATEGORY_DOCTRINE: DOCTRINE_FAMILY.roe_pattern_fields,
        CATEGORY_UNDECIDED: ("<待裁定 / to-be-adjudicated>",),
    }
)


def authority_categories_for_token(token: str) -> frozenset[str]:
    """Return the candidate authority categories a census detection token may express."""
    return AUTHORITY_TOKEN_CATEGORIES[token]


def candidate_categories_for_tokens(tokens: tuple[str, ...] | list[str]) -> frozenset[str]:
    """Return the union of candidate authority categories implied by a token set."""
    out: set[str] = set()
    for token in tokens:
        out |= AUTHORITY_TOKEN_CATEGORIES[token]
    return frozenset(out)


def token_surface(token: str) -> str:
    """Return the scan surface (``"code"`` or ``"prose"``) for a detection token."""
    return AUTHORITY_TOKEN_SURFACE[token]


def registered_terms_for_category(category: str) -> tuple[str, ...]:
    """Return the declared vocabulary terms for an authority category."""
    return CATEGORY_VOCABULARY[category]


__all__ = [
    "ACTION_INTERFACE_KINDS",
    "ACTION_INTERFACE_SCOPES",
    "ACTIVATION_GATES",
    "AGENT_ROLE_SCHEMA_FIELDS",
    "ARBITRATION_MECHANISMS",
    "AUTHORITY_CATEGORIES",
    "AUTHORITY_ROLES",
    "AUTHORITY_SCOPE_LEVELS",
    "AUTHORITY_TOKEN_CATEGORIES",
    "AUTHORITY_TOKEN_SURFACE",
    "AuthorityRole",
    "CATEGORY_ARBITRATION",
    "CATEGORY_DELEGATION",
    "CATEGORY_DOCTRINE",
    "CATEGORY_GATING",
    "CATEGORY_ROLE",
    "CATEGORY_SCOPE",
    "CATEGORY_UNDECIDED",
    "CATEGORY_VOCABULARY",
    "COMMAND_RELATIONSHIPS",
    "COMPILED_AUTHORIZATION_GATES",
    "COORDINATION_MODES",
    "DEFAULT_AUTHORITY_SCOPE",
    "DEFAULT_COMMAND_RELATIONSHIP",
    "DELEGATION_CARRIERS",
    "DOCTRINE_FAMILY",
    "DoctrineFamilyPlaceholder",
    "FIRE_ELIGIBILITY_GATES",
    "MERGE_POLICIES",
    "NAVAL_WARFARE_ROLES",
    "SCHEMA_UNSPECIFIED",
    "SCOPE_FOLKLORE_RULES",
    "SOURCE_PRIORITY_ORDER",
    "SURFACE_CODE",
    "SURFACE_PROSE",
    "authority_categories_for_token",
    "candidate_categories_for_tokens",
    "registered_terms_for_category",
    "token_surface",
]
