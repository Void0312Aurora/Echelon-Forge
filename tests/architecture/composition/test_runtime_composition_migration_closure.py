from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
TOOL_PATH = ROOT / "tools/maintenance/runtime_composition_migration_closure.py"
FIXTURE = (
    ROOT
    / "tests/architecture/composition/fixtures/default_runtime_composition_migration_closure.v1.json"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "runtime_composition_migration_closure", TOOL_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reseal(record: dict) -> dict:
    value = copy.deepcopy(record)
    value.pop("canonical_json", None)
    value.pop("closure_sha256", None)
    canonical = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    value["canonical_json"] = canonical
    value["closure_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return value


@pytest.fixture(scope="module")
def closure_context():
    tool = load_tool()
    record = json.loads(FIXTURE.read_text(encoding="utf-8"))
    tool.validate_record(record)
    return tool, record


def test_p8a_closure_fixture_is_schema_valid_and_fresh(closure_context) -> None:
    tool, record = closure_context
    assert record["closure_sha256"] == tool.sha256_text(record["canonical_json"])


def test_p8a_has_one_explicit_native_truth_path_and_no_retired_setters(closure_context) -> None:
    tool, record = closure_context
    tool.verify_source_truth()
    assert record["truth_path"]["native_composition_builder"] == (
        "runtime::providers::build_default_simulation_composition"
    )
    assert all(row["status"] == "absent" for row in record["retired_surfaces"])


def test_p8a_lexical_guards_reject_whitespace_fallback_and_comment_only_alias() -> None:
    tool = load_tool()
    assert tool.cpp_has_implicit_manifest_fallback(
        "if (\n  resolved_manifest_json . empty ( )\n) { use_hidden_default(); }"
    )
    disguised = """
      // SimulationKernel(runtime::providers::default_compatibility_resolved_manifest_json())
      SimulationKernel::SimulationKernel()
          : SimulationKernel(hidden_default_manifest()) {}
    """
    assert not tool.cpp_has_default_manifest_alias(disguised)
    assert tool.cpp_has_default_manifest_alias(
        """
        SimulationKernel::SimulationKernel()
            : SimulationKernel(
                runtime::providers::default_compatibility_resolved_manifest_json()) {}
        """
    )


def test_p8a_python_ast_inventory_covers_from_import_and_aliases() -> None:
    tool = load_tool()
    assert tool.python_source_calls_ef_py_symbol(
        "from ef_py import SimulationKernel as Kernel\nKernel()\n", "SimulationKernel"
    )
    assert tool.python_source_calls_ef_py_symbol(
        "import ef_py as native\nAlias = native.SimulationKernel\nAlias()\n",
        "SimulationKernel",
    )
    assert tool.python_source_calls_ef_py_symbol(
        "from ef_py import *\nSimulationKernel()\n", "SimulationKernel"
    )
    assert tool.python_source_calls_ef_py_symbol(
        "import ef_py\nnative = ef_py\nnative.SimulationKernel()\n",
        "SimulationKernel",
    )
    assert tool.python_source_calls_ef_py_symbol(
        "import ef_py\ngetattr(ef_py, 'SimulationKernel')()\n",
        "SimulationKernel",
    )
    assert tool.python_source_calls_ef_py_symbol(
        "__import__('ef_py').SimulationKernel()\n", "SimulationKernel"
    )
    assert tool.python_source_calls_ef_py_symbol(
        "import importlib\nimportlib.import_module('ef_py').SimulationKernel()\n",
        "SimulationKernel",
    )
    assert tool.python_source_calls_ef_py_symbol(
        "from importlib import import_module as load\nload('ef_py').SimulationKernel()\n",
        "SimulationKernel",
    )
    assert not tool.python_source_calls_ef_py_symbol(
        "# from ef_py import SimulationKernel\n# SimulationKernel()\n", "SimulationKernel"
    )
    assert tool.yaml_source_may_call_ef_py_symbol(
        "run: |\n  from ef_py import SimulationKernel as Kernel\n  Kernel()\n",
        "SimulationKernel",
    )
    assert not tool.yaml_source_may_call_ef_py_symbol(
        "# from ef_py import SimulationKernel as Kernel\n# Kernel()\n",
        "SimulationKernel",
    )


def test_p8a_cpp_inventory_covers_temporaries_qualified_names_and_using_aliases() -> None:
    tool = load_tool()
    assert tool.cpp_source_constructs_default_kernel("auto kernel = SimulationKernel{};")
    assert tool.cpp_source_constructs_default_kernel("auto kernel = ::SimulationKernel();")
    assert tool.cpp_source_constructs_default_kernel(
        "using Kernel = runtime::SimulationKernel; Kernel kernel;"
    )
    assert tool.cpp_source_constructs_default_kernel(
        "typedef runtime::SimulationKernel Kernel; auto kernel = Kernel{};"
    )
    assert not tool.cpp_source_constructs_default_kernel(
        "SimulationKernel kernel(load_hidden_manifest());"
    )
    assert tool.cpp_source_constructs_explicit_kernel(
        "SimulationKernel kernel(load_hidden_manifest());"
    )
    assert tool.cpp_source_constructs_runtime_facade(
        "using Facade = runtime::RuntimeFacade; Facade branch(1);"
    )
    assert tool.cpp_source_constructs_runtime_facade("auto branch = RuntimeFacade{1};")
    assert tool.cpp_source_constructs_default_kernel(
        "std::optional<SimulationKernel> kernel; kernel.emplace();"
    )
    assert tool.cpp_source_constructs_explicit_kernel(
        "std::optional<SimulationKernel> kernel; kernel.emplace(load_hidden_manifest());"
    )
    assert tool.cpp_source_constructs_default_kernel(
        "std::construct_at<SimulationKernel>(storage);"
    )
    assert tool.cpp_source_constructs_explicit_kernel(
        "std::construct_at<SimulationKernel>(storage, load_hidden_manifest());"
    )
    assert tool.cpp_source_constructs_explicit_kernel(
        "new (storage) SimulationKernel(load_hidden_manifest());"
    )
    assert tool.cpp_source_constructs_default_kernel("SimulationKernel kernels[2];")
    assert tool.cpp_source_constructs_default_kernel(
        "std::vector<SimulationKernel> kernels; kernels.emplace_back();"
    )
    assert tool.cpp_source_constructs_explicit_kernel(
        "std::vector<SimulationKernel> kernels; kernels.emplace_back(load_hidden_manifest());"
    )
    assert tool.cpp_source_constructs_default_kernel("std::make_optional<SimulationKernel>();")
    assert tool.cpp_source_constructs_explicit_kernel(
        "std::make_optional<SimulationKernel>(load_hidden_manifest());"
    )
    assert tool.cpp_source_constructs_default_kernel(
        "std::allocate_shared<SimulationKernel>(allocator);"
    )
    assert tool.cpp_source_constructs_explicit_kernel(
        "std::allocate_shared<SimulationKernel>(allocator, load_hidden_manifest());"
    )
    assert tool.cpp_source_constructs_runtime_facade(
        "std::vector<RuntimeFacade> facades; facades.emplace_back(1);"
    )
    assert not tool.cpp_source_constructs_default_kernel(
        '// auto kernel = SimulationKernel{};\nconst char *text = "SimulationKernel()";'
    )
    assert tool.cpp_source_references_symbol(
        "auto build = &runtime::providers::build_default_simulation_composition_for_testing;",
        "build_default_simulation_composition_for_testing",
    )
    assert not tool.cpp_source_references_symbol(
        "// build_default_simulation_composition_for_testing(kernel);\n"
        'const char *name = "build_default_simulation_composition_for_testing";',
        "build_default_simulation_composition_for_testing",
    )


def test_p8a_inventory_classifies_retained_callers_and_names_residual_owners(
    closure_context,
) -> None:
    _, record = closure_context
    surfaces = {row["surface_id"]: row for row in record["caller_inventory"]}
    assert surfaces["runtime_facade.maintained_host"]["callers"]
    assert surfaces["simulation_kernel.default_compatibility"]["callers"]
    assert surfaces["simulation_kernel.native_default_callers"]["callers"] == [
        "src/core/engine/world_batch_runtime.cpp",
        "src/main.cpp",
    ]
    assert "runtime_facade.native_internal_callers" not in surfaces
    assert surfaces["simulation_kernel.test_fault_injection"]["callers"] == [
        "src/core/engine/testing/simulation_kernel_composition_test_access.cpp",
        "src/core/engine/testing/simulation_kernel_composition_test_access.h",
        "src/tests/test_simulation_kernel_smoke.cpp"
    ]
    assert all(row["owner"] and row["activation_gate"] for row in record["residuals"])
    states = {row["cluster"]: row["state"] for row in record["acceptance_matrix"]}
    assert states["P0-A"] == "accepted"
    assert states["P6-B"] == "held"
    assert states["P8-A"] == "accepted"


def test_p8a_schema_rejects_forged_authority_and_extra_truth(closure_context) -> None:
    tool, record = closure_context
    validator = tool.jsonschema.Draft202012Validator(tool.load_json(tool.SCHEMA_PATH))
    forged_authority = copy.deepcopy(record)
    forged_authority["authority_chain"] = {f"forged_{index}": "x" for index in range(13)}
    with pytest.raises(tool.jsonschema.ValidationError):
        validator.validate(forged_authority)
    extra_truth = copy.deepcopy(record)
    extra_truth["truth_path"]["extra_truth"] = "hidden"
    with pytest.raises(tool.jsonschema.ValidationError):
        validator.validate(extra_truth)


def test_p8a_recomputes_underlying_request_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    tool = load_tool()
    original_load = tool.load_json

    def tampered_load(path: Path):
        value = original_load(path)
        if path.name == "default_runtime_composition_request.v1.json":
            value["required_capabilities"] = ["forged.capability"]
            value["configuration"]["seed"] = 999999
        return value

    monkeypatch.setattr(tool, "load_json", tampered_load)
    with pytest.raises((tool.ClosureError, tool.jsonschema.ValidationError)):
        tool.artifact_identities()


@pytest.mark.parametrize(
    "attack",
    [
        "authority",
        "caller",
        "setter",
        "residual",
        "node",
    ],
)
def test_p8a_rejects_resealed_closure_forgeries(
    attack: str, closure_context, monkeypatch: pytest.MonkeyPatch
) -> None:
    tool, accepted = closure_context
    record = copy.deepcopy(accepted)
    if attack == "authority":
        record["authority_chain"]["resolved_manifest_sha256"] = "0" * 64
    elif attack == "caller":
        record["caller_inventory"][0]["callers"].append("python/hidden_truth.py")
    elif attack == "setter":
        record["retired_surfaces"][0]["status"] = "retained"
    elif attack == "residual":
        record["residuals"][0]["owner"] = ""
    else:
        next(row for row in record["acceptance_matrix"] if row["cluster"] == "P6-B")["state"] = (
            "accepted"
        )
    monkeypatch.setattr(tool, "build_record", lambda: copy.deepcopy(accepted))
    with pytest.raises((tool.ClosureError, tool.jsonschema.ValidationError)):
        tool.validate_record(reseal(record))
