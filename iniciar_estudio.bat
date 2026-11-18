@echo off
rem Starts the Studio with a double click: Docker stack, local AI model, Home Assistant setup, web server and browser.
setlocal EnableDelayedExpansion
cd /d "%~dp0"
set "STACK=stack\domotica-voz"
if not exist "%STACK%\.env" copy "%STACK%\.env.example" "%STACK%\.env" >nul
for /f "usebackq eol=# tokens=1,* delims==" %%a in ("%STACK%\.env") do set "%%a=%%b"
set "HA_URL=http://127.0.0.1:%HA_PORT%"
set "MQTT_WS_URL=ws://127.0.0.1:%MQTT_WS_PORT%"
if "%STUDIO_PORT%"=="" set "STUDIO_PORT=8765"

where uv >nul 2>nul || (echo [E_NO_UV] Falta uv. Instalalo desde https://docs.astral.sh/uv/ y vuelve a abrir este archivo. & pause & exit /b 1)
where ollama >nul 2>nul || (echo [E_NO_OLLAMA] Falta Ollama. Instalalo desde https://ollama.com y vuelve a abrir este archivo. & pause & exit /b 1)

docker info >nul 2>nul
if errorlevel 1 (
  echo Arrancando Docker Desktop...
  start "" "%LOCALAPPDATA%\Programs\DockerDesktop\Docker Desktop.exe" 2>nul || start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
  for /l %%i in (1,1,60) do (docker info >nul 2>nul && goto docker_ok) & timeout /t 5 >nul
  echo [E_DOCKER_DOWN] Docker no arranco en 5 minutos. Abre Docker Desktop a mano y repite. & pause & exit /b 1
)
:docker_ok
echo Levantando Home Assistant, MQTT, Whisper y Piper...
docker compose -f "%STACK%\docker-compose.yml" --env-file "%STACK%\.env" up -d || (echo [E_STACK] No arranco el stack. & pause & exit /b 1)

ollama list | findstr /b /c:"%OLLAMA_MODEL%" >nul || (echo Descargando el modelo de IA %OLLAMA_MODEL%... & ollama pull %OLLAMA_MODEL%)

echo Configurando Home Assistant (la primera vez tarda unos minutos)...
uv run "%STACK%\setup\setup_ha.py" || (pause & exit /b 1)

echo Abriendo el Estudio en http://127.0.0.1:%STUDIO_PORT%/demos/voice/
start "" "http://127.0.0.1:%STUDIO_PORT%/demos/voice/"
uv run --no-project python serve.py --port %STUDIO_PORT%
