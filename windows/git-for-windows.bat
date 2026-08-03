@echo off
setlocal

echo === Install Git for Windows and enable Unix tools ===

where git >nul 2>nul
if %errorlevel% neq 0 (
    echo Git not found. Trying winget install...

    where winget >nul 2>nul
    if %errorlevel% equ 0 (
        winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    ) else (
        echo winget not found. Trying choco install...

        where choco >nul 2>nul
        if %errorlevel% equ 0 (
            choco install git -y
        ) else (
            echo ERROR: neither winget nor choco found.
            echo Please install Git for Windows manually:
            echo https://git-scm.com/download/win
            pause
            exit /b 1
        )
    )
) else (
    echo Git already installed.
)

set "GIT_USR_BIN=%ProgramFiles%\Git\usr\bin"

if not exist "%GIT_USR_BIN%\du.exe" (
    set "GIT_USR_BIN=%ProgramFiles(x86)%\Git\usr\bin"
)

if not exist "%GIT_USR_BIN%\du.exe" (
    echo ERROR: Cannot find Git Unix tools directory.
    echo Expected: C:\Program Files\Git\usr\bin
    pause
    exit /b 1
)

echo Found Unix tools: %GIT_USR_BIN%

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$add='%GIT_USR_BIN%';" ^
  "$p=[Environment]::GetEnvironmentVariable('Path','User');" ^
  "$items=$p -split ';' | Where-Object { $_ -ne '' };" ^
  "if($items -notcontains $add) { [Environment]::SetEnvironmentVariable('Path', ($add + ';' + $p).TrimEnd(';'), 'User'); Write-Host 'Added to User PATH'; } else { Write-Host 'Already in User PATH'; }"

set "PATH=%GIT_USR_BIN%;%PATH%"

echo.
echo === Verify ===
where du
du --version

echo.
echo Done. Please reopen PowerShell or CMD, then test:
echo   du -sh D:/go/pkg/mod
echo   find . -type f -name "*.go"
echo   grep -R "xxx" .
pause