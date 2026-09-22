from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]

_NAVAL_STANDARD_EN = REPO_ROOT / "docs" / "domains" / "naval" / "standards" / "minimal_task_structure.md"
_NAVAL_STANDARD_ZH = REPO_ROOT / "docs" / "domains" / "naval" / "standards" / "minimal_task_structure.zh.md"
_NAVAL_ENUMS = (
  REPO_ROOT
  / "src"
  / "components"
  / "domains"
  / "naval"
  / "tasking"
  / "naval_tasking_enums.h"
)
_NAVAL_PROFILE = REPO_ROOT / "python" / "rl" / "profile" / "naval_profile.py"

_STARTER_TASKS = ("TASK_SCREEN", "TASK_SUPPORT", "TASK_PATROL", "TASK_RECOVER")
_TASK_SECTION_RE = re.compile(
  r"(?ms)^###\s+`(?P<task>TASK_[A-Z_]+)`\s*$\n"
  r"(?P<body>.*?)(?=^##(?:#|\s)|\Z)"
)
_INLINE_TOKEN_RE = re.compile(r"`([^`\r\n]+)`")

_EXPECTED_TASK_TOKENS = {
  "TASK_SCREEN": frozenset(
    {
      "task_family",
      "Escort",
      "coordination_mode",
      "Screen",
      "warfare_role_code",
      "ScreenCommander",
      "naval_station_type",
      "officer_in_tactical_command",
    }
  ),
  "TASK_SUPPORT": frozenset(
    {
      "task_family",
      "Escort",
      "coordination_mode",
      "Support",
      "warfare_role_code",
      "LogisticsCoordinator",
      "naval_station_type",
      "officer_in_tactical_command",
    }
  ),
  "TASK_PATROL": frozenset(
    {
      "task_family",
      "Patrol",
      "warfare_role_code",
      "SeaControlCommander",
      "naval_station_type",
      "PatrolStation",
      "officer_in_tactical_command",
    }
  ),
  "TASK_RECOVER": frozenset(
    {
      "task_family",
      "Recover",
      "coordination_mode",
      "Detached",
      "warfare_role_code",
      "Unspecified",
      "naval_station_type",
      "officer_in_tactical_command",
    }
  ),
}


def _task_tokens(path: Path) -> dict[str, frozenset[str]]:
  text = path.read_text(encoding="utf-8")
  sections: dict[str, frozenset[str]] = {}
  for match in _TASK_SECTION_RE.finditer(text):
    tokens: set[str] = set()
    for token in _INLINE_TOKEN_RE.findall(match.group("body")):
      if "=" in token:
        key, value = token.split("=", 1)
        tokens.update({key.strip(), value.strip()})
      else:
        tokens.add(token.strip())
    sections[match.group("task")] = frozenset(tokens)
  return sections


def test_bilingual_naval_standard_tokens_and_support_mapping_are_aligned() -> None:
  english = _task_tokens(_NAVAL_STANDARD_EN)
  chinese = _task_tokens(_NAVAL_STANDARD_ZH)

  assert tuple(english) == _STARTER_TASKS
  assert tuple(chinese) == _STARTER_TASKS
  assert english == chinese
  assert english == _EXPECTED_TASK_TOKENS

  enums = _NAVAL_ENUMS.read_text(encoding="utf-8")
  assert re.search(
    r"enum class NavalWarfareRole\s*:\s*int\s*\{.*?\bLogisticsCoordinator\s*=\s*5\s*,?",
    enums,
    re.DOTALL,
  )
  assert "SupportCoordinator" not in enums

  profile = _NAVAL_PROFILE.read_text(encoding="utf-8")
  assert re.search(
    r'if name == "TASK_SUPPORT":\s+return getattr\(namespace, "LogisticsCoordinator"\)',
    profile,
  )
  assert "SupportCoordinator" not in profile
