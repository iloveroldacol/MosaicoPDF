@echo off
title Instalador MosaicoPDF 2.0
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar_windows.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] La instalacion encontro un problema. Revisa el mensaje anterior.
    pause
    exit /b %ERRORLEVEL%
)
echo.
pause
