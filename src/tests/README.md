# C++ Unit Tests

These are C++-level tests for the Echelon Forge simulation engine, built on
[doctest](https://github.com/doctest/doctest) and integrated with CTest.

## Running

From the build directory:

```bash
# Build the test target
cmake --build . --target ef_test

# Run all C++ tests via CTest
ctest --test-dir . -R ef_test

# Run a single test suite by name
./ef_test --test-case="simulation_kernel_smoke*"

# Run all tests directly (verbose)
./ef_test -s
```

## Organisation

| File | Suite | Coverage |
|------|-------|----------|
| `test_main.cpp` | — | doctest `main()` entry point |
| `test_simulation_kernel_smoke.cpp` | `simulation_kernel_smoke` | Kernel lifecycle, spawn/step/observation/reset |
| `test_components_basic.cpp` | `components_basic` | Math utilities, component defaults, struct invariants |

## Adding Tests

1. Create a new `.cpp` file in this directory.
2. Register it in `CMakeLists.txt` under `EF_TEST_SOURCES`.
3. Use `TEST_SUITE("your_suite_name")` to group related tests.
4. Rebuild `ef_test` and run `ctest` to verify.
