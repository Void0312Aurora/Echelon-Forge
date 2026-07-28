"""A3 authority-default name-ownership pin (I68).

The maintained tasking normalization layer's command-relationship / authority-
scope *default name* is declared once in the agency registry
(:data:`agency_registry.DEFAULT_COMMAND_RELATIONSHIP` /
:data:`agency_registry.DEFAULT_AUTHORITY_SCOPE`) and consumed by the leaf default
provider A3 (``python/rl/profile/common_core_defaults.py``), which resolves the
declared *name* against the compiled ``ef_py`` enum. This pins the equivalence so
neither side can drift silently, and proves the move is byte-identical to the
former local literals (``"TACON"`` / ``"Tactical"``): the runtime value is the
exact same compiled enum member.

It is the A3 analogue of the I53 ``agent_shim`` merge-policy drift pin
(``tests/runtime/test_agent_shim.py``). Every test function here contains at
least one assertion on a symbol that did not exist at the baseline (0aa76a00),
so the whole module is red before the change and green after (the
"red -> green" equivalence evidence at function granularity).
"""

from __future__ import annotations

import ef_py

from python.rl.profile import common_core_defaults as a3
from python.tasking_contracts import agency_registry as registry


def test_default_names_are_registry_owned_and_mirror_the_compiled_enum_positions():
    # The default *name* is a declared registry constant (single owner of the
    # choice), not a value invented at the consumer.
    assert registry.DEFAULT_COMMAND_RELATIONSHIP == "TACON"
    assert registry.DEFAULT_AUTHORITY_SCOPE == "Tactical"

    # Each name is a member of its compiled-enum mirror tuple, at the compiled
    # enum's integer position -- so the declared default is grounded in the
    # compiled authority model, never a free-floating string.
    assert registry.DEFAULT_COMMAND_RELATIONSHIP in registry.COMMAND_RELATIONSHIPS
    assert registry.DEFAULT_AUTHORITY_SCOPE in registry.AUTHORITY_SCOPE_LEVELS
    assert registry.COMMAND_RELATIONSHIPS.index(
        registry.DEFAULT_COMMAND_RELATIONSHIP
    ) == int(ef_py.CommandRelationship.TACON)
    assert registry.AUTHORITY_SCOPE_LEVELS.index(
        registry.DEFAULT_AUTHORITY_SCOPE
    ) == int(ef_py.AuthorityScope.Tactical)


def test_a3_defaults_resolve_byte_identically_to_the_former_literals():
    # A3 now resolves the registry-owned name; the runtime value must be the exact
    # same compiled enum member the former local "TACON"/"Tactical" literals
    # produced (zero-behavior convergence).
    assert a3.command_relationship_default() == ef_py.CommandRelationship.TACON
    assert a3.authority_scope_default() == ef_py.AuthorityScope.Tactical
    assert int(a3.command_relationship_default()) == int(ef_py.CommandRelationship.TACON)
    assert int(a3.authority_scope_default()) == int(ef_py.AuthorityScope.Tactical)

    # Equivalent to resolving the registry constant directly -- the two paths are
    # one source.
    assert a3.command_relationship_default() == getattr(
        ef_py.CommandRelationship, registry.DEFAULT_COMMAND_RELATIONSHIP
    )
    assert a3.authority_scope_default() == getattr(
        ef_py.AuthorityScope, registry.DEFAULT_AUTHORITY_SCOPE
    )


def test_a3_binding_is_the_registry_object_so_the_pin_is_not_vacuous():
    """Negative-side self-test: A3's default provider is bound to the registry
    constant object itself (``is`` identity on the interned name), so the single
    source cannot silently fork into a stale local copy. This is the structural
    guarantee behind the byte-identity above."""
    assert a3._DEFAULT_COMMAND_RELATIONSHIP is registry.DEFAULT_COMMAND_RELATIONSHIP
    assert a3._DEFAULT_AUTHORITY_SCOPE is registry.DEFAULT_AUTHORITY_SCOPE
    # Guard the pin's discriminating power: the default is a *specific* member, so a
    # different registered relationship/scope would not satisfy the equivalence.
    assert a3.command_relationship_default() != getattr(ef_py.CommandRelationship, "Support")
    assert a3.authority_scope_default() != getattr(ef_py.AuthorityScope, "Operational")
