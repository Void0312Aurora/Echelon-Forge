"""T9 authority-representation boundary gate (adjudicated this iteration).

Pins the **no-mapping verdicts** of the T9 authority representation
adjudication
(``docs/systems/command-tasking/reference/t9_authority_representation_adjudication_20260726.md``):
the maintained surface carries two disjoint authority representations --

- the **echelon representation**: the compiled ``CommandRelationship`` /
  ``AuthorityScope`` enums (``src/components/tasking/common/core_tasking_enums.h``)
  carried by ``TaskOrderCore`` and defaulted/inferred by the A2/A4/A5/A6 profile
  sites and read (as fire-authority DTO fields) by the A13 who-may-fire gate; and
- the **action-interface representation**: the compiled ``AgentRole`` /
  ``AgentAuthorityScope`` contracts (``src/runtime/contracts/policy_contracts.h``)
  consumed by the runtime-face ``authorize_maintained_*`` authorization path
  (``python/rl/runtime/world_batch/adapter.py``, ``python/rl/runtime/agent_shim.py``)

-- and the adjudication found **no code path on either side that flows an
echelon-authority value into, or compares one against, an action-interface
authority value**. This gate makes that verdict structural: each no-mapping site
must stay free of the *other* family's discriminating identifiers on its
executable-code surface (docstrings/comments stripped -- prose may legitimately
discuss both families), and the compiled headers of each family must stay free
of the other family's type names. Injecting a cross-family link (tamper tests
below) turns the gate red, so a future mapping cannot appear silently: it must
arrive together with a census/adjudication update and, per the T9 key risk,
domain-evidence review.

Deliberate token-set boundaries (documented, not blind spots):

- ``mission_command`` is a **homonym** across the families (the
  ``kAgentAuthorityScopeMissionCommand`` scope string, the
  ``kActionInterfacePayloadMissionCommand`` payload type, the scenario
  ``mission_command`` dict key, and the compiled ``MissionCommand`` DTO) and is
  therefore not a discriminating token on either side.
- The snake_case ``authority_scope`` attribute is likewise a homonym
  (``TaskOrder.authority_scope`` echelon field vs ``AgentRole.authority_scope``
  struct member) and is not used as a discriminator; the CamelCase enum/type
  names and the distinctive enum members discriminate instead.
- Generic echelon member spellings (``None``, ``Unspecified``, ``Support``,
  ``Strategic``, ``Operational``, ``Tactical``, ``Execution``) are excluded as
  hopelessly collision-prone; the distinctive members (``COCOM`` / ``OPCON`` /
  ``TACON`` / ``ADCON`` / ``DIRLAUTH`` / ``CoordinatingAuthority``) plus the
  enum/type and accessor names carry the discrimination.

Zero C2 behavior change: this module is a read-only structural gate.
"""

from __future__ import annotations

import re

import pytest

from tests.architecture.agency.test_authority_registry_gate import (
    _count_token_occurrences,
    _split_code_and_prose,
    _strip_cpp_comments,
)
from tests.support.paths import REPO_ROOT

# --------------------------------------------------------------------------- #
# Discriminating identifier families
# --------------------------------------------------------------------------- #
# Echelon-authority family: the CommandRelationship / AuthorityScope enum
# representation (core_tasking_enums.h:31-48, TaskOrderCore task_order_core.h:15-16,
# pybind exports bindings_command.cpp:150-165).
ECHELON_TOKENS: tuple[str, ...] = (
    "CommandRelationship",
    "AuthorityScope",  # \b-matched: does NOT match inside AgentAuthorityScope
    "COCOM",
    "OPCON",
    "TACON",
    "ADCON",
    "DIRLAUTH",
    "CoordinatingAuthority",
    "command_relationship",
    "infer_command_relationship",
)

# Action-interface authority family: the AgentRole / AgentAuthorityScope
# representation and its authorization entry points
# (policy_contracts.h:278-285, 319-330, 454-503; pybind exports
# bindings_runtime.cpp:399-406, 441-452, 638-645).
ACTION_INTERFACE_TOKENS: tuple[str, ...] = (
    "AgentRole",
    "AgentAuthorityScope",
    "AgentRoleAuthorizationResult",
    "authorize_maintained_action_intent",
    "authorize_maintained_coordination_intent",
    "agent_role_has_maintained_authority_shape",
    "agent_role_action_interface_matches_authority_scope",
    "is_known_agent_authority_scope",
    "platform_control",
    "formation_coordination",
    "PilotActionAssignment",
    "CommandChainAssignment",
)

# --------------------------------------------------------------------------- #
# No-mapping verdict pins (adjudication verdict matrix rows)
# --------------------------------------------------------------------------- #
# Echelon-side sites (census A2/A4/A5/A6/A13): verdict **no-mapping** -- their
# code surface must carry none of the action-interface family. ``marker`` is an
# own-family sanity token proving the gate is still looking at a live authority
# site (a hollowed-out or repurposed file fails the sanity pin instead of
# passing the absence check vacuously).
ECHELON_NO_MAPPING_SITES: dict[str, str] = {
    "python/rl/tasking/common_core_profile.py": "command_relationship",  # A2
    "python/rl/profile/air_profile.py": "command_relationship",  # A4
    "python/rl/profile/ground_profile.py": "infer_command_relationship",  # A5
    "python/rl/profile/naval_profile.py": "command_relationship",  # A6
    "gym_envs/universal_env_parts/air_combat_event_action.py": (
        "engagement_authority_holder_id"  # A13 (fire-authority DTO reader)
    ),
}

# Action-interface-side sites (runtime authorization path): verdict
# **no-mapping** in the reverse direction -- their code surface must carry none
# of the echelon family.
ACTION_INTERFACE_NO_MAPPING_SITES: dict[str, str] = {
    "python/rl/runtime/world_batch/adapter.py": "AgentRole",
    "python/rl/runtime/agent_shim.py": "AgentRole",
}

# Compiled-surface disjointness: each family's defining headers must not name
# the other family's types.
ECHELON_FAMILY_HEADERS: tuple[str, ...] = (
    "src/components/tasking/common/core_tasking_enums.h",
    "src/components/tasking/common/task_order_core.h",
)
ACTION_INTERFACE_FAMILY_HEADERS: tuple[str, ...] = (
    "src/runtime/contracts/policy_contracts.h",
    "src/runtime/contracts/information_transform_contracts.h",
    "src/runtime/contracts/counterfactual_replay_contract_types.h",
)
COMPILED_ECHELON_TYPE_TOKENS: tuple[str, ...] = (
    "CommandRelationship",
    "AuthorityScope",
)
COMPILED_ACTION_INTERFACE_TYPE_TOKENS: tuple[str, ...] = (
    "AgentRole",
    "AgentAuthorityScope",
)


# --------------------------------------------------------------------------- #
# Checker (shared by the gate assertions and the tamper self-tests)
# --------------------------------------------------------------------------- #
def cross_family_hits(source: str, forbidden_tokens: tuple[str, ...]) -> dict[str, int]:
    """Word-boundary counts of ``forbidden_tokens`` on the executable-code surface.

    Docstrings and comments are stripped first (prose may legitimately discuss
    both representations; only executable code constitutes a mapping path), and
    ``import``/``__all__`` re-export plumbing is dropped, reusing the census
    gate's scanner so both gates agree about what "code surface" means. String
    literals stay on the code surface: an action-interface scope travels as a
    string literal (e.g. ``role.authority_scope.scope = "platform_control"``),
    so literals are exactly where a smuggled mapping could hide.
    """
    code_text, _prose = _split_code_and_prose(source)
    hits: dict[str, int] = {}
    for token in forbidden_tokens:
        count = _count_token_occurrences(code_text, token)
        if count:
            hits[token] = count
    return hits


def _read(rel_path: str) -> str:
    path = REPO_ROOT / rel_path
    assert path.is_file(), (
        f"adjudicated no-mapping site {rel_path} no longer exists; the "
        "representation-boundary verdict matrix must be re-adjudicated"
    )
    return path.read_text(encoding="utf-8", errors="replace")


# --------------------------------------------------------------------------- #
# Gate: no-mapping verdicts hold on the Python surface
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("rel_path", sorted(ECHELON_NO_MAPPING_SITES))
def test_echelon_site_carries_no_action_interface_authority(rel_path: str) -> None:
    source = _read(rel_path)
    marker = ECHELON_NO_MAPPING_SITES[rel_path]
    code_text, _prose = _split_code_and_prose(source)
    assert _count_token_occurrences(code_text, marker), (
        f"{rel_path}: own-family sanity marker {marker!r} vanished from the code "
        "surface; the site changed shape and the adjudication must be revisited"
    )
    hits = cross_family_hits(source, ACTION_INTERFACE_TOKENS)
    assert not hits, (
        f"{rel_path}: adjudicated no-mapping (echelon -> action-interface), but "
        f"action-interface authority identifiers appeared on its code surface: "
        f"{hits}. A real mapping between CommandRelationship/AuthorityScope and "
        "AgentRole/AgentAuthorityScope is a T9 semantic change: update the "
        "adjudication doc pair and obtain domain-evidence review first."
    )


@pytest.mark.parametrize("rel_path", sorted(ACTION_INTERFACE_NO_MAPPING_SITES))
def test_action_interface_site_carries_no_echelon_authority(rel_path: str) -> None:
    source = _read(rel_path)
    marker = ACTION_INTERFACE_NO_MAPPING_SITES[rel_path]
    code_text, _prose = _split_code_and_prose(source)
    assert _count_token_occurrences(code_text, marker), (
        f"{rel_path}: own-family sanity marker {marker!r} vanished from the code "
        "surface; the site changed shape and the adjudication must be revisited"
    )
    hits = cross_family_hits(source, ECHELON_TOKENS)
    assert not hits, (
        f"{rel_path}: adjudicated no-mapping (action-interface -> echelon), but "
        f"echelon authority identifiers appeared on its code surface: {hits}. "
        "A real mapping between the families is a T9 semantic change: update the "
        "adjudication doc pair and obtain domain-evidence review first."
    )


# --------------------------------------------------------------------------- #
# Gate: compiled headers of the two families stay type-disjoint
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("rel_path", ECHELON_FAMILY_HEADERS)
def test_echelon_family_header_names_no_action_interface_type(rel_path: str) -> None:
    clean = _strip_cpp_comments(_read(rel_path))
    hits = {
        token: _count_token_occurrences(clean, token)
        for token in COMPILED_ACTION_INTERFACE_TYPE_TOKENS
        if _count_token_occurrences(clean, token)
    }
    assert not hits, (
        f"{rel_path}: echelon-family header now names action-interface authority "
        f"types {hits}; the compiled representation boundary moved and the "
        "adjudication must be revisited"
    )


@pytest.mark.parametrize("rel_path", ACTION_INTERFACE_FAMILY_HEADERS)
def test_action_interface_family_header_names_no_echelon_type(rel_path: str) -> None:
    clean = _strip_cpp_comments(_read(rel_path))
    hits = {
        token: _count_token_occurrences(clean, token)
        for token in COMPILED_ECHELON_TYPE_TOKENS
        if _count_token_occurrences(clean, token)
    }
    assert not hits, (
        f"{rel_path}: action-interface-family header now names echelon authority "
        f"types {hits}; the compiled representation boundary moved and the "
        "adjudication must be revisited"
    )


def test_word_boundary_does_not_flag_agent_authority_scope_as_echelon() -> None:
    # Regression pin for the discriminator itself: the echelon token
    # ``AuthorityScope`` must not fire inside ``AgentAuthorityScope`` (this is
    # what lets counterfactual_replay_contract_types.h line 96 stay green).
    assert _count_token_occurrences("AgentAuthorityScope authority_scope{};", "AuthorityScope") == 0
    assert _count_token_occurrences("AuthorityScope scope;", "AuthorityScope") == 1


# --------------------------------------------------------------------------- #
# Tamper self-tests: the gate bites rather than passing vacuously
# --------------------------------------------------------------------------- #
def test_gate_bites_on_injected_action_interface_link() -> None:
    source = _read("python/rl/profile/ground_profile.py")
    tampered = source + (
        "\n\n_probe_role = ef_py.AgentRole()\n"
        "_probe_role.authority_scope.scope = \"platform_control\"\n"
    )
    hits = cross_family_hits(tampered, ACTION_INTERFACE_TOKENS)
    assert hits.get("AgentRole") == 1
    assert hits.get("platform_control") == 1


def test_gate_bites_on_injected_echelon_link() -> None:
    source = _read("python/rl/runtime/world_batch/adapter.py")
    tampered = source + (
        "\n\n_probe_relationship = getattr(ef_py.CommandRelationship, \"TACON\")\n"
    )
    hits = cross_family_hits(tampered, ECHELON_TOKENS)
    assert hits.get("CommandRelationship") == 1
    assert hits.get("TACON") == 1


def test_gate_bites_on_injected_cross_family_comparison() -> None:
    # The exact failure mode the adjudication rules out: comparing an echelon
    # value against an action-interface scope.
    tampered = (
        "def _leak(order, role):\n"
        "    return int(order.authority_scope) == 3 and "
        "role.authority_scope.scope == \"mission_command\" and "
        "is_known_agent_authority_scope(role.authority_scope.scope)\n"
    )
    hits = cross_family_hits(tampered, ACTION_INTERFACE_TOKENS)
    assert hits.get("is_known_agent_authority_scope") == 1


def test_gate_ignores_docstring_and_comment_mentions() -> None:
    innocent = (
        '"""Discusses AgentRole and CommandRelationship in prose only."""\n'
        "# comment: AgentAuthorityScope vs AuthorityScope, TACON, platform_control\n"
        "value = 1\n"
    )
    assert cross_family_hits(innocent, ACTION_INTERFACE_TOKENS) == {}
    assert cross_family_hits(innocent, ECHELON_TOKENS) == {}
