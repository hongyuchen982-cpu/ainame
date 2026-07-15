@echo off
setlocal

rem Always run from the directory containing this script.
cd /d "%~dp0"

set "REDIS_DIR=C:\Program Files\Redis"
set "REDIS_CLI=%REDIS_DIR%\redis-cli.exe"
set "REDIS_SERVER=%REDIS_DIR%\redis-server.exe"

rem Start Redis only when it is not already responding.
"%REDIS_CLI%" ping 2>nul | findstr /x /c:"PONG" >nul
if errorlevel 1 (
    if not exist "%REDIS_SERVER%" (
        echo [ERROR] Redis was not found at "%REDIS_SERVER%".
        pause
        exit /b 1
    )

    echo Starting Redis...
    start "Redis" /min "%REDIS_SERVER%"
    timeout /t 2 /nobreak >nul

    "%REDIS_CLI%" ping 2>nul | findstr /x /c:"PONG" >nul
    if errorlevel 1 (
        echo [ERROR] Redis failed to start.
        pause
        exit /b 1
    )
) else (
    echo Redis is already running.
)

echo Starting FastAPI...
echo Open http://127.0.0.1:8000/docs in your browser.
echo.
uvicorn main:app --reload

if errorlevel 1 (
    echo.
    echo [ERROR] Uvicorn exited with an error.
    pause
)

endlocal
