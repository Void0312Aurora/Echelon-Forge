# P8 Linux Qualification Probe

Status: `2026-09-28` — current-branch Linux probe restored on HEI; the
platform remains partial and is not promoted into the bounded P8 acceptance.

## Environment and source

- Remote host: `HEI-FRP`, Linux x86_64, GCC 13.3.0, CMake 3.28.3, Ninja
  1.11.1.
- Source: isolated checkout
  `/tmp/echelon-forge-governance.ga3IQb` at branch
  `codex/long-horizon-governance-architecture`, commit `ae9de540`.
- The checkout has full history (`1154` commits); no maintained project
  checkout or service was modified.
- Python extension: matching build output
  `build-long-horizon-linux/ef_py.cpython-312-x86_64-linux-gnu.so`.

## Executed checks

```bash
cmake -S . -B build-long-horizon-linux \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON \
  -DEF_ENABLE_CUDA_EXPERIMENTS=OFF \
  -DEF_ENABLE_CUDA_RESIDENT_BACKEND=OFF \
  -DEF_FETCHCONTENT_REVALIDATE_PINS=OFF \
  -DCMAKE_CXX_FLAGS="-fconstexpr-loop-limit=1000000 -fconstexpr-ops-limit=1000000000"
cmake --build build-long-horizon-linux --target ef_core ef_py ef_test -j4
./build-long-horizon-linux/ef_test
PYTHONPATH=$PWD/build-long-horizon-linux /usr/bin/python3.12 -c \
  'import ef_py; print(ef_py.__file__)'
```

Results:

- CMake configure: **passed**.
- `ef_core`, `ef_py`, and `ef_test` build: **passed**.
- Matching CPython 3.12 extension import: **passed**.
- Native `ef_test`: **152 passed, 0 failed** out of 152 test cases (19388
  assertions; 19388 passed, 0 failed).

The initial probe at `1f968aad` exposed two failures:

1. `CPU reference pins the direct-pilot control-preparation stage trace`;
2. `RB4 CPU reference independently pins fixed-air identity and reset parity`.

Both failures asserted the CUDA fixed-air contract value `581`, while the
Linux Flecs CPU runtime returned the valid runtime entity value `1470`. The
repair at `ae9de540` keeps `581` owned by the CUDA-resident fixture, makes the
CPU/Flecs reference use its returned runtime IDs, and retains the state and
reset-parity checks. The rebuilt native suite now passes completely.

The first build attempt hit GCC's default constexpr loop limit while compiling
the generated plan string. Raising that compiler limit in the isolated build
directory allowed the build to complete; the repository does not carry that
temporary flag.

## Governance interpretation

The Linux governance subset remains green (`15 passed`), and the broader
Linux-applicable governance set passes (`76 passed`; the three omitted cases
are Windows `.pyd`-specific P2-B measurements). The matching native build,
import, and `ef_test` evidence is now green. Linux nevertheless remains
`partial` because package/CI qualification and a separate support-matrix
admission have not been performed.

This probe does **not** promote Linux/package qualification into P8 acceptance.
The current accepted scope remains the Windows CPU in-process lane. A separate
Linux package/CI admission packet is still required before treating Linux as
an admitted support row.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p8_linux_qualification_probe_20260928.md`
Owner: `release/runtime integration`
Last verified: `2026-09-28`
