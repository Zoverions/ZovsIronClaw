@echo off
echo === ZovsIronClaw Installer ===

WHERE node >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Node.js is required but not installed. Aborting.
    exit /b 1
)

WHERE python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Python is required but not installed. Aborting.
    exit /b 1
)

WHERE pnpm >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo pnpm is required but not installed. Aborting.
    exit /b 1
)

WHERE ffmpeg >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Warning: ffmpeg is not installed. Audio/Video features may fail.
    echo Please install ffmpeg via choco or winget.
)

echo Prerequisites checked.

echo Installing Node.js dependencies...
call pnpm install

echo Setting up Python environment...
cd apps\gca-service
if not exist ".venv" (
    python -m venv .venv
    echo Created virtual environment in apps\gca-service\.venv
)

call .venv\Scripts\activate
echo Installing Python dependencies...
pip install -r requirements.txt
cd ..

echo Configuring environment...
if not exist ".env" (
    if exist ".env.ironclaw.example" (
        copy .env.ironclaw.example .env
    ) else if exist ".env.example" (
        copy .env.example .env
    )

    echo Appending local settings to .env...
    echo. >> .env
    echo # Local Config >> .env
    echo GCA_SERVICE_URL=http://localhost:8000 >> .env
    echo ENABLED_EXTENSIONS=gca-brain,voice-call >> .env
    echo OPENCLAW_STATE_DIR=%%USERPROFILE%%\.openclaw >> .env

    echo NOTE: Please verify .env has OPENCLAW_GATEWAY_TOKEN set.
) else (
    echo .env already exists. Skipping.
)

if not exist "apps\gca-service\gca_assets" mkdir "apps\gca-service\gca_assets"

echo === Installation Complete ===
echo Run 'scripts\start.bat' to start the system.
pause
