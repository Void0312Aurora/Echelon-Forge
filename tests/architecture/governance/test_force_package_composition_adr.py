from tests.architecture.helpers import REPO_ROOT


def test_force_package_adr_separates_membership_and_runtime_authority() -> None:
  adr = (REPO_ROOT / "docs" / "architecture" / "standards" /
         "force_package_composition_adr.md").read_text(encoding="utf-8")
  assert "existing scenario entities" in adr
  assert "deterministic DAG" in adr
  assert "communications links" in adr
  assert "does not grant command authority" in adr
  assert "existing CSG compiler" in adr
  assert "before entity creation" in adr
