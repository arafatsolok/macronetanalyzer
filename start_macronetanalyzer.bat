@echo off
setlocal EnableExtensions EnableDelayedExpansion

:: ===================== CONFIG =====================
set "APP_CACHE1=%APPDATA%\NetCache"
set "APP_CACHE2=%APPDATA%\.netcache"
set "LOG=%APP_CACHE1%\netsetup.log"
set "REPO_URL=https://github.com/arafatsolok/macronetanalyzer.git"

:: Candidate working dirs
set "CANDIDATE1=C:\macronetanalyzer"
set "CANDIDATE2=%USERPROFILE%\macronetanalyzer"
set "CANDIDATE3=%LOCALAPPDATA%\macronetanalyzer"
set "CANDIDATE4=%TEMP%\macronetanalyzer"

:: Git direct installer fallback
set "GIT_FILE_VER=2.45.2"
set "GIT_TAG_VER=2.45.2.windows.1"
set "GIT_URL=https://github.com/git-for-windows/git/releases/download/v%GIT_TAG_VER%/Git-%GIT_FILE_VER%-64-bit.exe"

:: Python installer
set "PY_FULL_VER=3.12.6"
set "PY_INSTALLER_URL=https://www.python.org/ftp/python/%PY_FULL_VER%/python-%PY_FULL_VER%-amd64.exe"
set "PY_PERUSER_DIR=%LocalAppData%\Programs\Python\Python312"
set "PY_PERUSER_EXE=%PY_PERUSER_DIR%\python.exe"
:: ==================================================

:: --- Logging dirs (create both to satisfy any script version) ---
if not exist "%APP_CACHE1%" md "%APP_CACHE1%" 2>nul
if not exist "%APP_CACHE2%" md "%APP_CACHE2%" 2>nul
attrib +h "%APP_CACHE1%" 2>nul
attrib +h "%APP_CACHE2%" 2>nul

call :log "Starting setup launcher..."

:: --- Work dir selection (labels to avoid parser quirks) ---
set "WORKDIR="
for %%D in ("%CANDIDATE1%" "%CANDIDATE2%" "%CANDIDATE3%" "%CANDIDATE4%") do (
  call :try_dir "%%~D"
  if defined WORKDIR goto HAVE_WORKDIR
)
call :log "ERROR: Could not create any working directory."
echo Failed to create working directory. See log: "%LOG%"
exit /b 1

:HAVE_WORKDIR
call :log "Using work directory: %WORKDIR%"

:: --- Ensure Git ---
call :ensure_git
if errorlevel 1 (
  call :log "ERROR: Git not available after install attempts."
  echo Git installation failed. See log: "%LOG%"
  exit /b 2
)
call :run_ok "git --version"

:: --- Ensure Python & set PY_CMD ---
call :ensure_python_and_set_cmd
if errorlevel 1 (
  call :log "ERROR: Python not available after install attempts."
  echo Python installation failed. See log: "%LOG%"
  exit /b 3
)
call :log "Using PY_CMD=%PY_CMD%"

:: --- Clone or update (no parentheses; absolute paths only) ---
if exist "%WORKDIR%\.git\" goto UPDATE_REPO
goto CLONE_REPO

:CLONE_REPO
call :log "Cloning fresh from %REPO_URL% into %WORKDIR% ..."
rem If the dir exists and is not a repo, clear it
dir /b "%WORKDIR%" >nul 2>&1
if not errorlevel 1 rmdir /s /q "%WORKDIR%" 2>nul
md "%WORKDIR%" 2>nul

for %%P in ("%WORKDIR%") do set "PARENT=%%~dpP"
if not exist "%PARENT%" md "%PARENT%" 2>nul

call :run_ok "git clone "%REPO_URL%" "%WORKDIR%""
if errorlevel 1 (
  call :log "ERROR: git clone failed."
  echo git clone failed. See log: "%LOG%"
  exit /b 4
)
goto AFTER_REPO

:UPDATE_REPO
call :log "Repo detected. Fetching latest and resetting..."
pushd "%WORKDIR%"
call :run_ok "git remote -v"
call :run_ok "git fetch --all --prune"
git rev-parse --verify origin/main 1>>"%LOG%" 2>&1
if not errorlevel 1 (
  call :run_ok "git reset --hard origin/main"
) else (
  call :log "WARN: 'origin/main' not found; trying 'origin/master'."
  call :run_ok "git reset --hard origin/master"
)
popd

:AFTER_REPO
:: --- Ensure Python-side log dir(s) exist for old/new scripts ---
if not exist "%APP_CACHE1%" md "%APP_CACHE1%" 2>nul
if not exist "%APP_CACHE2%" md "%APP_CACHE2%" 2>nul
attrib +h "%APP_CACHE1%" 2>nul
attrib +h "%APP_CACHE2%" 2>nul

:: --- Run setup_macronetanalyzer.py from repo root ---
set "PY_SETUP=%WORKDIR%\setup_macronetanalyzer.py"
if not exist "%PY_SETUP%" (
  call :log "ERROR: Setup script not found: %PY_SETUP%"
  echo Setup script not found: "%PY_SETUP%"
  exit /b 5
)
pushd "%WORKDIR%"
call :run_ok "%PY_CMD% --version"
call :run_ok "%PY_CMD% "%PY_SETUP%""
set "RC=!ERRORLEVEL!"
popd

if "!RC!"=="0" (
  call :log "Setup completed successfully."
  echo Setup completed successfully.
) else (
  call :log "ERROR: Setup failed with code !RC!."
  echo Setup failed with exit code !RC!. See log: "%LOG%"
  exit /b !RC!
)

echo.
pause
exit /b 0


:: ===================== FUNCTIONS =====================

:log
set "TS=%date% %time%"
echo %~1
>>"%LOG%" echo %TS% - %~1
goto :eof

:run_ok
set "CMDLINE=%~1"
call :log "EXEC: %CMDLINE%"
cmd /c %CMDLINE% 1>>"%LOG%" 2>&1
set "RC=!ERRORLEVEL!"
if not "!RC!"=="0" call :log "RC=!RC! for: %CMDLINE%"
exit /b !RC!

:try_dir
set "TRY=%~1"
if not defined TRY exit /b 0
if exist "%TRY%\." (
  set "WORKDIR=%TRY%"
  call :log "Directory exists: %TRY%"
  exit /b 0
)
if exist "%TRY%" (
  call :log "Path exists but is a file: %TRY%"
  exit /b 0
)
md "%TRY%" 1>>"%LOG%" 2>&1
if exist "%TRY%\." (
  set "WORKDIR=%TRY%"
  call :log "Created directory with md: %TRY%"
  exit /b 0
)
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
  "New-Item -Path '%TRY%' -ItemType Directory -Force | Out-Null" 1>>"%LOG%" 2>&1
if exist "%TRY%\." (
  set "WORKDIR=%TRY%"
  call :log "Created directory with PowerShell: %TRY%"
  exit /b 0
)
call :log "Failed to create: %TRY%"
exit /b 0

:ensure_git
call :log "Checking for Git..."
where git >nul 2>nul
if not errorlevel 1 (
  for /f "usebackq tokens=1,2*" %%A in (`git --version 2^>^&1`) do set "GIT_VER=%%A %%B"
  call :log "Git present: !GIT_VER!"
  exit /b 0
)
call :log "Git not found. Trying winget..."
where winget >nul 2>nul
if not errorlevel 1 (
  winget install --id Git.Git -e --silent --accept-package-agreements --accept-source-agreements 1>>"%LOG%" 2>&1
  if not errorlevel 1 (
    call :log "Git installed via winget."
    call :ensure_git_path
    where git >nul 2>nul && exit /b 0
  ) else (
    call :log "winget install failed; will try alternatives."
  )
)
call :log "Trying Chocolatey (if present)..."
where choco >nul 2>nul
if not errorlevel 1 (
  choco install git -y --no-progress 1>>"%LOG%" 2>&1
  if not errorlevel 1 (
    call :log "Git installed via Chocolatey."
    call :ensure_git_path
    where git >nul 2>nul && exit /b 0
  ) else (
    call :log "Chocolatey install failed; will try direct download."
  )
)
call :log "Downloading Git installer from %GIT_URL% ..."
set "GIT_EXE=%TEMP%\git-install-%RANDOM%.exe"
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
  "Try{Invoke-WebRequest -Uri '%GIT_URL%' -OutFile '%GIT_EXE%' -UseBasicParsing; exit 0}Catch{exit 1}"
if not exist "%GIT_EXE%" (
  call :log "ERROR: Failed to download Git installer."
  exit /b 1
)
call :log "Running Git installer silently..."
"%GIT_EXE%" /VERYSILENT /NORESTART 1>>"%LOG%" 2>&1
set "IR=!ERRORLEVEL!"
del /q "%GIT_EXE%" 2>nul
if not "!IR!"=="0" (
  call :log "ERROR: Git installer returned code !IR!."
  exit /b 1
)
call :ensure_git_path
where git >nul 2>nul
if not errorlevel 1 (
  call :log "Git available after install."
  exit /b 0
) else (
  call :log "ERROR: Git still not on PATH after install."
  exit /b 1
)

:ensure_git_path
for %%D in ("%ProgramFiles%\Git\cmd" "%ProgramFiles(x86)%\Git\cmd" "%LocalAppData%\Programs\Git\cmd") do (
  if exist "%%~D\git.exe" (
    set "PATH=%%~D;%PATH%"
    call :log "Session PATH updated with %%~D"
    goto :eof
  )
)
goto :eof

:ensure_python_and_set_cmd
call :log "Checking for Python..."
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -V >nul 2>&1
  if not errorlevel 1 (
    for /f "usebackq tokens=*" %%A in (`py -3 -V 2^>^&1`) do set "PY_VER=%%A"
    set "PY_CMD=py -3"
    call :log "Python present via launcher: !PY_VER!"
    exit /b 0
  )
)
where python3 >nul 2>nul
if not errorlevel 1 (
  for /f "usebackq tokens=*" %%A in (`python3 --version 2^>^&1`) do set "PV=%%A"
  echo !PV! | findstr /c:"Python 3" >nul
  if not errorlevel 1 (
    set "PY_CMD=python3"
    call :log "Python present: !PV!"
    exit /b 0
  )
)
where python >nul 2>nul
if not errorlevel 1 (
  for /f "usebackq tokens=*" %%A in (`python --version 2^>^&1`) do set "PV=%%A"
  echo !PV! | findstr /c:"Python 3" >nul
  if not errorlevel 1 (
    set "PY_CMD=python"
    call :log "Python present: !PV!"
    exit /b 0
  )
)
call :log "Python not found; downloading %PY_FULL_VER% ..."
set "PY_EXE=%TEMP%\py-install-%RANDOM%.exe"
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
  "Try{Invoke-WebRequest -Uri '%PY_INSTALLER_URL%' -OutFile '%PY_EXE%' -UseBasicParsing; exit 0}Catch{exit 1}"
if not exist "%PY_EXE%" (
  call :log "ERROR: Failed to download Python installer."
  exit /b 1
)
call :log "Installing Python silently..."
"%PY_EXE%" /quiet InstallAllUsers=0 Include_launcher=1 PrependPath=1 SimpleInstall=1 1>>"%LOG%" 2>&1
set "IR=!ERRORLEVEL!"
del /q "%PY_EXE%" 2>nul
if not "!IR!"=="0" (
  call :log "ERROR: Python installer returned code !IR!."
  exit /b 1
)
if exist "%PY_PERUSER_EXE%" (
  set "PATH=%PY_PERUSER_DIR%;%PATH%"
  call :log "Session PATH prepended: %PY_PERUSER_DIR%"
  set "PY_CMD=%PY_PERUSER_EXE%"
) else (
  for /f "usebackq delims=" %%P in (`
    powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
      "$d=Join-Path $env:LocalAppData 'Programs\Python'; if(Test-Path $d){ Get-ChildItem $d -Directory | Sort-Object Name -Descending | ForEach-Object { $e=Join-Path $_.FullName 'python.exe'; if(Test-Path $e){ Write-Output $e; break }}}"
  `) do set "PY_CMD=%%~fP" & set "PY_PERUSER_DIR=%%~dpP"
  if defined PY_CMD (
    set "PATH=%PY_PERUSER_DIR%;%PATH%"
    call :log "Session PATH prepended: %PY_PERUSER_DIR%"
  )
)
if not defined PY_CMD (
  call :log "ERROR: Could not resolve python.exe path."
  exit /b 1
)
call :run_ok "%PY_CMD% --version"
exit /b !ERRORLEVEL!
