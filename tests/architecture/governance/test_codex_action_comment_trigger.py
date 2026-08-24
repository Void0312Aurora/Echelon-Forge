from __future__ import annotations

from pathlib import Path


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


def test_codex_action_is_pinned_and_avoids_protected_config_overrides() -> None:
  workflow = WORKFLOW.read_text(encoding="utf-8")
  pinned_action = (
    "uses: openai/codex-action@"
    "52fe01ec70a42f454c9d2ebd47598f9fd6893d56 # v1.11"
  )

  assert workflow.count(pinned_action) == 5
  assert "uses: openai/codex-action@v1" not in workflow
  assert "service_tier" not in workflow
  assert """CODEX_ARGS: '["--config","disable_response_storage=true"]'""" in workflow
