@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
cd /d "D:\workshop\Research\Echelon-Forge\.codex\worktrees\cuda-promotion"
cmake -S . -B build-cuda -G Ninja -DCMAKE_BUILD_TYPE=Release -DEF_ENABLE_CUDA_RESIDENT_BACKEND=ON -DCMAKE_CUDA_ARCHITECTURES=86
if errorlevel 1 (echo CONFIGURE_FAILED & exit /b 1)
cmake --build build-cuda --target ef_cuda_resident_backend ef_cuda_resident_full_window_runner ef_cuda_resident_lifecycle_test ef_cuda_resident_replay_test ef_cuda_resident_full_window_test ef_cuda_resident_full_window_cuda_probe ef_cuda_resident_cr2_matrix_cuda_probe ef_cuda_resident_rb9_cuda_probe ef_cuda_resident_resource_probe -j4
echo BUILD_EXIT=%ERRORLEVEL%
