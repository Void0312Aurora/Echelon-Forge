"""Weapon-guidance realism runtime guards.

Capability sub-surfaces are split across five independently-runnable test
modules (``test_launch_guidance_and_dynamics``,
``test_warhead_and_component_damage``, ``test_vulnerability_authority``,
``test_consumer_validation``, ``test_geometry_and_edge_cases``). Each module
composes its capability mixins under a real :class:`unittest.TestCase` so it can
be selected, run, and triaged on its own. Shared support helpers live in
``helpers``.
"""
