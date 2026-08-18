@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
call "%SCRIPT_DIR%start.bat" -Mode Local %*
exit /b %ERRORLEVEL%
