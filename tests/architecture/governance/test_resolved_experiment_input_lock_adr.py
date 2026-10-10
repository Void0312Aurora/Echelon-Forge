from tests.architecture.helpers import REPO_ROOT


def test_resolved_experiment_adr_reuses_native_evidence_authorities() -> None:
  adr = (REPO_ROOT / "docs" / "architecture" / "standards" /
         "resolved_experiment_input_lock_adr.md").read_text(encoding="utf-8")
  assert "references, rather than recomputes or replaces" in adr
  assert "RunReceipt" in adr
  assert "realized Flecs scheduler topology" in adr
  assert "partially failed or state-uncertain" in adr
  assert "No second ledger" in adr
