@echo off
setlocal
cd /d "%~dp0"
echo Building PortDetector...
if not exist "assets\icon.ico" (
  echo.
  echo [ERROR] Missing runtime icon asset: assets\icon.ico
  exit /b 1
)
if exist "dist\PortDetector.exe" (
  for /f %%I in ('powershell -NoProfile -Command "$p = Resolve-Path 'dist\\PortDetector.exe' -ErrorAction SilentlyContinue; if ($p) { Get-Process | Where-Object { $_.Path -eq $p.Path } | Select-Object -ExpandProperty Id -First 1 }"') do set "RUNNING_PORTDETECTOR_PID=%%I"
  if defined RUNNING_PORTDETECTOR_PID (
    echo.
    echo [ERROR] Existing packaged PortDetector.exe is still running ^(PID %RUNNING_PORTDETECTOR_PID%^). Close it before build.
    exit /b 1
  )
)
set "PYI_WORKDIR=%TEMP%\PortDetector-pyinstaller-%RANDOM%%RANDOM%"
pyinstaller --clean --noconfirm --workpath "%PYI_WORKDIR%" PortDetector.spec
if errorlevel 1 (
  echo.
  echo [ERROR] PyInstaller build failed.
  exit /b 1
)

if not exist "dist\PortDetector.exe" (
  echo.
  echo [ERROR] Built executable not found: dist\PortDetector.exe
  exit /b 1
)

set "DOCTOR_EXPORT=%TEMP%\PortDetector-desktop-doctor.json"
if exist "%DOCTOR_EXPORT%" del /q "%DOCTOR_EXPORT%"

echo.
echo Running packaged doctor smoke...
"dist\PortDetector.exe" --doctor --doctor-export "%DOCTOR_EXPORT%"
if errorlevel 1 (
  echo.
  echo [ERROR] Packaged doctor smoke failed.
  exit /b 1
)

if not exist "%DOCTOR_EXPORT%" (
  echo.
  echo [ERROR] Packaged doctor export missing: %DOCTOR_EXPORT%
  exit /b 1
)

echo.
echo Packaged doctor export: %DOCTOR_EXPORT%
echo Build complete! Check dist\PortDetector.exe
if exist "%PYI_WORKDIR%" rmdir /s /q "%PYI_WORKDIR%" >nul 2>&1
