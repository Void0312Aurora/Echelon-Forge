from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path

from python.testing.runtime import build_dir, ensure_repo_imports


class DiagnosticsImportOrderTests(unittest.TestCase):
    def test_common_import_prefers_repo_build_ef_py(self) -> None:
        ensure_repo_imports()

        sys.modules.pop("ef_py", None)
        sys.modules.pop("tools.diagnostics.common", None)

        common = importlib.import_module("tools.diagnostics.common")
        ef_py = importlib.import_module("ef_py")

        expected_root = Path(build_dir()).resolve()
        module_path = Path(str(getattr(ef_py, "__file__", ""))).resolve()

        self.assertEqual(common.ef_py, ef_py)
        self.assertTrue(str(module_path).startswith(str(expected_root)))
        self.assertTrue(hasattr(ef_py, "ConditionalObjectiveProperty"))
        self.assertTrue(hasattr(ef_py, "WorldBatchRuntime"))


if __name__ == "__main__":
    unittest.main()
