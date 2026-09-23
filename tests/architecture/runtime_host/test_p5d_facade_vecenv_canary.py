from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv  # noqa: E402
from tests.architecture.runtime_host.test_rollout_evidence_binding import (  # noqa: E402
    KEY,
    PACKAGE,
    PLAN,
    WHEEL,
    _write_admitted_records,
)
from tests.support._world_batch_vec_env_test_support import (  # noqa: E402
    _inline_vec_env_scenario,
)


ROOT = Path(__file__).resolve().parents[3]


def test_real_facade_vecenv_canary_reset_and_step_are_admission_bound(tmp_path: Path) -> None:
    release_path, receipt_path, store = _write_admitted_records(tmp_path)
    admission = store.read()
    assert admission is not None
    scenario_path = tmp_path / "canary_scenario.json"
    scenario_path.write_text(
        json.dumps(_inline_vec_env_scenario(), ensure_ascii=True), encoding="utf-8"
    )

    vec_env = WorldBatchVecEnv(
        scenario_path=str(scenario_path),
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        production_rollout_path=str(store.path),
        production_rollout_key=KEY,
        require_production_admission=True,
        production_release_id="release-evidence-test",
        production_manifest_sha256=str(admission.envelope["payload"]["manifest_sha256"]),
        production_plan_sha256=PLAN,
        production_release_manifest_path=str(release_path),
        production_run_receipt_path=str(receipt_path),
        production_package_digest=PACKAGE,
        production_wheel_digest=WHEEL,
    )
    try:
        vec_env.seed(17)
        observation = vec_env.reset()
        assert observation is not None
        assert vec_env._runtime_adapter.rollout_admission is not None
        assert vec_env._runtime_adapter.rollout_admission.production_authorized
        stepped, rewards, dones, infos = vec_env.step(
            np.zeros((1, 17), dtype=np.float32)
        )
        assert stepped is not None
        assert rewards.shape == (1,)
        assert dones.shape == (1,)
        assert len(infos) == 1
        assert vec_env._runtime_adapter.rollout_admission.production_authorized
    finally:
        vec_env.close()
