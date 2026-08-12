from __future__ import annotations

import os
import subprocess
import sys
import unittest


_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_BUILD_GPU = os.path.join(_REPO_ROOT, "build-gpu")


class CudaImportOrderTests(unittest.TestCase):
  # NOTE(I57): the CUDA import-order check needs a GPU CUDA build tree
  # (build-gpu/) so the subprocess can import the GPU-built ef_py. Worktrees
  # that only carry the CPU build-local-win snapshot (or point CMO_BUILD_DIR at
  # a shared CPU snapshot) never materialize build-gpu/, so this is an
  # environmental precondition, not a product defect: skip conditionally on its
  # presence rather than failing closed with ModuleNotFoundError: ef_py. See
  # docs/plan/archive/unified_architecture_program_completed_20260727/t6_residual_ledger.md section 5/8
  # (build-gpu-absent environmental red).
  @unittest.skipUnless(
    os.path.isdir(_BUILD_GPU),
    "requires the build-gpu/ GPU CUDA build tree (absent on CPU-only "
    "worktrees/snapshots); see t6_residual_ledger.md section 5/8 "
    "build-gpu-absent environmental red",
  )
  def test_world_batch_vec_env_import_after_torch_runtime_setup(self) -> None:
    repo_root = _REPO_ROOT
    build_gpu = _BUILD_GPU
    flecs_build = os.path.join(build_gpu, "_deps", "flecs-build")
    env = dict(os.environ)
    env["PYTHONPATH"] = build_gpu + os.pathsep + repo_root
    env["LD_LIBRARY_PATH"] = flecs_build + os.pathsep + env.get("LD_LIBRARY_PATH", "")
    proc = subprocess.run(
      [
        sys.executable,
        "-c",
        "import python.rl.runtime.world_batch_vec_env as wb; print('ok', wb.WorldBatchVecEnv.__name__)",
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
