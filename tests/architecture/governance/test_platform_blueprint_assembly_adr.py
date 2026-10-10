from tests.architecture.helpers import REPO_ROOT


def test_platform_blueprint_adr_preserves_native_materialization_authority() -> None:
  adr = (REPO_ROOT / "docs" / "architecture" / "standards" /
         "platform_blueprint_assembly_adr.md").read_text(encoding="utf-8")
  assert "native factory remains the only owner" in adr
  assert "fail-closed before publication" in adr
  assert "UnitDefinition" in adr
  assert "CapabilityBundle" in adr
  assert "DefaultUnitFactory" in adr
  assert "arbitrary plugins" in adr
