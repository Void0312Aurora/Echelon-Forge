# Tests Archive

`tests/archive/` stores historical test assets retained for provenance only.

Files here are not part of the maintained pytest or JSON contract surfaces.
Do not add new active regressions here. To restore an archived contract, move it
back under `tests/contracts/`, add it to the contract surface matrix or suite,
and verify the intended runner policy.
