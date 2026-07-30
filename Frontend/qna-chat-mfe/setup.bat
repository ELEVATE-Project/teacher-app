@echo off
SETLOCAL EnableDelayedExpansion

echo ===================================================
echo   Chanakya Frontend Setup Assistant (Windows)
echo ===================================================
echo.

:: Check for Node.js
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js is not installed or not in your PATH.
    echo Please install Node.js (v18 or higher) from https://nodejs.org/
    exit /b 1
)

:: Get Node version
for /f "tokens=*" %%i in ('node -v') do set NODE_VER=%%i
echo [*] Found Node.js: %NODE_VER%

:: Check for npm
where npm >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] npm is not installed or not in your PATH.
    exit /b 1
)

:: Get npm version
for /f "tokens=*" %%i in ('npm -v') do set NPM_VER=%%i
echo [*] Found npm: %NPM_VER%
echo.

:: Check for root .env
echo [*] Checking environment configuration...
set ROOT_ENV=..\..\.env
set ROOT_ENV_EXAMPLE=..\..\.env.example

if not exist "%ROOT_ENV%" (
    if exist "%ROOT_ENV_EXAMPLE%" (
        echo [!] .env file not found at workspace root.
        echo [*] Copying .env.example to .env at workspace root...
        copy "%ROOT_ENV_EXAMPLE%" "%ROOT_ENV%" >nul
        echo [SUCCESS] Created .env file from template. Please update the API keys in the root .env file.
    ) else (
        echo [!] Neither .env nor .env.example found at workspace root.
        echo [*] Creating a basic .env file at workspace root...
        (
            echo # Frontend API Configurations
            echo VITE_API_URL=http://localhost:3000
            echo VITE_FEEDBACK_BACKEND_URL=http://localhost:3000
            echo VITE_SARVAM_API_KEY=your_sarvam_api_key_here
        ) > "%ROOT_ENV%"
        echo [SUCCESS] Created a default .env file.
    )
) else (
    echo [*] .env file found at workspace root.
)
echo.

:: Install dependencies
echo [*] Installing frontend dependencies (npm install)...
echo.
call npm install
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] npm install failed. Please check the logs above.
    exit /b 1
)

echo.
echo ===================================================
echo [SUCCESS] Frontend setup completed successfully!
echo ===================================================
echo.
echo To start the development server, run:
echo   npm run dev
echo.
echo The frontend will be available at:
echo   http://localhost:5173
echo.
pause
