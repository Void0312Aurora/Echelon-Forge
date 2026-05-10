from __future__ import annotations

import os
import subprocess
import sys
import unittest


class CudaImportOrderTests(unittest.TestCase):
    def test_world_batch_vec_env_import_after_torch_runtime_setup(self) -> None:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        build_gpu = os.path.join(repo_root, "build-gpu")
        flecs_build = os.path.join(build_gpu, "_deps", "flecs-build")
        env = dict(os.environ)
        env["PYTHONPATH"] = build_gpu + os.pathsep + repo_root
        env["LD_LIBRARY_PATH"] = flecs_build + os.pathsep + env.get("LD_LIBRARY_PATH", "")
        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                "import python.rl.world_batch_vec_env as wb; print('ok', wb.WorldBatchVecEnv.__name__)",
            ],
            cwd=repo_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(
            proc.returncode,
            0,
            msg=f"import failed\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
        )
        self.assertIn("ok WorldBatchVecEnv", proc.stdout)


if __name__ == "__main__":
    unittest.main()
