from pathlib import Path

from tests.architecture.helpers import REPO_ROOT


def test_typed_mechanism_ports_adr_keeps_native_runtime_authoritative() -> None:
  adr = (REPO_ROOT / "docs" / "architecture" / "standards" /
         "typed_mechanism_ports_adr.md").read_text(encoding="utf-8")
  assert "no production activation" in adr
  assert "native runtime remains the sole execution authority" in adr
  assert "before provider or world publication" in adr
  assert "Instantaneous same-window cycles are rejected" in adr
  assert "builtin.default_compatibility" in adr
  assert "failure-domain taxonomy" in adr
