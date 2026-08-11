call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
cd /d "D:\workshop\Research\Echelon-Forge\.codex\worktrees\cuda-promotion"
cmake --build build-cuda --target ef_cuda_resident_backend ef_cuda_resident_lifecycle_test ef_cuda_resident_replay_test ef_cuda_resident_full_window_test -j4
echo BUILD_EXIT=%ERRORLEVEL%
