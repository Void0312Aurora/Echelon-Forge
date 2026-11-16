from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()


def test_candidate_journals_survive_another_process_owner_cleanup(tmp_path: Path) -> None:
    native = pytest.importorskip("ef_runtime_candidate_py")
    # Both processes start their native resource sequence at one, deliberately
    # using the same host identity and temporary root. A process-local counter
    # is not a journal ownership boundary.
    work = textwrap.dedent(
        """
        import ef_runtime_candidate_py as native
        candidate = native.RuntimeKernelCandidate(12345, 67890)
        assert candidate.start()
        assert candidate.step_native('a' * 64)
        branch = candidate.fork_native('b' * 64, 4)
        assert branch is not None
        saved = branch.checkpoint()
        assert saved is not None
        assert saved.step('c' * 64)
        """
    )
    script = work + textwrap.dedent(
        f"""
        import gc
        import pathlib
        import subprocess
        import sys
        import tempfile
        root = pathlib.Path(tempfile.gettempdir())
        owned = set(root.glob('echelon_forge_p4c_*/runtime.wal'))
        assert len(owned) == 3, sorted(str(path) for path in owned)
        other = subprocess.run([sys.executable, '-c', {work!r}],
                               capture_output=True, text=True, timeout=60)
        assert other.returncode == 0, other.stdout + other.stderr
        assert all(path.exists() for path in owned)
        assert set(root.glob('echelon_forge_p4c_*/runtime.wal')) == owned
        continued = saved.checkpoint()
        assert continued is not None
        assert continued.step('d' * 64)
        assert branch.step('e' * 64)
        assert candidate.shutdown()
        del continued, saved, branch, candidate
        gc.collect()
        assert not list(root.iterdir()), list(root.iterdir())
        """
    )
    environment = dict(os.environ)
    environment.update(TMP=str(tmp_path), TEMP=str(tmp_path), TMPDIR=str(tmp_path))
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(Path(native.__file__).resolve().parent), environment.get("PYTHONPATH", "")]
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
