@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
cd /d "D:\workshop\Research\Echelon-Forge\.codex\worktrees\cuda-promotion"
ctest --test-dir build-cuda -R "cuda_resident_lifecycle|cuda_resident_replay|cuda_resident_full_window" --output-on-failure
echo CTEST_EXIT=%ERRORLEVEL%
