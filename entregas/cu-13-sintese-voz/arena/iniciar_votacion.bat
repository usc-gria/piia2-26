@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem ==================== CONFIGURACION ====================
rem Carpeta con los audios (IDIOMA\MODELO\PERFIL\*.wav)
set "AUDIOS=..\audios"
rem Parte de las parejas que vota cada persona (entre 0 y 1)
set "PROPORCION=0.5"
rem =======================================================

set "PY=python"
where py >nul 2>nul && set "PY=py -3"
%PY% --version >nul 2>nul || (
  echo No se encuentra Python. Instala Python 3.9 o superior desde https://www.python.org
  pause
  exit /b 1
)

%PY% votar.py --audios "%AUDIOS%" --proporcion %PROPORCION% --frases frases_prueba.csv --perfiles perfiles.csv --salida resultados
pause
