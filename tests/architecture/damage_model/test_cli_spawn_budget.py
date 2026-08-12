"""Spawn budget for the damage-model audit CLI tests.

These audit modules used to restart the interpreter for every CLI assertion:
each ``subprocess`` call re-imported the whole ``damage_model.py`` producer
stack and re-ran a full gate just to check a handful of artifacts, which cost
more wall clock than the gate itself. The tier now keeps exactly one real
end-to-end smoke per CLI family and drives every other call site through
``tests.support.cli.run_maintenance_cli_in_process``.

This module guards both halves of that arrangement, because each half decays in
the opposite direction: without a ceiling the spawns creep back one convenient
copy-paste at a time, and without a floor the last real subprocess run can be
"simplified" away, leaving nothing that proves ``damage_model.py`` still routes
a command line to its producer.
"""

from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path


AUDIT_DIR = Path(__file__).resolve().parent

#: Call targets that start a separate interpreter for a maintenance CLI.
#: ``run_maintenance_cli``/``run_maintenance_json_cli`` are the sanctioned
#: wrappers around ``subprocess.run``, so they count exactly like a raw spawn.
SPAWNING_CALLS = frozenset(
  {
    "subprocess.run",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
    "subprocess.Popen",
    "run_maintenance_cli",
    "run_maintenance_json_cli",
  }
)

#: ``damage_model.py`` domains exercised from this directory. Each one keeps a
#: real subprocess smoke; its remaining sub-commands run in-process.
REQUIRED_SMOKE_FAMILIES = frozenset(
  {
    "benchmark-evidence",
    "candidate-artifacts",
    "external-evidence",
    "independent-review",
    "release-governance",
    "scope-provenance",
    "source-governance",
  }
)

#: One smoke per family plus a little headroom, so landing a genuinely new CLI
#: family does not require editing this budget in the same change.
MAX_SPAWN_CALL_SITES = len(REQUIRED_SMOKE_FAMILIES) + 2

UNRESOLVED_FAMILY = "<unresolved>"


def _string_tokens(node: ast.AST) -> list[str]:
  """Collect string-literal words below ``node`` in source order.

  Order is what makes the family readable: the domain is the token directly
  after the entrypoint, in both the wrapper shape (a
  ``"damage_model.py <domain>"`` head string plus loose arguments) and the raw
  ``subprocess.run([...])`` list shape. ``ast.iter_child_nodes`` walks fields in
  source order, unlike ``ast.walk``.
  """
  if isinstance(node, ast.Constant):
    return node.value.split() if isinstance(node.value, str) else []
  tokens: list[str] = []
  for child in ast.iter_child_nodes(node):
    tokens.extend(_string_tokens(child))
  return tokens


def _cli_family(call: ast.Call) -> str:
  tokens = _string_tokens(call)
  for index, token in enumerate(tokens):
    entrypoint = token.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if not entrypoint.endswith(".py"):
      continue
    if entrypoint != "damage_model.py":
      return entrypoint
    if index + 1 < len(tokens):
      return tokens[index + 1]
    break
  return UNRESOLVED_FAMILY


def _spawn_sites() -> list[tuple[str, str]]:
  """Return ``(family, "file:line")`` for every spawning call in this tier."""
  sites: list[tuple[str, str]] = []
  for path in sorted(AUDIT_DIR.glob("*.py")):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
      if isinstance(node, ast.Call) and ast.unparse(node.func) in SPAWNING_CALLS:
        sites.append((_cli_family(node), f"{path.name}:{node.lineno}"))
  return sites


def test_audit_cli_spawn_sites_stay_within_budget() -> None:
  sites = _spawn_sites()
  assert len(sites) <= MAX_SPAWN_CALL_SITES, (
    f"{len(sites)} subprocess spawn sites exceed the budget of "
    f"{MAX_SPAWN_CALL_SITES}; route new CLI assertions through "
    "tests.support.cli.run_maintenance_cli_in_process instead of adding a "
    f"spawn: {sorted(location for _, location in sites)}"
  )


def test_every_cli_family_keeps_an_end_to_end_subprocess_smoke() -> None:
  per_family = Counter(family for family, _ in _spawn_sites())
  missing = sorted(REQUIRED_SMOKE_FAMILIES - set(per_family))
  assert not missing, (
    "each damage_model.py CLI family must keep at least one real subprocess "
    "run so the entrypoint wiring stays covered; families with none left: "
    f"{missing}"
  )


def test_spawn_sites_resolve_to_the_known_cli_families() -> None:
  sites = _spawn_sites()
  unresolved = sorted(
    location for family, location in sites if family == UNRESOLVED_FAMILY
  )
  assert not unresolved, (
    "a spawn site names no recognizable maintenance entrypoint, so the budget "
    f"cannot attribute it to a CLI family: {unresolved}"
  )

  unexpected = sorted(
    {family for family, _ in sites} - REQUIRED_SMOKE_FAMILIES
  )
  assert not unexpected, (
    "a spawn site targets a CLI family this budget does not track; add it to "
    f"REQUIRED_SMOKE_FAMILIES together with its smoke: {unexpected}"
  )
