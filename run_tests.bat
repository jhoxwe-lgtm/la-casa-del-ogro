@echo off
cd /d "%~dp0"

py -c "import pytest, pytest_cov" >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias de pruebas...
    py -m pip install -r requirements-dev.txt
    if errorlevel 1 goto :error
)

echo Ejecutando suite automatizada y cobertura de ramas de casa_ogro.rules...
py -m pytest -v --cov=casa_ogro.rules --cov-branch --cov-report=term-missing
if errorlevel 1 goto :error

echo.
echo Pruebas finalizadas correctamente.
pause
exit /b 0

:error
echo.
echo Hubo errores en la instalacion o ejecucion de las pruebas.
pause
exit /b 1
