from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.governance_audit


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "codex-action.yml"


def _comment_task_block() -> str:
  workflow = WORKFLOW.read_text(encoding="utf-8")
  _, comment_task = workflow.split("\n  comment-task:\n", maxsplit=1)
  block, _ = comment_task.split("\n  post-comment-task:\n", maxsplit=1)
  return block


def test_comment_task_uses_an_exact_slash_codex_command() -> None:
  block = _comment_task_block()

  assert "name: Codex /codex comment task" in block
  assert "github.event.comment.body == '/codex'" in block
  assert "startsWith(github.event.comment.body, '/codex ')" in block
  assert "contains(github.event.comment.body" not in block
  assert "@codex" not in block


def test_comment_task_remains_owner_scoped_and_read_only() -> None:
  block = _comment_task_block()

  assert "github.actor == 'Void0312Aurora'" in block
  assert '["OWNER","MEMBER","COLLABORATOR"]' in block
  assert "sandbox: read-only" in block
