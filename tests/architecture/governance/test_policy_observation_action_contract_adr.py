from tests.architecture.helpers import REPO_ROOT


def test_policy_contract_adr_keeps_descriptor_non_authoritative() -> None:
  adr = (REPO_ROOT / "docs" / "architecture" / "standards" /
         "policy_observation_action_contract_adr.md").read_text(encoding="utf-8")
  assert "non-authoritative policy compatibility descriptor" in adr
  assert "before policy binding or runtime side effects" in adr
  assert "Unknown categories neither grant capability" in adr
  assert "DecisionModel" in adr
  assert "current maintained outputs" in adr
