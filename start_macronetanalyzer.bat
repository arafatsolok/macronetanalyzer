@echo off
setlocal EnableExtensions EnableDelayedExpansion

:: --------- CONFIG ---------
set "PY_VER_MAJOR=3"
set "PY_FULL_VER=3.12.6"
set "PY_INSTALLER_URL=https://www.python.org/ftp/python/3.12.6/python-3.12.6-amd64.exe"
set "APP_CACHE=%APPDATA%\NetCache"
set "LOG=%APP_CACHE%\netsetup.log"
set "THISDIR=%~dp0"
set "PY_SETUP=%THISDIR%setup_macronetanalyzer.py"
:: --------------------------

:: Ensure cache dir exists (hidden)
if not exist "%APP_CACHE%" (
  md "%APP_CACHE%" 2>nul
  attrib +h "%APP_CACHE%" 2>nul
)

:: ---- Logging helper ----
set "TS=%date% %time%"
call :log "Starting setup process..."
echo.

:: Prefer the Python launcher if present
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  call :log "Found 'py' launcher."
  py -%PY_VER_MAJOR% -V >nul 2>nul
  if %ERRORLEVEL%==0 (
    for /f "usebackq tokens=1,2*" %%A in (`py -%PY_VER_MAJOR% -V 2^>^&1`) do set "PY_FOUND=%%A %%B"
    call :log "Python detected via launcher: !PY_FOUND!"
    set "PY_CMD=py -%PY_VER_MAJOR%"
    goto :check_deps
  )
)

:: Fallback: python3
where python3 >nul 2>nul
if %ERRORLEVEL%==0 (
  for /f "usebackq tokens=*" %%A in (`python3 --version 2^>^&1`) do set "PY_FOUND=%%A"
  call :log "Python detected: !PY_FOUND!"
  set "PY_CMD=python3"
  goto :check_deps
)

:: Fallback: python
where python >nul 2>nul
if %ERRORLEVEL%==0 (
  for /f "usebackq tokens=*" %%A in (`python --version 2^>^&1`) do set "PY_FOUND=%%A"
  echo !PY_FOUND! | findstr /c:"Python %PY_VER_MAJOR%" >nul
  if %ERRORLEVEL%==0 (
    call :log "Python detected: !PY_FOUND!"
    set "PY_CMD=python"
    goto :check_deps
  )
)

:: ---- Download & install Python ----
call :log "Python not found; downloading %PY_FULL_VER% ..."
set "INSTALLER=%TEMP%\py_install_%RANDOM%.exe"

:: Prefer modern PowerShell downloader
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
  "Try { Invoke-WebRequest -Uri '%PY_INSTALLER_URL%' -OutFile '%INSTALLER%' -UseBasicParsing; exit 0 } Catch { exit 1 }"
if not exist "%INSTALLER%" (
  call :log "Download failed via Invoke-WebRequest. Trying WebClient..."
  powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
    "(New-Object Net.WebClient).DownloadFile('%PY_INSTALLER_URL%', '%INSTALLER%')"
)

if not exist "%INSTALLER%" (
  call :log "ERROR: Failed to download Python installer."
  echo.
  echo Failed to download Python. See log: "%LOG%"
  exit /b 1
)

call :log "Installing Python silently..."
:: Per-user install; add to PATH for future sessions
"%INSTALLER%" /quiet InstallAllUsers=0 Include_launcher=1 PrependPath=1 SimpleInstall=1
set "INSTALL_RC=%ERRORLEVEL%"
del /q "%INSTALLER%" 2>nul

if not "%INSTALL_RC%"=="0" (
  call :log "ERROR: Python installer returned code %INSTALL_RC%."
  echo.
  echo Python installation failed (code %INSTALL_RC%). See log: "%LOG%"
  exit /b 1
)

:: Attempt to locate the newly installed python for THIS session
set "PY_CMD="
:: Try launcher again
where py >nul 2>nul && set "PY_CMD=py -%PY_VER_MAJOR%"
if not defined PY_CMD (
  :: Default per-user path pattern
  for /f "usebackq tokens=* delims=" %%P in (`
    powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
      "$p=(Get-ChildItem -Path $env:LocalAppData\Programs\Python -Directory -ErrorAction SilentlyContinue ^| Sort-Object Name -Descending ^| Select-Object -First 1).FullName; if($p){Join-Path $p 'python.exe'}"
  `) do set "PY_CAND=%%P"
  if exist "!PY_CAND!" set "PY_CMD=!PY_CAND!"
)

if not defined PY_CMD (
  call :log "WARNING: Could not resolve python.exe path for current session. Will try 'python'."
  set "PY_CMD=python"
)

:: Quick sanity check
"%PY_CMD%" --version >nul 2>nul
if %ERRORLEVEL%==0 (
  for /f "usebackq tokens=*" %%A in (`"%PY_CMD%" --version 2^>^&1`) do set "PY_FOUND=%%A"
  call :log "Python installed and usable: !PY_FOUND!"
) else (
  call :log "ERROR: Python not usable after install."
  echo.
  echo Python appears installed but not yet usable in this session.
  echo Please open a NEW terminal and re-run this script.
  exit /b 1
)

:check_deps
call :log "Running setup_macronetanalyzer.py ..."
if not exist "%PY_SETUP%" (
  call :log "ERROR: Setup script not found at %PY_SETUP%."
  echo Setup script not found: "%PY_SETUP%"
  exit /b 1
)

"%PY_CMD%" "%PY_SETUP%"
set "RC=%ERRORLEVEL%"

if "%RC%"=="0" (
  call :log "Setup completed successfully."
  echo Setup completed successfully.
) else (
  call :log "ERROR: Setup failed with code %RC%."
  echo Setup failed with exit code %RC%. See log: "%LOG%"
  exit /b %RC%
)

echo.
pause
exit /b 0

:: --------- functions ----------
:log
set "TS=%date% %time%"
echo %~1
>>"%LOG%" echo %TS% - %~1
goto :eof
