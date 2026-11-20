@echo off
rem Starts the Studio with a double click, all in Docker: voice stack, local AI, Home Assistant setup and the Studio.
rem Needs only Docker Desktop. The first time it downloads several GB and takes a while.
setlocal EnableDelayedExpansion
cd /d "%~dp0"
set "STACK=stack\domotica-voz"
if not exist "%STACK%\.env" copy "%STACK%\.env.example" "%STACK%\.env" >nul
if not exist ".env" copy ".env.example" ".env" >nul
for /f "usebackq eol=# tokens=1,* delims==" %%a in ("%STACK%\.env") do set "%%a=%%b"
for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do set "%%a=%%b"
if "%STUDIO_PORT%"=="" set "STUDIO_PORT=8765"
echo Project Studio

docker info >nul 2>nul
if errorlevel 1 (
  echo Arrancando Docker Desktop...
  start "" "%LOCALAPPDATA%\Programs\DockerDesktop\Docker Desktop.exe" 2>nul || start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
  for /l %%i in (1,1,60) do (docker info >nul 2>nul && goto docker_ok) & timeout /t 5 >nul
  echo [E_DOCKER_DOWN] Docker no arranco en 5 minutos. Abre Docker Desktop a mano y repite. & pause & exit /b 1
)
:docker_ok
echo Docker listo.
rem The two folders Docker mounts; everything inside them is made by the init service.
if not exist "..\project_studio_data" mkdir "..\project_studio_data"
if not exist "%USERPROFILE%\.agents\secrets\project_studio" mkdir "%USERPROFILE%\.agents\secrets\project_studio"
rem An NVIDIA card runs the local AI much faster: switch the default "cpu" to "gpu".
if /i "%COMPOSE_PROFILES%"=="cpu" (where nvidia-smi >nul 2>nul && set "COMPOSE_PROFILES=gpu")

set "COMPOSE=docker compose --env-file %STACK%\.env --env-file .env"
%COMPOSE% run --rm --build init || (echo [E_INIT] No se crearon las carpetas y claves. & pause & exit /b 1)
echo Arrancando (la primera vez descarga varios GB y tarda)...
%COMPOSE% up -d --build || (echo [E_SETUP] No arranco. Mira: docker compose logs setup & pause & exit /b 1)

echo Abriendo el Estudio en http://127.0.0.1:%STUDIO_PORT%/studio/
start "" "http://127.0.0.1:%STUDIO_PORT%/studio/"
