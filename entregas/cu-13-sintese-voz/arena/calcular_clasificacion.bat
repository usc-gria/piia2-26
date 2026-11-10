@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem ==================== CONFIGURACION ====================
rem Participaciones minimas de una pareja de modelos para entrar en el ranking
set "MIN_VOTOS=35"
rem =======================================================

set "PY=python"
where py >nul 2>nul && set "PY=py -3"
%PY% --version >nul 2>nul || (
  echo No se encuentra Python. Instala Python 3.9 o superior desde https://www.python.org
  pause
  exit /b 1
)

%PY% clasificacion.py resultados --min-votos %MIN_VOTOS% --salida clasificacion
pause
