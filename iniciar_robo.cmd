@echo off
cd /d "%~dp0"
if exist ".runtime\python\python.exe" (
  ".runtime\python\python.exe" robo.py %*
) else (
  python robo.py %*
)
pause
