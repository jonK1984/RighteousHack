@echo off
setlocal

cd /d "%~dp0"

:: Load VS environment once
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" x64 >nul

echo.
echo ============================================================
echo   RighteousHack build menu
echo ============================================================
echo.
echo   "1) Full clean + package     (use only when you changed sys/winnt files,"
echo   "                            added new source files, or want to be 100% safe)"
echo   "2) Quick rebuild            (default - just recompile changed .c files)"
echo   "3) Just run the game        (no compile - fastest to testing)"
echo.
choice /c 123 /n /m "Choose [1-3]: "

REM ─────────────────────────────────────────────────────────────
if %errorlevel%==1 (
    echo.
    echo *** Full clean + package ***
    cd src
    nmake -f Makefile clean
    nmake -f Makefile package
    goto :done
)

if %errorlevel%==2 (
    echo.
    echo "*** Quick rebuild (only changed files) ***"
    cd src
    nmake -f Makefile
    goto :done
)

if %errorlevel%==3 (
    echo.
    echo "*** Launching the game (no build) ***"
    if exist binary\nethack.exe (
        echo Starting nethack.exe ...
        start "" "binary\nethack.exe" -D -u prophet
    ) else (
        echo No binary\nethack.exe found – doing a quick build first...
        cd src
        nmake -f Makefile.vstudio
    )
    goto :done
)

:done
echo.
if %errorlevel%==0 (
    echo ========== BUILD / LAUNCH SUCCEEDED ==========
) else (
    echo ========== BUILD FAILED ==========
)
echo.
echo Press any key to exit...
pause >nul
endlocal