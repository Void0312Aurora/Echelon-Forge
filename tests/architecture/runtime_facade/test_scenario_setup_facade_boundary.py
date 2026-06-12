from __future__ import annotations

from tests.architecture.runtime_facade.helpers import *


def test_scenario_loader_state_shell_classification_is_architecture_contract() -> None:
  shell_fields = frozenset(field_def.name for field_def in fields(ScenarioLoaderStateShell))
  expected_buckets = frozenset(EXPECTED_SCENARIO_LOADER_STATE_SHELL_CLASSIFICATION_BY_BUCKET)

  assert shell_fields == SCENARIO_LOADER_STATE_SHELL_ATTRS
  assert frozenset(SCENARIO_LOADER_STATE_SHELL_CLASSIFICATIONS) == shell_fields
  assert SCENARIO_LOADER_STATE_SHELL_CLASSIFICATION_BUCKETS == expected_buckets

  actual_by_bucket = {
    bucket: frozenset(
      attr
      for attr, classification in SCENARIO_LOADER_STATE_SHELL_CLASSIFICATIONS.items()
      if classification == bucket
    )
    for bucket in expected_buckets
  }
  assert actual_by_bucket == EXPECTED_SCENARIO_LOADER_STATE_SHELL_CLASSIFICATION_BY_BUCKET

def test_runtime_world_layout_setup_seam_stays_named_and_explicit() -> None:
  maintained_source = (REPO_ROOT / "python" / "scenario" / "runtime" / "world_setup.py").read_text(encoding="utf-8")
  diagnostics_source = (REPO_ROOT / "python" / "scenario" / "diagnostics" / "runtime_setup.py").read_text(
    encoding="utf-8"
  )
  package_source = (REPO_ROOT / "python" / "scenario" / "runtime" / "__init__.py").read_text(encoding="utf-8")

  assert "def build_runtime_world_layout_request(" in maintained_source
  assert "def apply_runtime_world_layout_request_maintained(setup_target: Any, request: Any) -> Any:" in maintained_source
  assert "def apply_world_setup_request_maintained(setup_target: Any, request: Any) -> list[int]:" in maintained_source
  assert 'hasattr(setup_target, "world_compatibility_quarantine")' in maintained_source
  assert 'hasattr(setup_target, "world")' in maintained_source
  assert 'not hasattr(setup_target, "facade")' in maintained_source
  assert "def apply_world_setup_payload_maintained(" in maintained_source
  assert "diagnostics" not in maintained_source
  assert ".world_compatibility_quarantine(" not in maintained_source

  assert "def apply_runtime_world_layout_request_diagnostics(runtime: Any, request: Any) -> Any:" in diagnostics_source
  assert "def apply_world_setup_payload_diagnostics(" in diagnostics_source
  assert "def apply_world_setup_request_diagnostics(" in diagnostics_source
  assert "def read_runtime_world_time_step_diagnostics(" in diagnostics_source
  assert "world_compatibility_quarantine" in diagnostics_source
  assert "apply_world_setup_batch(" in diagnostics_source
  assert "RuntimeWorldLayoutRequestCompat" in maintained_source
  assert "RuntimeWorldLayoutResultCompat" in maintained_source
  assert "apply_world_setup_payload_diagnostics" not in package_source
  assert "apply_runtime_world_layout_request_diagnostics" not in package_source

def test_wp24_scenario_setup_default_path_uses_maintained_facade_target() -> None:
  batch_apply = (SCENARIO_RUNTIME / "batch_apply.py").read_text(encoding="utf-8")
  adapter = _adapter_source()

  assert "def load_compiled_scenario_for_setup_target(" in batch_apply
  assert "def apply_world_layouts_to_setup_target(" in batch_apply
  assert "facade_setup_target" in batch_apply
  assert "apply_world_setup_payload_maintained(" in batch_apply
  assert "apply_world_setup_payload_compat(" not in batch_apply
  assert "compatibility_quarantine" not in batch_apply
  assert "diagnostics" not in batch_apply
  assert "from .world_setup import apply_world_setup_payload_maintained" in batch_apply
  assert "from .world_setup_compat import" not in batch_apply
  assert "from python.scenario.diagnostics" not in batch_apply
  assert "load_compiled_scenario_batch = load_compiled_scenario_for_setup_target" not in batch_apply
  assert "apply_world_layouts_to_batch = apply_world_layouts_to_setup_target" not in batch_apply

  assert "from python.scenario.runtime.world_setup import" in adapter
  assert "from python.scenario.runtime.world_setup_compat import" not in adapter
  assert "from python.scenario.diagnostics" not in adapter
  assert "apply_world_setup_request_maintained(self.facade, request)" in adapter
  assert "requires maintained BatchWorldSetupRequest bindings" in adapter

def test_wp24_legacy_scenario_runtime_shim_is_removed_from_python_surface() -> None:
  assert not (REPO_ROOT / "python" / "scenario_runtime.py").exists()

def test_wp24_maintained_python_paths_do_not_import_diagnostics_scenario_setup() -> None:
  violations: list[tuple[str, int, str]] = []
  for root in (REPO_ROOT / "python", REPO_ROOT / "gym_envs"):
    for path in root.rglob("*.py"):
      rel = path.relative_to(REPO_ROOT).as_posix()
      if rel.startswith("python/scenario/diagnostics/"):
        continue
      for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if "python.scenario.diagnostics" in stripped:
          violations.append((rel, lineno, stripped))

  assert not violations, (
    "maintained Python runtime paths must import python.scenario.runtime directly; "
    f"diagnostics scenario setup imports found: {violations}"
  )

def test_wp24_scenario_raw_setup_fallbacks_are_quarantined_by_name() -> None:
  setup_source = (REPO_ROOT / "python" / "scenario" / "diagnostics" / "runtime_setup.py").read_text(
    encoding="utf-8"
  )
  tree = ast.parse(setup_source)
  offenders: list[tuple[str, int, str]] = []

  for node in ast.walk(tree):
    if not isinstance(node, ast.FunctionDef):
      continue
    for child in ast.walk(node):
      if not (
        isinstance(child, ast.Call)
        and isinstance(child.func, ast.Attribute)
        and child.func.attr in {"apply_world_setup_batch", "apply_world_layout"}
      ):
        continue
      if "diagnostics" not in node.name:
        offenders.append((node.name, int(getattr(child, "lineno", 0) or 0), child.func.attr))

  assert not offenders, f"raw setup fallback calls must stay inside diagnostics helpers: {offenders}"

def test_wp24_scenario_runtime_does_not_construct_raw_runtime_on_production_path() -> None:
  violations: list[tuple[str, int, str]] = []
  forbidden_markers = ("ef_py.SimulationKernel(", "ef_py.WorldBatchRuntime(")

  for path in SCENARIO_RUNTIME.rglob("*.py"):
    rel = path.relative_to(REPO_ROOT).as_posix()
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
      stripped = line.strip()
      for marker in forbidden_markers:
        if marker in stripped:
          violations.append((rel, lineno, stripped))

  assert not violations, (
    "scenario runtime setup must use maintained facade/adapter setup targets instead of "
    f"constructing raw runtime objects: {violations}"
  )

def test_wp24_universal_env_raw_kernel_path_is_explicit_compatibility_quarantine() -> None:
  universal_env = UNIVERSAL_ENV.read_text(encoding="utf-8")
  train_source = (REPO_ROOT / "train.py").read_text(encoding="utf-8")

  assert "runtime_compatibility_enabled: bool = False" in universal_env
  assert "self.runtime_compatibility_enabled = _normalize_runtime_compatibility_enabled(" in universal_env
  assert "if not self.runtime_compatibility_enabled:" in universal_env
  assert "_raw_universal_env_compatibility_required_message()" in universal_env
  assert universal_env.index("if not self.runtime_compatibility_enabled:") < universal_env.index(
    "self.sim = ef_py.SimulationKernel()"
  )
  assert "ef_py.WorldBatchRuntime(" not in universal_env
  assert "WorldBatchVecEnv/RuntimeFacadeAdapter" in universal_env

  assert "The standard UniversalEnv execution path owns a raw SimulationKernel" in train_source
  assert "runtime.world_batch_vec_env=true" in train_source
  assert "env.runtime_compatibility_enabled=true" not in train_source
  assert "Direct raw UniversalEnv diagnostics must be run outside" in train_source

def test_wp24_legacy_runtime_and_backend_inputs_stay_retired() -> None:
  production_entrypoints = [
    REPO_ROOT / "gym_envs" / "scenario_loader" / "common.py",
    REPO_ROOT / "gym_envs" / "universal_env.py",
    REPO_ROOT / "tools" / "eval" / "sb3_eval_base.py",
    REPO_ROOT / "tools" / "diagnostics" / "arma_proxy_backend_echelon_env.py",
    REPO_ROOT / "tools" / "diagnostics" / "leader_perf_probe.py",
    REPO_ROOT / "tools" / "diagnostics" / "benchmarks" / "policy_observation_bridge.py",
    REPO_ROOT / "tools" / "diagnostics" / "benchmarks" / "world_batch_vec_env.py",
  ]
  forbidden_snippets = (
    'choices=["compiled", "legacy"]',
    'choices=["auto", "legacy", "compiled", "gpu_host"]',
    'choices=["case", "auto", "legacy", "compiled", "gpu_host"]',
    'return "legacy"',
    "return 'legacy'",
  )
  offenders: list[tuple[str, str]] = []

  for path in production_entrypoints:
    rel = path.relative_to(REPO_ROOT).as_posix()
    source = path.read_text(encoding="utf-8")
    for snippet in forbidden_snippets:
      if snippet in source:
        offenders.append((rel, snippet))

  assert not offenders, (
    "legacy runtime/backend string inputs must stay retired from maintained CLI and "
    f"normalizer surfaces: {offenders}"
  )

def test_wp24_public_vec_env_runtime_compatibility_flag_is_retired() -> None:
  world_batch_source = (
    REPO_ROOT / "python" / "rl" / "runtime" / "world_batch_vec_env.py"
  ).read_text(encoding="utf-8")
  cooperative_source = (
    REPO_ROOT / "python" / "rl" / "runtime" / "cooperative_world_batch_vec_env.py"
  ).read_text(encoding="utf-8")

  for source in (world_batch_source, cooperative_source):
    assert "runtime_compatibility_enabled: bool = False" in source
    assert "runtime_compatibility_enabled=True has been removed from maintained VecEnv paths" in source
    assert "_RuntimeFacadeAdapter(\n            self.n_envs,\n            runtime_compatibility_enabled=True" not in source
    assert "_RuntimeFacadeAdapter(\n            self.world_count,\n            runtime_compatibility_enabled=True" not in source
