"""Executable Python layer policy for the cross-language dependency inventory."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from tools.architecture.dependency_inventory import DependencyEdge, Inventory, build_inventory

REPO_ROOT = Path(__file__).resolve().parents[2]
EXCEPTION_PATH = REPO_ROOT / "tests/architecture/fixtures/python_dependency_transitions.json"

# These are responsibility groups, not top-level package names. In particular,
# python/ contains both low-level contracts and high-level training code.
_PREFIX_ROLES = (
  ("python.tasking_contracts", "contracts"),
  ("python.architecture", "contracts"),
  ("python.angles", "contracts"),
  ("python.coercion", "contracts"),
  ("python.mission_obs_taxonomy", "contracts"),
  ("python.scenario_compiler", "substrate"),
  ("python.scenario", "substrate"),
  ("python.content", "substrate"),
  ("python.rl.tasking.bridge", "compatibility"),
  ("python.rl.runtime", "runtime_adapter"),
  ("python.rl", "policy"),
  ("python.models", "policy"),
  ("python.world_model", "policy"),
  ("python.testing", "test_support"),
  ("python.training_callbacks", "orchestration"),
  ("python.training", "orchestration"),
  ("python.experiment", "orchestration"),
  ("_world_model_train_impl", "orchestration"),
  ("gym_envs", "environment"),
  ("python.artifact_paths", "shared"),
  ("python.env_config", "shared"),
  ("python.runtime_bootstrap", "shared"),
  ("python", "shared"),
  ("tests", "external"),
  ("tools", "external"),
  ("examples", "external"),
  ("scripts", "external"),
  ("train", "external"),
  ("evaluate", "external"),
  ("world_model_train", "external"),
)

ALLOWED_TARGETS = {
  "contracts": frozenset({"contracts"}),
  "substrate": frozenset({"contracts", "substrate", "shared"}),
  "shared": frozenset({"contracts", "substrate", "shared"}),
  "environment": frozenset({"contracts", "substrate", "shared", "environment", "compatibility"}),
  "compatibility": frozenset({"contracts", "substrate", "shared", "policy", "runtime_adapter", "compatibility"}),
  "policy": frozenset({"contracts", "substrate", "shared", "environment", "policy", "runtime_adapter", "compatibility"}),
  "runtime_adapter": frozenset({"contracts", "substrate", "shared", "environment", "policy", "runtime_adapter", "compatibility"}),
  "orchestration": frozenset({"contracts", "substrate", "shared", "environment", "policy", "runtime_adapter", "orchestration", "compatibility"}),
  "test_support": frozenset({"contracts", "substrate", "shared", "environment", "policy", "runtime_adapter", "orchestration", "test_support", "compatibility", "external"}),
  "external": frozenset({"contracts", "substrate", "shared", "environment", "policy", "runtime_adapter", "orchestration", "test_support", "compatibility", "external"}),
}


def role_of(module: str) -> str:
  for prefix, role in _PREFIX_ROLES:
    if module == prefix or module.startswith(prefix + "."):
      return role
  return "unclassified"


@dataclass(frozen=True)
class PolicyFinding:
  source: str
  target: str
  source_role: str
  target_role: str
  code: str
  sites: int


def _transition_key(edge: DependencyEdge) -> tuple[str, str, str]:
  return edge.kind, edge.source, edge.target


def load_transitions(path: Path = EXCEPTION_PATH) -> dict[tuple[str, str, str], dict[str, object]]:
  payload = json.loads(path.read_text(encoding="utf-8"))
  if payload.get("schema_version") != "python_dependency_transition.v1":
    raise ValueError(f"unsupported transition schema: {payload.get('schema_version')!r}")
  entries = payload.get("entries")
  if not isinstance(entries, list):
    raise ValueError("transition fixture requires an entries list")
  transitions: dict[tuple[str, str, str], dict[str, object]] = {}
  for entry in entries:
    key = (entry["kind"], entry["source"], entry["target"])
    if key in transitions:
      raise ValueError(f"duplicate transition: {key}")
    if not all(str(entry.get(field, "")).strip() for field in ("owner", "reason", "exit_condition")):
      raise ValueError(f"transition requires owner, reason, exit_condition: {key}")
    if type(entry.get("max_sites")) is not int or entry["max_sites"] < 1:
      raise ValueError(f"transition requires positive max_sites: {key}")
    transitions[key] = entry
  return transitions


def check_python_policy(inventory: Inventory, transitions: dict[tuple[str, str, str], dict[str, object]]) -> list[PolicyFinding]:
  sites = Counter(_transition_key(edge) for edge in inventory.python_edges)
  findings: list[PolicyFinding] = []
  for module in inventory.python_modules:
    if role_of(module) == "unclassified":
      findings.append(PolicyFinding(module, "", "unclassified", "", "unclassified_module", 0))
  for (kind, source, target), count in sorted(sites.items()):
    source_role, target_role = role_of(source), role_of(target)
    if source_role == "unclassified" or target_role == "unclassified":
      findings.append(PolicyFinding(source, target, source_role, target_role, "unclassified_edge", count))
    elif target_role not in ALLOWED_TARGETS[source_role]:
      entry = transitions.get((kind, source, target))
      if entry is None:
        findings.append(PolicyFinding(source, target, source_role, target_role, "new_forbidden_edge", count))
      elif count > entry["max_sites"]:
        findings.append(PolicyFinding(source, target, source_role, target_role, "transition_growth", count))
  for (kind, source, target), entry in sorted(transitions.items()):
    count = sites.get((kind, source, target), 0)
    if count == 0:
      findings.append(PolicyFinding(source, target, role_of(source), role_of(target), "stale_transition", 0))
    elif role_of(target) in ALLOWED_TARGETS.get(role_of(source), frozenset()):
      findings.append(PolicyFinding(source, target, role_of(source), role_of(target), "unnecessary_transition", count))
  return findings


def classify_python_edges(inventory: Inventory, transitions: dict[tuple[str, str, str], dict[str, object]]) -> Counter[str]:
  states: Counter[str] = Counter()
  for edge in inventory.python_edges:
    source_role, target_role = role_of(edge.source), role_of(edge.target)
    if source_role == "unclassified" or target_role == "unclassified":
      states["unclassified"] += 1
    elif target_role in ALLOWED_TARGETS[source_role] and target_role == "compatibility":
      states["compatibility"] += 1
    elif target_role in ALLOWED_TARGETS[source_role]:
      states["allowed"] += 1
    elif _transition_key(edge) in transitions:
      states["transitional"] += 1
    else:
      states["forbidden"] += 1
  return states


def policy_report(inventory: Inventory, transitions: dict[tuple[str, str, str], dict[str, object]]) -> dict[str, object]:
  findings = check_python_policy(inventory, transitions)
  return {
    "states": dict(sorted(classify_python_edges(inventory, transitions).items())),
    "transition_count": len(transitions),
    "findings": [
      {
        "code": finding.code,
        "source": finding.source,
        "target": finding.target,
        "source_role": finding.source_role,
        "target_role": finding.target_role,
        "sites": finding.sites,
      }
      for finding in findings
    ],
  }


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--format", choices=("summary", "json"), default="summary")
  args = parser.parse_args()
  report = policy_report(build_inventory(), load_transitions())
  if args.format == "json":
    print(json.dumps(report, indent=2, ensure_ascii=True, sort_keys=True))
  else:
    print(f"transition_count={report['transition_count']}")
    print("states=" + ", ".join(f"{key}:{value}" for key, value in report["states"].items()))
    print(f"findings={len(report['findings'])}")
    for finding in report["findings"]:
      print(f"{finding['code']}: {finding['source']} -> {finding['target']} ({finding['sites']})")
  return 0 if not report["findings"] else 1


if __name__ == "__main__":
  raise SystemExit(main())
