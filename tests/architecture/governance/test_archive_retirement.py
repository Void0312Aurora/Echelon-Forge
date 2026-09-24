"""Keep documentation history on the one admitted retention route.

422 Markdown files and two figures sat under an `archive/`, `Archive/`, or
`temp/` path component: a parallel documentation tree with no owner, no SLA,
and 78 live pages pointing into it. They were deleted, and git history became
the archive. `docs/engineering/documentation/reference/retired_documents.json`
records the last commit that modified each one, so `git show <commit>:<path>`
still prints the retired content.

P7-A admits one explicitly registered owner-local archive for the already
accepted Cordis composition history. It has an owner, archived README metadata,
and bilingual index routes. Every other archive path remains forbidden.

Two ways the retirement could quietly undo itself, one guarded by each test
below: a new document lands under a resurrected archive path, or a live page
grows a Markdown link to a path that no longer exists. The second failure is
already caught by the link audit, but only as "target does not exist"; naming
the retrieval address in the failure message is the difference between a
reviewer restoring the file and a reviewer citing the ledger.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.governance_audit


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_ROOT = REPO_ROOT / "docs"
REGISTRY_PATH = DOCS_ROOT / "engineering/documentation/reference/retired_documents.json"
RETENTION_AUTHORITY_PATH = (
  DOCS_ROOT / "engineering/documentation/reference/retention_authority.json"
)
RETIRED_DIR_NAMES = frozenset({"archive", "Archive", "temp"})


def _git_lines(*args: str) -> list[str]:
  result = subprocess.run(
    ["git", *args],
    cwd=REPO_ROOT,
    check=True,
    capture_output=True,
    text=True,
    encoding="utf-8",
  )
  return [line for line in result.stdout.splitlines() if line]


def _tracked_present_docs() -> list[str]:
  """Tracked paths under `docs/` that still exist in the working tree.

  Subtracting `--deleted` keeps the gate honest while a retirement is staged
  but not yet committed: the index still carries those paths, and reporting
  them would be a false failure. On a clean checkout the subtraction is empty
  and this is exactly `git ls-files -- docs`.
  """
  return sorted(set(_git_lines("ls-files", "--", "docs")) - set(_git_lines("ls-files", "--deleted", "--", "docs")))


@pytest.fixture(scope="module")
def retention_authority() -> dict:
  payload = json.loads(RETENTION_AUTHORITY_PATH.read_text(encoding="utf-8"))
  assert payload["schema_version"] == 1
  assert payload["policy_id"] == "documentation_retention.v1"
  return payload


def _governed_archive_roots(retention_authority: dict) -> tuple[str, ...]:
  routes = retention_authority["history_routes"]
  owner_local = routes["owner_local_archive"]
  return tuple(item["path"] for item in owner_local["allowed_roots"])


def _governed_archive_files(retention_authority: dict) -> tuple[str, ...]:
  return tuple(retention_authority["history_routes"]["owner_local_archive"]["allowed_files"])


def _is_under(relative: str, root: str) -> bool:
  return relative == root or relative.startswith(root.rstrip("/") + "/")


@pytest.fixture(scope="module")
def registry() -> dict[str, dict[str, str]]:
  payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
  assert payload["schema_version"] == 1
  documents: dict[str, dict[str, str]] = payload["documents"]
  assert len(documents) == payload["total"]
  assert documents, "an empty registry would make the link assertion vacuous"
  return documents


def test_no_tracked_document_lives_under_an_ungoverned_archive_path(
  retention_authority: dict,
) -> None:
  governed_roots = _governed_archive_roots(retention_authority)
  governed_files = _governed_archive_files(retention_authority)
  offenders = sorted(
    relative
    for relative in _tracked_present_docs()
    if RETIRED_DIR_NAMES.intersection(Path(relative).parts[1:-1])
    and relative not in governed_files
    and not any(_is_under(relative, root) for root in governed_roots)
  )

  assert offenders == [], (
    f"{len(offenders)} tracked file(s) use an ungoverned "
    f"{sorted(RETIRED_DIR_NAMES)} path component under docs/. Retire a "
    "superseded document through the retention authority or add an explicitly "
    "reviewed owner-local route:\n  "
    + "\n  ".join(offenders)
  )


def test_governed_owner_archive_is_indexed_and_metadata_bearing(
  retention_authority: dict,
) -> None:
  owner_local = retention_authority["history_routes"]["owner_local_archive"]
  assert owner_local["default"] == "forbidden"
  assert owner_local["required_readme_lifecycle"] == "archived"
  roots = owner_local["allowed_roots"]
  assert roots
  for path in owner_local["allowed_files"]:
    assert (REPO_ROOT / path).is_file(), path

  for entry in roots:
    root = REPO_ROOT / entry["path"]
    readme = REPO_ROOT / entry["readme"]
    assert root.is_dir(), entry["path"]
    assert readme.is_file(), entry["readme"]
    text = readme.read_text(encoding="utf-8")
    assert "Document kind:" in text
    assert "Lifecycle: `archived`" in text
    assert f"Owner: `{entry['owner']}`" in text
    for index in entry["indexes"]:
      assert (REPO_ROOT / index).is_file(), index


def test_the_retired_containers_are_gone_from_the_tracked_tree() -> None:
  tracked = _tracked_present_docs()
  resurrected = sorted(
    {
      f"docs/{root}/"
      for root in ("Archive", "evaluation", "manual", "plan", "task")
      if any(relative.startswith(f"docs/{root}/") for relative in tracked)
    }
  )

  assert resurrected == [], (
    "these legacy containers were retired on 2026-08-13 and must stay retired: "
    + ", ".join(resurrected)
  )


def test_no_live_document_links_to_a_retired_path(
  registry: dict[str, dict[str, str]],
) -> None:
  from tools.maintenance.docs_link import iter_markdown_links

  dangling: list[str] = []
  for relative in _tracked_present_docs():
    if not relative.endswith(".md"):
      continue
    source = REPO_ROOT / relative
    for link in iter_markdown_links(source.read_text(encoding="utf-8")):
      target = link.target.split("#", 1)[0].split("?", 1)[0].strip()
      if not target or "://" in target:
        continue
      try:
        resolved = (source.parent / target).resolve().relative_to(REPO_ROOT)
      except (ValueError, OSError):
        continue
      entry = registry.get(resolved.as_posix())
      if entry is None:
        continue
      dangling.append(
        f"{relative}:{link.line} -> {resolved.as_posix()}\n"
        f"      retrieve it with: git show {entry['last_commit']}:{resolved.as_posix()}\n"
        f"      ledger: {entry['ledger']}"
      )

  assert dangling == [], (
    f"{len(dangling)} Markdown link(s) point at a document retired on "
    "2026-08-13. Cite the retrieval address inline instead of linking, the way "
    "the root README does, or promote the content to a maintained owner page:\n  "
    + "\n  ".join(dangling)
  )


def test_every_registry_entry_is_retired_rather_than_still_tracked(
  registry: dict[str, dict[str, str]],
) -> None:
  """A registry row for a live file would send readers to a stale snapshot."""
  still_tracked = sorted(set(registry) & set(_tracked_present_docs()))

  assert still_tracked == [], (
    "these paths are recorded as retired but are tracked again; drop the "
    "registry row or delete the file:\n  " + "\n  ".join(still_tracked)
  )


def test_registry_rows_carry_a_usable_retrieval_address(
  registry: dict[str, dict[str, str]],
) -> None:
  ledgers = {"docs/archive_ledger.md", "docs/systems/archive_ledger.md"}
  for ledger in ledgers:
    assert (REPO_ROOT / ledger).is_file(), f"missing archive ledger: {ledger}"

  malformed = sorted(
    relative
    for relative, entry in registry.items()
    if not (
      entry["ledger"] in ledgers
      and entry["retired"] == "2026-08-13"
      and len(entry["last_commit"]) >= 7
      and all(character in "0123456789abcdef" for character in entry["last_commit"])
    )
  )

  assert malformed == [], (
    "these registry rows cannot be resolved back to a commit:\n  "
    + "\n  ".join(malformed[:20])
  )


def test_a_sampled_retrieval_address_still_resolves(
  registry: dict[str, dict[str, str]],
) -> None:
  """Prove the ledger is usable, not just well-formed.

  Sampling keeps the gate fast; a bad commit is a systematic error from
  regenerating the registry, not a per-row typo, so a handful of probes finds
  it. One probe per ledger keeps both owners covered.
  """
  probes = {}
  for relative, entry in sorted(registry.items()):
    probes.setdefault(entry["ledger"], (relative, entry["last_commit"]))

  assert len(probes) == 2, sorted(probes)
  for ledger, (relative, commit) in sorted(probes.items()):
    result = subprocess.run(
      ["git", "cat-file", "-e", f"{commit}:{relative}"],
      cwd=REPO_ROOT,
      capture_output=True,
    )
    assert result.returncode == 0, (
      f"{ledger} records `git show {commit}:{relative}`, but that object is "
      "not reachable from this checkout"
    )
