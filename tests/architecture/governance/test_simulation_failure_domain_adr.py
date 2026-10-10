from tests.architecture.helpers import REPO_ROOT


def test_failure_domain_adr_forbids_implicit_rollback_and_retry() -> None:
  adr = (REPO_ROOT / "docs" / "architecture" / "standards" /
         "simulation_failure_domain_adr.md").read_text(encoding="utf-8")
  assert "native world/ECS truth remains authoritative" in adr
  assert "unknown/untrusted state" in adr
  assert "callers may not transparently retry" in adr
  assert "A partial batch is never reported as synchronized success" in adr
  assert "bounded subprocess" in adr
